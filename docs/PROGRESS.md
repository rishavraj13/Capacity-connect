# Capacity Connect - Implementation Progress

## Phase Tracking

| Phase | Scope | Gate (acceptance criteria) |
|---|---|---|
| **B0 Foundations** | Repo, virtualenv, split settings, `.env`, ruff, pytest, `core` app, custom `User` model and first migration | `pytest` runs, `ruff` clean, migrations apply on a fresh DB |
| **B1 Accounts** | Signup with role choice, approval gate at login, role mixins, admin user management (approve, reject, change role) | Unapproved login blocked; role isolation tests pass |
| **B2 Catalog and Profiles** | Subjects, skills, both profiles, qualifications, experience, external certificates, upload validation | Profile CRUD works per role; invalid uploads rejected |
| **B3 Courses and Library** | Courses, modules, enrollment, progress, library uploads and listing | Ownership enforced; duplicate enrollment impossible; `station_map_for` correct |
| **B4 Assessments** | Questionnaires, questions, options, attempt flow, auto-grading, deadlines, results, trainer participation view | All business rules 2 to 4 proven by tests, including boundary times |
| **B5 Feedback and Certificates** | Ratings, completion logic, certificate issuance, PDF, public verification by ID | Certificate issued exactly once; PDF opens; verification works |
| **B6 Competency, Announcements, Dashboards** | Ranking selector, announcement CRUD and publish flow, admin analytics selectors | Ranking matches the formula in tests; unpublished items never appear |
| **B7 Hardening** | Security pass, query optimisation, settings review, seed command, README | Section 11 checklist fully ticked |

Status: B0, B1 and B2/B2.1 approved; B3 approved; B4 gate passed and awaiting review; B5 through B7 not started. Historical fix rounds remain below.

## Phase B1.1 Fix Round Changelog

- Saved and committed verbatim implementation brief in `docs/IMPLEMENTATION_BRIEF.md`.
- Hardened `config/settings/prod.py`: env-driven `DEBUG=False`, `SECRET_KEY` with no default, `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `SECURE_HSTS_SECONDS=3600`, `SECURE_HSTS_INCLUDE_SUBDOMAINS=False`, and `SECURE_CONTENT_TYPE_NOSNIFF=True`.
- Implemented database-level case-insensitive email uniqueness via `models.UniqueConstraint(Lower("email"), name="unique_lower_email")` in migration `0002_user_unique_lower_email.py` and added test verifying database rejection of `A@x.com` when `a@x.com` exists.
- Implemented single 54-combination parametrized permission matrix table in `apps/accounts/tests/test_permissions.py` covering all 6 actors across all 9 protected endpoints.
- Added tests asserting 405 Method Not Allowed on GET requests for state-changing endpoints (`logout`, `admin_approve_user`, `admin_reject_user`, `admin_change_role`).
- Implemented and tested `next` URL validation in `login_view` using `url_has_allowed_host_and_scheme` to discard untrusted external targets.
- Added strict login leak tests asserting identical generic error messages for unapproved, inactive, and nonexistent accounts upon wrong password entry.
- Added test proving an account rejected/deactivated while holding an active session loses portal access on the immediate next request.
- Performed AST-based function audit proving all 95 functions across `apps/` and `config/` are $\le 25$ lines.
- Recorded ADRs 012-014 in `docs/DECISIONS.md`.

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
- Verified line count of all `.py` files (all <= 104 lines, well within 250 line limit).
- Documented ADRs 005-008 in `docs/DECISIONS.md`.
- Added `docs/IMPLEMENTATION_BRIEF.md` covering all 16 architecture and engineering sections.
- Re-verified all gate checks: Pytest, Coverage, Ruff check, Ruff format, makemigrations, fresh database migration, check, and pip check.

## B2 Catalog and Profiles (approved; merged and tagged b2-approved)
- [x] B1 merged into main and tagged b1-approved.
- [x] Phase table corrected and ADR 015 appended in the first B2 commit.
- [x] Added root AGENTS.md; split authentication and administrator view tests.
- [x] Extracted reusable permission matrix helper with readable case IDs.
- [x] Enabled branch coverage and added missing service/form branch tests.
- [x] Reproduced and fixed HTTPS login redirect downgrade (BUG 001).
- [x] Added catalog models, constraints, services, selectors and role-restricted views.
- [x] Added lazy role profiles, account editing and owner-scoped child CRUD.
- [x] Added private uploads, validation, UUID naming and commit-time file cleanup.
- [x] Added complete new-route matrices, CSRF, IDOR, mass-assignment and query-count tests.
- [x] Completed final gate: 517 tests pass, 867/867 statements and 116/118 branches covered; all service/selector/form/permission modules at 100%.
- [x] Delivered docs/B2_REPORT.md and docs/B2_GATE_OUTPUT.txt with raw command evidence.
- [x] User approved B2/B2.1; merged into main and tagged b2-approved.

## Current known issues
- Login and signup throttling is not implemented (ADR 011, planned for B7).
- HSTS is 3600 s; include-subdomains and preload are intentionally off until HTTPS is verified (B7).
- Library video downloads do not implement Range requests; long videos cannot seek (planned for B7 deployment).
- Storage writes are not transactional; new files can remain unreferenced after an outer transaction rollback (ADR 021).

## B2.1 pre-merge review (approved)
- [x] Confirmed initial profiles migrations shared one first commit; regenerated one clean 0001.
- [x] Fixed source encoding, setup README and status-independent AGENTS instructions.
- [x] Removed committed raw transcript from Git; local evidence is ignored.
- [x] Enforced production HttpOnly CSRF cookie and image decompression limits.
- [x] Preserved retired skills and recovered account email database races.
- [x] Added 1/10-child query counts and covered both inherited account view branches.
- [x] Final gate: 532 tests passed; 898/898 statements and 120/120 branches covered.
- [x] Delivered docs/B21_REPORT.md with requested source and real verification output.
- [x] User approved B2.1 and authorized B3.

## B3 Step 0
- [x] Approved B2 merged and tagged b2-approved; created phase/b3-courses-library.
- [x] Verified ignore rules for public/private storage and local evidence.
- [x] Moved CSRF_COOKIE_HTTPONLY to base settings; dev/prod inherit True.
- [x] Full pytest: 533 passed in 6.28s; real private_uploads file list before=[] and after=[] (identical).

## B3 Courses and Library (approved; merged and tagged b3-approved)
- [x] Course/module/enrollment/progress models, named constraints and migrations.
- [x] Eligible-role and owner/Admin writes, clean unique races and sequential progress.
- [x] Visibility/count selectors and immutable station-map handoff.
- [x] Kind-specific private library uploads, lifecycle and download delivery.
- [x] Bare semantic views, reachable navigation, seven-actor new-route matrix and CSRF tests.
- [x] Four-query station-map tests at small and large scales; IDOR and file cleanup tests.
- [x] Final gate: 948 tests passed; 1597/1597 statements and 222/222 branches covered.
- [x] Compact report delivered in docs/B3_REPORT.md; full transcript ignored in .local/reports/.
- [x] User B3 approval; merged/tagged b3-approved and authorized B4.

## B4 Step 0 and Assessments
- [x] B3 merged/tagged; created phase/b4-assessments.
- [x] Authorized Attempt.status amendment recorded in section 4.
- [x] Reproduced/fixed course-wide module-order freeze; retained unpublished access.
- [x] Proved existing Admin trainer reassignment and ACTIVE all-DONE station maps.
- [x] Questionnaire/question/option authoring, protected history and first-attempt freeze.
- [x] Shared clock, exact start/grace boundaries, quota/resume/expiry and atomic idempotent grading.
- [x] Safe paper/results DTOs, departures, annotated usage and constant-query participation/statistics.
- [x] Bare HTML routes, explicit roles/ownership, seven-actor GET/POST matrix, CSRF/IDOR/mass-assignment checks.
- [x] Fresh migration and full gate: 1265 tests; coverage 99% (2303 statements, 7 missed; 324 branches, 2 partial).
- [x] Compact report docs/B4_REPORT.md; full transcript ignored in .local/reports/.
- [ ] User B4 review/approval. Do not merge/tag B4 or start B5 before approval.
