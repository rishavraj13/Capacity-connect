# Capacity Connect - Implementation Progress

## Phase Tracking

| Phase | Description | Status | Gate Passed |
|---|---|---|---|
| **B0** | Foundations (layout, custom User, settings, tooling, base tests) | Merged & Tagged `b0-approved` | Yes |
| **B0.1** | Foundations Fix Round (Django 5.2 LTS, Ruff rules, Coverage config, ADRs) | Approved | Yes |
| **B1** | Accounts (Signup, Approval Gate, Login/Logout, Roles, Admin Management) | Complete | Yes |
| **B2** | Course & Competency Management | Not Started | No |
| **B3** | Assessment Engine | Not Started | No |
| **B4** | Verification & Certification | Not Started | No |

## Phase B1 Changelog

- Moved `apps/accounts/factories.py` to `apps/accounts/tests/factories.py` (dev-only dependency isolation).
- Created domain exceptions in `apps/core/exceptions.py` (`UserManagementError`, `SelfModificationError`, `LastAdminProtectionError`, `InvalidRoleError`).
- Implemented `apps/accounts/services.py` with `register_user`, `approve_user`, `reject_user`, `change_role`, ensuring admin self-protection and last active admin safety.
- Implemented `apps/accounts/selectors.py` (`pending_users`, `users_filtered`) with deterministic ordering.
- Implemented `apps/accounts/forms.py` (`SignupForm`, `LoginForm`, `RoleChangeForm`), guaranteeing password-first verification to prevent user status leaks, case-insensitive email normalization, and blocking privileged field tampering.
- Implemented `apps/accounts/permissions.py` with `RoleRequiredMixin` and `@role_required` decorator enforcing authentication, active approval, and role authorization.
- Created semantic unstyled templates extending `templates/base.html`, including `templates/includes/messages.html`, `templates/includes/form_field.html`, and account portal templates.
- Implemented views in `apps/accounts/views.py` (thin, <= 15 lines of logic each), POST-only logout, stable role landing views (`/trainee/`, `/trainer/`, `/admin-panel/`), and administrator management actions with CSRF protection and 20-item pagination.
- Achieved 100% test coverage across all `apps/` code with 73 unit and integration tests covering all matrix permissions, query count boundaries, and edge cases.
- Recorded ADRs 009-011 in `docs/DECISIONS.md`.

## Phase B0.1 Changelog

- Upgraded and pinned `Django==5.2.18` (LTS) for official Python 3.14 support.
- Configured coverage in `pyproject.toml` (`source = ["apps"]`, omitting migrations and tests) with 100% test coverage.
- Enforced mechanical Ruff rules in `pyproject.toml`: `C901` (max-complexity 8), `PLR0913` (max-args 4), `PLR0915` (max-statements 20), `T20` (ban print), `E722` (ban bare except), `ERA001` (ban commented-out code).
- Verified line count of all `.py` files (all ≤ 104 lines, well within 250 line limit).
- Documented ADRs 005-008 in `docs/DECISIONS.md`.
- Added `docs/IMPLEMENTATION_BRIEF.md` covering all 16 architecture and engineering sections.
- Re-verified all gate checks: Pytest, Coverage, Ruff check, Ruff format, makemigrations, fresh database migration, check, and pip check.
