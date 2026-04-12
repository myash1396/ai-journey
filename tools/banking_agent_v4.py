import os
import math
import json
from datetime import datetime
from typing import TypedDict, Annotated, Sequence
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

# ─── STATE ───
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# ─── DATABASE PATH ───
DB_PATH = "loan_database.json"

def load_db():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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
    Use to read customer profiles, policy documents or BRDs from docs folder.
    Input should be filename only like 'customer_profile.txt'
    """
    filepath = os.path.join("docs", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File '{filename}' not found."
    except Exception as e:
        return f"Error: {str(e)}"

# ─── TOOL 3: WEB SEARCH ───
web_search = TavilySearch(
    max_results=2,
    topic="general",
    include_answer=True,
    include_raw_content=False,
)

# ─── TOOL 4: GET LOAN STATUS (MCP) ───
@tool
def get_loan_status(loan_id: str) -> str:
    """
    Use to get current status and details of a loan application.
    Input should be loan ID like 'LOAN001'.
    Use this when you need to check existing loan information
    before making decisions.
    """
    loan_id = loan_id.upper()
    db = load_db()

    if loan_id not in db["loans"]:
        return f"No loan found with ID: {loan_id}"

    loan = db["loans"][loan_id]
    return f"""
Loan ID: {loan['loan_id']}
Customer: {loan['customer_name']} ({loan['customer_id']})
Type: {loan['loan_type']}
Amount: Rs {loan['amount']:,}
Status: {loan['status']}
Applied: {loan['applied_date']}
Disbursement: {loan['disbursement_date'] or 'Not yet disbursed'}
Rejection Reason: {loan['rejection_reason'] or 'N/A'}
"""

# ─── TOOL 5: UPDATE LOAN STATUS (MCP) ───
@tool
def update_loan_status(loan_id: str, status: str, reason: str = "") -> str:
    """
    Use to update the status of a loan application in the system.
    Valid statuses: Submitted, Under Review, Approved, Rejected.
    Use this ONLY after completing eligibility analysis and making
    a clear decision. This makes real changes to the database.
    Input: loan_id, status, reason (required if Rejected)
    """
    loan_id = loan_id.upper()
    valid_statuses = ["Submitted", "Under Review", "Approved", "Rejected"]

    if status not in valid_statuses:
        return f"Invalid status: {status}. Valid: {', '.join(valid_statuses)}"

    db = load_db()

    if loan_id not in db["loans"]:
        return f"No loan found with ID: {loan_id}"

    old_status = db["loans"][loan_id]["status"]
    db["loans"][loan_id]["status"] = status

    if status == "Rejected" and reason:
        db["loans"][loan_id]["rejection_reason"] = reason

    if status == "Approved":
        db["loans"][loan_id]["disbursement_date"] = datetime.now().strftime("%Y-%m-%d")

    save_db(db)

    return f"✅ Loan {loan_id} updated: {old_status} → {status}"

# ─── LLM SETUP ───
tools = [calculator, read_document, web_search, get_loan_status, update_loan_status]

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
    temperature=0.1
).bind_tools(tools)

# ─── SYSTEM PROMPT ───
SYSTEM_PROMPT = """You are a Senior Banking AI Assistant with access to loan management tools.

You can:
1. Read customer documents and profiles
2. Search for current RBI rates and banking regulations
3. Perform financial calculations
4. Check loan status in the system
5. Update loan status based on eligibility decisions

When processing a loan application:
- Always read the customer profile first
- Check current RBI repo rate via web search
- Calculate applicable interest rate based on credit score:
  CIBIL above 750 = RBI repo rate + 2%
  CIBIL 700-750 = RBI repo rate + 3%
  CIBIL below 700 = Reject application
- Calculate monthly EMI if approved
- Update loan status in system
- Provide clear reasoning for decision

Be precise, professional and thorough."""

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
        {"call_tool": "tools", "end": END}
    )
    graph.add_edge("tools", "agent")
    return graph.compile()

# ─── ASK AGENT ───
def ask_agent(question: str):
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}\n")

    agent = build_agent()
    final_answer = ""
    seen_tool_calls = set()
    seen_tool_results = set()

    for step in agent.stream(
        {"messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=question)
        ]},
        stream_mode="values"
    ):
        last_message = step["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tc in last_message.tool_calls:
                tool_id = tc.get("id", tc["name"])
                if tool_id not in seen_tool_calls:
                    seen_tool_calls.add(tool_id)
                    print(f"🔧 Tool: {tc['name']} | Input: {tc['args']}")

        elif hasattr(last_message, "type") and last_message.type == "tool":
            tool_id = getattr(last_message, "tool_call_id", "")
            if tool_id not in seen_tool_results:
                seen_tool_results.add(tool_id)
                print(f"📊 Result: {last_message.content[:100]}...")

        elif hasattr(last_message, "content"):
            if isinstance(last_message.content, str) and last_message.content:
                if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
                    final_answer = last_message.content

    # Save output
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"outputs/loan_decision_{timestamp}.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"Question: {question}\n\n")
        f.write(f"Decision:\n{final_answer}")
    print(f"\n{'='*60}")
    print(f"Final Answer:\n{final_answer}")
    print(f"{'='*60}")
    print(f"💾 Saved to: {output_path}")

    return final_answer

# ─── TEST ───
if __name__ == "__main__":
    question = """
    Process the loan application for customer in docs/customer_profile.txt:
    
    1. Read and analyze the customer profile
    2. Search for current RBI repo rate
    3. Based on CIBIL score calculate applicable interest rate
    4. Calculate monthly EMI for the requested amount and tenure
    5. Make approval/rejection decision
    6. Update loan status in system (loan ID is LOAN001)
    7. Provide complete decision summary
    """
    ask_agent(question)