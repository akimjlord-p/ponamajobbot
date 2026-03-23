from unittest.mock import AsyncMock
import pytest


@pytest.fixture
def session_fixture():
    return AsyncMock()


@pytest.fixture
def llm_fixture():
    return AsyncMock()


def overlap_ratio(a: list[str], b: list[str]) -> float:
    a_set = set(a)
    b_set = set(b)

    if not a_set or not b_set:
        return 0.0

    intersection = len(a_set & b_set)

    precision = intersection / len(a_set)
    recall = intersection / len(b_set)

    return 2 * precision * recall / (precision + recall)