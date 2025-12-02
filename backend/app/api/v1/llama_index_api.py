from app.api import crud as api_crud
from app.api.deps import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.openai import OpenAI
from llama_cloud_services import LlamaParse

_HAVE_LLAMA_PARSE = True


router = APIRouter()

# --- Pydantic Models (保持不變) ---


class IngestResponse(BaseModel):
    ingested: int


class ChatRequest(BaseModel):
    client_id: str
    query: str
    top_k: int = 3


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]


class IndexManager:
    """
    LlamaIndex v0.14.8 Compatible Manager
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._docs: List[Dict[str, Any]] = []

        # 檢查 API Key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Warning: OPENAI_API_KEY not found. Chat functionality will fail.")

        # 設定全域 Settings
        try:
            # 初始化 OpenAI (gpt-3.5-turbo 或 gpt-4o)
            self.llm = OpenAI(model="gpt-3.5-turbo", api_key=api_key)

            # 將其綁定到全域設定，這樣後續建立 Index 時會自動使用這個 LLM
            Settings.llm = self.llm
        except Exception as e:
            print(f"LLM Initialization failed: {e}")
            self.llm = None

    async def add_text(self, client_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        async with self._lock:
            doc_id = str(uuid.uuid4())
            md = metadata.copy() if metadata else {}
            # Metadata Filtering 核心：標記 client_id
            md["client_id"] = client_id
            self._docs.append({"id": doc_id, "text": text, "metadata": md})

    async def add_bytes(self, client_id: str, content_bytes: bytes, metadata: Optional[Dict[str, Any]] = None) -> None:
        try:
            text = content_bytes.decode("utf-8")
        except Exception:
            text = "<binary content: decoding failed>"
        await self.add_text(client_id, text, metadata=metadata)

    async def query(self, client_id: str, query: str, top_k: int = 3) -> Dict[str, Any]:
        async with self._lock:
            # 1. 在記憶體中過濾該租戶的文件 (Simulating Metadata Filtering)
            tenant_docs_data = [d for d in self._docs if d.get(
                "metadata", {}).get("client_id") == client_id]

        if not tenant_docs_data:
            return {"answer": "No documents found for this client.", "sources": []}

        # 2. 轉換為 LlamaIndex 的 Document 物件
        docs = [Document(text=d["text"], metadata=d["metadata"])
                for d in tenant_docs_data]

        try:
            # 3. 建立臨時索引
            # 它會自動讀取我們在 __init__ 設定好的 Settings.llm
            index = VectorStoreIndex.from_documents(docs)

            # 4. 建立查詢引擎
            query_engine = index.as_query_engine(similarity_top_k=top_k)

            # 5. 執行 RAG 查詢
            response = query_engine.query(query)

            # 6. 整理回應
            answer = str(response)
            sources = []

            # 提取來源 (Source Nodes)
            if response.source_nodes:
                for node in response.source_nodes:
                    sources.append(node.node.get_content())

            return {"answer": answer, "sources": sources}

        except Exception as e:
            print(f"Query Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"RAG Error: {str(e)}"
            )


# --- Global Instance Management ---
_INDEX_MANAGER: Optional[IndexManager] = None


def get_index_manager() -> IndexManager:
    global _INDEX_MANAGER
    if _INDEX_MANAGER is None:
        _INDEX_MANAGER = IndexManager()
    return _INDEX_MANAGER


# --- API Endpoints ---
@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    client_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    mgr = get_index_manager()
    count = 0
    filename = "text_input"

    if file:
        content = await file.read()
        filename = file.filename

        # If LlamaParse is available, try to parse file into multiple text chunks
        parsed_any = False
        # Lookup tenant config (client) and retrieve its API key
        client = await api_crud.get_client(db, str(client_id))
        if client is None:
            raise HTTPException(status_code=404, detail="client_id not found")

        tenant_api_key = None
        # NOTE: currently stored API key is expected to be plaintext in `api_key` column.
        # For production, store encrypted values and decrypt here.
        tenant_api_key = getattr(
            client, "api_key", None) or os.getenv("OPENAI_API_KEY")
        if _HAVE_LLAMA_PARSE:
            try:
                parser = LlamaParse(api_key=tenant_api_key)
                # Prefer a generic `parse` API, fall back to `parse_bytes` if needed
                if hasattr(parser, "parse"):
                    parsed = parser.parse(content, filename=filename)
                elif hasattr(parser, "parse_bytes"):
                    parsed = parser.parse_bytes(content, filename=filename)
                else:
                    parsed = None

                if parsed:
                    # Normalize parsed into list of strings
                    if isinstance(parsed, (list, tuple)):
                        texts = []
                        for item in parsed:
                            if isinstance(item, dict):
                                txt = item.get("text") or item.get(
                                    "content") or str(item)
                            else:
                                txt = getattr(item, "text", None) or getattr(
                                    item, "content", None) or str(item)
                            texts.append(txt)
                    else:
                        txt = getattr(parsed, "text", None) or getattr(
                            parsed, "content", None) or str(parsed)
                        texts = [txt]

                    for t in texts:
                        await mgr.add_text(client_id, t, metadata={"filename": filename})
                    count = len(texts)
                    parsed_any = True
            except Exception:
                parsed_any = False

        if not parsed_any:
            # Fallback: store as single text document (existing behavior)
            await mgr.add_bytes(client_id, content, metadata={"filename": filename})
            count = 1
    elif text:
        await mgr.add_text(client_id, text, metadata={"filename": "raw_text"})
        count = 1
    else:
        raise HTTPException(
            status_code=400, detail="Either file or text is required")

    return {"ingested": count}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    mgr = get_index_manager()
    res = await mgr.query(req.client_id, req.query, top_k=req.top_k)
    return {"answer": res.get("answer", ""), "sources": res.get("sources", [])}
