PHASE / TASK: B6 Competency, Announcements and Dashboards, including Step 0

STATUS: Done

GOAL: Deliver exact trainer rankings, a public published-only announcement board, and role-isolated read-only dashboard handoffs.

WHAT CHANGED: Approved B5 merged into main and tagged b5-approved (2e7c41c); phase/b6-competency-announcements-dashboards created. First commit 626271f changes certificate averaging to READY quizzes, rejects missing ready submissions, corrects ADR attribution and covers reviewed B5 branches. Only competency, announcements and dashboards apps were added. Competency includes trainer-only declarations and Admin ranking. Announcements adds manual Admin publication and a public root board. Dashboards has no models and returns eager aggregate DTOs; core receives the shared percentage helper. Bare views/nav/landing links are connected; existing role landing URL names remain unchanged. BUGs 020-021 were reproduced before fixes. No new dependencies, seed command, charts, export, email, CSS or B7 work.

HOW IT WAS VERIFIED:

Full stdout/stderr and inventories: ignored [.local/reports/B6_GATE_OUTPUT.txt](../.local/reports/B6_GATE_OUTPUT.txt); carry-over .local/reports/B6_STEP0.txt; font inventory .local/reports/B6_FONTS.txt; actual fake Admin output .local/reports/B6_FAKE_ADMIN.json and its nine SQL queries .local/reports/B6_ADMIN_SQL.txt. Commands used venv/Scripts/python.exe unless the bundled-runtime PDF inspection is explicitly named. Fresh migrate used a temporary DB; production check used a temporary strong secret, explicit hosts and SITE_BASE_URL. No persistent DB was migrated.

```text
python -m pytest
======================= 1747 passed in 79.49s (0:01:19) =======================
python -m coverage run -m pytest
============================ 1747 passed in 25.65s ============================
python -m coverage report -m (TOTAL and modules below 100% only)
apps\courses\completion.py                                    33      0     10      1    98%   54->exit
apps\courses\management\commands\evaluate_completions.py      19      0      6      1    96%   25->19
TOTAL                                                       3296      0    418      2    99%
python -m ruff check .: All checks passed!
python -m ruff format --check . (final post-report): 301 files already formatted
python manage.py makemigrations --check: No changes detected
python manage.py migrate --noinput (fresh DB): all migrations OK, including announcements.0001_initial and competency.0001_initial
python manage.py check: System check identified no issues (0 silenced).
python -m pip check: No broken requirements found.
python manage.py check --deploy --settings=config.settings.prod: 2 issues (0 silenced), W005 and W021
```

Branch coverage: 416/418 branches covered (99.52%); two partial branches; zero excluded lines. Every new service/selector and both dashboard aggregate modules are 100%. The only modules below 100% are the two listed above: completion's no-ACTIVE-enrollment path after a passing submit, and the retry command skipping a candidate whose requirements are not met. Both are valid no-op paths; they were not newly tested in B6. No pragma was used.

Step 0 full coverage run: `1492 passed in 88.17s`; TOTAL `2849 0 384 2 99%`. All six reviewed branches are covered:

| Reviewed reference | Disposition / passing proof |
|---|---|
| certificates/issuance.py:50 | Covered yearly sequence exhaustion with an existing CC-2026-99999 row: test_yearly_sequence_exhaustion_is_domain_error. |
| certificates/pdf.py:27,29 | Covered font shrinking and truncation: test_long_pdf_text_fits_and_uses_only_helvetica_times. |
| certificates/services.py:81 | Covered the real one-to-one collision with a controlled competing winner: test_issuance_unique_enrollment_race_returns_winner. |
| feedback/services.py:57 | Covered a real unique collision with unrecoverable controlled stale reads: test_feedback_collision_without_recoverable_winner_is_domain_error. |
| feedback/views.py:79 | Covered course ownership changing between the two real scoped reads: test_summary_ownership_changed_after_lookup_returns_404. |

Certificate-average regressions failed first: ready 100 + empty draft originally yielded 50.00, and missing ready submissions yielded a fabricated zero. Both now pass; no model or migration changed. The previous all-questionnaire/zero-substitution rule in ADR 053 is explicitly superseded as ratified by reviewer. ADR 047 uses reviewer attribution without an unquoted user-approval claim.

The bundled Poppler package has no pdffonts executable. Equivalent inspection used the bundled runtime's pypdf to enumerate every actual /Font resource dictionary (no project dependency added). The sample was regenerated; output:

```text
name | type | encoding | embedded
Helvetica | Type1 | WinAnsiEncoding | False
Helvetica-Bold | Type1 | WinAnsiEncoding | False
Times-Bold | Type1 | WinAnsiEncoding | False
Times-Roman | Type1 | WinAnsiEncoding | False
Times-Italic | Type1 | WinAnsiEncoding | False
```

Only standard Helvetica/Times Type1 fonts occur; no Symbol or nonstandard font appeared, so no glyph substitution fix was needed. The PDF byte-resource test also covers long text shrinking/truncation and permits only those five names.

Requested feedback proof nodes (all passed):

```text
apps/feedback/tests/test_selectors.py::test_trainer_anonymity_admin_identity_and_escaped_comments
apps/feedback/tests/test_services.py::test_course_feedback_upsert_for_every_enrollment_status[ACTIVE]
apps/feedback/tests/test_services.py::test_course_feedback_upsert_for_every_enrollment_status[DROPPED]
apps/feedback/tests/test_services.py::test_course_feedback_upsert_for_every_enrollment_status[COMPLETED]
apps/feedback/tests/test_services.py::test_non_enrolled_course_and_unpublished_resource_are_refused
apps/feedback/tests/test_services.py::test_insert_race_recovers_and_updates_real_unique_winner
apps/feedback/tests/test_views.py::test_other_feedback_author_cannot_edit_or_delete
```

The combined anonymity/XSS node asserts trainer HTML and DTO omit the author name, Admin HTML includes it, and script text is escaped. The combined IDOR node asserts both ineligible-target editing and another author's delete are 404.

`wc -l` equivalent (Python splitlines inventory of every project .py excluding migrations), files over 150 lines only; complete inventory is in the transcript:

```text
 166 apps/accounts/tests/test_auth_views.py
 193 apps/accounts/tests/test_forms.py
 163 apps/accounts/views.py
 164 apps/assessments/authoring.py
 192 apps/assessments/models.py
 242 apps/assessments/selectors.py
 183 apps/assessments/services.py
 158 apps/assessments/tests/test_authoring.py
 164 apps/assessments/tests/test_grading.py
 179 apps/assessments/tests/test_selectors.py
 192 apps/assessments/tests/test_views.py
 159 apps/courses/services.py
 201 apps/courses/tests/test_completion.py
 157 apps/courses/tests/test_course_services.py
 160 apps/dashboards/admin_selectors.py
 179 apps/dashboards/tests/test_selectors.py
 155 apps/profiles/tests/test_crud.py
```

AST top 5 (all functions <=25, handwritten modules <=250, views <=15 logic statements); UTF-8/no-BOM audit and git diff --check found no errors:

```text
25 apps/library/tests/test_crud.py:42 test_edit_replace_delete_forms_cleanup_files
25 apps/certificates/services.py:60 issue_certificate
24 apps/profiles/tests/test_crud.py:116 test_child_create_edit_delete
24 apps/profiles/tests/test_crud.py:20 test_trainee_profile_post_and_private_photo
24 apps/feedback/tests/test_views.py:53 test_csrf_required_for_submit_and_delete
```

New migration inventory:

```text
competency.0001_initial: CreateModel TrainerCompetency
  constraints: unique_trainer_subject_competency, competency_proficiency_bounds, competency_experience_bounds
announcements.0001_initial: CreateModel Announcement
  constraints: announcement_published_timestamp
dashboards: no models and no generated migration.
No AlterField and no migration on main was edited.
```

| Selector | Small fixture | Large fixture | Queries, small / large |
|---|---|---|---|
| rank_trainers_for | 1 trainer, 2 feedback rows | 12 trainers, 24 feedback rows | 1 / 1 |
| board | 1 published item | 12 published items | 1 / 1 |
| admin_dashboard | 1 subject/course/enrollment, 2 submitted attempts | 10 subjects/courses/enrollments, 20 submitted attempts | 9 / 9 |
| trainer_dashboard | 1 own course/quiz | 10 own courses/quizzes | 2 / 2 |

Ranking test nodes (all passed):

```text
apps/competency/tests/test_ranking.py::test_ranking_formula_examples_and_experience_cap
apps/competency/tests/test_ranking.py::test_ratings_average_rows_across_targets_and_only_ranked_subject
apps/competency/tests/test_ranking.py::test_ranking_ties_use_published_course_count_then_trainer_id
apps/competency/tests/test_ranking.py::test_equal_display_scores_are_ordered_by_unrounded_score
apps/competency/tests/test_ranking.py::test_ineligible_trainers_with_leftover_competencies_are_excluded[changes0]
apps/competency/tests/test_ranking.py::test_ineligible_trainers_with_leftover_competencies_are_excluded[changes1]
apps/competency/tests/test_ranking.py::test_ineligible_trainers_with_leftover_competencies_are_excluded[changes2]
apps/competency/tests/test_ranking.py::test_ranking_constant_query_count[small]
apps/competency/tests/test_ranking.py::test_ranking_constant_query_count[large]
```

Published-only and escaped-public-content proof nodes:

```text
apps/announcements/tests/test_selectors.py::test_drafts_and_unpublished_items_never_appear_on_public_home_or_board
apps/announcements/tests/test_selectors.py::test_public_body_is_escaped_with_only_line_breaks
apps/announcements/tests/test_selectors.py::test_board_limits_each_category_and_orders_stably
apps/announcements/tests/test_views.py::test_non_admin_cannot_reach_any_draft_listing
```

Root route proof (B5 URLconf loaded directly from Git, current route resolved separately): `b5-approved root: Resolver404 (unmatched); current root: announcements:home`. Anonymous home is 200; no draft/withdrawn text appears, including for logged-in visitors. All eight new mutation routes have explicit CSRF tests. Admin management pagination is tested at twenty rows.

Actual AdminDashboard output from analytics_dataset(), also asserted by test_admin_dashboard_exact_fake_dataset_numbers (fresh in-memory DB and temporary private storage):

| Metric | Value |
|---|---|
| Active users by role; pending | TRAINEE 4, TRAINER 2, ADMIN 1; pending 1 |
| Courses | 3 total, 2 published |
| Enrollments | 4 total: ACTIVE 2, COMPLETED 1, DROPPED 1 |
| Line load | Data Skills 4 total / 2 active; Zero Enrollments 0 / 0 |
| Certificates | 1 total: A 1, B/C/D 0 |
| Assessments | 3 questionnaires, 4 submitted attempts, 3 distinct trainee/questionnaire pairs |
| Pair statistics | Best scores 80, 100, 20: average 66.67%, pass rate 66.67% |
| Participation cohort | 2 enrolled trainees, 2 attempted in cohort, 100.00% |

A dropped-only trainee's submitted attempt remains in assessment pair statistics but not participation. The retake pair counts once. Admin assessment aggregation performs SQL GROUP BY/MAX and outer SUM/COUNT; pair rows are never looped in Python. The 1000-pair half-up boundary test also passes. Trainer totals weight course-rating rows correctly, hide unrelated courses and carry direct existing participation links.

New-URL permission matrix: 196 cases (14 URLs x 7 actors x GET/POST). Empty form POSTs return 200; valid form submissions redirect. Method guards precede object lookup; both trainers access their own dashboard/list, while trainer-other edit/remove scopes are denied. Public home permits safe methods regardless of login/approval.

| URL | Method | Anon | Trainee | Trainer owner | Trainer other | Admin | Unapproved | Inactive |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| competency:mine | GET | 302 | 403 | 200 | 200 | 403 | 403 | 302 |
| competency:mine | POST | 302 | 403 | 405 | 405 | 403 | 403 | 302 |
| competency:add | GET | 302 | 403 | 200 | 200 | 403 | 403 | 302 |
| competency:add | POST | 302 | 403 | 200 | 200 | 403 | 403 | 302 |
| competency:edit | GET | 302 | 403 | 200 | 404 | 403 | 403 | 302 |
| competency:edit | POST | 302 | 403 | 200 | 404 | 403 | 403 | 302 |
| competency:remove | GET | 302 | 403 | 405 | 405 | 403 | 403 | 302 |
| competency:remove | POST | 302 | 403 | 302 | 404 | 403 | 403 | 302 |
| dashboards:trainer | GET | 302 | 403 | 200 | 200 | 403 | 403 | 302 |
| dashboards:trainer | POST | 302 | 403 | 405 | 405 | 403 | 403 | 302 |
| competency:ranking | GET | 302 | 403 | 403 | 403 | 200 | 403 | 302 |
| competency:ranking | POST | 302 | 403 | 403 | 403 | 405 | 403 | 302 |
| announcements:manage | GET | 302 | 403 | 403 | 403 | 200 | 403 | 302 |
| announcements:manage | POST | 302 | 403 | 403 | 403 | 405 | 403 | 302 |
| announcements:create | GET | 302 | 403 | 403 | 403 | 200 | 403 | 302 |
| announcements:create | POST | 302 | 403 | 403 | 403 | 200 | 403 | 302 |
| announcements:edit | GET | 302 | 403 | 403 | 403 | 200 | 403 | 302 |
| announcements:edit | POST | 302 | 403 | 403 | 403 | 200 | 403 | 302 |
| announcements:publish | GET | 302 | 403 | 403 | 403 | 405 | 403 | 302 |
| announcements:publish | POST | 302 | 403 | 403 | 403 | 302 | 403 | 302 |
| announcements:unpublish | GET | 302 | 403 | 403 | 403 | 405 | 403 | 302 |
| announcements:unpublish | POST | 302 | 403 | 403 | 403 | 302 | 403 | 302 |
| announcements:delete | GET | 302 | 403 | 403 | 403 | 405 | 403 | 302 |
| announcements:delete | POST | 302 | 403 | 403 | 403 | 302 | 403 | 302 |
| dashboards:admin | GET | 302 | 403 | 403 | 403 | 200 | 403 | 302 |
| dashboards:admin | POST | 302 | 403 | 403 | 403 | 405 | 403 | 302 |
| announcements:home | GET | 200 | 200 | 200 | 200 | 200 | 200 | 200 |
| announcements:home | POST | 405 | 405 | 405 | 405 | 405 | 405 | 405 |

DECISIONS AND ASSUMPTIONS: ADRs 053 and 056-061 document READY-only averaging, attribution, retained declarations and trainer-only editing, exact ranking population/weights/ties, public manual announcements/publication timestamps, SQL best-pair analytics and the participation cohort, trainer totals and percentage-helper move. Active pending approvals exclude inactive/rejected users. D still denotes completed below 50; normal B6 issuance requires the ready-quiz submitted history and existing certificate snapshots remain unchanged.

User's exact answer to the B6 participation-cohort question (2026-11-02):

> Use the enrolled cohort (Recommended)

The answer is also quoted verbatim with its date in ADR 060. No other new user approval is claimed for an ADR.

KNOWN ISSUES / RISKS:

- Login and signup throttling is not implemented (ADR 011, planned for B7).
- HSTS is 3600 s; include-subdomains and preload are intentionally off until HTTPS is verified (B7), producing W005/W021.
- public verification shows the current name of the trainee, while the stored PDF keeps the name from issuance; a rename makes them differ.
- Non-Latin names are not rendered correctly in PDFs; a bundled Unicode font requires user approval in B7.
- Sequential certificate IDs are enumerable; verification rate limiting is planned for B7.
- SQLite row locks are no-ops and concurrent writes can encounter lock contention; tests control constraint collisions, not multi-process load. Arbitrary outer rollbacks cannot make filesystem storage transactional, and denied cleanup requires operator action. Library video Range support remains B7; raised quiz quota cannot retract previously disclosed answers.

DEMO STEPS: On this review branch, migrate a fresh local DB, createsuperuser and runserver. The public root shows only published board items with login/signup/verify links. Admin creates a manual draft, publishes/unpublishes it, and opens Find trainers or Admin statistics. An approved Trainer declares competencies, edits/removes own declarations and opens My trainer statistics with existing questionnaire participation links. Admin cannot edit competencies; trainees cannot open ranking/dashboards. Existing /trainee/, /trainer/ and /admin-panel/ names/paths remain unchanged. Fake analytics data was temporary test data, not a new seed command or persistent seeded login. Existing regenerated sample remains ignored at C:/Django/Project/.local/samples/sample_certificate.pdf.

NEXT: Await B6 approval on phase/b6-competency-announcements-dashboards. B6 is not merged or tagged; B7 has not started.
