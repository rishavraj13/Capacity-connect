# Capacity Connect

Capacity Connect is a Django learning-management portal for Trainees, Trainers, and Admins. The current stage is backend only, followed by testing and bug fixing; B2 Catalog and Profiles is in progress.

Binding rules: docs/IMPLEMENTATION_BRIEF.md. Read it before any task.

Models define data; selectors read; services write and enforce rules.
Forms validate input; permissions declare roles; views coordinate HTTP only.
Functions: at most 25 lines and 4 parameters; modules: at most 250 lines.
Views: at most 15 lines of logic; use type hints and one-line why docstrings.

Run before reporting (activate venv first):
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

Use the section 12 report format. Never start a phase without approval.
