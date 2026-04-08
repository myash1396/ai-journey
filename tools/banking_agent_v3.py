import os
import math
from typing import TypedDict, Annotated, Sequence
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
from datetime import datetime

# ─── STATE ───
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# ─── TOOL 1: CALCULATOR ───
@tool
def calculator(expression: str) -> str:
    """
    Use for any mathematical or financial calculations.
    Input must be a valid Python math expression.
    Example: '500000 * 0.085 / 12' for monthly interest
    """
    try:
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return f"Result: {result:.2f}"
    except Exception as e:
        return f"Error: {str(e)}"

# ─── TOOL 2: DOCUMENT READER ───
@tool
def read_document(filename: str) -> str:
    """
    Use to read policy documents or BRDs from the docs folder.
    Input should be filename only like 'sample_policy.txt'
    """
    filepath = os.path.join("docs", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File '{filename}' not found. Available: sample_policy.txt, sample_brd.txt"
    except Exception as e:
        return f"Error: {str(e)}"

# ─── TOOL 3: WEB SEARCH ───
web_search = TavilySearch(
    max_results=3,
    topic="general",
    include_answer=True,
    include_raw_content=False,
)

# ─── LLM SETUP ───
tools = [calculator, read_document, web_search]

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
    temperature=0.1
).bind_tools(tools)

# ─── AGENT NODE ───
def agent_node(state: AgentState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# ─── TOOL NODE ───
tool_node = ToolNode(tools)

# ─── CONDITIONAL EDGE ───
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "call_tool"
    return "end"

# ─── BUILD GRAPH ───
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

# ─── RUN AGENT ───
def ask_agent(question: str, save_output: bool = True):
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}\n")

    agent = build_agent()
    steps_log = []
    steps_log.append(f"Question: {question}\n")
    steps_log.append("="*60 + "\n")

    final_answer = ""
    seen_tool_calls = set()
    seen_tool_results = set()

    for step in agent.stream(
        {"messages": [HumanMessage(content=question)]},
        stream_mode="values"
    ):
        last_message = step["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tc in last_message.tool_calls:
                tool_id = tc.get("id", tc["name"])
                if tool_id not in seen_tool_calls:
                    seen_tool_calls.add(tool_id)
                    log = f"🔧 Tool called: {tc['name']}\n   Input: {tc['args']}"
                    print(log)
                    steps_log.append(log + "\n")

        elif hasattr(last_message, "type") and last_message.type == "tool":
            tool_id = getattr(last_message, "tool_call_id", "")
            if tool_id not in seen_tool_results:
                seen_tool_results.add(tool_id)
                log = f"📊 Tool result: {last_message.content[:200]}..."
                print(log)
                steps_log.append(log + "\n")

        elif hasattr(last_message, "content"):
            if isinstance(last_message.content, str) and last_message.content:
                if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
                    final_answer = last_message.content

    print(f"\n{'='*60}")
    print(f"Final Answer:\n{final_answer}")
    print(f"{'='*60}\n")

    if save_output:
        os.makedirs("outputs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"outputs/agent_session_{timestamp}.txt"
        steps_log.append("\n" + "="*60 + "\n")
        steps_log.append(f"Final Answer:\n{final_answer}\n")
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(steps_log)
        print(f"💾 Session saved to: {output_path}")

    return final_answer

# ─── TEST ───
if __name__ == "__main__":
    question = "What is the current RBI repo rate and how does it affect home loan interest rates in India?"
    ask_agent(question)