# AI Journey 🤖

A collection of AI-powered tools built with Python, focused on real-world
banking and finance use cases. Built as part of a structured AI learning
journey — from zero to deployed web applications in short time.

---

## 🚀 Live Demo

**Pega BRD Analyzer** — Live on Streamlit Cloud:
👉 [https://ai-journey-myash-brd-analyzer.streamlit.app](https://ai-journey-myash-brd-analyzer.streamlit.app)

---

## 🛠️ What's Built

### 🏦 AI Banking Assistant (`app.py`)
A full multi-tool web application running in the browser.

**Email Agent**
- Review and rewrite draft emails with AI memory
- Choose Professional, Friendly or Formal tone
- Session history remembered automatically
- Auto saves all outputs with timestamps

**Document Summarizer**
- Upload TXT or PDF documents
- Three summary formats — General, Brief, Bullet Points
- Structured output with Purpose, Key Points, Risk Flags
- Auto saves summaries with timestamps

**Document Q&A**
- Load any document and ask questions in plain English
- AI answers using only the document content — no hallucination
- Full Q&A session saved as audit trail
- Supports TXT and PDF files

---

### 📋 Pega BRD Analyzer (`brd_app.py` / `brd_app_claude.py`)
An AI powered Senior BA that analyzes Business Requirements Documents.

**Two versions available:**
- `brd_app.py` — runs on Llama3 locally, completely offline, free
- `brd_app_claude.py` — runs on Claude API, significantly better output

**Analysis produced:**
- 📋 Requirement Summary
- 👤 User Stories — properly formatted As a / I want / So that
- 📐 Business Rules — numbered BR-XXX format
- ⚠️ Edge Cases — gaps and unhandled scenarios EC-XXX format
- ❓ Developer Questions — Pega specific DQ-XXX format
- 🚨 Risk Flags — compliance and technical risks RF-XXX format
- 📊 Complexity Assessment — rating and story point estimate

---

### 🖥️ Terminal Tools
Earlier versions built during learning — fully functional CLI tools.

- `email_reviewer.py` — Day 1 email reviewer
- `tools/email_agent.py` — memory enabled email agent
- `tools/summarizer.py` — document summarizer
- `master_agent.py` — master terminal agent combining all tools

---

## 🏦 Banking Use Cases
- Review and rewrite internal emails professionally
- Summarize policy documents, compliance reports and BRDs
- Query BRDs and architecture documents with natural language
- Analyze loan agreements and regulatory documents
- Auto extract user stories and business rules from requirements
- Generate audit trails of all document analysis sessions

---

## ⚙️ Setup

### Requirements
- Python 3.14+
- Ollama running locally (for local versions)
- Llama3 model pulled via Ollama
- Anthropic API key (for Claude version only)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/myash1396/ai-journey.git
cd ai-journey
```

**2. Create and activate virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. For local versions — make sure Ollama is running**
```bash
ollama serve
```

**5. Run the main web app**
```bash
streamlit run app.py
```

**6. Run the BRD Analyzer**
```bash
streamlit run brd_app.py
```

**7. For Claude API version — set your API key**
```bash
$env:ANTHROPIC_API_KEY="your-key-here"
streamlit run brd_app_claude.py
```

---

## 📁 Project Structure
````markdown
```
ai-journey/
│
├── app.py                   → AI Banking Assistant web app
├── brd_app.py               → Pega BRD Analyzer (local Llama3)
├── brd_app_claude.py        → Pega BRD Analyzer (Claude API)
├── master_agent.py          → Terminal master agent
├── email_reviewer.py        → Terminal email reviewer
├── requirements.txt         → Python dependencies
│
├── tools/
│   ├── email_agent.py       → Memory enabled email agent
│   ├── summarizer.py        → Document summarizer
│   ├── brd_analyzer.py      → BRD analysis logic (local)
│   ├── brd_analyzer_claude.py → BRD analysis logic (Claude API)
│   └── pdf_reader.py        → PDF text extraction
│
├── prompts/
│   ├── email_rewriter.md    → Email agent prompt
│   ├── summarizer_general.md → General summary prompt
│   ├── summarizer_brief.md  → Brief summary prompt
│   ├── summarizer_bullet.md → Bullet point summary prompt
│   ├── document_qa.md       → Document Q&A prompt
│   └── brd_analyzer.md      → Senior BA analysis prompt
│
├── docs/                    → Test documents
└── outputs/                 → Generated files (local only)
```
````
---

## 🧠 Technical Highlights
- **Local LLM integration** — Ollama + Llama3, fully offline
- **Cloud LLM integration** — Anthropic Claude API
- **Prompt engineering** — chain of thought, negative prompting,
  few shot examples, temperature tuning
- **Streamlit web apps** — multi page, session state, file upload
- **PDF support** — pdfplumber for text extraction
- **Error handling** — defensive programming, graceful degradation
- **External prompt files** — prompt management system
- **Live deployment** — Streamlit Community Cloud

---

## 🗺️ Journey Progress

**Week 1 ✅** — Python + AI foundations, local LLM integration,
terminal tools, document Q&A, master agent

**Week 2 ✅** — Streamlit UI, prompt engineering, PDF support,
error handling, BRD Analyzer, Claude API, live deployment

**Week 3 🔜** — Agents, automation, decision making, web search

**Week 4 🔜** — RAG, vector databases, multi document Q&A

**Week 5 🔜** — Portfolio, freelance, visibility, launch

---

## 👤 About
Pega developer with banking domain expertise, upskilling in AI
application development. Focused on building practical AI tools
for regulated industries.

---

*Built with Python 🐍 | Powered by Llama3 🦙 + Claude 🤖 |
Local & Cloud ☁️ | Banking Domain 🏦*