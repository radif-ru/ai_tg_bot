# Спринт 01. MVP

- **Источник:** `_docs/mvp.md` §5 (критерии приёмки), `_docs/requirements.md` (FR-1…FR-12, NFR-1…NFR-9), `_docs/roadmap.md` «Этапы 2–9».
- **Ветка:** `main` (задним числом — спринт оформлен после введения формата `sprints/<NN>-<short-name>.md`; до введения правила «новый спринт = новая ветка»).
- **Открыт:** 2026-04-25
- **Закрыт:** 2026-04-26

## 1. Цель спринта

Довести проект от пустого скелета (закрытого спринта 00) до запускаемого MVP: Telegram-бот на `aiogram 3` с локальной LLM через Ollama, с командами `/start`, `/help`, `/models`, `/model`, `/prompt`, обработкой произвольного текста, логированием, обработкой ошибок и unit-тестами через мок-объекты.

## 2. Скоуп и non-goals

- **В скоупе:** конфигурация (`Settings`), логирование (`RotatingFileHandler`), `OllamaClient` и иерархия `LLMError`, `UserSettingsRegistry`, entrypoint, все 5 команд бота, обработчик произвольного текста, middleware логирования, глобальный error handler, README, чек-лист приёмки.
- **Вне скоупа (non-goals):** Docker / CI, throttling, `/reset`, стриминг ответа, web-UI, любые персистентные хранилища. Эти пункты — кандидаты в следующие спринты (см. `_docs/roadmap.md` Этап 10).

## 3. Acceptance Criteria спринта

- [x] `python -m app` запускается, в консоли появляется `INFO ... Bot started`.
- [x] В Telegram работают `/start`, `/help`, `/models`, `/model <name>`, `/prompt [<text>]`.
- [x] Произвольный текст возвращает ответ от выбранной LLM (ручная проверка).
- [x] При остановленной Ollama бот не падает, отвечает «LLM сейчас недоступна», в логе — `ERROR`.
- [x] Логи пишутся в консоль и в файл с ротацией (`logs/bot.log` по умолчанию).
- [x] `pytest -q` зелёный (минимум: LLM-клиент, /start, обработчик текста, /models/model/prompt, middleware, error handler, registry, config, logging, utils).
- [x] `README.md` содержит разделы: «Установка», «Настройка», «Запуск», «Команды бота», «Тесты», «Ограничения MVP».
- [x] Все 10 пунктов `_docs/mvp.md` §5 закрыты (см. `_board/progress.txt`).
- [x] Все задачи спринта — `Done`, сводная таблица актуальна.

## 4. Этап 1. Конфигурация и LLM-клиент

Слой настроек/логирования + LLM-сервис, не зависящий от Telegram. Здесь закладывается архитектурный фундамент.

### Задача 1.1. Конфигурация (`Settings`) и логирование

- **Статус:** Done
- **Приоритет:** high
- **Объём:** M
- **Зависит от:** Задача 1.2 из `sprints/00-bootstrap.md`
- **Связанные документы:** `_docs/architecture.md` §3.2–§3.3, `_docs/stack.md` §4–§5, `_docs/instructions.md` §5–§6, `_docs/testing.md` §3.1, `_docs/roadmap.md` «Этап 2».
- **Затрагиваемые файлы:** `app/config.py`, `app/logging_config.py`, `tests/test_config.py`, `tests/test_logging_config.py`.

#### Описание

1. Реализовать `app/config.py`:
   - Класс `Settings(BaseSettings)` на `pydantic-settings`.
   - Поля: `telegram_bot_token: SecretStr`, `ollama_base_url: str`, `ollama_default_model: str`, `ollama_available_models: list[str]` (парсинг из CSV), `ollama_timeout: int`, `system_prompt: str`, `log_level: str`, `log_file: str`.
   - `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")`.
   - Валидатор: `ollama_default_model` должен присутствовать в `ollama_available_models`.
2. Реализовать `app/logging_config.py`:
   - Функция `setup_logging(settings: Settings) -> None`.
   - `logging.config.dictConfig` с двумя handler'ами (`StreamHandler` + `RotatingFileHandler` с `maxBytes=1_000_000`, `backupCount=3`).
   - Формат: `%(asctime)s | %(levelname)s | %(name)s | %(message)s`.
   - Автосоздание каталога для файла логов.
   - Никаких секретов в логах.
3. Тесты `tests/test_config.py` (≥ 4 сценария): загрузка из env, парсинг CSV, отсутствие токена → `ValidationError`, default-model вне списка → `ValidationError`.

#### Definition of Done

- [x] `pytest tests/test_config.py -q` зелёный, минимум 4 теста.
- [x] `python -c "from app.config import Settings; print(Settings().ollama_default_model)"` при заполненном `.env` выводит имя модели.
- [x] `setup_logging` не требует `app/` на диске: при запуске в tmp-каталоге создаёт файл логов.
- [x] В логах при `LOG_LEVEL=DEBUG` не печатается `TELEGRAM_BOT_TOKEN`.

---

### Задача 1.2. LLM-клиент (`OllamaClient`) и иерархия исключений

- **Статус:** Done
- **Приоритет:** high
- **Объём:** L
- **Зависит от:** Задача 1.1
- **Связанные документы:** `_docs/architecture.md` §3.4, §5, `_docs/stack.md` §3, `_docs/instructions.md` §3–§4, `_docs/testing.md` §3.2, `_docs/roadmap.md` «Этап 3».
- **Затрагиваемые файлы:** `app/services/llm.py`, `tests/services/test_llm_client.py`.

#### Описание

1. В `app/services/llm.py`:
   - Иерархия исключений: `LLMError` → `LLMTimeout`, `LLMUnavailable`, `LLMBadResponse`.
   - Класс `OllamaClient`:
     - Конструктор: `base_url`, `timeout`, опциональный `client: ollama.AsyncClient | None` (для тестов).
     - `async generate(prompt, *, model, system_prompt) -> str`.
     - `async close()` — graceful shutdown HTTP-сессии.
   - Реализация на `ollama.AsyncClient`.
   - Маппинг ошибок: `httpx.TimeoutException` / `asyncio.TimeoutError` → `LLMTimeout`; `httpx.ConnectError` → `LLMUnavailable`; `ollama.ResponseError` 404 → `LLMBadResponse("модель не найдена")`; прочие 4xx/5xx → `LLMBadResponse`.
   - Логирование каждого вызова: INFO с полями `model`, `len_in`, `len_out`, `dur_ms`, `status`.
2. Тесты `tests/services/test_llm_client.py` (≥ 6 сценариев).

#### Definition of Done

- [x] `pytest tests/services/test_llm_client.py -q` зелёный, минимум 6 тестов.
- [x] `OllamaClient` не импортирует `aiogram` (проверено `grep`).
- [x] Весь I/O — `async`, никаких `time.sleep` / `requests`.
- [x] Логирование пишет строку с `model`, `len_in`, `len_out`, `dur_ms` на каждый успешный вызов.
- [x] Исключения экспортируются из `app.services.llm` (через `__all__`).

---

### Задача 1.3. `UserSettingsRegistry` для модели и системного промпта

- **Статус:** Done
- **Приоритет:** high
- **Объём:** S
- **Зависит от:** Задача 1.2
- **Связанные документы:** `_docs/architecture.md` §3.5, `_docs/commands.md` §«/model», §«/prompt», `_docs/testing.md` §3.3, `_docs/roadmap.md` «Этап 4».
- **Затрагиваемые файлы:** `app/services/model_registry.py`, `tests/services/test_model_registry.py`.

#### Описание

1. В `app/services/model_registry.py`:
   - Класс `UserSettingsRegistry` с методами `get_model`, `set_model`, `get_prompt`, `set_prompt`, `reset_prompt` (общий `reset` — задел на будущее, см. `_docs/current-state.md` §2.1).
   - Конструктор: `default_model`, `default_prompt`.
   - Состояние **только in-memory** (CON-1, CON-3 из `_docs/requirements.md`).
2. Тесты `tests/services/test_model_registry.py` (≥ 4 сценария): default без `set`, корректность `set` → `get`, `reset` → default, изоляция между `user_id`.

#### Definition of Done

- [x] `pytest tests/services/test_model_registry.py -q` зелёный, минимум 4 теста.
- [x] Никаких обращений к файловой системе / сети.
- [x] Публичный API задокументирован docstring'ами.

---

## 5. Этап 2. Telegram-бот: команды и сообщения

Сборка приложения: entrypoint + handlers + middleware + error handler. Пользовательский путь от `/start` до произвольного текста.

### Задача 2.1. Entrypoint и команды `/start`, `/help`

- **Статус:** Done
- **Приоритет:** high
- **Объём:** M
- **Зависит от:** Задача 1.3
- **Связанные документы:** `_docs/architecture.md` §3.1, §3.6, `_docs/commands.md` §«/start», §«/help», §«BotFather / setMyCommands», `_docs/stack.md` §2, `_docs/roadmap.md` «Этап 5».
- **Затрагиваемые файлы:** `app/main.py`, `app/__main__.py`, `app/handlers/commands.py`, `tests/handlers/test_commands.py`, `tests/test_main.py`.

#### Описание

1. `app/main.py`: `async def main()` собирает `Bot`, `Dispatcher`, `OllamaClient`, `UserSettingsRegistry`, прокидывает в `dp[...]`, регистрирует роутеры, вызывает `bot.set_my_commands(...)` (5 команд), запускает polling, в `finally` закрывает клиенты.
2. `app/__main__.py`: `asyncio.run(main())`.
3. `app/handlers/commands.py`: роутер `commands`, хендлеры `/start` (приветствие из `_docs/commands.md`) и `/help` (справка с текущей моделью + срез системного промпта).
4. Тесты: `/start` → текст содержит «Привет»; `/help` → содержит имя текущей модели; smoke-тест `main()` со всеми моками доходит до `Bot started`.

#### Definition of Done

- [x] `python -m app` запускается, в консольном логе строка «Bot started».
- [x] В Telegram `/start` возвращает приветствие со списком команд.
- [x] В Telegram `/help` возвращает расширенную справку.
- [x] `pytest tests/handlers/test_commands.py -q` зелёный, минимум 2 теста.
- [x] Бот корректно завершается по Ctrl+C, без `Unclosed client session`.
- [x] В BotFather UI после запуска видны 5 команд.

---

### Задача 2.2. Основной обработчик текста → LLM

- **Статус:** Done
- **Приоритет:** high
- **Объём:** L
- **Зависит от:** Задача 2.1
- **Связанные документы:** `_docs/architecture.md` §4–§5, `_docs/commands.md` §«Произвольный текст», §«Ограничения ввода», `_docs/testing.md` §3.4, `_docs/roadmap.md` «Этап 6».
- **Затрагиваемые файлы:** `app/handlers/messages.py`, `app/utils/text.py`, `app/main.py`, `tests/handlers/test_messages.py`, `tests/test_utils_text.py`.

#### Описание

1. `app/handlers/messages.py`:
   - Роутер `messages`, фильтр `F.text & ~F.text.startswith("/")`.
   - Алгоритм: TYPING → берём `model` и `system_prompt` из registry → проверяем длину (`> 4000` → подсказка) → `llm_client.generate(...)` → `message.answer(response)` (с разбивкой `> 4096`).
   - Маппинг исключений: `LLMTimeout` → «Модель слишком долго отвечает», `LLMUnavailable` → «LLM сейчас недоступна», `LLMBadResponse` («не найдена») → «Модель не найдена, выберите через /models», прочее `LLMBadResponse` → текст исключения, `LLMError` → общий «Произошла ошибка при обращении к LLM».
2. `app/utils/text.py::split_long_message(text, limit=4096) -> list[str]` — разбивка по границам строк/пробелов.
3. Подключить роутер в `app/main.py` после `commands_handlers.router`.
4. Тесты `tests/handlers/test_messages.py` (≥ 5 сценариев) + тесты `tests/test_utils_text.py`.

#### Definition of Done

- [x] `pytest tests/handlers/ -q` зелёный, минимум 5 тестов в `test_messages.py`.
- [x] В Telegram произвольный текст возвращает ответ от LLM (ручная проверка).
- [x] При остановленной Ollama бот **не падает**, пользователь видит «LLM сейчас недоступна…», лог содержит `ERROR`.
- [x] Индикатор «печатает…» виден в чате.
- [x] В логе на каждое сообщение есть запись с `user`, `chat`, `model`, `dur_ms`.

---

### Задача 2.3. Команды `/models`, `/model <name>`, `/prompt [text]`

- **Статус:** Done
- **Приоритет:** high
- **Объём:** M
- **Зависит от:** Задача 2.2
- **Связанные документы:** `_docs/commands.md` §«/models», §«/model», §«/prompt», `_docs/testing.md` §3.4, `_docs/roadmap.md` «Этап 7».
- **Затрагиваемые файлы:** `app/handlers/commands.py`, `tests/handlers/test_commands.py`.

#### Описание

В `app/handlers/commands.py` добавить:

- `/models` — список из `settings.ollama_available_models` с маркером активной модели + подсказка `/model <имя>`.
- `/model <name>`: без аргумента → подсказка-использование; имя не из списка → «Модель не найдена. Доступно: …»; иначе → `registry.set_model(...)` + ответ.
- `/prompt [text]`: пусто → `registry.reset_prompt(user_id)` + сообщение о сбросе; непусто → `registry.set_prompt(user_id, text)` + сообщение об обновлении.

Парсинг аргументов через `CommandObject.args`. Тесты — минимум 6 дополнительных.

#### Definition of Done

- [x] `pytest tests/handlers/test_commands.py -q` зелёный, минимум 6 доп. тестов.
- [x] В Telegram все три команды работают, переключение модели видно в логе и применяется к следующему запросу к LLM.
- [x] Невалидные аргументы (`/model`, `/model qwe rty`) не валят бот.

---

### Задача 2.4. Middleware логирования и глобальный error handler

- **Статус:** Done
- **Приоритет:** high
- **Объём:** M
- **Зависит от:** Задача 2.3
- **Связанные документы:** `_docs/architecture.md` §3.7, §5, `_docs/instructions.md` §4–§5, `_docs/roadmap.md` «Этап 8».
- **Затрагиваемые файлы:** `app/middlewares/logging_mw.py`, `app/handlers/errors.py`, `app/main.py`, `tests/test_middleware_logging.py`, `tests/handlers/test_errors.py`.

#### Описание

1. `app/middlewares/logging_mw.py`: `LoggingMiddleware(BaseMiddleware)` — INFO-запись `user/chat/type/dur_ms/status` без контента сообщения. Регистрируется на `dp.update.middleware(...)`.
2. `app/handlers/errors.py`: глобальный error handler через `@router.errors(...)` (aiogram 3); `logger.exception(...)` со stacktrace; пытается отправить нейтральное сообщение «Что-то пошло не так. Попробуйте ещё раз.»; не пробрасывает исключение дальше.
3. Зарегистрировать роутер `errors` и middleware в `app/main.py`.
4. Тесты middleware (мок-handler логирует) и error handler (намеренно падающий хендлер не валит polling).

#### Definition of Done

- [x] Намеренно падающий хендлер приводит к: записи `EXCEPTION` со stacktrace; нейтральному сообщению пользователю; продолжению polling.
- [x] На каждый апдейт в лог-файле есть ровно одна INFO-строка от middleware с полями `user`, `chat`, `type`, `dur_ms`, `status`.
- [x] Контент сообщения в логе middleware **не появляется**.
- [x] `pytest -q` зелёный.

---

## 6. Этап 3. Документация и приёмка MVP

Финальная сборка: README, чистка, прогон чек-листа.

### Задача 3.1. README, финальная полировка и чек-лист приёмки MVP

- **Статус:** Done
- **Приоритет:** high
- **Объём:** M
- **Зависит от:** Задача 2.4
- **Связанные документы:** `_docs/mvp.md` §5, `_docs/instructions.md` §1, `_docs/testing.md` §5–§6, `_docs/roadmap.md` «Этап 9».
- **Затрагиваемые файлы:** `README.md`, `_board/progress.txt`.

#### Описание

1. Заполнить `README.md` разделами: «О проекте», «Требования», «Установка», «Настройка», «Запуск», «Команды бота», «Тесты», «Ограничения MVP».
2. Проверить `.gitignore` — `git status` не показывает `.env`, `logs/`, `.venv/`, `__pycache__/`.
3. Прогнать `pytest -q` (зелёное) и при наличии `pytest-cov` — `pytest --cov=app`.
4. Прогнать чек-лист `_docs/mvp.md` §5 — отметить все 10 пунктов.
5. Убедиться, что в истории коммитов нет реального токена (`git log -p | grep TELEGRAM_BOT_TOKEN=`).

#### Definition of Done

- [x] `README.md` содержит все указанные разделы, инструкция воспроизводима на чистой машине.
- [x] `git status` чист.
- [x] `pytest -q` зелёный.
- [x] Все 10 пунктов `_docs/mvp.md` §5 отмечены (см. `_board/progress.txt`).
- [x] В репозитории нет реального `.env` и токена в истории.

---

## 7. Риски и смягчение

| # | Риск                                              | Смягчение                                                                 |
|---|---------------------------------------------------|---------------------------------------------------------------------------|
| 1 | Имя тега модели в Ollama не совпадает с ТЗ         | `OLLAMA_AVAILABLE_MODELS` через `.env`, проверка `ollama list`            |
| 2 | aiogram 3 не имеет ожидаемого API (DI / Errors)    | Закреплено в `requirements.txt` (`aiogram>=3.4,<4`), тестируется моками   |
| 3 | Долгий ответ LLM воспринимается как зависание      | Индикатор `ChatAction.TYPING` + сообщение об ошибке при `LLMTimeout`      |
| 4 | Утечка токена в логи                               | `LoggingMiddleware` не пишет контент; `OllamaClient` логирует только метрики |

## 8. Сводная таблица задач спринта

| #   | Задача                                              | Приоритет | Объём | Статус | Зависит от                       |
|-----|-----------------------------------------------------|:---------:|:-----:|:------:|:--------------------------------:|
| 1.1 | Конфигурация (`Settings`) и логирование             | high      | M     | Done   | Задача 1.2 (sprint 00)           |
| 1.2 | LLM-клиент (`OllamaClient`) и иерархия исключений   | high      | L     | Done   | Задача 1.1                       |
| 1.3 | `UserSettingsRegistry` для модели и промпта         | high      | S     | Done   | Задача 1.2                       |
| 2.1 | Entrypoint и команды `/start`, `/help`              | high      | M     | Done   | Задача 1.3                       |
| 2.2 | Основной обработчик текста → LLM                    | high      | L     | Done   | Задача 2.1                       |
| 2.3 | Команды `/models`, `/model <name>`, `/prompt [text]`| high      | M     | Done   | Задача 2.2                       |
| 2.4 | Middleware логирования + глобальный error handler   | high      | M     | Done   | Задача 2.3                       |
| 3.1 | README, финальная полировка, чек-лист MVP           | high      | M     | Done   | Задача 2.4                       |

## 9. История изменений спринта

- **2026-04-25** — закрыты задачи 1.1, 1.2, 1.3 (исходные коммиты: `feat(config): add Settings and logging`, `feat(llm): add OllamaClient and LLMError hierarchy`, `feat(registry): add UserSettingsRegistry for per-user model and prompt`).
- **2026-04-25** — закрыта задача 2.1 (`feat(handlers): add entrypoint, /start and /help commands`).
- **2026-04-26** — закрыты задачи 2.2, 2.3, 2.4 (`feat(handlers): add text handler with LLM call and error mapping`, `feat(handlers): add /models, /model, /prompt commands`, `feat(middleware+errors): add logging middleware and global error handler`).
- **2026-04-26** — закрыта задача 3.1 (`docs(readme): add installation, commands, tests and MVP limitations`); MVP принят, чек-лист зафиксирован в `_board/progress.txt`.
- **2026-04-26** — спринт оформлен задним числом в формат `sprints/01-mvp.md` (после реструктуризации `_board/`).
