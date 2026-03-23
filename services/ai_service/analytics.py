import json
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import Base
from db.models import AdminRequestsContext
from services.ai_service.llm_connection import LLMConnection
from services.ai_service.prompts import Prompts


MAX_SQL_STEPS = 5
MAX_SQL_LIMIT = 50
MAX_ROWS_FOR_MODEL = 30


@dataclass
class AnalyticsStep:
    step_number: int
    sql: str
    comment: str
    rows: list[dict[str, Any]]


@dataclass
class AnalyticsResult:
    answer: str
    question: str


class AIAnalytics:
    def __init__(self, connection: LLMConnection, session: AsyncSession):
        self.connection = connection
        self.session = session

    @staticmethod
    def _get_db_schema_description() -> str:
        lines: list[str] = []
        for table_name, table in Base.metadata.tables.items():
            lines.append(f"Table {table_name}:")
            for column in table.columns:
                fk_targets = [str(fk.column) for fk in column.foreign_keys]
                if fk_targets:
                    lines.append(f"- {column.name} -> {', '.join(fk_targets)}")
                else:
                    lines.append(f"- {column.name}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _format_request_contexts(contexts: list[AdminRequestsContext]) -> str:
        if not contexts:
            return "Нет дополнительного контекста."
        return "\n".join(
            f"- {context.text.strip()}"
            for context in contexts
            if context.text and context.text.strip()
        ) or "Нет дополнительного контекста."

    @staticmethod
    def _is_safe_sql(query: str) -> bool:
        normalized = " ".join(query.strip().lower().split())
        if not normalized:
            return False
        if not (normalized.startswith("select") or normalized.startswith("with")):
            return False
        if ";" in normalized.rstrip(";"):
            return False
        forbidden = [
            "insert",
            "update",
            "delete",
            "drop",
            "alter",
            "create",
            "attach",
            "detach",
            "pragma",
            "vacuum",
            "truncate",
            "replace",
        ]
        return not any(word in normalized for word in forbidden)

    @staticmethod
    def _apply_limit(query: str, max_limit: int = MAX_SQL_LIMIT) -> str:
        cleaned = query.strip().rstrip(";")
        match = re.search(r"\blimit\s+(\d+)\b", cleaned, flags=re.IGNORECASE)
        if match:
            current_limit = int(match.group(1))
            if current_limit > max_limit:
                cleaned = re.sub(
                    r"\blimit\s+\d+\b",
                    f"LIMIT {max_limit}",
                    cleaned,
                    flags=re.IGNORECASE,
                )
            return cleaned
        return f"{cleaned}\nLIMIT {max_limit}"

    async def execute_read_only_query(self, query: str) -> list[dict[str, Any]]:
        result = await self.session.execute(text(query))
        rows = result.mappings().all()
        return [dict(row) for row in rows]

    @staticmethod
    def _rows_for_model(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return rows[:MAX_ROWS_FOR_MODEL]

    @staticmethod
    def _extract_json(raw_text: str) -> dict[str, Any] | None:
        text_value = raw_text.strip()
        if text_value.startswith("```"):
            lines = text_value.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text_value = "\n".join(lines).strip()
        try:
            return json.loads(text_value)
        except Exception:
            return None

    async def question(
        self,
        question: str,
        context: list[AdminRequestsContext],
    ) -> AnalyticsResult | None:
        schema = self._get_db_schema_description()
        request_context = self._format_request_contexts(context)
        steps: list[AnalyticsStep] = []
        for step_number in range(1, MAX_SQL_STEPS + 1):
            prompt = Prompts.get_prompt_for_analytics_step(
                question=question,
                schema=schema,
                request_context=request_context,
                previous_steps=steps,
                max_limit=MAX_SQL_LIMIT,
            )
            raw_response = await self.connection.ask_text(prompt)
            if not raw_response:
                return None
            model_decision = self._extract_json(raw_response)
            if not model_decision:
                return None
            action = model_decision.get("action")
            if action == "final":
                answer = model_decision.get("answer")
                if not answer:
                    return None
                return AnalyticsResult(answer=answer, question=question)
            if action != "query":
                return None
            sql = model_decision.get("sql")
            comment = model_decision.get("comment", "")
            if not sql or not isinstance(sql, str):
                return None
            if not self._is_safe_sql(sql):
                return None
            sql = self._apply_limit(sql)
            rows = await self.execute_read_only_query(sql)
            steps.append(
                AnalyticsStep(
                    step_number=step_number,
                    sql=sql,
                    comment=comment,
                    rows=self._rows_for_model(rows),
                )
            )
        final_prompt = Prompts.get_prompt_for_analytics_final_answer(
            question=question,
            request_context=request_context,
            previous_steps=steps,
        )

        final_raw_response = await self.connection.ask_text(final_prompt)
        if not final_raw_response:
            return None

        final_data = self._extract_json(final_raw_response)
        if not final_data:
            return None

        final_answer = final_data.get("answer")
        if not final_answer:
            return None

        return AnalyticsResult(answer=final_answer, question=question)