# Структура проекта

Целевая структура репозитория после реализации MVP.

```
ai_tg_bot/
├── .env.example              # шаблон конфигурации (коммитится)
├── .env                      # реальные секреты (в .gitignore)
├── .gitignore
├── CLAUDE.md                 # поведенческие гайдлайны LLM-агента (общие)
├── README.md                 # инструкция запуска + команды бота
├── requirements.txt          # runtime + dev-зависимости
├── pyproject.toml            # конфиг pytest (asyncio_mode=auto)
│
├── _docs/                     # проектная документация для LLM-агентов (этот каталог)
│   ├── README.md             # индекс документации
│   ├── RAW.md                # исходное ТЗ в свободной форме (источник истины)
│   ├── mvp.md                # scope MVP и критерии приёмки
│   ├── requirements.md       # FR / NFR / CON / ASM
│   ├── architecture.md       # компоненты, потоки данных, обработка ошибок
│   ├── stack.md              # версии, зависимости, переменные окружения
│   ├── instructions.md       # правила разработки (проектные)
│   ├── project-structure.md  # этот файл
│   ├── commands.md           # спецификация команд бота
│   ├── testing.md            # стратегия тестирования
│   └── roadmap.md            # этапы реализации
│
├── _board/                    # процесс и итерации для LLM-агентов
│   ├── README.md             # индекс
│   ├── plan.md               # детальный план задач (статусы ToDo/Progress/Done)
│   ├── process.md            # пошаговый процесс выполнения одной задачи
│   └── progress.txt          # ad-hoc заметки о прогрессе / чек-лист приёмки
│
├── logs/                      # файлы логов (в .gitignore)
│   └── bot.log
│
├── app/                       # код приложения
│   ├── __init__.py
│   ├── __main__.py            # entrypoint: python -m app
│   ├── main.py                # async def main(): запуск polling
│   ├── config.py              # Settings на pydantic-settings
│   ├── logging_config.py      # dictConfig для logging
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py        # /start, /help, /models, /model, /prompt
│   │   ├── messages.py        # F.text & ~F.text.startswith('/') → LLM
│   │   └── errors.py          # глобальный error handler (router.errors)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm.py             # OllamaClient + LLMError/LLMTimeout/LLMUnavailable/LLMBadResponse
│   │   └── model_registry.py  # UserSettingsRegistry: user_id → model + prompt
│   │
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── logging_mw.py      # LoggingMiddleware (user/chat/type/dur_ms/status)
│   │
│   └── utils/
│       ├── __init__.py
│       └── text.py            # split_long_message
│
└── tests/                     # зеркалирует app/
    ├── __init__.py
    ├── conftest.py            # фикстура base_env (изоляция переменных окружения)
    ├── test_config.py
    ├── test_logging_config.py
    ├── test_main.py           # smoke-тест сборки main()
    ├── test_middleware_logging.py
    ├── test_utils_text.py
    ├── services/
    │   ├── __init__.py
    │   ├── test_llm_client.py
    │   └── test_model_registry.py
    └── handlers/
        ├── __init__.py
        ├── test_commands.py
        ├── test_errors.py
        └── test_messages.py
```

## Назначение ключевых модулей

| Путь | Ответственность |
|------|-----------------|
| `CLAUDE.md` | Общие поведенческие гайдлайны LLM-агента (think before coding, simplicity, surgical changes, goal-driven). Читается первым перед любой задачей. |
| `_docs/RAW.md` | Исходное ТЗ в свободной форме — источник истины при расхождениях. |
| `_docs/*.md` | Проектная документация: формализованные требования, архитектура, стек, инструкции, roadmap. |
| `_board/plan.md` | Детальный план задач со статусами и Definition of Done. |
| `_board/process.md` | Пошаговый алгоритм выполнения одной задачи. |
| `_board/progress.txt` | Ad-hoc заметки о прогрессе / фиксация чек-листа приёмки. |
| `app/__main__.py` | Запуск `asyncio.run(main())`. |
| `app/main.py` | Собирает `Bot`, `Dispatcher`, регистрирует роутеры и middleware, стартует polling. |
| `app/config.py` | Класс `Settings(BaseSettings)`, парсинг `.env`, валидация. |
| `app/logging_config.py` | Функция `setup_logging(settings)` → `dictConfig`. |
| `app/handlers/commands.py` | Router с обработчиками команд (`/start`, `/help`, `/models`, `/model`, `/prompt`). |
| `app/handlers/messages.py` | Router с обработчиком `F.text & ~F.text.startswith('/')` → LLM. |
| `app/handlers/errors.py` | `@router.errors()` — единая точка для необработанных ошибок. |
| `app/services/llm.py` | `OllamaClient` (async) + иерархия `LLMError` → `LLMTimeout`/`LLMUnavailable`/`LLMBadResponse`. |
| `app/services/model_registry.py` | `UserSettingsRegistry`: in-memory `user_id → model` и `user_id → prompt`. |
| `app/middlewares/logging_mw.py` | Логирование каждого апдейта (`user`, `chat`, `type`, `dur_ms`, `status`). |
| `app/utils/text.py` | `split_long_message` — разбивка длинных ответов LLM по границам строк/пробелов. |
| `tests/` | Зеркалирует `app/`, unit-тесты с моками; никаких сетевых вызовов. |

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
