import streamlit as st
import requests
import os
from datetime import datetime

# ─── PAGE CONFIG ───
st.set_page_config(
    page_title="AI Banking Assistant",
    page_icon="🏦",
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
    .tool-description {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ─── SESSION STATE INIT ───
if "email_history" not in st.session_state:
    st.session_state.email_history = []
if "qa_pairs" not in st.session_state:
    st.session_state.qa_pairs = []
if "loaded_document" not in st.session_state:
    st.session_state.loaded_document = None
if "document_name" not in st.session_state:
    st.session_state.document_name = None

# ─── SIDEBAR ───
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bank-building.png", width=80)
    st.title("AI Banking Assistant")
    st.caption("Powered by Llama3 — Running Locally 🔒")
    st.divider()

    selected_tool = st.radio(
        "Choose a tool:",
        options=[
            "🏠 Home",
            "✉️ Email Agent",
            "📄 Document Summarizer",
            "❓ Document Q&A"
        ],
        index=0
    )

    st.divider()
    st.caption("🔒 All data stays on your machine")
    st.caption("🦙 Model: Llama3 via Ollama")
    st.caption("🐍 Built with Python + Streamlit")

# ─── HOME PAGE ───
if selected_tool == "🏠 Home":
    st.markdown('<p class="main-header">🏦 AI Banking Assistant</p>',
                unsafe_allow_html=True)
    st.markdown("#### Your personal AI toolkit for banking and finance work.")
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### ✉️ Email Agent")
        st.markdown('<p class="tool-description">Review and rewrite draft emails with memory. Choose your tone and get professional results instantly.</p>',
                    unsafe_allow_html=True)
        if st.button("Open Email Agent", use_container_width=True):
            st.session_state.selected_tool = "✉️ Email Agent"

    with col2:
        st.markdown("### 📄 Document Summarizer")
        st.markdown('<p class="tool-description">Upload any document and get a structured summary. Perfect for policy documents, reports and BRDs.</p>',
                    unsafe_allow_html=True)
        if st.button("Open Summarizer", use_container_width=True):
            st.session_state.selected_tool = "📄 Document Summarizer"

    with col3:
        st.markdown("### ❓ Document Q&A")
        st.markdown('<p class="tool-description">Load any document and ask questions about it in plain English. Get precise answers instantly.</p>',
                    unsafe_allow_html=True)
        if st.button("Open Q&A", use_container_width=True):
            st.session_state.selected_tool = "❓ Document Q&A"

    st.divider()
    st.info("🔒 All processing happens locally on your machine. No data is sent to any external server.")

# ─── EMAIL AGENT PAGE ───
elif selected_tool == "✉️ Email Agent":
    st.markdown("## ✉️ Email Agent")
    st.markdown('<p class="tool-description">Review and rewrite your draft emails with AI. Your session history is remembered.</p>',
                unsafe_allow_html=True)
    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📝 Your Draft Email")
        draft = st.text_area(
            label="Type or paste your draft email here",
            height=250,
            placeholder="e.g. hi john, need the report asap. let me know.",
            key="email_draft"
        )

        tone = st.radio(
            "Choose tone:",
            options=["Professional", "Friendly", "Formal"],
            horizontal=True,
            key="email_tone"
        )

        if st.button("✨ Rewrite Email", type="primary", use_container_width=True):
            if not draft.strip():
                st.warning("⚠️ Please enter a draft email first.")
            else:
                # Build prompt with history
                history_text = ""
                for msg in st.session_state.email_history:
                    history_text += f"{msg['role']}: {msg['content']}\n\n"

                prompt = f"""You are an expert email assistant working in 
the banking and finance industry. Rewrite draft emails to be clear, 
polite and {tone.lower()}. Only return the rewritten email. Nothing else.

{history_text}
User: Please rewrite this email in a {tone.lower()} tone:\n{draft}"""

                with st.spinner("AI is rewriting your email..."):
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "llama3",
                            "prompt": prompt,
                            "stream": False
                        }
                    )
                    result = response.json()
                    rewritten = result["response"]

                # Save to session state
                st.session_state.email_history.append({
                    "role": "User",
                    "content": f"Rewrite in {tone} tone: {draft}"
                })
                st.session_state.email_history.append({
                    "role": "Assistant",
                    "content": rewritten
                })

                # Save to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs("outputs", exist_ok=True)
                with open(f"outputs/email_{timestamp}.txt", "a") as f:
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Tone: {tone}\n\n")
                    f.write(f"ORIGINAL:\n{draft}\n\n")
                    f.write(f"REWRITTEN:\n{rewritten}\n\n")

    with col2:
        st.markdown("### ✅ Rewritten Email")
        if st.session_state.email_history:
            last_response = st.session_state.email_history[-1]["content"]
            st.success(last_response)
            st.markdown("### 📋 Copy Ready Version")
            st.code(last_response, language=None)
        else:
            st.info("Your rewritten email will appear here.")

        # Session history
        if st.session_state.email_history:
            st.divider()
            st.markdown(f"### 📊 Session History")
            email_count = len(st.session_state.email_history) // 2
            st.metric("Emails reviewed this session", email_count)
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.email_history = []
                st.rerun()

# ─── DOCUMENT SUMMARIZER PAGE ───
elif selected_tool == "📄 Document Summarizer":
    st.markdown("## 📄 Document Summarizer")
    st.markdown('<p class="tool-description">Upload any document or paste text and get a structured AI summary instantly.</p>',
                unsafe_allow_html=True)
    st.divider()

    # Input method selector
    input_method = st.radio(
        "How would you like to provide the document?",
        options=["📁 Upload a file", "📋 Paste text directly"],
        horizontal=True
    )

    document_text = None

    if input_method == "📁 Upload a file":
        uploaded_file = st.file_uploader(
            "Upload a text file",
            type=["txt"],
            help="Only .txt files supported for now"
        )
        if uploaded_file:
            document_text = uploaded_file.read().decode("utf-8")
            st.success(f"✅ File loaded: {uploaded_file.name} ({len(document_text)} characters)")

    else:
        pasted_text = st.text_area(
            "Paste your document text here",
            height=250,
            placeholder="Paste any policy document, report, email thread or BRD here..."
        )
        if st.button("📋 Load Text", use_container_width=True):
            st.session_state.loaded_document = pasted_text
            st.session_state.document_name = "Pasted Text"

    if input_method == "📁 Upload a file" and uploaded_file:
        st.session_state.loaded_document = document_text
        st.session_state.document_name = uploaded_file.name

    document_text = st.session_state.loaded_document

    if document_text:
        st.divider()
        st.markdown("### 🎯 Choose Summary Type")

        summary_type = st.radio(
    "Select summary type:",
    options=["General", "Brief", "Bullet Points"],
    captions=[
        "Structured summary — Purpose, Key Points, Who it affects, Action Items, Risk Flags",
        "Concise paragraph with critical information — perfect for busy professionals",
        "Clean bullet points only — maximum 10 points"
    ],
    horizontal=True
)

        if st.button("📄 Generate Summary", type="primary", use_container_width=True):
            prompts = {
                "General": """You are an expert document analyst working in banking and finance.
Read the following document and provide a structured summary with these sections:
1. PURPOSE - What is this document about in one sentence
2. KEY POINTS - Top 5 most important points as bullet points
3. WHO IT AFFECTS - Who does this apply to
4. ACTION ITEMS - What actions are required if any
5. RISK FLAGS - Any compliance or risk related items to be aware of
Be concise. Use plain English. No jargon.""",

                "Brief": """You are an expert document analyst working in banking and finance.
Summarize the following document as a single concise paragraph.
Focus only on the most critical information. No bullet points, no headers.
Write it in a way that a busy banking professional can read in 30 seconds.""",

                "Bullet Points": """You are an expert document analyst working in banking and finance.
Convert the following document into clean bullet points only.
Maximum 10 bullet points. Each point must be one clear sentence."""
            }

            prompt = f"{prompts[summary_type]}\n\nDOCUMENT:\n{document_text}"

            with st.spinner("Analyzing document..."):
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3",
                        "prompt": prompt,
                        "stream": False
                    }
                )
                result = response.json()
                summary = result["response"]

            st.divider()
            st.markdown("### ✅ Summary")
            st.markdown(summary)

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("outputs", exist_ok=True)
            with open(f"outputs/summary_{timestamp}.txt", "w") as f:
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Summary Type: {summary_type}\n\n")
                f.write(f"SUMMARY:\n{summary}\n")

            st.success(f"✅ Summary saved to outputs folder")
            st.code(summary, language=None)

# ─── DOCUMENT Q&A PAGE ───
elif selected_tool == "❓ Document Q&A":
    st.markdown("## ❓ Document Q&A")
    st.markdown('<p class="tool-description">Load any document and ask questions about it in plain English. Get precise answers instantly.</p>',
                unsafe_allow_html=True)
    st.divider()

    # Document loading section
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📂 Load Document")
        input_method = st.radio(
            "How would you like to provide the document?",
            options=["📁 Upload a file", "📋 Paste text directly"],
            horizontal=True,
            key="qa_input_method"
        )

        if input_method == "📁 Upload a file":
            uploaded_file = st.file_uploader(
                "Upload a text file",
                type=["txt"],
                key="qa_uploader"
            )
            if uploaded_file and not st.session_state.loaded_document:
                st.session_state.loaded_document = uploaded_file.read().decode("utf-8")
                st.session_state.document_name = uploaded_file.name
                st.success(f"✅ Loaded: {uploaded_file.name}")

        else:
            pasted_text = st.text_area(
                "Paste your document text here",
                height=200,
                placeholder="Paste any policy document, BRD, report here...",
                key="qa_paste"
            )
            if st.button("📋 Load Text", use_container_width=True, key="qa_load"):
                st.session_state.loaded_document = pasted_text
                st.session_state.document_name = "Pasted Text"
                st.success("✅ Text loaded successfully")

        if st.session_state.loaded_document:
            st.info(f"📄 Active document: **{st.session_state.document_name}**")
            word_count = len(st.session_state.loaded_document.split())
            st.caption(f"Document size: {word_count} words")

            if st.button("🗑️ Clear Document", use_container_width=True):
                st.session_state.loaded_document = None
                st.session_state.document_name = None
                st.session_state.qa_pairs = []
                st.rerun()

    with col2:
        st.markdown("### 💬 Ask Questions")

        if not st.session_state.loaded_document:
            st.info("👈 Please load a document first to start asking questions.")
        else:
            question = st.text_input(
                "Type your question:",
                placeholder="e.g. What is the risk classification for self employed customers?",
                key="qa_question"
            )

            if st.button("🔍 Get Answer", type="primary", use_container_width=True):
                if not question.strip():
                    st.warning("⚠️ Please type a question first.")
                else:
                    prompt = f"""You are an expert document analyst working in banking and finance.
Answer the following question using ONLY the information found in the document.
If the answer is not in the document say: I could not find this information in the document.
Be specific and concise.

DOCUMENT:
{st.session_state.loaded_document}

QUESTION:
{question}

ANSWER:"""

                    with st.spinner("Searching document..."):
                        response = requests.post(
                            "http://localhost:11434/api/generate",
                            json={
                                "model": "llama3",
                                "prompt": prompt,
                                "stream": False
                            }
                        )
                        result = response.json()
                        answer = result["response"]

                    st.session_state.qa_pairs.append((question, answer))

            # Display Q&A history
            if st.session_state.qa_pairs:
                st.divider()
                st.markdown(f"### 📊 Session — {len(st.session_state.qa_pairs)} questions asked")

                for i, (q, a) in enumerate(reversed(st.session_state.qa_pairs), 1):
                    with st.expander(f"Q{len(st.session_state.qa_pairs) - i + 1}: {q}"):
                        st.markdown(a)

                st.divider()
                # Save session
                if st.button("💾 Save Q&A Session", use_container_width=True):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    os.makedirs("outputs", exist_ok=True)
                    with open(f"outputs/qa_session_{timestamp}.txt", "w") as f:
                        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Document: {st.session_state.document_name}\n")
                        f.write("=" * 50 + "\n\n")
                        for i, (q, a) in enumerate(st.session_state.qa_pairs, 1):
                            f.write(f"Q{i}: {q}\n")
                            f.write(f"A{i}: {a}\n\n")
                    st.success("✅ Q&A session saved to outputs folder")

                if st.button("🗑️ Clear Q&A History", use_container_width=True):
                    st.session_state.qa_pairs = []
                    st.rerun()

