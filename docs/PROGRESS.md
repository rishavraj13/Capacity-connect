# Capacity Connect - Implementation Progress

## Phase Tracking

| Phase | Description | Status | Gate Passed |
|---|---|---|---|
| **B0** | Foundations (layout, custom User, settings, tooling, base tests) | Reviewed | Yes |
| **B0.1** | Foundations Fix Round (Django 5.2 LTS, Ruff rules, Coverage config, ADRs) | Complete | Yes |
| **B1** | Authentication & Onboarding (Pending User Approval) | Not Started | No |
| **B2** | Course & Competency Management | Not Started | No |
| **B3** | Assessment Engine | Not Started | No |
| **B4** | Verification & Certification | Not Started | No |

## Phase B0.1 Changelog

- Upgraded and pinned `Django==5.2.18` (LTS) for official Python 3.14 support.
- Configured coverage in `pyproject.toml` (`source = ["apps"]`, omitting migrations and tests) with 100% test coverage.
- Enforced mechanical Ruff rules in `pyproject.toml`: `C901` (max-complexity 8), `PLR0913` (max-args 4), `PLR0915` (max-statements 20), `T20` (ban print), `E722` (ban bare except), `ERA001` (ban commented-out code).
- Verified line count of all `.py` files (all ≤ 104 lines, well within 250 line limit).
- Documented ADRs 005-008 in `docs/DECISIONS.md`.
- Added `docs/IMPLEMENTATION_BRIEF.md` covering all 16 architecture and engineering sections.
- Re-verified all gate checks: Pytest, Coverage, Ruff check, Ruff format, makemigrations, fresh database migration, check, and pip check.
