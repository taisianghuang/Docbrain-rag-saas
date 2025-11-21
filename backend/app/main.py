import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router

app = FastAPI(title="RAG-as-a-Service Backend")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount compiled widget static files. Try several likely locations.
possible_paths = [
    Path(os.getcwd()) / "widget_dist",  # when mounted in container
    Path(__file__).resolve().parents[2] / "widget" / "dist",  # repo layout
]

mounted = False
for p in possible_paths:
    if p.exists() and p.is_dir():
        app.mount("/static", StaticFiles(directory=str(p)), name="static")
        mounted = True
        break

if not mounted:
    # If widget dist isn't available yet, create an in-memory placeholder mount path
    placeholder = Path(os.getcwd()) / "_widget_placeholder"
    placeholder.mkdir(exist_ok=True)
    (placeholder / "widget.js").write_text("// widget not built yet")
    app.mount("/static", StaticFiles(directory=str(placeholder)), name="static")

app.include_router(api_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
