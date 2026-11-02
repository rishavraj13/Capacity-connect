PHASE / TASK: B2 Catalog and Profiles, including Steps A-C and phase-table correction

STATUS: Done

GOAL: Deliver the catalog, role-specific profiles and private uploads with tested authorization, while preserving the approved B1 baseline.

WHAT CHANGED:

Historical B2 submission: superseded by the B2.1 review. B2 is not approved or merged. The figures below describe that earlier run.

- Git: fast-forwarded main to B1 commit 1a7618a; tagged b1-approved; created phase/b2-catalog-profiles. First B2 commit aadef76 is exactly `docs: align PROGRESS.md phases with brief section 8`; only PROGRESS.md and appended ADR 015 changed. Second commit 5954e74 adds AGENTS.md.
- Housekeeping: split authentication/admin view tests; shared matrix helper with readable IDs; enabled branch coverage; fixed HTTPS next redirects and required production hosts. Added failing regression tests before fixes.
- Catalog: Subject and Skill with database Lower(name) uniqueness, protected subject references, services, optimized selectors, form validation, approved-user listing and Admin write actions.
- Profiles: TraineeProfile, TrainerProfile, Qualification, WorkExperience and ExternalCertificate; lazy idempotent profile creation; basic account editing for every approved role; private selectors and owner-only child writes; service allowlists and cleanup.
- Core: UUID UploadPath, extension/size/content validators, PrivateStorage, PrivateFileInput and shared form coordination. Bare semantic templates and role-aware nav link to new features.
- Tests/docs: factories, 366 matrix cases (54 preserved B1 + 96 catalog + 216 profiles), all 19 new write-route CSRF checks, IDOR, uploads, constraints, file cleanup and query counts. ADRs 015-023 and BUGs 001-005 recorded. No dependencies added; no B3 work.

Corrected phase table, copied exactly from brief section 8:

| Phase | Scope | Gate (acceptance criteria) |
|---|---|---|
| **B0 Foundations** | Repo, virtualenv, split settings, `.env`, ruff, pytest, `core` app, custom `User` model and first migration | `pytest` runs, `ruff` clean, migrations apply on a fresh DB |
| **B1 Accounts** | Signup with role choice, approval gate at login, role mixins, admin user management (approve, reject, change role) | Unapproved login blocked; role isolation tests pass |
| **B2 Catalog and Profiles** | Subjects, skills, both profiles, qualifications, experience, external certificates, upload validation | Profile CRUD works per role; invalid uploads rejected |
| **B3 Courses and Library** | Courses, modules, enrollment, progress, library uploads and listing | Ownership enforced; duplicate enrollment impossible; `station_map_for` correct |
| **B4 Assessments** | Questionnaires, questions, options, attempt flow, auto-grading, deadlines, results, trainer participation view | All business rules 2 to 4 proven by tests, including boundary times |
| **B5 Feedback and Certificates** | Ratings, completion logic, certificate issuance, PDF, public verification by ID | Certificate issued exactly once; PDF opens; verification works |
| **B6 Competency, Announcements, Dashboards** | Ranking selector, announcement CRUD and publish flow, admin analytics selectors | Ranking matches the formula in tests; unpublished items never appear |
| **B7 Hardening** | Security pass, query optimisation, settings review, seed command, README | Section 11 checklist fully ticked |

HOW IT WAS VERIFIED:

Commands use the existing venv executables; `pytest` was invoked as `venv/Scripts/python.exe -m pytest`. The complete stdout/stderr, including every test ID, migration and traceback, is pasted in [local ignored B2 transcript](../.local/reports/B2_GATE_OUTPUT.txt).

Baseline from Step A, before changes (real output summary):

```text
python --version: Python 3.14.6
python -m django --version: 5.2.18
git status:
On branch phase/b1-accounts
nothing to commit, working tree clean
git branch -a:
  main
  phase/b0-foundations
* phase/b1-accounts
git tag:
b0-approved
pytest:
============================= 115 passed in 1.32s =============================
coverage run -m pytest:
============================= 115 passed in 1.38s =============================
coverage report -m:
TOTAL                            325      0   100%
ruff check .:
All checks passed!
ruff format --check .:
44 files already formatted
python manage.py makemigrations --check:
No changes detected
python manage.py check:
System check identified no issues (0 silenced).
python -m pip check:
No broken requirements found.
```

Baseline fresh migrations all applied, including accounts.0001_initial and accounts.0002_user_unique_lower_email. The earlier report accidentally transcribed auth.0010 incorrectly before correcting it; the real migration was auth.0010_alter_group_name_max_length, which succeeded.

Final documentation quality check after adding this report: `ruff check .` returned `All checks passed!`; `ruff format --check .` returned `95 files already formatted`; `git diff --check` produced no output. The gate transcript's 94-file formatting count predates this report.

Actual PowerShell wc invocation (Git's bundled executable; the same complete 4416-line file set is pasted below):

```powershell
$projectPythonFiles = rg --files -g '*.py' -g '!venv/**' -g '!.venv/**' -g '!**/migrations/**'
& 'C:\Program Files\Git\usr\bin\wc.exe' -l $projectPythonFiles
```

Final gate output excerpts (full unabridged pytest output is in the transcript):

`pytest` - exit 0:

```text
apps/profiles/tests/test_forms.py::test_forms_have_no_privileged_fields[ExternalCertificateForm] PASSED [100%]

============================= 517 passed in 6.10s =============================
```

`coverage run -m pytest` - exit 0:

```text
apps/profiles/tests/test_forms.py::test_forms_have_no_privileged_fields[ExternalCertificateForm] PASSED [100%]

============================= 517 passed in 5.62s =============================
```

`coverage report -m` - exit 0:

```text
Name                              Stmts   Miss Branch BrPart  Cover   Missing
-----------------------------------------------------------------------------
apps\__init__.py                      0      0      0      0   100%
apps\accounts\__init__.py             0      0      0      0   100%
apps\accounts\admin.py               10      0      0      0   100%
apps\accounts\apps.py                 5      0      0      0   100%
apps\accounts\constants.py           15      0      0      0   100%
apps\accounts\forms.py               51      0     16      0   100%
apps\accounts\managers.py            19      0      4      0   100%
apps\accounts\models.py              19      0      0      0   100%
apps\accounts\permissions.py         30      0     12      0   100%
apps\accounts\selectors.py           18      0      8      0   100%
apps\accounts\services.py            38      0     12      0   100%
apps\accounts\urls.py                 3      0      0      0   100%
apps\accounts\views.py               99      0     24      2    98%   52->65, 157->163
apps\catalog\__init__.py              0      0      0      0   100%
apps\catalog\admin.py                 0      0      0      0   100%
apps\catalog\apps.py                  4      0      0      0   100%
apps\catalog\constants.py             1      0      0      0   100%
apps\catalog\forms.py                14      0      0      0   100%
apps\catalog\models.py               21      0      0      0   100%
apps\catalog\selectors.py            17      0      0      0   100%
apps\catalog\services.py             44      0      4      0   100%
apps\catalog\urls.py                  4      0      0      0   100%
apps\catalog\views.py                42      0      0      0   100%
apps\core\__init__.py                 0      0      0      0   100%
apps\core\apps.py                     5      0      0      0   100%
apps\core\constants.py                0      0      0      0   100%
apps\core\exceptions.py               8      0      0      0   100%
apps\core\form_views.py              23      0      2      0   100%
apps\core\models.py                   7      0      0      0   100%
apps\core\storage.py                  6      0      0      0   100%
apps\core\uploads.py                 15      0      2      0   100%
apps\core\validators.py              37      0     10      0   100%
apps\core\widgets.py                  6      0      0      0   100%
apps\profiles\__init__.py             0      0      0      0   100%
apps\profiles\admin.py                0      0      0      0   100%
apps\profiles\apps.py                 4      0      0      0   100%
apps\profiles\constants.py           11      0      0      0   100%
apps\profiles\forms.py               42      0      2      0   100%
apps\profiles\models.py              40      0      0      0   100%
apps\profiles\selectors.py           20      0      2      0   100%
apps\profiles\services.py            60      0     16      0   100%
apps\profiles\urls.py                 4      0      0      0   100%
apps\profiles\views\__init__.py       0      0      0      0   100%
apps\profiles\views\children.py      61      0      0      0   100%
apps\profiles\views\files.py         26      0      4      0   100%
apps\profiles\views\profiles.py      38      0      0      0   100%
-----------------------------------------------------------------------------
TOTAL                               867      0    118      2    99%
```

`ruff check .` - exit 0:

```text
All checks passed!
```

`ruff format --check .` - exit 0:

```text
94 files already formatted
```

`python manage.py makemigrations --check` - exit 0:

```text
No changes detected
```

`python manage.py check` - exit 0:

```text
System check identified no issues (0 silenced).
```

`python -m pip check` - exit 0:

```text
No broken requirements found.
```

`python manage.py migrate --noinput (fresh temporary DATABASE_URL)` - exit 0:

```text
Operations to perform:
  Apply all migrations: accounts, admin, auth, catalog, contenttypes, profiles, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying accounts.0001_initial... OK
  Applying accounts.0002_user_unique_lower_email... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying catalog.0001_initial... OK
  Applying profiles.0001_initial... OK
  Applying profiles.0002_alter_externalcertificate_file_and_more... OK
  Applying profiles.0003_alter_qualification_year... OK
  Applying sessions.0001_initial... OK
```

`python manage.py check --deploy --settings=config.settings.prod (temporary strong key and explicit host)` - exit 0:

```text
System check identified some issues:

WARNINGS:
?: (security.W005) You have not set the SECURE_HSTS_INCLUDE_SUBDOMAINS setting to True. Without this, your site is potentially vulnerable to attack via an insecure connection to a subdomain. Only set this to True if you are certain that all subdomains of your domain should be served exclusively via SSL.
?: (security.W021) You have not set the SECURE_HSTS_PRELOAD setting to True. Without this, your site cannot be submitted to the browser preload list.

System check identified 2 issues (0 silenced).
```

`python manage.py check --settings=config.settings.prod with SECRET_KEY unset (isolated subprocess; .env autoload disabled via read_env mock)` - exit 1:

```text
Traceback (most recent call last):
  File "C:\Django\Project\venv\Lib\site-packages\environ\environ.py", line 520, in get_value
    value = self.ENVIRON[var_name]
            ~~~~~~~~~~~~^^^^^^^^^^
  File "<frozen os>", line 709, in __getitem__
KeyError: 'SECRET_KEY'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import runpy, sys; from unittest.mock import patch; sys.argv=['manage.py','check','--settings=config.settings.prod']; guard=patch('environ.Env.read_env'); guard.start(); runpy.run_path('manage.py',run_name='__main__')
                                                                                                                                                                              ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen runpy>", line 294, in run_path
  File "<frozen runpy>", line 98, in _run_module_code
  File "<frozen runpy>", line 88, in _run_code
  File "manage.py", line 22, in <module>
    main()
    ~~~~^^
  File "manage.py", line 18, in main
    execute_from_command_line(sys.argv)
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\core\management\__init__.py", line 442, in execute_from_command_line
    utility.execute()
    ~~~~~~~~~~~~~~~^^
  File "C:\Django\Project\venv\Lib\site-packages\django\core\management\__init__.py", line 436, in execute
    self.fetch_command(subcommand).run_from_argv(self.argv)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\core\management\base.py", line 412, in run_from_argv
    parser = self.create_parser(argv[0], argv[1])
  File "C:\Django\Project\venv\Lib\site-packages\django\core\management\base.py", line 375, in create_parser
    self.add_arguments(parser)
    ~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\core\management\commands\check.py", line 47, in add_arguments
    choices=tuple(connections),
            ~~~~~^^^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\utils\connection.py", line 73, in __iter__
    return iter(self.settings)
                ^^^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\utils\functional.py", line 47, in __get__
    res = instance.__dict__[self.name] = self.func(instance)
                                         ~~~~~~~~~^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\utils\connection.py", line 45, in settings
    self._settings = self.configure_settings(self._settings)
                     ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\db\utils.py", line 148, in configure_settings
    databases = super().configure_settings(databases)
  File "C:\Django\Project\venv\Lib\site-packages\django\utils\connection.py", line 50, in configure_settings
    settings = getattr(django_settings, self.settings_name)
  File "C:\Django\Project\venv\Lib\site-packages\django\conf\__init__.py", line 81, in __getattr__
    self._setup(name)
    ~~~~~~~~~~~^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\conf\__init__.py", line 68, in _setup
    self._wrapped = Settings(settings_module)
                    ~~~~~~~~^^^^^^^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\conf\__init__.py", line 166, in __init__
    mod = importlib.import_module(self.SETTINGS_MODULE)
  File "C:\Users\risha\anaconda3\Lib\importlib\__init__.py", line 88, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1406, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1371, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1342, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 938, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 759, in exec_module
  File "<frozen importlib._bootstrap>", line 491, in _call_with_frames_removed
  File "C:\Django\Project\config\settings\prod.py", line 5, in <module>
    from config.settings.base import *  # noqa: F403
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Django\Project\config\settings\base.py", line 17, in <module>
    SECRET_KEY: str = env("SECRET_KEY")
                      ~~~^^^^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\environ\environ.py", line 250, in __call__
    return self.get_value(
           ~~~~~~~~~~~~~~^
        var,
        ^^^^
    ...<2 lines>...
        parse_default=parse_default
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\Django\Project\venv\Lib\site-packages\environ\environ.py", line 524, in get_value
    raise ImproperlyConfigured(error_msg) from exc
django.core.exceptions.ImproperlyConfigured: Set the SECRET_KEY environment variable
```

`python manage.py check --settings=config.settings.prod with ALLOWED_HOSTS unset (isolated subprocess; .env autoload disabled via read_env mock)` - exit 1:

```text
Traceback (most recent call last):
  File "C:\Django\Project\venv\Lib\site-packages\environ\environ.py", line 520, in get_value
    value = self.ENVIRON[var_name]
            ~~~~~~~~~~~~^^^^^^^^^^
  File "<frozen os>", line 709, in __getitem__
KeyError: 'ALLOWED_HOSTS'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import runpy, sys; from unittest.mock import patch; sys.argv=['manage.py','check','--settings=config.settings.prod']; guard=patch('environ.Env.read_env'); guard.start(); runpy.run_path('manage.py',run_name='__main__')
                                                                                                                                                                              ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen runpy>", line 294, in run_path
  File "<frozen runpy>", line 98, in _run_module_code
  File "<frozen runpy>", line 88, in _run_code
  File "manage.py", line 22, in <module>
    main()
    ~~~~^^
  File "manage.py", line 18, in main
    execute_from_command_line(sys.argv)
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\core\management\__init__.py", line 442, in execute_from_command_line
    utility.execute()
    ~~~~~~~~~~~~~~~^^
  File "C:\Django\Project\venv\Lib\site-packages\django\core\management\__init__.py", line 436, in execute
    self.fetch_command(subcommand).run_from_argv(self.argv)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\core\management\base.py", line 412, in run_from_argv
    parser = self.create_parser(argv[0], argv[1])
  File "C:\Django\Project\venv\Lib\site-packages\django\core\management\base.py", line 375, in create_parser
    self.add_arguments(parser)
    ~~~~~~~~~~~~~~~~~~^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\core\management\commands\check.py", line 47, in add_arguments
    choices=tuple(connections),
            ~~~~~^^^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\utils\connection.py", line 73, in __iter__
    return iter(self.settings)
                ^^^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\utils\functional.py", line 47, in __get__
    res = instance.__dict__[self.name] = self.func(instance)
                                         ~~~~~~~~~^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\utils\connection.py", line 45, in settings
    self._settings = self.configure_settings(self._settings)
                     ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\db\utils.py", line 148, in configure_settings
    databases = super().configure_settings(databases)
  File "C:\Django\Project\venv\Lib\site-packages\django\utils\connection.py", line 50, in configure_settings
    settings = getattr(django_settings, self.settings_name)
  File "C:\Django\Project\venv\Lib\site-packages\django\conf\__init__.py", line 81, in __getattr__
    self._setup(name)
    ~~~~~~~~~~~^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\conf\__init__.py", line 68, in _setup
    self._wrapped = Settings(settings_module)
                    ~~~~~~~~^^^^^^^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\django\conf\__init__.py", line 166, in __init__
    mod = importlib.import_module(self.SETTINGS_MODULE)
  File "C:\Users\risha\anaconda3\Lib\importlib\__init__.py", line 88, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1406, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1371, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1342, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 938, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 759, in exec_module
  File "<frozen importlib._bootstrap>", line 491, in _call_with_frames_removed
  File "C:\Django\Project\config\settings\prod.py", line 8, in <module>
    ALLOWED_HOSTS: list[str] = environ.Env().list("ALLOWED_HOSTS")
                               ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "C:\Django\Project\venv\Lib\site-packages\environ\environ.py", line 339, in list
    return self.get_value(
           ~~~~~~~~~~~~~~^
        var,
        ^^^^
        cast=list if not cast else [cast],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        default=default
        ^^^^^^^^^^^^^^^
    )
    ^
  File "C:\Django\Project\venv\Lib\site-packages\environ\environ.py", line 524, in get_value
    raise ImproperlyConfigured(error_msg) from exc
django.core.exceptions.ImproperlyConfigured: Set the ALLOWED_HOSTS environment variable
```

`python manage.py shell --settings=config.settings.prod -c <cookie/host/HSTS settings>` - exit 0:

```text
13 objects imported automatically (use -v 2 for details).

{'ALLOWED_HOSTS': ['capacity.example.com'], 'SESSION_COOKIE_HTTPONLY': True, 'CSRF_COOKIE_HTTPONLY': False, 'SECURE_HSTS_SECONDS': 3600, 'SECURE_HSTS_INCLUDE_SUBDOMAINS': False, 'SECURE_HSTS_PRELOAD': False}
```

`pytest apps/accounts/tests/test_permissions.py -k test_permission_matrix` - exit 0:

```text
apps/accounts/tests/test_permissions.py::test_permission_matrix[rejected_user-logout-POST] PASSED [100%]

====================== 54 passed, 4 deselected in 0.65s =======================
```

`git diff --check` - exit 0:

```text

```

`rg -n -i --hidden -g !.git/** -g !venv/** -g !.venv/** -g !.env -g !*.sqlite3 -g !.coverage "Course & Curriculum|Course & Competency|Assessment Engine|Verification & PDF|Verification & Certification|Executive Summary|Phased Delivery Roadmap|\bB[0-7]\b|phase [0-7]" .` - exit 0:

```text
.\README.md:9:   git checkout phase/b0-foundations
.\AGENTS.md:3:Capacity Connect is a Django learning-management portal for Trainees, Trainers, and Admins. The current stage is backend only, followed by testing and bug fixing; B2 Catalog and Profiles is in progress.
.\docs\PROGRESS.md:7:| **B0 Foundations** | Repo, virtualenv, split settings, `.env`, ruff, pytest, `core` app, custom `User` model and first migration | `pytest` runs, `ruff` clean, migrations apply on a fresh DB |
.\docs\PROGRESS.md:8:| **B1 Accounts** | Signup with role choice, approval gate at login, role mixins, admin user management (approve, reject, change role) | Unapproved login blocked; role isolation tests pass |
.\docs\PROGRESS.md:9:| **B2 Catalog and Profiles** | Subjects, skills, both profiles, qualifications, experience, external certificates, upload validation | Profile CRUD works per role; invalid uploads rejected |
.\docs\PROGRESS.md:10:| **B3 Courses and Library** | Courses, modules, enrollment, progress, library uploads and listing | Ownership enforced; duplicate enrollment impossible; `station_map_for` correct |
.\docs\PROGRESS.md:11:| **B4 Assessments** | Questionnaires, questions, options, attempt flow, auto-grading, deadlines, results, trainer participation view | All business rules 2 to 4 proven by tests, including boundary times |
.\docs\PROGRESS.md:12:| **B5 Feedback and Certificates** | Ratings, completion logic, certificate issuance, PDF, public verification by ID | Certificate issued exactly once; PDF opens; verification works |
.\docs\PROGRESS.md:13:| **B6 Competency, Announcements, Dashboards** | Ranking selector, announcement CRUD and publish flow, admin analytics selectors | Ranking matches the formula in tests; unpublished items never appear |
.\docs\PROGRESS.md:14:| **B7 Hardening** | Security pass, query optimisation, settings review, seed command, README | Section 11 checklist fully ticked |
.\docs\PROGRESS.md:16:Status: B0 and B1 approved; B2 in progress; B3 through B7 not started. Historical fix rounds remain below.
.\docs\PROGRESS.md:18:## Phase B1.1 Fix Round Changelog
.\docs\PROGRESS.md:31:## Phase B1 Changelog
.\docs\PROGRESS.md:44:## Phase B0.1 Changelog
.\docs\PROGRESS.md:54:## B2 housekeeping (in progress)
.\docs\PROGRESS.md:55:- [x] B1 merged into main and tagged b1-approved.
.\docs\PROGRESS.md:56:- [x] Phase table corrected and ADR 015 appended in the first B2 commit.
.\docs\PROGRESS.md:65:- [ ] Complete final verification and deliver section 12 report; await B2 approval.
.\docs\IMPLEMENTATION_BRIEF.md:13:1. **Build** the backend phases B0 to B7 (section 8).
.\docs\IMPLEMENTATION_BRIEF.md:174:One Git branch per phase (`phase/b1-accounts`), Conventional Commits (`feat:`, `fix:`, `test:`, `refactor:`, `docs:`). **A phase is not done until its gate passes and its report is delivered.** Do not start the next phase before the user replies "approved" to your report.
.\docs\IMPLEMENTATION_BRIEF.md:180:| **B0 Foundations** | Repo, virtualenv, split settings, `.env`, ruff, pytest, `core` app, custom `User` model and first migration | `pytest` runs, `ruff` clean, migrations apply on a fresh DB |
.\docs\IMPLEMENTATION_BRIEF.md:181:| **B1 Accounts** | Signup with role choice, approval gate at login, role mixins, admin user management (approve, reject, change role) | Unapproved login blocked; role isolation tests pass |
.\docs\IMPLEMENTATION_BRIEF.md:182:| **B2 Catalog and Profiles** | Subjects, skills, both profiles, qualifications, experience, external certificates, upload validation | Profile CRUD works per role; invalid uploads rejected |
.\docs\IMPLEMENTATION_BRIEF.md:183:| **B3 Courses and Library** | Courses, modules, enrollment, progress, library uploads and listing | Ownership enforced; duplicate enrollment impossible; `station_map_for` correct |
.\docs\IMPLEMENTATION_BRIEF.md:184:| **B4 Assessments** | Questionnaires, questions, options, attempt flow, auto-grading, deadlines, results, trainer participation view | All business rules 2 to 4 proven by tests, including boundary times |
.\docs\IMPLEMENTATION_BRIEF.md:185:| **B5 Feedback and Certificates** | Ratings, completion logic, certificate issuance, PDF, public verification by ID | Certificate issued exactly once; PDF opens; verification works |
.\docs\IMPLEMENTATION_BRIEF.md:186:| **B6 Competency, Announcements, Dashboards** | Ranking selector, announcement CRUD and publish flow, admin analytics selectors | Ranking matches the formula in tests; unpublished items never appear |
.\docs\IMPLEMENTATION_BRIEF.md:187:| **B7 Hardening** | Security pass, query optimisation, settings review, seed command, README | Section 11 checklist fully ticked |
.\docs\IMPLEMENTATION_BRIEF.md:191:## 9. Testing (after B7, but tests are written **with** every phase)
.\docs\IMPLEMENTATION_BRIEF.md:212:## 11. Security checklist (gate for B7)
.\docs\IMPLEMENTATION_BRIEF.md:281:Begin with **B0**. Before writing code, reply with a short plan for B0 in the section 12 format (status "Needs decision" only if something is unclear), then proceed.
.\docs\BUGS.md:5:| None | No defects recorded in Phase B0 | - | - | - |
.\docs\BUGS.md:12:- Commit: fix(accounts): preserve HTTPS login redirects (B2 housekeeping).
.\docs\DECISIONS.md:29:- **Context:** Although not strictly enumerated in the raw B0 deliverable list, administrative visibility into custom user attributes is necessary for operator workflows.
.\docs\DECISIONS.md:60:- **Consequences:** Post-login redirection logic and role permission matrices remain immutable across Phase B2 through B7 evolutions.
.\docs\DECISIONS.md:62:## ADR 011: Deferral of Authentication Throttling to Phase B7
.\docs\DECISIONS.md:64:- **Decision:** Rate limiting and request throttling on `/signup/` and `/login/` endpoints are explicitly deferred from Phase B1 to Phase B7 (Security & Hardening).
.\docs\DECISIONS.md:65:- **Consequences:** B1 remains focused on foundational authentication mechanics and role access control; security throttling will be systematically layered in during Phase B7.
.\docs\DECISIONS.md:113:- **Consequences:** New views declare roles explicitly, remain thin, and share validation-error presentation. Catalog matrix has 96 cases; profiles have 216 cases including three private-file variants. The approved B1 matrix retains all 54 cases with readable actor-url_name-METHOD IDs.
.\docs\DECISIONS.md:118:- **Consequences:** All application and test modules remain limited to 250 lines; the final wc/AST audit excludes generated migrations as requested in the B2 gate.
.\apps\accounts\tests\test_permissions.py:77:    """Preserve the approved B1 permission contract through shared machinery."""
```

`AST longest functions: end_lineno - lineno + 1; top 10; all functions <=25` - exit 0:

```text
24 apps/profiles/tests/test_crud.py:20 test_trainee_profile_post_and_private_photo
24 apps/profiles/tests/test_crud.py:116 test_child_create_edit_delete
24 apps/accounts/permissions.py:36 role_required
24 apps/accounts/forms.py:79 clean
23 apps/profiles/tests/test_permissions.py:94 matrix_target
23 apps/profiles/tests/test_permissions.py:53 expected_status
23 apps/accounts/tests/test_settings.py:17 test_production_requires_allowed_hosts
22 apps/core/validators.py:28 validate_content
21 apps/profiles/views/files.py:28 private_file
21 apps/profiles/tests/test_services.py:90 test_child_save_delete_and_certificate_cleanup
```

`"C:\Program Files\Git\usr\bin\wc.exe" -l <every .py under apps/ and config/, plus manage.py; migrations excluded>` - exit 0:

```text
     1 apps/__init__.py
     1 apps/accounts/__init__.py
    32 apps/accounts/admin.py
    11 apps/accounts/apps.py
    42 apps/accounts/constants.py
   111 apps/accounts/forms.py
    52 apps/accounts/managers.py
    51 apps/accounts/models.py
    59 apps/accounts/permissions.py
    44 apps/accounts/selectors.py
    82 apps/accounts/services.py
     1 apps/accounts/tests/__init__.py
    75 apps/accounts/tests/factories.py
   120 apps/accounts/tests/test_admin_views.py
   152 apps/accounts/tests/test_auth_views.py
   193 apps/accounts/tests/test_forms.py
    89 apps/accounts/tests/test_models.py
   133 apps/accounts/tests/test_permissions.py
    63 apps/accounts/tests/test_selectors.py
   130 apps/accounts/tests/test_services.py
    39 apps/accounts/tests/test_settings.py
    35 apps/accounts/urls.py
   163 apps/accounts/views.py
     0 apps/catalog/__init__.py
     1 apps/catalog/admin.py
    10 apps/catalog/apps.py
     3 apps/catalog/constants.py
    31 apps/catalog/forms.py
    48 apps/catalog/models.py
    43 apps/catalog/selectors.py
    74 apps/catalog/services.py
     0 apps/catalog/tests/__init__.py
    29 apps/catalog/tests/factories.py
    84 apps/catalog/tests/test_catalog.py
    58 apps/catalog/tests/test_permissions.py
    59 apps/catalog/tests/test_views.py
    25 apps/catalog/urls.py
    82 apps/catalog/views.py
     1 apps/core/__init__.py
    11 apps/core/apps.py
     1 apps/core/constants.py
    26 apps/core/exceptions.py
    39 apps/core/form_views.py
    22 apps/core/models.py
    13 apps/core/storage.py
     1 apps/core/tests/__init__.py
    47 apps/core/tests/matrix.py
    24 apps/core/tests/test_core.py
    39 apps/core/tests/test_csrf.py
    25 apps/core/tests/test_form_views.py
    77 apps/core/tests/test_uploads.py
    25 apps/core/uploads.py
    63 apps/core/validators.py
    15 apps/core/widgets.py
     0 apps/profiles/__init__.py
     1 apps/profiles/admin.py
    10 apps/profiles/apps.py
    13 apps/profiles/constants.py
    98 apps/profiles/forms.py
   119 apps/profiles/models.py
    49 apps/profiles/selectors.py
   114 apps/profiles/services.py
     0 apps/profiles/tests/__init__.py
     9 apps/profiles/tests/conftest.py
    95 apps/profiles/tests/factories.py
   155 apps/profiles/tests/test_crud.py
    84 apps/profiles/tests/test_files.py
    79 apps/profiles/tests/test_forms.py
    55 apps/profiles/tests/test_idor.py
    46 apps/profiles/tests/test_models.py
   125 apps/profiles/tests/test_permissions.py
    51 apps/profiles/tests/test_selectors.py
   146 apps/profiles/tests/test_services.py
    45 apps/profiles/urls.py
     1 apps/profiles/views/__init__.py
   116 apps/profiles/views/children.py
    48 apps/profiles/views/files.py
    85 apps/profiles/views/profiles.py
     1 config/__init__.py
     9 config/asgi.py
     1 config/settings/__init__.py
   114 config/settings/base.py
     9 config/settings/dev.py
    22 config/settings/prod.py
    19 config/settings/test.py
    11 config/urls.py
     9 config/wsgi.py
    22 manage.py
  4416 total
```

Contamination sweep interpretation: only the stale PROGRESS table contained reconstructed phase scopes; all were corrected in aadef76. Remaining matches are the binding table, accurate historical notes, current phase status, and the existing B0 setup-branch reference. The command includes docs, README, Python comments/docstrings/test names, and hidden repository content; Git internals, dependencies, secrets and database/coverage binaries are excluded. The pasted sweep was captured before this evidence report was added, to avoid matching its quoted search patterns.

Production isolation proof: to test an unset environment variable without changing the developer's .env file, each command ran through this subprocess wrapper with the relevant key removed from os.environ; the other required variable was supplied. Only .env autoload was disabled; Django's settings and check command were real:

```python
import runpy, sys
from unittest.mock import patch

sys.argv = ["manage.py", "check", "--settings=config.settings.prod"]
with patch("environ.Env.read_env"):
    runpy.run_path("manage.py", run_name="__main__")
```

Coverage totals: 867/867 statements; 116/118 branches (98.31% branch coverage); combined coverage displayed by coverage.py is 99%. Every services/selectors/permissions/forms module has 100% combined coverage. Only two inherited accounts.views branches remain uncovered (52->65 and 157->163). Query tests prove subjects_with_skills uses 2 queries and the complete trainee detail HTTP response uses 8 with multiple children/skills. All application/test modules are at most 193 lines; the longest function is 24 lines. The 297-line generated initial profiles migration is explicitly exempt under ADR 023 by user approval.

Permission matrix: statuses are tested expectations, not inferred from decorators. Inactive accounts are treated as anonymous by Django. Private-file rows distinguish the three variants of the same named URL. Read/form POSTs with empty input return validation pages; the trainee profile empty POST is valid and redirects. Destructive/lifecycle GETs return 405 for authorized actors; form GETs display forms without submitting changes.

| URL name / variant | Method | Anonymous | Trainee | Trainer | Admin | Unapproved | Inactive |
|---|---|---:|---:|---:|---:|---:|---:|
| trainee_home | GET | 302 | 200 | 403 | 403 | 403 | 302 |
| trainer_home | GET | 302 | 403 | 200 | 403 | 403 | 302 |
| admin_panel | GET | 302 | 403 | 403 | 200 | 403 | 302 |
| admin_user_list | GET | 302 | 403 | 403 | 200 | 403 | 302 |
| admin_pending_list | GET | 302 | 403 | 403 | 200 | 403 | 302 |
| admin_approve_user | POST | 302 | 403 | 403 | 302 | 403 | 302 |
| admin_reject_user | POST | 302 | 403 | 403 | 302 | 403 | 302 |
| admin_change_role | POST | 302 | 403 | 403 | 302 | 403 | 302 |
| logout | POST | 302 | 302 | 302 | 302 | 302 | 302 |
| catalog:subject_list | GET | 302 | 200 | 200 | 200 | 403 | 302 |
| catalog:subject_list | POST | 302 | 405 | 405 | 405 | 403 | 302 |
| catalog:subject_create | GET | 302 | 403 | 403 | 200 | 403 | 302 |
| catalog:subject_create | POST | 302 | 403 | 403 | 200 | 403 | 302 |
| catalog:subject_edit | GET | 302 | 403 | 403 | 200 | 403 | 302 |
| catalog:subject_edit | POST | 302 | 403 | 403 | 200 | 403 | 302 |
| catalog:subject_deactivate | GET | 302 | 403 | 403 | 405 | 403 | 302 |
| catalog:subject_deactivate | POST | 302 | 403 | 403 | 302 | 403 | 302 |
| catalog:subject_reactivate | GET | 302 | 403 | 403 | 405 | 403 | 302 |
| catalog:subject_reactivate | POST | 302 | 403 | 403 | 302 | 403 | 302 |
| catalog:skill_create | GET | 302 | 403 | 403 | 200 | 403 | 302 |
| catalog:skill_create | POST | 302 | 403 | 403 | 200 | 403 | 302 |
| catalog:skill_edit | GET | 302 | 403 | 403 | 200 | 403 | 302 |
| catalog:skill_edit | POST | 302 | 403 | 403 | 200 | 403 | 302 |
| catalog:skill_delete | GET | 302 | 403 | 403 | 405 | 403 | 302 |
| catalog:skill_delete | POST | 302 | 403 | 403 | 302 | 403 | 302 |
| profiles:profile_list | GET | 302 | 200 | 200 | 200 | 403 | 302 |
| profiles:profile_list | POST | 302 | 405 | 405 | 405 | 403 | 302 |
| profiles:account_edit | GET | 302 | 200 | 200 | 200 | 403 | 302 |
| profiles:account_edit | POST | 302 | 200 | 200 | 200 | 403 | 302 |
| profiles:trainee_detail | GET | 302 | 200 | 404 | 200 | 403 | 302 |
| profiles:trainee_detail | POST | 302 | 405 | 405 | 405 | 403 | 302 |
| profiles:trainer_detail | GET | 302 | 200 | 200 | 200 | 403 | 302 |
| profiles:trainer_detail | POST | 302 | 405 | 405 | 405 | 403 | 302 |
| profiles:trainee_edit | GET | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:trainee_edit | POST | 302 | 302 | 403 | 403 | 403 | 302 |
| profiles:trainer_edit | GET | 302 | 403 | 200 | 403 | 403 | 302 |
| profiles:trainer_edit | POST | 302 | 403 | 200 | 403 | 403 | 302 |
| profiles:qualification_create | GET | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:qualification_create | POST | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:qualification_edit | GET | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:qualification_edit | POST | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:qualification_delete | GET | 302 | 405 | 403 | 403 | 403 | 302 |
| profiles:qualification_delete | POST | 302 | 302 | 403 | 403 | 403 | 302 |
| profiles:experience_create | GET | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:experience_create | POST | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:experience_edit | GET | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:experience_edit | POST | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:experience_delete | GET | 302 | 405 | 403 | 403 | 403 | 302 |
| profiles:experience_delete | POST | 302 | 302 | 403 | 403 | 403 | 302 |
| profiles:certificate_create | GET | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:certificate_create | POST | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:certificate_edit | GET | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:certificate_edit | POST | 302 | 200 | 403 | 403 | 403 | 302 |
| profiles:certificate_delete | GET | 302 | 405 | 403 | 403 | 403 | 302 |
| profiles:certificate_delete | POST | 302 | 302 | 403 | 403 | 403 | 302 |
| profiles:private_file_trainee | GET | 302 | 200 | 404 | 200 | 403 | 302 |
| profiles:private_file_trainee | POST | 302 | 405 | 405 | 405 | 403 | 302 |
| profiles:private_file_trainer | GET | 302 | 200 | 200 | 200 | 403 | 302 |
| profiles:private_file_trainer | POST | 302 | 405 | 405 | 405 | 403 | 302 |
| profiles:private_file_certificate | GET | 302 | 200 | 404 | 200 | 403 | 302 |
| profiles:private_file_certificate | POST | 302 | 405 | 405 | 405 | 403 | 302 |


Full source of LoginForm.clean (unchanged):

```python
def clean(self) -> dict[str, Any]:
    """Verify password first to prevent status leaks for non-existent users."""
    username: str | None = self.cleaned_data.get("username")
    password: str | None = self.cleaned_data.get("password")
    if not username or not password:
        return self.cleaned_data
    user: User | None = User.objects.filter(username__iexact=username).first()
    if user is None or not user.check_password(password):
        raise forms.ValidationError(
            MSG_INVALID_CREDENTIALS,
            code="invalid_login",
        )
    if not user.is_active:
        raise forms.ValidationError(
            MSG_ACCOUNT_DISABLED,
            code="inactive",
        )
    if not user.is_approved:
        raise forms.ValidationError(
            MSG_AWAITING_APPROVAL,
            code="unapproved",
        )
    self.user_cache = user
    return self.cleaned_data
```

Full source of test_login_form_status_leak_prevention (unchanged):

```python
@pytest.mark.django_db
def test_login_form_status_leak_prevention() -> None:
    """Verify wrong passwords for unapproved/inactive users yield identical errors."""
    pwd = "ValidPass123!"
    UserFactory(username="unapp_u", pending_trainee=True, password=pwd)
    UserFactory(username="inact_u", rejected_user=True, password=pwd)

    unknown_err = _get_login_errors("ghost", "x")
    assert _get_login_errors("unapp_u", "x") == unknown_err == [MSG_INVALID_CREDENTIALS]
    assert _get_login_errors("inact_u", "x") == unknown_err == [MSG_INVALID_CREDENTIALS]
    assert _get_login_errors("unapp_u", pwd) == [MSG_AWAITING_APPROVAL]
    assert _get_login_errors("inact_u", pwd) == [MSG_ACCOUNT_DISABLED]
```

Regression evidence: HTTPS next downgrade failed before require_https=request.is_secure(); the production-host regression failed before replacing the inherited environ schema lookup. Valid account POST failed before separating account writes from file handling. Private file URL generation failed its deny-URL test before PrivateStorage. Three matrix cases then reproduced Django's default widget requesting file.url; PrivateFileInput fixes the rendering cause. All now pass in the full suite. See BUGS.md for root causes and test names.

DECISIONS AND ASSUMPTIONS:

ADRs 015-023 record the binding brief, catalog lifecycle/constraints, lazy role profiles and retained history, no Admin profile model, private selector visibility and attachment delivery, upload limits/content checks, fixed qualification year bounds 1900..2100, experience bounds 0..60, commit-time file cleanup, shared form/matrix machinery, and the explicit generated-migration size exception. Generated migration history was preserved. No production deployment or persistent development database migration was performed.

KNOWN ISSUES / RISKS:

- Login and signup throttling is not implemented (ADR 011, planned for B7).
- HSTS is 3600 s; include-subdomains and preload are intentionally off until HTTPS is verified (B7). check --deploy emits security.W005 and security.W021; no warnings were silenced.
- File storage is not transactional: a new upload may remain unreferenced if an outer database transaction later rolls back. Old files remain intact; replacement/deletion cleanup occurs only after successful commit (ADR 021).

DEMO STEPS:

1. Activate venv and run `python manage.py migrate`, then `python manage.py createsuperuser` and `python manage.py runserver` locally. These demo commands are instructions; the persistent database has not been migrated by this task.
2. Open /login/ with that Admin. Use Catalog to create subjects/skills and exercise edit/deactivate/reactivate/delete controls.
3. Sign up trainee and trainer accounts at /signup/; approve them via the Admin pending list. No seeded logins were created; the idempotent demo seed command remains scheduled for B7 under brief section 8.
4. As Trainee, use My trainee profile, add qualifications/experience/certificates, and download private evidence. As Trainer, edit the trainer profile. All roles can edit Account details; the profile directory links to visible profiles.
5. Try another trainee's profile or evidence URL to see 404. An Admin can read trainee profiles; approved users can read trainer profiles.

NEXT: B3 Courses and Library, awaiting the user's reply "approved". B3 has not started; B2 remains on phase/b2-catalog-profiles for review.
