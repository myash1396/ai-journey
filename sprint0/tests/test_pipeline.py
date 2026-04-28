"""DeepEval test suite for Sprint 0 Accelerator pipeline outputs.

Reads the most recent saved pipeline outputs from sprint0/outputs/ and
evaluates them with DeepEval metrics plus a few structural assertions.

Run with:
    pytest sprint0/tests/test_pipeline.py -v
    deepeval test run sprint0/tests/test_pipeline.py
"""

import os
import glob

from deepeval.models import AnthropicModel
from deepeval import assert_test
import pytest
import deepeval  # noqa: F401
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    HallucinationMetric,
)
from deepeval.test_case import LLMTestCase
from deepeval.dataset import EvaluationDataset  # noqa: F401


HERE = os.path.dirname(os.path.abspath(__file__))
SPRINT0_ROOT = os.path.abspath(os.path.join(HERE, ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(SPRINT0_ROOT, ".."))
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
BRD_PATH_CANDIDATES = [
    os.path.join(SPRINT0_ROOT, "docs", "mini_brd.txt"),
    os.path.join(PROJECT_ROOT, "docs", "mini_brd.txt"),
]

def _truncate(text: str, max_chars: int = 1500) -> str:
    """Truncate text to stay within DeepEval evaluation limits."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[... truncated for evaluation ...]"

def get_latest_file(prefix: str) -> str:
    """Return the path to the most recently modified file in outputs/ matching prefix*."""
    pattern = os.path.join(OUTPUTS_DIR, f"{prefix}*")
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(
            f"No files matching {pattern!r} found. "
            f"Run the Sprint 0 pipeline first to generate outputs."
        )
    matches.sort(key=os.path.getmtime, reverse=True)
    return matches[0]


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _resolve_brd() -> str:
    for p in BRD_PATH_CANDIDATES:
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(
        f"Could not find mini_brd.txt in any of: {BRD_PATH_CANDIDATES}"
    )


def _latest_with_fallback(primary_prefix: str, fallback_prefix: str) -> str:
    try:
        return get_latest_file(primary_prefix)
    except FileNotFoundError:
        return get_latest_file(fallback_prefix)


def get_latest_outputs() -> dict:
    """Load BRD plus the latest BA / TL / Dev / Reviewer outputs.

    Returns a dict with keys: brd, ba, tl, dev, rev.
    """
    if not os.path.isdir(OUTPUTS_DIR):
        raise FileNotFoundError(
            f"Outputs directory not found: {OUTPUTS_DIR}. "
            f"Run the Sprint 0 pipeline first."
        )

    ba_path = get_latest_file("sprint0_ba_")
    tl_path = get_latest_file("sprint0_tl_")
    dev_path = _latest_with_fallback("sprint0_dev_iter1_", "sprint0_dev_")
    rev_path = _latest_with_fallback("sprint0_rev_iter1_", "sprint0_rev_")
    brd_path = _resolve_brd()

    return {
        "brd": _read(brd_path),
        "ba": _read(ba_path),
        "tl": _read(tl_path),
        "dev": _read(dev_path),
        "rev": _read(rev_path),
    }


def test_ba_faithfulness(pipeline_outputs):
    """BA analysis should be faithful (non-contradictory) to the input BRD."""
    test_case = LLMTestCase(
        input="Analyze this BRD and produce a BA analysis",
        actual_output=_truncate(pipeline_outputs["ba"]),
        retrieval_context=[_truncate(pipeline_outputs["brd"])],
    )
    metric = FaithfulnessMetric(threshold=0.7, model=AnthropicModel(model="claude-haiku-4-5-20251001"))
    metric.measure(test_case)
    print(f"\n[BA faithfulness] score={metric.score} reason={metric.reason}")
    assert_test(test_case, [metric])


def test_ba_relevancy(pipeline_outputs):
    """BA analysis should be relevant to the structured analysis request."""
    test_case = LLMTestCase(
        input=(
            "Analyze this BRD: produce requirement summary, user stories, "
            "business rules, edge cases, risk flags, developer questions, complexity"
        ),
        actual_output=_truncate(pipeline_outputs["ba"]),
    )
    metric = AnswerRelevancyMetric(threshold=0.7, model=AnthropicModel(model="claude-haiku-4-5-20251001"))
    metric.measure(test_case)
    print(f"\n[BA relevancy] score={metric.score} reason={metric.reason}")
    assert_test(test_case, [metric])


def test_tl_relevancy(pipeline_outputs):
    """Tech Lead design should be relevant to the BA analysis it derives from."""
    test_case = LLMTestCase(
        input="Create a technical design from this BA analysis",
        actual_output=_truncate(pipeline_outputs["tl"]),
        retrieval_context=[_truncate(pipeline_outputs["ba"])],
    )
    metric = AnswerRelevancyMetric(threshold=0.7, model=AnthropicModel(model="claude-haiku-4-5-20251001"))
    metric.measure(test_case)
    print(f"\n[TL relevancy] score={metric.score} reason={metric.reason}")
    assert_test(test_case, [metric])


def test_dev_relevancy(pipeline_outputs):
    """Developer specs should be relevant to the upstream tech design."""
    test_case = LLMTestCase(
        input="Create implementation specifications from this technical design",
        actual_output=_truncate(pipeline_outputs["dev"]),
        retrieval_context=[_truncate(pipeline_outputs["tl"])],
    )
    metric = AnswerRelevancyMetric(threshold=0.7, model=AnthropicModel(model="claude-haiku-4-5-20251001"))
    metric.measure(test_case)
    print(f"\n[Dev relevancy] score={metric.score} reason={metric.reason}")
    assert_test(test_case, [metric])


def test_rev_has_verdict(pipeline_outputs):
    """Reviewer report should include a clear verdict and numbered issues."""
    rev_text = pipeline_outputs["rev"]
    assert (
        "VERDICT: APPROVED" in rev_text
        or "VERDICT: REVISION NEEDED" in rev_text
    ), "Reviewer output is missing a clear VERDICT line"
    assert "ISS-001" in rev_text, (
        "Reviewer output is missing numbered issues (expected ISS-001 pattern)"
    )


def test_ba_no_hallucination(pipeline_outputs):
    """BA analysis should not hallucinate facts beyond what the BRD states."""
    test_case = LLMTestCase(
        input="Analyze this BRD",
        actual_output=_truncate(pipeline_outputs["ba"]),
        context=[_truncate(pipeline_outputs["brd"])],
    )
    metric = HallucinationMetric(threshold=0.7, model=AnthropicModel(model="claude-haiku-4-5-20251001"))
    metric.measure(test_case)
    print(f"\n[BA hallucination] score={metric.score} reason={metric.reason}")
    assert_test(test_case, [metric])


def test_pipeline_output_completeness(pipeline_outputs):
    """Each stage's output should contain its expected named sections."""
    ba = pipeline_outputs["ba"].upper()
    for section in (
        "REQUIREMENT SUMMARY",
        "USER STORIES",
        "BUSINESS RULES",
        "EDGE CASES",
        "RISK FLAGS",
        "DEVELOPER QUESTIONS",
        "COMPLEXITY",
    ):
        assert section in ba, f"BA output missing section: {section}"

    tl = pipeline_outputs["tl"].upper()
    for section in ("ARCHITECTURE", "INTEGRATION", "DATA MODEL"):
        assert section in tl, f"TL output missing section: {section}"

    dev = pipeline_outputs["dev"].upper()
    for section in ("IMPLEMENTATION", "ACCEPTANCE CRITERIA"):
        assert section in dev, f"Dev output missing section: {section}"

    rev = pipeline_outputs["rev"].upper()
    for section in ("CHECKLIST", "ISSUES FOUND", "VERDICT"):
        assert section in rev, f"Reviewer output missing section: {section}"
