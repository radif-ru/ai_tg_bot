# Документация проекта

Telegram-бот с локальной LLM (Ollama + aiogram). Документы описывают ТЗ, архитектуру и план работ.

## Навигация

- [`mvp.md`](./mvp.md) — scope MVP и критерии приёмки.
- [`requirements.md`](./requirements.md) — формализованные функциональные/нефункциональные требования, ограничения и трассировка.
- [`architecture.md`](./architecture.md) — архитектура системы, компоненты, поток данных, обработка ошибок.
- [`stack.md`](./stack.md) — технологический стек, версии, зависимости, переменные окружения.
- [`project-structure.md`](./project-structure.md) — структура репозитория и назначение модулей.
- [`commands.md`](./commands.md) — спецификация команд бота и поведения.
- [`testing.md`](./testing.md) — стратегия и категории тестов.
- [`instructions.md`](./instructions.md) — правила разработки (в т.ч. LLM-driven требование ТЗ).
- [`roadmap.md`](./roadmap.md) — план реализации по этапам.

## Порядок чтения

1. Новичок на проекте → `mvp.md` → `architecture.md` → `project-structure.md` → `roadmap.md`.
2. Перед написанием кода → `instructions.md` + `stack.md` + `commands.md`.
3. При реализации фичи/бага → `requirements.md` (найти требование) → `testing.md` (как покрывать).

## Источник истины

Исходное ТЗ — `../RAW.md`. Все документы в `docs/` — его формализация. При расхождении приоритет у `RAW.md`, далее — у `requirements.md`.
