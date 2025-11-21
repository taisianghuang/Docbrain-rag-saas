import os
import io
import json
from uuid import uuid4
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, JSONResponse

from pypdf import PdfReader

import chromadb
from chromadb.config import Settings

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings

import openai

router = APIRouter()

# Initialize Chroma client and embeddings lazily
CHROMA_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
_chroma_client = None
_collection = None
_embeddings = None


def get_chroma_collection():
    global _chroma_client, _collection
    if _chroma_client is None:
        _chroma_client = chromadb.Client(
            Settings(chroma_db_impl="duckdb+parquet", persist_directory=CHROMA_DIR))
    if _collection is None:
        try:
            _collection = _chroma_client.get_collection(name="documents")
        except Exception:
            _collection = _chroma_client.create_collection(name="documents")
    return _collection


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings()
    return _embeddings


def extract_text_from_pdf(file_bytes: bytes) -> str:
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
    """Accept PDF/TXT files, chunk them, embed and store into ChromaDB."""
    docs = []
    metadatas = []

    for f in files:
        content = await f.read()
        text = ""
        if f.filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(content)
        else:
            try:
                text = content.decode("utf-8")
            except Exception:
                text = content.decode("latin-1", errors="ignore")

        if not text.strip():
            continue

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_text(text)

        for idx, c in enumerate(chunks):
            docs.append(c)
            metadatas.append({"source": f.filename, "chunk": idx})

    if not docs:
        return JSONResponse({"inserted": 0})

    embeddings = get_embeddings()
    embs = embeddings.embed_documents(docs)

    collection = get_chroma_collection()
    ids = [str(uuid4()) for _ in docs]
    collection.add(documents=docs, metadatas=metadatas,
                   ids=ids, embeddings=embs)
    # persist handled by chroma client implementation

    return {"inserted": len(docs)}


@router.post("/chat")
async def chat(request: Request):
    """Accepts {message, history}. Retrieves context and streams back model output."""
    payload = await request.json()
    message = payload.get("message", "")
    history = payload.get("history", [])

    if not message:
        return JSONResponse({"error": "message required"}, status_code=400)

    embeddings = get_embeddings()
    collection = get_chroma_collection()

    # similarity search: use query API
    try:
        results = collection.query(query_texts=[message], n_results=4, include=[
                                   "documents", "metadatas"])
        docs = []
        if results and len(results.get("documents", [])):
            hits = results["documents"][0]
            docs = [h for h in hits if h]
    except Exception:
        docs = []

    context = "\n---\n".join(docs)

    system_prompt = (
        "You are a helpful assistant that answers questions using the provided context. "
        "If the answer is not contained in the context, say you don't know and offer to help in other ways.\n\nContext:\n" + context
    )

    # Prepare messages for OpenAI
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        return JSONResponse({"error": "OPENAI_API_KEY not configured on server"}, status_code=500)
    openai.api_key = openai_api_key

    async def event_stream():
        # Use OpenAI streaming to yield tokens as they arrive
        try:
            # NOTE: openai.ChatCompletion.create with stream True is a blocking generator.
            # Using the sync generator in an async context is acceptable here because FastAPI
            # will run the generator in a threadpool. We yield plain text chunks.
            for chunk in openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, stream=True):
                if not chunk:
                    continue
                choices = chunk.get("choices")
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                content = delta.get("content")
                if content:
                    yield content
            yield "\n"
        except Exception as e:
            yield f"[ERROR] {str(e)}"

    return StreamingResponse(event_stream(), media_type="text/plain")
