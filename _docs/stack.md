# Технологический стек

## 1. Runtime

- **Python** — 3.11+ (рекомендуется 3.12). Нужен нативный `asyncio` + `tomllib`, совместимость с актуальными aiogram/pydantic.
- **OS** — Linux / WSL2 Ubuntu (пользовательское окружение) / macOS. Windows нативно — не приоритет.

## 2. Telegram

- **aiogram** — `^3.4` (актуальная v3.x). Async, Router-based, встроенные middleware, удобный `Dispatcher.start_polling`.
  - `aiogram.client.default.DefaultBotProperties` для `parse_mode`.
  - `aiogram.filters.Command` для команд.
- Режим получения апдейтов — **long polling** (`dp.start_polling(bot)`), без webhook.

## 3. LLM-слой

- **Ollama** — локальный runtime для моделей. REST API на `http://localhost:11434`.
- **Модели из ТЗ**:
  - `qwen3.5:0.8b`
  - `deepseek-r1:1.5b`
  - Точные имена тегов уточнять через `ollama list` в своём окружении; конфигурируются через `.env`.
- **Клиент**: официальная библиотека **`ollama`** (async-вариант: `ollama.AsyncClient`) или прямые HTTP-запросы через **`httpx`** (async). Рекомендуется `ollama.AsyncClient` — меньше кода, стабильный API.

### Обоснование выбора
- `ollama` library — типизированные ответы, нативная поддержка стриминга, async-клиент.
- `httpx` — запасной вариант, если нужен полный контроль над HTTP.

## 4. Конфигурация

- **pydantic-settings** — `^2.1`. Загрузка `.env`, валидация типов, дефолты.
- **python-dotenv** — автоматически подтянется через `pydantic-settings[dotenv]`; явная установка не обязательна.

## 5. Логирование

- Стандартный модуль **`logging`** + `logging.handlers.RotatingFileHandler`.
- Конфигурация через `dictConfig` в `app/logging_config.py`.
- Формат: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`.
- Уровень — из `LOG_LEVEL` (`INFO` по умолчанию).
- Файл — из `LOG_FILE` (например, `logs/bot.log`), каталог `logs/` добавлен в `.gitignore`.

## 6. Тестирование

- **pytest** — `^8.0`.
- **pytest-asyncio** — `^0.23` (режим `asyncio_mode = "auto"` или `strict` с маркером).
- **pytest-mock** — `^3.12` (удобные моки).
- **respx** или **httpx.MockTransport** — мок HTTP-слоя для `httpx`. Если используется `ollama.AsyncClient`, можно мокать сам клиент через `pytest-mock`.
- Опционально: **coverage.py** (`pytest-cov`) для отчёта покрытия.

## 7. Качество кода (рекомендовано, не обязательно для MVP)

- **ruff** — линтер + форматтер в одном.
- **mypy** — статическая типизация (режим `--strict` на модулях сервис-слоя).
- **pre-commit** — хуки перед коммитом.

## 8. Менеджмент зависимостей

Два варианта на выбор (один из):

### Вариант A: `requirements.txt` + `venv` (минималистичный, под ТЗ)
```
aiogram>=3.4,<4
ollama>=0.3
pydantic-settings>=2.1,<3
pytest>=8
pytest-asyncio>=0.23
pytest-mock>=3.12
```
Плюс `requirements-dev.txt` с ruff/mypy при необходимости.

### Вариант B: `pyproject.toml` + `uv` / `poetry`
Предпочтителен, если команде удобно. Структура `pyproject.toml` с группами `[tool.poetry.group.dev.dependencies]` или `[project.optional-dependencies]`.

Для MVP достаточно **варианта A** — минимум артефактов, соответствует ТЗ.

## 9. Переменные окружения (`.env`)

Файл `.env.example` коммитится, `.env` — в `.gitignore`.

```dotenv
# --- Telegram ---
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# --- Ollama ---
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=qwen3.5:0.8b
OLLAMA_AVAILABLE_MODELS=qwen3.5:0.8b,deepseek-r1:1.5b
OLLAMA_TIMEOUT=60

# --- Bot behavior ---
SYSTEM_PROMPT=Ты — полезный ассистент. Отвечай кратко и по делу.

# --- Logging ---
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
```

## 10. Локальные требования окружения

- Установлен **Ollama** (`https://ollama.com`), запущен сервис (`ollama serve` или systemd-юнит).
- Модели предварительно загружены: `ollama pull qwen3.5:0.8b`, `ollama pull deepseek-r1:1.5b` (имена теги уточнить).
- Telegram-бот создан через `@BotFather`, токен сохранён в `.env`.

## 11. Чего в стеке нет (и не будет в MVP)

- БД любого рода.
- Redis / брокеры очередей.
- Docker / docker-compose (можно добавить позже, опционально).
- ORM, миграции.
- FastAPI / any web framework — polling не требует входящего HTTP.
