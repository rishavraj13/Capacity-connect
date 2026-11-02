PHASE / TASK: B7 Hardening (including Step 0)

STATUS: Done

GOAL: Complete the backend security, query, settings and operational gate before reviewer approval.

WHAT CHANGED: B6 merged into main and tagged b6-approved; work is on phase/b7-hardening. First B7 commit d9221ad covers the two completion branches and splits assessment readers without changing public imports. Core adds cache throttles, trusted-proxy parsing, CSP, seed and orphan maintenance. Accounts/admin enforce approved ADMIN access; BUG 022 records failing tests before the fix. Shared forms add certificate name help. Production gains DatabaseCache, logging, configurable admin path and documented go-live settings. Four measured indexes are the only model changes, in three new AddIndex-only migrations. No dependency or approved migration changed. README, deployment catalogue, ADRs and progress are updated.

HOW IT WAS VERIFIED:

Step 0 before split: 1749 passed in 20.43s; after: 1749 passed in 21.89s. After coverage: 3322 statements, 418 branches, zero misses, 100%. ADR 060 explicitly includes dropped trainees' submitted attempts in assessment aggregates, while participation uses ACTIVE/COMPLETED enrollment.

Final gate (real output; full transcripts ignored under .local/reports/B7_GATE_OUTPUT.txt):

`python -m pytest` (exit 0):

```text
============================ 1962 passed in 22.91s ============================
```

`python -m coverage run -m pytest` (exit 0):

```text
============================ 1962 passed in 22.93s ============================
```

`python -m coverage report -m` (exit 0):

```text
TOTAL                                                       3770      0    510      0   100%
```

`python -m ruff check .` (exit 0):

```text
All checks passed!
```

`python -m ruff format --check .` (exit 0):

```text
343 files already formatted
```

`python manage.py makemigrations --check` (exit 0):

```text
No changes detected
```

`python manage.py migrate --noinput` (exit 0):

```text
Operations to perform:
  Apply all migrations: accounts, admin, announcements, assessments, auth, catalog, certificates, competency, contenttypes, courses, feedback, library, profiles, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying accounts.0001_initial... OK
  Applying accounts.0002_user_unique_lower_email... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying announcements.0001_initial... OK
  Applying announcements.0002_announcement_announcement_public_board_idx... OK
  Applying catalog.0001_initial... OK
  Applying courses.0001_initial... OK
  Applying assessments.0001_initial... OK
  Applying assessments.0002_questionnaire_quiz_deadline_pk_idx... OK
  Applying certificates.0001_initial... OK
  Applying competency.0001_initial... OK
  Applying courses.0002_course_course_published_pk_idx_and_more... OK
  Applying library.0001_initial... OK
  Applying feedback.0001_initial... OK
  Applying profiles.0001_initial... OK
  Applying sessions.0001_initial... OK
```

`python manage.py check` (exit 0):

```text
System check identified no issues (0 silenced).
```

`python -m pip check` (exit 0):

```text
No broken requirements found.
```

`python manage.py check --deploy --settings=config.settings.prod` (exit 0):

```text
System check identified no issues (0 silenced).
```

Coverage: every measured application module is 100%; all 3770 statements and 510 branches covered, no exclusions added. Production settings are checked in isolated subprocesses because configuration is outside application coverage. Go-live check used a freshly generated strong secret, localhost/127.0.0.1 hosts, https://capacity.example, HSTS=31536000, include-subdomains=True and preload=True. No persistent DB was used for fresh migrations or seed proofs.

Section 11 evidence (all eight items):

PASS: DEBUG=False, ALLOWED_HOSTS, secure/HttpOnly cookies, CSRF and HSTS: apps/core/tests/test_environment_catalogue.py::test_production_defaults_and_opt_in_proxy; apps/accounts/tests/test_settings.py; apps/core/tests/test_csrf.py; zero-issue production deploy check.

PASS: manage.py check --deploy shows no warnings: System check identified no issues (0 silenced), go-live environment above.

PASS: Password validators on; no secrets in repository: four validators in base; git grep secret-pattern scan reviewed: 42 matches are environment reads, public placeholders/test credentials and documentation; no live secrets found; .env ignored.

PASS: Explicit view roles and ownership: apps/core/tests/test_route_audit.py: 147 passed; app permission/IDOR suites; public admin:login exception ADR 063.

PASS: Normal forms cannot set role/is_approved: apps/accounts/tests/test_forms.py and apps/profiles/tests/test_forms.py privileged-field/mass-assignment tests.

PASS: Validated uploads; media never executed or publicly served: apps/core/tests/test_uploads.py; apps/library/tests/test_uploads.py; apps/profiles/tests/test_files.py; private-storage route tests and no media/static URL alias.

PASS: Login and signup rate-limited: apps/core/tests/test_throttle.py: pair/IP thresholds, rollover, success reset, forged header, enumeration shape, signup/verify and admin login.

PASS: No list-page N+1: apps/core/tests/test_page_queries.py::test_every_page_has_constant_queries: 33 SMALL/LARGE rendered response checks.

Exact security test nodes (paths under apps/core/tests/):

- `test_throttle.py::test_fixed_window_threshold_and_rollover`
- `test_throttle.py::test_cache_keys_hash_every_identity_and_handle_eviction`
- `test_throttle.py::test_forwarded_ip_is_ignored_unless_explicitly_trusted`
- `test_throttle.py::test_login_pair_limit_different_name_and_ip_remain_independent`
- `test_throttle.py::test_login_ip_limit_spans_usernames`
- `test_throttle.py::test_success_resets_pair_but_not_ip_counter`
- `test_throttle.py::test_unknown_and_existing_users_have_identical_429_and_safe_log`
- `test_throttle.py::test_signup_and_verify_handler_limits`
- `test_throttle.py::test_django_admin_login_uses_the_same_failure_limit`
- `test_route_audit.py::test_every_route_declares_access_and_denies_anonymous_unless_public`
- `test_route_audit.py::test_every_state_action_returns_405_on_get`
- `test_route_audit.py::test_audit_rejects_new_route_without_role_check`
- `test_route_audit.py::test_route_names_are_unique_for_reliable_auditing`
- `test_security.py::test_security_headers_on_public_and_authenticated_pages`
- `test_security.py::test_bare_403_and_404_and_old_admin_path_with_debug_false`
- `test_security.py::test_permission_denial_is_logged_without_sensitive_data`
- `test_security.py::test_name_help_text_does_not_reject_non_latin_names`
- `test_admin_security.py::test_unapproved_or_demoted_staff_cannot_authenticate_or_open_admin`
- `test_admin_security.py::test_approved_admin_login_still_works`
- `test_demo_seed.py::test_demo_seed_is_idempotent_with_all_requested_states`
- `test_demo_seed.py::test_seed_requires_debug_and_explicit_production_force`
- `test_demo_seed.py::test_demo_account_builders_reuse_existing_namespace_accounts`
- `test_demo_seed.py::test_seed_command_help_and_validation_error`
- `test_orphans.py::test_cleanup_dry_run_delete_and_reference_age_guards`
- `test_orphans.py::test_cleanup_rechecks_references_created_after_scan`
- `test_orphans.py::test_cleanup_rejects_negative_age_and_handles_empty_roots`

Query counts include authentication/templates after framework-metadata warmup. SMALL is the initial fixture; LARGE adds nine related rows via each page recipe.

| Page | SMALL | LARGE |
|---|---:|---:|
| accounts pending | 3 | 3 |
| accounts users | 4 | 4 |
| admin dashboard | 11 | 11 |
| announcements home | 1 | 1 |
| announcements manage | 4 | 4 |
| assessment authoring detail | 5 | 5 |
| assessment authoring list | 4 | 4 |
| assessment detail | 3 | 3 |
| assessment history | 3 | 3 |
| assessment participation | 6 | 6 |
| assessment result | 7 | 7 |
| assessments mine | 4 | 4 |
| catalog list | 4 | 4 |
| certificates mine | 3 | 3 |
| competency mine | 3 | 3 |
| competency ranking | 5 | 5 |
| course detail | 9 | 9 |
| course feedback admin | 7 | 7 |
| course feedback trainer | 7 | 7 |
| courses list | 3 | 3 |
| feedback mine | 3 | 3 |
| library detail | 4 | 4 |
| library list | 5 | 5 |
| my courses | 3 | 3 |
| participants | 4 | 4 |
| profile directory | 4 | 4 |
| public verification | 1 | 1 |
| resource feedback admin | 7 | 7 |
| resource feedback trainer | 7 | 7 |
| station map | 6 | 6 |
| trainee detail | 8 | 8 |
| trainer dashboard | 4 | 4 |
| trainer detail | 3 | 3 |

SQLite EXPLAIN QUERY PLAN, 2000 rows per table (40 published courses, 200 active enrollments):

`Course published/PK`:

```text
BEFORE
3 0 216 SCAN courses_course
AFTER
4 0 212 SCAN courses_course USING INDEX course_published_pk_idx
```

`Enrollment status/PK`:

```text
BEFORE
3 0 216 SCAN courses_enrollment
AFTER
4 0 62 SEARCH courses_enrollment USING INDEX enrollment_status_idx (status=?)
```

`Questionnaire future deadline`:

```text
BEFORE
3 0 216 SCAN assessments_questionnaire
22 0 0 USE TEMP B-TREE FOR ORDER BY
AFTER
4 0 202 SEARCH assessments_questionnaire USING INDEX quiz_deadline_pk_idx (deadline>?)
```

`Attempt status/questionnaire`:

```text
BEFORE
4 0 61 SEARCH assessments_attempt USING INDEX assessments_attempt_questionnaire_id_91d0ac4e (questionnaire_id=?)
AFTER
4 0 61 SEARCH assessments_attempt USING INDEX assessments_attempt_questionnaire_id_91d0ac4e (questionnaire_id=?)
```

`Announcement public/category/newest`:

```text
BEFORE
3 0 216 SCAN announcements_announcement
21 0 0 USE TEMP B-TREE FOR ORDER BY
AFTER
4 0 61 SEARCH announcements_announcement USING INDEX announcement_public_board_idx (category=?)
```

Course still scans a partial index containing 40 entries, rather than the 2000-row table. Attempt already uses its questionnaire FK index, so no index was added there. No timing claim or PostgreSQL plan is inferred.

Seed idempotency: test compares every stored row/value, timestamps and file keys as well as identical command output. First/second counts:

| Model | First | Second |
|---|---:|---:|
| admin.LogEntry | 0 | 0 |
| auth.Permission | 108 | 108 |
| auth.Group_permissions | 0 | 0 |
| auth.Group | 0 | 0 |
| contenttypes.ContentType | 27 | 27 |
| sessions.Session | 0 | 0 |
| accounts.User_groups | 0 | 0 |
| accounts.User_user_permissions | 0 | 0 |
| accounts.User | 16 | 16 |
| catalog.Subject | 4 | 4 |
| catalog.Skill | 8 | 8 |
| profiles.TraineeProfile_skills | 12 | 12 |
| profiles.TraineeProfile | 12 | 12 |
| profiles.Qualification | 0 | 0 |
| profiles.WorkExperience | 0 | 0 |
| profiles.ExternalCertificate | 0 | 0 |
| profiles.TrainerProfile | 3 | 3 |
| courses.Course | 5 | 5 |
| courses.Module_skills | 16 | 16 |
| courses.Module | 15 | 15 |
| courses.Enrollment | 12 | 12 |
| courses.ModuleProgress | 9 | 9 |
| library.LibraryResource | 2 | 2 |
| assessments.Questionnaire | 2 | 2 |
| assessments.Question | 1 | 1 |
| assessments.Option | 2 | 2 |
| assessments.Attempt | 3 | 3 |
| assessments.AttemptAnswer | 2 | 2 |
| feedback.Feedback | 4 | 4 |
| certificates.Certificate | 1 | 1 |
| competency.TrainerCompetency | 6 | 6 |
| announcements.Announcement | 5 | 5 |

Cleanup command proof with real temporary files:

```json
{
  "dry_run": "C:\\Users\\risha\\AppData\\Local\\Temp\\pytest-of-risha\\pytest-103\\test_cleanup_dry_run_delete_an0\\private\\orphan.pdf\nC:\\Users\\risha\\AppData\\Local\\Temp\\pytest-of-risha\\pytest-103\\test_cleanup_dry_run_delete_an0\\public\\orphan.png\norphans=2 deleted=0 dry_run=True\n",
  "delete": "C:\\Users\\risha\\AppData\\Local\\Temp\\pytest-of-risha\\pytest-103\\test_cleanup_dry_run_delete_an0\\private\\orphan.pdf\nC:\\Users\\risha\\AppData\\Local\\Temp\\pytest-of-risha\\pytest-103\\test_cleanup_dry_run_delete_an0\\public\\orphan.png\norphans=2 deleted=2 dry_run=False\n",
  "referenced_preserved": true,
  "recent_preserved": true
}
```

All three operational commands --help exited 0; transcript B7_COMMAND_HELP.txt.

Size audit: no module >250, function >25, or view >15 logic statements; full wc-equivalent for every .py excluding migrations and AST inventory is in B7_GATE_OUTPUT.txt. UTF-8/no-BOM audit found zero errors. Files are written with Path.write_text(..., encoding="utf-8"), avoiding Windows shell encoding defaults.

Files over 150 lines:

- `apps/accounts/tests/test_auth_views.py`: 166.
- `apps/accounts/tests/test_forms.py`: 193.
- `apps/accounts/views.py`: 157.
- `apps/assessments/authoring.py`: 164.
- `apps/assessments/models.py`: 193.
- `apps/assessments/services.py`: 183.
- `apps/assessments/tests/test_authoring.py`: 158.
- `apps/assessments/tests/test_grading.py`: 164.
- `apps/assessments/tests/test_selectors.py`: 179.
- `apps/assessments/tests/test_views.py`: 192.
- `apps/core/tests/test_throttle.py`: 174.
- `apps/courses/services.py`: 159.
- `apps/courses/tests/test_completion.py`: 201.
- `apps/courses/tests/test_course_services.py`: 157.
- `apps/dashboards/admin_selectors.py`: 160.
- `apps/dashboards/tests/test_selectors.py`: 179.
- `apps/profiles/tests/test_crud.py`: 155.

Only handwritten module over 200: apps/courses/tests/test_completion.py (201), retained because it is one cohesive completion workflow regression suite and remains below 250.

AST top five longest functions:

- 25 lines: `apps/library/tests/test_crud.py:42` `test_edit_replace_delete_forms_cleanup_files`.
- 25 lines: `apps/core/tests/test_environment_catalogue.py:40` `test_production_defaults_and_opt_in_proxy`.
- 25 lines: `apps/core/demo_learning.py:54` `demo_assessments`.
- 25 lines: `apps/certificates/services.py:60` `issue_certificate`.
- 25 lines: `apps/accounts/permissions.py:45` `role_required`.

Settings comparison: see docs/DEPLOYMENT.md table (base/shared, dev, test, prod). All environment reads exactly match .env.example, enforced by test_environment_example_and_documentation_match_settings. Static grep reviewed raw SQL, SQLite references, select_for_update, Lower, DecimalField and constraints: runtime application queries use ORM; SQLite locking is weaker, case matching/collation and concurrency require future PostgreSQL execution. PostgreSQL supports the used Decimal/Lower/partial constraints. Complete grep output: .local/reports/B7_SCAN_1.txt. git check-ignore confirms .env, media, private_uploads and .local/reports ignored. Secret scan output: B7_SCAN_0.txt; no private-key material found. Public demo/test credentials are intentional, not deployment credentials.

DECISIONS AND ASSUMPTIONS: ADRs 062–067. User quotation (2026-11-02): "Allow admin:login explicitly (Recommended)". User quotation (2026-11-02): "PNG profile photo; PDF library resources (Recommended)". Other new judgments are proposed by agent. DatabaseCache counters are best-effort/non-atomic; no account-global username lock. Clock override is scoped and restored. Cleanup deletion belongs in a maintenance window. CSP font/style adaptation awaits the frontend stage.

KNOWN ISSUES / RISKS: Not run against PostgreSQL. HSTS is 3600 s; include-subdomains and preload are intentionally off until HTTPS is verified (B7); documented go-live environment passes with one-year HSTS. Signup unique username/email errors and awaiting-approval login messages remain as specified. DatabaseCache limits are best-effort. Filesystem writes cannot roll back with a DB transaction; interrupted seeding can leave aged orphans. Concurrent filesystem/database operations require maintenance coordination. Large-video Range/X-Accel is documented, not implemented. Non-Latin names are accepted but the current PDF font has limited glyph coverage. Verification shows the current trainee name while an issued PDF preserves its original snapshot.

DEMO STEPS: From main after eventual approval/merge: create venv, install requirements/dev.txt, copy .env.example to .env and replace SECRET_KEY; migrate, createsuperuser, seed_demo_data, runserver. During review use phase/b7-hardening. Open /login/, courses and station map, assessments, certificate downloads/verification, resource PDFs, rankings and dashboards. Public development password: Demo-Connect-2026! (override DEMO_PASSWORD). Seed output:

```text
MODEL | ROWS
accounts.User | 16
admin.LogEntry | 0
announcements.Announcement | 5
assessments.Attempt | 3
assessments.AttemptAnswer | 2
assessments.Option | 2
assessments.Question | 1
assessments.Questionnaire | 2
auth.Group | 0
auth.Permission | 108
catalog.Skill | 8
catalog.Subject | 4
certificates.Certificate | 1
competency.TrainerCompetency | 6
contenttypes.ContentType | 27
courses.Course | 5
courses.Enrollment | 12
courses.Module | 15
courses.ModuleProgress | 9
feedback.Feedback | 4
library.LibraryResource | 2
profiles.ExternalCertificate | 0
profiles.Qualification | 0
profiles.TraineeProfile | 12
profiles.TrainerProfile | 3
profiles.WorkExperience | 0
sessions.Session | 0
USERNAME | ROLE | STATUS
demo_admin | ADMIN | approved
demo_trainee_aarav | TRAINEE | approved
demo_trainee_arjun | TRAINEE | approved
demo_trainee_dev | TRAINEE | approved
demo_trainee_diya | TRAINEE | approved
demo_trainee_ishaan | TRAINEE | approved
demo_trainee_kabir | TRAINEE | pending
demo_trainee_leela | TRAINEE | rejected
demo_trainee_meera | TRAINEE | approved
demo_trainee_nisha | TRAINEE | approved
demo_trainee_rohan | TRAINEE | approved
demo_trainee_sana | TRAINEE | approved
demo_trainee_tara | TRAINEE | pending
demo_trainer_ananya | TRAINER | approved
demo_trainer_kavita | TRAINER | approved
demo_trainer_vikram | TRAINER | approved
Demo password (development only): Demo-Connect-2026!
```

NEXT: Await reviewer "approved". B7 is not merged or tagged. Testing stage and frontend have not started.
