from fastapi.testclient import TestClient


def test_save_and_get_rag_config(client: TestClient):
    payload = {
        "embedding": {
            "model_name": "text-embedding-3-small",
            "provider": "openai",
            "model_params": {},
            "api_key_ref": "tenant_openai_key",
            "batch_size": 100,
        },
        "chunking": {
            "strategy": "standard",
            "chunk_size": 512,
            "chunk_overlap": 100,
            "semantic_threshold": 0.8,
            "window_size": 3,
            "respect_document_structure": True,
        },
        "retrieval": {
            "strategy": "vector",
            "top_k_initial": 10,
            "top_k_final": 5,
            "hybrid_weights": {"semantic": 0.7, "bm25": 0.3},
            "enable_reranking": False,
            "reranker_model": None,
            "similarity_threshold": 0.7,
        },
        "llm": {
            "model_name": "gpt-4o-mini",
            "provider": "openai",
            "temperature": 0.1,
            "max_tokens": 1000,
            "system_prompt": None,
            "api_key_ref": "tenant_openai_key",
        },
        "visual_processing": None,
        "performance_settings": {
            "cache_embeddings": True,
            "batch_processing": True,
            "parallel_workers": 4,
            "memory_limit_mb": 2048,
        },
    }

    resp = client.post("/api/rag-config/test-chatbot", json=payload)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp2 = client.get("/api/rag-config/test-chatbot")
    assert resp2.status_code == 200
    body = resp2.json()
    assert body["retrieval"]["strategy"] == "vector"
    assert body["embedding"]["model_name"] == "text-embedding-3-small"
