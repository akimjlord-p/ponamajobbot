import re
import httpx
import asyncio

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase

from config import OPENAI_API_KEY, PROXY_URL


MAX_SQL_STEPS = 4


db = SQLDatabase.from_uri("sqlite:///database.db")
http_client = httpx.AsyncClient(proxy=PROXY_URL, timeout=30.0)

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=OPENAI_API_KEY,
    http_async_client=http_client,
    temperature=0,
)


def build_schema_text(db: SQLDatabase) -> str:
    tables = db.get_usable_table_names()
    parts = []

    for table in tables:
        try:
            schema = db.get_table_info([table])
            parts.append(schema)
        except Exception:
            pass

    return "\n\n".join(parts)


SCHEMA_TEXT = build_schema_text(db)


FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|ATTACH|DETACH|PRAGMA)\b",
    re.IGNORECASE,
)


def extract_sql(text: str) -> str:
    text = text.strip()
    text = text.replace("```sql", "").replace("```", "").strip()
    return text


def validate_sql(sql: str) -> str:
    sql = sql.strip()

    if FORBIDDEN.search(sql):
        raise ValueError("Разрешены только SELECT-запросы.")

    if not sql.upper().startswith("SELECT"):
        raise ValueError("Разрешены только SELECT-запросы.")

    parts = [part.strip() for part in sql.split(";") if part.strip()]

    if len(parts) != 1:
        raise ValueError("Разрешен только один SQL-запрос.")

    return parts[0] + ";"


async def generate_next_step(question, history):
    prompt = f"""
Ты опытный бизнес-аналитик и эксперт по SQL (SQLite).

Твоя задача — ответить на вопрос пользователя, анализируя данные в базе.

Ты работаешь как аналитик данных и можешь выполнить до {MAX_SQL_STEPS} SQL-запросов.

Работай по этапам:

1. Сначала получи общую картину данных (агрегированные показатели).
2. Затем исследуй возможные причины или детали.
3. После этого сделай аналитический вывод.

Если данных уже достаточно для ответа — напиши:

FINAL

Если данных недостаточно — верни следующий SQL-запрос.


────────────────
ПРАВИЛА SQL
────────────────

1. Используй только SELECT.
2. Запрещены любые изменения базы данных:
INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, ATTACH, DETACH, PRAGMA.
3. Верни только SQL без пояснений.
4. Не возвращай несколько SQL-запросов.
5. Используй только таблицы и поля из схемы.
6. Ограничивай большие выборки LIMIT 20.
7. Не повторяй SQL, который уже выполнялся.
8. Если используется ID (например worker_id), постарайся сделать JOIN и вернуть понятные поля (например username).


────────────────
ПРАВИЛА АГРЕГАЦИИ
────────────────

Если агрегируются данные из нескольких таблиц,
не делай несколько LEFT JOIN с COUNT одновременно,
потому что это может создать умножение строк.

В таких случаях используй:

• подзапросы (subqueries)
или
• COUNT(DISTINCT ...)
или
• отдельные агрегаты

чтобы каждая метрика считалась независимо.


────────────────
ПРАВИЛА АНАЛИЗА
────────────────

Если вопрос аналитический (например:

• какие проблемы у бизнеса
• кто работает лучше
• где слабые места
• почему показатели отличаются
• что работает хуже других
• где низкая эффективность

),

работай так:

1. Сначала собери агрегированные показатели.
2. Затем исследуй возможные причины различий.
3. Если нужно — получи детальные записи или текстовые данные.
4. Только после этого делай вывод.

Не завершай анализ, если агрегированные данные не объясняют причины различий.


────────────────
АНАЛИЗ БИЗНЕСА
────────────────

При бизнес-анализе обращай внимание на:

• различия между объектами
• аномально низкие показатели
• сильные отклонения
• дисбаланс метрик
• необычные паттерны данных


────────────────
ВАЖНО
────────────────

Никогда не выбирай "лучшего" или "худшего" объекта (LIMIT 1),
пока не сравнишь несколько кандидатов.


────────────────
СХЕМА БАЗЫ ДАННЫХ
────────────────

{SCHEMA_TEXT}


────────────────
ВОПРОС ПОЛЬЗОВАТЕЛЯ
────────────────

{question}


────────────────
ПРЕДЫДУЩИЕ SQL И РЕЗУЛЬТАТЫ
────────────────

{history}


Если требуется больше данных — верни следующий SQL-запрос.

Если данных достаточно — напиши:

FINAL
""".strip()

    resp = await llm.ainvoke(prompt)

    return resp.content.strip()


async def ask_sql(question: str) -> str:

    history = ""
    last_result = None

    for step in range(MAX_SQL_STEPS):


        action = await generate_next_step(question, history)

        if action.upper().startswith("FINAL"):
            break

        sql = extract_sql(action)
        sql = validate_sql(sql)


        result = db.run(sql)


        last_result = result

        history += f"\nSQL: {sql}\nRESULT: {result}\n"

    answer_prompt = f"""
Ты бизнес-аналитик.

Ты провел анализ данных, чтобы ответить на вопрос пользователя.


ВОПРОС ПОЛЬЗОВАТЕЛЯ:

{question}


В ХОДЕ АНАЛИЗА БЫЛИ ВЫПОЛНЕНЫ SQL-ЗАПРОСЫ:

{history}


Твоя задача — сформулировать понятный аналитический вывод.


────────────────
ПРАВИЛА
────────────────

1. Используй только данные из результатов SQL.
2. Не придумывай факты.
3. Если данных недостаточно — честно скажи об этом.
4. Если данные противоречивы — объясни это.


────────────────
КАК ДЕЛАТЬ АНАЛИЗ
────────────────

Если вопрос связан с анализом бизнеса, попробуй:

• найти слабые места
• сравнить показатели
• выявить аномалии
• объяснить возможные причины


Например проблемы могут быть:

• низкая активность
• падение метрик
• неравномерная нагрузка
• дисбаланс показателей
• отсутствие регулярности


────────────────
СТИЛЬ ОТВЕТА
────────────────

Ответ должен быть:

• 3–6 предложений
• понятным
• аналитическим
• с упоминанием конкретных метрик


Пример хорошего ответа:

"Активность сотрудников распределена неравномерно.  
Иван и Петр показывают наибольшее рабочее время (216 часов),  
тогда как у Анны и Олега значительно меньше суммарная занятость.  

Это может говорить о дисбалансе нагрузки внутри команды.  
Если такая ситуация сохраняется, стоит проверить распределение смен."


Не используй технические ID, если есть более понятные поля (например username).
""".strip()

    resp = await llm.ainvoke(answer_prompt)

    return resp.content


