import os
import operator
from typing import TypedDict, Annotated, Sequence
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from datetime import datetime

# ─── STATE DEFINITION ───
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# ─── TOOL 1: READ DOCUMENT ───
@tool
def read_document(filename: str) -> str:
    """
    Use to read BRDs, policy documents, or any reference files from the docs folder.
    Input should be filename only like 'mini_brd.txt'
    """
    filepath = os.path.join("docs", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File '{filename}' not found in docs/ folder."
    except Exception as e:
        return f"Error: {str(e)}"

# ─── TOOL 2: WEB SEARCH ───
web_search = TavilySearch(
    max_results=3,
    topic="general",
    include_answer=True,
    include_raw_content=False,
)

# ─── TOOL 3: PEGA KNOWLEDGE ───
@tool
def pega_knowledge(query: str) -> str:
    """
    Use for Pega BPM architecture, component design, integration patterns, or banking system questions.
    Input should be a clear question about Pega platform, case design, or banking integrations.
    """
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system="You are a Pega Architect with 15 years experience in Pega BPM, banking integrations, and enterprise architecture. Answer concisely in 3 sentences max.",
        messages=[{
            "role": "user",
            "content": query
        }]
    )
    return response.content[0].text

# ─── LLM SETUP ───
tools = [read_document, web_search, pega_knowledge]

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
    temperature=0.1
).bind_tools(tools)

# ─── SYSTEM PROMPT ───
SYSTEM_PROMPT = """You are a Senior Tech Lead and Pega Architect with 15 years experience in banking systems.
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
- IMPORTANTt: Do not start with any preamble like "I now have all the information" or "Let me compile".
- IMPORTANT: sections should only be filled if there is relevant information in the BA analysis. Do not add generic content or assumptions. If you add assumptions, clearly tag them as [ASSUMPTION].
- Be comprehensive but concise. Do not hesitate to keep sections blank if need, do not add unnecessary information.
- Start directly with TECHNICAL DESIGN DOCUMENT header.
- Be precise and technical. This document is for Pega developers.
- Each section should be clear and only required details unless absolutely necessary.
- Use [CONFIRMED/INFERRED/RECOMMENDED] tags consistently.
- Use text-based diagrams where helpful. Do not add unnecessary diagrams.
- Tables for structured data.
- Use today's actual date provided in the message."""

# ─── NODE 1: AGENT NODE ───
def agent_node(state: AgentState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# ─── NODE 2: TOOL NODE ───
tool_node = ToolNode(tools)

# ─── CONDITIONAL EDGE ───
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "call_tool"
    return "end"

# ─── BUILD THE GRAPH ───
def build_agent():
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "call_tool": "tools",
            "end": END
        }
    )

    graph.add_edge("tools", "agent")

    return graph.compile()

# ─── DESIGN FROM BA ANALYSIS ───
def design_from_ba(ba_analysis: str, context: str = None):
    print(f"\n{'='*60}")
    print("Tech Lead Agent - Technical Design")
    print(f"{'='*60}\n")

    agent = build_agent()

    # Build the human message
    today = datetime.now().strftime("%B %d, %Y")
    human_content = f"Today's date is {today}. Create a technical design from this BA analysis:\n\n{ba_analysis}"
    if context:
        human_content += f"\n\nAdditional Context:\n{context}"

    final_answer = ""
    seen_tool_calls = set()
    seen_tool_results = set()

    for step in agent.stream(
        {"messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=human_content)
        ]},
        stream_mode="values"
    ):
        last_message = step["messages"][-1]

        # Show tool calls - only if not seen before
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tc in last_message.tool_calls:
                tool_id = tc.get("id", tc["name"])
                if tool_id not in seen_tool_calls:
                    seen_tool_calls.add(tool_id)
                    print(f"🔧 Tool called: {tc['name']}\n   Input: {tc['args']}")

        # Show tool results - only ToolMessage type
        elif hasattr(last_message, "type") and last_message.type == "tool":
            tool_id = getattr(last_message, "tool_call_id", "")
            if tool_id not in seen_tool_results:
                seen_tool_results.add(tool_id)
                print(f"📊 Tool result: {last_message.content[:150]}...")

        # Capture final answer
        elif hasattr(last_message, "content"):
            if isinstance(last_message.content, str) and last_message.content:
                if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
                    final_answer = last_message.content

    print(f"\n{'='*60}")
    print(f"Technical Design:\n{final_answer}")
    print(f"{'='*60}\n")

    # Save to file - clean output only for developers
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"outputs/tech_lead_analysis_{timestamp}.md"

    # Only save the clean analysis - no tool logs
    with open(output_path, "w", encoding="utf-8") as f:
        #f.write(f"TECHNICAL DESIGN DOCUMENT\n")
        #f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(final_answer)

    print(f"💾 Design saved to: {output_path}")

    return final_answer

# ─── TEST ───
if __name__ == "__main__":
    # Find the most recent ba_analysis file from outputs/
    outputs_dir = "outputs"
    ba_files = [f for f in os.listdir(outputs_dir) if f.startswith("ba_analysis_") and f.endswith(".md")]
    ba_files.sort(reverse=True)

    if not ba_files:
        print("No BA analysis files found in outputs/ folder. Run ba_agent.py first.")
    else:
        latest_ba = os.path.join(outputs_dir, ba_files[0])
        print(f"Reading BA analysis from: {latest_ba}")

        with open(latest_ba, "r", encoding="utf-8") as f:
            ba_content = f.read()

        design_from_ba(ba_content)
