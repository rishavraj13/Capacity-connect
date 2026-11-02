# Deployment and operations

Use Python 3.14 and the pinned requirements. PostgreSQL readiness is a static review only; no driver was added.

## Environment catalogue

The table below lists every environment variable read by our settings. `.env.example` uses development values. SECRET_KEY, ALLOWED_HOSTS and SITE_BASE_URL are required in production. Base DEBUG defaults False; dev defaults True; prod always forces False. Base hosts default to localhost and 127.0.0.1. Relative paths resolve from the process working directory.

| Variable | Required | Default expression | Purpose |
|---|---|---|---|
| `ADMIN_URL` | no | `'django-admin/'` | admin url |
| `ALLOWED_HOSTS` | production | `required` | allowed hosts |
| `CACHE_TABLE` | no | `'capacity_connect_cache'` | cache table |
| `CACHE_URL` | no | `f'dbcache://{CACHE_TABLE}'` | cache url |
| `CERTIFICATE_MAX_BYTES` | no | `5 * 1024 * 1024` | certificate max bytes |
| `CERTIFICATE_SIGNATORY_NAME` | no | `'Capacity Connect Administrator'` | certificate signatory name |
| `CERTIFICATE_SIGNATORY_TITLE` | no | `'Programme Director'` | certificate signatory title |
| `CONTENT_SECURITY_POLICY` | no | `"default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"` | content security policy |
| `CSRF_COOKIE_SAMESITE` | no | `'Lax'` | csrf cookie samesite |
| `CSRF_COOKIE_SECURE` | no | `True` | csrf cookie secure |
| `DATABASE_URL` | no | `f"sqlite:///{BASE_DIR / 'db.sqlite3'}"` | database url |
| `DEBUG` | no | `required` | debug |
| `DEMO_PASSWORD` | no | `'Demo-Connect-2026!'` | demo password |
| `LIBRARY_DOCUMENT_MAX_BYTES` | no | `25 * 1024 * 1024` | library document max bytes |
| `LIBRARY_PRESENTATION_MAX_BYTES` | no | `25 * 1024 * 1024` | library presentation max bytes |
| `LIBRARY_VIDEO_MAX_BYTES` | no | `200 * 1024 * 1024` | library video max bytes |
| `LOGIN_FAILURE_LIMIT` | no | `5` | login failure limit |
| `LOGIN_IP_LIMIT` | no | `20` | login ip limit |
| `LOGIN_WINDOW_SECONDS` | no | `15 * 60` | login window seconds |
| `PHOTO_MAX_BYTES` | no | `2 * 1024 * 1024` | photo max bytes |
| `PRIVATE_MEDIA_ROOT` | no | `str(BASE_DIR / 'private_uploads')` | private media root |
| `SECRET_KEY` | production | `required` | secret key |
| `SECURE_CONTENT_TYPE_NOSNIFF` | no | `True` | secure content type nosniff |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | no | `False` | secure hsts include subdomains |
| `SECURE_HSTS_PRELOAD` | no | `False` | secure hsts preload |
| `SECURE_HSTS_SECONDS` | no | `3600` | secure hsts seconds |
| `SECURE_REFERRER_POLICY` | no | `'same-origin'` | secure referrer policy |
| `SECURE_SSL_REDIRECT` | no | `True` | secure ssl redirect |
| `SESSION_COOKIE_AGE` | no | `12 * 60 * 60` | session cookie age |
| `SESSION_COOKIE_SAMESITE` | no | `'Lax'` | session cookie samesite |
| `SESSION_COOKIE_SECURE` | no | `True` | session cookie secure |
| `SIGNUP_IP_LIMIT` | no | `5` | signup ip limit |
| `SIGNUP_WINDOW_SECONDS` | no | `60 * 60` | signup window seconds |
| `SITE_BASE_URL` | production | `'http://127.0.0.1:8000'` | site base url |
| `TRUSTED_PROXY_COUNT` | no | `0` | trusted proxy count |
| `USE_X_FORWARDED_PROTO` | no | `False` | use x forwarded proto |
| `VERIFY_IP_LIMIT` | no | `30` | verify ip limit |
| `VERIFY_WINDOW_SECONDS` | no | `60` | verify window seconds |
| `X_FRAME_OPTIONS` | no | `'DENY'` | x frame options |

## Settings differences

| Module | Differences |
|---|---|
| base + security | Shared domain settings, password validators, HttpOnly cookies, CSP, LocMem cache; DEBUG defaults False |
| dev | DEBUG defaults True; local allowed hosts |
| test | DEBUG False, in-memory SQLite, fast test hasher, in-memory email; cache cleared per test |
| prod | DEBUG always False, required key/hosts/site, HTTPS redirect, secure cookies, conservative HSTS, DatabaseCache, console logging |

## Go-live after HTTPS verification

Verify HTTPS on the host and all subdomains first. Generate a unique random SECRET_KEY; never use this placeholder. Supply real host and signatory values:

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.prod
SECRET_KEY=<unique-random-secret-at-least-50-characters>
ALLOWED_HOSTS=learning.example.org
SITE_BASE_URL=https://learning.example.org
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
CACHE_URL=dbcache://capacity_connect_cache
CACHE_TABLE=capacity_connect_cache
CERTIFICATE_SIGNATORY_NAME=Authorised Signatory
CERTIFICATE_SIGNATORY_TITLE=Programme Director
```

DJANGO_SETTINGS_MODULE is Django's process selector. Conservative code defaults keep HSTS at 3600 seconds, subdomains and preload off, until HTTPS is verified. Enable USE_X_FORWARDED_PROTO only when a trusted proxy removes client-supplied forwarding headers and sets its own. TRUSTED_PROXY_COUNT defaults to zero, ignoring X-Forwarded-For; configure the exact trusted hop count before trusting forwarded client addresses.

Deploy using the production environment for every command:

```sh
python -m pip install -r requirements/base.txt
python manage.py migrate --noinput
python manage.py createcachetable
python manage.py collectstatic --noinput
python manage.py check --deploy --settings=config.settings.prod
```

Start the hosting platform's WSGI process with `config.wsgi:application`. PythonAnywhere can load that module in its WSGI entrypoint; Render can use its Python WSGI service. Linux gunicorn + nginx is an operator option requiring separately approved gunicorn installation; it is not a project dependency. Serve STATIC_ROOT through static hosting. Never alias MEDIA_ROOT or PRIVATE_MEDIA_ROOT. Private files use authorised Django attachment views; no urls.py exposes either root. Keep private uploads outside all document roots and static aliases in dev and prod.

Large-video HTTP Range or nginx internal X-Accel-Redirect support is documented as a future approved change, not implemented. Current downloads stream through Django.

Back up the database and upload roots together, restrict access, encrypt off-host backups and test restoration. Use a consistent SQLite backup operation rather than copying a live database. PostgreSQL would use pg_dump after driver/hosting approval.

Example cron entries (replace paths and load the production environment):

```cron
*/5 * * * * cd /srv/capacity && /srv/capacity/venv/bin/python manage.py evaluate_completions
0 3 * * * cd /srv/capacity && /srv/capacity/venv/bin/python manage.py cleanup_orphan_files --min-age-hours 24
```

Cleanup is dry-run by default. Inspect output before adding --delete. It checks every model FileField reference, excludes recent files and paths resolving outside configured roots, and rechecks references before unlinking. Run deletion during a maintenance window to avoid filesystem/database races. It never recursively deletes directories.

## Commands and demo

`seed_demo_data [--force]` refuses DEBUG=False or production unless forced. Use a disposable development database. A second completed run changes no rows or timestamps. It prints counts and logins; DEMO_PASSWORD defaults to the public development password `Demo-Connect-2026!`. Never deploy demo accounts. PNG is used for a profile photo; library resources are generated PDFs. Names are Indian names in Latin letters.

`cleanup_orphan_files [--min-age-hours 24] [--delete]` lists unreferenced aged files and deletes only with --delete. `evaluate_completions` retries eligible completion and certificate issuance. All support --help.

## Static PostgreSQL review and limitations

Not run against PostgreSQL. Runtime application queries use the ORM; SQLite EXPLAIN QUERY PLAN is confined to local evidence scripts. PostgreSQL supports the existing Decimal fields, Lower-based constraints and partial unique/index conditions. SQLite select_for_update is a no-op, so these tests do not prove concurrent row locking. Case matching/collation and transaction races need PostgreSQL execution after driver approval. DatabaseCache increments are best-effort and non-atomic; throttling is anti-abuse, not a security boundary.

Signup intentionally reports unique username/email conflicts; login reports awaiting approval as specified. Those disclosures remain. The CSP permits self only; the later frontend phase must review font/style requirements in CONTENT_SECURITY_POLICY. Certificate name help requests Latin letters without rejecting other scripts; current PDF font glyph coverage remains limited.
