import os
import json
from datetime import datetime
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from pega_mcp_server import (
    get_cases,
    get_case_details,
    create_case,
    get_assignments,
    run_report,
)

# ─── TOOL WRAPPERS ────────────────────────────────────────────────────────────

@tool
def query_cases(
    status: Optional[str] = None,
    case_type: Optional[str] = None,
    days_back: int = 30,
    risk_only: bool = False,
) -> str:
    """
    Search Pega cases with optional filters.
    - status: 'Open', 'Pending-Approval', 'Resolved-Completed', 'Resolved-Rejected'
    - case_type: 'PersonalLoan', 'HomeLoan', 'AutoLoan'
    - days_back: how many days back to look (default 30)
    - risk_only: set True to return only flagged risk cases
    Use this for case searches, listings, and risk audits.
    """
    return get_cases(
        status=status,
        case_type=case_type,
        days_back=days_back,
        risk_only=risk_only,
    )


@tool
def case_details(case_id: str) -> str:
    """
    Retrieve all fields for a single case by its case ID (e.g. 'L-1001').
    Use this when the user asks about a specific case or wants full details.
    """
    return get_case_details(case_id=case_id)


@tool
def create_new_case(
    case_type: str,
    customer_name: str,
    customer_id: str,
    loan_amount: float,
    cibil_score: int,
    monthly_income: float,
) -> str:
    """
    Create a new loan case in Pega.
    - case_type: 'PersonalLoan', 'HomeLoan', or 'AutoLoan'
    - customer_name: full name of the applicant
    - customer_id: bank customer ID (e.g. 'CUST-201')
    - loan_amount: requested loan amount in INR
    - cibil_score: applicant's CIBIL credit score (300–900)
    - monthly_income: gross monthly income in INR
    CIBIL scores below 650 will auto-flag the case as risk.
    Only use this after the user explicitly confirms creation.
    """
    return create_case(
        case_type=case_type,
        customer_name=customer_name,
        customer_id=customer_id,
        loan_amount=loan_amount,
        cibil_score=cibil_score,
        monthly_income=monthly_income,
    )


@tool
def check_assignments(assigned_to: Optional[str] = None) -> str:
    """
    Fetch the pending worklist (cases with status Open or Pending-Approval).
    - assigned_to: filter by officer login (e.g. 'officer.verma'); omit for all officers.
    Results are sorted by urgency (10 = highest priority in Pega).
    Use this to check workload, unattended cases, or a specific officer's queue.
    """
    return get_assignments(assigned_to=assigned_to)


@tool
def generate_report(report_type: str) -> str:
    """
    Run a predefined Pega report. Valid report_type values:
    - 'defaulters'         : all risk-flagged cases (fraud or potential defaulters)
    - 'monthly_summary'    : case counts by status and type for the last 30 days
    - 'high_value'         : cases with loan amount exceeding Rs 10,00,000
    - 'pending_approvals'  : all cases currently awaiting approval
    Use this for management dashboards, audits, and trend analysis.
    """
    return run_report(report_type=report_type)


# ─── AGENT SETUP ─────────────────────────────────────────────────────────────

_tools = [query_cases, case_details, create_new_case, check_assignments, generate_report]

_llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
    temperature=0,
)

agent = create_react_agent(_llm, _tools)

# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an AI-powered Banking Operations Assistant connected to the
bank's Pega case management system.

You can:
1. Query and search cases by status, type, date range, or risk flags
2. Get detailed information about any specific case
3. Create new loan cases
4. Check pending assignments and worklists
5. Generate reports (defaulters, monthly summary, high value, pending approvals)

RESPONSE GUIDELINES:
- Present data in clean, readable tables when showing multiple cases
- For risk analysis, explain the risk factors clearly
- For fraud detection, highlight specific red flags
- When asked about trends, analyze the data and provide insights
- Always mention case IDs when referring to specific cases
- Format currency in Indian Rupees (Rs)
- Be proactive: if you notice risk flags while answering, mention them

IMPORTANT:
- You have read-only access for queries and reports
- Case creation is the only write operation
- Always confirm before creating a new case
"""

# ─── STREAMING RUNNER ─────────────────────────────────────────────────────────

# Claude Sonnet 4 pricing: $3/M input, $15/M output
_INPUT_COST_PER_M = 3.0
_OUTPUT_COST_PER_M = 15.0


def run_query(user_message: str) -> tuple[str, int, int]:
    """
    Stream one user query through the agent.
    Returns (final_answer, total_input_tokens, total_output_tokens).
    """
    final_answer = ""
    seen_tool_calls: set[str] = set()
    seen_tool_results: set[str] = set()
    total_input = 0
    total_output = 0

    for step in agent.stream(
        {
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_message),
            ]
        },
        stream_mode="values",
    ):
        last_message = step["messages"][-1]

        # Accumulate token usage
        if hasattr(last_message, "usage_metadata") and last_message.usage_metadata:
            usage = last_message.usage_metadata
            total_input += usage.get("input_tokens", 0)
            total_output += usage.get("output_tokens", 0)

        # Tool call: print tool name + args
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tc in last_message.tool_calls:
                tool_id = tc.get("id", tc["name"])
                if tool_id not in seen_tool_calls:
                    seen_tool_calls.add(tool_id)
                    args_preview = json.dumps(tc["args"], ensure_ascii=False)
                    print(f"  🔧 Tool: {tc['name']}  |  Args: {args_preview}")

        # Tool result: print a short preview
        elif hasattr(last_message, "type") and last_message.type == "tool":
            tool_id = getattr(last_message, "tool_call_id", "")
            if tool_id not in seen_tool_results:
                seen_tool_results.add(tool_id)
                content_preview = str(last_message.content)[:200].replace("\n", " ")
                print(f"  📊 Result: {content_preview}...")

        # Agent text response (not a tool call)
        elif hasattr(last_message, "content"):
            if (
                isinstance(last_message.content, str)
                and last_message.content
                and not (hasattr(last_message, "tool_calls") and last_message.tool_calls)
            ):
                final_answer = last_message.content

    return final_answer, total_input, total_output


# ─── INTERACTIVE LOOP ─────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 65)
    print("  Pega Banking Operations Assistant")
    print("=" * 65)
    print("Connected to: Pega DX API (simulated)")
    print()
    print("What you can ask:")
    print("  • Show all open cases / pending approvals")
    print("  • Get details for case L-1005")
    print("  • Show risk-flagged cases")
    print("  • Check assignments for officer.verma")
    print("  • Run monthly summary / defaulters / high-value report")
    print("  • Create a new PersonalLoan case for [customer]")
    print()
    print("Type 'exit' to quit.")
    print("=" * 65 + "\n")

    session_input_tokens = 0
    session_output_tokens = 0
    query_count = 0

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession ended.")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "bye"}:
            print("\nGoodbye!")
            break

        query_count += 1
        print(f"\n{'─' * 65}")
        print(f"Query #{query_count}")
        print("─" * 65)

        try:
            answer, input_tok, output_tok = run_query(user_input)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

        session_input_tokens += input_tok
        session_output_tokens += output_tok

        print(f"\n{'─' * 65}")
        print(f"Assistant:\n{answer}")

        # Per-query cost
        q_cost = (input_tok / 1_000_000) * _INPUT_COST_PER_M + \
                 (output_tok / 1_000_000) * _OUTPUT_COST_PER_M
        print(f"\n📊 Tokens — input: {input_tok:,}  output: {output_tok:,}  "
              f"| 💰 Query cost: ${q_cost:.4f}")
        print("─" * 65 + "\n")

    # Session summary
    if query_count > 0:
        total_cost = (
            (session_input_tokens / 1_000_000) * _INPUT_COST_PER_M
            + (session_output_tokens / 1_000_000) * _OUTPUT_COST_PER_M
        )
        print(f"\n{'=' * 65}")
        print(f"Session Summary  ({query_count} quer{'y' if query_count == 1 else 'ies'})")
        print(f"{'=' * 65}")
        print(f"  Input tokens :  {session_input_tokens:,}")
        print(f"  Output tokens:  {session_output_tokens:,}")
        print(f"  Total tokens :  {session_input_tokens + session_output_tokens:,}")
        print(f"  Total cost   :  ${total_cost:.4f}")
        print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
