PHASE / TASK: B3 Courses and Library, including Step 0

STATUS: Done

GOAL: Enforce course ownership, unique enrollment, sequential progress and private resource delivery with a constant-query station-map handoff.

WHAT CHANGED: Merged approved B2/B2.1 into main and tagged b2-approved; created phase/b3-courses-library. First commit 5ce0d8a completes Step 0. Courses adds Course, Module, Enrollment, ModuleProgress plus role/owner services, visibility/count selectors and Line/Station dataclasses. Library adds LibraryResource, kind-specific private uploads, filtered pagination and protected downloads. Bare templates/nav and landing links make the new pages reachable. Shared persistence/form feedback and temporary test storage are reused; no dependencies or extra apps were added. BUGs 012-013 were reproduced before fixes.

HOW IT WAS VERIFIED:

Full stdout/stderr and file inventories: ignored [.local/reports/B3_GATE_OUTPUT.txt](../.local/reports/B3_GATE_OUTPUT.txt); Step 0 before/after proof: ignored .local/reports/B3_STEP0.json. Only compact gate output is pasted here.

```text
============================ 948 passed in 10.47s =============================
============================ 948 passed in 10.99s =============================
TOTAL                                  1597      0    222      0   100%
No module is under 100%.
ruff check .: All checks passed!
ruff format --check . (final, report included): 148 files already formatted
makemigrations --check: No changes detected
fresh migrate: all migrations OK, including courses.0001_initial and library.0001_initial.
manage.py check: System check identified no issues (0 silenced).
pip check: No broken requirements found.
check --deploy (prod): System check identified 2 issues (0 silenced): security.W005, security.W021.
```

Step 0 ignore proof, `git check-ignore -v media/ private_uploads/ .local/ media/test-upload.png private_uploads/test-upload.pdf`:

```text
.gitignore:15:media/	media/
.gitignore:47:private_uploads/	private_uploads/
.gitignore:48:.local/	.local/
.gitignore:15:media/	media/test-upload.png
.gitignore:47:private_uploads/	private_uploads/test-upload.pdf
```

Step 0 storage proof: before=[]; after=[]; identical=True; full pytest 533 passed in 6.28s. The final full B3 pytest run also left before=[] and after=[] unchanged. Test uploads use temporary roots outside the real private directory.

Shared cookie proof: dev CSRF_COOKIE_HTTPONLY=True; prod CSRF_COOKIE_HTTPONLY=True (real settings subprocesses, inherited from base.py).

`wc -l` output, files over 150 lines only (all handwritten files <=250):

```text
 193 apps/accounts/tests/test_forms.py
 166 apps/accounts/tests/test_auth_views.py
 163 apps/accounts/views.py
 157 apps/courses/tests/test_course_services.py
 155 apps/profiles/tests/test_crud.py
```

AST top 5 longest functions (all functions <=25; registered views <=15 logic statements):

```text
25 apps/library/tests/test_crud.py:42 test_edit_replace_delete_forms_cleanup_files
24 apps/profiles/tests/test_crud.py:116 test_child_create_edit_delete
24 apps/profiles/tests/test_crud.py:20 test_trainee_profile_post_and_private_photo
24 apps/accounts/permissions.py:36 role_required
24 apps/accounts/forms.py:79 clean
```

New migration inventory (no AlterField):

```text
courses.0001_initial:
  CreateModel Course
  CreateModel Enrollment
  CreateModel Module
  CreateModel ModuleProgress
  constraint course_dates_ordered
  constraint unique_trainee_course
  constraint unique_course_module_order
  constraint module_order_at_least_one
  constraint unique_enrollment_module
library.0001_initial:
  CreateModel LibraryResource
```

Station-map proof: small 1 course x 2 modules x 1 skill = 4 queries; large 8 courses x 7 modules x 3 skills = 4 queries. Both were asserted with django_assert_num_queries:

```text
======================= 2 passed, 2 deselected in 0.82s =======================
```

New-URL permission matrix only: 322 cases (23 URLs x 7 actors x GET/POST). Empty form POSTs return validation pages (200); authorized state-action POSTs redirect (302). Inactive sessions load as anonymous. Object-level denials are 404; method guards run before object lookup.

| URL | Method | Anon | Trainee | Trainer owner | Trainer other | Admin | Unapproved | Inactive |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| courses:list | GET | 302 | 200 | 200 | 200 | 200 | 403 | 302 |
| courses:list | POST | 302 | 405 | 405 | 405 | 405 | 403 | 302 |
| courses:detail | GET | 302 | 200 | 200 | 200 | 200 | 403 | 302 |
| courses:detail | POST | 302 | 405 | 405 | 405 | 405 | 403 | 302 |
| courses:create | GET | 302 | 403 | 200 | 200 | 200 | 403 | 302 |
| courses:create | POST | 302 | 403 | 200 | 200 | 200 | 403 | 302 |
| courses:edit | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| courses:edit | POST | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| courses:publish | GET | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| courses:publish | POST | 302 | 403 | 302 | 404 | 302 | 403 | 302 |
| courses:unpublish | GET | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| courses:unpublish | POST | 302 | 403 | 302 | 404 | 302 | 403 | 302 |
| courses:module_add | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| courses:module_add | POST | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| courses:module_edit | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| courses:module_edit | POST | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| courses:module_delete | GET | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| courses:module_delete | POST | 302 | 403 | 302 | 404 | 302 | 403 | 302 |
| courses:enroll | GET | 302 | 405 | 403 | 403 | 403 | 403 | 302 |
| courses:enroll | POST | 302 | 302 | 403 | 403 | 403 | 403 | 302 |
| courses:drop | GET | 302 | 405 | 403 | 403 | 403 | 403 | 302 |
| courses:drop | POST | 302 | 302 | 403 | 403 | 403 | 403 | 302 |
| courses:complete_module | GET | 302 | 405 | 403 | 403 | 403 | 403 | 302 |
| courses:complete_module | POST | 302 | 302 | 403 | 403 | 403 | 403 | 302 |
| courses:my_courses | GET | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| courses:my_courses | POST | 302 | 405 | 403 | 403 | 403 | 403 | 302 |
| courses:station_map | GET | 302 | 200 | 403 | 403 | 403 | 403 | 302 |
| courses:station_map | POST | 302 | 405 | 403 | 403 | 403 | 403 | 302 |
| courses:participants | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| courses:participants | POST | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| library:list | GET | 302 | 200 | 200 | 200 | 200 | 403 | 302 |
| library:list | POST | 302 | 405 | 405 | 405 | 405 | 403 | 302 |
| library:detail | GET | 302 | 200 | 200 | 200 | 200 | 403 | 302 |
| library:detail | POST | 302 | 405 | 405 | 405 | 405 | 403 | 302 |
| library:create | GET | 302 | 403 | 200 | 200 | 200 | 403 | 302 |
| library:create | POST | 302 | 403 | 200 | 200 | 200 | 403 | 302 |
| library:edit | GET | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| library:edit | POST | 302 | 403 | 200 | 404 | 200 | 403 | 302 |
| library:delete | GET | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| library:delete | POST | 302 | 403 | 302 | 404 | 302 | 403 | 302 |
| library:publish | GET | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| library:publish | POST | 302 | 403 | 302 | 404 | 302 | 403 | 302 |
| library:unpublish | GET | 302 | 403 | 405 | 405 | 405 | 403 | 302 |
| library:unpublish | POST | 302 | 403 | 302 | 404 | 302 | 403 | 302 |
| library:download | GET | 302 | 200 | 200 | 200 | 200 | 403 | 302 |
| library:download | POST | 302 | 405 | 405 | 405 | 405 | 403 | 302 |

DECISIONS AND ASSUMPTIONS: ADRs 029-037 record shared HttpOnly cookies; eligible role/owner checks; protected history/no course delete service; active-subject assignment; unique enrollment race recovery and dropped reactivation; ordered/idempotent module completion; station-map states/interchanges/order/query budget; matching library course/trainer/subject; signature-only office validation and private delivery; shared domain feedback and temporary storage. evaluate_completion(enrollment) is deferred to B4/B5 and is not implemented in B3. Course edits cannot invalidate existing resource associations.

KNOWN ISSUES / RISKS:

- Login and signup throttling is not implemented (ADR 011, planned for B7).
- HSTS is 3600 s; include-subdomains and preload are intentionally off until HTTPS is verified (B7); these are the two deployment warnings.
- Library video downloads do not support Range requests; long videos cannot seek (B7 deployment).
- Storage is not transactional: a new file can remain unreferenced after an outer transaction rollback; old files remain intact (ADR 021).

DEMO STEPS: On this review branch, migrate a fresh local database, create a superuser and runserver. Sign up/approve trainer and trainee accounts. As Admin create an active subject and skills; as Trainer create a course/modules, publish it and upload/publish a library resource. As Trainee enroll, complete modules in order, inspect My courses/Station map, then drop/resume and confirm progress is retained. Trainers/Admin can inspect participants. No seeded logins or persistent DB changes were made by this task.

NEXT: Await B3 approval. B4 has not started; the B3 branch is not merged or tagged.
