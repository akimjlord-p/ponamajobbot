# ponamajobbot

Telegram-бот для учета рабочих смен, сбора отчетов и формирования управленческой аналитики.

## Что есть в проекте сейчас

- Контроль доступа по `@username` + роль администратора.
- Админский сценарий добавления сотрудника (`/worker`).
- Учет рабочей смены:
  - `/checkin` — открыть смену;
  - `/checkout` — закрыть смену и отправить дневной отчет.
- Недельный отчет сотрудника (`/report`).
- Автоматические рассылки руководителю:
  - ежедневная сводка;
  - еженедельная сводка.
- AI-режим для админа (`/ai`): бот строит SQL-запросы к базе отчетов и возвращает текстовую аналитику.
- Хранение данных в SQLite через SQLAlchemy.

## Технологии

- Python 3.11+
- [aiogram](https://docs.aiogram.dev/)
- SQLAlchemy
- APScheduler
- python-dotenv
- httpx
- langchain-openai
- langchain-community
- SQLite (текущая БД)

## Структура проекта

```text
.
├── main.py               # Точка входа
├── bot.py                # Инициализация бота, роутеры, scheduler
├── config.py             # Переменные окружения
├── db.py                 # Синхронный слой работы с БД
├── models.py             # SQLAlchemy-модели
├── auto_mailings.py      # Ежедневная/еженедельная рассылка
├── ai_connection.py      # AI-аналитика (LLM + SQL)
├── middlewares.py        # Access/Admin middleware
├── keyboards.py          # Клавиатуры
└── handlers/
    ├── start.py          # /start
    ├── admin.py          # /worker
    ├── report.py         # /checkin, /checkout, /report
    └── ai_mod.py         # /ai
```

## Быстрый старт (локально)

### 1) Подготовка окружения

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Установка зависимостей

`requirements.txt` пока не добавлен, поэтому установка вручную:

```bash
pip install aiogram sqlalchemy apscheduler python-dotenv httpx langchain-openai langchain-community
```

### 3) Настройка `.env`

Создайте `.env` в корне проекта:

```env
BOT_TOKEN=your_telegram_bot_token
MAIN_ID=your_telegram_id
ADMINS=123456789,987654321

# Для AI-модуля (имя переменной должно совпадать с кодом config.py)
OPENAPI_API_KEY=your_openai_api_key
PROXY_URL=http://your-proxy:port
```

> Примечание: в текущем коде используется переменная `OPENAPI_API_KEY` (именно в таком написании).

### 4) Запуск

```bash
python main.py
```

При первом запуске создается файл БД `database.db` (SQLite).

## Текущий план разработки

Приоритетные задачи:

1. Перевести слой БД на **асинхронные запросы**.
2. Убрать проблему **N+1** при формировании рассылок отчетов.
3. Добавить **Docker** (сборка и запуск сервиса).
4. Добавить и поддерживать **requirements.txt**.

## Возможные задачи следующего этапа

- Переход с SQLite на **PostgreSQL**.
- Добавление миграций схемы БД (например, **Alembic**).

## Статус

Проект активно развивается: документация и инфраструктура будут расширяться вместе с реализацией roadmap-задач.
