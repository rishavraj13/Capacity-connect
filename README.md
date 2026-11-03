# Capacity Connect - Backend Portal

Capacity Connect is a Django learning-management portal for Trainees, Trainers, and Admins.
Read docs/IMPLEMENTATION_BRIEF.md for binding scope and docs/PROGRESS.md for current status.

## Local setup (Windows PowerShell)

Clone main for an approved release. When validating an explicitly selected review branch, keep that branch throughout these setup commands:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements/dev.txt -c requirements/constraints.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data
python manage.py runserver
```

Set a strong SECRET_KEY in .env before deployment. Never commit .env.
Open /login/ locally with the created administrator account.

The committed constraints pin all 20 distributions from the verified Python 3.14.6 Windows environment, including transitive packages and pip. Use the constraint file on every install; constraints limit versions but do not install packages by themselves. See ADR 072 for upgrades and refresh instructions.

## Verify

With the virtual environment active:

```powershell
pytest
coverage run -m pytest
coverage report -m
ruff check .
ruff format --check .
python manage.py makemigrations --check
python manage.py check
python -m pip check
```

## Private uploads and production

Profile files live in PRIVATE_MEDIA_ROOT (default: private_uploads/), separate from
MEDIA_ROOT and STATIC_ROOT. No urls.py serves that directory. Never configure a
web-server alias for PRIVATE_MEDIA_ROOT; authenticated downloads use the profiles
file view. Production requires SECRET_KEY and ALLOWED_HOSTS environment values.

Verification transcripts are local ignored evidence under .local/reports/.

## Requirements and app map

Python 3.14, Django 5.x and requirements/dev.txt. Core supplies clock, storage, throttles and operational commands; accounts manages approval and roles; catalog/profiles manage skills and people; courses/library manage learning; assessments grades attempts; feedback/certificates manage completion evidence; competency/announcements/dashboards provide ranking and reporting.

Demo password: `Demo-Connect-2026!` (DEMO_PASSWORD override). The seed prints all login names and statuses. Use `python manage.py cleanup_orphan_files` for a dry run; add --delete only after reviewing candidates. `python manage.py evaluate_completions` retries completion/certificates.

See [deployment and environment catalogue](docs/DEPLOYMENT.md), [decisions](docs/DECISIONS.md), [progress](docs/PROGRESS.md) and [binding brief](docs/IMPLEMENTATION_BRIEF.md).

## Line design foundations

Run `python manage.py runserver` and open `/styleguide/` with `DEBUG=True` to review the components. Use the Theme control to choose Day, Night or Signage. The browser remembers the choice locally. On first visit the theme follows the system dark preference and otherwise starts in Day. Forms and the collapsible navigation work without JavaScript.

Django serves `static/` during development. For deployment, run `python manage.py collectstatic --noinput` and serve the collected directory at `/static/`. See [deployment instructions](docs/DEPLOYMENT.md) and [font sources](static/fonts/SOURCES.md).

See the [frontend report](docs/FRONTEND_REPORT.md) and [accessibility checklist](docs/ACCESSIBILITY.md). For local visual evidence, open \`.local/screenshots/INDEX.html\` when the ignored screenshots are available. The seed command prints the demo logins. Use the theme control for Day, Night or Signage.
