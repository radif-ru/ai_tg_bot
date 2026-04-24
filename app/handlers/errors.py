"""Глобальный error handler: ловит исключения, которые не обработал ни один хендлер.

Пишет stacktrace в лог и отправляет пользователю нейтральное сообщение.
Возвращает True, чтобы aiogram не пробрасывал исключение дальше и polling
не останавливался.
"""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import ErrorEvent

router = Router(name="errors")

_logger = logging.getLogger(__name__)

_USER_FALLBACK_MESSAGE = "Что-то пошло не так. Попробуйте ещё раз."


@router.errors()
async def on_error(event: ErrorEvent) -> bool:
    """Обработать любое необработанное исключение хендлера.

    - Логирует stacktrace через `logger.exception`.
    - Пытается отправить пользователю нейтральное сообщение, если доступен `message`.
    - Возвращает `True` — исключение считается обработанным, polling продолжается.
    """
    _logger.error(
        "Unhandled error: %s",
        event.exception,
        exc_info=event.exception,
    )

    update = event.update
    message = getattr(update, "message", None)
    if message is not None:
        try:
            await message.answer(_USER_FALLBACK_MESSAGE)
        except Exception:
            _logger.exception("Failed to notify user about the error")
    return True
