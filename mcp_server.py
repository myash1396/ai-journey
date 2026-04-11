import json
import os
from datetime import datetime
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# ─── LOAD DATABASE ───
DB_PATH = "loan_database.json"

def load_db():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ─── CREATE MCP SERVER ───
app = Server("retailLoan-mcp-server")

# ─── TOOL DEFINITIONS ───
@app.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="get_loan_status",
            description="Get the current status and details of a loan application by loan ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "loan_id": {
                        "type": "string",
                        "description": "The loan application ID e.g. LOAN001"
                    }
                },
                "required": ["loan_id"]
            }
        ),
        types.Tool(
            name="update_loan_status",
            description="Update the status of a loan application. Valid statuses: Submitted, Under Review, Approved, Rejected",
            inputSchema={
                "type": "object",
                "properties": {
                    "loan_id": {
                        "type": "string",
                        "description": "The loan application ID"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status: Submitted, Under Review, Approved, Rejected"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for status change (required for Rejected status)"
                    }
                },
                "required": ["loan_id", "status"]
            }
        ),
        types.Tool(
            name="get_customer_loans",
            description="Get all loan applications for a specific customer by customer ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer ID e.g. CUST001"
                    }
                },
                "required": ["customer_id"]
            }
        )
    ]

# ─── TOOL EXECUTION ───
@app.call_tool()
async def call_tool(name: str, arguments: dict):

    if name == "get_loan_status":
        loan_id = arguments.get("loan_id", "").upper()
        db = load_db()

        if loan_id not in db["loans"]:
            return [types.TextContent(
                type="text",
                text=f"No loan found with ID: {loan_id}"
            )]

        loan = db["loans"][loan_id]
        result = f"""
Loan Details:
─────────────
Loan ID:        {loan['loan_id']}
Customer:       {loan['customer_name']} ({loan['customer_id']})
Type:           {loan['loan_type']}
Amount:         Rs {loan['amount']:,}
Status:         {loan['status']}
Applied Date:   {loan['applied_date']}
Disbursement:   {loan['disbursement_date'] or 'Not yet disbursed'}
Rejection:      {loan['rejection_reason'] or 'N/A'}
"""
        return [types.TextContent(type="text", text=result)]

    elif name == "update_loan_status":
        loan_id = arguments.get("loan_id", "").upper()
        new_status = arguments.get("status", "")
        reason = arguments.get("reason", "")

        valid_statuses = ["Submitted", "Under Review", "Approved", "Rejected"]
        if new_status not in valid_statuses:
            return [types.TextContent(
                type="text",
                text=f"Invalid status: {new_status}. Valid: {', '.join(valid_statuses)}"
            )]

        db = load_db()

        if loan_id not in db["loans"]:
            return [types.TextContent(
                type="text",
                text=f"No loan found with ID: {loan_id}"
            )]

        old_status = db["loans"][loan_id]["status"]
        db["loans"][loan_id]["status"] = new_status

        if new_status == "Rejected" and reason:
            db["loans"][loan_id]["rejection_reason"] = reason

        if new_status == "Approved":
            db["loans"][loan_id]["disbursement_date"] = datetime.now().strftime("%Y-%m-%d")

        save_db(db)

        return [types.TextContent(
            type="text",
            text=f"✅ Loan {loan_id} updated successfully\nOld status: {old_status}\nNew status: {new_status}"
        )]

    elif name == "get_customer_loans":
        customer_id = arguments.get("customer_id", "").upper()
        db = load_db()

        customer_loans = [
            loan for loan in db["loans"].values()
            if loan["customer_id"] == customer_id
        ]

        if not customer_loans:
            return [types.TextContent(
                type="text",
                text=f"No loans found for customer: {customer_id}"
            )]

        result = f"Loans for {customer_id}:\n" + "─" * 40 + "\n"
        for loan in customer_loans:
            result += f"""
{loan['loan_id']} | {loan['loan_type']}
Amount: Rs {loan['amount']:,} | Status: {loan['status']}
Applied: {loan['applied_date']}
"""
        return [types.TextContent(type="text", text=result)]

    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

# ─── RUN SERVER ───
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())