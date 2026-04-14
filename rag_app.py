import streamlit as st
import os
import shutil
from datetime import datetime

import chromadb
from sentence_transformers import SentenceTransformer
import anthropic

from tools.rag_engine import chunk_document, ingest_documents, query_rag  # noqa: F401
from tools.pdf_reader import extract_text_from_pdf


# ─── PAGE CONFIG ───
st.set_page_config(
    page_title="RAG Knowledge Base",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# ─── CONSTANTS ───
COLLECTION_NAME = "banking_docs"
CHROMA_PATH = "./chroma_db"
DOCS_DIR = "docs"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Sonnet pricing (approx, per 1M tokens)
COST_INPUT_PER_1M = 3.0
COST_OUTPUT_PER_1M = 15.0


# ─── CUSTOM CSS ───
st.markdown("""
<style>
:root {
    --bg-primary: #0a0f1e;
    --bg-secondary: #111827;
    --bg-card: #1a2236;
    --bg-card-hover: #1f2a42;
    --accent: #00d4ff;
    --accent-glow: rgba(0, 212, 255, 0.3);
    --success: #00ff88;
    --success-glow: rgba(0, 255, 136, 0.3);
    --warning: #ffaa00;
    --warning-glow: rgba(255, 170, 0, 0.3);
    --error: #ff4444;
    --error-glow: rgba(255, 68, 68, 0.3);
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --border: #2a3550;
}

.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: var(--bg-primary) !important;
}
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
header[data-testid="stHeader"] { background-color: transparent !important; }

h1, h2, h3, h4, h5, h6, p, span, div, label, li {
    color: var(--text-primary) !important;
    font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif !important;
}
.stMarkdown p { color: var(--text-secondary) !important; }

/* ─── HERO ─── */
.hero-wrap {
    position: relative;
    padding: 24px 28px;
    background: radial-gradient(circle at 0% 0%, rgba(0, 212, 255, 0.08), transparent 60%),
                radial-gradient(circle at 100% 100%, rgba(0, 255, 136, 0.06), transparent 60%),
                var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    margin-bottom: 20px;
    overflow: hidden;
}
.hero-wrap::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), var(--success), var(--accent), transparent);
    background-size: 200% 100%;
    animation: shimmer 4s linear infinite;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00d4ff 0%, #00ff88 50%, #00d4ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    letter-spacing: -1.2px;
    line-height: 1.1;
}
.hero-subtitle {
    font-size: 0.85rem;
    color: var(--text-muted) !important;
    font-weight: 500;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 6px;
}
.hero-stats {
    display: flex;
    gap: 18px;
    margin-top: 18px;
    flex-wrap: wrap;
}
.hero-stat {
    background: rgba(0, 212, 255, 0.05);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 0.8rem;
}
.hero-stat b {
    color: var(--accent) !important;
    font-weight: 700;
    margin-right: 6px;
}

/* ─── SECTION HEADER ─── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 22px 0 14px 0;
}
.section-header .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 10px var(--accent-glow);
}
.section-header .title {
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    color: var(--text-primary) !important;
}
.section-header .badge {
    font-size: 0.7rem;
    color: var(--text-muted) !important;
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 2px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ─── CHUNK CARDS ─── */
.chunk-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
    height: 100%;
    min-height: 180px;
    transition: all 0.3s ease;
}
.chunk-card:hover { transform: translateY(-2px); }
.chunk-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}
.chunk-card.green::before { background: var(--success); }
.chunk-card.green { box-shadow: 0 0 12px rgba(0, 255, 136, 0.12); border-color: rgba(0, 255, 136, 0.35); }
.chunk-card.amber::before { background: var(--warning); }
.chunk-card.amber { box-shadow: 0 0 12px rgba(255, 170, 0, 0.10); border-color: rgba(255, 170, 0, 0.35); }
.chunk-card.red::before { background: var(--error); }
.chunk-card.red { box-shadow: 0 0 12px rgba(255, 68, 68, 0.10); border-color: rgba(255, 68, 68, 0.35); }

.chunk-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.chunk-num {
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 2px;
}
.chunk-score {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace !important;
}
.chunk-score.green { background: rgba(0, 255, 136, 0.15); color: var(--success) !important; border: 1px solid var(--success); }
.chunk-score.amber { background: rgba(255, 170, 0, 0.15); color: var(--warning) !important; border: 1px solid var(--warning); }
.chunk-score.red   { background: rgba(255, 68, 68, 0.15);  color: var(--error) !important;   border: 1px solid var(--error); }

.chunk-source {
    font-size: 0.75rem;
    color: var(--accent) !important;
    font-family: 'JetBrains Mono', monospace !important;
    margin-bottom: 10px;
    word-break: break-all;
}
.chunk-source::before {
    content: '📄 ';
}
.chunk-text {
    font-size: 0.85rem;
    color: var(--text-secondary) !important;
    line-height: 1.55;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
}

/* ─── ANSWER CARD ─── */
.answer-wrap {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.04), rgba(0, 255, 136, 0.04)), var(--bg-card);
    border: 1px solid var(--accent);
    border-radius: 16px;
    padding: 22px 26px;
    box-shadow: 0 0 25px rgba(0, 212, 255, 0.12);
    margin-top: 12px;
}
.answer-label {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--accent) !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 10px;
}
.answer-label::before {
    content: '';
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--success);
    box-shadow: 0 0 8px var(--success-glow);
    animation: pulse-dot 1.8s ease-in-out infinite;
}
.answer-text {
    color: var(--text-primary) !important;
    font-size: 0.98rem;
    line-height: 1.7;
}
.answer-text p { color: var(--text-primary) !important; }

/* ─── NO MATCH WARN ─── */
.no-match-card {
    background: rgba(255, 170, 0, 0.06);
    border: 1px solid var(--warning);
    border-radius: 14px;
    padding: 20px 24px;
    color: var(--warning) !important;
}
.no-match-card b { color: var(--warning) !important; }

/* ─── BUTTONS ─── */
div.stButton > button {
    background: linear-gradient(135deg, #00d4ff, #0099cc) !important;
    color: #0a0f1e !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px 26px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 0 15px var(--accent-glow) !important;
}
div.stButton > button:hover {
    box-shadow: 0 0 25px var(--accent-glow), 0 0 50px rgba(0, 212, 255, 0.15) !important;
    transform: translateY(-1px) !important;
}
/* Secondary (danger) button for Clear DB */
.stButton.danger-btn button, div[data-testid*="clear_db"] > button {
    background: transparent !important;
    color: var(--error) !important;
    border: 1px solid var(--error) !important;
    box-shadow: none !important;
}

/* ─── TEXT INPUT ─── */
textarea, [data-testid="stTextArea"] textarea,
input[type="text"], [data-testid="stTextInput"] input {
    background-color: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 10px var(--accent-glow) !important;
}

/* ─── SLIDER ─── */
[data-testid="stSlider"] > div > div > div { color: var(--accent) !important; }

/* ─── FILE UPLOADER ─── */
[data-testid="stFileUploader"] {
    background-color: var(--bg-card) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }

/* ─── EXPANDER ─── */
[data-testid="stExpander"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    margin: 6px 0 !important;
}
[data-testid="stExpander"] summary { color: var(--text-primary) !important; }
[data-testid="stExpander"] details summary::before { content: "▶ " !important; }
[data-testid="stExpander"][open] details summary::before { content: "▼ " !important; }

hr { border-color: var(--border) !important; opacity: 0.5; }

/* ─── SIDEBAR PANELS ─── */
.sidebar-panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    margin: 10px 0;
}
.sidebar-label {
    font-size: 0.68rem;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 6px;
    font-weight: 600;
}
.doc-pill {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: rgba(0, 212, 255, 0.06);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    margin: 5px 0;
    font-size: 0.78rem;
    color: var(--text-secondary) !important;
    font-family: 'JetBrains Mono', monospace !important;
    word-break: break-all;
}

/* ─── FOOTER ─── */
.footer-bar {
    margin-top: 32px;
    padding: 14px 22px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    display: flex;
    justify-content: space-around;
    flex-wrap: wrap;
    gap: 12px;
}
.footer-stat {
    text-align: center;
    flex: 1;
    min-width: 110px;
}
.footer-stat .value {
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--accent) !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.footer-stat .label {
    font-size: 0.65rem;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 2px;
}

/* ─── ANIMATIONS ─── */
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.3); }
}

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

[data-testid="stToolbar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ─── SESSION STATE ───
def init_state():
    defaults = {
        "ingested_files": [],
        "chat_history": [],
        "retrieved_chunks": [],
        "last_question": "",
        "last_answer": None,
        "last_cost": 0.0,
        "last_no_match": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─── CACHED RESOURCES ───
@st.cache_resource(show_spinner=False)
def load_embedding_model():
    return SentenceTransformer(EMBED_MODEL)


@st.cache_resource(show_spinner=False)
def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)


# ─── HELPERS ───
def distance_tier(distance: float):
    """Return (css_class, label) based on distance score."""
    if distance < 1.0:
        return "green", "HIGH RELEVANCE"
    elif distance <= 1.5:
        return "amber", "MODERATE"
    else:
        return "red", "LOW RELEVANCE"


def estimate_cost(input_text: str, output_text: str) -> float:
    """Rough cost estimate assuming ~4 chars per token."""
    in_tokens = len(input_text) / 4
    out_tokens = len(output_text) / 4
    return (in_tokens / 1_000_000) * COST_INPUT_PER_1M + (out_tokens / 1_000_000) * COST_OUTPUT_PER_1M


def estimate_tokens(text: str) -> int:
    return int(len(text) / 4)


def get_db_stats():
    """Return (collection_exists, chunk_count, unique_sources)."""
    try:
        client = get_chroma_client()
        collection = client.get_collection(name=COLLECTION_NAME)
        count = collection.count()
        # Get unique sources
        if count > 0:
            data = collection.get(include=["metadatas"])
            sources = set()
            for m in data.get("metadatas", []):
                if m and "source" in m:
                    sources.add(m["source"])
            return True, count, sorted(sources)
        return True, 0, []
    except Exception:
        return False, 0, []


def save_and_prepare_uploads(uploaded_files):
    """Persist uploads to docs/, converting PDFs to .txt. Returns list of .txt paths."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    prepared = []
    errors = []

    for f in uploaded_files:
        name = f.name
        target = os.path.join(DOCS_DIR, name)

        try:
            with open(target, "wb") as out:
                out.write(f.getbuffer())
        except Exception as e:
            errors.append(f"{name}: {e}")
            continue

        ext = os.path.splitext(name)[1].lower()
        if ext == ".txt":
            prepared.append(target)
        elif ext == ".pdf":
            text, pages, err = extract_text_from_pdf(file_path=target)
            if err or not text:
                errors.append(f"{name}: {err or 'no text extracted'}")
                continue
            txt_path = os.path.join(DOCS_DIR, os.path.splitext(name)[0] + ".txt")
            try:
                with open(txt_path, "w", encoding="utf-8") as out:
                    out.write(text)
                prepared.append(txt_path)
            except Exception as e:
                errors.append(f"{name}: could not write converted txt — {e}")
        else:
            errors.append(f"{name}: unsupported file type {ext}")

    return prepared, errors


def run_rag_query(question: str, n_results: int, distance_threshold: float):
    """Perform retrieval + Claude call inline so we can surface chunks and enforce threshold."""
    model = load_embedding_model()
    client = get_chroma_client()

    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception:
        st.session_state.last_no_match = True
        st.session_state.retrieved_chunks = []
        st.session_state.last_answer = None
        st.error("No collection found. Ingest documents first using the sidebar.")
        return

    try:
        q_embedding = model.encode([question]).tolist()
        results = collection.query(
            query_embeddings=q_embedding,
            n_results=n_results,
        )
    except Exception as e:
        st.error(f"Retrieval failed: {e}")
        return

    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    chunks = [
        {"text": d, "distance": dist, "source": m.get("source", "unknown")}
        for d, dist, m in zip(documents, distances, metadatas)
    ]
    st.session_state.retrieved_chunks = chunks

    # Threshold check
    best = distances[0] if distances else float("inf")
    if best > distance_threshold:
        st.session_state.last_no_match = True
        st.session_state.last_answer = None
        st.session_state.last_cost = 0.0
        st.session_state.last_question = question
        st.session_state.chat_history.append({
            "question": question,
            "chunks": chunks,
            "answer": None,
            "cost": 0.0,
            "no_match": True,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })
        return

    # Build prompt and call Claude
    context = "\n\n".join(documents)
    system_prompt = (
        "You are a banking domain expert. Answer questions using ONLY the provided context. "
        "If the context does not contain the answer, say 'I don't have enough information to answer this.' "
        "Do not use any outside knowledge."
    )
    user_prompt = f"Context:\n\n{context}\n\nQuestion: {question}"

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
        st.error(f"Claude API error: {e}")
        return

    cost = estimate_cost(system_prompt + user_prompt, answer)
    st.session_state.last_no_match = False
    st.session_state.last_answer = answer
    st.session_state.last_cost = cost
    st.session_state.last_question = question
    st.session_state.chat_history.append({
        "question": question,
        "chunks": chunks,
        "answer": answer,
        "cost": cost,
        "no_match": False,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    })


# ─── SIDEBAR ───
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 18px 0 8px 0;">
        <div style="font-size: 2.8rem;">🧠</div>
        <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;
                    letter-spacing: 3px; margin-top: 2px;">Knowledge Base</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Document Management ──
    st.markdown('<div class="sidebar-label">📚 Document Management</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        key="doc_uploader",
        label_visibility="collapsed"
    )

    if st.button("📥 Ingest Documents", use_container_width=True, key="ingest_btn"):
        if not uploaded_files:
            st.warning("Upload at least one file first.")
        else:
            with st.spinner("Preparing files…"):
                prepared, errors = save_and_prepare_uploads(uploaded_files)

            if errors:
                for err in errors:
                    st.error(err)

            if prepared:
                with st.spinner(f"Embedding & indexing {len(prepared)} file(s)…"):
                    try:
                        # Use engine's ingest function to add chunks to chroma_db
                        ingest_documents(prepared, collection_name=COLLECTION_NAME)

                        # Pull chunk counts per file from the collection
                        _, _, sources = get_db_stats()
                        st.session_state.ingested_files = sources

                        # Show per-file chunk count
                        client = get_chroma_client()
                        coll = client.get_collection(name=COLLECTION_NAME)
                        for p in prepared:
                            src_name = os.path.basename(p)
                            res = coll.get(where={"source": src_name}, include=["metadatas"])
                            n = len(res.get("ids", []))
                            st.success(f"✅ {src_name} — {n} chunks")
                    except Exception as e:
                        st.error(f"Ingestion failed: {e}")

    # Ingested list
    _, total_chunks, sources = get_db_stats()
    if sources:
        st.markdown('<div class="sidebar-label" style="margin-top:14px;">🗂️ Indexed Documents</div>',
                    unsafe_allow_html=True)
        for s in sources:
            st.markdown(f'<div class="doc-pill">📄 {s}</div>', unsafe_allow_html=True)
        st.session_state.ingested_files = sources

    st.markdown("---")

    # Clear DB
    if st.button("🗑️ Clear Database", use_container_width=True, key="clear_db"):
        try:
            # Delete the collection first (cleaner on Windows where sqlite may hold locks)
            try:
                client = get_chroma_client()
                client.delete_collection(name=COLLECTION_NAME)
            except Exception:
                pass
            # Drop in-memory cached client so its file handles release
            get_chroma_client.clear()
            # Best-effort folder removal
            if os.path.isdir(CHROMA_PATH):
                shutil.rmtree(CHROMA_PATH, ignore_errors=True)
            st.session_state.ingested_files = []
            st.session_state.chat_history = []
            st.session_state.retrieved_chunks = []
            st.session_state.last_answer = None
            st.session_state.last_no_match = False
            st.session_state.last_question = ""
            st.success("Database cleared.")
            st.rerun()
        except Exception as e:
            st.error(f"Clear failed: {e}")

    st.markdown("---")

    # ── Tuning ──
    with st.expander("⚙️ Tuning Parameters", expanded=False):
        n_results = st.slider(
            "Retrieved Chunks (n_results)",
            min_value=1, max_value=10, value=3, step=1, key="n_results"
        )
        distance_threshold = st.slider(
            "Distance Threshold",
            min_value=0.5, max_value=2.0, value=1.5, step=0.1, key="distance_threshold"
        )
        st.markdown("""
        <div style="font-size: 0.75rem; color: #94a3b8; line-height: 1.6; margin-top: 8px;">
            <b style="color:#00d4ff;">n_results</b> — how many chunks to pull from the vector store.<br>
            <b style="color:#00d4ff;">threshold</b> — reject queries whose best chunk distance exceeds this value (saves API cost).
        </div>
        """, unsafe_allow_html=True)


# ─── MAIN AREA ───

# Hero
_, total_chunks, sources = get_db_stats()
queries_asked = len(st.session_state.chat_history)

st.markdown(f"""
<div class="hero-wrap">
    <div class="hero-title">🧠 RAG Knowledge Base</div>
    <div class="hero-subtitle">Retrieval · Embed · Ground · Answer</div>
    <div class="hero-stats">
        <div class="hero-stat"><b>{len(sources)}</b>Documents</div>
        <div class="hero-stat"><b>{total_chunks}</b>Chunks Indexed</div>
        <div class="hero-stat"><b>{queries_asked}</b>Queries this session</div>
        <div class="hero-stat"><b>MiniLM-L6-v2</b>Embedder</div>
        <div class="hero-stat"><b>Sonnet 4</b>Generator</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── RETRIEVED CHUNKS PREVIEW ───
if st.session_state.retrieved_chunks:
    st.markdown(f"""
    <div class="section-header">
        <span class="dot"></span>
        <span class="title">Retrieved Chunks</span>
        <span class="badge">{len(st.session_state.retrieved_chunks)} results</span>
    </div>
    """, unsafe_allow_html=True)

    chunks = st.session_state.retrieved_chunks
    # Up to 3 cards per row for readability
    per_row = min(3, len(chunks)) if len(chunks) <= 3 else 3
    for row_start in range(0, len(chunks), per_row):
        row_chunks = chunks[row_start:row_start + per_row]
        cols = st.columns(len(row_chunks))
        for i, (col, c) in enumerate(zip(cols, row_chunks)):
            idx = row_start + i + 1
            tier, label = distance_tier(c["distance"])
            preview = c["text"][:200] + ("…" if len(c["text"]) > 200 else "")
            # Basic HTML-safety: escape angle brackets
            safe_preview = (preview.replace("&", "&amp;")
                                   .replace("<", "&lt;")
                                   .replace(">", "&gt;"))
            safe_source = c["source"].replace("<", "&lt;").replace(">", "&gt;")
            with col:
                st.markdown(f"""
                <div class="chunk-card {tier}">
                    <div class="chunk-header">
                        <span class="chunk-num">Chunk #{idx}</span>
                        <span class="chunk-score {tier}">{c['distance']:.3f}</span>
                    </div>
                    <div class="chunk-source">{safe_source}</div>
                    <div style="font-size:0.65rem; color:#64748b; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:6px;">
                        {label}
                    </div>
                    <div class="chunk-text">{safe_preview}</div>
                </div>
                """, unsafe_allow_html=True)


# ─── CHAT INTERFACE ───
st.markdown("""
<div class="section-header">
    <span class="dot" style="background:#00ff88;"></span>
    <span class="title">Ask Your Knowledge Base</span>
    <span class="badge">RAG · Grounded</span>
</div>
""", unsafe_allow_html=True)

col_q, col_btn = st.columns([5, 1])
with col_q:
    question = st.text_input(
        "Your question",
        key="question_input",
        placeholder="e.g. What is the bank's policy on overdraft fees?",
        label_visibility="collapsed"
    )
with col_btn:
    ask_clicked = st.button("🔍 Ask", use_container_width=True, key="ask_btn")

if ask_clicked:
    if not question.strip():
        st.warning("Please type a question.")
    elif total_chunks == 0:
        st.warning("No documents indexed yet. Upload and ingest documents from the sidebar first.")
    else:
        with st.spinner("Retrieving relevant context & generating answer…"):
            run_rag_query(
                question.strip(),
                n_results=st.session_state.get("n_results", 3),
                distance_threshold=st.session_state.get("distance_threshold", 1.5),
            )
        st.rerun()

# Latest answer
if st.session_state.last_no_match and st.session_state.last_question:
    best_d = (st.session_state.retrieved_chunks[0]["distance"]
              if st.session_state.retrieved_chunks else None)
    best_str = f"{best_d:.3f}" if best_d is not None else "N/A"
    threshold = st.session_state.get("distance_threshold", 1.5)
    st.markdown(f"""
    <div class="no-match-card">
        <b>⚠️ No relevant documents found for this query.</b><br>
        Best chunk distance: <b>{best_str}</b> exceeds threshold of <b>{threshold:.2f}</b>.
        Claude was not called — no API cost incurred. Try rephrasing, lowering the threshold, or ingesting more documents.
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.last_answer:
    # Escape for safety inside HTML container — but preserve newlines with <br>
    ans_html = (st.session_state.last_answer
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>"))
    tokens_in = estimate_tokens(st.session_state.last_question) + sum(
        estimate_tokens(c["text"]) for c in st.session_state.retrieved_chunks
    )
    tokens_out = estimate_tokens(st.session_state.last_answer)
    st.markdown(f"""
    <div class="answer-wrap">
        <div class="answer-label">Grounded Answer</div>
        <div class="answer-text">{ans_html}</div>
        <div style="margin-top:14px; display:flex; gap:12px; flex-wrap:wrap; font-size:0.72rem; color:#64748b;">
            <span>🔤 ~{tokens_in} in / {tokens_out} out tokens</span>
            <span>💰 ~${st.session_state.last_cost:.4f}</span>
            <span>🧩 {len(st.session_state.retrieved_chunks)} chunks used</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── CHAT HISTORY ───
if len(st.session_state.chat_history) > 1:
    st.markdown("""
    <div class="section-header" style="margin-top:32px;">
        <span class="dot" style="background:#64748b;"></span>
        <span class="title">Session History</span>
        <span class="badge">Past queries</span>
    </div>
    """, unsafe_allow_html=True)

    # Reverse order, skip the latest (already shown above)
    history = list(reversed(st.session_state.chat_history[:-1]))
    for i, item in enumerate(history):
        label_icon = "⚠️" if item.get("no_match") else "✅"
        status = "No match" if item.get("no_match") else "Answered"
        title = f"[{item['timestamp']}] {status} - {item['question'][:80]}"
        with st.expander(title):
            # Summary of chunks
            if item["chunks"]:
                summary_parts = []
                for idx, c in enumerate(item["chunks"], 1):
                    tier, _ = distance_tier(c["distance"])
                    color = {"green": "#00ff88", "amber": "#ffaa00", "red": "#ff4444"}[tier]
                    summary_parts.append(
                        f'<span style="color:{color};font-family:JetBrains Mono,monospace;">'
                        f'#{idx} {c["source"]} ({c["distance"]:.3f})</span>'
                    )
                st.markdown(
                    "<div style='font-size:0.8rem; margin-bottom:10px;'>"
                    + " · ".join(summary_parts) + "</div>",
                    unsafe_allow_html=True
                )

            if item.get("no_match"):
                st.warning("No relevant chunks matched — Claude was not called.")
            elif item["answer"]:
                st.markdown(item["answer"])
                st.caption(f"Est. cost: ${item['cost']:.4f}")


# ─── FOOTER ───
total_cost = sum(h.get("cost", 0.0) for h in st.session_state.chat_history)
st.markdown(f"""
<div class="footer-bar">
    <div class="footer-stat">
        <div class="value">{len(sources)}</div>
        <div class="label">Documents</div>
    </div>
    <div class="footer-stat">
        <div class="value">{total_chunks}</div>
        <div class="label">Chunks in DB</div>
    </div>
    <div class="footer-stat">
        <div class="value">{queries_asked}</div>
        <div class="label">Queries Asked</div>
    </div>
    <div class="footer-stat">
        <div class="value">${total_cost:.4f}</div>
        <div class="label">Session Cost</div>
    </div>
</div>
""", unsafe_allow_html=True)
