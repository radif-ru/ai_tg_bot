# Стратегия тестирования

## 1. Цели

- Гарантировать соответствие требованиям из `requirements.md` (столбец «T» в таблице верификации).
- Ловить регрессии при доработках.
- Проверять обработку ошибок LLM-слоя.
- Выполняться быстро (< 5 сек на MVP) и без внешних зависимостей (без реального Telegram, без реальной Ollama).

## 2. Инструменты

- **pytest** — раннер.
- **pytest-asyncio** — поддержка `async def test_...`.
- **pytest-mock** — фикстура `mocker`.
- **respx** или `httpx.MockTransport` — если `OllamaClient` построен на `httpx`.
- **coverage / pytest-cov** — отчёт покрытия (желательно ≥ 70% на MVP).

Конфиг в `pyproject.toml` (или `pytest.ini`):

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-ra -q"
```

## 3. Категории тестов

### 3.1 Unit — конфигурация (`tests/test_config.py`)
- `Settings` корректно читает `.env`-подобный ввод (через `_env_file` или monkeypatch `os.environ`).
- Отсутствие обязательного поля (`TELEGRAM_BOT_TOKEN`) → `ValidationError`.
- `OLLAMA_AVAILABLE_MODELS` парсится как список из CSV.

### 3.2 Unit — LLM-клиент (`tests/services/test_llm_client.py`)

Обязательные сценарии:
- **Успех**: mock возвращает JSON с ответом → `generate` отдаёт строку.
- **Таймаут**: mock кидает `httpx.TimeoutException` → `generate` кидает `LLMTimeout`.
- **Недоступность**: mock кидает `httpx.ConnectError` → `generate` кидает `LLMUnavailable`.
- **HTTP 404 (модель не найдена)** → `LLMError` с соответствующим сообщением.
- **HTTP 5xx** → `LLMError`.
- **Пустой ответ модели** → `LLMError` или пустая строка (выбрать стратегию и закрепить тестом).

Пример (псевдокод):

```python
@pytest.mark.asyncio
async def test_generate_success(mocker):
    client = OllamaClient(base_url="http://x", timeout=5)
    mocker.patch.object(client._http, "post", return_value=_ok({"response": "hi"}))
    assert await client.generate("ping", model="m", system_prompt=None) == "hi"

@pytest.mark.asyncio
async def test_generate_timeout(mocker):
    client = OllamaClient(base_url="http://x", timeout=0.01)
    mocker.patch.object(client._http, "post", side_effect=httpx.TimeoutException("t"))
    with pytest.raises(LLMTimeout):
        await client.generate("ping", model="m", system_prompt=None)
```

### 3.3 Unit — registry (`tests/services/test_model_registry.py`)
- `get(user_id)` без записи → default.
- `set(user_id, model)` → последующий `get(user_id)` возвращает модель.
- `reset(user_id)` → снова default.

### 3.4 Unit — handlers (`tests/handlers/`)

Стратегия: **не поднимать реальный aiogram Dispatcher**, вызывать handler-функцию напрямую с мок-объектом `Message`.

- `test_commands.py`:
  - `/start` → `message.answer` вызван с текстом, содержащим «Привет».
  - `/models` → ответ содержит имена моделей из `Settings`.
  - `/model qwen3.5:0.8b` → `registry.set` вызван с корректными аргументами, пользователю отправлен успех.
  - `/model unknown` → ответ содержит «не найдена», `registry.set` **не** вызывался.
  - `/prompt текст` → `prompt_registry.set` вызван.
  - `/prompt` (без аргумента) → `prompt_registry.reset` вызван.

- `test_messages.py`:
  - Успешный путь: `llm_client.generate` мокается → возвращает «ответ» → `message.answer("ответ")`.
  - `LLMUnavailable` → `message.answer(<сообщение об ошибке>)`, `logger.error` вызван.
  - `LLMTimeout` → ветка с сообщением о таймауте.
  - Длинный ответ (> 4096) → вызывается разбивка (несколько `answer`).

Пример мок-фабрики `Message`:

```python
@pytest.fixture
def fake_message(mocker):
    m = mocker.MagicMock()
    m.from_user.id = 111
    m.chat.id = 111
    m.text = "hello"
    m.answer = mocker.AsyncMock()
    m.bot.send_chat_action = mocker.AsyncMock()
    return m
```

### 3.5 Smoke / e2e (опционально, вручную)

Не автоматизируем в MVP, но держим чек-лист:
- Реальный Telegram + реальная Ollama.
- Отправить `/start`, произвольный текст, `/model ...`, остановить Ollama, снова отправить текст → получить сообщение об ошибке.

## 4. Моки внешних систем

| Система     | Как мокаем                                                                 |
|-------------|----------------------------------------------------------------------------|
| Telegram    | Не трогаем реальный API; `Message`/`Bot` — `MagicMock`/`AsyncMock`.        |
| Ollama HTTP | `httpx.MockTransport` или `respx`; для `ollama.AsyncClient` — `mocker.patch.object(client, "generate", ...)`. |
| Файлы логов | Временный каталог через `tmp_path`; не проверяем содержимое в CI, только что пишет. |

## 5. Покрытие

- Цель на MVP: **70%+** по пакету `app/` (без `__main__.py` и `main.py`).
- Модули `services/` и `handlers/` — **≥ 85%**.

## 6. Запуск

```bash
pytest -q
pytest -q --cov=app --cov-report=term-missing   # при установленном pytest-cov
```

## 7. CI (опционально)

Простой workflow GitHub Actions: `actions/setup-python@v5` → `pip install -r requirements-dev.txt` → `pytest -q`. За рамками MVP, но структура тестов должна это позволять (никаких сетевых запросов в unit-тестах).
