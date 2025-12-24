# Phase 0 — Research: Decisions & Rationale

This document resolves outstanding clarifications from the Implementation Plan and the Constitution Check: queue selection, property-testing framework, and performance SLOs.

1) Queue selection (Kafka vs alternatives)

- Decision: Implement a pluggable Queue Adapter interface (`backend/app/processing/queue_adapter.py`) that abstracts enqueue/consume semantics. For the MVP and developer workflows use a lightweight async in-memory queue or Redis-backed queue if operations prefers. Roadmap: provide an ops playbook to deploy Kafka and switch the adapter to a Kafka-backed implementation before broad rollout.

- Rationale: The constitution requires Kafka for production-grade async reliability, but the repository and current infra (`docker-compose.yml`) do not include Kafka. Building an adapter removes a hard dependency on a particular queue and enables development to progress without infra changes while preserving the option to adopt Kafka for production.

- Alternatives considered:
  - Add Kafka now in `docker-compose`: Pros — matches constitution; Cons — requires ops/config time and increases complexity for early development and CI.
  - Use Redis Streams as a drop-in durable queue: Pros — simpler to add and many teams have Redis; Cons — different semantics from Kafka and may require lifecycle changes later.

2) Property-testing framework (Hypothesis)

- Decision: Add `hypothesis` to the backend dev/test dependencies and scaffold property-test templates that correspond to the design doc properties. Use `pytest` as test runner.

- Rationale: Constitution mandates property-based testing. `pytest` is already present; adding `hypothesis` is low friction and enables implementing the property tests required by the design doc.

- Alternatives considered:
  - Use only unit tests + integration tests: faster to adopt, but would violate the constitution requirement for property tests.

3) Performance goals and SLOs

- Decision: Use the measurable outcomes in the spec as the initial SLOs and convert them into concrete, testable performance targets during Phase 1 design. Example SLOs:
  - Ingestion latency: 95% of single-document ingestions reach `processing` within 30s under baseline worker counts.
  - Pipeline availability: 99% during business hours.

- Rationale: These map directly to measurable outcomes in the spec and will guide the worker sizing, queue configuration, and monitoring.

4) Secrets and tenant isolation

- Decision: Verify and adopt the existing `backend/app/core/security.py` patterns for secret encryption. If missing, implement tenant-scoped encryption via symmetric encryption with tenant-specific keys stored in the DB encrypted by a master key.

- Rationale: Constitution requires encrypted per-tenant secrets and auditability.

5) Model provider integration and API key validation

- Decision: Implement provider-agnostic `ModelProvider` interfaces and `ConfigValidator.validate_api_keys` that attempt a lightweight connectivity check (e.g., metadata query) at validation time. Do not store raw API keys; store references/IDs to encrypted secrets.

- Rationale: Prevent invalid configuration saves and allow early detection of missing/invalid credentials.

Conclusion

All NEEDS-CLARIFICATION items are resolved with the above decisions. The chosen approach emphasizes an adapter-based architecture to avoid blocking development while preserving constitution goals. Phase 1 (design) will convert SLOs to concrete benchmarks and implement the queue adapter and property-test scaffolding.

**Decisions summary**

- Queue: pluggable adapter; directly use Kafka as production rollout.
- Property tests: add `hypothesis` and scaffold tests.
- Performance: use spec measurable outcomes as SLOs; refine in Phase 1.
- Secrets: verify and enforce tenant-scoped encrypted storage.
- Model provider validation: lightweight connectivity checks on save, store references to encrypted secrets.
