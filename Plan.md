# DocBrain — Project Execution Plan

**Overview**
DocBrain is a B2B RAG (Retrieval-Augmented Generation) SaaS platform that allows businesses to upload documentation, build a knowledge base, and expose a customizable chatbot widget for embedding.

---

## 📊 Project Architecture Summary

### Tech Stack
- **Backend**: FastAPI + SQLAlchemy (async) + Alembic migrations
- **Database**: PostgreSQL + pgvector for embeddings
- **LLM Integration**: OpenAI GPT-4o/GPT-3.5-turbo (tenant-scoped keys)
- **Document Parsing**: LlamaParse (complex PDF handling)
- **Vector Store**: LlamaIndex PGVectorStore
- **Frontend**: Next.js 15 (App Router) + TypeScript + shadcn/ui + TanStack Query
- **Widget**: Vanilla JavaScript with Shadow DOM (IIFE bundle)
- **Infrastructure**: Docker Compose + PostgreSQL 18 + pgvector

### Core Components

**Backend Structure:**
```
backend/app/
├── main.py                          # FastAPI app, logging setup, Sentry config
├── schemas.py                       # Pydantic V2 models (requests/responses)
├── api/
│   ├── api.py                       # Router registration
│   ├── deps.py                      # Dependency injection (8 repository providers, services)
│   └── endpoints/
│       ├── auth.py                  # Register/Login (with logging)
│       ├── conversation.py          # POST /conversation/chat (with logging)
│       ├── documents.py             # ✅ GET /chatbots/{id}/documents, DELETE /document/{id}
│       ├── chatbots.py              # ✅ GET/POST /chatbots, GET/PATCH/DELETE /chatbots/{id}
│       ├── settings.py              # ✅ GET/PATCH /tenant/settings (encrypted key management)
│       ├── health.py                # Health check
├── models/
│   ├── tenant.py, account.py, chatbot.py, conversation.py, document.py
├── services/
│   ├── auth.py                      # Register, authenticate, token validation (with logging)
│   ├── chat.py                      # ✅ RAG orchestration (depends on ConversationRepository)
│   ├── chatbot.py                   # ✅ Chatbot CRUD (with logging, added update/delete/list methods)
│   ├── ingestion.py                 # ✅ File upload → parse → chunk → vectorize (with logging, uses DocumentRepository)
│   ├── account.py                   # ✅ Account service (depends on AccountRepository)
│   ├── tenant.py                    # ✅ Tenant service (depends on TenantRepository, added update_tenant_settings)
│   └── vector_store.py              # Vector store utilities
├── repositories/                    # ✅ NEW: Repository pattern for DB access
│   ├── chatbot.py                   # ChatbotRepository (CRUD operations)
│   ├── document.py                  # DocumentRepository (document operations)
│   ├── account.py                   # ✅ AccountRepository (email/ID lookups, CRUD)
│   ├── tenant.py                    # ✅ TenantRepository (tenant lookups, updates)
│   └── conversation.py              # ✅ ConversationRepository (message operations)
├── core/
│   ├── config.py                    # Environment-driven settings (pydantic-settings)
│   ├── security.py                  # Password hashing, JWT, encryption/decryption
│   ├── chunking_strategies.py       # Standard/Markdown/Semantic/Window splitting
│   ├── rag_factory.py               # PGVectorStore factory
│   └── rag_strategies.py            # ✅ Chat engine factory with system prompts
├── db/
│   ├── session.py                   # Async SQLAlchemy engine/sessionmaker
│   ├── base.py                      # Base declarative model
│   └── wait_for_db.py               # Startup DB health check
└── alembic/                         # Migrations (3 versions)
```

**Frontend Structure:**
```
frontend/src/
├── app/
│   ├── layout.tsx                   # Root layout with providers
│   ├── (auth)/                      # Auth routes (login, register)
│   └── (dashboard)/                 # Protected dashboard
│       ├── page.tsx                 # Overview with stats
│       ├── chatbots/                # List and detail pages
│       ├── chatbots/[id]/           # Config, Knowledge, Playground tabs
│       └── settings/                # Tenant API key management
├── components/
│   ├── providers/                   # AuthProvider, AppProviders
│   ├── chatbot-detail/              # ConfigTab, KnowledgeTab, PlaygroundTab
│   └── ui/                          # shadcn components (30+ UI primitives)
├── lib/
│   ├── api.ts                       # Axios client, service factories
│   └── utils.ts                     # cn() helper (clsx + tailwind-merge)
└── types/index.ts                   # TypeScript interfaces for all domain models
```

### Data Flow
1. **Registration**: Email/Password → Creates Tenant + Account + Default Chatbot
2. **Document Ingestion**: File → LlamaParse (PDF→Markdown) → Split (strategy) → Embed → PGVector
3. **Chat**: Query → Retrieval (vector search) → LLM (with system prompt) → Response + Sources
4. **Configuration**: Tenant-scoped API keys encrypted at rest, decrypted at runtime

---

## ✅ Completed Steps

| # | Step | Status | Details |
|---|------|--------|---------|
| 1 | Repository Analysis | ✅ Complete | Analyzed 100+ files, mapped all services and endpoints |
| 2 | Project Planning | ✅ Complete | Created Plan.md with 6-phase roadmap |
| 3 | Logging Instrumentation | ✅ Complete | Added structured logging to 7 core files (auth, chat, ingestion, chatbot, conversation, documents, endpoints) |
| 4 | Agent Documentation | ✅ Complete | Created AgentWorkflow.md with Taiwan timezone (UTC+8) timestamps and work history |
| 5 | Git Commit (Phase 0) | ✅ Complete | Committed logging + docs changes |
| 6 | Verify Binary Files | ✅ Complete | All 3 files verified as intact: documents.py, rag_strategies.py, vector_store.py |
| 7 | Repository Pattern Implementation | ✅ Complete | Created 5 repository classes: ChatbotRepository, DocumentRepository, AccountRepository, TenantRepository, ConversationRepository |
| 8 | Service Refactoring | ✅ Complete | Refactored AccountService, TenantService, ChatService to depend on repositories (zero direct AsyncSession usage) |
| 9 | CRUD Endpoints Implementation | ✅ Complete | Created chatbots.py (5 endpoints), settings.py (2 endpoints), enhanced documents.py (2 endpoints) |
| 10 | Dependency Injection Setup | ✅ Complete | Updated deps.py with 8 repository providers and service constructors |

**What Works Now:**
- ✅ User registration and JWT authentication
- ✅ Chatbot CRUD (list, create, read, update, delete with full endpoints)
- ✅ Document management (list by chatbot, delete single document)
- ✅ Tenant settings management (get and update encrypted API keys)
- ✅ Document ingestion pipeline (LlamaParse → chunking → vectorization)
- ✅ RAG chat with vector search and OpenAI LLM
- ✅ Repository pattern: all DB operations isolated from services (5 repositories)
- ✅ Dependency injection: 8 repository providers in deps.py
- ✅ Multi-tenant architecture (account → tenant → chatbot → documents)
- ✅ Async database operations (SQLAlchemy + asyncpg)
- ✅ Frontend authentication flow with token persistence
- ✅ Dashboard with chatbot management UI
- ✅ Knowledge base upload and document listing
- ✅ Chat playground with source citations

---

## ❌ Incomplete Steps (Priority Order)

| # | Step | Priority | Status | Blockers | Est. Effort |
|---|------|----------|--------|----------|-------------|
| 11 | **Type Safety & Pydantic V2 Audit** | 🟠 High | Not Started | Run mypy --strict on backend/, verify all schemas use V2 patterns | 3-5 hours |
| 12 | **Unit Tests & Integration Tests** | 🟠 High | Not Started | Create test fixtures, auth/chat/ingestion service tests (≥70% coverage) | 5-7 hours |
| 13 | **CI/CD Setup (GitHub Actions)** | 🟠 High | Not Started | Create .github/workflows/ci.yml with ruff/mypy/pytest stages | 2-3 hours |
| 14 | **Error Handling & Validation** | 🟡 Medium | Partial | Centralize error responses, add error handling middleware | 2-3 hours |
| 15 | **Observability & Metrics** | 🟡 Medium | Partial | Add correlation IDs to logs, optional Prometheus exporter | 3-4 hours |
| 16 | **Security Audit** | 🟡 Medium | Not Started | Secrets validation, API key rotation, CORS hardening, rate limiting | 2-3 hours |
| 17 | **Documentation & Runbook** | 🟡 Medium | Not Started | README, setup guide, API docs, deployment instructions | 2-3 hours |
| 18 | **Performance Testing** | 🟢 Low | Not Started | Load test chat/ingestion, tune resource settings | 2-3 hours |

---

## Goals (short term)
- Stabilize backend services, ensure robust async behavior and full type coverage.
- Ensure Pydantic v2 usage, dependency injection, and environment-driven configuration.
- Harden ingestion, chunking, vectorization, and chat flows with observability (logging + errors).
- Build CI checks, tests, and a clear deployment workflow.

**Constraints & Non-goals**
- Non-goal: Rewriting third-party libraries or changing core llama-index behavior.
- Secrets must remain in environment and be validated by `pydantic-settings`.


---

## Milestones & Phases (Phase-by-Phase Breakdown)

### **Phase 0 — Repository Review & Stabilization** ✅ COMPLETE
**Status**: In Progress (5/5 tasks done)

**Tasks:**
- [x] Analyze repository structure and architecture
  - 100+ files reviewed, tech stack documented, data flow mapped
  - All service responsibilities identified
- [x] Document project goals and constraints
  - Plan.md created with 6-phase roadmap
  - Architecture decisions documented
  - 7 backend files updated with structured logging (INFO/DEBUG/WARNING/ERROR levels)
  - Files: auth.py, conversation.py, documents.py (needs repair), chat.py, chatbot.py, ingestion.py, auth (service)
- [x] Create work history documentation
 [x] Add logging instrumentation to core services
  - Agent.md created with 9 timestamped entries (UTC ISO 8601)
  - Status tracking for all completed work
- [x] Commit Phase 0 changes
  - Git commit with logging + documentation

**Deliverables:** ✅ Plan.md, ✅ Agent.md, ✅ Logging Infrastructure

**Timeline**: 1–2 days ✅ Complete

---

### **Phase 1 — Type Safety & Pydantic V2 Migration** ❌ NOT STARTED
**Status**: Pending (0/5 tasks done)

**Tasks:**
- [ ] Audit all Pydantic models in `app/schemas.py`
  - Check for V1 patterns (old Config class, @validator decorators)
  - Identify fields needing `Annotated[]` for complex validators
  - Ensure all models use `model_config` dict (V2 style)
  
- [ ] Verify async signatures across services
  - All database operations must use `AsyncSession`
  - All file I/O must use `aiofiles` or equivalent
  - No blocking calls in request handlers
  
- [ ] Add missing type hints
  - Services: add return types and parameter hints
  - Endpoints: fully annotate request/response models
  - Database layer: type dict/JSON fields explicitly
  
- [ ] Run type checker in strict mode
  - `mypy --strict app/` on all backend code
  - Fix all type violations
  
- [ ] Update migration scripts
  - Verify Alembic models align with SQLAlchemy type definitions

**Blockers:**
- Binary files (documents.py, rag_strategies.py, vector_store.py) must be repaired first

**Deliverables:**
- Type coverage report (100% on critical modules)
- Updated schemas with Pydantic V2 patterns
- mypy strict mode passing

**Timebox**: 3–5 days

**Next Action**: Repair 3 binary files, then run mypy audit

### Repository Pattern & TDD Refactor (Recommended)

To make the codebase highly testable and to enable fast TDD cycles, introduce a Repository layer that isolates all database operations from the Service layer. This will let services be instantiated with lightweight fake repositories in tests (millisecond-level), avoiding complex AsyncSession mocks.

Goals:
- Separate DB access (CRUD/selects) into `repositories/*` classes (e.g., `ChatbotRepository`, `DocumentRepository`, `VectorRepository`).
- Services (e.g., `IngestionService`, `ChatService`, `ChatbotService`) depend on repository interfaces instead of `AsyncSession`.
- Provide a small set of repository interfaces (or abstract base classes) to enable Fake implementations for tests.

Recommended Steps (TDD-first):
1. Define repository interfaces for core aggregates:
  - `ChatbotRepository` with `get_by_id`, `get_by_public_id`, `list_for_tenant`, `create`, `update`, `delete`.
  - `DocumentRepository` with `create`, `delete_by_id`, `list_by_chatbot_id`.
  - `VectorRepository` (or keep `VectorStoreService`) to abstract vector-store operations.

2. Implement concrete Repositories that wrap SQLAlchemy `AsyncSession` calls and return domain models or DTOs.

3. Refactor `IngestionService` to accept `document_repo: DocumentRepository` and `chatbot_repo: ChatbotRepository` (or a single `ChatbotRepository`) instead of raw `db: AsyncSession`.

4. Write tests using Fake Repositories (in-memory dict-backed implementations) and run them:
  - Test: FakeChatbotRepository returns a chatbot object when `get_by_id` called.
  - Test: IngestionService.ingest_file(chatbot, file, ...) uses fake repos and fake vector-store to assert behavior without DB.

5. Incrementally replace service DB calls with repository calls and keep tests green.

Acceptance Criteria:
- Repository interfaces defined under `backend/app/repositories/`.
- At least one service (`IngestionService`) refactored to depend on repository interfaces.
- A test suite using `FakeRepository` for `IngestionService` exists and runs in <100ms locally without Docker.

Notes:
- This work complements the Phase 1 type-safety changes: repository methods should be typed (return types annotated). Use `Protocol` or ABC for interfaces where helpful.
- Keep the existing layered architecture (endpoints -> services -> repositories -> db) unchanged for runtime wiring (use `deps.py` to inject concrete implementations).

---

### **Phase 2 — Tests, Static Analysis & CI** ❌ NOT STARTED
**Status**: Pending (0/4 tasks done)

**Tasks:**
- [ ] Repair binary files (URGENT)
  - Recreate `backend/app/api/endpoints/documents.py`
    - POST /document/ingest (file upload handler)
    - DELETE /document/{id} (document removal)
    - Integrate with IngestionService
    - Add logging for all operations
  
  - Recreate `backend/app/core/rag_strategies.py`
    - `create_chat_engine()` factory function
    - Integration with VectorStoreIndex, LLM, filters
    - Support for different chunking strategies
  
  - Recreate/fix `backend/app/services/vector_store.py`
    - Vector store utility functions (if custom logic needed)
    - Or verify it's just re-exporting from rag_factory.py

- [ ] Implement missing backend endpoints
  - `GET/POST /chatbots` (list and create)
  - `GET/PATCH/DELETE /chatbots/{id}` (retrieve, update, delete)
  - `GET /chatbots/{id}/documents` (list documents by chatbot)
  - `DELETE /document/{id}` (delete single document)
  - `GET/PATCH /tenant/settings` (API key management)
  - `GET /stats/overview` (usage statistics)
  
  - All endpoints must:
    - Include proper error handling
    - Add logging (request received, success, errors)
    - Validate tenant scoping (no cross-tenant access)
    - Return appropriate HTTP status codes

- [ ] Write unit tests for core services
  - **AuthService**:
    - `register()` - success, email duplicate, validation errors
    - `authenticate()` - valid credentials, invalid password, not found
    - `get_active_user_by_token()` - valid token, expired, invalid
  
  - **IngestionService**:
    - `ingest_file()` - successful chunking, LlamaParse mock, vector store write
    - Error handling: missing keys, file parsing failures
    - Mock: LlamaParse, vector store, DB operations
  
  - **ChatService**:
    - `chat()` - successful query, vector retrieval, LLM generation
    - Error handling: chatbot not found, missing API keys
    - Mock: VectorStoreIndex, LLM, DB session
  
  - **ChatbotService**:
    - `get_chatbot_by_id()`, `get_chatbot_by_public_id()`
    - `create_chatbot()` - success, validation
    - Mock: SQLAlchemy session, relationship loading
  
  - **Target**: ≥70% coverage on critical modules

- [ ] Write integration tests (lightweight)
  - Use in-memory SQLite + async fixtures
  - OR mock asyncpg/SQLAlchemy at session level
  - Test: auth flow (register → login), document upload → chat retrieval
  - Single test per major workflow

- [ ] Add static analysis & CI
  - `pyproject.toml` scripts:
    - `lint`: ruff check + mypy
    - `test`: pytest with coverage
    - `format`: ruff format
  
  - GitHub Actions workflow (`.github/workflows/ci.yml`):
    - Matrix: Python 3.11+
    - Lint stage (ruff, mypy)
    - Test stage (pytest, coverage >70%)
    - Enforce on PRs

**Blockers:**
- Binary files must be fixed first
- Missing endpoints prevent full integration testing

**Deliverables:**
- ✅ Repaired binary files
- ✅ All CRUD endpoints implemented
- ✅ Unit tests (≥70% coverage)
- ✅ Passing CI pipeline on main branch
- ✅ GitHub Actions workflow running on PRs

**Timebox**: 3–7 days

**Next Action**: Start with binary file repair, then endpoints, then tests

---

### **Phase 3 — Observability & Error Handling** ❌ NOT STARTED
**Status**: Pending (0/3 tasks done)

**Tasks:**
- [ ] Centralize error handling
  - Custom exception classes (APIError, ValidationError, NotFoundError)
  - Unified error response format (detail, code, timestamp)
  - Middleware for catching unhandled exceptions → 500 responses
  
- [ ] Enhance structured logging
  - Request/response logging middleware
  - Correlation IDs for tracing (request → ingestion → chat)
  - JSON logging output option (controlled by env: LOG_FORMAT=json)
  
- [ ] Add metrics/observability
  - Prometheus exporter (optional):
    - Chat request duration, tokens used
    - Ingestion throughput, chunk count
    - Vector store query latency
  - OR simple counter logs for MVP
  
- [ ] Integrate Sentry (optional, env-gated)
  - Already configured in `app/main.py`
  - Verify error event capture, breadcrumbs
  - Set up team notifications

**Blockers:** None

**Deliverables:**
- Centralized error handling module
- Structured logs (with correlation IDs)
- Metrics dashboard or Prometheus scrape config

**Timebox**: 2–4 days

---

### **Phase 4 — Security & Secrets Management** ❌ NOT STARTED
**Status**: Pending (0/4 tasks done)

**Tasks:**
- [ ] Secrets validation
  - All secrets must be read via `pydantic-settings` (`app/core/config.py`)
  - Add helpful error messages if required secrets are missing
  - Validate format/length of API keys at startup
  
- [ ] API key encryption & rotation
  - Review encryption in `app/core/security.py` (currently uses Fernet)
  - Document how to rotate ENCRYPTION_KEY without data loss
  - Add instructions to runbook
  
- [ ] CORS & origin validation
  - Hardening CORS config for production (currently allows "*")
  - Only allow registered chatbot domains
  
- [ ] Rate limiting (optional)
  - Add rate limit middleware for `/conversation/chat` and `/document/ingest`
  - Per-tenant or per-IP limits
  
- [ ] Role-based access control (optional)
  - Verify account.is_superuser is checked for admin endpoints
  - Add permission decorators if needed

**Blockers:** None

**Deliverables:**
- Security checklist + findings
- Updated config validation
- Runbook with key rotation instructions

**Timebox**: 2–4 days

---

### **Phase 5 — Scaling & Deployment** ❌ NOT STARTED
**Status**: Pending (0/4 tasks done)

**Tasks:**
- [ ] Containerization audit
  - Review `Dockerfile` (uv-based, multi-stage optimization)
  - Verify `.dockerignore` excludes unnecessary files
  - Test build time and image size
  
- [ ] Database & migrations strategy
  - Verify Alembic runs automatically on startup (or manual step)
  - Test migration rollback safety
  - Document migration workflow
  
- [ ] Resource tuning
  - SQLAlchemy pool settings (pool_size, max_overflow, recycle timeout)
  - Vector store batch size for large ingestions
  - Uvicorn worker count based on CPU cores
  
- [ ] Load testing
  - Simulate concurrent chat requests
  - Measure ingestion throughput with large documents
  - Identify bottlenecks (DB, vector store, LLM rate limits)
  
- [ ] Deployment playbook
  - Docker Compose setup for staging
  - Environment variable checklist
  - Health check and readiness probes
  - Graceful shutdown procedures

**Blockers:** None

**Deliverables:**
- Deployment playbook (README.md)
- Resource tuning recommendations
- Load test results & bottleneck analysis

**Timebox**: 3–7 days

---

## Detailed Task Breakdown (Actionable)

### **URGENT: Repair Binary Files** (Do This First)
```bash
# 1. backend/app/api/endpoints/documents.py
# 2. backend/app/core/rag_strategies.py
 **Tasks:**
```

**Why this matters:**
- `documents.py` contains the file ingestion endpoint (POST /document/ingest)
- `rag_strategies.py` contains the `create_chat_engine()` factory needed for chat
- `vector_store.py` may contain utility functions or re-exports

---

### **NEXT: Implement Missing Endpoints** (After Binary Repair)

**Chatbot CRUD:**
```python
# GET /chatbots - List all chatbots for current tenant
# POST /chatbots - Create new chatbot
# GET /chatbots/{id} - Retrieve chatbot details
# PATCH /chatbots/{id} - Update chatbot (RAG config, widget config)
# DELETE /chatbots/{id} - Delete chatbot (cascade delete documents/conversations)
```

```python
# GET /chatbots/{id}/documents - List documents for chatbot
# DELETE /document/{id} - Delete single document
```

**Tenant Settings:**
```python
# GET /tenant/settings - Retrieve current tenant's API keys (masked)
# PATCH /tenant/settings - Update API keys (encrypted storage)
```

**Statistics (Optional MVP):**
```python
# GET /stats/overview - Return usage stats (currently mocked in frontend)
```

---

### **THEN: Write Tests** (Parallel with endpoints)

**Test files to create:**
```
backend/tests/
├── conftest.py                # Fixtures (async DB, auth tokens, services)
├── test_auth_service.py       # AuthService unit tests
├── test_chat_service.py       # ChatService unit tests
├── test_ingestion_service.py  # IngestionService unit tests
├── test_chatbot_service.py    # ChatbotService unit tests
└── test_integration.py        # End-to-end flows (register → upload → chat)
```

---

### **FINALLY: Setup CI** (Automate everything)

**GitHub Actions workflow (.github/workflows/ci.yml):**
```yaml
name: CI
on: [pull_request, push]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install ruff mypy
      - run: ruff check backend/
      - run: mypy --strict backend/
  
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg18
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install pytest pytest-cov pytest-asyncio
      - run: pytest backend/tests/ --cov=backend/app --cov-report=term-missing
      - run: exit 1 if coverage < 70%
```

---

## Acceptance Criteria

**Phase 0 (Complete):**
- ✅ Plan.md created with full roadmap
- ✅ Agent.md created with work history
- ✅ Logging added to 7 core service files
- ✅ All changes committed to git

**Phase 1 (Type Safety):**
- All Pydantic models pass `mypy --strict`
- Zero type violations in `app/schemas.py`, `app/models/*`, `app/services/*`
- All async operations properly typed (`AsyncSession`, `Coroutine`, etc.)
- README updated with type-checking setup

**Phase 2 (Tests & CI):**
- ✅ 3 binary files repaired/recreated with full functionality
- ✅ All CRUD endpoints implemented (chatbots, documents, settings)
- Unit tests: ≥70% coverage on critical modules (auth, chat, ingestion, chatbot)
- All tests passing locally and in CI
- GitHub Actions workflow running on PRs, enforcing lint/type/test

**Phase 3 (Observability):**
- Centralized error handling with consistent response format
- Structured logs with correlation IDs throughout request lifecycle
- Optional Prometheus metrics endpoint (or detailed logs)
- Sentry integration verified in staging

**Phase 4 (Security):**
- All required secrets validated at startup with helpful error messages
- API key encryption/decryption working end-to-end
- CORS hardened for production
- Role-based access control for admin endpoints

**Phase 5 (Scaling):**
- Docker image builds and runs successfully
- Database migrations execute safely
- Load testing results documented (bottlenecks identified)
- Deployment playbook includes all necessary steps

---

## Recommended Execution Order

### **Week 1: Phase 0 + Phase 2 Foundation** (5-7 days)
1. **Day 1-2**: Repair 3 binary files
   - `documents.py` - file upload/delete endpoints
   - `rag_strategies.py` - chat engine factory
   - `vector_store.py` - vector utilities
   
2. **Day 2-3**: Implement all missing CRUD endpoints
   - Chatbot management (list, create, update, delete)
   - Document management (list, delete)
   - Tenant settings (get, update)
   - All with proper logging and error handling
   
3. **Day 4-5**: Write unit + integration tests
   - Auth service (3 test functions)
   - Chat service (3 test functions)
   - Ingestion service (3 test functions)
   - Chatbot service (2 test functions)
   - Integration test (full flow: register → upload → chat)
   
4. **Day 5-6**: Setup CI/CD
   - Create `.github/workflows/ci.yml`
   - Add `pyproject.toml` scripts (lint, test, format)
   - Run locally, verify pass/fail scenarios
   
5. **Day 7**: Commit Phase 2, update Agent.md

### **Week 2: Phase 1 + Phase 3** (4-5 days)
1. **Day 1-2**: Type safety audit
   - Run `mypy --strict backend/` find violations
   - Fix Pydantic V2 compliance issues
   - Add missing type hints
   
2. **Day 2-3**: Enhance observability
   - Add error handling middleware
   - Implement correlation IDs
   - Optional: Prometheus exporter
   
3. **Day 3-4**: Security audit
   - Secrets validation startup checks
   - Key rotation documentation
   - CORS hardening

### **Week 3: Phase 4 + Phase 5** (4-5 days)
1. **Day 1**: Scaling & performance
   - Load test chat/ingestion
   - Tune resource settings
   
2. **Day 2-3**: Documentation
   - README.md (dev setup, deployment)
   - Runbook (operations, troubleshooting)
   - API documentation (endpoints, examples)
   
3. **Day 3-4**: Final validation
   - Full end-to-end testing
   - Security checklist review
   - Performance baseline established

**Total Estimated Timeline**: 3-4 weeks (17-22 days)

---

## Quick Start (What to Do Now)

### **Immediate Next Steps (Do This Today):**

```bash
# 1. Create backup of current state
git checkout -b feature/phase2-foundation

# 2. Identify binary file issues
file backend/app/api/endpoints/documents.py
file backend/app/core/rag_strategies.py
file backend/app/services/vector_store.py

# 3. Start with documents.py repair
# This file should contain POST /document/ingest endpoint
# See: backend/app/services/ingestion.py for reference on expected imports
```

### **What I'm Ready To Do:**
- [ ] Repair all 3 binary files with full implementations
- [ ] Implement all 6-8 missing endpoints
- [ ] Create test fixtures and unit test suite
- [ ] Setup GitHub Actions CI workflow
- [ ] Type audit and Pydantic V2 compliance check
- [ ] Security audit and hardening
- [ ] Performance testing and optimization

### **What Requires Your Input:**
- ✅ Confirm binary file repair approach (recreate from scratch vs. restore from backup)
- ✅ Approve endpoint specifications (request/response formats)
- ✅ Test environment setup (test DB credentials, Sentry project ID)
- ✅ Deployment target (Render.com, Docker registry, Kubernetes?)

---

## Summary Table: All Tasks

| Phase | Task | Status | Days | Start | End |
|-------|------|--------|------|-------|-----|
| 0 | Repo analysis | ✅ | 2 | Day -2 | Today |
| 0 | Plan + Agent docs | ✅ | 1 | Day -1 | Today |
| 0 | Logging infra | ✅ | 1 | Day 0 | Today |
| 2 | Repair binary files | ❌ | 2 | Day 1 | Day 2 |
| 2 | Implement endpoints | ❌ | 2 | Day 2 | Day 4 |
| 2 | Unit + int tests | ❌ | 2 | Day 4 | Day 6 |
| 2 | CI/CD setup | ❌ | 1 | Day 6 | Day 7 |
| 1 | Type safety | ❌ | 2 | Day 8 | Day 9 |
| 3 | Observability | ❌ | 2 | Day 10 | Day 11 |
| 4 | Security | ❌ | 1 | Day 12 | Day 12 |
| 5 | Scaling | ❌ | 2 | Day 13 | Day 14 |
| - | Documentation | ❌ | 2 | Day 15 | Day 17 |
| - | Validation | ❌ | 1 | Day 18 | Day 18 |

**Critical Path**: Phase 0 → Phase 2 Foundation (binary + endpoints + tests + CI) → Full validation

---

*Last Updated: 2025-12-07 by Agent*
*Next Review: Upon completion of Phase 2 Foundation*