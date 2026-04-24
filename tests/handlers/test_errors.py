"""Тесты глобального error-хендлера."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.handlers.errors import on_error


def _make_event(exception: Exception, *, with_message: bool = True) -> MagicMock:
    event = MagicMock()
    event.exception = exception
    event.update = MagicMock()
    if with_message:
        event.update.message = MagicMock()
        event.update.message.answer = AsyncMock()
    else:
        event.update.message = None
    return event


async def test_error_handler_logs_exception_and_notifies_user(
    caplog: pytest.LogCaptureFixture,
) -> None:
    event = _make_event(RuntimeError("boom"))
    caplog.set_level(logging.ERROR, logger="app.handlers.errors")

    result = await on_error(event)

    assert result is True
    event.update.message.answer.assert_awaited_once()
    text = event.update.message.answer.call_args.args[0]
    assert "Что-то пошло не так" in text
    # stacktrace должен уйти в лог
    assert any("boom" in rec.message or rec.exc_info for rec in caplog.records)


async def test_error_handler_without_message_still_returns_true(
    caplog: pytest.LogCaptureFixture,
) -> None:
    event = _make_event(RuntimeError("boom"), with_message=False)
    caplog.set_level(logging.ERROR, logger="app.handlers.errors")

    result = await on_error(event)

    assert result is True


async def test_error_handler_survives_failure_to_notify(
    caplog: pytest.LogCaptureFixture,
) -> None:
    event = _make_event(RuntimeError("boom"))
    event.update.message.answer = AsyncMock(side_effect=RuntimeError("tg-failure"))
    caplog.set_level(logging.ERROR, logger="app.handlers.errors")

    result = await on_error(event)

    # Даже если отправка сообщения провалилась — handler не должен падать.
    assert result is True
