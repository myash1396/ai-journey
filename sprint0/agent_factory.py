"""Shared utility for creating and running LangGraph agents.

Eliminates duplicated boilerplate across agent files by providing a common
factory for ChatAnthropic + create_react_agent setup, plus a streaming
runner that tracks tool calls, results, tokens, and cost.
"""

import os
import json
import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent


CLAUDE_MODEL = "claude-sonnet-4-20250514"
INPUT_COST_PER_M = 3.0
OUTPUT_COST_PER_M = 15.0


def create_agent(tools: list):
    llm = ChatAnthropic(model=CLAUDE_MODEL, temperature=0)
    return create_react_agent(llm, tools)


def run_agent(agent, query: str, system_prompt: str) -> dict:
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=query)]

    seen_tool_calls = set()
    seen_tool_results = set()
    tools_used = []
    answer = ""
    input_tokens = 0
    output_tokens = 0

    for chunk in agent.stream({"messages": messages}, stream_mode="values"):
        msgs = chunk.get("messages", [])
        for msg in msgs:
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                for tc in tool_calls:
                    name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                    args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
                    key = (name, json.dumps(args, sort_keys=True, default=str))
                    if key not in seen_tool_calls:
                        seen_tool_calls.add(key)
                        tools_used.append({"name": name, "args": args})
                        print(f"🔧 Tool: {name} | Args: {args}")

            if msg.__class__.__name__ == "ToolMessage":
                content = getattr(msg, "content", "")
                preview = str(content)[:200]
                if preview not in seen_tool_results:
                    seen_tool_results.add(preview)
                    print(f"📊 Result: {preview}...")

            usage = getattr(msg, "usage_metadata", None)
            if usage:
                input_tokens += usage.get("input_tokens", 0)
                output_tokens += usage.get("output_tokens", 0)

            if msg.__class__.__name__ == "AIMessage":
                content = getattr(msg, "content", "")
                if isinstance(content, str) and content:
                    answer = content
                elif isinstance(content, list):
                    texts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
                    if texts:
                        answer = "".join(texts)

    cost = estimate_cost(input_tokens, output_tokens)

    return {
        "answer": answer,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost": cost,
        "tools_used": tools_used,
    }


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * INPUT_COST_PER_M + (output_tokens / 1_000_000) * OUTPUT_COST_PER_M
