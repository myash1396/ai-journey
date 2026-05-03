# AI Journey 🚀

An AI learning journey — from Python basics to full-stack AI applications, 
built step by step over 27 days. Covers RAG, multi-agent pipelines, 
vector databases, MCP integrations, and more — all applied to real-world 
banking use cases.

Built by a Pega BPM developer in banking — combining deep domain expertise 
with hands-on AI engineering.

---

## Table of Contents

- [What's Built](#-whats-built)
- [Live Demo](#-live-demo)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Setup](#-setup)
- [Project Structure](#-project-structure)
- [Journey Progress](#-journey-progress)
- [About](#-about)

---

## 🛠 What's Built

### BankAI Knowledge Hub — Full-Stack RAG Application

A complete full-stack application where banking professionals upload policy documents, BRDs, and regulatory circulars, then ask natural language questions and get grounded answers from their knowledge base.

- React frontend with chat interface, document management, chunk preview
- FastAPI REST API with 6 endpoints and auto-generated Swagger docs
- RAG pipeline: document ingestion → embedding → vector search → grounded answers
- ChromaDB vector database with persistent storage
- Distance threshold: skips Claude API call when no relevant docs found
- Color-coded chunk relevance (green/amber/red based on distance score)
- Cost tracking per query and per session

**Tech:** React 18, FastAPI, ChromaDB, Sentence Transformers, Claude API

### Sprint 0 Accelerator — Multi-Agent BRD Pipeline

A full-stack multi-agent pipeline that transforms a Business Requirements 
Document into implementation-ready specifications through four AI agents.

- **Architecture:** StateGraph orchestration with create_react_agent for individual agents
- 4-agent pipeline: BA Agent → Tech Lead → Developer ↔ Reviewer
- BA Agent uses hybrid RAG (vector + BM25 keyword search via Reciprocal Rank Fusion) 
  to search internal knowledge base before web search
- Developer ↔ Reviewer feedback loop with iteration history tracking
- On approval: auto-creates Pega case via MCP for implementation tracking
- React "Mission Control" UI with real-time agent status, output tabs, iteration sub-tabs
- FastAPI backend with 11 endpoints, background threading for non-blocking pipeline runs
- DeepEval test suite: faithfulness, relevancy, hallucination metrics on Confident AI dashboard
- Cost tracking per agent and per pipeline run

**Tech:** React, FastAPI, LangGraph StateGraph, ChromaDB, BM25, Sentence Transformers, 
MCP, DeepEval, Claude API

### RAG-Enhanced BA Agent

BA Agent with a three-tier search hierarchy (designed for banking compliance):

1. Read input BRD document
2. Search internal knowledge base via ChromaDB for related existing documents
3. Web search restricted to regulatory / compliance / legal validation only

- Source confidence tags: `CONFIRMED`, `INFERRED`, `RECOMMENDED`
- Pega-specific analysis when relevant
- Cost: ~11 cents per analysis

### Pega DX API Integration

MCP server simulating Pega DX API for AI agent integration.

- 5 tools: `get_cases`, `get_case_details`, `create_case`, `get_assignments`, `run_report`
- AI agent for natural language case queries, fraud detection, risk analysis
- Realistic Indian banking case data with CIBIL scores, loan workflows
- Production-ready architecture: swap simulated data with real Pega DX API calls

### RAG Knowledge Base (Streamlit)

Streamlit-based RAG application with dark theme UI.

- Document upload and ingestion
- Chunk preview cards with distance scores
- Chat history with session tracking
- Tuning parameters: `n_results`, distance threshold

### Banking Agent Evolution

| Version | Day | What Changed |
| --- | --- | --- |
| `banking_agent.py` | 14 | Pre-built `create_react_agent`, 3 tools |
| `banking_agent_v2.py` | 15 | Manual StateGraph with streaming |
| `banking_agent_v3.py` | 16 | Added Tavily web search |
| `banking_agent_v4.py` | 20 | MCP tools, real loan decision workflow |
| `ba_agent_v2.py` | 23 | RAG-enhanced with three-tier search |

### AI Banking Assistant

Multi-tool Streamlit web application:

- Email Agent — rewrite emails with AI memory and tone selection
- Document Summarizer — general, brief, bullet point formats
- Document Q&A — natural language questions on uploaded documents
- PDF support via `pdfplumber`
- Session history and auto-save

### Pega BRD Analyzer

AI-powered Senior BA that analyzes Business Requirements Documents.

- Two versions: Llama3 (local, free) and Claude API (production quality)
- Generates: user stories, business rules, edge cases, risk flags, developer questions, complexity assessment
- Deployed live on Streamlit Cloud

### AI Evaluation

- DeepEval integration with Confident AI
- Faithfulness, relevancy, hallucination metrics
- `pytest`-based evaluation suite

---

## 🌐 Live Demo

**Pega BRD Analyzer** — deployed on Streamlit Cloud:

https://ai-journey-myash-brd-analyzer.streamlit.app

---

## 📐 Architecture

**RAG Pipeline:**

```
Documents → Chunking → Embeddings → ChromaDB (Vector Store)
                                          ↓
User Question → Embedding → Similarity Search → Top Chunks
                                          ↓
                                 Claude API (Grounded Answer)
                                          ↓
                                   React Frontend
```

**Multi-Agent Pipeline:**

```
BRD Input → BA Agent → Tech Lead → Developer ↔ Reviewer
              ↓           ↓           ↓           ↓
          read_doc    read_doc    read_doc    read_doc
          search_kb   web_search  web_search  pega_knowledge
          web_search  pega_kb     pega_kb
```

**BankAI Knowledge Hub Architecture:**

```
React Frontend (port 3000)
        ↓ HTTP / REST
FastAPI Backend (port 8000)
        ↓
ChromaDB + Claude API + Sentence Transformers
```

---

## 🧰 Tech Stack

| Category | Technologies |
| --- | --- |
| Languages | Python, JavaScript (React) |
| LLMs | Claude API (Sonnet 4), Llama3 (local via Ollama) |
| Frameworks | FastAPI, LangGraph, LangChain, Streamlit |
| Vector DB | ChromaDB |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| AI Evaluation | DeepEval, Confident AI |
| Protocols | MCP (Model Context Protocol) |
| Search | Tavily API |
| Frontend | React 18, Custom CSS |
| API Docs | OpenAPI / Swagger (auto-generated) |
| Version Control | Git, GitHub |
| Deployment | Streamlit Cloud |
| Hybrid Search | BM25 (rank-bm25) + Reciprocal Rank Fusion |

---

## ⚙ Setup

### Prerequisites

- Python 3.14+
- Ollama (for local LLM versions)
- Anthropic API key
- Tavily API key (for web search features)

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

**4. Set environment variables**

```powershell
$env:ANTHROPIC_API_KEY="your-key"
$env:TAVILY_API_KEY="your-key"
```

### Running the Applications

**BankAI Knowledge Hub (Full Stack):**

```bash
# Terminal 1 — API server
uvicorn api_server:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && python -m http.server 3000
```

Open http://localhost:3000 | API docs at http://localhost:8000/docs

**AI Banking Assistant:**

```bash
streamlit run app.py
```

**BRD Analyzer (Claude):**

```bash
streamlit run brd_app_claude.py
```

**Sprint 0 Accelerator:**

```bash
streamlit run pipeline_ui.py
```

**RAG Knowledge Base:**

```bash
streamlit run rag_app.py
```

**Pega AI Agent:**

```bash
python pega_agent.py
```

---

## 📁 Project Structure

```
ai-journey/
├── api_server.py               # FastAPI REST backend
├── app.py                      # AI Banking Assistant (Streamlit)
├── brd_app.py                  # BRD Analyzer (Llama3)
├── brd_app_claude.py           # BRD Analyzer (Claude API)
├── pipeline.py                 # 4-agent pipeline runner
├── pipeline_ui.py              # Sprint 0 Accelerator UI
├── rag_app.py                  # RAG Knowledge Base (Streamlit)
├── mcp_server.py               # MCP server (loan tools)
├── mcp_client_test.py          # MCP client tester
├── pega_mcp_server.py          # Pega DX API MCP server
├── pega_agent.py               # Pega AI operations agent
├── loan_database.json          # Simulated loan data
├── pega_cases.json             # Simulated Pega case data
├── conftest.py                 # pytest config
├── requirements.txt
├── sprint0/
│   ├── __init__.py
│   ├── agent_factory.py        # Shared agent creation utility
│   ├── pipeline.py             # StateGraph pipeline orchestrator
│   ├── api.py                  # FastAPI backend (RAG + pipeline)
│   ├── hybrid_rag.py           # BM25 + vector hybrid search
│   ├── frontend/
│   │   └── index.html          # React Mission Control UI
│   └── tests/
│       ├── conftest.py         # Test fixtures
│       └── test_pipeline.py    # DeepEval test suite
│
├── tools/
│   ├── rag_engine.py           # ChromaDB RAG pipeline
│   ├── ba_agent.py             # BA Agent v1
│   ├── ba_agent_v2.py          # RAG-enhanced BA Agent
│   ├── banking_agent.py        # Day 14 agent
│   ├── banking_agent_v2.py     # StateGraph agent
│   ├── banking_agent_v3.py     # Web search agent
│   ├── banking_agent_v4.py     # MCP integrated agent
│   ├── tech_lead_agent.py      # Tech Lead Agent
│   ├── developer_agent.py      # Developer Agent
│   ├── reviewer_agent.py       # Reviewer Agent
│   ├── brd_analyzer.py         # BRD analyzer (Llama3)
│   ├── brd_analyzer_claude.py  # BRD analyzer (Claude)
│   ├── email_agent.py          # Email agent
│   ├── summarizer.py           # Document summarizer
│   └── pdf_reader.py           # PDF extraction
│
├── prompts/                    # External prompt files
├── frontend/
│   └── index.html              # React frontend
├── docs/                       # Test documents
├── tests/
│   └── test_brd_analyzer.py    # DeepEval tests
├── chroma_db/                  # Vector database (local)
├── outputs/                    # Generated files
└── uploads/                    # Uploaded documents
```

---

## 📅 Journey Progress

**Week 1** ✅ Python + AI Foundations
Days 1-6: Local LLM, terminal tools, document Q&A, Git, first Streamlit UI

**Week 2** ✅ UI + Prompt Engineering
Days 7-13: Prompt management, error handling, PDF support, BRD Analyzer, Claude API, Streamlit Cloud deployment, DeepEval, Upwork profile

**Week 3** ✅ Agents + Automation
Days 14-20: LangGraph agents, StateGraph, web search, 4-agent pipeline, MCP server, banking workflow automation

**Week 4** ✅ RAG + Full Stack
Days 21-27: ChromaDB, vector search, RAG engine, RAG-enhanced agents, Pega DX API, FastAPI backend, React frontend

**Week 5** ✅ Flagship Product + Deep Knowledge
Days 28-34: Codebase retrospect, Sprint 0 Accelerator flagship — StateGraph pipeline, 
FastAPI backend (11 endpoints), React Mission Control UI, hybrid RAG (BM25 + vector), 
DeepEval test suite with Confident AI, CI/CD knowledge, Transformers architecture

---

## 👤 About

Pega BPM developer with banking domain expertise, building production-grade AI applications for regulated industries. From Python basics to full-stack AI systems in 27 days.

**Focus areas:** AI agents, RAG systems, banking automation, document intelligence, Pega + AI integration

- **GitHub:** github.com/myash1396
- **Upwork:** Available for AI development projects

---

Built with Python | Powered by Claude + Llama3 | FastAPI + React + ChromaDB | Banking Domain
