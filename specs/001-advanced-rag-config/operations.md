# Operations Checklist: Advanced RAG Config

Monitoring & SLOs
- Queue depth (per tenant) and consumer lag
- Worker count and throughput
- Embedding cache hit-rate
- Ingestion success rate and dead-letter counts
- API latency for save/get endpoints

Alerts
- DLQ threshold exceeded
- Reranker model unavailable (fallback used)
- Reprocessing backlog growth beyond SLO

Runbooks
- How to scale consumers
- How to rotate provider API keys
- How to trigger reprocessing safely
