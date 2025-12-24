"""
RAG retrieval and ranking strategies.

Provides strategy functions for configuring retrieval pipelines:
- Vector retrieval
- BM25 keyword search
- Hybrid search (vector + keyword)
- Router-based retrieval
- Reranking and post-processing

These are pure strategy functions that return configuration/parameters.
"""

from typing import Optional, List, Any
from enum import Enum
from dataclasses import dataclass

from llama_index.core import VectorStoreIndex, get_response_synthesizer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.retrievers import VectorIndexRetriever, RouterRetriever
from llama_index.core.tools import RetrieverTool
from llama_index.core.postprocessor import (
    MetadataReplacementPostProcessor,
    SimilarityPostprocessor
)
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.vector_stores import MetadataFilters
from llama_index.core.llms import LLM


class RAGStrategy(str, Enum):
    """Supported RAG retrieval strategies."""
    VECTOR = "vector"                  # Standard vector retrieval
    HYBRID = "hybrid"                  # Vector + keyword (BM25)
    ROUTER = "router"                  # LLM-based routing between strategies
    SENTENCE_WINDOW = "sentence_window"  # Sentence window retrieval
    PARENT_CHILD = "parent_child"       # Parent-child document hierarchy


@dataclass
class RetrievalParams:
    """
    Parameters for retrieval pipeline.

    Extracted from RAG config for use in building retrieval engines.
    """
    strategy: RAGStrategy
    top_k_initial: int
    top_k_final: int
    enable_reranking: bool
    reranker_model: Optional[str]
    hybrid_weights: Optional[dict]
    similarity_threshold: float


def build_retrieval_params(rag_config: dict) -> RetrievalParams:
    """
    Extract and normalize retrieval parameters from RAG config.

    Args:
        rag_config: RAG configuration dictionary

    Returns:
        RetrievalParams with normalized values and defaults
    """
    strategy = RAGStrategy(rag_config.get("mode", "vector"))

    # Determine top_k values
    # For reranking: retrieve more initially, then rerank to final count
    enable_reranking = rag_config.get("rerank", False)
    top_k_final = int(rag_config.get("top_k", 5))

    # Determine coarse top-k based on scale or explicit config
    if "top_k_coarse" in rag_config:
        top_k_initial = int(rag_config["top_k_coarse"])
    else:
        db_scale = rag_config.get("db_scale", "small")
        scale_mapping = {
            "small": 15,
            "medium": 30,
            "large": 50
        }
        top_k_initial = scale_mapping.get(db_scale, 15)

    # If not reranking, use same value for initial and final
    if not enable_reranking:
        top_k_initial = top_k_final

    # Extract other parameters
    reranker_model = rag_config.get("reranker_model")
    hybrid_weights = rag_config.get(
        "hybrid_weights", {"semantic": 0.7, "bm25": 0.3})
    similarity_threshold = float(rag_config.get("similarity_threshold", 0.7))

    return RetrievalParams(
        strategy=strategy,
        top_k_initial=top_k_initial,
        top_k_final=top_k_final,
        enable_reranking=enable_reranking,
        reranker_model=reranker_model,
        hybrid_weights=hybrid_weights,
        similarity_threshold=similarity_threshold
    )


def create_chat_engine(
    index: VectorStoreIndex,
    llm: LLM,
    filters: MetadataFilters,
    system_prompt: str,
    rag_config: dict
) -> CondensePlusContextChatEngine:
    """
    Create a chat engine with configured retrieval strategy.

    Args:
        index: Vector store index
        llm: Language model for generation
        filters: Metadata filters (tenant isolation, etc.)
        system_prompt: System prompt for the chat
        rag_config: RAG configuration dictionary

    Returns:
        Configured chat engine with retrieval and post-processing
    """
    params = build_retrieval_params(rag_config)

    retriever = None
    node_postprocessors = []

    # --- Build Retriever based on strategy ---

    if params.strategy == RAGStrategy.HYBRID:
        # Hybrid search: vector + keyword (BM25)
        retriever = index.as_retriever(
            similarity_top_k=params.top_k_initial,
            vector_store_kwargs={
                "hybrid_search": True,
                "alpha": params.hybrid_weights.get("semantic", 0.7)
            },
            filters=filters
        )

    elif params.strategy == RAGStrategy.ROUTER:
        # Router: LLM decides between retrieval strategies
        vector_tool = RetrieverTool.from_defaults(
            retriever=index.as_retriever(
                similarity_top_k=params.top_k_initial,
                filters=filters
            ),
            description="Useful for semantic search and answering questions about topics."
        )

        retriever = RouterRetriever(
            selector=LLMSingleSelector.from_defaults(llm=llm),
            retriever_tools=[vector_tool],
            llm=llm
        )

    elif params.strategy == RAGStrategy.SENTENCE_WINDOW:
        # Sentence window: retrieve sentences with surrounding context
        retriever = index.as_retriever(
            similarity_top_k=params.top_k_initial,
            filters=filters
        )
        # Add metadata replacement post-processor for window context
        node_postprocessors.append(
            MetadataReplacementPostProcessor(target_metadata_key="window")
        )

    else:  # Default: VECTOR
        retriever = index.as_retriever(
            similarity_top_k=params.top_k_initial,
            filters=filters
        )

    # --- Add Post-processors (Reranking & Filtering) ---

    if params.enable_reranking and params.reranker_model:
        # Import reranker only when needed (may require model download)
        try:
            from llama_index.postprocessor.flag_embedding_reranker import FlagEmbeddingReranker

            reranker = FlagEmbeddingReranker(
                model_name=params.reranker_model or "BAAI/bge-reranker-base",
                top_n=params.top_k_final,
                use_fp16=False  # CPU-safe, use True for GPU
            )
            node_postprocessors.append(reranker)
        except ImportError:
            # Fallback if reranker not available
            pass

    # Add similarity score filtering
    node_postprocessors.append(
        SimilarityPostprocessor(similarity_cutoff=params.similarity_threshold)
    )

    # --- Assemble Chat Engine ---

    chat_engine = CondensePlusContextChatEngine.from_defaults(
        retriever=retriever,
        llm=llm,
        system_prompt=system_prompt,
        node_postprocessors=node_postprocessors,
        verbose=True
    )

    return chat_engine
