from unittest.mock import patch

import pytest

from services.ai_service.synonyms import AISynonymsGenerator
from config import RUN_LLM_TEST
from services.ai_service.container import llm_connection


@pytest.mark.asyncio
@patch("services.ai_service.synonyms.Prompts.get_prompt_for_synonym")
async def test_generate_returns_none_if_llm_returns_none(
    mock_get_prompt_for_synonym,
    llm_fixture,
):
    word = "ремень"
    mock_get_prompt_for_synonym.return_value = f"get synonyms prompt {word}"

    ai_synonyms_generator = AISynonymsGenerator(llm_fixture)

    llm_fixture.ask_text.return_value = None

    synonyms = await ai_synonyms_generator.generate(word)

    assert synonyms is None
    mock_get_prompt_for_synonym.assert_called_once_with(word)
    llm_fixture.ask_text.assert_awaited_once_with(f"get synonyms prompt {word}")


@pytest.mark.asyncio
@patch("services.ai_service.synonyms.Prompts.get_prompt_for_synonym")
async def test_generate_returns_synonyms_list(
    mock_get_prompt_for_synonym,
    llm_fixture,
):
    word = "ремень"
    mock_get_prompt_for_synonym.return_value = f"get synonyms prompt {word}"

    ai_synonyms_generator = AISynonymsGenerator(llm_fixture)

    llm_fixture.ask_text.return_value = "пояс, лента, ремешок"

    synonyms = await ai_synonyms_generator.generate(word)

    assert synonyms == ["пояс", "лента", "ремешок"]
    mock_get_prompt_for_synonym.assert_called_once_with(word)
    llm_fixture.ask_text.assert_awaited_once_with(f"get synonyms prompt {word}")


@pytest.mark.asyncio
@pytest.mark.skipif(not RUN_LLM_TEST, reason="LLM test disabled")
async def test_generate_synonyms_with_real_llm():
    need_result = "ремень,belt,strap,белт,стрэп".split(",")
    ai_synonyms_generator = AISynonymsGenerator(llm_connection)
    real_result = await ai_synonyms_generator.generate('ремень')

    assert len(real_result) >= 3
    assert len(set(real_result) & set(need_result)) >= 2
    assert all(word == word.lower() for word in real_result)
    assert len(real_result) == len(real_result)


