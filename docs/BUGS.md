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
