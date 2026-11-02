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

## ADR 023: Generated migration size and pre-merge cleanup (user authorized)
- **Context:** All three profiles migrations were first committed together in 1802c41; 0001 was not previously committed before 0002/0003 were generated. They ran only on disposable databases, never a persistent database.
- **Decision:** For B2.1, the user explicitly authorized replacing that pre-merge sequence with one clean 0001_initial from final models. The generated-migration 250-line exemption remains approved. Catalog and accounts migration history stays unchanged.
- **Consequences:** Profiles has only CreateModel operations with final storage and year validators, no AlterField operations. After merge into main the committed migration history is frozen.

## ADR 024: Explicit UTF-8 text I/O and local evidence
- **Context:** Implicit Windows text decoding corrupted punctuation in the earlier report and progress notes.
- **Decision:** Read and write repository text with explicit encoding="utf-8", without BOM. Use ASCII punctuation in new reports and verify all tracked/new text decodes as UTF-8 with no BOM. README starts from main; AGENTS points to PROGRESS for status.
- **Consequences:** The formerly committed docs/B2_GATE_OUTPUT.txt is removed from Git and retained as ignored local evidence under .local/reports/. New transcripts remain ignored; review reports stay in docs/.

## ADR 025: Production CSRF cookie is HttpOnly
- **Decision:** Set CSRF_COOKIE_HTTPONLY=True explicitly in production, alongside secure cookies and the default HttpOnly session cookie. The server-rendered forms use csrf_token; no application code reads the CSRF cookie with JavaScript.
- **Consequences:** Cookie access from scripts is unnecessary; a settings regression test enforces the production requirement.

## ADR 026: Retired subject selections preserve trainee history
- **Decision:** Deactivating a subject leaves existing trainee skills intact and visible. Form choices include active skills plus that trainee's existing retired skills. Saving preserves retired selections even if omitted from the POST, and the form help text states this. Only new skill selections require an active subject; active selections can still be deselected.
- **Consequences:** Older browser forms and unrelated profile edits cannot silently erase retired skills. A trainee cannot add an inactive skill selected by somebody else; the service revalidates independently of the form.

## ADR 027: Dedicated private storage and bounded image headers
- **Decision:** PrivateStorage uses PRIVATE_MEDIA_ROOT (default private_uploads/), independently of MEDIA_ROOT and STATIC_ROOT in dev and prod. No urls.py serves it. Pillow DecompressionBombWarning and DecompressionBombError both become form validation errors, using a local warnings context rather than changing process-global policy.
- **Consequences:** Private files are delivered only by the existing visibility-checked attachment route; Content-Type comes from the validated storage suffix, never the upload content_type header. Deployment operators must keep the private root outside public web-server aliases.

## ADR 028: Database email-race recovery
- **Decision:** Account writes run inside an inner atomic savepoint. After an IntegrityError rolls back that savepoint, the service rechecks case-insensitive email ownership; a collision becomes an email ValidationError. Unrelated integrity errors are re-raised.
- **Consequences:** The shared form coordinator displays an email field error with HTTP 200, while the original account data remains unchanged and the connection remains usable. The test inserts a real competing case variant after service full_clean, exercising the database constraint rather than mocking its exception.

## ADR 029: Shared HttpOnly CSRF cookie and storage isolation
- **Decision:** CSRF_COOKIE_HTTPONLY=True lives in base.py so dev, test and prod match. Server-rendered csrf_token fields require no JavaScript cookie reader.
- **Consequences:** Ignore rules protect media/, private_uploads/ and .local/; a before/after full-suite file inventory verifies that tests leave the real private storage unchanged.

## ADR 030: Course schema and eligible role references
- **Decision:** Course and Enrollment retain subject/trainer/trainee references with PROTECT; modules cascade with their course, and progress cascades with enrollment but protects modules. Named constraints enforce course date order, module order >=1, unique course/order, unique trainee/course and unique enrollment/module.
- **Consequences:** User role eligibility cannot be a database FK check. Shared account services re-read persisted role, approval and active state for trainer assignment and trainee participation. There is no course delete service or URL; enrolled courses are protected by their FK history.

## ADR 031: Course ownership and descriptive edits
- **Decision:** Trainers create/manage only their own courses and resources; trainer ownership is assigned from the actor automatically. Admin can assign any currently valid trainer and manage any record. Services accept the actor where needed to enforce ownership even outside views; views filter object access to 404. Publication uses separate POST actions, never mass-assigned form fields.
- **Consequences:** New courses and new subject assignments require active subjects. Existing retired-subject history can be edited without changing its subject. Course trainer/subject edits that would invalidate existing library associations are rejected until those resources are detached/reassigned, rather than silently corrupting the invariant.

## ADR 032: Unique enrollment and reactivation
- **Decision:** enroll checks an approved active trainee and a published course with an eligible trainer. ACTIVE repeats reuse their row; DROPPED resumes ACTIVE with progress retained; COMPLETED raises already completed. A unique constraint arbitrates races inside an inner atomic savepoint; only after rollback does the service retrieve the winning enrollment or raise a clean conflict error.
- **Consequences:** No duplicate participation or broken transaction is exposed. drop is owner-only and accepts ACTIVE -> DROPPED only. Enrolled trainees retain course visibility after unpublishing, including retained dropped history.

## ADR 033: Sequential station progress and deferred final completion
- **Decision:** complete_module requires the owner of an ACTIVE enrollment and a module from that course. Only the lowest incomplete module order can advance; repeating existing progress is idempotent and preserves its timestamp. Module deletion with progress is a domain error, including the FK-protection race.
- **Consequences:** B3 never sets enrollment status COMPLETED. evaluate_completion(enrollment) is reserved for B4/B5 when quizzes/completion rules exist; no placeholder or premature implementation is added in B3.

## ADR 034: Station-map handoff and query contract
- **Decision:** Frozen Line/Station dataclasses contain no lazy ORM objects. ACTIVE and COMPLETED enrollments only; dropped are excluded. Lines sort by subject ID; stations by course ID and module order. Progress is DONE, the first missing ACTIVE station CURRENT, later missing stations LOCKED; a COMPLETED enrollment renders all DONE. Two or more distinct skill subjects make an interchange.
- **Consequences:** One joined enrollment query and three prefetch queries bound populated maps at four queries. Empty enrollments may skip unnecessary prefetches. Tests prove four queries for 1 course x 2 modules x 1 skill and 8 courses x 7 modules x 3 skills.

## ADR 035: Private library associations and visibility
- **Decision:** A resource's optional course must belong to its trainer and subject; references use PROTECT. Approved users see published resources; owner/Admin also see drafts. Lists use select_related and twenty-item pagination with validated subject/kind filters.
- **Consequences:** A published resource does not grant access to unpublished course metadata; its course link is rendered only when course visibility permits it. File visibility remains the resource's own published/owner/Admin policy.

## ADR 036: Library signatures, limits and download behavior
- **Decision:** Reuse PrivateStorage and deconstructible UUID UploadPath. VIDEO accepts mp4 (ftyp at byte 4) or webm (EBML prefix), 200 MiB; PRESENTATION accepts pptx ZIP or pdf, 25 MiB; DOCUMENT accepts docx ZIP or pdf, 25 MiB. Limits/extensions live in settings; prefix validation is composable beside the existing validators. Office files are signature-checked only, never parsed, and served as attachments only.
- **Consequences:** Content-Type comes from validated extension, never browser MIME. Video streams inline; other kinds are attachments; all are private/no-store. Replaced/deleted files are removed after commit. Range requests are not implemented: long videos cannot seek until B7 deployment adds protected Range-capable delivery. The existing storage rollback/orphan limitation remains ADR 021.

## ADR 037: Shared domain feedback and global upload test isolation
- **Decision:** Course/resource services raise CapacityConnectError subclasses. Shared validated persistence converts model errors and DB constraint races after savepoint rollback; form/action coordinators render domain feedback without HTTP logic in services.
- **Consequences:** Temporary MEDIA_ROOT/PRIVATE_MEDIA_ROOT fixtures now live in root conftest.py, protecting cross-app resource factories as well as profile tests. The prior settings-loader test now inspects the configured environment rather than override-holder metadata; concrete DB/hasher/timezone assertions remain. Raw transcripts stay ignored in .local/reports/; phase reports use the user's compact nine-field format.

## ADR 038: Authorized B4 attempt status amendment
- **Decision:** User authorized Attempt.status as TextChoices IN_PROGRESS, SUBMITTED, TIMED_OUT, default IN_PROGRESS. Section 4 is amended in the first B4 commit; no other domain fields are added.

## ADR 039: Module order after first course progress
- **Decision:** Any course progress freezes every existing module order; titles and skills remain editable. New modules must append at max(order)+1. Module mutation and first progress share a course-first lock order, then enrollment/module locks, avoiding inconsistent ordering and lock cycles.
- **Consequences:** Violations are CourseRuleError; the three new regression cases failed before the fix. Unprogressed courses keep their prior order-edit behavior.

## ADR 040: Unpublished enrolled access and existing trainer reassignment
- **Decision:** Unpublishing forbids new enrollment but enrolled trainees retain course access, module progress and, in B4, assessment attempts while enrollment remains ACTIVE. The existing Admin CourseForm includes trainer and can reassign to a valid trainer; its existing library-association guard remains unchanged. No new reassignment feature is built.
- **Consequences:** Dedicated HTTP/service tests prove retained module access and the existing Admin reassignment; quiz access on unpublished courses is covered with B4. ACTIVE all-done station maps contain only DONE and no CURRENT.

## ADR 041: Assessment schema and atomic authoring
- **Decision:** All five B4 models inherit timestamps; every FK uses PROTECT and related_name. Database bounds, ordered questions, one correct option at most, one open attempt and unique answers supplement service validation. Exactly one correct option and 2..6 choices are validated together, atomically. QuestionInput groups text, options, zero-based correct_index and marks to respect the four-parameter limit; forms display a human one-based option number.
- **Consequences:** Only the five brief models and authorized status field are added. Draft deletion removes children explicitly; attempted history cannot be deleted. No approved migration is rewritten.

## ADR 042: Shared clock and inclusive elapsed-time limit
- **Decision:** Assessment services/selectors obtain time only from core.clock.now; each operation captures one instant. New starts require opens_at <= now < deadline. The elapsed submission limit is started_at + duration_minutes + ATTEMPT_GRACE_SECONDS (30); equality is on time and one microsecond later is late.
- **Consequences:** An unexpired existing attempt resumes even after the questionnaire deadline, because resuming creates no new start. A quiz started before the deadline may finish after it. No sleeps or JavaScript timing authority are used.

## ADR 043: Late submissions are rejected without grading
- **Decision:** Expiry produces TIMED_OUT, score/percent zero, passed False, submitted_at=now and no answers. Both a late POST and the explicitly requested expired-take GET finalize identically. This lazy-expiry GET is the user's explicit exception to POST-only state changes; all other assessment mutations require POST.
- **Consequences:** Expiry consumes an attempt. It is a normal stored outcome, not an exception. Subsequent submits return that outcome without changing timestamps or rows.

## ADR 044: Serialized starts, savepoint recovery and idempotent submissions
- **Decision:** A start locks the questionnaire and checks a freshly validated active/approved trainee with ACTIVE enrollment, including unpublished courses. All attempt statuses consume quota. An expired open attempt is finalized before evaluating a replacement; refusal is raised after the outer transaction commits so that the timeout survives. Partial uniqueness arbitrates competing open inserts; an inner savepoint permits recovery of the winner.
- **Consequences:** PostgreSQL row locks serialize starts and authoring. select_for_update is a no-op on SQLite; unique constraints remain the last defense, and SQLite simultaneous writes may still produce database-lock contention. Race tests reproduce real constraint collisions with controlled stale reads, rather than claiming a multi-process load test. submit_attempt has one outer atomic transaction containing validation, answer writes and grading; an inner write savepoint permits a unique-answer collision to return a finalized winner or raise a domain conflict. Final states are pure reads on repeat submissions, including HTTP. Submitting an already-started attempt requires its eligible owner; ACTIVE enrollment is checked when starting, not re-required to finish an existing attempt.

## ADR 045: Freeze grading terms from the first attempt
- **Decision:** Any attempt freezes questions, option identities/text/correctness, marks, pass_percent and duration. Scheduling and title stay editable; max_attempts can be raised but cannot be lowered after history exists. Questionnaire locks coordinate authoring with starts. The course trainer/subject guard also rejects edits that would make existing questionnaires disagree with their course.
- **Consequences:** Admin's existing trainer reassignment form remains usable for courses without conflicting library/assessment references; bulk reassignment of linked histories is deferred. An attempted questionnaire must retain its references. No completion logic or certificate issuance is implemented until B5.

## ADR 046: Safe paper and quota-dependent result disclosure
- **Decision:** paper_for returns frozen plain DTOs containing only IDs, question/option text, order and marks; its option SQL never selects is_correct. A trainee's questionnaire detail contains metadata only. Result selectors show right/wrong to the owner and reveal correct-option text only when all current attempts are used; owning trainers/Admin always receive it. Staff access follows current course ownership.
- **Consequences:** Hidden correctness never enters the paper/form context. Raising max_attempts hides correct-option text on later result reads but cannot undo answers a trainee already saw when their old quota was exhausted. Grade calculation trusts database flags only and validates the whole selection set before any answer write; unanswered questions create no rows. Decimal ROUND_HALF_UP to two places is compared to the pass threshold, without floats.

## ADR 047: Participation denominators and constant-query handoffs
- **Decision:** Per the user's answer, average_best_percent averages attempted trainees only; pass_rate is passed/attempted*100, both zero with no attempted trainees. Participation includes all recorded course enrollments, including zero-attempt and retained dropped/completed history; attempts_used counts every status and last_attempt_at is the latest started_at. Best percent is the maximum stored percent; passed requires a submitted passing attempt.
- **Consequences:** Participation returns plain row/statistic DTOs in two queries including authorization. next_deadlines_for and trainee_questionnaires each require one query for small and large datasets; departure rows are ACTIVE-only, future-deadline, remaining-quota and not-passed, ordered by deadline/ID with default limit five. The quiz list retains ACTIVE/COMPLETED enrollment metadata. Read-only has_passed and passed_questionnaire_ids are the B5 handoff.
