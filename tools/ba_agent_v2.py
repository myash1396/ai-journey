import os
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent

from sentence_transformers import SentenceTransformer
import chromadb


# ─── TOOL 1: READ DOCUMENT ───
@tool
def read_document(file_path: str) -> str:
    """
    Read a document file from the docs/ folder. Use this to read the input BRD
    or any reference files. Input should be a path like 'docs/mini_brd.txt'.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"File '{file_path}' not found."
    except Exception as e:
        return f"Error reading file: {str(e)}"


# ─── TOOL 2: SEARCH KNOWLEDGE BASE (RAG) ───
@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the internal knowledge base for existing documents, old BRDs, policies,
    application documentation, and business rules. Use this BEFORE web search to
    check internal knowledge first.
    """
    try:
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        client = chromadb.PersistentClient(path="./chroma_db")

        try:
            collection = client.get_collection(name="banking_docs")
        except Exception:
            return (
                "No knowledge base found. "
                "Ingest documents first using rag_engine.py"
            )

        query_embedding = model.encode([query]).tolist()
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=3,
        )

        documents = results["documents"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]

        if not documents:
            return "No relevant chunks found in the internal knowledge base."

        formatted = []
        for i, (doc, dist, meta) in enumerate(zip(documents, distances, metadatas)):
            source = meta.get("source", "unknown")
            formatted.append(
                f"--- Chunk {i + 1} ---\n"
                f"Source: {source}\n"
                f"Distance: {dist:.4f}\n"
                f"Text: {doc}\n"
            )
        return "\n".join(formatted)
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


# ─── TOOL 3: WEB SEARCH (regulatory only) ───
_tavily = TavilySearch(max_results=3)


@tool
def search_web(query: str) -> str:
    """
    Search the web ONLY for external regulatory information, RBI circulars,
    government policies, legal compliance requirements, and security standards.
    Do NOT use this for general business logic — check internal knowledge base first.
    """
    try:
        results = _tavily.invoke(query)
        return str(results)
    except Exception as e:
        return f"Error searching web: {str(e)}"


# ─── TOOL 4: BANKING KNOWLEDGE ───
@tool
def banking_knowledge(query: str) -> str:
    """
    Use for banking domain, Pega BPM, or regulatory clarifications.
    Input should be a clear question about banking processes, RBI regulations,
    or banking architecture.
    """
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system="You are a Senior Banking domain expert with 15 years experience in banking, Pega BPM, and RBI regulations. Answer concisely and accurately.",
        messages=[{
            "role": "user",
            "content": query
        }]
    )
    return response.content[0].text


# ─── AGENT SETUP ───
tools = [read_document, search_knowledge_base, search_web, banking_knowledge]

llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
    temperature=0,
)

agent = create_react_agent(llm, tools)


# ─── SYSTEM PROMPT ───
SYSTEM_PROMPT = """
You are a Senior Business Analyst in a banking technology team.

ANALYSIS APPROACH — Follow this search hierarchy strictly:
1. FIRST: Read the input BRD document provided by the user
2. SECOND: Search the internal knowledge base for related existing
   documents, old BRDs, policies, and business rules that may relate
   to the new BRD requirements
3. THIRD: Search the web ONLY for regulatory/compliance/legal/security
   validation — RBI circulars, government policies, data protection laws,
   banking regulations. Do NOT search web for general business logic.
4. Use banking_knowledge tool for domain-specific clarifications

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


# ─── RUN ANALYSIS ───
def analyze(file_path: str):
    print(f"\n{'=' * 60}")
    print("BA Agent v2 - RAG-Enhanced BRD Analysis")
    print(f"{'=' * 60}\n")
    print(f"📄 Input BRD: {file_path}\n")

    today = datetime.now().strftime("%B %d, %Y")
    query = (
        f"Today's date is {today}. "
        f"Read the document at {file_path} and produce a complete BA analysis. "
        f"Search internal knowledge base for any related existing documents. "
        f"Check web for any regulatory or compliance requirements that apply."
    )

    final_answer = ""
    seen_tool_calls = set()
    seen_tool_results = set()
    total_input_tokens = 0
    total_output_tokens = 0

    for step in agent.stream(
        {"messages": [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=query),
        ]},
        stream_mode="values",
    ):
        last_message = step["messages"][-1]

        # Track token usage if available
        if hasattr(last_message, "usage_metadata") and last_message.usage_metadata:
            usage = last_message.usage_metadata
            total_input_tokens += usage.get("input_tokens", 0)
            total_output_tokens += usage.get("output_tokens", 0)

        # Tool calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tc in last_message.tool_calls:
                tool_id = tc.get("id", tc["name"])
                if tool_id not in seen_tool_calls:
                    seen_tool_calls.add(tool_id)
                    print(f"🔧 Tool called: {tc['name']}")
                    print(f"   Input: {tc['args']}")

        # Tool results
        elif hasattr(last_message, "type") and last_message.type == "tool":
            tool_id = getattr(last_message, "tool_call_id", "")
            if tool_id not in seen_tool_results:
                seen_tool_results.add(tool_id)
                content_preview = str(last_message.content)[:200]
                print(f"📊 Tool result: {content_preview}...")

        # Final answer
        elif hasattr(last_message, "content"):
            if isinstance(last_message.content, str) and last_message.content:
                if not (hasattr(last_message, "tool_calls") and last_message.tool_calls):
                    final_answer = last_message.content

    print(f"\n✅ BA Analysis complete\n")

    # Save output
    os.makedirs("outputs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"outputs/ba_rag_analysis_{timestamp}.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# BA RAG Analysis Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Input BRD: {file_path}\n")
        f.write("=" * 60 + "\n\n")
        f.write(final_answer)

    print(f"💾 Analysis saved to: {output_path}")

    # Cost estimate — Claude Sonnet 4: $3/M input, $15/M output
    input_cost = (total_input_tokens / 1_000_000) * 3.0
    output_cost = (total_output_tokens / 1_000_000) * 15.0
    total_cost = input_cost + output_cost

    print(f"\n📊 Token Usage:")
    print(f"   Input tokens:  {total_input_tokens:,}")
    print(f"   Output tokens: {total_output_tokens:,}")
    print(f"   Total tokens:  {total_input_tokens + total_output_tokens:,}")
    print(f"💰 Estimated cost: ${total_cost:.4f} "
          f"(input: ${input_cost:.4f}, output: ${output_cost:.4f})")

    return final_answer


# ─── MAIN ───
if __name__ == "__main__":
    user_input = input("Enter BRD file path [docs/mini_brd.txt]: ").strip()
    brd_path = user_input if user_input else "docs/mini_brd.txt"
    analyze(brd_path)
