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
