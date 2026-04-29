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


MAX_ANALYTICS_STEPS = 5
MAX_SQL_LIMIT = 50
MAX_ROWS_FOR_MODEL = 30
MAX_TEXT_RESULT_CHARS = 1800
MAX_STEP_RESULT_CHARS = 1800
MAX_LOG_TEXT_PREVIEW = 4000


logger = get_logger(__name__)


def _preview(text: str, limit: int = MAX_LOG_TEXT_PREVIEW) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated {len(text) - limit} chars]"


@dataclass
class AnalyticsStep:
    step_number: int
    action: str
    comment: str
    query: str
    result: Any


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
        return f" enum_db_values={db_values}"

    @classmethod
    def _get_db_schema_description(cls) -> str:
        lines: list[str] = ["Enum rule: use enum_db_values in SQL WHERE/IN."]
        for table_name, table in Base.metadata.tables.items():
            column_descriptions: list[str] = []
            for column in table.columns:
                fk_targets = [str(fk.column) for fk in column.foreign_keys]
                type_name = column.type.__class__.__name__.replace("Integer", "Int").replace("DateTime", "DT")
                enum_description = cls._format_enum_column_description(column)
                description = f"{column.name}:{type_name}{enum_description}"
                if fk_targets:
                    description = f"{description}->" + ",".join(fk_targets)
                column_descriptions.append(description)
            lines.append(f"{table_name}({'; '.join(column_descriptions)})")
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
    def _format_steps_for_model(steps: list[AnalyticsStep]) -> str:
        def _compact_result(result: Any) -> Any:
            if isinstance(result, str):
                if len(result) <= MAX_STEP_RESULT_CHARS:
                    return result
                return {
                    "truncated": True,
                    "chars": len(result),
                    "preview": result[:MAX_STEP_RESULT_CHARS],
                }

            try:
                serialized = json.dumps(result, ensure_ascii=False, default=str)
            except TypeError:
                serialized = str(result)

            if len(serialized) <= MAX_STEP_RESULT_CHARS:
                return result
            return {
                "truncated": True,
                "chars": len(serialized),
                "preview": serialized[:MAX_STEP_RESULT_CHARS],
            }

        payload = [
            {
                "n": step.step_number,
                "action": step.action,
                "comment": step.comment,
                "query": step.query,
                "result": _compact_result(step.result),
            }
            for step in steps
        ]
        return json.dumps(payload, ensure_ascii=False)

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

    @staticmethod
    def _is_safe_sql(query: str) -> bool:
        normalized = " ".join(query.strip().lower().split())
        if not normalized:
            return False
        if not (normalized.startswith("select") or normalized.startswith("with")):
            return False
        if ";" in normalized.rstrip(";"):
            return False

        forbidden = {
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
        }
        tokens = re.findall(r"[a-z_]+", normalized)
        return not any(word in tokens for word in forbidden)

    @staticmethod
    def _apply_limit(query: str, max_limit: int = MAX_SQL_LIMIT) -> str:
        cleaned = query.strip().rstrip(";")
        match = re.search(r"\blimit\s+(\d+)\b", cleaned, flags=re.IGNORECASE)
        if match:
            current_limit = int(match.group(1))
            if current_limit > max_limit:
                return re.sub(r"\blimit\s+\d+\b", f"LIMIT {max_limit}", cleaned, flags=re.IGNORECASE)
            return cleaned
        return f"{cleaned}\nLIMIT {max_limit}"

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
            logger.info("Analytics enum literal normalized: '%s' -> '%s'", literal, normalized_literal)
            return f"'{normalized_literal}'"

        in_pattern = re.compile(
            rf"(?i)(\b(?:\w+\.)?(?:{column_pattern})\b\s+(?:not\s+)?in\s*\()([^)]+)(\))"
        )

        def _replace_in_literals(match: re.Match) -> str:
            new_body = re.sub(
                r"'([^']*)'",
                lambda literal_match: _normalize_literal(literal_match.group(1)),
                match.group(2),
            )
            return f"{match.group(1)}{new_body}{match.group(3)}"

        query = in_pattern.sub(_replace_in_literals, query)

        eq_pattern = re.compile(
            rf"(?i)(\b(?:\w+\.)?(?:{column_pattern})\b\s*(?:=|!=|<>)\s*)'([^']*)'"
        )
        return eq_pattern.sub(lambda match: f"{match.group(1)}{_normalize_literal(match.group(2))}", query)

    async def _ask_next_action(
        self,
        question: str,
        schema: str,
        request_context: str,
        steps: list[AnalyticsStep],
    ) -> dict[str, Any] | None:
        prompt = Prompts.get_prompt_for_analytics_step(
            question=question,
            schema=schema,
            request_context=request_context,
            previous_steps=self._format_steps_for_model(steps),
            max_limit=MAX_SQL_LIMIT,
        )
        logger.info("Analytics decision prompt built: chars=%s\n%s", len(prompt), _preview(prompt))

        raw_response = await self.connection.ask_text(prompt)
        if not raw_response:
            logger.warning("Analytics failed: empty decision response")
            return None
        logger.info("Analytics decision raw response: chars=%s\n%s", len(raw_response), _preview(raw_response))

        decision = self._extract_json(raw_response)
        if not decision:
            logger.warning("Analytics failed: invalid decision JSON")
            return None
        logger.info("Analytics decision JSON payload=%s", _preview(json.dumps(decision, ensure_ascii=False)))
        return decision

    async def execute_read_only_query(self, query: str) -> list[dict[str, Any]]:
        logger.info("Executing analytics SQL query:\n%s", query)
        result = await self.session.execute(text(query))
        rows = result.mappings().all()
        logger.info("Analytics SQL executed: rows=%s", len(rows))
        return [dict(row) for row in rows]

    async def _handle_sql_action(self, step_number: int, decision: dict[str, Any]) -> AnalyticsStep | None:
        query = decision.get("query") or decision.get("sql")
        comment = str(decision.get("comment", "")).strip()
        if not query or not isinstance(query, str):
            logger.warning("Analytics SQL action failed: query missing")
            return None
        if not self._is_safe_sql(query):
            logger.warning("Analytics SQL action failed: unsafe SQL")
            return None

        prepared_query = self._normalize_enum_literals_in_sql(self._apply_limit(query))
        rows = await self.execute_read_only_query(prepared_query)
        result = {
            "returned": len(rows),
            "shown": min(len(rows), MAX_ROWS_FOR_MODEL),
            "rows": rows[:MAX_ROWS_FOR_MODEL],
        }
        return AnalyticsStep(
            step_number=step_number,
            action="sql",
            comment=comment,
            query=prepared_query,
            result=result,
        )

    async def _handle_internet_action(
        self,
        step_number: int,
        question: str,
        decision: dict[str, Any],
    ) -> AnalyticsStep:
        query = str(decision.get("query") or "").strip()
        comment = str(decision.get("comment", "")).strip()
        if not query:
            query = "Нужны внешние данные по вопросу администратора."

        if not self.connection.web_search_enabled:
            result = "Интернет-поиск отключен для этой модели."
        else:
            prompt = Prompts.get_prompt_for_internet_observation(
                question=question,
                research_query=query,
                max_chars=MAX_TEXT_RESULT_CHARS,
            )
            result = await self.connection.ask_web_search(prompt) or "Интернет-поиск не вернул данных."
            result = result[:MAX_TEXT_RESULT_CHARS]

        return AnalyticsStep(
            step_number=step_number,
            action="internet",
            comment=comment,
            query=query,
            result=result,
        )

    async def _build_final_answer(
        self,
        question: str,
        request_context: str,
        steps: list[AnalyticsStep],
    ) -> AnalyticsResult | None:
        prompt = Prompts.get_prompt_for_analytics_final_answer(
            question=question,
            request_context=request_context,
            previous_steps=self._format_steps_for_model(steps),
        )
        logger.info("Analytics final prompt built: chars=%s\n%s", len(prompt), _preview(prompt))

        raw_response = await self.connection.ask_text(prompt)
        if not raw_response:
            logger.warning("Analytics failed: empty final response")
            return None

        data = self._extract_json(raw_response)
        if not data or not data.get("answer"):
            logger.warning("Analytics failed: invalid final JSON")
            return None

        answer = str(data["answer"]).strip()
        logger.info("Analytics final answer:\n%s", answer)
        return AnalyticsResult(answer=answer, question=question)

    async def question(self, question: str, context: list[AdminRequestsContext]) -> AnalyticsResult | None:
        logger.info("Analytics question requested: question_len=%s contexts=%s", len(question), len(context))
        logger.info("Analytics question text:\n%s", question)

        schema = self._get_db_schema_description()
        request_context = self._format_request_contexts(context)
        steps: list[AnalyticsStep] = []

        for step_number in range(1, MAX_ANALYTICS_STEPS + 1):
            logger.info("Analytics step started: step=%s", step_number)
            decision = await self._ask_next_action(question, schema, request_context, steps)
            if not decision:
                return None

            action = str(decision.get("action", "")).strip().lower()
            if action == "final":
                answer = str(decision.get("answer", "")).strip()
                if not answer:
                    logger.warning("Analytics failed: empty final answer at step=%s", step_number)
                    return None
                logger.info("Analytics completed with model final action at step=%s", step_number)
                return AnalyticsResult(answer=answer, question=question)

            if action in {"sql", "query"}:
                step = await self._handle_sql_action(step_number, decision)
                if step is None:
                    return None
                steps.append(step)
                continue

            if action == "internet":
                step = await self._handle_internet_action(step_number, question, decision)
                steps.append(step)
                continue

            logger.warning("Analytics failed: invalid action=%s at step=%s", action, step_number)
            return None

        logger.info("Analytics max steps reached, building final answer")
        return await self._build_final_answer(question, request_context, steps)
