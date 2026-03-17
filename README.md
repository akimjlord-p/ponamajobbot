# ponamajobbot

Telegram bot for tracking work sessions, collecting reports, and building internal analytics.

The project is being rebuilt around an explicit service and repository architecture with SQLAlchemy models in `db/`.

## Architecture

```text
main.py
bot.py
config.py
middlewares.py
auto_mailings.py
ai_connection.py

handlers/
  start.py
  admin.py
  report.py
  worker.py

services/
  user_service.py
  worker_service.py
  session_service.py
  report_service.py
  operation_service.py
  rate_service.py
  comment_service.py
  analytic_service.py

repositories/
  user_repository.py
  session_repository.py
  report_repository.py
  operation_repository.py
  rate_repository.py
  comment_repository.py
  ai_repository.py

db/
  base.py
  enums.py
  models.py
  session.py
```

## Layers

- `handlers` handle Telegram updates and user flows
- `services` contain business logic
- `repositories` work with the database
- `db` contains SQLAlchemy models, enums, and session setup

## Goals

- write AI service
- write tests
- write handlers
- add Docker
- add GitHub actions
