import os
import operator
from typing import TypedDict, Annotated, Sequence
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
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

# ─── TOOL 2: PEGA KNOWLEDGE ───
@tool
def pega_knowledge(query: str) -> str:
    """
    Use for Pega QA standards, naming conventions, or implementation validation questions.
    Input should be a clear question about Pega best practices or standards.
    """
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        system="You are a Senior Pega QA Lead. Answer in 1-2 sentences max.",
        messages=[{
            "role": "user",
            "content": query
        }]
    )
    return response.content[0].text

# ─── LLM SETUP ───
tools = [read_document, pega_knowledge]

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
    temperature=0.1
).bind_tools(tools)

# ─── SYSTEM PROMPT ───
SYSTEM_PROMPT = """You are a Senior Pega QA Lead and Code Reviewer with 10 years experience in Pega QA and code review.
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
- Be objective and specific.
- Do not start with preamble.
- Start directly with REVIEW REPORT header.
- Keep total output under 500 words.
- Always end with VERDICT line."""

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

# ─── REVIEW IMPLEMENTATION ───
def review_implementation(developer_spec: str):
    print(f"\n{'='*60}")
    print("Reviewer Agent - Implementation Review")
    print(f"{'='*60}\n")

    agent = build_agent()

    # Build the human message
    today = datetime.now().strftime("%B %d, %Y")
    human_content = f"Today's date is {today}. Review this Developer Implementation Specification:\n\n{developer_spec}"

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

    print(f"\n✅ Review Report complete — output saved to file")

    # Save to file - clean output only
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"outputs/review_report_{timestamp}.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_answer)

    print(f"💾 Review saved to: {output_path}")

    return final_answer

# ─── TEST ───
if __name__ == "__main__":
    # Find the most recent developer_specs file from outputs/
    outputs_dir = "outputs"
    dev_files = [f for f in os.listdir(outputs_dir) if f.startswith("developer_specs_") and f.endswith(".md")]
    dev_files.sort(reverse=True)

    if not dev_files:
        print("No developer specs files found in outputs/ folder. Run developer_agent.py first.")
    else:
        latest_dev = os.path.join(outputs_dir, dev_files[0])
        print(f"Reading developer spec from: {latest_dev}")

        with open(latest_dev, "r", encoding="utf-8") as f:
            dev_content = f.read()

        review_implementation(dev_content)
