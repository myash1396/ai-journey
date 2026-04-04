# My AI Journey - Context File

---

## Who I Am
- **Role:** Pega developer working in banking domain
- **Location:** India
- **Goal:** High paying job (India or abroad) + side income safety net
- **Availability:** 2 hours per day
- **Python level:** Beginner but fast learner
- **Coaching style:** Step by step, explain as we build, curiosity driven

---

## My Setup
- OS: Windows
- Tools installed: Ollama, VS Code, Python 3.14, Docker
- Local AI model: Llama3 (running via Ollama on localhost:11434)
- Project folder: C:\Users\ymusa\ai-journey
- Virtual environment: venv (activate with `venv\Scripts\activate`)
- If activation fails run first: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

---

## Project Structure
ai-journey/
│
├── prompts/                 → external prompt files
│   ├── email_rewriter.md
│   ├── summarizer_general.md
│   ├── summarizer_brief.md
│   ├── summarizer_bullet.md
│   ├── brd_analyzer.md      → Senior BA prompt
│   └── document_qa.md
├── tools/
│   ├── email_agent.py       → Day 2 memory enabled email agent
│   ├── summarizer.py        → Day 3 document summarizer
│   └── pdf_reader.py        → Day 10 PDF text extraction
│   ├── brd_analyzer.py      → BRD analysis core logic
├── docs/
│   ├── sample_policy.txt    → test text document
│   ├── sample_brd.txt       → test BRD document
│   └── test_banking_policy.pdf → test PDF document
├── create_test_pdf.py       → one time script to create test PDF
├── outputs/                 → generated files (local only)
├── venv/                    → engine room, never touch
├── app.py                   → Day 6-7 master Streamlit web app
├── brd_app.py               → Day 12 Pega BRD Analyzer
├── email_reviewer.py        → Day 1 basic email reviewer
├── email_ui.py              → Day 5 first Streamlit UI (practice)
├── master_agent.py          → Day 4 master terminal agent
├── README.md                → project front door for GitHub
└── my_context.md            → insurance policy / context file

## Coming Soon (Day 7+)
├── prompts/                 → external prompt files (Day 7)
│   ├── email_rewriter.txt
│   ├── summarizer_general.txt
│   ├── summarizer_brief.txt
│   ├── summarizer_bullet.txt
│   └── document_qa.txt

---

## My Goal
- Build real demonstrable AI skills
- Stay ahead of AI disruption in banking and Pega space
- Be hireable at a higher level with real AI portfolio
- Create side income safety net through freelance or own product
- Understand what I build — not just copy paste code

---

## What We Have Built So Far

### Day 1 — Python + AI Foundations
- `email_reviewer.py`
- Interactive email reviewer with tone selection (professional, friendly, formal)
- Banking domain system prompt
- Connected Python to local Llama3 model via Ollama API
- Understood: functions, parameters, dictionaries, lists, API calls, system prompts

### Day 2 — Memory + File Handling
- `email_agent.py`
- Memory enabled — AI remembers all emails in the same session
- Modify last email feature — AI refers back to conversation history
- Auto save to file — every rewritten email saved to `reviewed_emails.txt` with timestamp
- Session history tracker
- Clean menu driven app
- Fixed first indentation bug independently
- Understood: how AI memory/context window works, file handling (append/write), how ALL AI chat apps work under the hood
- Bug fix: save_to_file for modification request now saves 
  the actual modification text using f-string interpolation

### Day 3 — Document Summarizer + Project Structure
- Organized project into tools/, outputs/, docs/ folders
- Built tools/summarizer.py with 3 summary types:
  general (structured), brief (5 sentences), bullet points
- Load from file path or paste text directly
- Auto save summaries with timestamps to outputs/ folder
- Tested on real banking policy document and real work content
- Understood os.path.join, os.path.exists
- Understood if __name__ == "__main__" fully

### Day 4 — Master Agent + Document Q&A + RAG
- Built master_agent.py combining all tools in one app
- Imported functions from email_agent.py and summarizer.py
- Built Document Q&A feature - ask questions about any document
- Q&A sessions saved with full audit trail in outputs/
- Understood DRY principle - Don't Repeat Yourself
- Understood RAG - Retrieval Augmented Generation
- Connected builds to real banking use cases - BRDs, 
  architecture docs, compliance policies
- Moved email_agent.py into tools/ folder

### Day 5 — GitHub + README + First Streamlit UI (Saturday)
- Installed Git and configured with GitHub account
- Created private GitHub repository - ai-journey; will make public once portfolio ready
- Learned full Git workflow: git add, commit, push
- Learned .gitignore concept - exclude venv/ and outputs/
- Pushed all Week 1 code to GitHub
- Written professional README.md for the project
- Installed Streamlit
- Built email_ui.py - first browser based UI for email agent
  * Text area for draft email input
  * Radio buttons for tone selection
  * Primary button to trigger AI rewrite
  * Success panel showing rewritten email
  * Copy ready code block output
- Learned about st.session_state concept coming in Day 6
- Learned about technical debt concept
- Understood DRY principle violation and why we did it intentionally
- Note for later : update readme as needed and clean outputs when making repo public

### Day 6 — Master Streamlit UI (Sunday 4hrs)
- Built app.py - complete multi tool web application in browser
- Sidebar navigation with 4 sections: Home, Email Agent, 
  Summarizer, Document Q&A
- Home page with 3 column layout and tool cards
- Email Agent page:
  * Two column layout - input left, output right
  * Memory using st.session_state
  * Session history counter
  * Clear history button
  * Auto saves to outputs folder
- Document Summarizer page:
  * Upload file OR paste text with Load Text button
  * Three summary types with captions directly on radio buttons
  * Brief changed to concise paragraph format
  * Auto saves summaries to outputs folder
- Document Q&A page:
  * Upload or paste document
  * Ask unlimited questions about document
  * Q&A history shown in expanders
  * Save Q&A session to file
  * Clear Q&A history button
- Learned st.session_state for memory management in Streamlit
- Learned st.columns for layout
- Learned st.expander for collapsible content
- Identified prompt management improvement for Day 7
- Known bug: Clear Document on uploaded files - to fix later

### Day 7 — Prompt Management + Bug Fix (Monday 2hrs)
- Created prompts/ folder with 5 external .md prompt files:
  email_rewriter.md, summarizer_general.md, summarizer_brief.md,
  summarizer_bullet.md, document_qa.md
- Built load_prompt() function with try/except error handling
- Refactored app.py - all prompts now loaded from external files
- Understood prompt templating - {placeholder} replaced dynamically
- Understood graceful degradation concept
- Fixed Clear Document bug using dynamic widget key pattern
  st.session_state.uploader_key += 1 forces Streamlit to 
  render fresh file uploader widget on clear
- All changes committed and verified on GitHub

### Day 8 — Prompt Engineering Deep Dive (Tuesday 2hrs)
- Learned how LLMs actually work - next word prediction at scale
- Understood three levels of context - role, task, constraint
- Zero shot vs few shot - when to use and when NOT to use examples
- Chain of thought prompting - implicit vs explicit reasoning
- Updated document_qa.md with implicit chain of thought
- Temperature control - set 0.1 for Q&A, 0.2 for summarizer, 
  0.4 for email agent
- Negative prompting - eliminating default AI behaviors
- Updated all summarizer prompts with negative prompting
- All prompt files now production quality
- Understood technical debt in app.py - noted for future refactor
- Understood separation of concerns concept

### Day 9 — Error Handling + Input Validation (Wednesday 2hrs)
- Built call_ollama() reusable function with try/except
- Handles ConnectionError, Timeout, and general exceptions
- Added timeout=60 to all Ollama API calls
- Tuple return pattern - returns (result, error)
- Fixed all three tools to use call_ollama()
- Empty file validation in summarizer and Q&A
- Blank text validation in summarizer and Q&A  
- Understood defensive programming concept
- Understood graceful degradation in practice
- App now production quality in terms of error handling

### Day 10 — PDF Support (Thursday 2hrs)
- Installed pdfplumber library
- Built tools/pdf_reader.py with extract_text_from_pdf()
- Handles file_path and file_object inputs
- Graceful handling of empty PDFs and scanned/image PDFs
- Added PDF upload support to Document Summarizer
- Added PDF upload support to Document Q&A
- MIME type checking - application/pdf
- Created test PDF using reportlab - docs/test_banking_policy.pdf
- Tested Q&A on PDF - accurate answers with section references
- Fixed duplicate success message bug independently
- Understood OCR concept for scanned PDFs - future topic

### Day 11 — Polish + Navigation Fix + Home Dashboard (Friday 2hrs)
- Fixed home page navigation using nav_trigger pattern
- nav_trigger prevents sidebar radio from overwriting button navigation
- Added unique keys to all buttons - fixed DuplicateElementId error
- Fixed email agent col2 - was incorrectly nested inside button block
- Built rich home page dashboard:
  + Live session metrics - emails reviewed, questions asked
  + Active document status
  + Tool cards with descriptions
  + Session activity panel showing recent actions
  + Pro tips section
- Complete clean app.py rewrite - all navigation debt resolved
- Better spinner messages - descriptive per tool and action
- Email input word count + character count - live as you type
- PDF page count + word count displayed on load
- TXT word count displayed on load
- Summarizer and Q&A share loaded_document intentionally
  - Feature: load once use in both tools
  - User can clear document manually if needed
- Committed and verified on GitHub

### Day 12 — Pega BRD Analyzer (Saturday 4hrs)
- Built brd_app.py - standalone Streamlit app for BRD analysis
- Built tools/brd_analyzer.py - core analysis logic
- Built prompts/brd_analyzer.md - Senior BA prompt
- Analysis sections: Requirement Summary, User Stories, 
  Business Rules, Edge Cases, Developer Questions, 
  Risk Flags, Complexity Assessment
- Added section tabs - each section in its own tab
- extract_section() function - parses AI output into sections
- Save analysis as .md report with timestamp
- View Full Raw Analysis expander
- Fixed encoding errors - utf-8 on read and write
- Fixed closing remarks with negative prompting
- Fixed user story consistency with few shot examples
- Committed and verified on GitHub
- READY TO DEMO TO TEAM 🎯

## UI Polish - To Do
- Smoother loading states with more descriptive spinners
- Word count display on email input
- Character count on document upload
- Better success feedback animations
- Mobile responsiveness check

## Known Bugs / To Fix
- None currently. All known bugs resolved. ✅

## Git Workflow (Daily Reminder)
git add .
git commit -m "describe what you built"
git push
Always run this before closing for the day.

---

## Key Concepts Understood So Far
- Virtual environments and why we use them
- How to connect Python to a local AI model
- What a system prompt is and why it matters
- How AI memory works — full conversation history sent every time
- Why AI has no memory between sessions (context window)
- Python: functions, lists, dictionaries, loops, conditionals, file handling
- How to read and debug code even if you didn't write it from scratch
- Using AI to generate code is valid — understanding what it does is the real skill

---

## Roadmap (Updated - Weekend Accelerated)

### Availability
- Weekdays: 2 hours per day (Mon-Fri)
- Weekends: 3-4 hours per day (Sat-Sun)
- This roadmap was updated on 28th Feb(Friday)

---

### Week 1 — Foundations ← COMPLETE
- Day 1 ✅ — Python + Ollama + first AI script
- Day 2 ✅ — Memory + file saving + agent menu
- Day 3 ✅ — Document summarizer + project structure
- Day 4 ✅ — Master agent + Document Q&A + RAG concepts
- Day 5 🟡 (Saturday - 4hrs) — GitHub setup + README + First streamlit UI
  + Polish all existing tools
  + Write proper README for project
  + Push everything to GitHub
  + First LinkedIn post about your journey
  + Install Streamlit
  + Email agent gets a browser based UI
  + Run your first AI web app locally
- Day 6 🟡 (Sunday - 4hrs) — Master Streamlit UI


---

### Week 2 — UI + Prompt Engineering + More <- INPROGRESS
- Day 7 — Prompt Management + Bug Fix
- Day 8 — Prompt Engineering Deep Dive
- Day 9 ✅ (Wed) — Error handling, input validation, call_ollama()
- Day 10 (Thu 2hrs) — PDF Support
  + Install pdfplumber
  + Add PDF upload to summarizer and Q&A
  + Test on real banking PDFs
  + Update file uploader to accept .pdf and .txt
- Day 11 (Fri 2hrs) — Polish + UI Improvements
  + Smooth loading states with descriptive spinners
  + Word count on email input
  + Character count on document load
  + Better success/error feedback
  + Mobile responsiveness check
  + Clean up app.py technical debt where possible
- Day 12 (Sat 4hrs) — Mini Product: Pega BRD Analyzer
  + Standalone tool built on top of existing app
  + Load any Pega BRD or requirements document
  + Auto extract user stories
  + Identify business rules
  + Flag edge cases and missing requirements
  + Generate developer questions before building
  + Full UI with Streamlit
  + Save analysis report to outputs
  + Push to GitHub as separate tool
- Day 13 (Sun 4hrs) — Portfolio + Visibility Day
  + Clean up GitHub repository
  + Update README with all new features
  + Record a short demo video
  + LinkedIn post with demo
  + Start freelance profile setup

---

### Week 3 — Agents + Automation
- Day 14 (Mon) — What agents really are + decision making
- Day 15 (Tue) — Build agent with multiple tools
- Day 16 (Wed) — Add web search to your agent
- Day 17 (Thu) — Connect agent to banking workflow
- Day 18 (Fri) — Test, debug, polish
- Day 19 (Sat 4hrs) — Build compliance checker agent
  + Load policy document
  + Check any process against it
  + Flag risks automatically
  + Save compliance report
- Day 20 (Sun 4hrs) — Extend compliance checker
  + Add UI
  + Test on real banking policies
  + Push to GitHub

---

### Week 4 — RAG Deep Dive + Portfolio
- Day 21 (Mon) — RAG properly + vector databases intro
- Day 22 (Tue) — Build proper RAG pipeline
- Day 23 (Wed) — Multi document RAG
- Day 24 (Thu) — BRD analyzer tool enhanced
- Day 25 (Fri) — Pega + AI connection in real world
- Day 26 (Sat 4hrs) — Flagship portfolio project begins
  + Full RAG app with UI
  + Banking/Pega domain specific
  + Clean documentation
- Day 27 (Sun 4hrs) — Flagship project complete
  + Push to GitHub with proper README
  + Record demo video

---

### Week 5 — Visibility + Money
- Day 28 (Mon) — Freelance profile setup
- Day 29 (Tue) — How to price your skills
- Day 30 (Wed) — APIs + making tools available to others
- Day 31 (Thu) — Packaging and sharing your tools
- Day 32 (Fri) — Final polish and prep
- Day 33 (Sat 4hrs) — Launch day
  + Finalize portfolio
  + Optimize LinkedIn with AI skills
  + Apply to 3 high paying roles
  + Send 3 freelance proposals
- Day 34 (Sun 4hrs) — Portfolio website
  + Simple personal site showcasing your projects
  + Goes live today

---

### Beyond Week 5
- Fine tuning models on domain specific data
- Cloud deployment (AWS / Azure)
- Enterprise AI consulting positioning
- Building your own AI product
- Build one complete project tied to Pega/banking background
- Update LinkedIn with real project post


---

## How To Use This File
1. Update "What We Have Built So Far" every day before closing chat
2. When starting a new chat with Claude paste this entire file first
3. Say: "Coach, here is my context. Continue from where we left off."
4. Claude will know exactly who you are, where we are and what comes next

---

## Important Reminders For Coach
- This person learns best by doing, not watching
- Always explain what code does in plain English before or after writing it
- Ask questions to check understanding — don't just give answers
- Connect everything back to banking/Pega domain where possible
- Celebrate small wins — confidence is part of the journey
- Be honest about limitations — this person is making real career decisions
- You are not only the coach but his future depends on you, Be resposible
