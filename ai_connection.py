import re
import httpx

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase

from config import OPENAI_API_KEY, PROXY_URL
from prompts import generate_sql_step_prompt, generate_final_answer_prompt


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

    prompt = generate_sql_step_prompt(
        question=question,
        history=history,
        schema_text=SCHEMA_TEXT,
        max_steps=MAX_SQL_STEPS
    )

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

    answer_prompt = generate_final_answer_prompt(
        question=question,
        history=history
    )

    resp = await llm.ainvoke(answer_prompt)

    return resp.content