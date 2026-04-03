import streamlit as st
import requests
import os
from datetime import datetime
from tools.pdf_reader import extract_text_from_pdf

# ─── PROMPT LOADER ───
def load_prompt(prompt_name):
    prompt_path = os.path.join("prompts", f"{prompt_name}.md")
    try:
        with open(prompt_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"⚠️ Prompt file not found: {prompt_path}")
        return None

# ─── OLLAMA API CALLER ───
def call_ollama(prompt, temperature=0.7):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "temperature": temperature
            },
            timeout=60
        )
        result = response.json()
        return result["response"], None
    except requests.exceptions.ConnectionError:
        return None, "⚠️ Cannot connect to Ollama. Please make sure Ollama is running and try again."
    except requests.exceptions.Timeout:
        return None, "⚠️ Request timed out. The model is taking too long to respond. Please try again."
    except Exception as e:
        return None, f"⚠️ Something went wrong: {str(e)}"

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
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "nav_selection" not in st.session_state:
    st.session_state.nav_selection = "🏠 Home"
if "nav_trigger" not in st.session_state:
    st.session_state.nav_trigger = False

# ─── SIDEBAR ───
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bank-building.png", width=80)
    st.title("AI Banking Assistant")
    st.caption("Powered by Llama3 — Running Locally 🔒")
    st.divider()

    options = [
        "🏠 Home",
        "✉️ Email Agent",
        "📄 Document Summarizer",
        "❓ Document Q&A"
    ]

    selected_tool = st.radio(
        "Choose a tool:",
        options=options,
        index=options.index(st.session_state.nav_selection),
        key="sidebar_radio"
    )

    # Only update from radio if no button triggered navigation
    if not st.session_state.nav_trigger:
        st.session_state.nav_selection = selected_tool
    else:
        st.session_state.nav_trigger = False

    st.divider()
    st.caption("🔒 All data stays on your machine")
    st.caption("🦙 Model: Llama3 via Ollama")
    st.caption("🐍 Built with Python + Streamlit")

# ─── HOME PAGE ───
if st.session_state.nav_selection == "🏠 Home":
    # Hero Section
    st.markdown('<p class="main-header">🏦 AI Banking Assistant</p>',
                unsafe_allow_html=True)
    st.markdown("#### Your personal AI toolkit for banking and finance work.")
    st.markdown("🔒 **Powered by Llama3 — All processing happens locally. No data leaves your machine.**")
    st.divider()

    # Quick Stats
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        email_count = len(st.session_state.email_history) // 2
        st.metric("✉️ Emails Reviewed", email_count)
    with col_s2:
        qa_count = len(st.session_state.qa_pairs)
        st.metric("❓ Questions Asked", qa_count)
    with col_s3:
        doc_status = "✅ Loaded" if st.session_state.loaded_document else "❌ None"
        st.metric("📄 Active Document", doc_status)
    with col_s4:
        st.metric("🦙 Model", "Llama3")

    st.divider()

    # Tool Cards
    st.markdown("### 🛠️ Available Tools")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style='padding: 1.5rem; border: 1px solid #333; border-radius: 10px; height: 200px;'>
            <h3>✉️ Email Agent</h3>
            <p style='color: #888; font-size: 0.9rem;'>Review and rewrite draft emails with AI memory. 
            Choose Professional, Friendly or Formal tone. 
            Session history remembered automatically.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='padding: 1.5rem; border: 1px solid #333; border-radius: 10px; height: 200px;'>
            <h3>📄 Document Summarizer</h3>
            <p style='color: #888; font-size: 0.9rem;'>Upload any TXT or PDF document and get 
            a structured AI summary. Choose between General, Brief or Bullet Point formats. 
            Perfect for policy docs and BRDs.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style='padding: 1.5rem; border: 1px solid #333; border-radius: 10px; height: 200px;'>
            <h3>❓ Document Q&A</h3>
            <p style='color: #888; font-size: 0.9rem;'>Load any document and ask questions in 
            plain English. AI answers using only the document content. 
            Full Q&A session saved automatically.</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Recent Activity
    st.markdown("### 📊 Session Activity")
    
    if not st.session_state.email_history and not st.session_state.qa_pairs and not st.session_state.loaded_document:
        st.info("👋 Welcome! No activity yet this session. Use the sidebar to get started.")
    else:
        activity = []
        
        if st.session_state.loaded_document:
            activity.append(f"📄 Document loaded: **{st.session_state.document_name}** ({len(st.session_state.loaded_document.split())} words)")
        
        if st.session_state.email_history:
            activity.append(f"✉️ **{email_count} email(s)** reviewed this session")
        
        if st.session_state.qa_pairs:
            activity.append(f"❓ **{qa_count} question(s)** asked about document")
            # Show last question
            last_q = st.session_state.qa_pairs[-1][0]
            activity.append(f"💬 Last question: *{last_q}*")
        
        for item in activity:
            st.markdown(f"- {item}")

    st.divider()

    # Pro Tips
    st.markdown("### 💡 Pro Tips")
    tip_col1, tip_col2 = st.columns(2)
    
    with tip_col1:
        st.success("**📄 PDF Support** — Upload any digital PDF directly. Works best with text-based PDFs.")
        st.success("**🧠 AI Memory** — Email Agent remembers your session. Ask it to modify the last email anytime.")
    
    with tip_col2:
        st.success("**❓ Precise Q&A** — Ask specific questions. The AI only uses your document, not general knowledge.")
        st.success("**💾 Auto Save** — All outputs automatically saved to your local outputs/ folder.")

# ─── EMAIL AGENT PAGE ───
elif st.session_state.nav_selection == "✉️ Email Agent":
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

        if draft:
            word_count = len(draft.split())
            char_count = len(draft)
            st.caption(f"📊 {word_count} words · {char_count} characters")

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
                history_text = ""
                for msg in st.session_state.email_history:
                    history_text += f"{msg['role']}: {msg['content']}\n\n"

                system_prompt = load_prompt("email_rewriter")
                system_prompt = system_prompt.replace("{tone}", tone.lower())
                prompt = f"{system_prompt}\n\n{history_text}User: Please rewrite this email in a {tone.lower()} tone:\n{draft}"

                with st.spinner("✍️ Rewriting your email in a " + tone.lower() + " tone..."):
                    rewritten, error = call_ollama(prompt, temperature=0.4)

                if error:
                    st.error(error)
                else:
                    st.session_state.email_history.append({
                        "role": "User",
                        "content": f"Rewrite in {tone} tone: {draft}"
                    })
                    st.session_state.email_history.append({
                        "role": "Assistant",
                        "content": rewritten
                    })

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

        if st.session_state.email_history:
            st.divider()
            st.markdown("### 📊 Session History")
            email_count = len(st.session_state.email_history) // 2
            st.metric("Emails reviewed this session", email_count)
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.email_history = []
                st.rerun()

# ─── DOCUMENT SUMMARIZER PAGE ───
elif st.session_state.nav_selection == "📄 Document Summarizer":
    st.markdown("## 📄 Document Summarizer")
    st.markdown('<p class="tool-description">Upload any document or paste text and get a structured AI summary instantly.</p>',
                unsafe_allow_html=True)
    st.divider()

    input_method = st.radio(
        "How would you like to provide the document?",
        options=["📁 Upload a file", "📋 Paste text directly"],
        horizontal=True
    )

    document_text = None

    if input_method == "📁 Upload a file":
        uploaded_file = st.file_uploader(
            "Upload a document",
            type=["txt", "pdf"],
            help="Supports .txt and .pdf files"
        )
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                with st.spinner("Reading PDF..."):
                    document_text, page_count, error = extract_text_from_pdf(
                        file_object=uploaded_file
                )
                if error:
                    st.error(error)
                else:
                    st.session_state.loaded_document = document_text
                    st.session_state.document_name = uploaded_file.name
                    st.success(f"✅ File loaded: {uploaded_file.name}")
                    st.caption(f"📄 {page_count} pages · {len(document_text.split())} words extracted")
            else:
                document_text = uploaded_file.read().decode("utf-8")
                if len(document_text.strip()) == 0:
                    st.warning("⚠️ The uploaded file is empty. Please upload a file with content.")
                else:
                    st.session_state.loaded_document = document_text
                    st.session_state.document_name = uploaded_file.name
                    st.success(f"✅ File loaded: {uploaded_file.name}")
                    st.caption(f"📄 {len(document_text.split())} words extracted")
    else:
        pasted_text = st.text_area(
            "Paste your document text here",
            height=250,
            placeholder="Paste any policy document, report, email thread or BRD here..."
        )
        if st.button("📋 Load Text", use_container_width=True):
            if not pasted_text.strip():
                st.warning("⚠️ Please paste some text before loading.")
            else:
                st.session_state.loaded_document = pasted_text
                st.session_state.document_name = "Pasted Text"
                st.success("✅ Text loaded successfully")

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
            prompt_map = {
                "General": "summarizer_general",
                "Brief": "summarizer_brief",
                "Bullet Points": "summarizer_bullet"
            }

            system_prompt = load_prompt(prompt_map[summary_type])
            prompt = f"{system_prompt}\n\nDOCUMENT:\n{document_text}"

            with st.spinner("📄 Analyzing document and generating " + summary_type.lower() + " summary..."):
                summary, error = call_ollama(prompt, temperature=0.2)

            if error:
                st.error(error)
            else:
                st.divider()
                st.markdown("### ✅ Summary")
                st.markdown(summary)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs("outputs", exist_ok=True)
                with open(f"outputs/summary_{timestamp}.txt", "w") as f:
                    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Summary Type: {summary_type}\n\n")
                    f.write(f"SUMMARY:\n{summary}\n")

                st.success("✅ Summary saved to outputs folder")
                st.code(summary, language=None)

# ─── DOCUMENT Q&A PAGE ───
elif st.session_state.nav_selection == "❓ Document Q&A":
    st.markdown("## ❓ Document Q&A")
    st.markdown('<p class="tool-description">Load any document and ask questions about it in plain English. Get precise answers instantly.</p>',
                unsafe_allow_html=True)
    st.divider()

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
                "Upload a document",
                type=["txt", "pdf"],
                key=f"qa_uploader_{st.session_state.uploader_key}"
            )
            if uploaded_file and not st.session_state.loaded_document:
                if uploaded_file.type == "application/pdf":
                    with st.spinner("Reading PDF..."):
                        content, page_count, error = extract_text_from_pdf(
                            file_object=uploaded_file
                    )
                    if error:
                        st.error(error)
                    else:
                        st.session_state.loaded_document = content
                        st.session_state.document_name = uploaded_file.name
                        st.success(f"✅ Loaded: {uploaded_file.name}")
                        st.caption(f"📄 {page_count} pages · {len(content.split())} words extracted")
                else:
                    content = uploaded_file.read().decode("utf-8")
                    if len(content.strip()) == 0:
                        st.warning("⚠️ The uploaded file is empty. Please upload a file with content.")
                    else:
                        st.session_state.loaded_document = content
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
                if not pasted_text.strip():
                    st.warning("⚠️ Please paste some text before loading.")
                else:
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
                st.session_state.uploader_key += 1
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
                    system_prompt = load_prompt("document_qa")
                    prompt = f"{system_prompt}\n\nDOCUMENT:\n{st.session_state.loaded_document}\n\nQUESTION:\n{question}\n\nANSWER:"

                    with st.spinner("🔍 Searching document for answer..."):
                        answer, error = call_ollama(prompt, temperature=0.1)

                    if error:
                        st.error(error)
                    else:
                        st.session_state.qa_pairs.append((question, answer))

            if st.session_state.qa_pairs:
                st.divider()
                st.markdown(f"### 📊 Session — {len(st.session_state.qa_pairs)} questions asked")

                for i, (q, a) in enumerate(reversed(st.session_state.qa_pairs), 1):
                    with st.expander(f"Q{len(st.session_state.qa_pairs) - i + 1}: {q}"):
                        st.markdown(a)

                st.divider()
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
