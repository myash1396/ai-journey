import os
from typing import TypedDict, Annotated, Sequence
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
import math

# ─── STATE DEFINITION ───
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# ─── TOOLS ───
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

@tool
def banking_knowledge(query: str) -> str:
    """
    Use for banking and finance domain questions.
    Input should be a clear banking question.
    """
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{
            "role": "user",
            "content": f"Banking expert. Answer in 2 sentences max: {query}"
        }]
    )
    return response.content[0].text

# ─── LLM SETUP ───
tools = [calculator, read_document, banking_knowledge]

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
    temperature=0.1
).bind_tools(tools)

# ─── NODE 1: AGENT NODE ───
def agent_node(state: AgentState):
    """
    The thinking node — Claude reads all messages
    and decides what to do next.
    Returns either a tool call or a final answer.
    """
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# ─── NODE 2: TOOL NODE ───
tool_node = ToolNode(tools)

# ─── CONDITIONAL EDGE ───
def should_continue(state: AgentState):
    """
    Decision point — should we call a tool or are we done?
    Reads the last message and checks if it contains a tool call.
    """
    last_message = state["messages"][-1]
    
    # If the last message has tool calls — go to tool node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "call_tool"
    
    # Otherwise — we're done
    return "end"

# ─── BUILD THE GRAPH ───
def build_agent():
    # Create the graph with our state definition
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    # Set entry point — where the graph starts
    graph.set_entry_point("agent")

    # Add conditional edge from agent node
    graph.add_conditional_edges(
        "agent",           # from this node
        should_continue,   # use this function to decide
        {
            "call_tool": "tools",  # if "call_tool" → go to tools node
            "end": END             # if "end" → finish
        }
    )

    # Add edge from tools back to agent
    # After tool runs → always go back to agent to think again
    graph.add_edge("tools", "agent")

    # Compile the graph
    return graph.compile()

# ─── RUN AGENT ───
def ask_agent(question: str, save_output: bool = True):
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}\n")

    agent = build_agent()
    
    # Track steps for file output
    steps_log = []
    steps_log.append(f"Question: {question}\n")
    steps_log.append("="*60 + "\n")

# Single run with streaming
    final_answer = ""
    seen_tool_calls = set()
    seen_tool_results = set()
    
    for step in agent.stream(
        {"messages": [HumanMessage(content=question)]},
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
    print(f"Final Answer:\n{final_answer}")
    print(f"{'='*60}\n")

    # Save to file
    if save_output:
        import os
        from datetime import datetime
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
    question = """Please do two things:
1. Read sample_policy.txt and find the record keeping duration
2. Calculate how many months that duration equals"""

    ask_agent(question)