"""
Document chunking strategies.

Provides different chunking approaches for document processing:
- Standard: Fixed-size chunks with overlap
- Markdown: Structure-aware chunking based on headers
- Semantic: Similarity-based chunking using embeddings
- Window: Sentence window retrieval for precise context

Dependencies are injected (e.g., openai_api_key) rather than imported globally.
"""

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
    """Supported chunking strategies."""
    STANDARD = "standard"        # Fixed-size chunks
    MARKDOWN = "markdown"        # Header-based structure chunking
    SEMANTIC = "semantic"        # Semantic similarity chunking
    WINDOW = "window"            # Sentence window retrieval


def get_nodes_from_strategy(
    documents: List[Document],
    rag_config: dict,
    openai_api_key: Optional[str] = None
) -> List[BaseNode]:
    """
    Chunk documents using configured strategy.

    Args:
        documents: List of LlamaIndex Document objects to chunk
        rag_config: Configuration dict with chunking_strategy, chunk_size, etc.
        openai_api_key: Optional API key for semantic chunking

    Returns:
        List of chunked nodes ready for embedding and indexing

    Raises:
        ValueError: If semantic strategy is selected without API key
    """

    # Extract configuration
    strategy = rag_config.get("chunking_strategy", ChunkingStrategy.STANDARD)
    chunk_size = int(rag_config.get("chunk_size", 1024))
    chunk_overlap = int(rag_config.get("chunk_overlap", 200))

    parser = None

    # Select and configure parser based on strategy
    if strategy == ChunkingStrategy.MARKDOWN:
        # MarkdownNodeParser splits by headers (H1, H2, etc.)
        # Does not use chunk_size - respects document structure
        parser = MarkdownNodeParser()

    elif strategy == ChunkingStrategy.SEMANTIC:
        # Semantic chunking requires embedding model to measure similarity
        if not openai_api_key:
            raise ValueError(
                "OpenAI API Key is required for Semantic Chunking Strategy. "
                "Provide openai_api_key parameter or use a different strategy."
            )

        embed_model = OpenAIEmbedding(
            api_key=openai_api_key,
            model='text-embedding-3-small'
        )
        parser = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
            embed_model=embed_model
        )

    elif strategy == ChunkingStrategy.WINDOW:
        # Sentence window retrieval - stores surrounding sentences as metadata
        # window_size=3 means 3 sentences before and after for context
        parser = SentenceWindowNodeParser(
            window_size=int(rag_config.get("window_size", 3)),
            window_metadata_key="window",
            original_text_metadata_key="original_text",
        )

    else:  # Default: STANDARD
        # Standard fixed-size chunking with overlap
        parser = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    # Execute chunking
    nodes = parser.get_nodes_from_documents(documents)

    return nodes


def estimate_chunk_count(
    document_size: int,
    rag_config: dict
) -> int:
    """
    Estimate number of chunks for a document.

    Useful for cost/reprocessing estimates.

    Args:
        document_size: Document size in characters
        rag_config: Chunking configuration

    Returns:
        Estimated number of chunks
    """
    strategy = rag_config.get("chunking_strategy", ChunkingStrategy.STANDARD)

    if strategy == ChunkingStrategy.MARKDOWN:
        # Markdown chunking is structure-dependent, rough estimate
        return max(1, document_size // 2000)

    elif strategy == ChunkingStrategy.SEMANTIC:
        # Semantic chunking creates variable-size chunks
        return max(1, document_size // 1500)

    elif strategy == ChunkingStrategy.WINDOW:
        # Window strategy creates many small overlapping chunks
        window_size = rag_config.get("window_size", 3)
        # Rough estimate based on sentence count
        avg_sentence_length = 100
        num_sentences = document_size // avg_sentence_length
        return max(1, num_sentences // (window_size * 2))

    else:  # STANDARD
        chunk_size = int(rag_config.get("chunk_size", 1024))
        chunk_overlap = int(rag_config.get("chunk_overlap", 200))
        effective_chunk_size = chunk_size - chunk_overlap
        return max(1, (document_size - chunk_overlap) // effective_chunk_size + 1)
