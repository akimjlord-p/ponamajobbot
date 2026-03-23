from unittest.mock import AsyncMock
import pytest
from services.ai_service.analytics import AIAnalytics
from services.report_service import ReportService

############### FIXTURES
@pytest.fixture
def session_fixture():
    return AsyncMock()

@pytest.fixture
def llm_fixture():
    return AsyncMock()

@pytest.fixture
def analytics(llm_fixture, session_fixture):
    return AIAnalytics(llm_fixture, session_fixture)

@pytest.fixture
def ai_service_fixture():
    return AsyncMock()


@pytest.fixture
def report_service(session_fixture, ai_service_fixture):
    return ReportService(session_fixture, ai_service_fixture)

############### HELP FUNC
def overlap_ratio(a: list[str], b: list[str]) -> float:
    a_set = set(a)
    b_set = set(b)

    if not a_set or not b_set:
        return 0.0

    intersection = len(a_set & b_set)

    precision = intersection / len(a_set)
    recall = intersection / len(b_set)

    return 2 * precision * recall / (precision + recall)


def make_query_response(sql="SELECT * FROM users", comment="test"):
    return f"""
    {{
        "action": "query",
        "sql": "{sql}",
        "comment": "{comment}"
    }}
    """


def make_final_response(answer="final answer"):
    return f"""
    {{
        "action": "final",
        "answer": "{answer}"
    }}
    """