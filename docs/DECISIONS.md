# Architectural Decision Records (ADR)

## ADR 001: Settings Hierarchy via django-environ
- **Context:** Applications need separate configurations across development, testing, and production without leaking secrets.
- **Decision:** Split settings into `config/settings/{base,dev,prod,test}.py`. All sensitive values and environment overrides are loaded from `.env` via `django-environ`.
- **Consequences:** Safe defaults in base; development uses SQLite and debug tools; test uses in-memory SQLite and MD5 password hashing; secrets are never committed.

## ADR 002: Custom User Model Before Initial Migration
- **Context:** Django strongly recommends defining a custom `User` model before creating the first migration to prevent future schema refactoring difficulties.
- **Decision:** Create `apps.accounts.models.User` subclassing `AbstractUser` with explicit `role` choices, `is_approved` boolean flag, and required unique `email`. Configure `AUTH_USER_MODEL = 'accounts.User'` in `base.py` before executing `makemigrations`.
- **Consequences:** Eliminates risks of migration collisions with Django's default auth user model and enables multi-role portal workflows (Trainee, Trainer, Admin).

## ADR 003: Abstract TimeStampedModel in Core
- **Context:** Multiple future domain models will require tracking creation and update timestamps.
- **Decision:** Implement an abstract `TimeStampedModel` in `apps.core.models` using `created_at` (`auto_now_add=True`) and `updated_at` (`auto_now=True`).
- **Consequences:** Standardizes timestamp handling across future apps without redundant column definitions.

## ADR 004: Strict Code Quality & Limits
- **Context:** Project brief enforces strict quality constraints: max 25 lines per function, max 250 lines per module, type hints on all functions, one-line docstrings stating why, no magic strings.
- **Decision:** Use Ruff for automated linting and formatting. Define enums (`UserRole`) for string constants.
- **Consequences:** Clean, maintainable, self-documenting code base.
