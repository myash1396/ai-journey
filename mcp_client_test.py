import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test 1 — List available tools
            print("=" * 50)
            print("Available Tools:")
            print("=" * 50)
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"🔧 {tool.name}: {tool.description}")

            # Test 2 — Get loan status
            print("\n" + "=" * 50)
            print("Test: Get Loan Status LOAN001")
            print("=" * 50)
            result = await session.call_tool(
                "get_loan_status",
                arguments={"loan_id": "LOAN001"}
            )
            print(result.content[0].text)

            # Test 3 — Get customer loans
            print("\n" + "=" * 50)
            print("Test: Get All Loans for CUST001")
            print("=" * 50)
            result = await session.call_tool(
                "get_customer_loans",
                arguments={"customer_id": "CUST001"}
            )
            print(result.content[0].text)

            # Test 4 — Update loan status
            print("\n" + "=" * 50)
            print("Test: Update LOAN001 to Approved")
            print("=" * 50)
            result = await session.call_tool(
                "update_loan_status",
                arguments={
                    "loan_id": "LOAN001",
                    "status": "Approved"
                }
            )
            print(result.content[0].text)

            # Test 5 — Verify update
            print("\n" + "=" * 50)
            print("Test: Verify LOAN001 after update")
            print("=" * 50)
            result = await session.call_tool(
                "get_loan_status",
                arguments={"loan_id": "LOAN001"}
            )
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_mcp_server())