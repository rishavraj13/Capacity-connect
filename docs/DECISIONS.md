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

## ADR 004: Strict Code Quality & Mechanical Enforcement
- **Context:** Project brief enforces strict quality constraints: max 25 lines per function, max 250 lines per module, type hints on all functions, one-line docstrings stating why, no magic strings.
- **Decision:** Configure Ruff in `pyproject.toml` with `C901` (max-complexity 8), `PLR0913` (max-args 4), `PLR0915` (max-statements 20), `T20` (ban print), `E722` (ban bare except), and `ERA001` (ban commented-out code).
- **Consequences:** Eliminates manual style debates, prevents complexity drift, and automates enforcement.

## ADR 005: Django 5.2.18 LTS Pin for Python 3.14 Compatibility
- **Context:** Django 5.1 reached end-of-life on 3 Dec 2025 and did not officially support Python 3.14.
- **Decision:** Upgrade the framework pin from Django 5.1 to the latest Django 5.2 LTS release (`Django==5.2.18`, exceeding the 5.2.8 minimum requirement).
- **Consequences:** Full official upstream support for Python 3.14 runtime, long-term security maintenance, and zero broken requirements under `pip check`.

## ADR 006: User Admin Registration
- **Context:** Although not strictly enumerated in the raw B0 deliverable list, administrative visibility into custom user attributes is necessary for operator workflows.
- **Decision:** Register `apps.accounts.models.User` in `apps.accounts.admin.UserAdmin` inheriting from `django.contrib.auth.admin.UserAdmin`, exposing `role` and `is_approved` in list displays, filters, and fieldsets.
- **Consequences:** Portal administrators can immediately view, filter, and modify approval status and user roles.

## ADR 007: Python Version Used
- **Context:** System runtime requires modern language features and predictable execution.
- **Decision:** The project targets and runs under **Python 3.14** (`3.14.6` on host), supported by Django 5.2.18 LTS.
- **Consequences:** Up-to-date syntax, performance optimizations, and forward compatibility.

## ADR 008: Dependency Pins and Rationale
- **Context:** All dependencies must be deterministically pinned with clear justification to prevent supply-chain drift and build breaks.
- **Decision:**
  - `Django==5.2.18`: Core web framework pinned to latest 5.2 LTS with official Python 3.14 support.
  - `django-environ==0.14.0`: Robust 12-factor application configuration parsing `.env` files.
  - `Pillow==13.0.0`: Required imaging library for user profile avatars and portal assets.
  - `reportlab==5.1.0`: PDF generation library for training certificates and grade reports.
  - `pytest==9.2.0`: Standard test runner framework.
  - `pytest-django==4.14.0`: Pytest integration plugin for Django settings and test database lifecycle.
  - `factory-boy==3.3.3`: Model factory generator for reliable unit test fixtures.
  - `coverage==7.17.0`: Test code coverage measurement and reporting tool.
  - `ruff==0.17.3`: High-performance linter and code formatter.
- **Consequences:** Repeatable, zero-conflict environment verified via `pip check`.

## ADR 009: Account Rejection Implemented via is_active=False
- **Context:** Brief mandates user approval gating without adding unauthorized database fields beyond Section 4 schema specifications.
- **Decision:** Rejection of user accounts deactivates the user record by setting `is_active=False` rather than creating a dedicated rejection field.
- **Consequences:** Conforms strictly to schema limits, leverages standard Django authentication safeguards preventing disabled user logins, and renders a generic disabled notification on login attempt.

## ADR 010: Stable Role Landing Page URL Identifiers
- **Context:** Upon successful login, users must be redirected to role-specific landing destinations (`/trainee/`, `/trainer/`, `/admin-panel/`).
- **Decision:** Establish stable URL patterns named `trainee_home`, `trainer_home`, and `admin_panel`. Future phases will build out functional content for these views without modifying their URL routes or reversing names.
- **Consequences:** Post-login redirection logic and role permission matrices remain immutable across Phase B2 through B7 evolutions.

## ADR 011: Deferral of Authentication Throttling to Phase B7
- **Context:** Protection against brute-force credential stuffing and registration spam is necessary for public production facing portals.
- **Decision:** Rate limiting and request throttling on `/signup/` and `/login/` endpoints are explicitly deferred from Phase B1 to Phase B7 (Security & Hardening).
- **Consequences:** B1 remains focused on foundational authentication mechanics and role access control; security throttling will be systematically layered in during Phase B7.
