# Capacity Connect - Backend Portal

Capacity Connect is a Django learning-management portal for Trainees, Trainers, and Admins.
Read docs/IMPLEMENTATION_BRIEF.md for binding scope and docs/PROGRESS.md for current status.

## Local setup (Windows PowerShell)

After cloning the repository, start from the approved main branch:

```powershell
git switch main
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements/dev.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Set a strong SECRET_KEY in .env before deployment. Never commit .env.
Open /login/ locally with the created administrator account.

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
