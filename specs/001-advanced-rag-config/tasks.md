# Tasks: Advanced RAG Configuration System

Feature: Advanced RAG Configuration System (`001-advanced-rag-config`)
Spec: `specs/001-advanced-rag-config/spec.md`

Phase 1 — Setup

- [ ] T001 Create `specs/001-advanced-rag-config/tasks.md` with phased checklist (this file)
- [P] T002 [P] Create RAG schema module `backend/app/schemas/rag_config.py` with data models for `AdvancedRAGConfig`, `EmbeddingConfig`, `ChunkingConfig`, `RetrievalConfig`, `LLMConfig`, and `VisualProcessingConfig`
- [P] T003 [P] Create property-test templates `backend/tests/property/test_properties_template.py` implementing Hypothesis scaffolding and headers referencing design properties

Phase 2 — Foundational (blocking prerequisites)

- [ ] T004 Implement `RAGConfigManager` in `backend/app/core/rag_config_manager.py` with async `validate_config`, `save_config`, and `get_config` methods that read/write using repositories
- [ ] T005 Implement `ConfigValidator` in `backend/app/core/config_validator.py` with `validate_model_compatibility`, `validate_api_keys`, and `estimate_costs` functions
- [ ] T006 Add DB models: `backend/app/models/rag_config.py` and `backend/app/models/processing_task.py` and add alembic migration placeholder `backend/alembic/versions/00xx_add_rag_config_and_tasks.py`
- [ ] T007 Implement repository accessors `backend/app/repositories/rag_config.py` and `backend/app/repositories/processing_task.py` for persistence operations

Phase 3 — User Story 1: Configure and Apply RAG Settings (Priority P1)

- [P] T008 [US1] Add API endpoint to save and retrieve RAG config in `backend/app/api/endpoints/rag_config.py` and wire into `backend/app/api/api.py`
- [P] T009 [US1] Add integration tests `backend/tests/test_rag_config_api.py` that exercise validation, save, and retrieval flows (use mocked model provider validation)
- [P] T010 [US1] Add UI configuration stub `frontend/src/components/chatbot-config/ConfigForm.tsx` and a README note `specs/001-advanced-rag-config/frontend.md` describing expected form fields

Phase 4 — User Story 2: Upload and Asynchronous Document Processing (Priority P2)

- [ ] T011 [US2] Update document upload endpoint `backend/app/api/endpoints/documents.py` to enqueue a `ProcessingTask` via the producer repository when a document is uploaded
- [ ] T012 [US2] Implement queue producer `backend/app/processing/producer.py` (abstracted interface) that publishes ProcessingTask messages to the chosen queue
- [ ] T013 [US2] Implement queue consumer scaffold `backend/app/processing/consumer.py` that consumes ProcessingTask messages and calls `DocumentProcessor.process_document`
- [P] T014 [US2] Create `backend/tests/test_processing_pipeline.py` that mocks the queue and validates that a document upload produces the expected ProcessingTask and status transitions

Phase 5 — User Story 3: Advanced Retrieval & Reranking Controls (Priority P3)

- [ ] T015 [US3] Create `backend/app/core/strategy_factory.py` with `create_embedder`, `create_chunker`, `create_retriever`, `create_reranker`, and `create_llm` stubs
- [ ] T016 [US3] Implement `backend/app/core/retriever.py` with a hybrid scoring function combining semantic scores and BM25-style scores (stubbed interfaces)
- [ ] T017 [US3] Add reranker integration placeholder `backend/app/core/reranker.py` and fallback logic when reranker unavailable
- [P] T018 [US3] Add property-based test template `backend/tests/property/test_hybrid_ranking.py` referencing **Property 5: Hybrid Search Composition** and scaffolded Hypothesis test

Final Phase — Polish & Cross-Cutting Concerns

- [P] T019 Add docs `specs/001-advanced-rag-config/README.md` summarizing feature, rollout plan, and reprocessing cost guidance
- [P] T020 Add operations checklist `specs/001-advanced-rag-config/operations.md` with monitoring/SLO items (queue depth, worker count, embedding cache hit-rate)
- [P] T021 Add CI job templates `ci/ci-rag-config.yml` entries (or notes) for running unit tests and property tests on PRs

Dependencies

- `T004,T005,T006,T007` must complete before `T008` (API) is fully testable.
- `T011,T012` depend on `T006` (ProcessingTask model) and `T007` (processing repository).
- `T015,T016,T017` are independent of upload flow and can run in parallel with `T011..T014` once foundational schemas exist.

Parallel execution examples

- Frontend work (`T009`) can be done in parallel with backend schema (`T002`) and validator (`T005`).
- Property-test scaffolding (`T003`, `T018`) can be implemented in parallel with feature code; they do not block API endpoints.

Implementation strategy

- MVP first: implement `RAGConfigManager`, `ConfigValidator`, schema, and a minimal API endpoint (`T004,T005,T002,T008`) to allow saving a validated config. Then implement asynchronous ingestion (`T011..T014`) and retrieval improvements (`T015..T017`).
- Incremental delivery: each user story phase should be independently deployable and testable. Start with US1 (P1) as MVP slice.

Estimate & Acceptance

- Each task should include at least one unit test or property-test template where applicable.
- A task is accepted when code is merged, tests pass in CI, and the acceptance scenario in `spec.md` for the story passes locally.