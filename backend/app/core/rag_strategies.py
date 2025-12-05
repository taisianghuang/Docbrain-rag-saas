# backend/app/core/rag_strategies.py
import os
from typing import Optional, List
from enum import Enum

from llama_index.core import VectorStoreIndex, get_response_synthesizer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.retrievers import VectorIndexRetriever, RouterRetriever
from llama_index.core.tools import RetrieverTool
from llama_index.core.postprocessor import MetadataReplacementPostProcessor, SimilarityPostprocessor
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.vector_stores import MetadataFilters
from llama_index.core.llms import LLM

# Rerankers
# 注意: 在 Docker 環境中，第一次執行會下載模型 (BAAI/bge-reranker-large)
# 建議在 Dockerfile 中預先下載，或掛載 Cache Volume
from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker


class RAGStrategy(str, Enum):
    VECTOR = "vector"                  # 標準向量檢索
    HYBRID = "hybrid"                  # 混合檢索 (向量 + 關鍵字)
    ROUTER = "router"                  # 路由器 (自動選擇 向量 或 關鍵字)
    SENTENCE_WINDOW = "sentence_window"  # TODO::句子視窗 (需配合特定 Ingestion)
    PARENT_CHILD = "parent_child"       # TODO::父子索引 (需配合特定 Ingestion)


def determine_top_k(rag_config: dict) -> int:
    """
    根據使用者建議的表格邏輯，決定第一階段檢索數量 (Coarse Top-K)。

    邏輯：
    1. 若 config 有指定 'top_k_coarse'，優先使用。
    2. 若無，則讀取 'db_scale' (small/medium/large) 來決定預設值。
    """
    if "top_k_coarse" in rag_config:
        return int(rag_config["top_k_coarse"])

    scale = rag_config.get("db_scale", "small")  # 預設小型

    if scale == 'medium':
        return 30  # 建議: 30~50
    elif scale == 'large':
        return 50  # 建議: 50~100
    else:  # small
        return 15  # 建議: 10~20


def create_chat_engine(
    index: VectorStoreIndex,
    llm: LLM,
    filters: MetadataFilters,
    system_prompt: str,
    rag_config: dict
) -> CondensePlusContextChatEngine:
    """
    RAG 策略工廠：根據 rag_config 決定檢索與排序方式
    """
    strategy = rag_config.get("mode", RAGStrategy.VECTOR)
    top_k_coarse = determine_top_k(rag_config)            # 第一階段粗排
    top_k_fine = int(rag_config.get("top_k", 5))          # 第二階段精排
    rerank_enabled = rag_config.get("rerank", False)      # 是否啟用 Reranker

    retriever = None
    node_postprocessors = []

    # --- 1. 定義 Retriever (第一階段檢索) ---

    if strategy == RAGStrategy.HYBRID:
        # 混合檢索: 需確保 PGVector 已啟用 hybrid_search
        # 這裡假設 vector_store 已正確設定
        retriever = index.as_retriever(
            similarity_top_k=top_k_coarse if rerank_enabled else top_k_fine,
            vector_store_kwargs={"hybrid_search": True},
            filters=filters
        )

    elif strategy == RAGStrategy.ROUTER:
        # Router: 讓 LLM 決定用關鍵字找還是用向量找
        vector_tool = RetrieverTool.from_defaults(
            retriever=index.as_retriever(filters=filters),
            description="Useful for summarizing or answering questions about specific semantic topics."
        )
        # 這裡簡化處理：Keyword 檢索通常也依賴同一個 Index 的不同查詢模式
        # 在純 LlamaIndex + PGVector 中，通常會建立兩個不同的 Retriever
        # 這裡示範概念
        retriever = RouterRetriever(
            selector=LLMSingleSelector.from_defaults(llm=llm),
            retriever_tools=[vector_tool],  # 實際應加入 KeywordTool
            llm=llm
        )

    elif strategy == RAGStrategy.SENTENCE_WINDOW:
        # 句子視窗: 檢索到句子後，擴展前後文
        # 注意: 這需要 MetadataReplacementPostProcessor
        retriever = index.as_retriever(
            similarity_top_k=top_k_coarse if rerank_enabled else top_k_fine,
            filters=filters
        )
        node_postprocessors.append(
            MetadataReplacementPostProcessor(target_metadata_key="window")
        )

    else:  # Default VECTOR
        retriever = index.as_retriever(
            similarity_top_k=top_k_coarse if rerank_enabled else top_k_fine,
            filters=filters
        )

    # --- 2. 定義 Postprocessors (Reranking & Filtering) ---

    # A. 強力 Reranker (Top-50 -> Top-5)
    if rerank_enabled:
        # 使用 BGE-Reranker (需 GPU 支援效果較好，CPU 會慢)
        # model 可選: 'BAAI/bge-reranker-base' 或 'BAAI/bge-reranker-large'
        reranker = FlagEmbeddingReranker(
            model_name="BAAI/bge-reranker-base",
            top_n=top_k_fine,
            use_fp16=False
        )
        node_postprocessors.append(reranker)

    # B. 基礎信心分數過濾 (保底)
    node_postprocessors.append(
        SimilarityPostprocessor(similarity_cutoff=0.7)
    )

    # --- 3. 組裝 Chat Engine ---

    # 使用 ContextChatEngine，因為它可以讓我們自定義 retriever
    chat_engine = CondensePlusContextChatEngine.from_defaults(
        retriever=retriever,
        llm=llm,
        system_prompt=system_prompt,
        node_postprocessors=node_postprocessors,
        verbose=True
    )

    return chat_engine
