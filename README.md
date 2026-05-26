# ponamajobbot

Telegram-бот для учета рабочих сессий, отчетов и внутренней аналитики.

## Технологии

- Python 3.11+
- aiogram 3
- SQLAlchemy (async) + aiosqlite
- APScheduler
- LangChain OpenAI (`langchain-openai`)
- python-dotenv

## Запуск

1. Создайте и активируйте виртуальное окружение.
2. Установите зависимости:

```bash
pip install aiogram sqlalchemy aiosqlite apscheduler python-dotenv httpx langchain-openai pytest
```

3. Заполните `.env`:

```env
BOT_TOKEN=...
OPENAPI_API_KEY=...
PROXY_URL=
TG_PROXY_URL=
RUN_LLM_TEST=False
```

4. Запустите бота:

```bash
python main.py
```

## Структура проекта

```text
main.py
bot.py
config.py
middlewares.py
keyboards.py

handlers/
  ai_chapter.py
  admin_worker_chapter.py
  operation_chapter.py
  product_chapter.py
  rates_chapter.py
  start.py
  worker_chapter.py

services/
  ai_service/
    analytics.py
    container.py
    llm_connection.py
    parsing.py
    prompts.py
    service.py
    synonyms.py
  comment_service.py
  context_service.py
  operation_service.py
  operation_type_service.py
  product_service.py
  rate_service.py
  report_service.py
  session_service.py
  user_service.py
  worker_service.py

repositories/
  ai_repository.py
  comment_repository.py
  operation_repository.py
  rate_repository.py
  report_repository.py
  session_repository.py
  user_repository.py

db/
  base.py
  models.py
  session.py

utils/
  logger.py
  proxy.py
```

## Слои

- `handlers` — Telegram-роутеры и пользовательские сценарии.
- `services` — бизнес-логика.
- `repositories` — доступ к данным.
- `db` — модели и настройка async-сессии SQLAlchemy.

## Команды бота

### `/ai`

- `/question` — задать вопрос ИИ-аналитике.
- `/context` — добавить запись в накопительный контекст для аналитики.
- `/show_context` — посмотреть текущий накопительный контекст для аналитики.
- `/back` — вернуться в главное меню.

## Тесты

```bash
pytest
```
