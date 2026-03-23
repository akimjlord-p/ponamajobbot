import json


class Prompts:
    @staticmethod
    def get_prompt_for_synonym(word: str) ->str:
        prompt = f"""
тебе будет дано одно слово — название товара или операции.
верни только полезные для распознавания варианты написания этого слова.

требования:
- включи русский вариант
- включи возможный английский вариант, если он реально используется
- включи транслит(английские слова кириллицей:(яблоко - apple на английском - эпл транслитом) только если он реалистичен
- не добавляй абстрактные близкие по смыслу слова
- не добавляй редкие или спорные варианты
- все слова в нижнем регистре
- только список через запятую без пробелов
- без пояснений
- без дубликатов

    слово: {word}"""

        return prompt

    @staticmethod
    def get_report_parsing_prompt(report_text: str, parsing_context: str | None = None) -> str:
        context_block = parsing_context or "Нет дополнительного контекста"

        return f"""
    Ты парсер рабочих отчетов сотрудников.

    Твоя задача:
    1. определить, можно ли извлечь из отчета операции
    2. если можно — вернуть список операций
    3. операция это: 
        operation_name: тип операции(например сборка/покраска/упаковка),
        product_name: название объекта над которым проводилась операция(например коробка/куртка/кружка)
        quantity: количество выполненных действий (целое число)
        пример: покрасил(operation_name: покраска) 5(quantity: 5) кружек (product_name: кружка) 
    4. если нельзя — вернуть text_only(полезная для бизнеса текстовая информация) или no_actionable_data(тяжело разобрать/есть вопросы)
    5. если не уверен в операции или товаре — лучше верни no_actionable_data
    Дополнительный контекст:
    {context_block}

    Отчет:
    {report_text}

    Верни только JSON без пояснений в формате:
    {{
      "report_result": "operations_created" | "text_only" | "no_actionable_data",
      "operations": [
        {{
          "product_name": "string",
          "operation_type_name": "string",
          "quantity": integer
        }}
      ]
    }}
    """

    @staticmethod
    def get_prompt_for_analytics_step(
        question: str,
        schema: str,
        request_context: str,
        previous_steps: list,
        max_limit: int,
    ) -> str:
        steps_payload = []
        for step in previous_steps:
            steps_payload.append(
                {
                    "step_number": step.step_number,
                    "sql": step.sql,
                    "comment": step.comment,
                    "rows": step.rows,
                }
            )

        return f"""
Ты аналитический AI для внутренней системы учета работы сотрудников.

Твоя задача: ответить на вопрос пользователя, используя ТОЛЬКО SQL SELECT запросы к SQLite базе.

Правила:
1. Разрешены только SELECT и WITH ... SELECT.
2. Никогда не используй INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA.
3. Не делай больше одного SQL statement.
4. Всегда думай пошагово.
5. Если данных уже достаточно — не предлагай новый SQL, а верни финальный ответ.
6. Если нужен SQL — делай только один следующий запрос.
7. Учитывай, что LIMIT больше {max_limit} недопустим.
8. Верни ТОЛЬКО JSON без markdown и без пояснений.

Схема БД:
{schema}

Контекст от админа:
{request_context}

Исходный вопрос:
{question}

Предыдущие шаги:
{json.dumps(steps_payload, ensure_ascii=False)}

Верни один из двух JSON форматов.

Если нужен следующий SQL:
{{
  "action": "query",
  "comment": "зачем нужен этот следующий запрос",
  "sql": "SELECT ..."
}}

Если данных уже достаточно:
{{
  "action": "final",
  "answer": "готовый понятный ответ пользователю на русском языке"
}}
""".strip()

    @staticmethod
    def get_prompt_for_analytics_final_answer(
        question: str,
        request_context: str,
        previous_steps: list,
    ) -> str:
        steps_payload = []
        for step in previous_steps:
            steps_payload.append(
                {
                    "step_number": step.step_number,
                    "sql": step.sql,
                    "comment": step.comment,
                    "rows": step.rows,
                }
            )

        return f"""
Ты аналитический AI.

Нужно дать финальный ответ пользователю на основе уже собранных данных.

Верни ТОЛЬКО JSON без markdown:
{{
  "answer": "финальный ответ пользователю на русском языке"
}}

Исходный вопрос:
{question}

Контекст от админа:
{request_context}

Собранные шаги и данные:
{json.dumps(steps_payload, ensure_ascii=False)}
""".strip()