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

## ADR 012: Production Security Baseline & HSTS Duration
- **Context:** Production deployment requires SSL redirection, secure cookies, and HTTP Strict Transport Security (HSTS). Enabling long HSTS prematurely without verified HTTPS can cause irreversible browser access lockouts.
- **Decision:** In `config/settings/prod.py`, enforce `DEBUG = False`, `SECRET_KEY` with no default (fails loudly if missing), `SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SECURE_CONTENT_TYPE_NOSNIFF = True`, and start `SECURE_HSTS_SECONDS = 3600` with `SECURE_HSTS_INCLUDE_SUBDOMAINS = False`. Once HTTPS certificate installation is verified in production, `SECURE_HSTS_SECONDS` must be raised to `31536000` (1 year).
- **Consequences:** Eliminates critical deployment warnings while providing a safe rollout window for SSL certificate validation.

## ADR 013: Database-Level Lowercase Email Uniqueness Constraint
- **Context:** Brief mandates case-insensitive email uniqueness. Application-level normalization and form validation alone do not prevent race conditions or direct DB insertions.
- **Decision:** Added `models.UniqueConstraint(Lower("email"), name="unique_lower_email")` to `User.Meta` via migration `0002_user_unique_lower_email.py`, maintaining form-level validation and manager normalization.
- **Consequences:** Guarantees database-level integrity rejecting duplicate emails differing only by casing (e.g., rejecting `A@x.com` when `a@x.com` exists).

## ADR 014: Secure Redirection for Next Parameter
- **Context:** The login view supports a `next` query/POST parameter to return users to requested protected pages after authentication. Unsanitized redirection can introduce open-redirect vulnerabilities.
- **Decision:** Validate `next` URLs using `django.utils.http.url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()})`. If `next` points to an untrusted external host, it is discarded and the user is redirected to their default role landing page.
- **Consequences:** Preserves seamless post-login navigation while mitigating phishing and open-redirect vectors.

## ADR 015: Binding phase definitions
- **Context:** PROGRESS.md was generated from a reconstructed brief.
- **Decision:** Corrected the phase table to section 8; the implementation brief is the single source of truth for phase names and scope.
- **Consequences:** Historical entries remain intact; phase planning follows section 8 exactly.

## ADR 016: Catalog lifecycle and database names
- **Decision:** Subject and Skill names have both form validation and authorized database Lower(name) uniqueness. Subject lifecycle uses deactivate/reactivate POST actions, never deletion; Skill.subject uses PROTECT. Descriptive names use a shared 150-character limit.
- **Consequences:** Existing subject references survive retirement. New skills and skill moves cannot target inactive subjects; an existing skill on a retired subject may be renamed without changing its subject.

## ADR 017: Lazy role profiles and account editing
- **Decision:** ensure_trainee_profile and ensure_trainer_profile are idempotent services without signals. A role change preserves the old profile and creates the new one lazily. There is no Admin profile model; all approved roles can edit basic account details.
- **Consequences:** Profile ownership and account privileges are excluded from forms and service write allowlists. Account email remains normalized to lowercase with the approved database constraint.

## ADR 018: Private file delivery and visibility
- **Decision:** Profile photos and certificate files use PrivateStorage, which refuses public URL generation. One FileResponse view checks selector visibility before opening storage; attachments use opaque filenames, explicit Content-Type and private/no-store caching. A shared PrivateFileInput renders existing uploads without calling file.url and preserves replacement/clear controls. MEDIA_ROOT must never be mapped by a public web server.
- **Consequences:** Trainee profiles and files are visible to owner and Admin; trainer profiles and photos are readable by any approved user. Cross-owner child edits/deletes return 404 from filtered selectors. Admin has read access, not child-edit privileges.

## ADR 019: Upload content contract and opaque paths
- **Decision:** A deconstructible UploadPath generates UUID names in per-model folders, retaining only allowlisted lowercase extensions. Photos accept jpg/jpeg/png up to 2 MiB; certificates additionally accept pdf up to 5 MiB. Settings allow size overrides. Pillow verify and matching image formats check images; PDFs must begin with %PDF-. Browser MIME headers are not trusted.
- **Consequences:** Empty, oversized, mismatched and extension-spoofed uploads fail before service persistence. The PDF signature check is the requested validation contract, not a full PDF parser.

## ADR 020: Profile validation bounds
- **Decision:** WorkExperience dates use the authorized nullable-aware database check. Trainer experience uses 0..60 validators. Qualification year bounds are named constants: 1900 through 2100. Descriptive profile fields use a shared 200-character limit.
- **Consequences:** Ongoing employment is accepted; reversed dates and out-of-range experience/year inputs are rejected. Fixed bounds avoid migration drift when the calendar year changes.

## ADR 021: File cleanup at transaction commit
- **Decision:** Services schedule deletion of replaced photos/evidence and deleted child evidence with transaction.on_commit; no signals are used.
- **Consequences:** A rollback preserves old files. Storage writes themselves are not transactional: a new upload written before an outer transaction rollback can remain unreferenced; reconciliation belongs to storage operations rather than deleting the preserved old file.

## ADR 022: Shared form coordination and permission contracts
- **Decision:** A small core FormAction dataclass groups HTTP form configuration; form_response handles validation and delegates writes to services. Forms display on GET and persist on POST; destructive/lifecycle endpoints accept POST only. Shared matrix machinery accepts declared rows and an optional fixture owner.
- **Consequences:** New views declare roles explicitly, remain thin, and share validation-error presentation. Catalog matrix has 96 cases; profiles have 216 cases including three private-file variants. The approved B1 matrix retains all 54 cases with readable actor-url_name-METHOD IDs.

## ADR 023: Generated migration size exception (explicit user approval)
- **Context:** Generated profiles migration 0001_initial is 297 lines and has run only in disposable test databases.
- **Decision:** The user explicitly chose to exempt generated migrations from the 250-line module limit. Preserve migration history; do not split or rewrite the applied generated migration.
- **Consequences:** All application and test modules remain limited to 250 lines; the final wc/AST audit excludes generated migrations as requested in the B2 gate.
