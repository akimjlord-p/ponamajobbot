from unittest.mock import AsyncMock
import pytest


@pytest.fixture
def session_fixture():
    return AsyncMock()