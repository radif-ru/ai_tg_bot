# ai_tg_bot

## О проекте

Telegram-бот, работающий как простой AI-чат: принимает текстовые сообщения, отправляет их
в локальную LLM через [Ollama](https://ollama.com) и возвращает ответ. Построен на
`aiogram 3` и `asyncio`, без БД и без истории диалога (stateless — каждое сообщение
обрабатывается независимо).

Подробная архитектура — `_docs/architecture.md`, полное ТЗ — `RAW.md`, формализованные
требования — `_docs/requirements.md`.

## Требования

- **Python 3.11+** (разрабатывалось и тестировалось на 3.12).
- **Ollama** с загруженными моделями (по умолчанию `qwen3.5:0.8b` и `deepseek-r1:1.5b`).
- **Telegram bot token** — получается у [@BotFather](https://t.me/BotFather).

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

1. Скопировать шаблон конфигурации:

   ```bash
   cp .env.example .env
   ```

2. Отредактировать `.env`. Переменные:

   | Переменная                | Назначение                                                                 |
   |---------------------------|----------------------------------------------------------------------------|
   | `TELEGRAM_BOT_TOKEN`      | Токен бота от @BotFather (обязательно).                                    |
   | `OLLAMA_BASE_URL`         | URL локального Ollama API (по умолчанию `http://localhost:11434`).         |
   | `OLLAMA_DEFAULT_MODEL`    | Модель по умолчанию (должна присутствовать в `OLLAMA_AVAILABLE_MODELS`).   |
   | `OLLAMA_AVAILABLE_MODELS` | Список разрешённых моделей через запятую.                                  |
   | `OLLAMA_TIMEOUT`          | Таймаут запроса к Ollama, секунды.                                         |
   | `SYSTEM_PROMPT`           | Системный промпт по умолчанию.                                             |
   | `LOG_LEVEL`               | Уровень логов: `DEBUG` \| `INFO` \| `WARNING` \| `ERROR`.                  |
   | `LOG_FILE`                | Путь к файлу логов (каталог создастся автоматически).                      |

3. Убедиться, что модели загружены:

   ```bash
   ollama pull qwen3.5:0.8b
   ollama pull deepseek-r1:1.5b
   ollama list
   ```

## Запуск

```bash
ollama serve &         # если ещё не запущен
source .venv/bin/activate
python -m app
```

В консоли должна появиться запись уровня `INFO`: `Bot started`. Остановить — `Ctrl+C`.

## Команды бота

| Команда            | Параметры       | Что делает                                                    |
|--------------------|-----------------|---------------------------------------------------------------|
| `/start`           | —               | Приветствие, краткая инструкция, список команд.               |
| `/help`            | —               | Подробная справка, текущая модель и системный промпт.         |
| `/models`          | —               | Список `OLLAMA_AVAILABLE_MODELS` с отметкой активной модели.  |
| `/model <name>`    | имя модели      | Переключить активную модель для текущего пользователя.        |
| `/prompt [text]`   | текст \| пусто  | Задать системный промпт; без аргумента — сброс к дефолту.     |
| *произвольный текст* | —             | Отправить в LLM и получить ответ.                             |

Подробнее — `_docs/commands.md`.

## Тесты

```bash
.venv/bin/pytest -q
```

Опционально, с покрытием (если установлен `pytest-cov`):

```bash
.venv/bin/pytest --cov=app --cov-report=term-missing
```

## Ограничения MVP

- Без истории диалога — каждое сообщение независимо.
- Без БД / persistent хранения.
- Без облачных LLM (только локальный Ollama).
- Только long polling, без webhook.
- Нет мультимодальных сообщений (фото/аудио/стикеры).

Полный список — `_docs/mvp.md` §3.
