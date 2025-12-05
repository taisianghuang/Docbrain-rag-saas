# backend/app/core/chunking_strategies.py
from enum import Enum
from typing import List, Optional
from llama_index.core.schema import Document, BaseNode
from llama_index.core.node_parser import (
    SentenceSplitter,
    MarkdownNodeParser,
    SemanticSplitterNodeParser,
    SentenceWindowNodeParser
)
from llama_index.embeddings.openai import OpenAIEmbedding


class ChunkingStrategy(str, Enum):
    STANDARD = "standard"        # 標準固定字數
    MARKDOWN = "markdown"        # 依據標題層級 (適合技術文件)
    SEMANTIC = "semantic"        # 依據語意相似度 (適合論文/法律)
    WINDOW = "window"            # 句子視窗 (適合精確檢索)


def get_nodes_from_strategy(
    documents: List[Document],
    rag_config: dict,
    openai_api_key: Optional[str] = None
) -> List[BaseNode]:
    """
    Chunking 策略工廠：
    接收原始文件 (LlamaDocs) 與設定，回傳切分後的節點 (Nodes)。
    """

    # 1. 讀取設定
    strategy = rag_config.get("chunking_strategy", ChunkingStrategy.STANDARD)
    chunk_size = int(rag_config.get("chunk_size", 1024))
    chunk_overlap = int(rag_config.get("chunk_overlap", 200))

    parser = None

    # 2. 選擇 Node Parser
    if strategy == ChunkingStrategy.MARKDOWN:
        # MarkdownNodeParser 不使用 chunk_size，而是依據 Header 結構
        parser = MarkdownNodeParser()

    elif strategy == ChunkingStrategy.SEMANTIC:
        # 語意切分需要 Embedding Model 來計算句子間的距離
        if not openai_api_key:
            raise ValueError(
                "OpenAI API Key is required for Semantic Chunking Strategy.")

        embed_model = OpenAIEmbedding(api_key=openai_api_key)
        parser = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
            embed_model=embed_model
        )

    elif strategy == ChunkingStrategy.WINDOW:
        # Window Retrieval 專用 parser
        # 預設 window_size=3 代表前後各抓 3 個句子當 context
        parser = SentenceWindowNodeParser(
            window_size=int(rag_config.get("window_size", 3)),
            window_metadata_key="window",
            original_text_metadata_key="original_text",
        )

    else:  # Default: STANDARD
        parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    # 3. 執行切分
    nodes = parser.get_nodes_from_documents(documents)

    return nodes
