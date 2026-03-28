# AI Journey 🤖

A collection of AI-powered tools built with Python and a locally running 
LLM (Llama3 via Ollama). All tools run completely offline — no API keys, 
no cloud, no data leaving your machine.

Built as part of a structured AI learning journey focused on real-world 
banking and finance use cases.

---

## 🛠️ Tools Built

### 1. Email Reviewer (`email_reviewer.py`)
Reviews and rewrites draft emails in your chosen tone.
- Choose between Professional, Friendly or Formal tone
- Powered by local Llama3 model
- Banking domain optimized

### 2. Email Agent (`tools/email_agent.py`)
An advanced email assistant with memory and file saving.
- Remembers all emails reviewed in the same session
- Modify previously rewritten emails
- Auto saves all outputs with timestamps
- Session history tracking

### 3. Document Summarizer (`tools/summarizer.py`)
Summarizes any document in three different formats.
- General summary with structured sections
- Brief 5 sentence summary
- Bullet points only
- Load from file or paste text directly
- Auto saves summaries with timestamps

### 4. Master Agent (`master_agent.py`)
A single app combining all tools plus Document Q&A.
- Email reviewing
- Document summarizing
- Ask any question about any document
- Full Q&A session saved with audit trail

---

## 🏦 Use Cases in Banking
- Review and rewrite internal emails professionally
- Summarize long policy documents and compliance reports
- Query BRDs and architecture documents with natural language
- Analyze loan agreements and regulatory documents
- Generate audit trails of document analysis sessions

---

## ⚙️ Setup

### Requirements
- Python 3.14+
- Ollama running locally
- Llama3 model pulled via Ollama

### Installation

1. Clone the repository
```
git clone https://github.com/myash1396/ai-journey.git
cd ai-journey
```

2. Create and activate virtual environment
```
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies
```
pip install requests
```

4. Make sure Ollama is running
```
ollama serve
```

5. Run any tool
```
python master_agent.py
```

---

## 📁 Project Structure
```
ai-journey/
│
├── tools/
│   ├── email_agent.py       → Memory enabled email agent
│   └── summarizer.py        → Document summarizer
├── docs/                    → Test documents
├── outputs/                 → Generated files (local only)
├── email_reviewer.py        → Basic email reviewer
├── master_agent.py          → Master agent combining all tools
└── README.md                → This file
```

---

## 🚀 Journey
This repository is being built day by day as part of a structured 
AI learning journey. New tools and features added regularly.

**Week 1** — Python + AI foundations, local LLM integration  
**Week 2** — Coming soon: Streamlit UI, web interface  
**Week 3** — Coming soon: Agents, automation, decision making  
**Week 4** — Coming soon: RAG, vector databases, multi document Q&A  
**Week 5** — Coming soon: Portfolio, freelance, visibility  

---

## 👤 About
Pega developer with banking domain expertise, upskilling in AI 
application development. Focused on building practical AI tools 
for regulated industries.

---
*Built with Python 🐍 | Powered by Llama3 🦙 | Running locally 🔒*
```
