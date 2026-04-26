# ai_tg_bot

Telegram-бот, работающий как простой AI-чат на **локальной** LLM. Принимает текстовые сообщения, отправляет их в [Ollama](https://ollama.com), возвращает ответ. Никаких облачных API, никакой базы данных, никакой истории диалога — каждое сообщение обрабатывается независимо.

Построен на [`aiogram 3`](https://docs.aiogram.dev/) + `asyncio` + [`pydantic-settings`](https://docs.pydantic.dev/latest/concepts/pydantic_settings/), покрыт unit-тестами на `pytest` с моками (никаких сетевых вызовов в тестах).

## Возможности

- 🚀 **Long polling** через aiogram 3, без webhook.
- 🧠 **Локальная LLM** через Ollama (по умолчанию `qwen3.5:0.8b` и `deepseek-r1:1.5b`, набор настраивается через `.env`).
- ⚙️ **Per-user настройки**: каждый пользователь может выбрать свою модель и системный промпт командой; настройки живут только в памяти процесса.
- 💬 **5 команд**: `/start`, `/help`, `/models`, `/model <name>`, `/prompt [<text>]`. Любой не-командный текст уходит в LLM.
- 🛡 **Обработка ошибок LLM**: таймаут / недоступность / 4xx-5xx — каждое отдаётся пользователю человеческим сообщением, в лог пишется `WARNING`/`ERROR`.
- 📜 **Логирование** в консоль и в файл с ротацией (`RotatingFileHandler`); метрики `user / chat / model / dur_ms / status` по каждому запросу. Контент сообщений в лог не пишется.
- ✂️ **Разбивка длинных ответов** > 4096 символов на части (Telegram API limit).
- 🧪 **Unit-тесты** через моки: ~60 тестов проходят за секунды без реального Telegram/Ollama.

## Требования

- **Python 3.11+** (разрабатывалось на 3.12).
- **Ollama** (локальный сервис) с предзагруженными моделями.
- **Telegram bot token** от [@BotFather](https://t.me/BotFather).

## Установка

```bash
git clone https://github.com/radif-ru/ai_tg_bot.git
cd ai_tg_bot

python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

## Настройка

1. Скопировать шаблон и отредактировать секреты:

   ```bash
   cp .env.example .env
   # вписать TELEGRAM_BOT_TOKEN и при необходимости поменять модели / URL Ollama
   ```

2. Переменные окружения (полный список — в `_docs/stack.md` §9):

   | Переменная                | Назначение                                                                 |
   |---------------------------|----------------------------------------------------------------------------|
   | `TELEGRAM_BOT_TOKEN`      | Токен бота от @BotFather (обязательно).                                    |
   | `OLLAMA_BASE_URL`         | URL локального Ollama API (по умолчанию `http://localhost:11434`).         |
   | `OLLAMA_DEFAULT_MODEL`    | Модель по умолчанию (должна быть в `OLLAMA_AVAILABLE_MODELS`).             |
   | `OLLAMA_AVAILABLE_MODELS` | Список разрешённых моделей через запятую.                                  |
   | `OLLAMA_TIMEOUT`          | Таймаут запроса к Ollama, секунды.                                         |
   | `SYSTEM_PROMPT`           | Системный промпт по умолчанию.                                             |
   | `LOG_LEVEL`               | Уровень логов: `DEBUG` \| `INFO` \| `WARNING` \| `ERROR`.                  |
   | `LOG_FILE`                | Путь к файлу логов (каталог создаётся автоматически).                      |

3. Загрузить модели в Ollama:

   ```bash
   ollama pull qwen3.5:0.8b
   ollama pull deepseek-r1:1.5b
   ollama list   # убедиться, что модели появились
   ```

## Запуск

```bash
ollama serve &              # если Ollama ещё не запущена
source .venv/bin/activate
python -m app
```

В консоли появится строка уровня `INFO`: `Bot started`. Остановить — `Ctrl+C`.

## Команды бота

| Команда                | Параметры       | Что делает                                                    |
|------------------------|-----------------|---------------------------------------------------------------|
| `/start`               | —               | Приветствие, краткая инструкция, список команд.               |
| `/help`                | —               | Подробная справка, текущая модель и системный промпт.         |
| `/models`              | —               | Список `OLLAMA_AVAILABLE_MODELS` с пометкой активной модели.  |
| `/model <name>`        | имя модели      | Переключить активную модель для текущего пользователя.        |
| `/prompt [<text>]`     | текст \| пусто  | Задать системный промпт; без аргумента — сброс к дефолту.     |
| *произвольный текст*   | —               | Отправить в LLM и получить ответ.                             |

Подробное поведение каждой команды — в `_docs/commands.md`.

## Тесты

```bash
pytest -q
```

С покрытием (если установлен `pytest-cov`):

```bash
pytest --cov=app --cov-report=term-missing
```

Тесты не делают сетевых вызовов — `aiogram.Bot`, `Message` и `ollama.AsyncClient` мокируются через `pytest-mock`.

## Структура проекта

```
app/                    # код приложения
├── main.py             # сборка Bot/Dispatcher и запуск polling
├── config.py           # Settings на pydantic-settings
├── logging_config.py   # dictConfig + RotatingFileHandler
├── handlers/           # /start, /help, /models, /model, /prompt + handler произвольного текста + errors
├── services/           # OllamaClient (LLM) + UserSettingsRegistry (per-user model/prompt)
├── middlewares/        # LoggingMiddleware
└── utils/              # split_long_message и пр.

tests/                  # зеркалит app/, моки aiogram и ollama
_docs/                  # проектная документация (см. _docs/README.md)
_board/                 # доска задач: индекс спринтов + sprints/<NN>-...
```

Полное дерево с описаниями — `_docs/project-structure.md`.

## Ограничения

По дизайну:

- Без **истории диалога** — каждое сообщение независимо.
- Без **БД** / persistent хранения.
- Без **облачных LLM** — только локальный Ollama.
- Только **long polling**, без webhook.
- Игнорирует **нетекстовые сообщения** (фото, аудио, стикеры).

Известные нюансы кода (легаси / тех.долг) — `_docs/current-state.md` §2 и `_docs/legacy.md`.
Кандидаты в следующие спринты (Docker, CI, throttling, `/reset`, стриминг) — `_docs/roadmap.md` Этап 10.

## Документация

- 📘 [`_docs/README.md`](./_docs/README.md) — индекс проектной документации.
- 🏗️ [`_docs/architecture.md`](./_docs/architecture.md) — компоненты и поток данных.
- 💬 [`_docs/commands.md`](./_docs/commands.md) — спецификация команд бота.
- 📌 [`_docs/current-state.md`](./_docs/current-state.md) — фактическое состояние кода (читать перед правками).
- 🛠️ [`_docs/instructions.md`](./_docs/instructions.md) — правила разработки.
- 🔗 [`_docs/links.md`](./_docs/links.md) — каталог внешних ссылок (aiogram, Ollama, pydantic, …).
- 📋 [`_board/README.md`](./_board/README.md) — процесс работы со спринтами и задачами.
