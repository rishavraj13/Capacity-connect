# Capacity Connect – Backend Implementation Brief

## 1. Executive Summary & Objectives
Capacity Connect is a digital learning management and institutional capacity-building portal. The backend is designed with a strict phased delivery model, role-based workflows, and automated verification gates.

## 2. Coding Standards & Architectural Rules
- **Function Limit:** Maximum 25 lines per function.
- **Module Limit:** Maximum 250 lines per module.
- **Type Annotations:** Explicit type hints on all function signatures and return types.
- **Documentation:** Concise, one-line docstrings stating *why* the function/class exists.
- **Cleanliness:** No magic strings (use enums/TextChoices), no commented-out code, and no patchwork refactoring.
- **Mechanical Enforcement:**
  - `C901`: Maximum cyclomatic complexity of 8.
  - `PLR0913`: Maximum 4 function/method arguments (excluding `self`/`cls`).
  - `PLR0915`: Maximum 20 statements per function.
  - `T20`: Ban `print()` statements in production code.
  - `E722`: Ban bare `except:` clauses.
  - `ERA001`: Ban commented-out code blocks.

## 3. Project Architecture & Layout
```text
config/
  settings/
    base.py
    dev.py
    prod.py
    test.py
  asgi.py
  urls.py
  wsgi.py
apps/
  core/
  accounts/
requirements/
  base.txt
  dev.txt
docs/
  PROGRESS.md
  DECISIONS.md
  BUGS.md
  IMPLEMENTATION_BRIEF.md
pyproject.toml
pytest.ini
manage.py
```

## 4. Environment & Dependency Governance
- All secrets and runtime variables must be parsed through `.env` using `django-environ`.
- A committed `.env.example` serves as the baseline template.
- Exact pinned dependencies only:
  - Base: `Django==5.2.18`, `django-environ==0.14.0`, `Pillow==13.0.0`, `reportlab==5.1.0`.
  - Dev: `pytest==9.2.0`, `pytest-django==4.14.0`, `factory-boy==3.3.3`, `coverage==7.17.0`, `ruff==0.17.3`.

## 5. Core Domain Primitives
- `apps/core/models.py`: Abstract `TimeStampedModel` tracking `created_at` and `updated_at`.
- `apps/core/constants.py`: Reserved for shared constants and evaluation grade bands.
- `apps/core/exceptions.py`: Base domain exception (`CapacityConnectError`).

## 6. User Management & Authentication
- Custom `User` subclassing `AbstractUser`:
  - `role`: TextChoices `TRAINEE`, `TRAINER`, `ADMIN`.
  - `is_approved`: Boolean flag defaulting to `False`.
  - `email`: Required and unique.
- Custom `UserManager`:
  - `create_superuser` enforces `role=ADMIN` and `is_approved=True`.
  - `create_user` validates email presence.
- `AUTH_USER_MODEL = 'accounts.User'` registered before generating the initial migration.

## 7. Assessment Engine & Grading
- Planned for Phase B3: Structured assessment models, question banks, and grade band calculations.

## 8. Course & Curriculum Management
- Planned for Phase B2: Course catalogs, module tracking, and trainee enrollment.

## 9. Verification & PDF Certification
- Planned for Phase B4: Generation of authenticated completion certificates via ReportLab.

## 10. Security & Hash Configuration
- Production enforces strong Argon2/PBKDF2 password hashing.
- Test settings enforce fast `MD5PasswordHasher` with an in-memory SQLite database (`:memory:`).

## 11. Testing & Code Quality Automation
- Pytest test runner with `pytest-django`.
- Factory Boy factories for test model generation (`UserFactory`).
- Coverage tracking with source scoped to `apps/` (omitting tests and migrations).

## 12. Reporting Protocol
Every phase report must strictly use the 9 labelled fields:
1. `PHASE/TASK`
2. `STATUS`
3. `GOAL`
4. `WHAT CHANGED`
5. `HOW IT WAS VERIFIED`
6. `DECISIONS AND ASSUMPTIONS`
7. `KNOWN ISSUES / RISKS`
8. `DEMO STEPS`
9. `NEXT`

## 13. Version Control & Git Workflow
- Branch naming convention: `phase/<phase-name>`.
- Commit messages formatted via Conventional Commits (`feat(...)`, `chore(...)`, `docs(...)`, `fix(...)`).

## 14. Phase Completion Verification Gates
A phase is complete only when all gate checks pass with real output:
1. `pytest` passes.
2. `coverage run -m pytest` and `coverage report -m` demonstrate high coverage.
3. `ruff check .` and `ruff format --check .` are clean.
4. `python manage.py makemigrations --check` detects no pending changes.
5. `python manage.py migrate` succeeds on a fresh database.
6. `python manage.py check` reports no issues.
7. `pip check` reports no broken requirements.

## 15. Operational Documentation Register
- `docs/PROGRESS.md`: Phase status and changelog.
- `docs/DECISIONS.md`: Architectural Decision Records (ADR).
- `docs/BUGS.md`: Bug and defect registry.

## 16. Phased Delivery Roadmap
- **B0:** Foundations (Project structure, custom User, settings, tooling, base tests).
- **B0.1:** Foundations Review & Upgrades (Django 5.2 LTS upgrade, mechanical Ruff rules, coverage configuration).
- **B1:** Authentication & Onboarding (Pending explicit approval).
- **B2:** Courses & Modules.
- **B3:** Assessment Engine.
- **B4:** Certification & Reporting.
