import json
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Enum as SAEnum, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import Base
from db.models import AdminRequestsContext
from services.ai_service.llm_connection import LLMConnection
from services.ai_service.prompts import Prompts
from utils.logger import get_logger


MAX_SQL_STEPS = 5
MAX_SQL_LIMIT = 50
MAX_ROWS_FOR_MODEL = 30
MAX_LOG_TEXT_PREVIEW = 4000


logger = get_logger(__name__)


def _preview(text: str, limit: int = MAX_LOG_TEXT_PREVIEW) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated {len(text) - limit} chars]"


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
        self.enum_column_names = self._get_enum_column_names()
        self.enum_literal_map = self._build_enum_literal_map()
        logger.info(
            "Analytics enum metadata initialized: enum_columns=%s enum_literals=%s",
            len(self.enum_column_names),
            len(self.enum_literal_map),
        )

    @staticmethod
    def _get_enum_column_names() -> set[str]:
        result: set[str] = set()
        for table in Base.metadata.tables.values():
            for column in table.columns:
                if isinstance(column.type, SAEnum):
                    result.add(column.name)
        return result

    @staticmethod
    def _build_enum_literal_map() -> dict[str, str]:
        enum_map: dict[str, str] = {}
        for table in Base.metadata.tables.values():
            for column in table.columns:
                column_type = column.type
                if not isinstance(column_type, SAEnum):
                    continue

                enum_class = getattr(column_type, "enum_class", None)
                db_values = [str(value) for value in (column_type.enums or [])]
                db_values_set = {value.casefold() for value in db_values}

                if enum_class is not None:
                    for enum_member in enum_class:
                        enum_name = enum_member.name
                        enum_value = str(enum_member.value)
                        db_literal = enum_name if enum_name.casefold() in db_values_set else enum_value
                        enum_map[enum_name.casefold()] = db_literal
                        enum_map[enum_value.casefold()] = db_literal
                else:
                    for db_value in db_values:
                        enum_map[db_value.casefold()] = db_value
        return enum_map

    @staticmethod
    def _format_enum_column_description(column) -> str:
        column_type = column.type
        if not isinstance(column_type, SAEnum):
            return ""

        db_values = [str(value) for value in (column_type.enums or [])]
        enum_class = getattr(column_type, "enum_class", None)

        if enum_class is None:
            return f" | enum_db_values={db_values}"

        enum_pairs = [f"{member.name}<{member.value}>" for member in enum_class]
        return (
            f" | enum_db_values={db_values}"
            f" | enum_python={enum_pairs}"
            f" | IMPORTANT: use enum_db_values literals in SQL predicates"
        )

    @classmethod
    def _get_db_schema_description(cls) -> str:
        lines: list[str] = []
        lines.append(
            "IMPORTANT ENUM RULE: for enum columns in WHERE/IN use ONLY enum_db_values."
        )
        lines.append("")
        for table_name, table in Base.metadata.tables.items():
            lines.append(f"Table {table_name}:")
            for column in table.columns:
                fk_targets = [str(fk.column) for fk in column.foreign_keys]
                type_name = column.type.__class__.__name__
                enum_description = cls._format_enum_column_description(column)
                if fk_targets:
                    lines.append(
                        f"- {column.name} ({type_name}) -> {', '.join(fk_targets)}{enum_description}"
                    )
                else:
                    lines.append(f"- {column.name} ({type_name}){enum_description}")
            lines.append("")
        return "\n".join(lines)

    def _normalize_enum_literals_in_sql(self, query: str) -> str:
        if not self.enum_literal_map or not self.enum_column_names:
            return query

        column_pattern = "|".join(
            sorted((re.escape(name) for name in self.enum_column_names), key=len, reverse=True)
        )

        def _normalize_literal(literal: str) -> str:
            normalized_literal = self.enum_literal_map.get(literal.casefold())
            if not normalized_literal or normalized_literal == literal:
                return f"'{literal}'"
            logger.info(
                "Analytics enum literal normalized: '%s' -> '%s'",
                literal,
                normalized_literal,
            )
            return f"'{normalized_literal}'"

        in_pattern = re.compile(
            rf"(?i)(\b(?:\w+\.)?(?:{column_pattern})\b\s+(?:not\s+)?in\s*\()([^)]+)(\))"
        )

        def _replace_in(match: re.Match[str]) -> str:
            prefix, body, suffix = match.groups()
            new_body = re.sub(r"'([^']*)'", lambda m: _normalize_literal(m.group(1)), body)
            return f"{prefix}{new_body}{suffix}"

        query = in_pattern.sub(_replace_in, query)

        eq_pattern = re.compile(
            rf"(?i)(\b(?:\w+\.)?(?:{column_pattern})\b\s*(?:=|!=|<>)\s*)'([^']*)'"
        )

        def _replace_eq(match: re.Match[str]) -> str:
            prefix = match.group(1)
            replaced_literal = _normalize_literal(match.group(2))
            return f"{prefix}{replaced_literal}"

        return eq_pattern.sub(_replace_eq, query)

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
        logger.info("Executing analytics SQL query:\n%s", query)
        result = await self.session.execute(text(query))
        rows = result.mappings().all()
        logger.info("Analytics SQL executed: rows=%s", len(rows))
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
        logger.info("Analytics question requested: question_len=%s contexts=%s", len(question), len(context))
        logger.info("Analytics question text:\n%s", question)
        schema = self._get_db_schema_description()
        request_context = self._format_request_contexts(context)
        logger.info("Analytics schema prepared: chars=%s", len(schema))
        logger.info("Analytics request context prepared:\n%s", _preview(request_context))
        steps: list[AnalyticsStep] = []
        for step_number in range(1, MAX_SQL_STEPS + 1):
            logger.info("Analytics step started: step=%s", step_number)
            prompt = Prompts.get_prompt_for_analytics_step(
                question=question,
                schema=schema,
                request_context=request_context,
                previous_steps=steps,
                max_limit=MAX_SQL_LIMIT,
            )
            logger.info(
                "Analytics step prompt built: step=%s chars=%s\n%s",
                step_number,
                len(prompt),
                _preview(prompt),
            )
            raw_response = await self.connection.ask_text(prompt)
            if not raw_response:
                logger.warning("Analytics failed: empty response at step=%s", step_number)
                return None
            logger.info(
                "Analytics step raw response: step=%s chars=%s\n%s",
                step_number,
                len(raw_response),
                _preview(raw_response),
            )
            model_decision = self._extract_json(raw_response)
            if not model_decision:
                logger.warning("Analytics failed: invalid JSON at step=%s", step_number)
                return None
            logger.info(
                "Analytics step JSON decision: step=%s payload=%s",
                step_number,
                _preview(json.dumps(model_decision, ensure_ascii=False)),
            )
            action = model_decision.get("action")
            if action == "final":
                answer = model_decision.get("answer")
                if not answer:
                    logger.warning("Analytics failed: empty final answer at step=%s", step_number)
                    return None
                logger.info("Analytics completed with model final action at step=%s", step_number)
                logger.info("Analytics final answer:\n%s", answer)
                return AnalyticsResult(answer=answer, question=question)
            if action != "query":
                logger.warning("Analytics failed: invalid action=%s at step=%s", action, step_number)
                return None
            sql = model_decision.get("sql")
            comment = model_decision.get("comment", "")
            logger.info("Analytics step model comment: step=%s comment=%s", step_number, comment)
            if not sql or not isinstance(sql, str):
                logger.warning("Analytics failed: SQL missing or invalid at step=%s", step_number)
                return None
            logger.info("Analytics step SQL raw: step=%s\n%s", step_number, sql)
            if not self._is_safe_sql(sql):
                logger.warning("Analytics failed: unsafe SQL at step=%s", step_number)
                return None
            sql = self._apply_limit(sql)
            sql = self._normalize_enum_literals_in_sql(sql)
            logger.info("Analytics step SQL prepared: step=%s\n%s", step_number, sql)
            rows = await self.execute_read_only_query(sql)
            logger.info("Analytics step completed: step=%s rows=%s", step_number, len(rows))
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
        logger.info("Analytics final prompt built: chars=%s\n%s", len(final_prompt), _preview(final_prompt))

        final_raw_response = await self.connection.ask_text(final_prompt)
        if not final_raw_response:
            logger.warning("Analytics failed: empty final response")
            return None
        logger.info(
            "Analytics final raw response: chars=%s\n%s",
            len(final_raw_response),
            _preview(final_raw_response),
        )

        final_data = self._extract_json(final_raw_response)
        if not final_data:
            logger.warning("Analytics failed: invalid final JSON")
            return None
        logger.info(
            "Analytics final JSON payload=%s",
            _preview(json.dumps(final_data, ensure_ascii=False)),
        )

        final_answer = final_data.get("answer")
        if not final_answer:
            logger.warning("Analytics failed: final answer missing")
            return None

        logger.info("Analytics completed with synthesized final answer")
        logger.info("Analytics final answer:\n%s", final_answer)
        return AnalyticsResult(answer=final_answer, question=question)
