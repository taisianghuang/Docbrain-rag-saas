# Frontend Expectations: RAG Config Form

Fields (align with `AdvancedRAGConfig`):
- Embedding: `model_name`, `provider`, `batch_size`, `api_key_ref`
- Chunking: `strategy`, `chunk_size`, `chunk_overlap`, `window_size`, `semantic_threshold`, `respect_document_structure`
- Retrieval: `strategy`, `top_k_initial`, `top_k_final`, `enable_reranking`, `reranker_model`, `similarity_threshold`, `hybrid_weights`
- LLM: `model_name`, `provider`, `temperature`, `max_tokens`, `system_prompt`, `api_key_ref`
- Visual Processing: `enable_ocr`, `enable_colpali`, `enable_vlm_summarization`, `ocr_provider`, `vlm_model`
- Performance: `cache_embeddings`, `batch_processing`, `parallel_workers`, `memory_limit_mb`

Notes:
- Warn users when changing embedding model (requires reprocessing).
- Validate required API keys before save.
