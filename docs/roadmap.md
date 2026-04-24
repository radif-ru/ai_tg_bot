# План разработки (Roadmap)

Этапы реализации проекта от пустого репозитория до готового MVP. Каждый этап завершается зелёным `pytest` и ручной проверкой.

## Этап 0. Подготовка окружения (0.5ч)

- [ ] Установить Python 3.11+.
- [ ] Установить Ollama, запустить сервис.
- [ ] `ollama pull qwen3.5:0.8b` и `ollama pull deepseek-r1:1.5b` (уточнить точные теги).
- [ ] Создать Telegram-бота через `@BotFather`, сохранить токен.
- [ ] Создать `venv`, базовый `requirements.txt`.

**Готово когда**: `ollama list` показывает нужные модели; `python -V` ≥ 3.11; токен есть.

## Этап 1. Скелет репозитория (0.5ч)

- [ ] `.gitignore` (см. `project-structure.md`).
- [ ] `.env.example` с полным набором переменных (см. `stack.md`).
- [ ] `requirements.txt`: aiogram, ollama, pydantic-settings, pytest, pytest-asyncio, pytest-mock.
- [ ] Пустые пакеты `app/`, `app/handlers/`, `app/services/`, `app/middlewares/`, `tests/` с `__init__.py`.
- [ ] `README.md` — заготовка.

**Готово когда**: структура соответствует `project-structure.md`, `pip install -r requirements.txt` отрабатывает.

## Этап 2. Конфиг и логирование (1ч)

- [ ] `app/config.py` — `Settings` на `pydantic-settings`.
- [ ] `app/logging_config.py` — `setup_logging(settings)` с консолью + файлом (RotatingFileHandler).
- [ ] `tests/test_config.py` — минимум 2 теста: корректная загрузка и ошибка на пустом токене.

**Готово когда**: `pytest` зелёный; запуск `python -c "from app.config import Settings; print(Settings())"` (с `.env`) выводит настройки.

## Этап 3. LLM-клиент (1.5ч)

- [ ] `app/services/llm.py`: `OllamaClient`, `LLMError`, `LLMTimeout`, `LLMUnavailable`.
- [ ] Метод `generate(prompt, model, system_prompt)`.
- [ ] Конструктор принимает `base_url`, `timeout`, async HTTP-клиент.
- [ ] `tests/services/test_llm_client.py`: успех, таймаут, недоступность, 404, 5xx.

**Готово когда**: юнит-тесты зелёные, клиент не зависит от aiogram.

## Этап 4. Model registry (0.5ч)

- [ ] `app/services/model_registry.py`: `ModelRegistry` с методами `get/set/reset`, thread-safe (`asyncio.Lock` если нужно).
- [ ] Аналогично `PromptRegistry` или общий `UserSettingsRegistry`.
- [ ] Тесты в `tests/services/test_model_registry.py`.

**Готово когда**: тесты зелёные.

## Этап 5. Entrypoint + /start (1ч)

- [ ] `app/main.py`: `async def main()`, создание `Bot`, `Dispatcher`, подключение роутеров, `set_my_commands`, запуск polling.
- [ ] `app/__main__.py`: `asyncio.run(main())`.
- [ ] `app/handlers/commands.py`: `/start`, `/help`.
- [ ] Регистрация зависимостей в `dp["settings"]`, `dp["llm_client"]`, `dp["model_registry"]`, `dp["prompt_registry"]`.
- [ ] Ручная проверка в Telegram: бот отвечает на `/start`.

**Готово когда**: `python -m app` стартует, логи показывают «Bot started», в Telegram `/start` возвращает приветствие.

## Этап 6. Основной обработчик текста (1ч)

- [ ] `app/handlers/messages.py`: handler `F.text & ~F.text.startswith("/")`.
- [ ] Индикатор «печатает…».
- [ ] Вызов `OllamaClient.generate` с моделью/промптом из registry.
- [ ] Обработка `LLMError*` с человеческими ответами.
- [ ] Тесты `tests/handlers/test_messages.py`: успех, timeout, unavailable.

**Готово когда**: в Telegram произвольный текст возвращает ответ от LLM; отключив `ollama serve`, бот отвечает «LLM недоступна».

## Этап 7. Команды /models, /model, /prompt (1ч)

- [ ] Реализация в `app/handlers/commands.py`.
- [ ] Валидация имени модели по `Settings.OLLAMA_AVAILABLE_MODELS`.
- [ ] Тесты `tests/handlers/test_commands.py`.

**Готово когда**: переключение модели видно в логах (`model=...`) и влияет на ответ.

## Этап 8. Middleware логирования + глобальный error handler (0.5ч)

- [ ] `app/middlewares/logging_mw.py`: логирует каждый update (user, chat, тип, длительность).
- [ ] `app/handlers/errors.py`: глобальный `@dp.errors` — ловит всё, что не поймали handlers, отвечает нейтральным сообщением, пишет `logger.exception`.

**Готово когда**: необработанное исключение в handler не приводит к падению polling, лог содержит stacktrace, пользователь получает сообщение.

## Этап 9. Полировка и README (1ч)

- [ ] `README.md`: «Установка», «Настройка», «Запуск», «Команды», «Тесты».
- [ ] Проверить `.gitignore` — нет реального `.env` в `git status`.
- [ ] `pytest -q` и `pytest --cov=app` — покрытие ≥ 70%.
- [ ] Прогон чек-листа из `mvp.md` § «Критерии приёмки».

**Готово когда**: все критерии приёмки MVP выполнены.

## Этап 10 (опционально). Дополнения

- [ ] `/reset` команда.
- [ ] Простой throttling middleware.
- [ ] Dockerfile + docker-compose (Ollama + бот).
- [ ] GitHub Actions CI: lint + test.
- [ ] Прогресс-сообщение со стримингом токенов (если `ollama` поддерживает stream).

## Ориентировочный тайминг

- Этапы 0–9: **~7–8 часов** чистого времени.
- Этап 10: +2–4 часа.

## Последовательность закрытия требований

| Этап | Закрывает требования |
|------|----------------------|
| 2    | FR-10, FR-11, NFR-9  |
| 3    | FR-2 (частично), NFR-3 (частично) |
| 4    | FR-6 (подготовка)    |
| 5    | FR-4, FR-8, NFR-1, NFR-10 |
| 6    | FR-1, FR-2, FR-3, FR-9, NFR-2, NFR-3, NFR-7 |
| 7    | FR-5, FR-6, FR-7     |
| 8    | NFR-3 (финал), FR-9 (финал) |
| 9    | FR-12, NFR-4         |
