# ponamajobbot

Telegram bot for tracking worker shifts, collecting free-text reports, and running AI-powered internal analytics.

## Tech stack

- Python 3.11+
- aiogram 3
- SQLAlchemy (async) + aiosqlite
- APScheduler
- LangChain OpenAI (`langchain-openai`)
- python-dotenv

## Getting started

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install aiogram sqlalchemy aiosqlite apscheduler python-dotenv httpx langchain-openai pytest
```

3. Fill in `.env`:

```env
BOT_TOKEN=...
OPENAI_API_KEY=...
MAIN_ID=<your telegram id>
PROXY_URL=
TG_PROXY_URL=
RUN_LLM_TEST=False
```

4. Run the bot:

```bash
python main.py
```

## Project structure

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
  mailing_service.py
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

## Layers

- `handlers` — Telegram routers and user interaction flows.
- `services` — business logic.
- `repositories` — database access.
- `db` — SQLAlchemy models and async session setup.

## Bot commands

### Worker

- `/checkin` — open a work shift.
- `/checkout` — close the shift and submit a free-text report (parsed by AI).
- `/comment` — leave an idea, complaint, or general comment.

### Admin

- `/workers` — manage workers (list / add / delete).
- `/products` — manage product catalogue.
- `/operations` — manage operation types.
- `/rates` — manage operation rates.
- `/ai` — AI analytics section.

Admins can also use all worker commands to track their own shifts.

### AI section (`/ai`)

- `/question` — ask the AI analyst a question about the data.
- `/context` — add a note to the persistent analytics context.
- `/show_context` — view the current analytics context.
- `/back` — return to the main menu.

## Scheduled jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| `send_weekly_reports` | Every Sunday 10:00 MSK | Sends a weekly report digest to `MAIN_ID`: unresolved reports first, then all others. |

## Tests

```bash
pytest
```
