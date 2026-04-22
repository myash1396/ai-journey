# PEGA DX API MCP SERVER
# This server simulates Pega DX API responses for AI agent integration.
# In production, replace simulated data with actual Pega DX API calls:
#   Base URL: https://{pega-host}/prweb/api/v1/
#   Auth: OAuth 2.0 or Basic Auth
#   Endpoints:
#     GET /cases           - list/search cases
#     GET /cases/{ID}      - case details
#     POST /cases          - create case
#     GET /assignments     - worklist
#     GET /data/{dataViewID} - run data view
# The tool interfaces stay the same - only the data source changes.

import json
import os
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP

# ─── SETUP ───────────────────────────────────────────────────────────────────

mcp = FastMCP("pegaDXAPI")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pega_cases.json")


def load_cases() -> list[dict]:
    """Load cases from the JSON database file."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Pega cases database not found at: {DB_PATH}")
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cases(cases: list[dict]) -> None:
    """Persist cases list back to the JSON database file."""
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)


def _next_case_id(cases: list[dict]) -> str:
    """Generate the next sequential case ID (e.g. L-1009)."""
    existing_ids = []
    for case in cases:
        try:
            num = int(case["caseID"].split("-")[1])
            existing_ids.append(num)
        except (IndexError, ValueError):
            pass
    next_num = max(existing_ids, default=1000) + 1
    return f"L-{next_num}"


# ─── TOOLS ───────────────────────────────────────────────────────────────────

@mcp.tool()
def get_cases(
    status: str = None,
    case_type: str = None,
    days_back: int = 30,
    risk_only: bool = False,
) -> str:
    """Query Pega cases with filters. Simulates Pega DX API GET /cases endpoint. Use for reporting and case search."""
    cases = load_cases()
    cutoff_date = (datetime.now() - timedelta(days=days_back)).date()

    results = []
    for case in cases:
        # Date filter
        try:
            create_date = datetime.strptime(case["createDate"], "%Y-%m-%d").date()
        except ValueError:
            continue
        if create_date < cutoff_date:
            continue

        # Status filter
        if status and case.get("status", "").lower() != status.lower():
            continue

        # Case type filter
        if case_type and case.get("caseType", "").lower() != case_type.lower():
            continue

        # Risk filter
        if risk_only and not case.get("riskFlag", False):
            continue

        results.append(case)

    if not results:
        filters = []
        if status:
            filters.append(f"status={status}")
        if case_type:
            filters.append(f"caseType={case_type}")
        filters.append(f"days_back={days_back}")
        if risk_only:
            filters.append("risk_only=true")
        return json.dumps(
            {"status": "no_results", "filters_applied": filters, "cases": []},
            indent=2,
        )

    return json.dumps(
        {
            "status": "success",
            "total": len(results),
            "cases": results,
        },
        indent=2,
    )


@mcp.tool()
def get_case_details(case_id: str) -> str:
    """Get complete case details by case ID. Simulates Pega DX API GET /cases/{ID} endpoint."""
    if not case_id or not case_id.strip():
        return json.dumps({"status": "error", "message": "case_id must not be empty."})

    case_id = case_id.strip().upper()
    cases = load_cases()

    for case in cases:
        if case.get("caseID", "").upper() == case_id:
            return json.dumps({"status": "success", "case": case}, indent=2)

    return json.dumps(
        {
            "status": "not_found",
            "message": f"No case found with ID '{case_id}'. Verify the case ID and try again.",
        },
        indent=2,
    )


@mcp.tool()
def create_case(
    case_type: str,
    customer_name: str,
    customer_id: str,
    loan_amount: float,
    cibil_score: int,
    monthly_income: float,
) -> str:
    """Create a new loan case. Simulates Pega DX API POST /cases endpoint."""
    # Input validation
    valid_case_types = ["PersonalLoan", "HomeLoan", "AutoLoan", "Sprint0Implementation"]
    if case_type not in valid_case_types:
        return json.dumps(
            {
                "status": "error",
                "message": f"Invalid caseType '{case_type}'. Must be one of: {', '.join(valid_case_types)}.",
            },
            indent=2,
        )

    if not customer_name or not customer_name.strip():
        return json.dumps({"status": "error", "message": "customer_name must not be empty."}, indent=2)

    if not customer_id or not customer_id.strip():
        return json.dumps({"status": "error", "message": "customer_id must not be empty."}, indent=2)

    if loan_amount <= 0:
        return json.dumps({"status": "error", "message": "loan_amount must be greater than 0."}, indent=2)

    if not (300 <= cibil_score <= 900):
        return json.dumps(
            {"status": "error", "message": "cibil_score must be between 300 and 900."}, indent=2
        )

    if monthly_income <= 0:
        return json.dumps({"status": "error", "message": "monthly_income must be greater than 0."}, indent=2)

    cases = load_cases()
    now_str = datetime.now().strftime("%Y-%m-%d")

    # Risk assessment
    risk_flag = False
    risk_reason = None
    if cibil_score < 650:
        risk_flag = True
        risk_reason = (
            f"Potential defaulter: CIBIL score below acceptable threshold ({cibil_score} < 650)."
        )

    new_case = {
        "caseID": _next_case_id(cases),
        "caseType": case_type,
        "status": "Open",
        "createDate": now_str,
        "lastUpdateDate": now_str,
        "customerName": customer_name.strip(),
        "customerID": customer_id.strip().upper(),
        "loanAmount": loan_amount,
        "cibilScore": cibil_score,
        "monthlyIncome": monthly_income,
        "existingEMI": 0,
        "requestedTenure": None,
        "assignedTo": None,
        "urgency": "20",
        "stage": "ApplicationReview",
        "riskFlag": risk_flag,
        "riskReason": risk_reason,
    }

    cases.append(new_case)
    save_cases(cases)

    return json.dumps(
        {
            "status": "success",
            "message": f"Case {new_case['caseID']} created successfully.",
            "case": new_case,
        },
        indent=2,
    )


@mcp.tool()
def get_assignments(assigned_to: str = None) -> str:
    """Get pending assignments/worklist. Simulates Pega DX API GET /assignments endpoint."""
    cases = load_cases()
    pending_statuses = {"Open", "Pending-Approval"}

    worklist = []
    for case in cases:
        if case.get("status") not in pending_statuses:
            continue
        if assigned_to and (case.get("assignedTo") or "").lower() != assigned_to.strip().lower():
            continue
        worklist.append(
            {
                "caseID": case["caseID"],
                "caseType": case["caseType"],
                "status": case["status"],
                "stage": case["stage"],
                "customerName": case["customerName"],
                "customerID": case["customerID"],
                "loanAmount": case["loanAmount"],
                "assignedTo": case["assignedTo"],
                "urgency": case["urgency"],
                "createDate": case["createDate"],
                "lastUpdateDate": case["lastUpdateDate"],
                "riskFlag": case["riskFlag"],
            }
        )

    # Sort by urgency ascending (lower number = higher priority in Pega)
    worklist.sort(key=lambda c: int(c["urgency"]))

    if not worklist:
        msg = (
            f"No pending assignments found for '{assigned_to}'."
            if assigned_to
            else "No pending assignments found."
        )
        return json.dumps({"status": "no_results", "message": msg, "assignments": []}, indent=2)

    return json.dumps(
        {
            "status": "success",
            "total": len(worklist),
            "filter_assigned_to": assigned_to,
            "assignments": worklist,
        },
        indent=2,
    )


@mcp.tool()
def run_report(report_type: str) -> str:
    """Run predefined Pega reports/data views. Simulates Pega DX API data views."""
    valid_reports = ["defaulters", "monthly_summary", "high_value", "pending_approvals"]
    if report_type not in valid_reports:
        return json.dumps(
            {
                "status": "error",
                "message": f"Unknown report type '{report_type}'. Valid options: {', '.join(valid_reports)}.",
            },
            indent=2,
        )

    cases = load_cases()
    today = datetime.now().date()

    if report_type == "defaulters":
        results = [c for c in cases if c.get("riskFlag")]
        return json.dumps(
            {
                "status": "success",
                "report": "defaulters",
                "description": "Cases flagged as high-risk (potential defaulters or fraud)",
                "total": len(results),
                "cases": results,
            },
            indent=2,
        )

    elif report_type == "monthly_summary":
        cutoff = today - timedelta(days=30)
        recent = []
        for c in cases:
            try:
                if datetime.strptime(c["createDate"], "%Y-%m-%d").date() >= cutoff:
                    recent.append(c)
            except ValueError:
                pass

        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for c in recent:
            s = c.get("status", "Unknown")
            t = c.get("caseType", "Unknown")
            by_status[s] = by_status.get(s, 0) + 1
            by_type[t] = by_type.get(t, 0) + 1

        return json.dumps(
            {
                "status": "success",
                "report": "monthly_summary",
                "description": f"Case summary for last 30 days (since {cutoff})",
                "total_cases": len(recent),
                "by_status": by_status,
                "by_case_type": by_type,
            },
            indent=2,
        )

    elif report_type == "high_value":
        results = [c for c in cases if c.get("loanAmount", 0) > 1_000_000]
        results.sort(key=lambda c: c["loanAmount"], reverse=True)
        return json.dumps(
            {
                "status": "success",
                "report": "high_value",
                "description": "Cases with loan amount exceeding Rs 10,00,000",
                "total": len(results),
                "cases": results,
            },
            indent=2,
        )

    elif report_type == "pending_approvals":
        results = [c for c in cases if c.get("status") == "Pending-Approval"]
        return json.dumps(
            {
                "status": "success",
                "report": "pending_approvals",
                "description": "Cases currently awaiting approval",
                "total": len(results),
                "cases": results,
            },
            indent=2,
        )


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
