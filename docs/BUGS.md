# Bug Tracking Register

| ID | Description | Severity | Status | Resolution |
|---|---|---|---|---|
| None | No defects recorded in Phase B0 | - | - | - |

## BUG 001: HTTPS login redirect downgrade
- Symptom: An HTTPS login accepted an HTTP next URL on the same host.
- Root cause: Login URL validation did not require HTTPS for secure requests.
- Fix: Pass request.is_secure() as require_https to Django URL validation.
- Test: test_secure_login_rejects_http_next (failed before the fix).
- Commit: fix(accounts): preserve HTTPS login redirects (B2 housekeeping).

## BUG 002: Production host fallback
- Symptom: Production started without ALLOWED_HOSTS.
- Root cause: The shared environ schema supplied development hosts even with a required production lookup.
- Fix: Use a fresh environment reader without the shared default for production hosts.
- Test: test_production_requires_allowed_hosts (failed before the fix).
- Commit: fix(settings): require explicit production hosts.
