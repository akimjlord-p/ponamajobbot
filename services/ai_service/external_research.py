from __future__ import annotations

import asyncio
from typing import Any

from openai import OpenAI

from config import OPENAI_API_KEY
from utils.logger import get_logger


logger = get_logger(__name__)


class ExternalResearchService:
    def __init__(self, model: str) -> None:
        self.model = model
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    async def research(self, question: str, research_brief: str) -> str | None:
        prompt = (
            "Ты бизнес-аналитик. Сделай краткий анализ по внешним источникам.\n"
            "Важно: речь про бизнес, а не про Telegram-бот как продукт.\n"
            f"Вопрос админа:\n{question}\n\n"
            f"Что проверить:\n{research_brief}\n\n"
            "Дай ответ на русском языке. В конце добавь блок 'Источники:' со ссылками."
        )
        logger.info("External research started: model=%s", self.model)
        try:
            response = await asyncio.to_thread(
                self.client.responses.create,
                model=self.model,
                tools=[{"type": "web_search"}],
                tool_choice="auto",
                input=prompt,
            )
        except Exception as ex:
            logger.exception("External research failed: %s", ex)
            return None

        output_text = getattr(response, "output_text", None)
        if output_text and str(output_text).strip():
            logger.info("External research completed with output_text")
            return str(output_text).strip()

        output: list[Any] = getattr(response, "output", []) or []
        text_chunks: list[str] = []
        for item in output:
            if getattr(item, "type", None) != "message":
                continue
            for content in getattr(item, "content", []) or []:
                if getattr(content, "type", None) == "output_text":
                    text_chunks.append(getattr(content, "text", ""))
        merged = "\n".join(chunk for chunk in text_chunks if chunk).strip()
        if merged:
            logger.info("External research completed with message content")
            return merged

        logger.warning("External research returned empty response")
        return None
