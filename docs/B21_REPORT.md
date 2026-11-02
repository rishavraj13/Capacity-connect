PHASE / TASK: B2.1 pre-merge review on phase/b2-catalog-profiles

STATUS: Done

GOAL: Clean the pre-merge migration state and resolve every B2 review item without merging, tagging or starting B3.

WHAT CHANGED:

- Migrations: regenerated profiles as one clean 0001_initial from final models, removing the earlier 0002/0003. All three were first committed together in 1802c41; none had been separately committed before generation or applied on a persistent database. Catalog and accounts migration files were untouched. Updated ADR 023 while retaining the approved generated-migration size exemption.
- Text/docs: repaired corrupted punctuation at source; explicit UTF-8/no-BOM reads and writes are now required in AGENTS. README setup starts from main and includes venv, requirements, .env, migrations, createsuperuser, runserver and pytest. AGENTS directs readers to PROGRESS for status. base.html declares exactly <meta charset="utf-8">.
- Transcript: docs/B2_GATE_OUTPUT.txt was committed in 1802c41. Ran git rm --cached to remove it from the index, then moved the retained local copy to ignored .local/reports/B2_GATE_OUTPUT.txt. New raw evidence is ignored .local/reports/B21_GATE_OUTPUT.txt. The old transcript still exists in Git history; no history rewriting was done.
- Settings/storage/uploads: production CSRF_COOKIE_HTTPONLY=True; no client-side code reads that cookie. PrivateStorage uses dedicated PRIVATE_MEDIA_ROOT; Pillow decompression-bomb warnings and errors become form errors through a local warnings context.
- Profiles: existing retired skills remain visible and are preserved even when omitted from a POST. Only new skills require active subjects, and form help text explains preservation. Shared choices are distinct. Account email database collisions are recovered after a savepoint rollback and become email field errors; unrelated integrity failures are re-raised.
- Tests: added actual hostile-dimension PNG form tests, post-validation database email-race tests, retired-skill tests, private-root/MIME-header tests, 1/10-child query counts, and both previously uncovered accounts view branches. BUGs 006-011 and ADRs 024-028 record the causes and choices.

HOW IT WAS VERIFIED:

All commands used the existing venv. The complete raw stdout/stderr is retained locally at [.local/reports/B21_GATE_OUTPUT.txt](../.local/reports/B21_GATE_OUTPUT.txt), ignored by Git. No persistent database was migrated.

Migration history and inventory below are real output captured before this B2.1 commit. The inventory reads operations from Django's MigrationLoader, rather than reconstructing them from models. Every catalog/profiles operation is CreateModel; there is no AlterField (related or unrelated). Named constraints are unique_lower_subject_name, unique_lower_skill_name and experience_dates_ordered. The unchanged accounts unique_lower_email constraint protects the email race.

`git log --oneline --stat -- apps/profiles/migrations apps/catalog/migrations` - exit 0:

```text
1802c41 feat(profiles): add private role profiles and catalog workflows
 apps/catalog/migrations/0001_initial.py            | 101 +++++++
 apps/catalog/migrations/__init__.py                |   0
 apps/profiles/migrations/0001_initial.py           | 297 +++++++++++++++++++++
 ...0002_alter_externalcertificate_file_and_more.py |  51 ++++
 .../migrations/0003_alter_qualification_year.py    |  24 ++
 apps/profiles/migrations/__init__.py               |   0
 6 files changed, 473 insertions(+)
```

`pytest` - exit 0:

```text
apps/profiles/tests/test_forms.py::test_forms_have_no_privileged_fields[WorkExperienceForm] PASSED [ 99%]
apps/profiles/tests/test_forms.py::test_forms_have_no_privileged_fields[ExternalCertificateForm] PASSED [100%]

============================= 532 passed in 6.47s =============================
```

`coverage run -m pytest` - exit 0:

```text
apps/profiles/tests/test_forms.py::test_forms_have_no_privileged_fields[WorkExperienceForm] PASSED [ 99%]
apps/profiles/tests/test_forms.py::test_forms_have_no_privileged_fields[ExternalCertificateForm] PASSED [100%]

============================= 532 passed in 6.16s =============================
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
apps\accounts\views.py               99      0     24      0   100%
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
apps\core\storage.py                 14      0      0      0   100%
apps\core\uploads.py                 15      0      2      0   100%
apps\core\validators.py              42      0     10      0   100%
apps\core\widgets.py                  6      0      0      0   100%
apps\profiles\__init__.py             0      0      0      0   100%
apps\profiles\admin.py                0      0      0      0   100%
apps\profiles\apps.py                 4      0      0      0   100%
apps\profiles\constants.py           11      0      0      0   100%
apps\profiles\forms.py               43      0      2      0   100%
apps\profiles\models.py              40      0      0      0   100%
apps\profiles\selectors.py           26      0      2      0   100%
apps\profiles\services.py            71      0     18      0   100%
apps\profiles\urls.py                 4      0      0      0   100%
apps\profiles\views\__init__.py       0      0      0      0   100%
apps\profiles\views\children.py      61      0      0      0   100%
apps\profiles\views\files.py         26      0      4      0   100%
apps\profiles\views\profiles.py      38      0      0      0   100%
-----------------------------------------------------------------------------
TOTAL                               898      0    120      0   100%
```

`ruff check .` - exit 0:

```text
All checks passed!
```

`ruff format --check .` - exit 0:

```text
98 files already formatted
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
  Applying sessions.0001_initial... OK
```

`python manage.py check --deploy --settings=config.settings.prod (temporary strong SECRET_KEY and explicit ALLOWED_HOSTS)` - exit 0:

```text
System check identified some issues:

WARNINGS:
?: (security.W005) You have not set the SECURE_HSTS_INCLUDE_SUBDOMAINS setting to True. Without this, your site is potentially vulnerable to attack via an insecure connection to a subdomain. Only set this to True if you are certain that all subdomains of your domain should be served exclusively via SSL.
?: (security.W021) You have not set the SECURE_HSTS_PRELOAD setting to True. Without this, your site cannot be submitted to the browser preload list.

System check identified 2 issues (0 silenced).
```

`python manage.py shell --settings=config.settings.dev -c <private-root containment and cookie assertion>` - exit 0:

```text
13 objects imported automatically (use -v 2 for details).

{"settings": "config.settings.dev", "DEBUG": true, "PRIVATE_MEDIA_ROOT": "C:\\Django\\Project\\private_uploads", "MEDIA_ROOT": "C:\\Django\\Project\\media", "STATIC_ROOT": "C:\\Django\\Project\\staticfiles", "STATICFILES_DIRS": [], "SESSION_COOKIE_HTTPONLY": true, "CSRF_COOKIE_HTTPONLY": false}
```

`python manage.py shell --settings=config.settings.prod -c <private-root containment and cookie assertion>` - exit 0:

```text
13 objects imported automatically (use -v 2 for details).

{"settings": "config.settings.prod", "DEBUG": false, "PRIVATE_MEDIA_ROOT": "C:\\Django\\Project\\private_uploads", "MEDIA_ROOT": "C:\\Django\\Project\\media", "STATIC_ROOT": "C:\\Django\\Project\\staticfiles", "STATICFILES_DIRS": [], "SESSION_COOKIE_HTTPONLY": true, "CSRF_COOKIE_HTTPONLY": true}
```

`Requested encoding rg scan (Unicode pattern shown escaped in the ignored transcript)` - exit 1:

```text
No matches. Actual stdout/stderr were empty; exit 1 is ripgrep's no-match status.
```

`rg -n "static\(|MEDIA_ROOT|PRIVATE_MEDIA_ROOT|document_root|serve" -g urls.py apps config` - exit 1:

```text
No matches (empty stdout/stderr).
```

`rg -n "document\.cookie|Cookies\.get" apps templates config` - exit 1:

```text
No matches (empty stdout/stderr).
```

`pytest --collect-only -q <all upload-related test modules>` - exit 0:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.2.0, pluggy-1.7.0
django: version: 5.2.18, settings: config.settings.test (from ini)
rootdir: C:\Django\Project
configfile: pytest.ini
plugins: Faker-40.44.0, django-4.14.0
collected 35 items

<Dir Project>
  <Package apps>
    <Package profiles>
      <Package tests>
        <Module test_upload_forms.py>
          <Function test_decompression_bomb_is_a_form_error[bomb-warning]>
          <Function test_decompression_bomb_is_a_form_error[bomb-error]>
        <Module test_files.py>
          <Function test_unknown_kind_and_empty_photo_return_404>
          <Function test_missing_storage_object_returns_404>
          <Function test_certificate_download_headers_and_bytes>
          <Function test_private_storage_has_no_public_url>
          <Function test_public_media_route_does_not_exist>
          <Function test_existing_photo_can_be_cleared_without_public_url>
          <Function test_download_ignores_untrusted_content_type[trainee]>
          <Function test_download_ignores_untrusted_content_type[certificate]>
          <Function test_private_storage_is_separate_from_public_roots>
        <Module test_services.py>
          <Function test_lazy_profiles_are_idempotent_and_preserve_role_history>
          <Function test_trainee_skills_and_mass_assignment>
          <Function test_photo_replacement_and_clear_cleanup>
          <Function test_trainer_update_and_photo_cleanup>
          <Function test_child_save_delete_and_certificate_cleanup>
          <Function test_account_update_normalizes_and_preserves_privileges>
          <Function test_rollback_preserves_old_file>
        <Module test_crud.py>
          <Function test_trainee_profile_post_and_private_photo>
          <Function test_trainer_profile_post>
          <Function test_account_post_preserves_privileges[TRAINEE]>
          <Function test_account_post_preserves_privileges[TRAINER]>
          <Function test_account_post_preserves_privileges[ADMIN]>
          <Function test_child_create_edit_delete[qualification]>
          <Function test_child_create_edit_delete[experience]>
          <Function test_child_create_edit_delete[certificate]>
          <Function test_invalid_upload_never_persists>
    <Package core>
      <Package tests>
        <Module test_uploads.py>
          <Function test_bad_uploads_are_rejected[bad.exe-%PDF-]>
          <Function test_bad_uploads_are_rejected[bad.pdf-plain text]>
          <Function test_bad_uploads_are_rejected[bad.png-plain text]>
          <Function test_bad_uploads_are_rejected[empty.pdf-]>
          <Function test_limits_and_content_are_composable>
          <Function test_actual_images_and_pdf_signatures_are_accepted>
          <Function test_upload_paths_discard_traversal_and_use_uuid>
          <Function test_real_jpeg_and_uppercase_extension_are_accepted>

========================= 35 tests collected in 0.06s =========================
```

`pytest apps/profiles/tests/test_selectors.py -k test_profile_page_query_count` - exit 0:

```text
apps/profiles/tests/test_selectors.py::test_profile_page_query_count[one-child-each] PASSED [ 50%]
apps/profiles/tests/test_selectors.py::test_profile_page_query_count[ten-children-each] PASSED [100%]

======================= 2 passed, 3 deselected in 0.30s =======================
```

`wc -l <every .py in apps/ and config/ plus manage.py, excluding migrations>` - exit 0:

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
   134 apps/accounts/tests/test_admin_views.py
   166 apps/accounts/tests/test_auth_views.py
   193 apps/accounts/tests/test_forms.py
    89 apps/accounts/tests/test_models.py
   133 apps/accounts/tests/test_permissions.py
    63 apps/accounts/tests/test_selectors.py
   130 apps/accounts/tests/test_services.py
    48 apps/accounts/tests/test_settings.py
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
    26 apps/core/storage.py
     1 apps/core/tests/__init__.py
    47 apps/core/tests/matrix.py
    24 apps/core/tests/test_core.py
    39 apps/core/tests/test_csrf.py
    25 apps/core/tests/test_form_views.py
    77 apps/core/tests/test_uploads.py
    25 apps/core/uploads.py
    72 apps/core/validators.py
    15 apps/core/widgets.py
     0 apps/profiles/__init__.py
     1 apps/profiles/admin.py
    10 apps/profiles/apps.py
    13 apps/profiles/constants.py
   102 apps/profiles/forms.py
   119 apps/profiles/models.py
    62 apps/profiles/selectors.py
   130 apps/profiles/services.py
     0 apps/profiles/tests/__init__.py
    10 apps/profiles/tests/conftest.py
    95 apps/profiles/tests/factories.py
    60 apps/profiles/tests/test_account_race.py
   155 apps/profiles/tests/test_crud.py
   119 apps/profiles/tests/test_files.py
    79 apps/profiles/tests/test_forms.py
    55 apps/profiles/tests/test_idor.py
    46 apps/profiles/tests/test_models.py
   125 apps/profiles/tests/test_permissions.py
    74 apps/profiles/tests/test_selectors.py
   146 apps/profiles/tests/test_services.py
    44 apps/profiles/tests/test_skill_retirement.py
    38 apps/profiles/tests/test_upload_forms.py
    45 apps/profiles/urls.py
     1 apps/profiles/views/__init__.py
   116 apps/profiles/views/children.py
    48 apps/profiles/views/files.py
    85 apps/profiles/views/profiles.py
     1 config/__init__.py
     9 config/asgi.py
     1 config/settings/__init__.py
   117 config/settings/base.py
     9 config/settings/dev.py
    23 config/settings/prod.py
    19 config/settings/test.py
    11 config/urls.py
     9 config/wsgi.py
    22 manage.py
  4713 total
```

`AST top 10 longest functions (end_lineno - lineno + 1)` - exit 0:

```text
24 apps/profiles/tests/test_crud.py:20 test_trainee_profile_post_and_private_photo
24 apps/profiles/tests/test_crud.py:116 test_child_create_edit_delete
24 apps/accounts/permissions.py:36 role_required
24 apps/accounts/forms.py:79 clean
23 apps/profiles/tests/test_permissions.py:94 matrix_target
23 apps/profiles/tests/test_permissions.py:53 expected_status
23 apps/accounts/tests/test_settings.py:17 test_production_requires_allowed_hosts
21 apps/profiles/views/files.py:28 private_file
21 apps/profiles/tests/test_services.py:90 test_child_save_delete_and_certificate_cleanup
21 apps/profiles/tests/test_services.py:113 test_account_update_normalizes_and_preserves_privileges
```

`MigrationLoader inventory of every catalog/profiles operation and named constraint` - exit 0:

```text
catalog.0001_initial:
  CreateModel Subject
    constraint unique_lower_subject_name
  CreateModel Skill
    constraint unique_lower_skill_name
profiles.0001_initial:
  CreateModel TraineeProfile
  CreateModel Qualification
  CreateModel ExternalCertificate
  CreateModel TrainerProfile
  CreateModel WorkExperience
    constraint experience_dates_ordered
```

`Byte audit of all tracked and nonignored new repository files` - exit 0:

```text
128 repository text files: valid UTF-8, no BOM.
```

`git diff --check` - exit 0:

```text

```

Encoding details: the initial requested scan found corrupted dash sequences in the earlier B2 report. A broader source review also found a corrupted comparison symbol in PROGRESS. Both sources were repaired. The final requested scan produced no output (exit 1). The pattern was passed as the actual Unicode characters, not as literal backslash-u sequences. The report labels it descriptively so its own command example cannot become a false-positive match. All tracked/new repository files were decoded strictly as UTF-8 and checked for the EF BB BF BOM; ignored secrets, venv and local evidence are outside that source audit. Files are written with Path.read_text(encoding="utf-8") and Path.write_text(..., encoding="utf-8"), never implicit Windows decoding or PowerShell text defaults. After adding this report, the final byte audit checked 129 repository text files: zero BOMs and zero UTF-8 decoding errors. The final ruff check returned All checks passed!, the final format check returned 99 files already formatted, and git diff --check produced no output.

The exact PowerShell form of the final no-corruption scan (constructing the same requested Unicode pattern without embedding corrupt-looking characters in this report):

```powershell
$encodingPattern = ([char]0x00e2).ToString() + [char]0x20ac + '|' + [char]0x00c3
rg -n $encodingPattern docs README.md AGENTS.md templates apps config
```

The wc command uses Git's bundled executable in PowerShell:

```powershell
$projectPythonFiles = rg --files -g '*.py' -g '!venv/**' -g '!.venv/**' -g '!**/migrations/**'
& 'C:\Program Files\Git\usr\bin\wc.exe' -l $projectPythonFiles
```

Query-count proof: test_profile_page_query_count[one-child-each] and [ten-children-each] each assert 8 queries around the full rendered HTTP response, with 1 and 10 Qualifications, WorkExperiences and ExternalCertificates respectively. Both also have 3 skills. Both passed in the explicit targeted command and the full suite.

The former accounts.views branches were: 52->65, invalid LoginForm on POST falling through to the rendered error page; and 157->163, invalid RoleChangeForm bypassing the service and redirecting without changing the target role. New tests test_invalid_login_post_renders_errors_without_authentication and test_invalid_role_post_keeps_existing_role cover them. All accounts.views branches now have coverage.

The email race test inserts a real competing email variant after the service full_clean has passed. Before the fix it raised a database unique_lower_email IntegrityError and returned 500. _persist_account now rolls back its inner savepoint before re-querying email ownership; a confirmed collision raises ValidationError({"email": ...}). The existing form coordinator attaches that error to the form and returns 200. The test proves the original email is unchanged and the database connection is usable. Its same-transaction simulated competitor rolls back with the outer service transaction; an unrelated IntegrityError is explicitly tested to remain visible.

The hostile PNG tests build a tiny valid-CRC PNG header declaring Image.MAX_IMAGE_PIXELS+1 and twice that limit plus one, without allocating a huge image. The lower threshold failed first with HTTP 302 (accepted); both thresholds now return HTTP 200 with photo form errors, no saved file and no 500. The requested upload cases exist in the collected test names above: text renamed .pdf/.png, oversize, empty, traversal names and UUID renaming. Additional HTTP upload and private-delivery tests are included in the same collection.

Private-root proof: both dev and prod resolve PRIVATE_MEDIA_ROOT to C:\Django\Project\private_uploads, a sibling of public media and staticfiles, with no STATICFILES_DIRS. The assertion verifies it is below neither public root. No urls.py contains static(), serve, document_root, MEDIA_ROOT or PRIVATE_MEDIA_ROOT. Tests request both /media/<stored-key> and /private_uploads/<stored-key> and get 404. File delivery is through the role/visibility-filtered profiles route. This verifies repository settings/URLs; no external production web-server configuration is present or deployed by this task. Deployment must keep the private directory out of public aliases.

Content-Type comes from CONTENT_TYPES[validated stored suffix], never the uploaded content_type header. The new tests provide valid PNG/PDF bytes labelled text/html and receive image/png/application/pdf with Content-Disposition: attachment. The server-rendered forms use csrf_token, and the JavaScript-cookie-read scan has no matches; production therefore requires no cookie reader exception.

Full requested source follows, copied from the final repository files.

`apps/core/validators.py`:

```python
"""Validate actual upload bytes before private files enter storage."""

import warnings
from pathlib import PurePath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from PIL import Image, UnidentifiedImageError

IMAGE_FORMATS = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG"}
PDF_SIGNATURE = b"%PDF-"


def validate_extension(file: UploadedFile, allowed: tuple[str, ...]) -> str:
    """Refuse filenames that cannot represent an allowed document type."""
    extension = PurePath(file.name).suffix.lower().lstrip(".")
    if extension not in allowed:
        raise ValidationError("Unsupported file extension.")
    return extension


def validate_size(file: UploadedFile, limit: int) -> None:
    """Bound parser work and reject empty uploads before inspecting content."""
    if not file.size or file.size > limit:
        raise ValidationError("File is empty or exceeds the upload size limit.")


def _validate_image(file: UploadedFile, extension: str) -> None:
    """Treat Pillow's warning threshold as a rejection without global filters."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(file) as image:
            if image.format != IMAGE_FORMATS[extension]:
                raise ValidationError("Image content does not match its extension.")
            image.verify()


def validate_content(file: UploadedFile, extension: str) -> None:
    """Check the file format independently of browser supplied MIME headers."""
    position = file.tell()
    try:
        file.seek(0)
        if extension == "pdf":
            if file.read(len(PDF_SIGNATURE)) != PDF_SIGNATURE:
                raise ValidationError("Invalid PDF content.")
        else:
            _validate_image(file, extension)
    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ValidationError("Invalid image content.") from exc
    finally:
        file.seek(position)


def validate_photo(file: UploadedFile) -> None:
    """Apply the shared photo contract at model and form boundaries."""
    extension = validate_extension(file, settings.PHOTO_EXTENSIONS)
    validate_size(file, settings.PHOTO_MAX_BYTES)
    validate_content(file, extension)


def validate_certificate(file: UploadedFile) -> None:
    """Allow documents and images only after size and content verification."""
    extension = validate_extension(file, settings.CERTIFICATE_EXTENSIONS)
    validate_size(file, settings.CERTIFICATE_MAX_BYTES)
    validate_content(file, extension)
```

`apps/core/uploads.py`:

```python
"""Generate migration-safe opaque storage names for private uploads."""

from pathlib import PurePath
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db.models import Model
from django.utils.deconstruct import deconstructible


@deconstructible
class UploadPath:
    """Keep user-controlled paths out of storage keys."""

    def __init__(self, folder: str, extensions: tuple[str, ...]) -> None:
        """Persist upload naming configuration in migrations."""
        self.folder = folder
        self.extensions = extensions

    def __call__(self, instance: Model, filename: str) -> str:
        """Retain only a validated extension under a fixed model folder."""
        extension = PurePath(filename.replace("\\", "/")).suffix.lower().lstrip(".")
        if extension not in self.extensions:
            raise ValidationError("Unsupported file extension.")
        return f"{self.folder}/{uuid4().hex}.{extension}"
```

`apps/core/storage.py`:

```python
"""Prevent private files from acquiring public media URLs."""

from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateStorage(FileSystemStorage):
    """Require callers to use the permission-checked download route."""

    @property
    def base_location(self) -> str:
        """Use private storage configuration instead of the public media root."""
        return str(self._value_or_setting(self._location, settings.PRIVATE_MEDIA_ROOT))

    @property
    def location(self) -> str:
        """Honor runtime settings overrides without cached public-root locations."""
        return str(Path(self.base_location).resolve())

    def url(self, name: str) -> str:
        """Fail loudly if a template tries to bypass file authorization."""
        raise ValueError("Private files have no public URL.")
```

`apps/profiles/views/files.py`:

```python
"""Serve private storage only after object visibility has been checked."""

from pathlib import PurePath

from django.http import FileResponse, Http404, HttpRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_safe

from apps.accounts.constants import UserRole
from apps.accounts.permissions import role_required
from apps.profiles import selectors

FILE_SELECTORS = {
    "trainee": (selectors.visible_trainees, "photo"),
    "trainer": (selectors.visible_trainers, "photo"),
    "certificate": (selectors.visible_certificates, "file"),
}
CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
}


@role_required(*UserRole.values)
@require_safe
def private_file(request: HttpRequest, kind: str, pk: int) -> FileResponse:
    """Apply profile visibility before opening an opaque storage key."""
    if kind not in FILE_SELECTORS:
        raise Http404
    selector, field = FILE_SELECTORS[kind]
    record = get_object_or_404(selector(request.user), pk=pk)
    file = getattr(record, field)
    if not file:
        raise Http404
    try:
        stream = file.open("rb")
    except FileNotFoundError as exc:
        raise Http404 from exc
    response = FileResponse(
        stream,
        as_attachment=True,
        filename=PurePath(file.name).name,
        content_type=CONTENT_TYPES[PurePath(file.name).suffix.lower()],
    )
    response["Cache-Control"] = "private, no-store"
    return response
```

DECISIONS AND ASSUMPTIONS:

ADRs 023-028 record the authorized pre-merge initial migration regeneration, retained generated-file size exemption, explicit UTF-8/no-BOM policy, ignored local transcripts, production HttpOnly CSRF cookie, retired-skill preservation, private-root and image-warning boundaries, and email-race savepoint recovery. No dependency or domain model/field was added. The existing original B2 report remains a marked historical submission with repaired encoding and a corrected local-transcript link.

KNOWN ISSUES / RISKS:

- Login and signup throttling is not implemented (ADR 011, planned for B7).
- HSTS is 3600 s; include-subdomains and preload are intentionally off until HTTPS is verified (B7). check --deploy emits exactly security.W005 and security.W021; no warnings were silenced.
- File storage is not transactional: a newly written file can remain unreferenced if an outer database transaction rolls back. Old files remain intact; commit-time cleanup is retained (ADR 021).

DEMO STEPS:

1. On the review branch, use a fresh local database, migrate, create a superuser and runserver. This task used only disposable databases; it did not migrate the persistent developer database or create seeded accounts.
2. Approve a trainee and select skills. As Admin, deactivate a selected skill's subject. As Trainee, confirm the skill remains shown; save only bio/interests and confirm the retired selection remains. A different inactive skill cannot be newly added.
3. Upload a normal PNG/PDF and download it through the profile link. Spoofed content and huge-dimension PNGs show form errors. Direct /media/ and /private_uploads/ requests return 404.
4. Run the targeted email-race and query-count tests to reproduce database-race recovery and equal query costs; no manual concurrent-browser race was claimed.

NEXT: Await the user's B2.1 approval and B3 instructions. B2 is not merged; no tag was created; B3 has not started.
