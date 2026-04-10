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

# ─── TOOL 3: BANKING KNOWLEDGE ───
@tool
def banking_knowledge(query: str) -> str:
    """
    Use for banking domain, Pega BPM, or regulatory clarifications.
    Input should be a clear question about banking processes, RBI regulations, or Pega architecture.
    """
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system="You are a Senior BA with 15 years banking and Pega BPM experience. Answer concisely in 3 sentences max.",
        messages=[{
            "role": "user",
            "content": query
        }]
    )
    return response.content[0].text

# ─── LLM SETUP ───
tools = [read_document, web_search, banking_knowledge]

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
    temperature=0.1
).bind_tools(tools)

# ─── SYSTEM PROMPT ───
SYSTEM_PROMPT = """You are a Senior Business Analyst with 15 years experience in banking and Pega BPM.
Your job is to analyze Business Requirements Documents thoroughly.

When given a BRD or requirements:
1. Use read_document tool to read any referenced documents
2. Use web_search to find relevant RBI regulations or banking standards
3. Use banking_knowledge for domain clarifications

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

# ─── ANALYZE BRD ───
def analyze_brd(brd_text: str, context: str = None):
    print(f"\n{'='*60}")
    print("BA Agent - BRD Analysis")
    print(f"{'='*60}\n")

    agent = build_agent()

    # Build the human message
    today = datetime.now().strftime("%B %d, %Y")
    human_content = f"Today's date is {today}. Analyze this BRD:\n\n{brd_text}"
    if context:
        human_content += f"\n\nAdditional Context:\n{context}"

    # Track steps for file output
    steps_log = []
    steps_log.append("BA Agent - BRD Analysis\n")
    steps_log.append("=" * 60 + "\n")

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
                    log = f"🔧 Tool called: {tc['name']}\n   Input: {tc['args']}"
                    print(log)
                    steps_log.append(log + "\n")

        # Show tool results - only ToolMessage type
        elif hasattr(last_message, "type") and last_message.type == "tool":
            tool_id = getattr(last_message, "tool_call_id", "")
            if tool_id not in seen_tool_results:
                seen_tool_results.add(tool_id)
                log = f"📊 Tool result: {last_message.content[:150]}..."
                print(log)
                steps_log.append(log + "\n")

        # Capture final answer
        elif hasattr(last_message, "content"):
            if isinstance(last_message.content, str) and last_message.content:
                if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
                    final_answer = last_message.content

    print(f"\n{'='*60}")
    print(f"BA Analysis:\n{final_answer}")
    print(f"{'='*60}\n")

    # Save to file - clean output only for Tech Lead
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"outputs/ba_analysis_{timestamp}.md"

    # Only save the clean analysis - no tool logs
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"BA ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        f.write(final_answer)

    print(f"💾 Analysis saved to: {output_path}")
    return final_answer

# ─── TEST ───
if __name__ == "__main__":
    brd_file = os.path.join("docs", "mini_brd.txt")
    with open(brd_file, "r", encoding="utf-8") as f:
        brd_content = f.read()

    analyze_brd(brd_content)
