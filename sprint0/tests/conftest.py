import pytest
import deepeval  # noqa: F401

from sprint0.tests.test_pipeline import get_latest_outputs


@pytest.fixture(scope="session")
def pipeline_outputs():
    """Load the most recent set of Sprint 0 pipeline outputs once per test session."""
    return get_latest_outputs()
