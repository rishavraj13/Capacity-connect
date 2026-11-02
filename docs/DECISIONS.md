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
- **Decision:** Ratified by reviewer; user may veto. Only attempted trainees enter either denominator. pass_rate_percent = passed * 100 / attempted, Decimal, two decimals, ROUND_HALF_UP, range 0..100, zero when nobody attempted. average_best_percent uses the same percentage unit and rounding over attempted trainees only. Participation includes all recorded course enrollments, including zero-attempt and retained dropped/completed history; attempts_used counts every status and last_attempt_at is the latest started_at. Best percent is the maximum stored percent; passed requires a submitted passing attempt.
- **Consequences:** Participation returns plain row/statistic DTOs in two queries including authorization. next_deadlines_for and trainee_questionnaires each require one query for small and large datasets; departure rows are ACTIVE-only, future-deadline, remaining-quota and not-passed, ordered by deadline/ID with default limit five. The quiz list retains ACTIVE/COMPLETED enrollment metadata. Read-only has_passed and passed_questionnaire_ids are the B5 handoff.

## ADR 048: Explicit statistics units without changing behavior
- **Decision:** User clarified that pass rate remains a 0..100 percentage; rename the plain dataclass field pass_rate to pass_rate_percent and update its template/tests. No migration or arithmetic change. ADR 047 attribution is reworded as requested; unspecified approval is described as proposed.
- **Consequences:** Tests pin 3/4=75.00, 1/3=33.33 and no attempts=0.00. Both percentage statistics use Decimal ROUND_HALF_UP.

## ADR 049: B5 carry-over coverage and derived ownership
- **Decision:** Remove the unreachable empty-total grading guard: ready quizzes have questions and positive marks. Remove draft-delete ProtectedError handlers: questionnaire locks serialize starts and the existing no-attempt guard prevents protected history; no supported service creates cross-questionnaire answers. Cover the public owned_attempts eligibility guard directly and test the real aware clock.
- **Decision:** Admin course reassignment updates derived questionnaire trainers in the same transaction, through the assessment write boundary. Library trainer ownership remains independent: count conflicting linked resources and require Admin to relink/unlink them. Assessment subject changes remain guarded.
- **Consequences:** No schema change or bulk reassignment feature. Both reassignment regressions failed first. Courses and assessment grading obtain time only from core.clock.

## ADR 050: Feedback identity, eligibility and race-safe edits
- **Decision:** One Feedback row per author/target; course opinions require any retained enrollment status and resource opinions require current published visibility. Only active approved trainees submit or delete their own opinions. Rating and comment validators run at the service boundary; stripped comments may be blank. Unique collisions recover in a savepoint and apply the newest requested opinion to the winning row.
- **Consequences:** Owning trainers receive comment/rating DTOs with author_name=None; Admin sees author names. No anonymous promise applies to self-identifying text in comments. Templates escape comments. Summary distribution uses one query and exact integer/Decimal ROUND_HALF_UP averages; staff pagination uses three queries for both small and large datasets, twenty rows per page. The public permission-row helper extends existing matrix machinery without changing private behavior.

## ADR 051: Completion policy and import direction
- **Decision:** courses.completion.evaluate_completion is the only completion entry; there are no signals. ACTIVE enrollments require at least one module, all progress, and submitted passing outcomes for all ready questionnaires. Starts and completion share assessments.readiness.ready_questionnaires, a single SQL predicate for nonempty quizzes whose questions have 2..6 options and exactly one correct option. Zero ready quizzes permits completion without a certificate. A missed quiz deadline leaves enrollment ACTIVE; completed records never revert when content is added later.
- **Consequences:** complete_module, passing on-time submit_attempt and dropped-enrollment reactivation call the same entry. The conditional ACTIVE-to-COMPLETED update arbitrates repeat/racing triggers. Course/assessment write modules lazily call completion; completion imports certificate issuance and completion selectors; selectors consume assessment read contracts; certificate averaging consumes assessment read contracts, never assessment writes. These imports form an acyclic top-level module graph; lazy trigger adapters avoid partially initialized write modules and never call themselves recursively. Import graph and fresh-process import-order checks are gate evidence. CompletionStatus uses two queries for small/large datasets and appears as 'What is left' on the course page.

## ADR 052: Isolated certificate failures and explicit retry
- **Decision:** Completion evaluation runs in its own atomic savepoint inside a triggering write. Certificate rendering/storage wraps specific expected OSError, ValueError, TypeError and ReportLab PDFError failures in CertificateGenerationError, logs via logging.exception at completion, and rolls back only that evaluation. Identifier retry exhaustion is also a generation failure. Progress/grades remain durable; enrollment stays ACTIVE with no partial certificate row. A newly stored file is deleted if saving its reference fails. A secondary delete OSError also becomes CertificateGenerationError, preserving the trigger; the logged error requests operator cleanup when the filesystem refuses deletion.
- **Consequences:** evaluate_completions streams ACTIVE enrollments, uses the same completion entry, and reports checked/completed/certificates/failed. It is the explicit idempotent retry path; no signal or background job duplicates completion rules. General outer transaction/storage rollback limitations still apply; no transaction can make filesystem storage fully transactional. SQLite row locks remain no-ops; tests control stale reads/conditional collisions, not multi-process throughput.

## ADR 053: Ready-questionnaire averaging supersedes the earlier all-quiz rule
- **Decision:** Ratified by reviewer for B6 Step 0, superseding the earlier all-questionnaire denominator and zero substitution. Certificate average is the Decimal mean of each READY questionnaire's best SUBMITTED percent, ROUND_HALF_UP to two decimals. Draft/invalid questionnaires never affect it; a missing submitted grade (or no ready quiz on direct issuance) is a CertificateRuleError. No model or migration changes.
- **Consequences:** Completion and certificate averaging now use the same readiness predicate. GRADE_BANDS remains A >=80, B >=65, C >=50, D otherwise; D denotes completed below 50. Yearly CC-YYYY-NNNNN unique IDs, bounded savepoint retries and idempotent existing records remain unchanged. B5's denominator was historical and is superseded, not an approval claimed for this rule.

## ADR 054: Immutable private PDF and built-in font limitations
- **Decision:** Pure render_certificate_pdf takes a frozen CertificateData input. ReportLab Canvas(invariant=1,pageCompression=0) emits one landscape A4 page using built-in fonts, point-based layout coordinates, double outer/inner gold border, drawn roundel/seal, route dots and signatures. Unsupported cp1252 characters are replaced; Canvas handles literal PDF escaping. Long central text is fitted; signature labels are bounded. Names, course title, grade, date and verification URL are snapshotted into the stored PDF at issuance.
- **Consequences:** The stored PDF is the historical record; later profile/title edits do not rewrite it. Public verification uses current relational trainee/course names because the approved model has no name snapshot fields. Non-Latin names are not rendered correctly in PDFs; fix in B7 with a bundled Unicode font, needs user approval. PrivateStorage/UploadPath restrict storage to UUID .pdf paths; downloads authorize the trainee, current course trainer or Admin, with attachment/application/pdf/private,no-store. Authorized staff participant rows annotate certificate links without extra queries. The fake-data sample lives only in ignored .local/samples/.

## ADR 055: Public verification and environment configuration
- **Decision:** Public safe-method /verify/ and /verify/<id>/ require no login. Malformed/unknown identifiers share the same 404 body. The detached public DTO exposes only valid status, ID, trainee full name, course title and issue date; no email, score or grade. GET responses include noindex and no-referrer headers. Sequential IDs are enumerable; rate limiting is planned for B7.
- **Consequences:** SITE_BASE_URL defaults to the dev origin in base settings but production requires an explicit environment value. Signatory name/title are environment-driven and documented in .env.example. No new dependency, public PDF URL, revocation or email workflow is introduced. New feedback/certificate migrations were regenerated before first commit after a validator adjustment; only disposable test databases had used them, and no migration on main was edited.

## ADR 056: B6 attribution and carry-over proof
- **Decision:** Proposed by agent: attribution in future ADRs uses 'ratified by reviewer' or 'proposed by agent' unless a dated verbatim user quotation is included. ADR 047 already uses reviewer ratification; ADR 053 is superseded as above. Uncovered bounds, long PDF text and real constraint/ownership races receive explicit tests without coverage exclusions. The sample's font dictionaries list only Helvetica/Times standard families; no Symbol substitution is present.
- **Consequences:** Public verification shows the current name of the trainee, while the stored PDF keeps the name from issuance; a rename makes them differ. This remains an explicit known issue. No approved migration is edited.

## ADR 057: Trainer-only competency declarations
- **Decision:** Ratified by reviewer: only the currently active approved owning TRAINER declares, edits or removes competencies; Admin may inspect rankings but cannot edit declarations. New declarations require an active subject. Retired-subject declarations remain visible/editable, and their subject cannot change. Model bounds are proficiency 1..5, experience 0..60, with protected references and unique trainer/subject.
- **Consequences:** Shared validated persistence reports validation/unique races as domain errors after savepoint rollback. Form whitelists exclude owner and immutable subject from updates. Query ownership filters return 404 for another trainer's IDs; no new reassignment feature is added.

## ADR 058: Ranking population, formula and exact ordering
- **Decision:** Ratified by reviewer: ratings are ALL feedback rows on the trainer's courses/resources in the ranked subject, including unpublished targets. Combine sums/counts across targets rather than averaging target averages. No ratings means avg_rating=None, rating_count=0 and zero rating contribution. Only active approved users whose current role is TRAINER and who have a competency in the subject are eligible; retired subjects remain rankable. Experience is that competency's years, capped at ten for scoring.
- **Consequences:** Decimal weights .40/.30/.30 live in constants. Scores use a 50-digit local Decimal context; sorting by the unquantized score occurs inside that context, then published course count in the ranked subject desc, then trainer ID asc. Only displayed score is quantized to four places ROUND_HALF_UP. Ranks are sequential positions. One joined/correlated query returns every trainer, rating sum/count and distinct published course count; small/large query tests assert one. No competency/profile fields are synthesized from other apps.

## ADR 059: Manual public announcements and publication lifecycle
- **Decision:** Ratified by reviewer: all four announcement categories are manually authored Admin posts. Announcements are public. Publishing a draft stamps clock.now; publishing an already-published item is a pure no-op. Unpublishing hides immediately and retains the last timestamp; republishing obtains a fresh timestamp. Text/category edits do not implicitly publish or restamp.
- **Consequences:** The new public root homepage replaces the previously unmatched root route; existing role landing names/paths are unchanged. Anonymous visitors receive published board items and login/signup/verify links; authenticated visitors get the same board and their role landing link. Text is escaped; line breaks are the only body formatting. A SQL row-number window limits newest items independently per category, ordered by timestamp/ID descending, with categories in TextChoices order. Board queries stay at one for populated small/large sets; nonpositive limits return empty category tuples without SQL. Private Admin lists paginate twenty rows, include drafts and preserve filters across pages. No public draft detail/list route or cross-app automatic announcements exist.

## ADR 060: Database dashboard aggregates and participation cohort
- **Decision:** Ratified by reviewer: Admin figures count active users by role; pending approvals count active unapproved users, excluding rejected/inactive accounts. Enrollment/status totals include all retained enrollments; line load includes every active subject, even zero-load subjects, sorted by total enrollment desc then name/ID. Certificate grade buckets include zeros. Assessment statistics use only SUBMITTED attempts, group by trainee/questionnaire in SQL, take MAX(percent) per pair and aggregate those groups in SQL; no pair rows are iterated in Python. Pair passing uses MAX of the persisted passed flag, equivalent to the best attempt's passing state because grading terms are frozen after the first attempt.
- **User quotation (2026-11-02):** "Use the enrolled cohort (Recommended)"
- **Consequences:** The quotation answers the participation denominator question. Enrolled trainees are distinct users with an ACTIVE/COMPLETED enrollment. Attempted trainees for participation are the subset with a submitted attempt; the rate remains within 0..100. Assessment pair statistics retain all submitted historical pairs, including dropped-only history. Empty averages/rates return Decimal 0.00; nonempty means/rates round half up to two places. AdminDashboard uses nine queries regardless of source dataset size.

## ADR 061: Trainer dashboard and shared percentage handoff
- **Decision:** Proposed by agent: TrainerDashboard exposes own courses only, counts non-dropped enrollment, ACTIVE/COMPLETED separately, certificates and questionnaires. Course ratings use course feedback rows only, with None for no ratings; total rating average is weighted over feedback rows. Independent correlated sum/count subqueries avoid multiplying rating weights through enrollment joins. A second global own-quiz read provides direct links to the existing questionnaire participation page.
- **Consequences:** TrainerDashboard stays at two queries for small/large datasets; no trainer ID is accepted from GET. Admin and trainee are refused by its view. The existing pure grading percent helper moves to core.percentages and all callers use it; the B6 empty-denominator contract adds a 0.00 guard, with nonempty grading behavior unchanged. Fixed SQL-query budgets are verified by tests, and all dashboard DTOs contain eager plain data. No dashboards models, seed command, chart, export, email or CSS is added in B6.

## ADR 062: B7 carry-over and stable assessment read imports
- **Decision:** Proposed by agent: assessment reads move unchanged into authoring_selectors, usage_selectors and attempt_selectors; selectors.py reexports the same public functions. Existing paper/result/participation modules remain unchanged. No behavior or migration change.
- **Consequences:** Before the move, 1749 tests passed and every module/branch was covered. Dedicated real tests cover a passing submit after drop and an unmet retry candidate. ADR 060 already states that assessment statistics include all submitted historical pairs, including dropped-only history, while participation uses the ACTIVE/COMPLETED enrolled cohort; B7 preserves that rule.

## ADR 063: Explicit public Django admin login audit exception
- **User quotation (2026-11-02):** "Allow admin:login explicitly (Recommended)"
- **Decision:** Proposed by agent, with the quoted answer: the route audit includes admin:login explicitly in its public allowlist. Every other built-in admin route must still deny or redirect an anonymous request, and every application private route must declare role metadata as well as deny anonymous access.

## ADR 064: Cache-based anti-abuse controls and proxy trust
- **Decision:** Proposed by agent: fixed windows use clock.now, hashed identity keys and cache.add/incr. Five failed pair logins or twenty IP failures fill a fifteen-minute window; the next request is blocked. Successful login resets only the pair. Signup counts five handler requests/hour, verification thirty/minute. Unknown and known accounts receive the same bare 429 and Retry-After. The built-in admin login uses the same helper.
- **Consequences:** Development/test use LocMem; production requires DatabaseCache and createcachetable. DatabaseCache increments are not atomic: limits are best-effort anti-abuse, not a security boundary. ADR 011's deferred throttling is implemented here. REMOTE_ADDR is authoritative unless an explicitly trusted hop count is configured; forwarded HTTPS trust is separately opt-in.

## ADR 065: Production headers, deployment and admin role enforcement
- **Decision:** Proposed by agent: CSP lives in one setting; frontend font/style needs will be reviewed later. HSTS defaults stay 3600 seconds with include-subdomains/preload off until HTTPS is verified. Deployment documents opt-in one-year HSTS and runs a zero-warning go-live check. HttpOnly cookies, bare error pages and secret-free warning logs are enforced.
- **Consequences:** Django's staff flag alone was insufficient for the approved role contract (BUG 022). Both admin authentication and admin-site permission checks require active approved ADMIN as well as staff. Signup unique username/email errors and awaiting-approval login messages remain intentional disclosures.

## ADR 066: Service-driven demo fixture and safe orphan maintenance
- **User quotation (2026-11-02):** "PNG profile photo; PDF library resources (Recommended)"
- **Decision:** Proposed by agent, with the quoted answer: generated Pillow PNG is a profile photo and ReportLab PDFs are library resources. Existing upload rules remain. Seed uses real services, one public development password, a final marker and a transaction; repeating a complete seed changes no rows/timestamps. A scoped clock override creates a real expired attempt through normal services without database timestamp edits.
- **Consequences:** Production seeding requires --force. Database transactions cannot roll back external file writes after an interrupted seed; aged orphan cleanup is the explicit recovery tool. Cleanup is dry-run, age-gated, confined to resolved storage roots and rechecks all model FileField references before unlinking. Use a maintenance window because filesystem and database operations cannot be atomic together.

## ADR 067: Measured query budgets and authorised indexes
- **Decision:** Proposed by agent: rendered-page tests warm framework metadata then compare small/large data with authentication included. All 33 page budgets remain constant. SQLite plans on 2000 rows per table justify partial published-course and public-announcement indexes, enrollment status and questionnaire deadline indexes; one new migration per affected app contains AddIndex only. Attempt already uses its questionnaire FK index and needs no new one.
- **Consequences:** The published-course plan remains a scan of a smaller partial index (40 entries), not a search; no timing claim is made. PostgreSQL review is static only, not run against PostgreSQL. Environment reads are checked against .env.example and documented exhaustively.
