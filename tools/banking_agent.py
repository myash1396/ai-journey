import os
import math
from typing import Annotated
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

# ─── TOOL 1: CALCULATOR ───
@tool
def calculator(expression: str) -> str:
    """
    Useful for mathematical calculations.
    Use this for any financial calculations like EMI, interest, percentages.
    Input should be a valid Python math expression.
    Example: '10000 * 0.085 / 12' for monthly interest calculation.
    """
    try:
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return f"Calculation result: {result:.2f}"
    except Exception as e:
        return f"Calculation error: {str(e)}"

# ─── TOOL 2: DOCUMENT READER ───
@tool
def read_document(filename: str) -> str:
    """
    Useful for reading documents from the docs folder.
    Use this when you need to find specific information from policy documents or BRDs.
    Input should be just the filename like 'sample_policy.txt' or 'sample_brd.txt'
    """
    filepath = os.path.join("docs", filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return f"Document content:\n{content}"
    except FileNotFoundError:
        return f"Document '{filename}' not found in docs folder. Available files: sample_policy.txt, sample_brd.txt, test_banking_policy.pdf"
    except Exception as e:
        return f"Error reading document: {str(e)}"

# ─── TOOL 3: BANKING KNOWLEDGE ───
@tool
def banking_knowledge(query: str) -> str:
    """
    Useful for answering general banking and finance questions.
    Use this for questions about banking concepts, RBI regulations, 
    banking terminology, compliance requirements.
    Input should be a clear question about banking or finance.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=160,
        messages=[{
            "role": "user",
            "content": f"""You are a banking and finance expert in India.
Answer in maximum 2 sentences only. Be very concise:
{query}"""
        }]
    )
    return response.content[0].text

# ─── CREATE AGENT ───
def create_banking_agent():
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        anthropic_api_key=api_key,
        temperature=0.1
    )

    tools = [calculator, read_document, banking_knowledge]

    agent = create_react_agent(llm, tools)
    return agent

# ─── ASK AGENT ───
def ask_agent(question: str):
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}\n")

    agent = create_banking_agent()

    result = agent.invoke({
        "messages": [HumanMessage(content=question)]
    })

    # Extract final answer
    final_message = result["messages"][-1]
    answer = final_message.content

    print(f"\n{'='*60}")
    print(f"Final Answer: {answer}")
    print(f"{'='*60}\n")

    return answer

# ─── TEST ───
if __name__ == "__main__":
    question = """Please do three things:
1. Read the sample_policy.txt document and tell me the record keeping duration mentioned
2. Calculate how many years remain if we are already 2 years into that requirement
3. Briefly explain what AML means in banking
4. What is KYC in banking and why is it important?"""
    
    ask_agent(question)