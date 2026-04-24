# Структура проекта

Целевая структура репозитория после реализации MVP.

```
ai_tg_bot/
├── .env.example              # шаблон конфигурации (коммитится)
├── .env                      # реальные секреты (в .gitignore)
├── .gitignore
├── README.md                 # инструкция запуска + команды бота
├── requirements.txt          # runtime-зависимости
├── requirements-dev.txt      # dev-зависимости (pytest, ruff, mypy...)  — опционально
├── pyproject.toml            # конфиг ruff / pytest / mypy — опционально
│
├── docs/                     # проектная документация (этот каталог)
│   ├── README.md
│   ├── architecture.md
│   ├── mvp.md
│   ├── stack.md
│   ├── instructions.md
│   ├── requirements.md
│   ├── project-structure.md
│   ├── commands.md
│   ├── testing.md
│   └── roadmap.md
│
├── logs/                     # файлы логов (в .gitignore)
│   └── bot.log
│
├── app/                      # код приложения
│   ├── __init__.py
│   ├── __main__.py           # entrypoint: python -m app
│   ├── main.py               # async def main(): запуск polling
│   ├── config.py             # Settings на pydantic-settings
│   ├── logging_config.py     # dictConfig для logging
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py       # /start, /help, /model, /models, /prompt
│   │   ├── messages.py       # обработка текстовых сообщений
│   │   └── errors.py         # глобальный error handler
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm.py            # OllamaClient, LLMError
│   │   └── model_registry.py # in-memory map chat_id -> model
│   │
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── logging_mw.py     # middleware для логирования апдейтов
│   │
│   └── utils/
│       ├── __init__.py
│       └── text.py           # split_long_message и т. п.
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_config.py
    ├── services/
    │   ├── test_llm_client.py
    │   └── test_model_registry.py
    └── handlers/
        ├── test_commands.py
        └── test_messages.py
```

## Назначение ключевых модулей

| Путь | Ответственность |
|------|-----------------|
| `app/__main__.py` | Запуск `asyncio.run(main())`. |
| `app/main.py` | Собирает `Bot`, `Dispatcher`, регистрирует роутеры и middleware, стартует polling. |
| `app/config.py` | Класс `Settings(BaseSettings)`, парсинг `.env`, валидация. |
| `app/logging_config.py` | Функция `setup_logging(settings)` → `dictConfig`. |
| `app/handlers/commands.py` | Router с обработчиками команд. |
| `app/handlers/messages.py` | Router с обработчиком `F.text & ~F.text.startswith('/')`. |
| `app/handlers/errors.py` | `@dp.errors` — единая точка для необработанных ошибок. |
| `app/services/llm.py` | `OllamaClient` (async), кастомные исключения `LLMError`, `LLMTimeout`, `LLMUnavailable`. |
| `app/services/model_registry.py` | Потокобезопасная in-memory структура `dict[int, str]` (user_id → model). |
| `app/middlewares/logging_mw.py` | Логирование каждого апдейта (тип, user, chat, длительность). |
| `tests/` | Зеркалирует структуру `app/`, unit-тесты с моками. |

## Принципы организации

- **Слои не протекают**: handler не знает про HTTP, сервис не знает про aiogram.
- **Интерфейсы тонкие**: handler вызывает `await llm_client.generate(prompt, model, system)` — и всё.
- **DI через aiogram `workflow_data`**: `dp["llm_client"] = ...`, `dp["settings"] = ...`, handler получает их через параметры (aiogram 3 умеет инжектить по имени).
- **Тесты рядом с тем, что тестируют**: `tests/services/` зеркалит `app/services/`.

## Что должно попасть в `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/

# Tests / tools
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# IDE
.idea/
.vscode/

# Logs
logs/
*.log

# Secrets
.env
.env.*
!.env.example
```
