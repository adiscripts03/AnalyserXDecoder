import os
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root and src to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT_DIR / "src"
STATIC_DIR = ROOT_DIR / "static"

for p in [str(ROOT_DIR), str(SRC_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from rag_app.main import (
    ingest_webpage,
    ingest_pdf_file,
    answer_query,
    clear_collection,
    DEFAULT_COLLECTION,
    DEFAULT_PROVIDER,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_MISTRAL_MODEL,
)

app = FastAPI(
    title="AnalyserXDecoder API",
    description="RAG Document Intelligence Web API",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class UrlIngestRequest(BaseModel):
    url: str
    collection_name: Optional[str] = DEFAULT_COLLECTION


class QueryRequest(BaseModel):
    question: str
    provider: Optional[str] = "gemini"
    model: Optional[str] = None
    search_type: Optional[str] = "similarity"
    k: Optional[int] = 4
    collection_name: Optional[str] = DEFAULT_COLLECTION


@app.get("/")
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    return FileResponse(str(index_file))


@app.post("/api/ingest/url")
async def api_ingest_url(request: UrlIngestRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty.")
    try:
        chunks = ingest_webpage(url, collection_name=request.collection_name or DEFAULT_COLLECTION)
        if chunks == 0:
            raise HTTPException(status_code=422, detail="Could not extract readable text from the provided URL.")
        return {
            "success": True,
            "chunks": chunks,
            "url": url,
            "message": f"Successfully ingested {chunks} chunks.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest/pdf")
async def api_ingest_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    tmp_path = None
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        chunks = ingest_pdf_file(tmp_path, collection_name=DEFAULT_COLLECTION)
        if chunks == 0:
            raise HTTPException(status_code=422, detail="Could not extract readable text from the uploaded PDF.")

        return {
            "success": True,
            "chunks": chunks,
            "filename": file.filename,
            "message": f"Successfully ingested {chunks} chunks.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@app.post("/api/query")
async def api_query(request: QueryRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = answer_query(
            question=question,
            collection_name=request.collection_name or DEFAULT_COLLECTION,
            search_type=request.search_type or "similarity",
            k=request.k or 4,
            provider=request.provider or DEFAULT_PROVIDER,
            model_name=request.model,
        )

        serialized_docs = []
        for doc in result.get("documents", []):
            serialized_docs.append({
                "page_content": doc.page_content,
                "metadata": doc.metadata or {},
            })

        return {
            "success": True,
            "answer": result["answer"],
            "documents": serialized_docs,
            "provider": result.get("provider", request.provider),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clear")
async def api_clear():
    try:
        clear_collection(DEFAULT_COLLECTION)
        return {"success": True, "message": "Knowledge base collection cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def api_status():
    return {
        "status": "online",
        "has_google_key": bool(os.getenv("GOOGLE_API_KEY")),
        "has_mistral_key": bool(os.getenv("MISTRAL_API_KEY")),
        "default_provider": DEFAULT_PROVIDER,
        "default_gemini_model": DEFAULT_GEMINI_MODEL,
        "default_mistral_model": DEFAULT_MISTRAL_MODEL,
    }
