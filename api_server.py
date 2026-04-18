from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import anthropic
import os
import json
import shutil
import datetime
import uuid
import pdfplumber

from tools.rag_engine import chunk_document


CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "banking_docs"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
UPLOAD_DIR = "./uploads"

INPUT_COST_PER_M = 3.0
OUTPUT_COST_PER_M = 15.0


app = FastAPI(title="BankAI Knowledge Hub API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


os.makedirs(UPLOAD_DIR, exist_ok=True)

print("Loading embedding model...")
embedding_model = SentenceTransformer(EMBED_MODEL)
print("Embedding model loaded.")


class QueryRequest(BaseModel):
    question: str
    n_results: int = 3
    distance_threshold: float = 1.5


class ChunkInfo(BaseModel):
    text: str
    source: str
    distance: float


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


@app.get("/api/health")
def health():
    """Quick health check to confirm the API and embedding model are ready."""
    return {"status": "healthy", "model": "loaded"}


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
            raise HTTPException(
                status_code=400, detail=f"Failed to read PDF: {e}"
            )
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
    metadatas = [
        {"source": source_name, "chunk_index": i} for i in range(len(chunks))
    ]

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
