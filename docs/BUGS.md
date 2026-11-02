# Bug Tracking Register

| ID | Description | Severity | Status | Resolution |
|---|---|---|---|---|
| None | No defects recorded in Phase B0 | - | - | - |

## BUG 001: HTTPS login redirect downgrade
- Symptom: An HTTPS login accepted an HTTP next URL on the same host.
- Root cause: Login URL validation did not require HTTPS for secure requests.
- Fix: Pass request.is_secure() as require_https to Django URL validation.
- Test: test_secure_login_rejects_http_next (failed before the fix).
- Commit: 061a56f (fix(accounts): preserve HTTPS login redirects and complete B2 housekeeping).

## BUG 002: Production host fallback
- Symptom: Production started without ALLOWED_HOSTS.
- Root cause: The shared environ schema supplied development hosts even with a required production lookup.
- Fix: Use a fresh environment reader without the shared default for production hosts.
- Test: test_production_requires_allowed_hosts (failed before the fix).
- Commit: 559ce79 (fix(settings): require explicit production hosts).

## BUG 003: Account edits through authenticated requests
- Symptom: Valid account POST requests raised AttributeError.
- Root cause: Generic file replacement code used type(instance).objects on Django's lazy request.user wrapper.
- Fix: Account writes have their own allowlisted validation and persistence path, independent of file handling.
- Test: test_account_post_preserves_privileges (originally the account half of test_trainer_profile_post_and_account_edit; failed before the fix).
- Commit: feat(profiles): add private role profiles and catalog workflows.

## BUG 004: Private file URL generation
- Symptom: Private FileFields could generate unauthenticated MEDIA_URL addresses.
- Root cause: Django's default FileSystemStorage exposes a public url method even without an application media route.
- Fix: PrivateStorage rejects URL generation; files are delivered only by the permission-checked view.
- Test: test_private_storage_has_no_public_url (failed before the fix).
- Commit: feat(profiles): add private role profiles and catalog workflows.

## BUG 005: Existing private uploads in edit forms
- Symptom: Existing-file edit forms failed after storage URL generation was disabled.
- Root cause: Django's default ClearableFileInput determines initial state and renders links using file.url.
- Fix: Shared PrivateFileInput identifies initial files by name and renders replacement/clear controls without a public link.
- Tests: test_profile_permission_matrix[approved_trainee-profiles:trainee_edit-GET], certificate_edit GET/POST (failed before the fix).
- Commit: feat(profiles): add private role profiles and catalog workflows.

## BUG 006: Silent removal of retired trainee skills
- Symptom: Inactive-subject selections disappeared from forms and could be silently removed on save.
- Root cause: Form choices excluded historical selections while the service replaced the entire M2M set from submitted choices.
- Fix: Include owner-retained choices in selectors and preserve existing retired skills at the service boundary.
- Tests: test_retired_selections_remain_visible_and_survive_form_save; test_service_retains_retired_skills_and_rejects_new_inactive_choices (failed first).
- Commit: fix(profiles): complete B2.1 pre-merge review.

## BUG 007: Account email uniqueness race returned 500
- Symptom: A database uniqueness collision after validation raised an unhandled IntegrityError.
- Root cause: Account writes relied on pre-write validation without recovering database-level email races.
- Fix: Isolate the write in a savepoint, then convert confirmed email collisions to field ValidationError; re-raise unrelated failures.
- Test: test_account_email_database_race_becomes_form_error (failed with unique_lower_email IntegrityError first).
- Commit: fix(profiles): complete B2.1 pre-merge review.

## BUG 008: Image decompression warning was accepted
- Symptom: A tiny PNG declaring 89478486 pixels was accepted despite Pillow's decompression-bomb warning.
- Root cause: Only DecompressionBombError was converted to validation feedback; the lower warning threshold did not reject uploads.
- Fix: Promote that warning locally and convert both warning/error thresholds to ValidationError.
- Test: test_decompression_bomb_is_a_form_error[bomb-warning] (failed with HTTP 302 first); bomb-error also covered.
- Commit: fix(profiles): complete B2.1 pre-merge review.

## BUG 009: Production CSRF cookie lacked explicit HttpOnly protection
- Symptom: Production inherited CSRF_COOKIE_HTTPONLY=False.
- Root cause: Production settings did not explicitly enforce the brief's HttpOnly cookie requirement.
- Fix: Set CSRF_COOKIE_HTTPONLY=True in prod.
- Test: test_production_csrf_cookie_is_httponly (failed first).
- Commit: fix(profiles): complete B2.1 pre-merge review.

## BUG 010: Corrupted documentation punctuation
- Symptom: The earlier B2 report and one historical progress line contained mojibake.
- Root cause: Earlier file rewrites used implicit Windows decoding before UTF-8 encoding.
- Fix: Repair corrupt sequences at source and require explicit UTF-8/no-BOM I/O.
- Verification: User-requested ripgrep scan reproduced the corruption; final scan and repository text byte audit are in B2.1 evidence.
- Commit: fix(profiles): complete B2.1 pre-merge review.

## BUG 011: Duplicate shared skill choices during B2.1
- Symptom: The new retained/active queryset union displayed shared active skills more than once.
- Root cause: Joining historical M2M selections duplicated active rows associated with multiple trainees.
- Fix: Apply distinct at the selector boundary before exposing form choices.
- Test: test_existing_and_active_choices_do_not_duplicate_shared_skills (failed first).
- Commit: fix(profiles): complete B2.1 pre-merge review.

## BUG 012: Resource detail leaked linked unpublished course titles
- Symptom: A published resource displayed its unpublished course title to an unrelated trainee.
- Root cause: The template used the resource FK directly without applying course visibility.
- Fix: Resolve course_visible through courses.selectors.visible_courses before rendering a course link.
- Test: test_public_resource_does_not_expose_unpublished_course_metadata (failed first).
- Commit: feat(courses): add B3 courses and private library workflows.

## BUG 013: Settings test assumed wrapper metadata was the configured module
- Symptom: The full suite's loader assertion failed after shared temporary-storage overrides were introduced.
- Root cause: Django's settings override holder has SETTINGS_MODULE=None even though the configured test loader, DB and hasher remain correct.
- Fix: Assert the configured DJANGO_SETTINGS_MODULE environment value; retain the concrete DB, hasher and timezone assertions.
- Test: test_settings_load_under_test_settings (failed in the full B3 suite before the adjustment).
- Commit: feat(courses): add B3 courses and private library workflows.

## BUG 014: Progressed course order could be rewritten
- Symptom: Existing station order changed and gaps could be inserted after progress existed.
- Root cause: Module writes validated uniqueness/positivity but not course-wide historical ordering.
- Fix: Course-locked order validation freezes existing orders and permits only max+1 append; progress uses the same course-first lock order.
- Tests: test_any_progress_freezes_existing_module_order (both cases), test_progress_allows_only_appended_modules (all failed first).
- Commit: fix(courses): freeze progressed module order and authorize B4 status.

## BUG 015: Empty deadline scope lost usage annotations
- Symptom: next_deadlines_for on an ineligible user raised FieldError instead of returning no data.
- Root cause: The early empty queryset omitted aliases used by downstream start/deadline filters.
- Fix: Preserve the annotated queryset contract for empty eligibility scopes too.
- Test: test_ineligible_users_have_no_departures (failed first).
- Commit: feat(assessments): add B4 authoring and timed atomic attempts.

## BUG 016: Course reassignment rejected derived quiz ownership
- Symptom: Valid Admin reassignment failed whenever questionnaires existed; library refusal omitted actionable counts.
- Root cause: Derived questionnaire trainer was treated as independent history instead of synchronizing it with the course.
- Fix: Update quiz trainers in the same course transaction and count independent conflicting resources in the refusal.
- Tests: test_reassignment_updates_all_questionnaires_atomically and test_linked_resource_refuses_reassignment_with_relink_count (failed first).
- Commit: fix(courses): synchronize quiz ownership and clean B4 carry-over.

## BUG 017: Direct feedback service accepted overlong comments
- Symptom: A 2001-character comment was saved through the service despite the 2000-character limit.
- Root cause: TextField max_length alone does not install a model MaxLengthValidator.
- Fix: Add MaxLengthValidator at the model boundary, reused by service full_clean; explicit form bounds remain.
- Test: test_invalid_feedback_returns_domain_error[4-comment2] failed before the fix.
- Commit: feat: add B5 feedback completion and private certificates.

## BUG 018: Staff certificate download lacked a reachable navigation link
- Symptom: Owning trainers/Admin could access downloads by URL but the course participants page offered no link.
- Root cause: The private delivery view was connected only to the trainee certificate list.
- Fix: Annotate certificate ID/PK into the already authorized participant query and render a link without extra per-row queries.
- Test: test_staff_participants_link_to_authorized_certificate_download failed first; existing one-query participation tests remain in the gate.
- Commit: feat: add B5 feedback completion and private certificates.

## BUG 019: Secondary certificate cleanup failure escaped generation isolation
- Symptom: An OSError deleting a just-written PDF could escape the generation domain boundary and roll back the triggering write.
- Root cause: The generation exception handler performed cleanup without converting its own expected I/O failure.
- Fix: Convert cleanup OSError to CertificateGenerationError too; the existing completion savepoint/logger handles it. A denied filesystem delete requires operator cleanup, but no partial certificate row persists.
- Test: test_cleanup_storage_failure_still_raises_generation_domain_error failed before the fix.
- Commit: feat: add B5 feedback completion and private certificates.

## BUG 020: Draft questionnaires diluted certificate averages
- Symptom: A ready quiz scored 100 plus an empty draft issued a 50.00 certificate; missing ready grades silently became zero.
- Root cause: Issuance averaged all questionnaires instead of completion's readiness-scoped set.
- Fix: Reuse readiness in the submitted-grade selector and reject missing ready submissions with a domain error.
- Tests: test_ready_quiz_and_empty_draft_average_is_100 and test_missing_ready_quiz_submission_is_domain_error (both failed first).
- Commit: fix(certificates): align ready-quiz averages and close B5 carry-over.

## BUG 021: Trainer dashboard annotation shadowed the questionnaire relation
- Symptom: Trainer dashboard raised ValueError even for an empty course scope.
- Root cause: An annotation used the existing reverse relation name questionnaires.
- Fix: Use questionnaire_count in SQL and map it into the CourseStats questionnaires field.
- Tests: test_trainer_dashboard_only_own_courses_and_weighted_totals and query-count/empty-scope tests failed first.
- Commit: feat: add B6 competency ranking public announcements and dashboards.

## BUG 022: Built-in admin trusted leftover staff flags after approval/role changes
- Symptom: An unapproved Admin or a demoted trainer retaining is_staff could authenticate to Django admin.
- Root cause: Django's default staff checks do not know the portal's is_approved or role fields.
- Fix: The custom Admin authentication form and AdminSite permission check require active approved ADMIN plus Django staff eligibility; generic denial logging and shared throttling remain in place.
- Test: test_unapproved_or_demoted_staff_cannot_authenticate_or_open_admin (both cases failed first).
- Commit: feat: harden B7 security deployment and operational workflows.

## BUG 023: Forced non-debug demo seeding accepted public credentials
- Symptom: --force with DEBUG=False seeded the documented public development password without an explicit DEMO_PASSWORD.
- Root cause: The environment guard checked force/debug status but not whether a production credential was explicitly supplied.
- Fix: Require a nonempty DEMO_PASSWORD environment value before non-debug seed execution, including reruns.
- Test: test_forced_non_debug_seed_requires_explicit_password failed first (DID NOT RAISE CommandError); after the fix it rejects missing credentials and accepts explicit credentials.
- Commit: fix: complete B7 demo and deployment carry-over.

## BUG 024: Authentication templates hid form-level errors
- Symptom: A fresh login client received no visible awaiting-approval or invalid-password explanation; signup password mismatches were invisible too.
- Root cause: The templates iterated bound fields but omitted form.non_field_errors, where authentication and cross-field validation place errors.
- Fix: Render Django's escaped non-field error list in both login and signup forms, leaving validation and disclosure rules unchanged.
- Tests: test_fresh_login_client_renders_form_level_error (two cases) and test_signup_renders_password_mismatch all failed first; isolated-client J2 exposed the issue without a signup flash message masking it.
- Commit: fix: render authentication form errors for fresh clients.
