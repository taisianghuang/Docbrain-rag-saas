# Advanced RAG Configuration: Rollout & Cost Guidance

Summary
- Tenant-scoped RAG configuration: embedding/LLM selection, chunking, retrieval, reranking, visual processing.
- MVP delivers save/retrieve API and sync ingestion fallback; queue backend deferred to Spec2.

Rollout Plan
- Phase 1: Schema + validator + manager + API (save/get).
- Phase 2: Async ingestion (producer/consumer scaffolds; real queue later).
- Phase 3: Advanced retrieval (hybrid/reranker stubs; property tests).

Reprocessing Cost Guidance
- Changing embedding model requires reprocessing all stored documents.
- Estimate chunk count via strategy; multiply by tokenization cost and embedding rate.
- Provide user confirmation with estimated cost before applying.

API
- POST `/api/rag-config/{chatbot_id}`: save config (validates, persists)
- GET  `/api/rag-config/{chatbot_id}`: retrieve config

Notes
- Queue backend (Kafka/Redis/RabbitMQ) is pluggable via `QueueAdapter` and will be decided in Spec2.
