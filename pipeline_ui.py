import streamlit as st
import os
import time
from datetime import datetime

# ─── PAGE CONFIG ───
st.set_page_config(
    page_title="Sprint 0 Accelerator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# ─── CUSTOM CSS ───
st.markdown("""
<style>
/* ─── BASE THEME ─── */
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

/* ─── GLOBAL OVERRIDES ─── */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: var(--bg-primary) !important;
}
[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* ─── TYPOGRAPHY ─── */
h1, h2, h3, h4, h5, h6, p, span, div, label, li {
    color: var(--text-primary) !important;
    font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif !important;
}
.stMarkdown p { color: var(--text-secondary) !important; }

/* ─── HERO TITLE ─── */
.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #00d4ff 0%, #00ff88 50%, #00d4ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0;
    letter-spacing: -1px;
}
.hero-subtitle {
    font-size: 1.1rem;
    color: var(--text-muted) !important;
    font-weight: 400;
    margin-top: -8px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

/* ─── AGENT CARDS ─── */
.agent-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    margin: 8px 0;
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
}
.agent-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--border);
    transition: all 0.4s ease;
}
.agent-card.waiting {
    border-color: var(--border);
    opacity: 0.6;
}
.agent-card.waiting::before {
    background: var(--text-muted);
}
.agent-card.running {
    border-color: var(--accent);
    box-shadow: 0 0 20px var(--accent-glow), 0 0 40px rgba(0, 212, 255, 0.1);
    animation: pulse-border 2s ease-in-out infinite;
}
.agent-card.running::before {
    background: linear-gradient(90deg, var(--accent), #00ff88, var(--accent));
    background-size: 200% 100%;
    animation: shimmer 1.5s linear infinite;
}
.agent-card.complete {
    border-color: var(--success);
    box-shadow: 0 0 15px var(--success-glow);
}
.agent-card.complete::before {
    background: var(--success);
}
.agent-card.revision {
    border-color: var(--warning);
    box-shadow: 0 0 15px var(--warning-glow);
}
.agent-card.revision::before {
    background: var(--warning);
}
.agent-card.error {
    border-color: var(--error);
    box-shadow: 0 0 15px var(--error-glow);
}
.agent-card.error::before {
    background: var(--error);
}

.agent-icon { font-size: 2rem; margin-bottom: 8px; }
.agent-name {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary) !important;
    margin-bottom: 4px;
    letter-spacing: 0.5px;
}
.agent-role {
    font-size: 0.75rem;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
}
.agent-status {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.status-waiting {
    background: rgba(100, 116, 139, 0.2);
    color: var(--text-muted) !important;
    border: 1px solid var(--text-muted);
}
.status-running {
    background: rgba(0, 212, 255, 0.15);
    color: var(--accent) !important;
    border: 1px solid var(--accent);
    animation: pulse-status 1.5s ease-in-out infinite;
}
.status-complete {
    background: rgba(0, 255, 136, 0.15);
    color: var(--success) !important;
    border: 1px solid var(--success);
}
.status-revision {
    background: rgba(255, 170, 0, 0.15);
    color: var(--warning) !important;
    border: 1px solid var(--warning);
}
.status-error {
    background: rgba(255, 68, 68, 0.15);
    color: var(--error) !important;
    border: 1px solid var(--error);
}

.agent-meta {
    margin-top: 12px;
    font-size: 0.8rem;
    color: var(--text-muted) !important;
}

/* ─── METRIC CARDS ─── */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}
.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--accent) !important;
    margin-bottom: 4px;
}
.metric-label {
    font-size: 0.75rem;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

/* ─── VERDICT BADGES ─── */
.verdict-approved {
    display: inline-block;
    padding: 8px 24px;
    background: rgba(0, 255, 136, 0.15);
    border: 2px solid var(--success);
    border-radius: 8px;
    color: var(--success) !important;
    font-weight: 800;
    font-size: 1.1rem;
    letter-spacing: 2px;
    box-shadow: 0 0 20px var(--success-glow);
}
.verdict-revision {
    display: inline-block;
    padding: 8px 24px;
    background: rgba(255, 170, 0, 0.15);
    border: 2px solid var(--warning);
    border-radius: 8px;
    color: var(--warning) !important;
    font-weight: 800;
    font-size: 1.1rem;
    letter-spacing: 2px;
    box-shadow: 0 0 20px var(--warning-glow);
}

/* ─── BUTTONS ─── */
div.stButton > button {
    background: linear-gradient(135deg, #00d4ff, #0099cc) !important;
    color: #0a0f1e !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 32px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    letter-spacing: 1px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 0 20px var(--accent-glow) !important;
}
div.stButton > button:hover {
    box-shadow: 0 0 30px var(--accent-glow), 0 0 60px rgba(0, 212, 255, 0.2) !important;
    transform: translateY(-1px) !important;
}
div.stDownloadButton > button {
    background: var(--bg-card) !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
div.stDownloadButton > button:hover {
    background: rgba(0, 212, 255, 0.1) !important;
    box-shadow: 0 0 15px var(--accent-glow) !important;
}

/* ─── TEXT AREA & INPUTS ─── */
textarea, [data-testid="stTextArea"] textarea {
    background-color: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.9rem !important;
}
textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 10px var(--accent-glow) !important;
}

/* ─── TABS ─── */
.stTabs [data-baseweb="tab-list"] {
    background-color: var(--bg-secondary) !important;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: var(--text-muted) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 8px 20px !important;
}
.stTabs [aria-selected="true"] {
    background-color: var(--bg-card) !important;
    color: var(--accent) !important;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background-color: var(--bg-card) !important;
    border-radius: 0 0 12px 12px !important;
    padding: 20px !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
}

/* ─── SLIDER ─── */
[data-testid="stSlider"] > div > div > div {
    color: var(--accent) !important;
}

/* ─── FILE UPLOADER ─── */
[data-testid="stFileUploader"] {
    background-color: var(--bg-card) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent) !important;
}

/* ─── EXPANDER ─── */
[data-testid="stExpander"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}

/* ─── DIVIDER ─── */
hr { border-color: var(--border) !important; opacity: 0.5; }

/* ─── ANIMATIONS ─── */
@keyframes pulse-border {
    0%, 100% { box-shadow: 0 0 20px var(--accent-glow); }
    50% { box-shadow: 0 0 35px var(--accent-glow), 0 0 60px rgba(0, 212, 255, 0.15); }
}
@keyframes pulse-status {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ─── SIDEBAR SECTIONS ─── */
.sidebar-section {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    margin: 12px 0;
}
.sidebar-label {
    font-size: 0.7rem;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 8px;
}
.cost-display {
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--accent) !important;
}
.history-item {
    padding: 8px 12px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    margin: 4px 0;
    font-size: 0.8rem;
    color: var(--text-secondary) !important;
}

/* ─── WORD COUNT BADGE ─── */
.word-count {
    display: inline-block;
    padding: 2px 10px;
    background: rgba(0, 212, 255, 0.1);
    border: 1px solid var(--accent);
    border-radius: 12px;
    font-size: 0.75rem;
    color: var(--accent) !important;
    font-weight: 600;
}
            
[data-testid="stToolbar"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)


# ─── SESSION STATE INIT ───
def init_state():
    defaults = {
        "pipeline_running": False,
        "pipeline_complete": False,
        "brd_input": "",
        "agent_statuses": {
            "ba": "waiting", "tech_lead": "waiting",
            "developer": "waiting", "reviewer": "waiting"
        },
        "agent_outputs": {
            "ba": None, "tech_lead": None,
            "developer": None, "reviewer": None
        },
        "agent_times": {
            "ba": 0, "tech_lead": 0,
            "developer": 0, "reviewer": 0
        },
        "total_iterations": 0,
        "final_verdict": None,
        "pipeline_start_time": None,
        "pipeline_total_time": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # if "test_mode" not in st.session_state:
    #     st.session_state.pipeline_complete = True
    #     st.session_state.agent_statuses = {
    #         "ba": "complete",
    #         "tech_lead": "complete", 
    #         "developer": "complete",
    #         "reviewer": "complete"
    # }

init_state()


# ─── HELPER FUNCTIONS ───
AGENT_CONFIG = {
    "ba":        {"icon": "📋", "name": "BA Agent",        "role": "Business Analyst"},
    "tech_lead": {"icon": "🏗️", "name": "Tech Lead Agent", "role": "Pega Architect"},
    "developer": {"icon": "💻", "name": "Developer Agent", "role": "Pega Developer"},
    "reviewer":  {"icon": "🔍", "name": "Reviewer Agent",  "role": "QA Lead"},
}

# Per-agent estimated cost (rough: prompt + completion tokens at Sonnet pricing)
COST_PER_AGENT = {"ba": 0.04, "tech_lead": 0.05, "developer": 0.03, "reviewer": 0.02}


def render_agent_card(agent_key):
    cfg = AGENT_CONFIG[agent_key]
    status = st.session_state.agent_statuses[agent_key]
    output = st.session_state.agent_outputs[agent_key]
    elapsed = st.session_state.agent_times[agent_key]

    meta_parts = []
    if elapsed > 0:
        meta_parts.append(f"⏱ {elapsed:.1f}s")
    if output:
        wc = len(output.split())
        meta_parts.append(f"📝 {wc} words")
    meta_html = " &nbsp;·&nbsp; ".join(meta_parts) if meta_parts else ""

    return f"""
    <div class="agent-card {status}">
        <div class="agent-icon">{cfg['icon']}</div>
        <div class="agent-name">{cfg['name']}</div>
        <div class="agent-role">{cfg['role']}</div>
        <span class="agent-status status-{status}">{status.upper()}</span>
        <div class="agent-meta">{meta_html}</div>
    </div>
    """


def render_metric_card(value, label):
    return f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


def get_pipeline_history():
    outputs_dir = "outputs"
    if not os.path.isdir(outputs_dir):
        return []
    files = [f for f in os.listdir(outputs_dir) if f.startswith("ba_analysis_") and f.endswith(".md")]
    files.sort(reverse=True)
    return files[:10]


def estimate_cost():
    total = 0.0
    for key in COST_PER_AGENT:
        if st.session_state.agent_statuses[key] in ("complete", "revision"):
            total += COST_PER_AGENT[key]
    # Add extra cost per review iteration beyond the first
    extra_iters = max(0, st.session_state.total_iterations - 1)
    total += extra_iters * (COST_PER_AGENT["developer"] + COST_PER_AGENT["reviewer"])
    return total


def save_pipeline_outputs():
    """Save all outputs to outputs/ folder."""
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = {}
    mapping = {
        "ba": f"ba_analysis_{timestamp}.md",
        "tech_lead": f"tech_lead_analysis_{timestamp}.md",
        "developer": f"developer_specs_{timestamp}.md",
        "reviewer": f"review_report_{timestamp}.md",
    }
    for key, filename in mapping.items():
        content = st.session_state.agent_outputs.get(key)
        if content:
            path = os.path.join("outputs", filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            saved[key] = path
    return saved


# ─── SIDEBAR ───
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 10px 0;">
        <div style="font-size: 3rem;">🤖</div>
        <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;
                    letter-spacing: 3px; margin-top: 4px;">Sprint 0 Accelerator</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Pipeline Configuration
    st.markdown('<div class="sidebar-label">⚙️ Pipeline Configuration</div>', unsafe_allow_html=True)
    max_iterations = st.slider("Max Review Iterations", min_value=1, max_value=3, value=2, key="max_iters")

    st.markdown(f"""
    <div class="sidebar-section">
        <div class="sidebar-label">Model</div>
        <div style="color: #00d4ff !important; font-weight: 600; font-size: 0.9rem;">claude-sonnet-4-6</div>
        <div style="color: #64748b; font-size: 0.7rem; margin-top: 2px;">via Anthropic API</div>
    </div>
    """, unsafe_allow_html=True)

    # Cost Tracker
    est_cost = estimate_cost()
    st.markdown(f"""
    <div class="sidebar-section">
        <div class="sidebar-label">💰 Estimated Cost</div>
        <div class="cost-display">${est_cost:.2f}</div>
        <div style="color: #64748b; font-size: 0.7rem; margin-top: 4px;">
            Main pipeline calls only<br>
            Actual cost may be 2-3x higher
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Pipeline History
    st.markdown('<div class="sidebar-label">📜 Pipeline History</div>', unsafe_allow_html=True)
    history = get_pipeline_history()
    if history:
        for f in history[:8]:
            # Extract timestamp from filename
            ts = f.replace("ba_analysis_", "").replace(".md", "")
            try:
                dt = datetime.strptime(ts, "%Y%m%d_%H%M%S")
                display = dt.strftime("%b %d, %Y %H:%M")
            except ValueError:
                display = ts
            st.markdown(f'<div class="history-item">📄 {display}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color: #64748b; font-size: 0.8rem;">No runs yet</div>',
                    unsafe_allow_html=True)


# ─── MAIN AREA ───

# Hero
st.markdown("""
<div style="padding: 10px 0 5px 0;">
    <div class="hero-title">🤖 Sprint 0 Accelerator</div>
    <div class="hero-subtitle">AI-Powered Development Pipeline</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─── SECTION 1: BRD INPUT ───
st.markdown("### 📄 Business Requirements Document")

col_input, col_upload = st.columns([3, 1])

with col_input:
    brd_text = st.text_area(
        "Paste your BRD here",
        height=220,
        placeholder="Paste your Business Requirements Document here...\n\n"
                    "Example:\n"
                    "Project: Customer Onboarding Portal\n"
                    "The bank requires a digital onboarding solution...",
        key="brd_textarea",
        label_visibility="collapsed"
    )

with col_upload:
    uploaded = st.file_uploader("Or upload a .txt file", type=["txt"], label_visibility="collapsed")
    if uploaded:
        brd_text = uploaded.read().decode("utf-8")
        st.success(f"Loaded: {uploaded.name}")

    if brd_text:
        wc = len(brd_text.split())
        st.markdown(f'<div class="word-count">{wc} words</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="word-count">0 words</div>', unsafe_allow_html=True)

# Run button
run_clicked = st.button("🚀  Run Pipeline", use_container_width=True, disabled=st.session_state.pipeline_running)


# ─── PIPELINE EXECUTION ───
def render_all_agent_cards():
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_agent_card("ba"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_agent_card("tech_lead"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_agent_card("developer"), unsafe_allow_html=True)
    with col4:
        st.markdown(render_agent_card("reviewer"), unsafe_allow_html=True)

def run_pipeline(brd_input, max_review_iters):
    """Run the 4-agent pipeline sequentially, updating session state."""
    from tools.ba_agent import analyze_brd
    from tools.tech_lead_agent import design_from_ba
    from tools.developer_agent import create_implementation
    from tools.reviewer_agent import review_implementation

    st.session_state.pipeline_running = True
    st.session_state.pipeline_complete = False
    st.session_state.pipeline_start_time = time.time()
    st.session_state.total_iterations = 0
    st.session_state.final_verdict = None

    # Reset all agents
    for key in st.session_state.agent_statuses:
        st.session_state.agent_statuses[key] = "waiting"
        st.session_state.agent_outputs[key] = None
        st.session_state.agent_times[key] = 0

    # ── AGENT 1: BA ──
    st.session_state.agent_statuses["ba"] = "running"
    st.rerun()

    t0 = time.time()
    try:
        ba_output = analyze_brd(brd_input)
    except Exception as e:
        ba_output = None
        st.error(f"BA Agent error: {e}")

    st.session_state.agent_times["ba"] = time.time() - t0

    if not ba_output:
        st.session_state.agent_statuses["ba"] = "error"
        st.session_state.pipeline_running = False
        st.rerun()
        return

    st.session_state.agent_outputs["ba"] = ba_output
    st.session_state.agent_statuses["ba"] = "complete"
    st.rerun()

    # ── AGENT 2: TECH LEAD ──
    st.session_state.agent_statuses["tech_lead"] = "running"
    st.rerun()

    t0 = time.time()
    try:
        tl_output = design_from_ba(ba_output)
    except Exception as e:
        tl_output = None
        st.error(f"Tech Lead Agent error: {e}")

    st.session_state.agent_times["tech_lead"] = time.time() - t0

    if not tl_output:
        st.session_state.agent_statuses["tech_lead"] = "error"
        st.session_state.pipeline_running = False
        st.rerun()
        return

    st.session_state.agent_outputs["tech_lead"] = tl_output
    st.session_state.agent_statuses["tech_lead"] = "complete"
    st.rerun()

    # ── AGENT 3 & 4: DEVELOPER + REVIEWER LOOP ──
    dev_input = tl_output
    iteration = 0

    while iteration < max_review_iters:
        iteration += 1
        st.session_state.total_iterations = iteration

        # Developer
        st.session_state.agent_statuses["developer"] = "running"
        st.rerun()

        t0 = time.time()
        try:
            dev_output = create_implementation(dev_input)
        except Exception as e:
            dev_output = None
            st.error(f"Developer Agent error: {e}")

        st.session_state.agent_times["developer"] = time.time() - t0

        if not dev_output:
            st.session_state.agent_statuses["developer"] = "error"
            st.session_state.pipeline_running = False
            st.rerun()
            return

        st.session_state.agent_outputs["developer"] = dev_output
        st.session_state.agent_statuses["developer"] = "complete"
        st.rerun()

        # Reviewer
        st.session_state.agent_statuses["reviewer"] = "running"
        st.rerun()

        t0 = time.time()
        try:
            review_output = review_implementation(dev_output)
        except Exception as e:
            review_output = None
            st.error(f"Reviewer Agent error: {e}")

        st.session_state.agent_times["reviewer"] = time.time() - t0

        if not review_output:
            st.session_state.agent_statuses["reviewer"] = "error"
            st.session_state.pipeline_running = False
            st.rerun()
            return

        st.session_state.agent_outputs["reviewer"] = review_output

        # Check verdict
        if "VERDICT: APPROVED" in review_output.upper():
            st.session_state.agent_statuses["reviewer"] = "complete"
            st.session_state.final_verdict = "APPROVED"
            break
        else:
            st.session_state.final_verdict = "REVISION NEEDED"
            if iteration < max_review_iters:
                st.session_state.agent_statuses["reviewer"] = "revision"
                st.session_state.agent_statuses["developer"] = "revision"
                st.rerun()
                # Feed review back as context for next developer iteration
                dev_input = tl_output + "\n\n--- REVIEWER FEEDBACK ---\n" + review_output
            else:
                st.session_state.agent_statuses["reviewer"] = "complete"

    st.rerun()

    # Finalize
    st.session_state.pipeline_total_time = time.time() - st.session_state.pipeline_start_time
    st.session_state.pipeline_running = False
    st.session_state.pipeline_complete = True

    # Save all outputs
    save_pipeline_outputs()

# ─── SECTION 2: PIPELINE STATUS ───
status_container = st.container()

if st.session_state.pipeline_running or st.session_state.pipeline_complete:
    render_all_agent_cards()


# ─── TRIGGER PIPELINE ───
if run_clicked and brd_text.strip():
    run_pipeline(brd_text.strip(), max_iterations)
    st.rerun()
elif run_clicked and not brd_text.strip():
    st.warning("Please enter or upload a BRD first.")


# ─── SECTION 3: PIPELINE METRICS ───
if st.session_state.pipeline_complete:
    st.markdown("---")
    st.markdown("### 📊 Pipeline Metrics")

    total_time = st.session_state.pipeline_total_time
    total_cost = estimate_cost()
    iterations = st.session_state.total_iterations
    verdict = st.session_state.final_verdict or "N/A"

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.markdown(render_metric_card(f"${total_cost:.2f}", "Est. Cost"), unsafe_allow_html=True)
    with m2:
        st.markdown(render_metric_card(f"{total_time:.0f}s", "Total Time"), unsafe_allow_html=True)
    with m3:
        st.markdown(render_metric_card(str(iterations), "Iterations"), unsafe_allow_html=True)
    with m4:
        if verdict == "APPROVED":
            st.markdown('<div style="text-align:center; padding-top: 16px;">'
                        '<span class="verdict-approved">✅ APPROVED</span></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center; padding-top: 16px;">'
                        '<span class="verdict-revision">⚠️ REVISION NEEDED</span></div>',
                        unsafe_allow_html=True)

    # ─── SECTION 4: OUTPUTS ───
    st.markdown("---")
    st.markdown("### 📦 Pipeline Outputs")

    tab_ba, tab_tl, tab_dev, tab_rev = st.tabs([
        "📋 BA Analysis", "🏗️ Tech Design", "💻 Dev Specs", "🔍 Review Report"
    ])

    outputs = st.session_state.agent_outputs

    with tab_ba:
        if outputs["ba"]:
            st.markdown(outputs["ba"])
            st.download_button(
                "⬇️ Download BA Analysis",
                data=outputs["ba"],
                file_name=f"ba_analysis_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
        else:
            st.info("No BA analysis output available.")

    with tab_tl:
        if outputs["tech_lead"]:
            st.markdown(outputs["tech_lead"])
            st.download_button(
                "⬇️ Download Tech Design",
                data=outputs["tech_lead"],
                file_name=f"tech_lead_analysis_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
        else:
            st.info("No tech design output available.")

    with tab_dev:
        if outputs["developer"]:
            st.markdown(outputs["developer"])
            st.download_button(
                "⬇️ Download Dev Specs",
                data=outputs["developer"],
                file_name=f"developer_specs_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
        else:
            st.info("No developer specs output available.")

    with tab_rev:
        if outputs["reviewer"]:
            st.markdown(outputs["reviewer"])
            st.download_button(
                "⬇️ Download Review Report",
                data=outputs["reviewer"],
                file_name=f"review_report_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
        else:
            st.info("No review report output available.")
