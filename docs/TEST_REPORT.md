# Testing stage evidence and requirements

T1–T7 verification is complete; see BACKEND_HANDOFF_REPORT.md for the final report. No frontend work. All evidence transcripts are UTF-8 under ignored .local/reports/.

## Requirements traceability

| ID | Requirement (verbatim) | Where implemented | Proving tests | Status |
|---|---|---|---|---|
| R1 | secure signup and login with three roles: Trainee, Trainer, Admin | accounts forms/services/permissions; Admin via createsuperuser | apps/accounts/tests/test_forms.py::test_signup_form_valid; apps/core/tests/journeys/test_failure_paths.py::test_j2_unapproved_wrong_role_and_rejected_session | Covered |
| R2 | Trainees create professional profiles with qualifications, work experience, interests, skills and certificates | profiles forms/services | apps/profiles/tests/test_services.py::test_child_save_delete_and_certificate_cleanup; apps/profiles/tests/test_services.py::test_trainee_skills_and_mass_assignment; apps/core/tests/test_t1_carryover.py::test_demo_has_professional_history_and_external_evidence | Covered |
| R3 | Trainees enroll in courses and access learning resources | courses/enrollment_services; library views | apps/core/tests/journeys/test_happy_path.py::test_j1_happy_path; apps/courses/tests/test_enrollment_services.py::test_enroll_requires_published_course_and_valid_trainer; apps/library/tests/test_permissions.py | Covered |
| R4 | Trainees attempt subject-wise MCQ assessments | assessments forms/services/usage_selectors; subject filter | apps/assessments/tests/test_subject_filter.py::test_mine_filters_questionnaires_and_departures_by_subject; apps/assessments/tests/test_boundaries.py; apps/core/tests/journeys/test_happy_path.py::test_j1_happy_path | Covered |
| R5 | Trainees provide feedback on courses and training content | feedback services/views | apps/feedback/tests/test_services.py; apps/core/tests/journeys/test_happy_path.py::test_j1_happy_path | Covered |
| R6 | Trainers manage their profiles | profiles services/views | apps/profiles/tests/test_services.py::test_trainer_update_and_photo_cleanup; apps/profiles/tests/test_crud.py | Covered |
| R7 | Trainers create questionnaires with deadlines | assessments authoring/forms | apps/assessments/tests/test_authoring.py; apps/assessments/tests/test_boundaries.py; apps/core/tests/journeys/test_happy_path.py::test_j1_happy_path | Covered |
| R8 | Trainers monitor trainee participation and performance | assessments participation/result selectors and views | apps/assessments/tests/test_selectors.py; apps/assessments/tests/test_idor.py; apps/dashboards/tests/test_selectors.py::test_trainer_dashboard_only_own_courses_and_weighted_totals | Covered |
| R9 | Trainers upload recorded lectures, presentations and study materials in a trainer library accessible to trainees | library forms/validation/services/views | apps/library/tests/test_uploads.py::test_valid_signatures_ignore_browser_mime; apps/library/tests/test_crud.py; apps/library/tests/test_permissions.py | Covered |
| R10 | Admin: user approval and role management | accounts services/admin views | apps/accounts/tests/test_admin_views.py; apps/accounts/tests/test_services.py; apps/core/tests/journeys/test_failure_paths.py::test_j2_unapproved_wrong_role_and_rejected_session | Covered |
| R11 | Admin dashboards for courses, enrollments, certifications, assessments and participation statistics | dashboards admin selectors | apps/dashboards/tests/test_selectors.py::test_admin_dashboard_exact_fake_dataset_numbers; apps/core/tests/journeys/test_happy_path.py::test_j1_happy_path | Covered |
| R12 | Admin publishes notifications, announcements, achievements and newly added learning content on the homepage | announcements services/board/views; manual NEW_CONTENT category | apps/announcements/tests/test_services.py::test_publish_idempotent_unpublish_retains_and_republish_restamps; apps/core/tests/journeys/test_happy_path.py::test_j1_happy_path | Covered |
| R13 | Competency mapping for identifying suitable trainers for various subjects | competency declaration/ranking selectors | apps/competency/tests/test_ranking.py::test_ranking_formula_examples_and_experience_cap; apps/core/tests/journeys/test_happy_path.py::test_j1_happy_path | Covered |
| R14 | Scalable, secure, user-friendly, accessible across devices | query budgets, constraints, ownership, security middleware; frontend deferred | apps/core/tests/test_page_queries.py::test_every_page_has_constant_queries; apps/core/tests/test_route_audit.py; security mapping below | Partial |

R9 covers backend file workflows, not browser playback. R14 backend bounded queries/security are verified; "user-friendly" and "accessible across devices" belong to the frontend stage and are NOT yet verified. No load/scaling proof is claimed.

R4 originally lacked grouped/filtered subject discovery. The reviewer authorised the subject filter on 2026-11-02: "Add subject filter, then continue (Recommended)" (ADR 069). It filters both list and departures, scoped to enrollment. R12 specifically supports Admin-authored NEW_CONTENT posts announcing library resources; J1 uploads a PDF then publishes such an announcement. It does not automatically publish library events (ADR 059).

## Security control mapping

| Control | Proving test nodes | Status |
|---|---|---|
| Authentication/password checks | accounts/tests/test_forms.py::test_login_form_wrong_password_gives_generic_message; test_login_form_approved_user_succeeds | Covered |
| Approval/rejection | accounts/tests/test_forms.py::test_login_form_unapproved_user_gives_awaiting_approval; core/tests/journeys/test_failure_paths.py::test_j2_unapproved_wrong_role_and_rejected_session | Covered |
| Roles/future routes | core/tests/test_route_audit.py::test_every_route_declares_access_and_denies_anonymous_unless_public; accounts/tests/test_permissions.py | Covered |
| Ownership/IDOR | core/tests/journeys/test_isolation.py::test_j3_url_walk_classifies_shared_reads_and_denies_cross_owner; profiles/tests/test_idor.py::test_other_trainee_history_and_files_are_hidden; courses/tests/test_idor.py; assessments/tests/test_idor.py | Covered |
| CSRF | core/tests/test_csrf.py::test_new_post_routes_enforce_csrf; core/tests/test_b3_csrf.py; assessments/tests/test_csrf.py | Covered |
| XSS escaping | announcements/tests/test_selectors.py::test_public_body_is_escaped_with_only_line_breaks; feedback/tests/test_selectors.py::test_trainer_anonymity_admin_identity_and_escaped_comments | Covered |
| Upload bytes/size/path abuse | core/tests/test_uploads.py; profiles/tests/test_upload_forms.py; library/tests/test_uploads.py::test_wrong_content_empty_and_oversize | Covered |
| Private files | profiles/tests/test_files.py::test_public_media_route_does_not_exist; profiles/tests/test_idor.py::test_other_trainee_history_and_files_are_hidden; certificates/tests/test_views.py::test_download_is_private_pdf_attachment_and_owner_only | Covered |
| Throttling/proxy trust | core/tests/test_throttle.py; core/tests/test_t1_carryover.py::test_proxy_uses_rightmost_client_and_ignores_forged_left_entry | Covered |
| Headers/CSP/cookies | core/tests/test_security.py::test_security_headers_on_public_and_authenticated_pages; core/tests/test_security_settings.py::test_shared_cookie_and_proxy_defaults | Covered |
| Admin path/approval/role | core/tests/test_security_settings.py::test_admin_path_is_environment_configurable; core/tests/test_admin_security.py | Covered |
| Logs without secrets | core/tests/test_throttle.py::test_unknown_and_existing_users_have_identical_429_and_safe_log; core/tests/test_security.py::test_permission_denial_is_logged_without_sensitive_data | Covered |
| Enumeration | accounts/tests/test_forms.py::test_login_form_status_leak_prevention; core/tests/test_throttle.py::test_unknown_and_existing_users_have_identical_429_and_safe_log | Covered; deliberate unique-signup and valid-password status messages remain |
| Privilege mass assignment | accounts/tests/test_forms.py::test_signup_form_privileged_field_injection_ignored; profiles/tests/test_forms.py::test_forms_have_no_privileged_fields | Covered |

All paths in this table are under apps/. Module references include all parametrized nodes; precise node inventories and execution output are in the transcripts. No named security control lacks tests.

## GAPS

- R4 subject discovery gap was approved and fixed separately (ADR 069); regression tests failed first.
- R14 is deliberately Partial: proposed default is to retain frontend usability/device/accessibility verification for the frontend stage, as already required. No frontend implementation is added.
- J3 classification was approved on 2026-11-02 and implemented as tests only (ADR 071). No unresolved backend requirement gap remains.

## What is not tested

PostgreSQL not run; no driver added. No multi-process, concurrency stress or load test. SQLite select_for_update is a no-op and does not prove PostgreSQL row-lock behavior. No browser, JavaScript, CSS, responsive design or accessibility verification: there is no frontend yet. No real email, proxy, TLS termination or external service is exercised. Filesystem/database operations are not transactional together; cleanup reference races cannot be eliminated by unit tests. Deployment is not exercised on a real server. Video tests validate upload formats/signatures, not browser playback, full codecs or malicious-file scanning. Range/X-Accel support is documented only. Certificate non-Latin glyph completeness is not solved; current-name verification can differ from an issued PDF snapshot. Cache limits are best-effort, not atomic across workers. Fresh-clone smoke uses the local Django development server, not a production host.

Operational note: behind one trusted reverse proxy set TRUSTED_PROXY_COUNT=1, otherwise all visitors share the proxy IP and can throttle each other. The proxy must sanitize forwarding headers; HTTPS proxy trust is separately opt-in. HSTS is 3600 s; include-subdomains and preload are intentionally off until HTTPS is verified; go-live checks use the documented strict environment.

## Final execution results

### Step 0

Qualification counts first/second: 3/3; work experiences: 3/3; external certificates: 2/2. Complete seed snapshots (every row/value, timestamps and file keys) and output are identical on rerun. Source: B7_SEED_PROOF.json regenerated by the T1 suite. Forced non-debug seed without explicit DEMO_PASSWORD failed first, then the guard was fixed; explicit credentials pass. Proxy defaults/forged-left-entry cases pass. Quiz take SMALL/LARGE: 10/10; participants: 4/4.

Installed top-level package versions (pip freeze; T1_VERSIONS.txt):

- Python 3.14.6
- Django 5.2.18
- django-environ 0.14.0
- Pillow 13.0.0
- ReportLab 5.1.0
- pytest 9.2.0
- pytest-django 4.14.0
- factory_boy 3.3.3
- coverage 7.17.0
- Ruff 0.17.3

### T1 fresh clone

Cloned into a new empty temporary directory; no working-tree files copied. Used the clone virtualenv Python explicitly (equivalent to activation), requirements/dev.txt, copied the clone .env.example, replaced only SECRET_KEY with a generated value, migrated and seeded (the authorised alternative to createsuperuser). Commands/results:

`git clone --branch phase/t1-testing C:\Django\Project C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n` (exit 0):

```text
Cloning into 'C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n'...
done.
```

`C:\Django\Project\venv\Scripts\python.exe -m venv venv` (exit 0):

```text

```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n\venv\Scripts\python.exe -m pip install -r requirements/dev.txt` (exit 0):

```text
-2.21.0 pytest-9.2.0 pytest-django-4.14.0 reportlab-5.1.0 ruff-0.17.3 sqlparse-0.6.1 tzdata-2026.6

[notice] A new release of pip is available: 26.1.2 -> 26.2.2
[notice] To update, run: C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n\venv\Scripts\python.exe -m pip install --upgrade pip
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n\venv\Scripts\python.exe manage.py migrate` (exit 0):

```text
g certificates.0001_initial... OK
  Applying competency.0001_initial... OK
  Applying courses.0002_course_course_published_pk_idx_and_more... OK
  Applying library.0001_initial... OK
  Applying feedback.0001_initial... OK
  Applying profiles.0001_initial... OK
  Applying sessions.0001_initial... OK
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n\venv\Scripts\python.exe manage.py seed_demo_data` (exit 0):

```text
proved
demo_trainee_rohan | TRAINEE | approved
demo_trainee_sana | TRAINEE | approved
demo_trainee_tara | TRAINEE | pending
demo_trainer_ananya | TRAINER | approved
demo_trainer_kavita | TRAINER | approved
demo_trainer_vikram | TRAINER | approved
Demo password (development only): Demo-Connect-2026!
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n\venv\Scripts\python.exe -m pytest` (exit 0):

```text
============================ 1984 passed in 35.68s ============================
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n\venv\Scripts\python.exe -m coverage run -m pytest` (exit 0):

```text
============================ 1984 passed in 35.53s ============================
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n\venv\Scripts\python.exe -m coverage report -m` (exit 0):

```text
TOTAL                                                       3817      0    522      0   100%
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n\venv\Scripts\python.exe -m ruff check .` (exit 0):

```text
All checks passed!
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n\venv\Scripts\python.exe -m ruff format --check .` (exit 0):

```text
361 files already formatted
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-clone-6kgrqy3n\venv\Scripts\python.exe manage.py check` (exit 0):

```text
System check identified no issues (0 silenced).
```

The tested source commit is fc844b5; subsequent changes are handoff documentation only. The clone runserver --noreload homepage returned HTTP 200, then the process was terminated. Full output: T1_CLONE_OUTPUT.txt. Requirements pin top-level versions; clone transitive sqlparse resolved 0.6.1 while the original environment has 0.6.0. Both passed; no transitive lockfile claim is made. The real installed package index was used; no package was added to requirements.

### T2 separate apps and orders

| App | Real summary |
|---|---|
| accounts | 123 passed in 2.17s |
| announcements | 23 passed in 0.87s |
| assessments | 320 passed in 3.98s |
| catalog | 105 passed in 1.39s |
| certificates | 173 passed in 2.51s |
| competency | 23 passed in 1.01s |
| core | 280 passed in 9.08s |
| courses | 276 passed in 3.79s |
| dashboards | 205 passed in 2.40s |
| feedback | 29 passed in 0.99s |
| library | 150 passed in 2.07s |
| profiles | 277 passed in 4.07s |

- REVERSE: 1984 passed in 34.74s.
- NORMAL_1: 1984 passed in 34.83s.
- NORMAL_2: 1984 passed in 33.61s.

Reverse run temporarily appended pytest_collection_modifyitems to conftest.py; original bytes restored in finally. Hook is not committed. Exact requested clock/sleep rg command returned exit 1 with no matches (T1_CLOCK_SCAN.txt); there are no matches to explain. Operational server-start polling outside the repo tests uses sleep; application tests do not.

### T3 hand-authored mutations

Each mutation was applied separately, relevant modules run, then git checkout -- <file> restored the source. git status --porcelain was asserted empty after every mutation. No mutation or temporary runner is committed. Initial selections for 4/5/6 missed the existing boundary module, and 16 missed the existing IDOR module; those were rerun with the correct modules. No unprotected rule remained, so no new mutation test was needed. Full outputs T1_MUTATION_01.txt through _20.txt.

| # | File:line | Mutation | Tests that failed | Result |
|---|---|---|---|---|
| 1 | apps/accounts/forms.py:101 | remove approval gate | apps/accounts/tests/test_forms.py::test_login_form_unapproved_user_gives_awaiting_approval<br>apps/accounts/tests/test_forms.py::test_login_form_status_leak_prevention | PROTECTED |
| 2 | apps/accounts/forms.py:91 | check status before password | apps/accounts/tests/test_forms.py::test_login_form_wrong_password_gives_generic_message<br>apps/accounts/tests/test_forms.py::test_login_form_status_leak_prevention | PROTECTED |
| 3 | apps/accounts/permissions.py:62 | allow any approved role | apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainer-trainee_home-GET]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_admin-trainee_home-GET]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainee-trainer_home-GET]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_admin-trainer_home-GET]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainee-admin_panel-GET]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainer-admin_panel-GET]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainee-admin_user_list-GET]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainer-admin_user_list-GET]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainee-admin_pending_list-GET]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainer-admin_pending_list-GET]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainee-admin_approve_user-POST]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainer-admin_approve_user-POST]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainee-admin_reject_user-POST]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainer-admin_reject_user-POST]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainee-admin_change_role-POST]<br>apps/accounts/tests/test_permissions.py::test_permission_matrix[approved_trainer-admin_change_role-POST] | PROTECTED |
| 4 | apps/assessments/services.py:73 | opens_at exclusive | apps/assessments/tests/test_boundaries.py::test_start_open_boundary[opens-exact] | PROTECTED |
| 5 | apps/assessments/services.py:73 | deadline inclusive | apps/assessments/tests/test_boundaries.py::test_start_deadline_boundary[deadline-exact] | PROTECTED |
| 6 | apps/assessments/rules.py:67 | exclude exact grace boundary | apps/assessments/tests/test_boundaries.py::test_submission_grace_boundary[grace-limit-exact] | PROTECTED |
| 7 | apps/assessments/grading.py:45 | trust client-selected option ID as correctness | apps/assessments/tests/test_grading.py::test_mixed_marks_wrong_and_unanswered_are_graded_from_database | PROTECTED |
| 8 | apps/core/percentages.py:3 | ROUND_DOWN | apps/assessments/tests/test_grading.py::test_half_up_rounding_and_all_unanswered<br>apps/core/tests/test_percentages.py::test_shared_percentage_units[1-32-3.13] | PROTECTED |
| 9 | apps/assessments/grading.py:67 | strict pass boundary | apps/assessments/tests/test_grading.py::test_exact_pass_percent_boundary[exact-threshold-passes] | PROTECTED |
| 10 | apps/assessments/services.py:77 | one extra attempt | apps/assessments/tests/test_attempts.py::test_all_final_statuses_consume_attempt_quota[SUBMITTED]<br>apps/assessments/tests/test_attempts.py::test_all_final_statuses_consume_attempt_quota[TIMED_OUT]<br>apps/assessments/tests/test_attempts.py::test_expired_open_finalization_commits_when_max_reached | PROTECTED |
| 11 | apps/courses/enrollment_services.py:41 | allow unpublished enrollment | apps/courses/tests/test_enrollment_services.py::test_enroll_requires_published_course_and_valid_trainer | PROTECTED |
| 12 | apps/courses/enrollment_services.py:98 | remove sequence gate | apps/courses/tests/test_enrollment_services.py::test_sequential_completion_is_idempotent_and_finishes_module_only_course | PROTECTED |
| 13 | apps/courses/completion_data.py:32 | ignore passing quizzes | apps/courses/tests/test_completion.py::test_last_passing_submit_completes_and_issues_once<br>apps/courses/tests/test_completion.py::test_exhausted_failed_quizzes_keep_enrollment_active<br>apps/courses/tests/test_completion.py::test_pdf_failure_preserves_passing_quiz_and_progress<br>apps/courses/tests/test_completion.py::test_missed_quiz_deadline_keeps_enrollment_active | PROTECTED |
| 14 | apps/certificates/constants.py:19 | B starts at 66 | apps/certificates/tests/test_services.py::test_certificate_grade_boundaries[65.00-B] | PROTECTED |
| 15 | apps/certificates/services.py:68 | remove certificate idempotency guards | apps/certificates/tests/test_services.py::test_idempotent_issuance_preserves_file_and_snapshot | PROTECTED |
| 16 | apps/profiles/views/files.py:33 | unfiltered private file lookup | apps/profiles/tests/test_idor.py::test_other_trainee_history_and_files_are_hidden[trainee]<br>apps/profiles/tests/test_idor.py::test_other_trainee_history_and_files_are_hidden[trainer] | PROTECTED |
| 17 | apps/announcements/selectors.py:23 | include drafts on board | apps/announcements/tests/test_selectors.py::test_drafts_and_unpublished_items_never_appear_on_public_home_or_board<br>apps/announcements/tests/test_views.py::test_admin_announcement_form_create_edit_publish_and_manage<br>apps/announcements/tests/test_views.py::test_non_admin_cannot_reach_any_draft_listing | PROTECTED |
| 18 | apps/competency/selectors.py:68 | remove experience cap | apps/competency/tests/test_ranking.py::test_ranking_formula_examples_and_experience_cap | PROTECTED |
| 19 | apps/core/throttle.py:59 | limit off by one | apps/core/tests/test_throttle.py::test_signup_and_verify_handler_limits[signup-SIGNUP_IP_LIMIT]<br>apps/core/tests/test_throttle.py::test_signup_and_verify_handler_limits[certificates:verify_form-VERIFY_IP_LIMIT]<br>apps/core/tests/test_throttle.py::test_fixed_window_threshold_and_rollover<br>apps/core/tests/test_throttle.py::test_cache_keys_hash_every_identity_and_handle_eviction | PROTECTED |
| 20 | apps/courses/selectors.py:32 | remove trainer management scope | apps/courses/tests/test_selectors.py::test_enrollment_and_participant_counts_have_one_query | PROTECTED |

### T4 journeys

Admin bootstrap is the only direct initial fixture write, equivalent to createsuperuser. Thereafter every signup, login, approval, content creation, upload and state change uses Client GET/POST. ORM reads assert results; core.clock is patched and storage is temporary. Journey nodes passed in the full suite:

- `apps/core/tests/journeys/test_failure_paths.py::test_j2_unapproved_wrong_role_and_rejected_session`: PASS.
- `apps/core/tests/journeys/test_failure_paths.py::test_j2_late_submission_and_third_attempt_refused`: PASS.
- `apps/core/tests/journeys/test_failure_paths.py::test_j2_module_skip_and_dropped_trainee_refused`: PASS.
- `apps/core/tests/journeys/test_happy_path.py::test_j1_happy_path`: PASS.
- `apps/core/tests/journeys/test_isolation.py::test_j3_url_walk_classifies_shared_reads_and_denies_cross_owner`: PASS.

J3 completed after the reviewer answered on 2026-11-02: "Classify shared reads explicitly (Recommended)" (ADR 071). Four parametrized HTTP walks cover all 59 integer-identifier app routes in both directions with trainer A/B and trainee A/B. Each issues 78 requests: 71 restricted requests returning 403/404, 5 shared reads returning 200 and 2 separately classified current-user participation actions. Total 312 requests. Three private-file kinds are exercised. Every target row exists and was created through HTTP. Snapshot comparisons prove protected requests leave all domain rows unchanged (sessions excluded); legitimate enrollment creates a distinct own ACTIVE row and preserves the target completed row. The URLconf inventory must exactly match bindings: unclassified new routes fail. Full route/method/status evidence: T1_J3_HTTP.json. Built-in admin routes and public string-ID verification retain route-audit/J1 coverage.

### Bugs and failing-first proof

- BUG 023: forced non-debug seed accepted public credentials. T1_STEP0_FAILING.txt: DID NOT RAISE CommandError. Fixed ce88e50; explicit env credential guard. Seed child history was separately authorised carry-over, not an unapproved feature.
- BUG 024: login/signup omitted non-field error rendering. T1_BUG024_FAILING.txt: three failing regressions. Fixed 7a88e7c; full suite T1_BUG024_PASS.txt: 1978 passed in 23.03s. Initial J2 saw an old signup flash; separate-client registration removed the masking message.
- R4 requirement gap: three HTTP regression cases failed (T1_R4_FAILING.txt), approved separately, fixed c333c5c.

### Standard verification gate

`python -m pytest` (exit 0):

```text
============================ 1984 passed in 31.10s ============================
```

`python -m coverage run -m pytest` (exit 0):

```text
============================ 1984 passed in 31.55s ============================
```

`python -m coverage report -m` (exit 0):

```text
TOTAL                                                       3817      0    522      0   100%
```

`python -m ruff check .` (exit 0):

```text
All checks passed!
```

`python -m ruff format --check .` (exit 0):

```text
361 files already formatted
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

Go-live environment used a unique generated SECRET_KEY (not logged), localhost/127.0.0.1 hosts, HTTPS SITE_BASE_URL, HSTS31536000/include-subdomains/preload True. Every measured module and all branches are 100%; no pragma added. Fresh migrate uses a disposable database. Complete transcript: T1_GATE_OUTPUT.txt. Size violations: []; UTF-8/no-BOM errors: [].

Files >150 lines:

- apps/accounts/tests/test_auth_views.py: 166.
- apps/accounts/tests/test_forms.py: 193.
- apps/accounts/views.py: 157.
- apps/assessments/authoring.py: 164.
- apps/assessments/models.py: 193.
- apps/assessments/services.py: 183.
- apps/assessments/tests/test_authoring.py: 158.
- apps/assessments/tests/test_grading.py: 164.
- apps/assessments/tests/test_selectors.py: 179.
- apps/assessments/tests/test_views.py: 192.
- apps/core/tests/journeys/isolation_data.py: 172.
- apps/core/tests/test_throttle.py: 174.
- apps/courses/services.py: 159.
- apps/courses/tests/test_completion.py: 201.
- apps/courses/tests/test_course_services.py: 157.
- apps/dashboards/admin_selectors.py: 160.
- apps/dashboards/tests/test_selectors.py: 179.
- apps/profiles/tests/test_crud.py: 155.

Only handwritten module >200: apps/courses/tests/test_completion.py, 201 lines; one cohesive completion regression suite, under the 250-line limit. Generated migrations exempt. Full wc-equivalent list for every project .py excluding migrations is in the gate transcript.

AST top ten:

- 25 lines: apps/library/tests/test_crud.py:42 test_edit_replace_delete_forms_cleanup_files.
- 25 lines: apps/core/tests/test_environment_catalogue.py:40 test_production_defaults_and_opt_in_proxy.
- 25 lines: apps/core/tests/journeys/isolation_data.py:148 _declarations.
- 25 lines: apps/core/demo_learning.py:54 demo_assessments.
- 25 lines: apps/certificates/services.py:60 issue_certificate.
- 25 lines: apps/accounts/permissions.py:45 role_required.
- 24 lines: apps/profiles/tests/test_crud.py:116 test_child_create_edit_delete.
- 24 lines: apps/profiles/tests/test_crud.py:20 test_trainee_profile_post_and_private_photo.
- 24 lines: apps/feedback/tests/test_views.py:53 test_csrf_required_for_submit_and_delete.
- 24 lines: apps/dashboards/tests/factories.py:11 analytics_dataset.

No production deployment, frontend work or testing-branch merge/tag has occurred. Final backend handoff is ready for reviewer approval.

## J3 parametrized node results

| Exact node under apps/core/tests/journeys/test_isolation.py | Requests | Result |
|---|---:|---|
| test_j3_url_walk_classifies_shared_reads_and_denies_cross_owner[0-staff] | 78 | PASS |
| test_j3_url_walk_classifies_shared_reads_and_denies_cross_owner[0-learner] | 78 | PASS |
| test_j3_url_walk_classifies_shared_reads_and_denies_cross_owner[1-staff] | 78 | PASS |
| test_j3_url_walk_classifies_shared_reads_and_denies_cross_owner[1-learner] | 78 | PASS |

All 59 app routes with pk, course_id or user_id are explicitly bound to actual existing objects. Built-in admin uses its separate audited policy, and public string-ID verification is covered by J1. Shared reads and own participation are recorded separately from forbidden cross-owner requests; no access rule was changed.

## Reproducible install follow-up (2026-11-03)

Tested commit d0483b7 on phase/t1-testing, in a new empty clone with its own virtualenv. No working-tree files were copied. requirements/constraints.txt was generated with pip freeze --all from the verified environment; all 20 installed distributions in the new clone match exactly, including pip 26.1.2 and sqlparse 0.6.0. No dependency was added or upgraded. Earlier unconstrained clone results above remain historical evidence. New installs must use constraints (ADR 072).

`git clone --branch phase/t1-testing C:\Django\Project C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do` (exit 0):

```text
Cloning into 'C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do'...
done.
```

`C:\Django\Project\venv\Scripts\python.exe -m venv venv` (exit 0):

```text

```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe -m pip install -r requirements/dev.txt -c requirements/constraints.txt` (exit 0):

```text
0 pytest-9.2.0 pytest-django-4.14.0 reportlab-5.1.0 ruff-0.17.3 sqlparse-0.6.0 tzdata-2026.6

[notice] A new release of pip is available: 26.1.2 -> 26.2.2
[notice] To update, run: C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe -m pip install --upgrade pip
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe manage.py migrate` (exit 0):

```text
g certificates.0001_initial... OK
  Applying competency.0001_initial... OK
  Applying courses.0002_course_course_published_pk_idx_and_more... OK
  Applying library.0001_initial... OK
  Applying feedback.0001_initial... OK
  Applying profiles.0001_initial... OK
  Applying sessions.0001_initial... OK
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe manage.py seed_demo_data` (exit 0):

```text
proved
demo_trainee_rohan | TRAINEE | approved
demo_trainee_sana | TRAINEE | approved
demo_trainee_tara | TRAINEE | pending
demo_trainer_ananya | TRAINER | approved
demo_trainer_kavita | TRAINER | approved
demo_trainer_vikram | TRAINER | approved
Demo password (development only): Demo-Connect-2026!
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe -m pytest` (exit 0):

```text
============================ 1984 passed in 28.53s ============================
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe -m coverage run -m pytest` (exit 0):

```text
============================ 1984 passed in 29.00s ============================
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe -m coverage report -m` (exit 0):

```text
TOTAL                                                       3817      0    522      0   100%
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe -m ruff check .` (exit 0):

```text
All checks passed!
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe -m ruff format --check .` (exit 0):

```text
362 files already formatted
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe manage.py makemigrations --check` (exit 0):

```text
No changes detected
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe manage.py check` (exit 0):

```text
System check identified no issues (0 silenced).
```

`C:\Users\risha\AppData\Local\Temp\capacity-t1-constrained-ml1mx7do\venv\Scripts\python.exe -m pip check` (exit 0):

```text
No broken requirements found.
```

Fresh migrate, seed and runserver homepage HTTP 200 also passed. Full UTF-8 transcript: .local/reports/T1_CONSTRAINED_CLONE_OUTPUT.txt; exact installed package inventory: .local/reports/T1_CONSTRAINED_FREEZE.txt.

Mutation-log confirmation: mutation 7 failed apps/assessments/tests/test_grading.py::test_mixed_marks_wrong_and_unanswered_are_graded_from_database (score 5 instead of 2). Mutation 20 failed apps/courses/tests/test_selectors.py::test_enrollment_and_participant_counts_have_one_query because another trainer unexpectedly received participant rows. That is the selector ownership assertion, not an edit-page assertion. The verbatim mutation table remains unchanged.
