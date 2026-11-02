PHASE / TASK: B4 Assessments, including Step 0

STATUS: Done

GOAL: Deliver protected questionnaire authoring and timed, atomic, idempotent assessment attempts with safe results and participation handoffs.

WHAT CHANGED: Approved B3 merged into main and tagged b3-approved (2e10087); phase/b4-assessments created. First commit 4ce2090 fixes the course-wide module-order freeze and records the authorized Attempt.status amendment. assessments adds the five brief models, owner services, safe DTO selectors, forms and 15 bare HTML routes; core adds the shared clock. Course trainer/subject edits preserve linked assessment references. Navigation/landing pages expose the workflows. No new dependencies, completion logic or certificates. BUGs 014-015 are recorded with failing-test evidence.

HOW IT WAS VERIFIED:

Full stdout/stderr and inventories: ignored [.local/reports/B4_GATE_OUTPUT.txt](../.local/reports/B4_GATE_OUTPUT.txt). Step 0 before/after output: ignored .local/reports/B4_STEP0.txt. Commands below used venv/Scripts/python.exe; fresh migrate used a temporary database, and deploy check used prod settings with a temporary strong secret and explicit hosts.

```text
python -m pytest
============================ 1265 passed in 13.23s ============================
python -m coverage run -m pytest
============================ 1265 passed in 14.30s ============================
python -m coverage report -m (TOTAL and modules under 100% only)
apps\assessments\authoring.py                    93      4     20      0    96%   104-105, 167-168
apps\assessments\grading.py                      37      1      8      1    96%   33
apps\assessments\selectors.py                    56      1      4      1    97%   128
apps\core\clock.py                                4      1      0      0    75%   10
TOTAL                                          2303      7    324      2    99%
python -m ruff check .: All checks passed!
python -m ruff format --check . (final post-report): 188 files already formatted
python manage.py makemigrations --check: No changes detected
python manage.py migrate --noinput (fresh DB): all migrations OK, including assessments.0001_initial
python manage.py check: System check identified no issues (0 silenced).
python -m pip check: No broken requirements found.
python manage.py check --deploy --settings=config.settings.prod: 2 issues (0 silenced), security.W005 and security.W021
```

Branch coverage: 324 branches, 2 partially covered branches; exact missed arcs are in the transcript/coverage JSON. Assessment services is 100%; selectors.py is 97%; paper/result/participation selectors are 100%. Uncovered authoring exception handlers protect FK-deletion races; grading's empty-total guard and owned_attempts' ineligible empty branch are also unexercised. The clock wrapper's production call is patched in deterministic assessment tests.

Step 0 proofs: module-order regression tests failed first (three cases) then passed; Step 0 full suite 955 passed in 10.09s. Existing unpublished enrollments retain access and module progress; B4 test `apps/assessments/tests/test_attempts.py::test_enrolled_unpublished_course_can_still_start_quiz` proves retained quiz access. Admin's existing form can reassign a trainer, proved by `apps/courses/tests/test_b4_carryover.py::test_admin_course_form_can_reassign_trainer`; linked library/assessment invariants can block reassignment.

Carry-over test nodes (all passed in the full gate):

```text
apps/courses/tests/test_b4_carryover.py::test_active_all_done_station_map_has_no_current
apps/courses/tests/test_enrollment_services.py::test_enroll_is_unique_and_reactivates_dropped_history
apps/courses/tests/test_enrollment_services.py::test_enrollment_unique_race_returns_existing_row
apps/courses/tests/test_enrollment_services.py::test_wrong_course_dropped_and_other_owners_cannot_change_progress
apps/courses/tests/test_idor.py::test_wrong_course_and_dropped_completion_are_blocked
apps/library/tests/test_uploads.py::test_valid_signatures_ignore_browser_mime[VIDEO-mp4]
apps/library/tests/test_uploads.py::test_valid_signatures_ignore_browser_mime[VIDEO-webm]
apps/library/tests/test_uploads.py::test_wrong_extension_for_kind_is_rejected[VIDEO-pdf]
```

`wc -l` equivalent (Python splitlines inventory of every project .py excluding migrations), files over 150 lines only; generated migrations are exempt. Full inventory is in the transcript:

```text
 166 apps/accounts/tests/test_auth_views.py
 193 apps/accounts/tests/test_forms.py
 163 apps/accounts/views.py
 168 apps/assessments/authoring.py
 192 apps/assessments/models.py
 203 apps/assessments/selectors.py
 174 apps/assessments/services.py
 158 apps/assessments/tests/test_authoring.py
 164 apps/assessments/tests/test_grading.py
 179 apps/assessments/tests/test_selectors.py
 192 apps/assessments/tests/test_views.py
 152 apps/courses/services.py
 157 apps/courses/tests/test_course_services.py
 155 apps/profiles/tests/test_crud.py
```

AST top 5 longest functions (all functions <=25, handwritten modules <=250, views <=15 logic statements):

```text
25 apps/library/tests/test_crud.py:42 test_edit_replace_delete_forms_cleanup_files
24 apps/profiles/tests/test_crud.py:116 test_child_create_edit_delete
24 apps/profiles/tests/test_crud.py:20 test_trainee_profile_post_and_private_photo
24 apps/courses/enrollment_services.py:78 complete_module
24 apps/assessments/tests/test_views.py:51 test_question_edit_and_questionnaire_schedule_form
```

UTF-8/no-BOM audit of tracked and new text: no errors. Files are written with explicit encoding="utf-8". git diff --check found no whitespace errors.

New migration inventory (no earlier migration changed):

```text
CreateModel: Question, Attempt, Option, AttemptAnswer, Questionnaire
Constraints:
one_correct_option_at_most
unique_attempt_question
questionnaire_window_ordered
questionnaire_duration_bounds
questionnaire_pass_bounds
questionnaire_attempt_bounds
unique_questionnaire_order
question_order_positive
question_marks_positive
attempt_percent_bounds
one_open_attempt
Other operations: two AddField operations to connect Question/Attempt to Questionnaire; no AlterField.
```

| Selector | Small dataset | Large dataset | Queries, small / large |
|---|---|---|---|
| next_deadlines_for | 1 quiz + attempt | 12 quizzes + attempts | 1 / 1 |
| trainee_questionnaires | 1 quiz + attempt | 12 quizzes + attempts | 1 / 1 |
| participation | 1 enrollee + attempt | 20 enrollees + attempts | 2 / 2 |

Query counts are asserted by test_deadline_and_questionnaire_query_counts[small/large] and test_participation_query_count[small/large].

Boundary, no-leak and idempotency test nodes (all passed):

```text
apps/assessments/tests/test_attempts.py::test_double_start_resumes_one_open_attempt
apps/assessments/tests/test_boundaries.py::test_start_open_boundary[opens-minus-microsecond]
apps/assessments/tests/test_boundaries.py::test_start_open_boundary[opens-exact]
apps/assessments/tests/test_boundaries.py::test_start_deadline_boundary[deadline-minus-microsecond]
apps/assessments/tests/test_boundaries.py::test_start_deadline_boundary[deadline-exact]
apps/assessments/tests/test_boundaries.py::test_submission_grace_boundary[grace-limit-exact]
apps/assessments/tests/test_boundaries.py::test_submission_grace_boundary[grace-limit-plus-microsecond]
apps/assessments/tests/test_boundaries.py::test_started_before_deadline_can_finish_after_deadline
apps/assessments/tests/test_grading.py::test_service_double_submit_returns_stored_result_unchanged
apps/assessments/tests/test_no_leak.py::test_paper_dataclasses_and_queries_have_no_correctness
apps/assessments/tests/test_no_leak.py::test_take_html_contains_no_correct_option_markers
apps/assessments/tests/test_no_leak.py::test_result_hides_correct_choice_until_quota_exhausted
apps/assessments/tests/test_no_leak.py::test_staff_see_correct_choices_and_other_trainees_do_not
apps/assessments/tests/test_views.py::test_http_double_submit_changes_nothing
```

New-URL permission matrix: 210 cases (15 URLs x 7 actors x GET/POST), using apps/core/tests/matrix.py. Empty form POSTs return 200, authorized state actions redirect 302, object denials are 404, method guards precede lookup. take GET is the explicitly requested lazy-expiry exception.

| URL | Method | Anon | Trainee | Trainer owner | Trainer other | Admin | Unapproved | Inactive |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| assessments:course_list | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| assessments:course_list | POST | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| assessments:create | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| assessments:create | POST | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| assessments:manage_detail | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| assessments:manage_detail | POST | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| assessments:edit | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| assessments:edit | POST | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| assessments:delete | GET | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| assessments:delete | POST | 302 | 403 | 302 | 404 | 302 | 403 | 302 |
| assessments:question_add | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| assessments:question_add | POST | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| assessments:question_edit | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| assessments:question_edit | POST | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| assessments:question_delete | GET | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| assessments:question_delete | POST | 302 | 403 | 302 | 404 | 302 | 403 | 302 |
| assessments:participation | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| assessments:participation | POST | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| assessments:mine | GET | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| assessments:mine | POST | 302 | 405 | 403 | 403 | 403 | 403 | 302 |
| assessments:detail | GET | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| assessments:detail | POST | 302 | 405 | 403 | 403 | 403 | 403 | 302 |
| assessments:start | GET | 302 | 405 | 403 | 403 | 403 | 403 | 302 |
| assessments:start | POST | 302 | 302 | 403 | 403 | 403 | 403 | 302 |
| assessments:take | GET | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| assessments:take | POST | 302 | 302 | 403 | 403 | 403 | 403 | 302 |
| assessments:result | GET | 302 | 200 | 200 | 404 | 200 | 403 | 302 |
| assessments:result | POST | 302 | 405 | 405 | 405 | 405 | 403 | 302 |
| assessments:history | GET | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| assessments:history | POST | 302 | 405 | 403 | 403 | 403 | 403 | 302 |

DECISIONS AND ASSUMPTIONS: ADRs 038-047 record the status amendment, module freeze, unpublished access/reassignment, protected schema/grouped question input, shared clock and exact boundaries, zero-grade late rejection, locks/savepoints/idempotency, grading freeze, safe answer visibility, and attempted-trainee statistics denominators approved by the user. Both statistics are zero when nobody attempted. Participation includes retained enrollment history; B5 handoffs are read-only.

KNOWN ISSUES / RISKS:

- Login and signup throttling is not implemented (ADR 011, planned for B7).
- HSTS is 3600 s; include-subdomains and preload are intentionally off until HTTPS is verified (B7); these produce W005/W021.
- Library video downloads do not support Range requests (B7).
- Storage is not transactional: an outer rollback can leave a new file unreferenced (ADR 021).
- SQLite select_for_update is a no-op; simultaneous writes can encounter database-lock contention. Controlled constraint-collision tests passed; no multi-process load test was run.
- Raising quota cannot retract answers already revealed when the previous quota was exhausted. Course reassignment is blocked when it would invalidate linked resources/questionnaires; bulk reassignment is deferred.

DEMO STEPS: On phase/b4-assessments, migrate a fresh local DB, create a superuser and runserver. Create/approve trainer and trainee accounts; create a subject, published course and enrollment. Trainer opens the course's Assessments link, creates a current-window questionnaire and adds questions with 2..6 choices and one numbered correct option. Trainee opens My assessments, starts, selects radios and submits; inspect results/history and repeat the POST. Trainer/Admin opens Participation and results. Try a second attempt when allowed and confirm correct-option text stays hidden until quota is exhausted. No demo seed or seeded logins exist yet (seed command remains B7); no persistent DB was migrated by this task.

NEXT: Await B4 approval on phase/b4-assessments. B4 is not merged or tagged; B5 has not started.
