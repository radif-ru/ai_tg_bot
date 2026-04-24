"""Middleware логирования каждого апдейта.

Пишет одну INFO-запись на апдейт с полями user/chat/type/dur_ms/status.
Контент сообщений (текст) в лог НЕ попадает — соблюдается приватность.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

_logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Логирует служебные метаданные каждого апдейта."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        started = time.monotonic()
        status = "ok"
        user_id = _extract_user_id(event)
        chat_id = _extract_chat_id(event)
        update_type = _extract_update_type(event)
        try:
            return await handler(event, data)
        except Exception:
            status = "error"
            raise
        finally:
            dur_ms = int((time.monotonic() - started) * 1000)
            _logger.info(
                "update user=%s chat=%s type=%s dur_ms=%d status=%s",
                user_id,
                chat_id,
                update_type,
                dur_ms,
                status,
            )


def _extract_user_id(event: Any) -> int | None:
    """Достать id пользователя из Update/Message/CallbackQuery без обращения к тексту."""
    from_user = getattr(event, "from_user", None)
    if from_user is not None:
        return getattr(from_user, "id", None)
    for attr in ("message", "edited_message", "callback_query", "inline_query"):
        inner = getattr(event, attr, None)
        if inner is None:
            continue
        inner_from = getattr(inner, "from_user", None)
        if inner_from is not None:
            return getattr(inner_from, "id", None)
    return None


def _extract_chat_id(event: Any) -> int | None:
    """Достать id чата из Update/Message без обращения к тексту."""
    chat = getattr(event, "chat", None)
    if chat is not None:
        return getattr(chat, "id", None)
    for attr in ("message", "edited_message", "channel_post"):
        inner = getattr(event, attr, None)
        if inner is None:
            continue
        inner_chat = getattr(inner, "chat", None)
        if inner_chat is not None:
            return getattr(inner_chat, "id", None)
    return None


def _extract_update_type(event: Any) -> str:
    """Вернуть тип апдейта: для Update — имя первого непустого поля, иначе имя класса."""
    if type(event).__name__ == "Update":
        for attr in (
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
            "callback_query",
            "inline_query",
            "chosen_inline_result",
            "my_chat_member",
            "chat_member",
        ):
            if getattr(event, attr, None) is not None:
                return attr
    return type(event).__name__
