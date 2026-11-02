PHASE / TASK: B5 Feedback, Completion and Certificates, including Step 0

STATUS: Done

GOAL: Deliver editable trainee feedback and atomic completion with exactly-once private certificate issuance, retry and minimal public verification.

WHAT CHANGED: Approved B4 merged into main and tagged b4-approved (e2870f0); phase/b5-feedback-certificates created. First commits 21b746d and bc51e6b clarify ADR 047, rename the DTO field to pass_rate_percent without changing percentage arithmetic, clean carry-over guards and synchronize quiz trainers on course reassignment. Only feedback and certificates apps were added. Courses owns the sole completion entry, retry command and constant-query status DTO; assessment readiness is shared with starts. Private PDF issuance, public lookup, safe views/templates and navigation are connected, including staff download links from course participants. core.clock adds today(); settings/.env.example add origin/signatories. No dependencies, extra model fields, signals, dashboards or B6 work. BUGs 016-019 include failing-test evidence.

HOW IT WAS VERIFIED:

Full stdout/stderr and inventories: ignored [.local/reports/B5_GATE_OUTPUT.txt](../.local/reports/B5_GATE_OUTPUT.txt); import proof .local/reports/B5_IMPORTS.txt. All commands used venv/Scripts/python.exe. Fresh migrate used a temporary DB; production check used a temporary strong secret, explicit hosts and SITE_BASE_URL. No persistent DB was migrated.

```text
python -m pytest
============================ 1486 passed in 17.69s ============================
python -m coverage run -m pytest
======================= 1486 passed in 72.32s (0:01:12) =======================
python -m coverage report -m (TOTAL and modules below 100% only)
apps\certificates\issuance.py                                 25      1      2      1    93%   50
apps\certificates\pdf.py                                      82      2      8      2    96%   27, 29
apps\certificates\services.py                                 54      1     12      1    97%   81
apps\courses\completion.py                                    33      0     10      1    98%   54->exit
apps\courses\management\commands\evaluate_completions.py      19      0      6      1    96%   25->19
apps\feedback\services.py                                     49      1      6      1    96%   57
apps\feedback\views.py                                        37      1      2      1    95%   79
TOTAL                                                       2847      6    382      8    99%
python -m ruff check .: All checks passed!
python -m ruff format --check .: 244 files already formatted
python manage.py makemigrations --check: No changes detected
python manage.py migrate --noinput (fresh DB): all migrations OK, including certificates.0001_initial and feedback.0001_initial
python manage.py check: System check identified no issues (0 silenced).
python -m pip check: No broken requirements found.
python manage.py check --deploy --settings=config.settings.prod: 2 issues (0 silenced), W005 and W021
```

Branch coverage: 374/382 branches covered (97.91%); eight partial branches; zero excluded lines. New services: certificates 97%, feedback 96%; new selectors and completion selectors 100%. Remaining branches include yearly sequence exhaustion, competing issuance winner recovery, long-text fitting, an absent active enrollment, command noncompletion, unrecoverable feedback conflict and summary authorization changing between lookups. The configured coverage floors pass; no pragma was added.

Step 0: coverage run -m pytest reported `1274 passed in 49.53s`; coverage TOTAL was `2301 0 322 0 100%`, with no module below 100%. The clock's real aware-datetime call and owned_attempts' direct ineligible scope are covered. Reassignment regressions failed before the fix, then passed; the final test proves multiple questionnaires, including an attempted one, receive the new trainer. Conflicting independent library resources remain unchanged and the domain error gives their count and asks Admin to relink or unlink.

Requested prior source excerpts (b4-approved, before removal):

```python
apps/assessments/grading.py (b4-approved):
30: def percent_for(score: int, total: int) -> Decimal:
31:     """Round only Decimal arithmetic with the mandated half-up rule."""
32:     if total <= 0:
33:         raise AssessmentRuleError("Questionnaire is not ready.")
34:     return (Decimal(score) * PERCENT_SCALE / Decimal(total)).quantize(
35:         PERCENT_QUANTUM, rounding=ROUND_HALF_UP
36:     )
apps/assessments/authoring.py (b4-approved):
95: @transaction.atomic
96: def delete_questionnaire(actor: User, questionnaire: Questionnaire) -> None:
97:     """Remove a draft explicitly without discarding protected assessment history."""
98:     questionnaire = managed_questionnaire(actor, questionnaire)
99:     require_editable_questions(questionnaire)
100:     try:
101:         Option.objects.filter(question__questionnaire=questionnaire).delete()
102:         questionnaire.questions.all().delete()
103:         questionnaire.delete()
104:     except ProtectedError as exc:
105:         raise AssessmentRuleError(
106:             "Questionnaire has protected assessment history."
107:         ) from exc
160:     """Keep attempted question/option history undeletable."""
161:     question = Question.objects.select_related("questionnaire").get(pk=question.pk)
162:     managed_questionnaire(actor, question.questionnaire)
163:     require_editable_questions(question.questionnaire)
164:     try:
165:         question.options.all().delete()
166:         question.delete()
167:     except ProtectedError as exc:
168:         raise AssessmentRuleError("Question has protected assessment history.") from exc
apps/assessments/selectors.py (b4-approved):
120: def owned_attempts(trainee: User) -> QuerySet[Attempt]:
121:     """Prevent guessed attempt IDs from reaching trainee read or submit flows."""
122:     attempts = Attempt.objects.select_related("questionnaire__course")
123:     if (
124:         not trainee.is_active
125:         or not trainee.is_approved
126:         or trainee.role != UserRole.TRAINEE
127:     ):
128:         return attempts.none()
129:     return attempts.filter(trainee=trainee)
```

Disposition: remove the empty-total guard (ready quizzes have questions and positive marks); remove the two draft-deletion ProtectedError handlers (the existing questionnaire lock/no-attempt rule prevents those supported history races); retain and cover the reachable owned_attempts guard with test_ineligible_owned_attempts_scope_is_empty. No cover exclusions. Current marks/attempt protection remains enforced by constraints/services.

Requested grading proof nodes (all passed):

```text
apps/assessments/tests/test_grading.py::test_exact_pass_percent_boundary[exact-threshold-passes]
apps/assessments/tests/test_grading.py::test_exact_pass_percent_boundary[49-99-below-50-fails]
apps/assessments/tests/test_grading.py::test_mixed_marks_wrong_and_unanswered_are_graded_from_database
apps/assessments/tests/test_grading.py::test_half_up_rounding_and_all_unanswered
apps/assessments/tests/test_grading.py::test_tampered_submission_is_rejected_whole[foreign-question]
apps/assessments/tests/test_grading.py::test_tampered_submission_is_rejected_whole[foreign-option]
apps/assessments/tests/test_grading.py::test_tampered_submission_is_rejected_whole[other-question-option]
apps/assessments/tests/test_grading.py::test_tampered_submission_is_rejected_whole[malformed-id]
apps/assessments/tests/test_b5_carryover.py::test_grading_uses_no_float_operations
```

Exact requested sweep:

```text
rg -n "float\(|timezone\.now|datetime\.now|date\.today" apps/assessments apps/courses
(no output; exit 1)
```

Brief amendment proof:

```text
$ git show --stat 4ce2090 -- docs/IMPLEMENTATION_BRIEF.md
commit 4ce20909074bcf0b33919987998abb3806ddede6
Author: rishavraj13 <rishavraj7016@gmail.com>
Date:   Mon Nov 2 15:32:14 2026 +0530

    fix(courses): freeze progressed module order and authorize B4 status

 docs/IMPLEMENTATION_BRIEF.md | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

Current section 4: - **Attempt**: `questionnaire`, `trainee`, `started_at`, `submitted_at` (nullable), `score`, `percent`, `passed`, `status` (IN_PROGRESS, SUBMITTED, TIMED_OUT; default IN_PROGRESS).

`wc -l` equivalent (Python splitlines inventory of every project .py excluding migrations), files over 150 lines only; full inventory is in the transcript:

```text
 166 apps/accounts/tests/test_auth_views.py
 193 apps/accounts/tests/test_forms.py
 163 apps/accounts/views.py
 164 apps/assessments/authoring.py
 192 apps/assessments/models.py
 240 apps/assessments/selectors.py
 183 apps/assessments/services.py
 158 apps/assessments/tests/test_authoring.py
 164 apps/assessments/tests/test_grading.py
 179 apps/assessments/tests/test_selectors.py
 192 apps/assessments/tests/test_views.py
 159 apps/courses/services.py
 201 apps/courses/tests/test_completion.py
 157 apps/courses/tests/test_course_services.py
 155 apps/profiles/tests/test_crud.py
```

AST top 5 (all functions <=25, handwritten modules <=250, views <=15 logic statements); UTF-8/BOM audit found no errors:

```text
25 apps/library/tests/test_crud.py:42 test_edit_replace_delete_forms_cleanup_files
25 apps/certificates/services.py:60 issue_certificate
24 apps/profiles/tests/test_crud.py:116 test_child_create_edit_delete
24 apps/profiles/tests/test_crud.py:20 test_trainee_profile_post_and_private_photo
24 apps/feedback/tests/test_views.py:53 test_csrf_required_for_submit_and_delete
```

New migration inventory (no migration on main changed; generated migrations are exempt from the module size rule):

```text
feedback.0001_initial: CreateModel Feedback
  feedback_rating_bounds, feedback_one_target, unique_author_course_feedback, unique_author_resource_feedback
  No AlterField or follow-up migration.
certificates.0001_initial: CreateModel Certificate
  certificate_percent_bounds
  No AlterField or follow-up migration.
```

| Selector | Small dataset | Large dataset | Queries, small / large |
|---|---|---|---|
| feedback_summary | 1 opinion | 25 opinions | 1 / 1 |
| feedback_page | 1 opinion | 25 opinions, page size 20 | 3 / 3 |
| completion_status | 1 module + ready quiz | 12 modules + ready quizzes | 2 / 2 |

Completion scenario/command nodes (all passed):

```text
apps/courses/tests/test_completion.py::test_modules_done_without_ready_quizzes_complete_without_certificate
apps/courses/tests/test_completion.py::test_last_passing_submit_completes_and_issues_once
apps/courses/tests/test_completion.py::test_last_module_after_passing_quiz_completes_and_issues
apps/courses/tests/test_completion.py::test_zero_modules_never_completes
apps/courses/tests/test_completion.py::test_exhausted_failed_quizzes_keep_enrollment_active
apps/courses/tests/test_completion.py::test_completed_status_never_reverts_after_new_content
apps/courses/tests/test_completion.py::test_dropped_is_ignored_then_reactivation_completes_history
apps/courses/tests/test_completion.py::test_pdf_failure_preserves_passing_quiz_and_progress
apps/courses/tests/test_completion.py::test_pdf_failure_preserves_last_module_progress
apps/courses/tests/test_completion.py::test_completion_status_constant_query_count[small]
apps/courses/tests/test_completion.py::test_completion_status_constant_query_count[large]
apps/courses/tests/test_completion.py::test_modules_done_with_zero_questionnaires_complete_without_certificate
apps/courses/tests/test_completion.py::test_missed_quiz_deadline_keeps_enrollment_active
apps/courses/tests/test_completion.py::test_conditional_update_race_produces_one_transition_and_certificate
apps/courses/tests/test_completion_command.py::test_evaluate_completions_counts_retry_and_idempotence
```

Certificate grade boundaries, average and PDF nodes (all passed):

```text
apps/certificates/tests/test_failures.py::test_pdf_reference_save_failure_removes_new_file
apps/certificates/tests/test_services.py::test_certificate_grade_boundaries[80.00-A]
apps/certificates/tests/test_services.py::test_certificate_grade_boundaries[79.99-B]
apps/certificates/tests/test_services.py::test_certificate_grade_boundaries[65.00-B]
apps/certificates/tests/test_services.py::test_certificate_grade_boundaries[64.99-C]
apps/certificates/tests/test_services.py::test_certificate_grade_boundaries[50.00-C]
apps/certificates/tests/test_services.py::test_certificate_grade_boundaries[49.99-D]
apps/certificates/tests/test_services.py::test_average_best_submitted_is_half_up_over_all_questionnaires
apps/certificates/tests/test_services.py::test_idempotent_issuance_preserves_file_and_snapshot
apps/certificates/tests/test_services.py::test_identifier_sequence_and_year_rollover
apps/certificates/tests/test_services.py::test_identifier_collision_retries_real_unique_constraint
apps/certificates/tests/test_pdf.py::test_certificate_pdf_is_one_page_reproducible_and_safe[latin]
apps/certificates/tests/test_pdf.py::test_certificate_pdf_is_one_page_reproducible_and_safe[latin-extended]
apps/certificates/tests/test_pdf.py::test_certificate_pdf_is_one_page_reproducible_and_safe[devanagari]
apps/certificates/tests/test_pdf.py::test_certificate_pdf_is_one_page_reproducible_and_safe[escaped-text]
```

Additional regression nodes (failed first, then passed):

```text
apps/certificates/tests/test_views.py::test_staff_participants_link_to_authorized_certificate_download
apps/certificates/tests/test_failures.py::test_cleanup_storage_failure_still_raises_generation_domain_error
```

Poppler pdfinfo opened the fake-data sample: one page, 841.89 x 595.276 points, A4 landscape, PDF 1.4, 4767 bytes. pdftoppm rendered it; the PNG was visually inspected for layout, legibility and clipping. Poppler emitted local display-font fallback messages for Symbol/ArialUnicode; the inspected output rendered the required built-in Latin text correctly. Unsupported non-Latin glyphs are the recorded limitation below.

Import direction: trigger write services lazily enter courses.completion -> certificate issuance and completion selectors -> assessment read contracts. Certificate issuance consumes assessment reads, never assessment writes. Top-level import graph, including from-package submodule imports: 130 application modules, cycles=[]. Two fresh processes imported write/completion modules in opposite orders, both exit 0. The transcript lists the exact orders. No signals or recursive completion rule copies exist.

New-URL matrix: 140 cases (10 URLs x 7 actors x GET/POST). Public rows use the shared public_permission_rows helper. Form POSTs below are empty/invalid and return 200; valid submit/edit POSTs redirect. IDOR and real CSRF/XSS tests run separately.

| URL | Method | Anon | Trainee | Trainer owner | Trainer other | Admin | Unapproved | Inactive |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| feedback:mine | GET | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| feedback:mine | POST | 302 | 405 | 403 | 403 | 403 | 403 | 302 |
| feedback:course_submit | GET | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| feedback:course_submit | POST | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| feedback:resource_submit | GET | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| feedback:resource_submit | POST | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| feedback:delete | GET | 302 | 405 | 403 | 403 | 403 | 403 | 302 |
| feedback:delete | POST | 302 | 302 | 403 | 403 | 403 | 403 | 302 |
| feedback:course_summary | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| feedback:course_summary | POST | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| feedback:resource_summary | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| feedback:resource_summary | POST | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| certificates:mine | GET | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| certificates:mine | POST | 302 | 405 | 403 | 403 | 403 | 403 | 302 |
| certificates:download | GET | 302 | 200 | 200 | 404 | 200 | 403 | 302 |
| certificates:download | POST | 302 | 405 | 405 | 405 | 405 | 403 | 302 |
| certificates:verify_form | GET | 200 | 200 | 200 | 200 | 200 | 200 | 200 |
| certificates:verify_form | POST | 405 | 405 | 405 | 405 | 405 | 405 | 405 |
| certificates:verify | GET | 200 | 200 | 200 | 200 | 200 | 200 | 200 |
| certificates:verify | POST | 405 | 405 | 405 | 405 | 405 | 405 | 405 |

DECISIONS AND ASSUMPTIONS: ADRs 047-055 record explicit 0..100 percentage units and attribution; derived questionnaire reassignment with independent resource refusal; trainee feedback eligibility/anonymity; one completion policy and import direction; zero-ready completion without certificate; isolated generation failure/retry; all-questionnaire averaging with user-confirmed missing grades=0.00; Decimal bands/yearly IDs; immutable PDF snapshots and font fallback; environment origin/signatories and minimal public lookup. D means completed below 50. Public lookup shows current relational names; the stored PDF retains issuance names. Existing COMPLETED enrollments never revert.

KNOWN ISSUES / RISKS:

- Login and signup throttling is not implemented (ADR 011, planned for B7).
- HSTS is 3600 s; include-subdomains and preload are intentionally off until HTTPS is verified (B7), producing W005/W021.
- Non-Latin names are not rendered correctly in PDFs; fix in B7 with a bundled Unicode font, needs user approval.
- Sequential certificate IDs are enumerable; verification rate limiting is planned for B7.
- SQLite row locks are no-ops and simultaneous writes may encounter lock contention. Constraint/conditional collisions were controlled in tests; no multi-process load test was run.
- Filesystem storage is not transactional with an arbitrary outer rollback (ADR 021); generation/reference-save failures clean up their own new files unless storage denies deletion; that error is logged and requires operator cleanup without losing the triggering write. Library video Range support remains deferred to B7. Raising quiz quota cannot retract already disclosed answers.

DEMO STEPS: Configure SITE_BASE_URL/signatory settings, migrate a fresh DB, create an Admin with createsuperuser and runserver. Create/approve trainer/trainee accounts; create a subject, published course with a module, valid quiz and enrollment. Trainee can edit feedback from course/resource detail and view My feedback; trainer/Admin can inspect scoped summaries. Complete modules and pass ready quizzes in either order; open My certificates and download. Open /verify/ anonymously and inspect only public fields. On a generation failure, run `python manage.py evaluate_completions` to retry. Review the deterministic fake-data sample at `C:/Django/Project/.local/samples/sample_certificate.pdf` (ignored, not committed). No persistent seeded logins were created; seed_demo_data remains B7.

NEXT: Await B5 approval on phase/b5-feedback-certificates. Do not merge/tag B5 or start B6 before approval.
