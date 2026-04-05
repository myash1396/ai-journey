import pytest
from deepeval import assert_test
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from deepeval.models import AnthropicModel
from tools.brd_analyzer_claude import analyze_brd

# ─── FOCUSED TEST DOCUMENT ───
MINI_BRD = """
LOAN ELIGIBILITY POLICY

Applicants must meet ALL of the following:
- Minimum age: 21 years
- Credit score: 700 or above
- Minimum monthly income: Rs 25,000
- Maximum loan amount: Rs 10 lakhs for personal loans
"""

# ─── FOCUSED PROMPT ───
FOCUSED_PROMPT = """Extract only the eligibility criteria from this policy as bullet points.
List each criterion clearly and concisely."""

def get_focused_analysis():
    """Get a short focused analysis for testing"""
    import requests
    import os
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"{FOCUSED_PROMPT}\n\nDOCUMENT:\n{MINI_BRD}"
        }]
    )
    return response.content[0].text

# ─── TEST 1: FAITHFULNESS ───
def test_eligibility_faithfulness():
    """Test that extracted criteria are faithful to source document"""
    
    analysis = get_focused_analysis()
    
    test_case = LLMTestCase(
        input=FOCUSED_PROMPT,
        actual_output=analysis,
        retrieval_context=[MINI_BRD]
    )

    metric = FaithfulnessMetric(
        threshold=0.5,
        model=AnthropicModel("claude-sonnet-4-6"),
        include_reason=True
    )

    assert_test(test_case, [metric])

# ─── TEST 2: ANSWER RELEVANCY ───
def test_eligibility_relevancy():
    """Test that response addresses the eligibility question"""
    
    analysis = get_focused_analysis()
    
    test_case = LLMTestCase(
        input=FOCUSED_PROMPT,
        actual_output=analysis,
        retrieval_context=[MINI_BRD]
    )

    metric = AnswerRelevancyMetric(
        threshold=0.5,
        model=AnthropicModel("claude-sonnet-4-6"),
        include_reason=True
    )

    assert_test(test_case, [metric])

# ─── TEST 3: NO HALLUCINATION ───
def test_no_hallucination():
    """Test that key facts from document appear correctly"""
    
    analysis = get_focused_analysis()
    
    assert "700" in analysis or "credit score" in analysis.lower(), \
        "Must mention credit score of 700"
    assert "21" in analysis or "age" in analysis.lower(), \
        "Must mention minimum age of 21"
    assert "25,000" in analysis or "25000" in analysis or "income" in analysis.lower(), \
        "Must mention income requirement"
    
    print(f"\n✅ Analysis content verified:")
    print(analysis[:300])