# Capacity Connect - Implementation Progress

## Phase Tracking

| Phase | Description | Status | Gate Passed |
|---|---|---|---|
| **B0** | Foundations (layout, custom User, settings, tooling, base tests) | Complete | Yes |
| **B1** | Authentication & Onboarding (Pending User Approval) | Not Started | No |
| **B2** | Course & Competency Management | Not Started | No |
| **B3** | Assessment Engine | Not Started | No |
| **B4** | Verification & Certification | Not Started | No |

## Phase B0 Changelog

- Initialized Git repository on branch `phase/b0-foundations`.
- Configured `.gitignore` for environments, secrets, databases, media, and build caches.
- Created multi-environment Django settings structure (`base.py`, `dev.py`, `prod.py`, `test.py`) with `django-environ`.
- Established `apps/` package with `apps/core` and `apps/accounts`.
- Implemented `TimeStampedModel` in `apps.core.models`, `constants.py`, and `exceptions.py`.
- Implemented custom `User` with `role` (`UserRole.TRAINEE`, `TRAINER`, `ADMIN`), `is_approved`, and unique required `email`.
- Implemented custom `UserManager` enforcing `role=ADMIN` and `is_approved=True` on `create_superuser`.
- Registered `AUTH_USER_MODEL = "accounts.User"` prior to generating initial migration `0001_initial.py`.
- Configured Ruff rules in `pyproject.toml` and Pytest in `pytest.ini`.
- Authored test suite covering default approval, role validity, email uniqueness, superuser privileges, and test settings loading.
