class Prompts:
    @staticmethod
    def get_prompt_for_synonym(word: str) ->str:
        prompt = f"""
    тебе будет дано одно слово (название операции или товара). верни список его синонимов и близких по смыслу вариантов.

    требования:
    - включи варианты на русском, английском и транслите (русское слово латиницей)
    - все слова должны быть в нижнем регистре
    - выведи только список слов
    - формат: через запятую без пробелов
    - не добавляй пояснений, только слова
    - избегай дубликатов

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
    3. если нельзя — вернуть text_only(полезная для бизнеса текстовая информация) или no_actionable_data(тяжело разобрать/есть вопросы)

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
          "operation_name": "string",
          "quantity": 1
        }}
      ]
    }}
    """