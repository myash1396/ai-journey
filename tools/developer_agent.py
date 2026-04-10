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
    max_results=2,
    topic="general",
    include_answer=True,
    include_raw_content=False,
)

# ─── TOOL 3: PEGA KNOWLEDGE ───
@tool
def pega_knowledge(query: str) -> str:
    """
    Use for specific Pega implementation details, component configuration, or coding patterns.
    Input should be a clear question about Pega development specifics.
    """
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        system="You are a Senior Pega Developer with 10 years experience. Answer in 2 sentences max about Pega implementation specifics.",
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
SYSTEM_PROMPT = """You are a Senior Pega Developer with 10 years experience in banking implementations.
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

# ─── CREATE IMPLEMENTATION SPECS ───
def create_implementation(tech_design: str):
    print(f"\n{'='*60}")
    print("Developer Agent - Implementation Specification")
    print(f"{'='*60}\n")

    agent = build_agent()

    # Build the human message
    today = datetime.now().strftime("%B %d, %Y")
    human_content = f"Today's date is {today}. Create implementation specifications from this Technical Design Document:\n\n{tech_design}"

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

    print(f"\n✅ Implementation Specs complete — output saved to file")

    # Save to file - clean output only
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"outputs/developer_specs_{timestamp}.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_answer)

    print(f"💾 Specs saved to: {output_path}")

    return final_answer

# ─── TEST ───
if __name__ == "__main__":
    # Find the most recent tech_lead_analysis file from outputs/
    outputs_dir = "outputs"
    tl_files = [f for f in os.listdir(outputs_dir) if f.startswith("tech_lead_analysis_") and f.endswith(".md")]
    tl_files.sort(reverse=True)

    if not tl_files:
        print("No tech lead analysis files found in outputs/ folder. Run tech_lead_agent.py first.")
    else:
        latest_tl = os.path.join(outputs_dir, tl_files[0])
        print(f"Reading tech design from: {latest_tl}")

        with open(latest_tl, "r", encoding="utf-8") as f:
            tl_content = f.read()

        create_implementation(tl_content)
