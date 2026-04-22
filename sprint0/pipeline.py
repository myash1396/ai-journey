"""Sprint 0 Accelerator pipeline orchestrator.

Uses a manual StateGraph to route between 4 agents (BA → TL → Dev → Reviewer)
with conditional revision loop and a final Pega case-creation step. Each
individual agent is built via agent_factory.create_agent (create_react_agent),
while the outer orchestration is an explicit StateGraph.
"""

import os
import datetime
import json
import operator
import sys
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sprint0.agent_factory import create_agent, run_agent, estimate_cost


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def read_document(file_path: str) -> str:
    """Read a document file. Use for BRDs, policies, or reference files."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def search_knowledge_base(query: str) -> str:
    """Search internal knowledge base for existing documents, old BRDs, policies. Use BEFORE web search."""
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")
        client = chromadb.PersistentClient(path="./chroma_db")
        try:
            collection = client.get_collection("banking_docs")
        except Exception:
            return "No knowledge base found"

        embedding = model.encode(query).tolist()
        results = collection.query(query_embeddings=[embedding], n_results=3)

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        if not docs:
            return "No relevant chunks found."

        out = []
        for i, doc in enumerate(docs):
            source = metas[i].get("source", "unknown") if i < len(metas) and metas[i] else "unknown"
            dist = dists[i] if i < len(dists) else 0.0
            out.append(f"[Source: {source} | Distance: {dist:.3f}]\n{doc}")
        return "\n\n---\n\n".join(out)
    except Exception as e:
        return f"Knowledge base error: {e}"


@tool
def search_web(query: str) -> str:
    """Search web ONLY for regulatory, compliance, legal, RBI circulars. Do NOT use for general business logic."""
    try:
        from langchain_tavily import TavilySearch
        search = TavilySearch(max_results=3)
        return str(search.invoke(query))
    except Exception as e:
        return f"Web search error: {e}"


@tool
def banking_knowledge(query: str) -> str:
    """Use for banking domain or regulatory clarifications."""
    try:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=500)
        resp = llm.invoke([
            SystemMessage(content="Senior Banking domain expert, 15 years experience"),
            HumanMessage(content=query),
        ])
        return resp.content if isinstance(resp.content, str) else str(resp.content)
    except Exception as e:
        return f"Banking knowledge error: {e}"


@tool
def pega_knowledge(query: str) -> str:
    """Use for Pega BPM architecture, case design, integration patterns."""
    try:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model="claude-sonnet-4-20250514", max_tokens=300)
        resp = llm.invoke([
            SystemMessage(content="Senior Pega Architect, 15 years experience"),
            HumanMessage(content=query),
        ])
        return resp.content if isinstance(resp.content, str) else str(resp.content)
    except Exception as e:
        return f"Pega knowledge error: {e}"


@tool
def create_pega_case(case_type: str, customer_name: str, project_name: str) -> str:
    """Create a Pega case for implementation tracking after pipeline approval."""
    try:
        from pega_mcp_server import create_case
        result = create_case(
            case_type=case_type,
            customer_name=customer_name,
            customer_id="AUTO",
            loan_amount=0,
            cibil_score=750,
            monthly_income=0,
        )
        # Append project name to the result
        return f"{result}\nProject: {project_name}"
    except Exception as e:
        return f"Pega case creation error: {e}"


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

BA_PROMPT = """
You are a Senior Business Analyst in a banking technology team.

ANALYSIS APPROACH — Follow this search hierarchy strictly:
1. FIRST: Read the input BRD document provided by the user
2. SECOND: Search the internal knowledge base for related existing
   documents, old BRDs, policies, and business rules that may relate
   to the new BRD requirements
3. THIRD: Search the web ONLY for regulatory/compliance/legal/security
   validation — RBI circulars, government policies, data protection laws,
   banking regulations. Do NOT search web for general business logic.
4. Use banking_knowledge tool for domain-specific clarifications

Produce a structured analysis with:
- REQUIREMENT SUMMARY: 2-3 sentence overview
- USER STORIES: Format- As a [user], I want [action] so that [value] - Max 5
- BUSINESS RULES: Numbered BR-001, BR-002 format - Max 5
- EDGE CASES: Numbered EC-001, EC-002 format - Max 5
- UI FLOW: Step by step user journey
- PEGA SPECIFIC: ONLY IF NEEDED draft a case management life cycle stage/process/steps at high level, personas to be created, portals to be created
- EXTERNAL INTEGRATIONS: Systems and APIs needed
- RISK FLAGS: Compliance and technical risks RF-001 format - Max 5
- DEVELOPER QUESTIONS: DQ-001 format, Pega specific - Max 5
- COMPLEXITY: Low/Medium/High with story point estimate

OUTPUT GUIDELINES:
- IMPORTANT: PEGA SPECIFIC section should only be filled if there are specific requirements that impact case design, stage design, or portal design. Do not add Pega content unless explicitly required by the BRD.
- Analyse and respond as per the requirement in the BRD. Do not add assumptions unless necessary. If you do, clearly tag them as [ASSUMPTION].
- Be comprehensive but concise. Do not hesitate to keep sections blank if need, do not add unnecessary information.
- A Tech Lead will use your output to design the technical architecture.
- Prioritize by business impact. Flag critical items clearly.
- For each item indicate source confidence:
  [CONFIRMED] = Explicitly stated in BRD
  [INFERRED] = Implied by BRD context
  [RECOMMENDED] = Industry best practice, not in BRD
- Do not start response with any preamble or introductory sentences.
- Start directly with the BRD Analysis Report header.
- Use today's actual date provided in the message for Analysis Date.
- Tables are preferred for structured data.
- Each section must have a clear header.
"""

TL_PROMPT = """You are a Senior Tech Lead and Pega Architect with 15 years experience in banking systems.
You receive a BA analysis document and produce a detailed technical design.

When given a BA analysis:
1. Use pega_knowledge tool for Pega architecture and component clarifications
2. Use web_search to find Pega documentation, API specs, or integration patterns
3. Use read_document if you need to reference any source documents

Produce a structured technical design with these exact sections:

TECHNICAL DESIGN DOCUMENT
==========================
Project: [from BA analysis]
Date: [today's date]
Tech Lead: Senior Pega Architect

1. ARCHITECTURE OVERVIEW
   - High level system architecture in text diagram format - keep it concise and simple
   - Key architectural decisions and rationale
   - [CONFIRMED/INFERRED/RECOMMENDED] tags for each decision

2. PEGA CASE DESIGN
   - Case type hierarchy (Top level + Child cases) - Add only as required - no unnecessary complexity
   - Stage and process breakdown per case type - Add only if explicitly required by BA analysis, do not add generic stages
   - Key personas and portal access - Add only if explicitly required by BA analysis, do not add generic personas or portals
   - Important decision rules and SLA rules - Add only if explicitly required by BA analysis, do not add generic rules
   - Assignment routing rules

3. INTEGRATION ARCHITECTURE - (Note: Do not overcomplicate with too many integrations, only add if explicitly required by BA analysis)
   - Each external system with integration pattern - only if explicitly required by BA analysis
   - API endpoint structure (REST/SOAP)
   - Error handling and retry strategy per integration
   - Authentication method per integration

4. DATA MODEL - (Note:Keep it focused on key data elements needed for case design and integrations, do not overcomplicate with unnecessary data elements/classes)
   - Key data classes only if needed
   - Important properties per class
   - Data relationships
   - External data sources mapped to Pega data pages

5. PEGA COMPONENTS BREAKDOWN - (Note: Do not overcomplicate with too many components, only add if explicitly required by BA analysis)
   - Decision rules (Decision Tables/Trees) needed
   - SLA rules with thresholds
   - Correspondence rules needed
   - UI components (sections, harnesses, portals)
   - Integration services

6. SECURITY DESIGN - (Note: Focus on critical security requirements mentioned in BA analysis, do not add generic security controls unless explicitly required)
   - Access groups and roles
   - Operator personas and portal access
   - Data encryption requirements
   - Audit requirements

7. TECHNICAL RISKS - Max 3 significant technical risks with severity and mitigation
   - TR-001 format
   - Each risk with severity and mitigation
   - [CONFIRMED/INFERRED/RECOMMENDED] tags

8. DEVELOPER STORIES BREAKDOWN - Max 5-6 critical developer stories derived from the BA user stories, focused on Pega implementation
   - Break BA user stories into technical tasks
   - Each story with Pega component to build
   - Story points per technical task
   - Dependencies between stories

9. IMPLEMENTATION ROADMAP
   - Phase 1 MVP components
   - Phase 2 components
   - Critical path items

10. OPEN QUESTIONS FOR BUSINESS - Max 3 critical questions that need business clarification before development
    - TQ-001 format
    - Technical questions needing business clarification

OUTPUT GUIDELINES:
- IMPORTANT: Do not start with any preamble like "I now have all the information" or "Let me compile".
- IMPORTANT: sections should only be filled if there is relevant information in the BA analysis. Do not add generic content or assumptions. If you do, clearly tag them as [ASSUMPTION].
- Be comprehensive but concise. Do not hesitate to keep sections blank if need, do not add unnecessary information.
- Start directly with TECHNICAL DESIGN DOCUMENT header.
- Be precise and technical. This document is for Pega developers.
- Each section should be clear and only required details unless absolutely necessary.
- Use [CONFIRMED/INFERRED/RECOMMENDED] tags consistently.
- Use text-based diagrams where helpful. Do not add unnecessary diagrams.
- Tables for structured data.
- Keep total output under 1800 words.
- Use today's actual date provided in the message."""

DEV_PROMPT = """You are a Senior Pega Developer with 10 years experience in banking implementations.
You receive a Technical Design Document and produce implementation specifications.

Given a tech design:
1. Use pega_knowledge for specific Pega implementation details if needed
2. Use web_search only if you need specific Pega documentation
3. Keep your output concise and focused

Produce implementation specs with these sections:

IMPLEMENTATION SPECIFICATION
=============================
Project: [from tech design]
Date: [today's date]
Developer: Senior Pega Developer

1. IMPLEMENTATION CHECKLIST
   - Ordered list of Pega components to build
   - Each item: Component Type | Component Name | Purpose
   - Mark dependencies between components
   - Maximum 8 items total

2. DATA MODEL SPECS
   - Class name and type (Data/Work/Abstract)
   - Key properties with data type
   - Maximum 5 classes

3. BUSINESS LOGIC SPECS
   - Each business rule with implementation approach
   - Decision Table structure where applicable
   - Maximum 8 rules

4. INTEGRATION SPECS
   - Each integration: Endpoint | Method | Auth | Error handling
   - Maximum 3 integrations

5. UI SPECS
   - Key screens/harnesses needed
   - Main sections per screen
   - Maximum 3 screens

6. ACCEPTANCE CRITERIA
   - One per user story from BA analysis
   - Format: Given [context] When [action] Then [result]
   - Maximum 8 criteria

7. OPEN ITEMS
   - OI-001 format
   - Items needing Tech Lead or BA clarification
   - Maximum 3 items

OUTPUT GUIDELINES:
- STRICTLY: Do not start with any preamble. Start directly with IMPLEMENTATION SPECIFICATION header.
- IMPORTANT: All instructions and configurations to be done based on PEGA 24.1.4 version.
- STRICTLY: Skip sections/leave blank saying "N/A" if not applicable as per the tech design. Do not invent details.
- Be specific and implementable. Every item must be actionable.
- Do not start with preamble.
- Start directly with IMPLEMENTATION SPECIFICATION header.
- Today's date will be provided in the message.
- Keep total output under 1000 words."""

REV_PROMPT = """You are a Senior Pega QA Lead and Code Reviewer with 10 years experience in Pega QA and code review.
You review Developer Implementation Specifications for completeness and correctness.

Review the implementation spec against this checklist:

REVIEW CHECKLIST:
1. Does every Business Rule have a corresponding implementation step?
2. Does every integration have error handling defined?
3. Does every UI screen have acceptance criteria?
4. Are Pega component names following naming conventions?
   (Data pages start with D_, Decision Tables start with DT_, etc.)
5. Are all Open Items clearly owned and impact assessed?
6. Is the data model complete for the described functionality?
7. Are there any obvious missing components?

Produce review report with these sections:

REVIEW REPORT
=============
Project: [from spec]
Date: [today's date]
Reviewer: Senior QA Lead

1. CHECKLIST RESULTS
   - Each checklist item: PASS / FAIL / PARTIAL
   - One line explanation per item

2. ISSUES FOUND
   - ISS-001 format
   - Severity: CRITICAL / MAJOR / MINOR
   - Description and suggested fix
   - Maximum 5 issues

3. COMMENDATIONS
   - What was done well
   - Maximum 3 items

4. VERDICT
   Must be exactly one of these two:
   VERDICT: APPROVED
   VERDICT: REVISION NEEDED

   If REVISION NEEDED - list top 3 items developer must fix before resubmission.

OUTPUT GUIDELINES:
- IMPORTANT: Do not start with preambles like "I have information for this review"
- Start the output directly with the REVIEW REPORT header.
- Be objective and specific.
- Do not start with preamble.
- Start directly with REVIEW REPORT header.
- Keep total output under 500 words.
- Always end with VERDICT line.
- IMPORTANT: Calibrate your review to the complexity of the spec.
  For simple small requirements - only flag CRITICAL and MAJOR issues.
  Do not fail a simple spec for minor naming conventions.
  VERDICT: APPROVED if only MINOR issues remain."""


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

ba_agent = create_agent([read_document, search_knowledge_base, search_web, banking_knowledge])
tl_agent = create_agent([read_document, search_web, pega_knowledge])
dev_agent = create_agent([read_document, search_web, pega_knowledge])
rev_agent = create_agent([read_document, pega_knowledge])


# ---------------------------------------------------------------------------
# Pipeline state
# ---------------------------------------------------------------------------

class PipelineState(TypedDict):
    brd_file: str
    brd_content: str
    ba_output: str
    tl_output: str
    dev_output: str
    rev_output: str
    dev_history: list    # stores all dev iterations
    rev_history: list    # stores all rev iterations
    verdict: str
    iteration: int
    max_iterations: int
    case_created: str
    agent_status: dict
    costs: dict
    errors: list


def _today() -> str:
    return datetime.date.today().isoformat()


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def ba_node(state: PipelineState) -> dict:
    print("Running BA Agent...")
    agent_status = dict(state.get("agent_status") or {})
    agent_status["ba"] = "running"

    query = (
        f"Today's date is {_today()}. Read the document at {state['brd_file']} "
        f"and produce a complete BA analysis. Search internal knowledge base "
        f"for related documents. Check web for regulatory requirements."
    )

    try:
        result = run_agent(ba_agent, query, BA_PROMPT)
        agent_status["ba"] = "complete"
        costs = dict(state.get("costs") or {})
        costs["ba"] = result["cost"]
        return {
            "ba_output": result["answer"],
            "agent_status": agent_status,
            "costs": costs,
        }
    except Exception as e:
        agent_status["ba"] = "error"
        errors = list(state.get("errors") or [])
        errors.append(f"ba: {e}")
        return {"ba_output": "", "agent_status": agent_status, "errors": errors}


def tl_node(state: PipelineState) -> dict:
    print("Running Tech Lead Agent...")
    agent_status = dict(state.get("agent_status") or {})
    agent_status["tl"] = "running"

    query = (
        f"Today's date is {_today()}. Create a technical design "
        f"from this BA analysis:\n\n{state['ba_output']}"
    )

    try:
        result = run_agent(tl_agent, query, TL_PROMPT)
        agent_status["tl"] = "complete"
        costs = dict(state.get("costs") or {})
        costs["tl"] = result["cost"]
        return {
            "tl_output": result["answer"],
            "agent_status": agent_status,
            "costs": costs,
        }
    except Exception as e:
        agent_status["tl"] = "error"
        errors = list(state.get("errors") or [])
        errors.append(f"tl: {e}")
        return {"tl_output": "", "agent_status": agent_status, "errors": errors}


def dev_node(state: PipelineState) -> dict:
    print("Running Developer Agent...")
    agent_status = dict(state.get("agent_status") or {})
    agent_status["dev"] = "running"
    iteration = state.get("iteration", 0)

    base = (
        f"Today's date is {_today()}. Produce implementation specs for this "
        f"technical design:\n\n{state['tl_output']}"
    )
    if iteration >= 1 and state.get("rev_output"):
        query = base + "\n\n---REVIEWER FEEDBACK---\n" + state["rev_output"]
    else:
        query = base

    try:
        result = run_agent(dev_agent, query, DEV_PROMPT)
        agent_status["dev"] = "complete"
        costs = dict(state.get("costs") or {})
        costs["dev"] = result["cost"]
        dev_history = list(state.get("dev_history") or [])
        dev_history.append({
            "iteration": iteration + 1,
            "output": result["answer"],
            "cost": result["cost"],
            "tools_used": result["tools_used"],
        })
        return {
            "dev_output": result["answer"],
            "iteration": iteration + 1,
            "agent_status": agent_status,
            "costs": costs,
            "dev_history": dev_history,
        }
    except Exception as e:
        agent_status["dev"] = "error"
        errors = list(state.get("errors") or [])
        errors.append(f"dev: {e}")
        return {
            "dev_output": "",
            "iteration": iteration + 1,
            "agent_status": agent_status,
            "errors": errors,
        }


def rev_node(state: PipelineState) -> dict:
    print("Running Reviewer Agent...")
    agent_status = dict(state.get("agent_status") or {})
    agent_status["rev"] = "running"

    query = (
        f"Today's date is {_today()}. Review this Developer "
        f"Implementation Specification:\n\n{state['dev_output']}"
    )

    try:
        result = run_agent(rev_agent, query, REV_PROMPT)
        answer = result["answer"]
        if "VERDICT: APPROVED" in answer:
            verdict = "APPROVED"
        elif "VERDICT: REVISION NEEDED" in answer:
            verdict = "REVISION NEEDED"
        else:
            verdict = "UNKNOWN"

        agent_status["rev"] = "complete"
        costs = dict(state.get("costs") or {})
        costs["rev"] = result["cost"]
        rev_history = list(state.get("rev_history") or [])
        rev_history.append({
            "iteration": state.get("iteration", 0),
            "output": answer,
            "verdict": verdict,
            "cost": result["cost"],
        })
        return {
            "rev_output": answer,
            "verdict": verdict,
            "agent_status": agent_status,
            "costs": costs,
            "rev_history": rev_history,
        }
    except Exception as e:
        agent_status["rev"] = "error"
        errors = list(state.get("errors") or [])
        errors.append(f"rev: {e}")
        return {
            "rev_output": "",
            "verdict": "UNKNOWN",
            "agent_status": agent_status,
            "errors": errors,
        }


def _extract_project_name(ba_output: str, brd_file: str) -> str:
    for line in (ba_output or "").splitlines():
        low = line.lower()
        if "project:" in low:
            return line.split(":", 1)[1].strip()
    return os.path.splitext(os.path.basename(brd_file))[0]


def mcp_node(state: PipelineState) -> dict:
    print("Creating Pega case...")
    if state.get("verdict") != "APPROVED":
        return {"case_created": ""}

    project = _extract_project_name(state.get("ba_output", ""), state["brd_file"])
    try:
        result = create_pega_case.invoke({
            "case_type": "Sprint0Implementation",
            "customer_name": "Internal",
            "project_name": project,
        })
        return {"case_created": str(result)}
    except Exception as e:
        errors = list(state.get("errors") or [])
        errors.append(f"mcp: {e}")
        return {"case_created": "", "errors": errors}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_after_review(state: PipelineState) -> str:
    if state.get("verdict") == "APPROVED":
        return "create_case"
    if state.get("iteration", 0) >= state.get("max_iterations", 2):
        return "end"
    return "revise"


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

def build_pipeline():
    graph = StateGraph(PipelineState)
    graph.add_node("ba", ba_node)
    graph.add_node("tl", tl_node)
    graph.add_node("dev", dev_node)
    graph.add_node("rev", rev_node)
    graph.add_node("mcp", mcp_node)

    graph.set_entry_point("ba")
    graph.add_edge("ba", "tl")
    graph.add_edge("tl", "dev")
    graph.add_edge("dev", "rev")
    graph.add_conditional_edges(
        "rev",
        route_after_review,
        {"create_case": "mcp", "revise": "dev", "end": END},
    )
    graph.add_edge("mcp", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_pipeline(brd_file: str, max_iterations: int = 2) -> dict:
    try:
        with open(brd_file, "r", encoding="utf-8") as f:
            brd_content = f.read()
    except Exception as e:
        print(f"Could not read BRD file: {e}")
        brd_content = ""

    initial: PipelineState = {
        "brd_file": brd_file,
        "brd_content": brd_content,
        "ba_output": "",
        "tl_output": "",
        "dev_output": "",
        "rev_output": "",
        "verdict": "",
        "iteration": 0,
        "max_iterations": max_iterations,
        "case_created": "",
        "agent_status": {},
        "costs": {},
        "errors": [],
        "dev_history": [],
        "rev_history": [],
    }

    pipeline = build_pipeline()
    final = pipeline.invoke(initial)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("outputs", exist_ok=True)

    # Save BA and TL (single run, no iterations)
    for key, label in [("ba_output", "ba"), ("tl_output", "tl")]:
        content = final.get(key) or ""
        if content:
            path = f"outputs/sprint0_{label}_{timestamp}.md"
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

    # Save Dev iterations
    for entry in (final.get("dev_history") or []):
        iter_num = entry["iteration"]
        path = f"outputs/sprint0_dev_iter{iter_num}_{timestamp}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(entry["output"])

    # Save Rev iterations
    for entry in (final.get("rev_history") or []):
        iter_num = entry["iteration"]
        path = f"outputs/sprint0_rev_iter{iter_num}_{timestamp}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(entry["output"])

    costs = final.get("costs") or {}
    total_cost = sum(costs.values())

    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"BA   | words: {len((final.get('ba_output') or '').split()):<5} | cost: ${costs.get('ba', 0):.4f}")
    print(f"TL   | words: {len((final.get('tl_output') or '').split()):<5} | cost: ${costs.get('tl', 0):.4f}")

    for entry in (final.get("dev_history") or []):
        i = entry["iteration"]
        w = len(entry["output"].split())
        c = entry["cost"]
        print(f"DEV (iter {i}) | words: {w:<5} | cost: ${c:.4f}")

    for entry in (final.get("rev_history") or []):
        i = entry["iteration"]
        w = len(entry["output"].split())
        v = entry["verdict"]
        c = entry["cost"]
        print(f"REV (iter {i}) | words: {w:<5} | verdict: {v} | cost: ${c:.4f}")

    print(f"\nTotal iterations: {final.get('iteration', 0)}")
    print(f"Final verdict: {final.get('verdict', 'UNKNOWN')}")
    print(f"Estimated total cost: ${total_cost:.4f} (actual may be lower)")
    if final.get("case_created"):
        print(f"Pega case: {final['case_created']}")
    if final.get("errors"):
        print(f"Errors: {final['errors']}")

    return dict(final)


if __name__ == "__main__":
    default_brd = "docs/mini_brd.txt"
    brd = input(f"BRD file path [{default_brd}]: ").strip() or default_brd
    run_pipeline(brd)
