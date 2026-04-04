import streamlit as st
import os
from datetime import datetime
from tools.brd_analyzer import analyze_brd, save_analysis
from tools.pdf_reader import extract_text_from_pdf

# ─── PAGE CONFIG ───
st.set_page_config(
    page_title="Pega BRD Analyzer",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ───
st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1f77b4;
    }
    .section-card {
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        background-color: #1a1a2e;
        margin-bottom: 1rem;
        border-radius: 0 8px 8px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ─── SESSION STATE ───
if "brd_analysis" not in st.session_state:
    st.session_state.brd_analysis = None
if "brd_document" not in st.session_state:
    st.session_state.brd_document = None
if "brd_name" not in st.session_state:
    st.session_state.brd_name = None
if "brd_uploader_key" not in st.session_state:
    st.session_state.brd_uploader_key = 0

# ─── SIDEBAR ───
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/workflow.png", width=80)
    st.title("Pega BRD Analyzer")
    st.caption("Powered by Llama3 — Running Locally 🔒")
    st.divider()

    st.markdown("### 🤖 About this tool")
    st.markdown("""
    This tool acts as a **Senior BA** and analyzes your BRD to produce:
    
    - 📋 Requirement Summary
    - 👤 User Stories
    - 📐 Business Rules
    - ⚠️ Edge Cases
    - ❓ Developer Questions
    - 🚨 Risk Flags
    - 📊 Complexity Assessment
    """)

    st.divider()
    st.caption("🔒 All data stays on your machine")
    st.caption("🦙 Model: Llama3 via Ollama")
    st.caption("🐍 Built with Python + Streamlit")

    if st.session_state.brd_analysis:
        st.divider()
        st.success("✅ Analysis ready")
        if st.button("🗑️ Clear & Start Over", use_container_width=True):
            st.session_state.brd_analysis = None
            st.session_state.brd_document = None
            st.session_state.brd_name = None
            st.session_state.brd_uploader_key += 1
            st.rerun()

# ─── HEADER ───
st.markdown('<p class="main-header">📋 Pega BRD Analyzer</p>',
            unsafe_allow_html=True)
st.markdown("#### Upload your BRD and get an instant structured analysis — User Stories, Business Rules, Edge Cases and more.")
st.divider()

# ─── INPUT SECTION ───
if not st.session_state.brd_analysis:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📂 Load Your BRD")
        input_method = st.radio(
            "How would you like to provide the BRD?",
            options=["📁 Upload a file", "📋 Paste text directly"],
            horizontal=True
        )

        if input_method == "📁 Upload a file":
            uploaded_file = st.file_uploader(
                "Upload BRD document",
                type=["txt", "pdf"],
                key=f"brd_uploader_{st.session_state.brd_uploader_key}",
                help="Supports .txt and .pdf files"
            )
            if uploaded_file:
                if uploaded_file.type == "application/pdf":
                    with st.spinner("Reading PDF..."):
                        content, page_count, error = extract_text_from_pdf(
                            file_object=uploaded_file
                        )
                    if error:
                        st.error(error)
                    else:
                        st.session_state.brd_document = content
                        st.session_state.brd_name = uploaded_file.name
                        st.success(f"✅ Loaded: {uploaded_file.name}")
                        st.caption(f"📄 {page_count} pages · {len(content.split())} words")
                else:
                    content = uploaded_file.read().decode("utf-8")
                    if len(content.strip()) == 0:
                        st.warning("⚠️ The uploaded file is empty.")
                    else:
                        st.session_state.brd_document = content
                        st.session_state.brd_name = uploaded_file.name
                        st.success(f"✅ Loaded: {uploaded_file.name}")
                        st.caption(f"📄 {len(content.split())} words")
        else:
            pasted_text = st.text_area(
                "Paste your BRD text here",
                height=300,
                placeholder="Paste your Business Requirements Document here..."
            )
            if st.button("📋 Load BRD", use_container_width=True):
                if not pasted_text.strip():
                    st.warning("⚠️ Please paste some text before loading.")
                else:
                    st.session_state.brd_document = pasted_text
                    st.session_state.brd_name = "Pasted BRD"
                    st.success("✅ BRD loaded successfully")
                    st.caption(f"📄 {len(pasted_text.split())} words")

    with col2:
        st.markdown("### ℹ️ What you'll get")
        st.markdown("""
        Once you load your BRD and click Analyze, the AI will produce:

        **📋 Requirement Summary**
        A concise overview of the entire requirement.

        **👤 User Stories**
        Properly formatted As a / I want / So that stories.

        **📐 Business Rules**
        All explicit and implicit rules with BR-XXX numbering.

        **⚠️ Edge Cases**
        Gaps and unhandled scenarios with EC-XXX numbering.

        **❓ Developer Questions**
        Questions to clarify before building, Pega specific.

        **🚨 Risk Flags**
        Compliance and technical risks with RF-XXX numbering.

        **📊 Complexity Assessment**
        Complexity rating and story point estimate.
        """)

    # ─── ANALYZE BUTTON ───
    st.divider()
    if st.session_state.brd_document:
        st.info(f"📄 BRD loaded: **{st.session_state.brd_name}** — {len(st.session_state.brd_document.split())} words")

        if st.button("🚀 Analyze BRD", type="primary", use_container_width=True):
            with st.spinner("🤖 Senior BA is analyzing your BRD... This may take up to 2 minutes for large documents."):
                analysis, error = analyze_brd(st.session_state.brd_document)

            if error:
                st.error(error)
            else:
                st.session_state.brd_analysis = analysis
                st.rerun()
    else:
        st.button("🚀 Analyze BRD", type="primary", use_container_width=True, disabled=True)
        st.caption("👆 Load a BRD document first to enable analysis")

# ─── RESULTS SECTION ───
else:
    st.success(f"✅ Analysis complete for: **{st.session_state.brd_name}**")
    st.divider()

    # Display analysis
    st.markdown(st.session_state.brd_analysis)

    st.divider()

    # Action buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("💾 Save Analysis Report", type="primary", use_container_width=True):
            output_path = save_analysis(
                st.session_state.brd_name,
                st.session_state.brd_analysis
            )
            st.success(f"✅ Report saved to: {output_path}")

    with col2:
        st.code(st.session_state.brd_analysis, language=None)