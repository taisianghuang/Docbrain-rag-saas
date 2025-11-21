import os
import io
from uuid import uuid4
from typing import List

from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import StreamingResponse, JSONResponse

from pypdf import PdfReader

import chromadb
# ChromaDB 0.4+ 不需要舊式的 Settings 設定

# 新版 LangChain Import 路徑
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

# 新版 OpenAI Client (v1.0+)
from openai import AsyncOpenAI

router = APIRouter()

# 設定儲存路徑
CHROMA_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")

# Lazy loading globals
_chroma_client = None
_collection = None
_embeddings = None


def get_chroma_collection():
    """取得 ChromaDB Collection (單例模式)"""
    global _chroma_client, _collection
    if _chroma_client is None:
        # ChromaDB 0.4+ 的新寫法：直接用 PersistentClient
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    if _collection is None:
        # 取得或建立集合
        _collection = _chroma_client.get_or_create_collection(name="documents")
        
    return _collection


def get_embeddings():
    """取得 OpenAI Embeddings 物件"""
    global _embeddings
    if _embeddings is None:
        # 使用新版 langchain-openai 套件
        _embeddings = OpenAIEmbeddings()
    return _embeddings


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """從 PDF 提取文字"""
    reader = PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        text_parts.append(text)
    return "\n".join(text_parts)


@router.post("/ingest")
async def ingest(files: List[UploadFile] = File(...)):
    """接收 PDF/TXT 檔案，切割後存入 ChromaDB。"""
    docs = []
    metadatas = []

    for f in files:
        content = await f.read()
        text = ""
        
        # 判斷檔案類型
        if f.filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(content)
        else:
            try:
                text = content.decode("utf-8")
            except Exception:
                text = content.decode("latin-1", errors="ignore")

        if not text.strip():
            continue

        # 使用新版 LangChain 的 Splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200
        )
        chunks = splitter.split_text(text)

        for idx, c in enumerate(chunks):
            docs.append(c)
            metadatas.append({"source": f.filename, "chunk": idx})

    if not docs:
        return JSONResponse({"inserted": 0})

    # 產生向量 (Embeddings)
    embeddings = get_embeddings()
    embs = embeddings.embed_documents(docs)

    # 存入資料庫
    collection = get_chroma_collection()
    ids = [str(uuid4()) for _ in docs]
    
    collection.add(
        documents=docs, 
        metadatas=metadatas,
        ids=ids, 
        embeddings=embs
    )

    return {"inserted": len(docs)}


@router.post("/chat")
async def chat(request: Request):
    """接收 {message, history}，回傳串流回應 (Streaming Response)。"""
    payload = await request.json()
    message = payload.get("message", "")
    # history = payload.get("history", []) # 暫時沒用到 history，未來可加入 Context

    if not message:
        return JSONResponse({"error": "message required"}, status_code=400)

    # 1. 搜尋相關文件 (RAG)
    collection = get_chroma_collection()
    context_text = ""
    
    try:
        # 使用 Embeddings 進行語意搜尋 (Query)
        embeddings = get_embeddings()
        query_vec = embeddings.embed_query(message)
        
        results = collection.query(
            query_embeddings=[query_vec],
            n_results=4,
            include=["documents"]
        )
        
        if results and results['documents']:
            # 扁平化 list
            hits = results['documents'][0]
            context_text = "\n---\n".join(hits)
    except Exception as e:
        print(f"Search Error: {e}")
        context_text = ""

    # 2. 準備 Prompt
    system_prompt = (
        "You are a helpful assistant. Answer questions using the provided context only. "
        "If you don't know, say so.\n\n"
        f"Context:\n{context_text}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    # 3. 使用新版 OpenAI Async Client 進行串流
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        return JSONResponse({"error": "OPENAI_API_KEY not configured"}, status_code=500)

    # 初始化 Async Client
    aclient = AsyncOpenAI(api_key=openai_api_key)

    async def event_stream():
        try:
            # 新版 API 呼叫方式 (v1.0+)
            stream = await aclient.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                stream=True
            )
            
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
            
            # 結束時可以傳一個換行確保格式
            yield "\n"
            
        except Exception as e:
            yield f"[ERROR] {str(e)}"

    return StreamingResponse(event_stream(), media_type="text/plain")