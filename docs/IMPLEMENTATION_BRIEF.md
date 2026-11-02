# Capacity Connect – Backend Implementation Brief

*For the coding agent. Read fully before writing any code. This document is binding.*

## 1. Mission and current stage

Build **Capacity Connect**, a Django learning-management portal with three roles (Trainee, Trainer, Admin).

**Current stage: backend only, then testing, then bug fixing.** The frontend (the approved *Metro Map* design system: Day/Night/Signage themes, departure board, quiz ticket, formal certificate, control room, station master) is built **after** the backend passes its gate. Do not start it early.

Stage order, strictly:

1. **Build** the backend phases B0 to B7 (section 8).
2. **Test** (section 9).
3. **Fix** bugs (section 10).
4. **Hand off** with a final report. Then wait for user approval before any frontend work.

### Stack (fixed)

Django 5.x, SQLite for development and PostgreSQL-ready settings, Django templates (no DRF, no React, no SPA), Pillow, ReportLab (certificate PDFs), `django-environ`. Tooling: `pytest`, `pytest-django`, `factory_boy`, `coverage`, `ruff`. **Do not add any other dependency without asking the user first.**

## 2. Non-negotiable coding rules

These exist to keep the code short, readable and maintainable. Violations must be fixed before a phase can be reported as done.

### Size and shape
- Functions: **max 25 lines**, one responsibility, max 4 parameters (group the rest in a dataclass).
- Modules: **max 250 lines**. If longer, split by responsibility, not arbitrarily.
- Views: **max 15 lines of logic**. A view only parses input, calls a service or selector, and returns a response.
- No nesting deeper than 3 levels. Use early returns and guard clauses.

### Layering (every app follows this)

| File | Holds | Never holds |
|---|---|---|
| `models.py` | Fields, constraints, `__str__`, tiny derived properties | Business workflows, queries across apps |
| `services.py` | **Writes** and business rules (enroll, grade, issue certificate) | HTTP objects, rendering |
| `selectors.py` | **Reads**: optimised querysets and aggregates | Writes |
| `forms.py` | Validation of user input | Business rules |
| `permissions.py` | Role mixins and decorators | Queries |
| `views.py` (or `views/`) | Thin request/response glue | Logic |
| `tests/` | Mirrors the above | |

### Style
- Type hints on all function signatures. One-line docstring on every public function and class that says *why*, not *what*.
- No magic strings or numbers: use `TextChoices`, constants in `constants.py`, or settings.
- No duplicated logic: if it appears twice, extract it once.
- No commented-out code, no `print`, no bare `except`, no `# TODO` without a matching entry in `docs/PROGRESS.md`.
- Use `select_related`/`prefetch_related` in selectors. No query inside a template loop.
- Run `ruff check` and `ruff format` before every commit. Zero warnings.

### What "patchwork" means here, and the rule against it

Patchwork is any fix that makes a symptom disappear without addressing its cause: special-case `if` branches, try/except that swallows errors, duplicated code with small tweaks, editing a migration that was already applied, copy-pasted views, or "temporary" workarounds.

When something does not fit the current design, **stop, fix the design properly (refactor), update the tests, and explain the change in your report.** Never layer a workaround on top.

## 3. Project layout

```
capacityconnect/            # repo root
├── config/                 # project package
│   └── settings/ base.py dev.py prod.py test.py
├── apps/
│   ├── core/               # abstract models, constants, shared mixins, exceptions
│   ├── accounts/           # User, signup, approval, role permissions
│   ├── profiles/           # trainee and trainer profiles, qualifications, experience
│   ├── catalog/            # Subject (a "line"), Skill
│   ├── courses/            # Course, Module (a "station"), Enrollment, progress
│   ├── library/            # trainer resources
│   ├── assessments/        # questionnaires, questions, attempts, grading
│   ├── feedback/           # ratings and comments
│   ├── certificates/       # issuance, PDF, public verification
│   ├── competency/         # trainer competency and ranking
│   ├── announcements/      # homepage board content
│   └── dashboards/         # read-only analytics selectors and views
├── templates/              # bare semantic HTML only at this stage
├── docs/ PROGRESS.md DECISIONS.md BUGS.md
├── .env.example  requirements/ base.txt dev.txt
└── manage.py  pytest.ini  pyproject.toml
```

Each app is created with `startapp` inside `apps/` and registered via its `AppConfig` path. Keep app boundaries clean: apps import **services/selectors** of other apps, never their views.

### Settings
- `base.py` shared, `dev.py` (DEBUG on), `prod.py` (DEBUG off, secure cookies, HSTS), `test.py` (fast hasher, in-memory DB).
- All secrets and environment values come from `.env` via `django-environ`. `.env` is git-ignored; `.env.example` is committed.

## 4. Domain model

Use `core.TimeStampedModel` (created/updated) as the base for all models. All choice fields use `TextChoices`. All foreign keys state `on_delete` deliberately and a `related_name`.

### accounts
- **User** (`AbstractUser`): `role` (TRAINEE, TRAINER, ADMIN), `is_approved` (bool, default False), `email` unique and required. Must exist **before the first migration**. Superusers created with `createsuperuser` are auto-approved ADMINs.

### catalog
- **Subject**: `name` (unique), `description`, `is_active`. In the UI this is a *line*.
- **Skill**: `name` (unique), `subject` (FK).

### profiles
- **TraineeProfile** (1:1 User): `bio`, `interests`, `skills` (M2M Skill), `photo`.
- **Qualification** (FK profile): `degree`, `institution`, `year`.
- **WorkExperience** (FK profile): `organisation`, `role`, `start_date`, `end_date` (nullable), `description`.
- **ExternalCertificate** (FK profile): `title`, `issuer`, `file`, `issued_on`.
- **TrainerProfile** (1:1 User): `bio`, `headline`, `years_experience`, `photo`.

### courses
- **Course**: `title`, `description`, `subject` (FK), `trainer` (FK User, role TRAINER), `start_date`, `end_date`, `is_published`.
- **Module** (a *station*): `course` (FK), `title`, `order` (unique per course), `skills` (M2M Skill; a module whose skills span subjects is an *interchange*).
- **Enrollment**: `trainee`, `course`, `status` (ACTIVE, COMPLETED, DROPPED). Unique on (trainee, course).
- **ModuleProgress**: `enrollment`, `module`, `completed_at`. Unique on (enrollment, module).

### library
- **LibraryResource**: `trainer`, `subject`, `course` (nullable), `title`, `kind` (VIDEO, PRESENTATION, DOCUMENT), `file`, `description`, `is_published`.

### assessments
- **Questionnaire**: `course`, `subject`, `trainer`, `title`, `opens_at`, `deadline`, `duration_minutes`, `pass_percent` (default 50), `max_attempts` (default 1).
- **Question**: `questionnaire`, `text`, `order`, `marks` (default 1).
- **Option**: `question`, `text`, `is_correct`. Exactly one correct option per question (enforced in the service and validated in the form).
- **Attempt**: `questionnaire`, `trainee`, `started_at`, `submitted_at` (nullable), `score`, `percent`, `passed`, `status` (IN_PROGRESS, SUBMITTED, TIMED_OUT; default IN_PROGRESS).
- **AttemptAnswer**: `attempt`, `question`, `selected_option`, `is_correct`. Unique on (attempt, question).

### feedback
- **Feedback**: `author`, `course` (FK, nullable), `resource` (FK, nullable), `rating` (1 to 5), `comment`. A database `CheckConstraint` requires exactly one of `course` or `resource`. Unique per (author, target).

### certificates
- **Certificate**: `enrollment` (1:1), `certificate_id` (unique, format `CC-YYYY-NNNNN`), `issued_on`, `average_percent`, `grade`, `pdf` (file).

### competency
- **TrainerCompetency**: `trainer`, `subject`, `proficiency` (1 to 5), `years_experience`. Unique on (trainer, subject).

### announcements
- **Announcement**: `title`, `body`, `category` (NOTICE, ACHIEVEMENT, NEW_CONTENT, DEADLINE), `is_published`, `published_at`, `created_by`.

## 5. Roles and permissions

| Capability | Trainee | Trainer | Admin |
|---|---|---|---|
| Sign up (needs approval) | Yes | Yes | No (created by superuser) |
| Edit own profile | Yes | Yes | Yes |
| View published courses and resources | Yes | Yes | Yes |
| Enroll, track progress, attempt quizzes, give feedback | Yes | No | No |
| Create and edit **own** courses, modules, questionnaires, resources | No | Yes | Yes (any) |
| View participation and results for **own** courses | No | Yes | Yes (all) |
| Approve users, change roles, publish announcements | No | No | Yes |
| View dashboards and competency ranking | No | Own stats only | Yes |

Enforcement: a `RoleRequiredMixin` (class-based views) and an `@role_required` decorator in `accounts/permissions.py`, plus an `ApprovedUserRequired` check. **Every view declares its role explicitly.** Object-level checks (a trainer touching only their own course) live in selectors by filtering querysets, so unauthorised objects return 404.

## 6. Business rules (server enforced, never UI-only)

1. **Approval:** unapproved users cannot log in. Login attempts return a clear "awaiting approval" message, not a generic failure.
2. **Deadlines:** an attempt can start only between `opens_at` and `deadline`, and a submission after `started_at + duration` (plus a small grace constant) is rejected or graded on saved answers only. Decide once in the service and document it in `DECISIONS.md`.
3. **Attempts:** a trainee cannot exceed `max_attempts`. Submissions are idempotent: a second submit of the same attempt does nothing.
4. **Grading:** auto-graded inside one `transaction.atomic()` in `assessments.services.submit_attempt`. Correct options are never sent to the client before submission.
5. **Enrollment:** only for published courses, and not duplicated.
6. **Completion:** an enrollment becomes COMPLETED when all modules are complete **and** every questionnaire for the course has a passing attempt.
7. **Certificate:** issued once, automatically, on completion. `average_percent` is the mean of each questionnaire's best attempt. Grade bands live in `constants.py`.
8. **Competency ranking:** `score = 0.4 × (proficiency/5) + 0.3 × (avg_rating/5) + 0.3 × min(years/10, 1)`. Weights are constants. Ranking is a selector, and ties break on courses delivered.
9. **Uploads:** validate extension, MIME type and size (limits in settings). Files are renamed and stored under a per-model path.

## 7. Metro hand-off contracts (build now, render later)

The frontend will need these. Provide them as **selectors returning plain dataclasses**, so the templates stay dumb and nothing has to be reworked later:

- `courses.selectors.station_map_for(trainee)` returns lines (subjects) with stations (modules) and each station's state: `DONE`, `CURRENT`, `LOCKED`, plus an `is_interchange` flag.
- `announcements.selectors.board()` returns the latest published items grouped by category for the departure board.
- `assessments.selectors.next_deadlines_for(trainee)` returns upcoming quiz departures.
- `dashboards.selectors` returns admin figures: enrollments per subject ("line load"), courses, certificates, average score, pending approvals.
- `competency.selectors.rank_trainers_for(subject)`.

## 8. Build phases

One Git branch per phase (`phase/b1-accounts`), Conventional Commits (`feat:`, `fix:`, `test:`, `refactor:`, `docs:`). **A phase is not done until its gate passes and its report is delivered.** Do not start the next phase before the user replies "approved" to your report.

Each phase delivers working but **unstyled, semantic HTML** views using one shared `base.html` with blocks and small partials. No CSS design work yet, so nothing is thrown away later.

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

Also provide a management command `seed_demo_data` (idempotent) so the user can see realistic data at any time.

## 9. Testing (after B7, but tests are written **with** every phase)

Every phase ships its own tests; the Testing stage is a full sweep and verification pass.

- **Tools:** `pytest-django`, `factory_boy` factories per app, `coverage`.
- **Layers:** model constraint tests, **service tests (most important)**, selector tests including query counts via `django_assert_num_queries`, view tests for status codes and redirects, permission matrix tests (every role against every protected URL).
- **Targets:** at least **90% coverage on `services.py` and `selectors.py`**, at least 80% overall. Coverage is a floor, not a goal: test behaviour and edge cases (deadline boundaries, duplicate submit, exactly-one-correct-option, ownership).
- **Security tests:** anonymous access, cross-role access, IDOR (one trainee reading another's attempt), CSRF on POST, upload abuse, mass-assignment of `role` or `is_approved` through forms.
- **Rule:** tests must be deterministic. Freeze time where needed, with no sleeps and no dependency on test order.

## 10. Bug protocol

For every bug, in this order:

1. **Reproduce** with a **failing test**. No test, no fix.
2. **Find the root cause.** State it in one sentence.
3. **Fix at the cause**, in the correct layer. If the design is the cause, refactor it (see the patchwork rule in section 2).
4. **Verify:** the new test passes, the full suite passes, `ruff` is clean.
5. **Record** in `docs/BUGS.md`: ID, symptom, root cause, fix, test name, commit.
6. **Report** it (section 12).

## 11. Security checklist (gate for B7)

- [x] `DEBUG=False`, `ALLOWED_HOSTS`, secure and HttpOnly cookies, CSRF, HSTS set in `prod.py`
- [x] `manage.py check --deploy` shows no warnings
- [x] Password validators on; no secrets in the repository
- [x] Every view has an explicit role requirement; object access is filtered by ownership
- [x] `role` and `is_approved` can never be set by a normal user through any form
- [x] Uploads validated; media never executed; private files not served publicly
- [x] Login and signup are rate-limited at least by simple throttling in a service, or the limitation is recorded in `DECISIONS.md`
- [x] No N+1 queries on list pages (verified by tests)

## 12. Communication protocol

You are working with a user who sees only your messages. Report clearly and honestly.

### Report after every phase (and after every bug fix), using exactly this format

```
PHASE / TASK: <id and name>
STATUS: Done | Blocked | Needs decision
GOAL: <one sentence>
WHAT CHANGED: <files and models, grouped by app, short>
HOW IT WAS VERIFIED: <exact commands and their real output summary:
  pytest result, coverage numbers, ruff result, manual checks>
DECISIONS AND ASSUMPTIONS: <anything not specified in this brief>
KNOWN ISSUES / RISKS: <honest list, or "none found">
DEMO STEPS: <how the user can try it, with seeded logins>
NEXT: <the next phase, awaiting approval>
```

### Rules of communication
- Report **real** results. Never claim tests pass unless you ran them. Paste the actual summary line.
- If something fails, say so, with the cause and your plan. Do not hide it or work around it quietly.
- Keep `docs/PROGRESS.md` (checklist per phase), `docs/DECISIONS.md` (every judgement call and why) and `docs/BUGS.md` current in the same commit as the work.
- **Stop and ask** the user before: adding a dependency, changing a model already approved, changing a business rule in section 6, deviating from this layout, or skipping any item here.
- Ask only **one clear question at a time**, state your recommended default, and continue with other unblocked work meanwhile.

## 13. Guardrails: staying on the goal

- **Scope:** only what the problem statement and this brief require. No extra features, apps, or "nice-to-haves". Proposals go in `DECISIONS.md` as suggestions, not code.
- **No frontend work** (CSS themes, Metro SVG, charts, animations) before the user approves the backend handoff.
- **No rewrites of approved work** without reporting the reason first.
- **No partial work disguised as complete.** An unfinished item stays unchecked in `PROGRESS.md`.
- If this brief is ambiguous or conflicts with itself, ask. Do not guess silently.

## 14. Definition of Done (every task)

- [ ] Meets the acceptance criteria in section 8
- [ ] Follows size, layering and style rules in section 2
- [ ] Tests written and passing; coverage targets respected
- [ ] `ruff check` and `ruff format` clean
- [ ] Migrations generated, committed, and apply cleanly on a fresh database
- [ ] Docs updated (`PROGRESS`, `DECISIONS`, `BUGS` where relevant)
- [ ] Report delivered in the exact format of section 12

## 15. Defaults the agent uses unless the user changes them

| Topic | Default |
|---|---|
| Pass mark | 50% per questionnaire |
| Attempts | 1 per questionnaire |
| Grade bands | A 80+, B 65 to 79, C 50 to 64 |
| Admin accounts | Created only by `createsuperuser` |
| Email verification | Not required; admin approval is the control |
| Certificate PDF | ReportLab, formal landscape layout matching the approved design |
| Time zone | `Asia/Kolkata`, with `USE_TZ=True` |

## 16. Start here

Begin with **B0**. Before writing code, reply with a short plan for B0 in the section 12 format (status "Needs decision" only if something is unclear), then proceed.
