from unittest.mock import patch, AsyncMock

import pytest

from services.ai_service.analytics import AIAnalytics, AnalyticsResult
from tests.conftest import make_final_response, make_query_response, llm_fixture

@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM users",
        "select id, username from users",
        " WITH temp AS (SELECT * FROM users) SELECT * FROM temp ",
    ],
)
def test_is_safe_sql_returns_true_for_read_only_queries(query):
    assert AIAnalytics._is_safe_sql(query) is True


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        "DELETE FROM users",
        "UPDATE users SET username = 'x'",
        "INSERT INTO users (username) VALUES ('x')",
        "DROP TABLE users",
        "ALTER TABLE users ADD COLUMN test TEXT",
        "CREATE TABLE test (id INT)",
        "PRAGMA table_info(users)",
        "VACUUM",
        "SELECT * FROM users; DELETE FROM users",
    ],
)
def test_is_safe_sql_returns_false_for_unsafe_queries(query):
    assert AIAnalytics._is_safe_sql(query) is False


def test_apply_limit_adds_limit_if_missing():
    query = "SELECT * FROM users"

    result = AIAnalytics._apply_limit(query)

    assert result == "SELECT * FROM users\nLIMIT 50"


def test_apply_limit_removes_trailing_semicolon_and_adds_limit():
    query = "SELECT * FROM users;"

    result = AIAnalytics._apply_limit(query)

    assert result == "SELECT * FROM users\nLIMIT 50"


def test_apply_limit_keeps_existing_limit_if_it_is_small_enough():
    query = "SELECT * FROM users LIMIT 10"

    result = AIAnalytics._apply_limit(query)

    assert result == "SELECT * FROM users LIMIT 10"


def test_apply_limit_reduces_existing_limit_if_it_is_too_large():
    query = "SELECT * FROM users LIMIT 1000"

    result = AIAnalytics._apply_limit(query)

    assert result == "SELECT * FROM users LIMIT 50"


def test_apply_limit_handles_lowercase_and_mixed_case_limit():
    query = "select * from users LiMiT 500"

    result = AIAnalytics._apply_limit(query)

    assert result == "select * from users LIMIT 50"


def test_apply_limit_does_not_change_small_limit_with_spaces():
    query = "  SELECT * FROM users LIMIT 5  "

    result = AIAnalytics._apply_limit(query)

    assert result == "SELECT * FROM users LIMIT 5"


def test_normalize_enum_literals_in_sql_converts_python_values_to_db_literals(analytics):
    query = (
        "SELECT id FROM work_reports "
        "WHERE status = 'parsed' AND result_type IN ('text_only', 'no_actionable_data')"
    )

    result = analytics._normalize_enum_literals_in_sql(query)

    assert "status = 'PARSED'" in result
    assert "result_type IN ('TEXT_ONLY', 'NO_ACTIONABLE_DATA')" in result


def test_schema_description_contains_enum_db_values():
    schema = AIAnalytics._get_db_schema_description()
    assert "enum_db_values" in schema


@pytest.mark.asyncio
@patch("services.ai_service.analytics.Prompts.get_prompt_for_analytics_step")
async def test_question_happy_path(mock_prompt, analytics, llm_fixture):
    mock_prompt.return_value = "prompt"

    llm_fixture.ask_text.side_effect = [
        make_query_response(),
        make_final_response("done"),
    ]

    with patch.object(analytics, "execute_read_only_query", new=AsyncMock(return_value=[{"id": 1}])):
        result = await analytics.question("question", [])

    assert isinstance(result, AnalyticsResult)
    assert result.answer == "done"
    assert result.question == "question"


@pytest.mark.asyncio
@patch("services.ai_service.analytics.Prompts.get_prompt_for_analytics_step")
async def test_question_unsafe_sql(mock_prompt, analytics, llm_fixture):
    mock_prompt.return_value = "prompt"

    llm_fixture.ask_text.return_value = make_query_response("DELETE FROM users")

    result = await analytics.question("question", [])

    assert result is None


@pytest.mark.asyncio
@patch("services.ai_service.analytics.Prompts.get_prompt_for_analytics_step")
async def test_question_invalid_json(mock_prompt, analytics, llm_fixture):
    mock_prompt.return_value = "prompt"

    llm_fixture.ask_text.return_value = "not json"

    result = await analytics.question("question", [])

    assert result is None


@pytest.mark.asyncio
@patch("services.ai_service.analytics.Prompts.get_prompt_for_analytics_step")
async def test_question_final_on_first_step(mock_prompt, analytics, llm_fixture):
    mock_prompt.return_value = "prompt"

    llm_fixture.ask_text.return_value = make_final_response("instant answer")

    result = await analytics.question("question", [])

    assert result.answer == "instant answer"


@pytest.mark.asyncio
@patch("services.ai_service.analytics.Prompts.get_prompt_for_analytics_step")
@patch("services.ai_service.analytics.Prompts.get_prompt_for_analytics_final_answer")
async def test_question_fallback_after_max_steps(
    mock_final_prompt,
    mock_step_prompt,
    analytics,
    llm_fixture,
):
    mock_step_prompt.return_value = "step_prompt"
    mock_final_prompt.return_value = "final_prompt"

    llm_fixture.ask_text.side_effect = (
        [make_query_response() for _ in range(5)]
        + [make_final_response("fallback answer")]
    )

    with patch.object(
        analytics,
        "execute_read_only_query",
        new=AsyncMock(return_value=[{"id": 1}]),
    ):
        result = await analytics.question("question", [])

    assert result.answer == "fallback answer"


