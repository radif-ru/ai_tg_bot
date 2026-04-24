"""Тесты `LoggingMiddleware`."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.middlewares.logging_mw import LoggingMiddleware


def _make_update(user_id: int = 111, chat_id: int = 222, *, text: str = "") -> MagicMock:
    event = MagicMock()
    event.__class__ = type("Update", (), {})
    event.from_user = None  # на Update.from_user отсутствует
    event.chat = None
    event.message = MagicMock()
    event.message.from_user.id = user_id
    event.message.chat.id = chat_id
    event.message.text = text
    event.edited_message = None
    event.channel_post = None
    event.callback_query = None
    event.inline_query = None
    return event


async def test_middleware_logs_ok_on_success(caplog: pytest.LogCaptureFixture) -> None:
    mw = LoggingMiddleware()
    handler = AsyncMock(return_value="ok")
    event = _make_update()

    caplog.set_level(logging.INFO, logger="app.middlewares.logging_mw")
    result = await mw(handler, event, {})

    assert result == "ok"
    assert any(
        "user=111" in rec.message
        and "chat=222" in rec.message
        and "status=ok" in rec.message
        and "dur_ms=" in rec.message
        for rec in caplog.records
    )


async def test_middleware_logs_error_on_exception_and_reraises(
    caplog: pytest.LogCaptureFixture,
) -> None:
    mw = LoggingMiddleware()
    handler = AsyncMock(side_effect=RuntimeError("boom"))
    event = _make_update()

    caplog.set_level(logging.INFO, logger="app.middlewares.logging_mw")
    with pytest.raises(RuntimeError):
        await mw(handler, event, {})

    assert any("status=error" in rec.message for rec in caplog.records)


async def test_middleware_does_not_log_message_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    mw = LoggingMiddleware()
    handler = AsyncMock()
    secret = "SECRET-CONTENT-XYZ-9999"
    event = _make_update(text=secret)

    caplog.set_level(logging.INFO, logger="app.middlewares.logging_mw")
    await mw(handler, event, {})

    for rec in caplog.records:
        assert secret not in rec.message


async def test_middleware_works_for_message_event() -> None:
    """Middleware должен переживать события, где нет вложенной структуры Update."""
    mw = LoggingMiddleware()
    handler = AsyncMock(return_value=None)
    event = MagicMock()
    event.from_user.id = 10
    event.chat.id = 20
    event.message = None

    await mw(handler, event, {})  # не должно упасть
    handler.assert_awaited_once()
