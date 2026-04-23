"""Sprint 0 Accelerator API.

Combines RAG document management (lifted from api_server.py) with
multi-agent pipeline orchestration (sprint0/pipeline.py).
"""

import os
import json
import shutil
import datetime
import uuid
import threading

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import chromadb
from sentence_transformers import SentenceTransformer
import anthropic
import pdfplumber

from tools.rag_engine import chunk_document
from sprint0.pipeline import run_pipeline, build_pipeline, PipelineState


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "banking_docs"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
UPLOAD_DIR = "./uploads"
BRD_DIR = "./docs"

INPUT_COST_PER_M = 3.0
OUTPUT_COST_PER_M = 15.0


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Sprint 0 Accelerator API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BRD_DIR, exist_ok=True)

print("Loading embedding model...")
embedding_model = SentenceTransformer(EMBED_MODEL)
print("Embedding model loaded.")

# In-memory store for pipeline run state (resets on restart)
pipeline_runs: dict = {}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str
    n_results: int = 3
    distance_threshold: float = 1.5


class QueryResponse(BaseModel):
    answer: str
    chunks: list
    cost: float
    no_match: bool


class DocumentInfo(BaseModel):
    name: str
    chunk_count: int


class IngestResponse(BaseModel):
    filename: str
    chunks_created: int
    status: str


class PipelineRequest(BaseModel):
    brd_file: str = "docs/mini_brd.txt"
    max_iterations: int = 2


class PipelineRunResponse(BaseModel):
    run_id: str
    status: str
    message: str


class PipelineStatusResponse(BaseModel):
    run_id: str
    status: str
    verdict: str
    iterations: int
    agent_status: dict
    costs: dict
    errors: list


class PipelineResultsResponse(BaseModel):
    run_id: str
    ba_output: str
    tl_output: str
    dev_output: str
    rev_output: str
    dev_history: list
    rev_history: list
    verdict: str
    case_created: str
    total_cost: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_collection():
    """Return a fresh ChromaDB collection handle."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def extract_pdf_text(pdf_path: str) -> str:
    """Extract all text from a PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def estimate_cost(input_text: str, output_text: str) -> float:
    """Estimate Claude Sonnet API cost from text lengths."""
    input_tokens = len(input_text) / 4
    output_tokens = len(output_text) / 4
    return (input_tokens / 1_000_000) * INPUT_COST_PER_M + (
        output_tokens / 1_000_000
    ) * OUTPUT_COST_PER_M


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    """Quick health check — confirms API, embedding model, and pipeline are ready."""
    return {
        "status": "healthy",
        "model_loaded": embedding_model is not None,
        "pipeline_ready": True,
    }


# ---------------------------------------------------------------------------
# Document management (RAG)
# ---------------------------------------------------------------------------

@app.post("/api/documents/upload", response_model=IngestResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a .txt or .pdf file, chunk it, embed it, and store in ChromaDB."""
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".txt", ".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .pdf files are supported.",
        )

    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if os.path.getsize(save_path) == 0:
        os.remove(save_path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if ext == ".pdf":
        try:
            text = extract_pdf_text(save_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="PDF contains no extractable text (may be scanned).",
            )
        txt_path = os.path.splitext(save_path)[0] + ".txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        chunk_source_path = txt_path
        source_name = filename
    else:
        chunk_source_path = save_path
        source_name = filename

    chunks = chunk_document(chunk_source_path)
    if not chunks:
        raise HTTPException(
            status_code=400, detail="No chunks could be created from the document."
        )

    embeddings = embedding_model.encode(chunks).tolist()
    name_stem = os.path.splitext(source_name)[0]
    ids = [f"doc_{name_stem}_chunk_{i}_{uuid.uuid4().hex[:8]}" for i in range(len(chunks))]
    metadatas = [{"source": source_name, "chunk_index": i} for i in range(len(chunks))]

    collection = get_collection()
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )

    return IngestResponse(
        filename=source_name,
        chunks_created=len(chunks),
        status="ingested",
    )


@app.get("/api/documents", response_model=list[DocumentInfo])
def list_documents():
    """List all ingested documents with per-document chunk counts."""
    collection = get_collection()
    data = collection.get(include=["metadatas"])
    metadatas = data.get("metadatas") or []

    counts: dict[str, int] = {}
    for meta in metadatas:
        if not meta:
            continue
        source = meta.get("source")
        if not source:
            continue
        counts[source] = counts.get(source, 0) + 1

    return [DocumentInfo(name=name, chunk_count=count) for name, count in counts.items()]


@app.delete("/api/documents/{doc_name}")
def delete_document(doc_name: str):
    """Delete every chunk whose metadata.source matches doc_name."""
    collection = get_collection()
    results = collection.get(where={"source": doc_name})
    ids = results.get("ids") or []

    if not ids:
        raise HTTPException(
            status_code=404, detail=f"No document named '{doc_name}' found."
        )

    collection.delete(ids=ids)
    return JSONResponse(
        {
            "status": "deleted",
            "document": doc_name,
            "chunks_removed": len(ids),
        }
    )


@app.get("/api/stats")
def stats():
    """Return aggregate statistics about the knowledge base."""
    collection = get_collection()
    total_chunks = collection.count()
    data = collection.get(include=["metadatas"])
    metadatas = data.get("metadatas") or []
    unique_sources = {
        (m or {}).get("source") for m in metadatas if m and m.get("source")
    }

    return {
        "total_documents": len(unique_sources),
        "total_chunks": total_chunks,
        "collection_name": COLLECTION_NAME,
    }


# ---------------------------------------------------------------------------
# RAG Query
# ---------------------------------------------------------------------------

@app.post("/api/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    """Answer a question using RAG: retrieve top chunks, then ask Claude."""
    collection = get_collection()
    question_embedding = embedding_model.encode([request.question]).tolist()

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=request.n_results,
    )

    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    chunks = [
        {
            "text": doc,
            "source": (meta or {}).get("source", "unknown"),
            "distance": float(dist),
        }
        for doc, dist, meta in zip(documents, distances, metadatas)
    ]

    if not chunks or chunks[0]["distance"] > request.distance_threshold:
        return QueryResponse(
            answer="",
            chunks=chunks,
            cost=0.0,
            no_match=True,
        )

    context = "\n\n".join(c["text"] for c in chunks)
    system_prompt = (
        "You are a banking domain expert. Answer questions using ONLY the provided context. "
        "If the context does not contain the answer, say 'I don't have enough information to answer this.' "
        "Do not use any outside knowledge."
    )
    user_prompt = f"Context:\n\n{context}\n\nQuestion: {request.question}"

    try:
        claude = anthropic.Anthropic()
        response = claude.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        answer = response.content[0].text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claude API error: {e}")

    cost = estimate_cost(system_prompt + user_prompt, answer)

    return QueryResponse(
        answer=answer,
        chunks=chunks,
        cost=cost,
        no_match=False,
    )


# ---------------------------------------------------------------------------
# Pipeline — BRD upload
# ---------------------------------------------------------------------------

@app.post("/api/pipeline/upload-brd")
async def upload_brd(file: UploadFile = File(...)):
    """Upload a BRD file into the docs/ folder for pipeline processing.

    Does NOT start the pipeline — just saves the file and confirms.
    """
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".txt", ".pdf", ".md"):
        raise HTTPException(
            status_code=400,
            detail="Only .txt, .pdf, and .md BRD files are supported.",
        )

    save_path = os.path.join(BRD_DIR, filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if os.path.getsize(save_path) == 0:
        os.remove(save_path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Convert PDF to text in-place so pipeline can read it as plain text
    if ext == ".pdf":
        try:
            text = extract_pdf_text(save_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read PDF: {e}")
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="PDF contains no extractable text (may be scanned).",
            )
        txt_path = os.path.splitext(save_path)[0] + ".txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        brd_file = f"docs/{os.path.splitext(filename)[0]}.txt"
    else:
        brd_file = f"docs/{filename}"

    return JSONResponse(
        {
            "filename": filename,
            "brd_file": brd_file,
            "message": f"BRD '{filename}' uploaded successfully. Use '{brd_file}' as brd_file in /api/pipeline/run.",
        }
    )


# ---------------------------------------------------------------------------
# Pipeline — run
# ---------------------------------------------------------------------------

@app.post("/api/pipeline/run", response_model=PipelineRunResponse)
def run_pipeline_endpoint(request: PipelineRequest):
    """Start the multi-agent pipeline in a background thread.

    Returns immediately with a run_id for polling via /api/pipeline/status/{run_id}.
    """
    run_id = uuid.uuid4().hex[:8]
    pipeline_runs[run_id] = {"status": "running", "result": None}

    def _thread_target():
        try:
            result = run_pipeline(request.brd_file, request.max_iterations)
            pipeline_runs[run_id]["result"] = result
            pipeline_runs[run_id]["status"] = "completed"
        except Exception as e:
            pipeline_runs[run_id]["result"] = {"errors": [str(e)]}
            pipeline_runs[run_id]["status"] = "failed"

    thread = threading.Thread(target=_thread_target, daemon=True)
    thread.start()

    return PipelineRunResponse(
        run_id=run_id,
        status="running",
        message=f"Pipeline started for '{request.brd_file}'. Poll /api/pipeline/status/{run_id} for updates.",
    )


# ---------------------------------------------------------------------------
# Pipeline — status
# ---------------------------------------------------------------------------

@app.get("/api/pipeline/status/{run_id}", response_model=PipelineStatusResponse)
def pipeline_status(run_id: str):
    """Return the current status of a pipeline run."""
    entry = pipeline_runs.get(run_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    status = entry["status"]
    result = entry.get("result") or {}

    if status == "running":
        # Return partial status — agent_status may be populated mid-run
        return PipelineStatusResponse(
            run_id=run_id,
            status="running",
            verdict="",
            iterations=result.get("iteration", 0),
            agent_status=result.get("agent_status") or {},
            costs=result.get("costs") or {},
            errors=result.get("errors") or [],
        )

    return PipelineStatusResponse(
        run_id=run_id,
        status=status,
        verdict=result.get("verdict") or "",
        iterations=result.get("iteration", 0),
        agent_status=result.get("agent_status") or {},
        costs=result.get("costs") or {},
        errors=result.get("errors") or [],
    )


# ---------------------------------------------------------------------------
# Pipeline — results
# ---------------------------------------------------------------------------

@app.get("/api/pipeline/results/{run_id}", response_model=PipelineResultsResponse)
def pipeline_results(run_id: str):
    """Return the full outputs of a completed pipeline run."""
    entry = pipeline_runs.get(run_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    if entry["status"] == "running":
        raise HTTPException(
            status_code=202,
            detail=f"Run '{run_id}' is still in progress. Check back shortly.",
        )

    if entry["status"] == "failed":
        errors = (entry.get("result") or {}).get("errors") or []
        raise HTTPException(
            status_code=500,
            detail=f"Run '{run_id}' failed. Errors: {errors}",
        )

    result = entry.get("result") or {}
    costs = result.get("costs") or {}
    total_cost = sum(costs.values())

    return PipelineResultsResponse(
        run_id=run_id,
        ba_output=result.get("ba_output") or "",
        tl_output=result.get("tl_output") or "",
        dev_output=result.get("dev_output") or "",
        rev_output=result.get("rev_output") or "",
        dev_history=result.get("dev_history") or [],
        rev_history=result.get("rev_history") or [],
        verdict=result.get("verdict") or "",
        case_created=result.get("case_created") or "",
        total_cost=total_cost,
    )


# ---------------------------------------------------------------------------
# Pipeline — history
# ---------------------------------------------------------------------------

@app.get("/api/pipeline/runs")
def list_pipeline_runs():
    """Return a summary of all pipeline runs in this server session."""
    runs = []
    for run_id, entry in pipeline_runs.items():
        result = entry.get("result") or {}
        costs = result.get("costs") or {}
        runs.append(
            {
                "run_id": run_id,
                "status": entry["status"],
                "verdict": result.get("verdict") or "",
                "iterations": result.get("iteration", 0),
                "total_cost": sum(costs.values()),
                "errors": result.get("errors") or [],
            }
        )
    return runs
