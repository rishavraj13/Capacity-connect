# Backend URL map and frontend data contracts

Generated from the actual URLconf. Role permission does not grant ownership: selectors still scope records. State changes require POST; GET forms do not write. Assessment take GET retains approved lazy expiry (ADR 043). No frontend work.

## Public

`admin:login`, `announcements:home`, `certificates:verify`, `certificates:verify_form`, `login`, `signup`

## TRAINEE

`assessments:detail`, `assessments:history`, `assessments:mine`, `assessments:result`, `assessments:start`, `assessments:take`, `catalog:subject_list`, `certificates:download`, `certificates:mine`, `courses:complete_module`, `courses:detail`, `courses:drop`, `courses:enroll`, `courses:list`, `courses:my_courses`, `courses:station_map`, `feedback:course_submit`, `feedback:delete`, `feedback:mine`, `feedback:resource_submit`, `library:detail`, `library:download`, `library:list`, `logout`, `profiles:account_edit`, `profiles:certificate_create`, `profiles:certificate_delete`, `profiles:certificate_edit`, `profiles:experience_create`, `profiles:experience_delete`, `profiles:experience_edit`, `profiles:private_file`, `profiles:profile_list`, `profiles:qualification_create`, `profiles:qualification_delete`, `profiles:qualification_edit`, `profiles:trainee_detail`, `profiles:trainee_edit`, `profiles:trainer_detail`, `trainee_home`

## TRAINER

`assessments:course_list`, `assessments:create`, `assessments:delete`, `assessments:edit`, `assessments:manage_detail`, `assessments:participation`, `assessments:question_add`, `assessments:question_delete`, `assessments:question_edit`, `assessments:result`, `catalog:subject_list`, `certificates:download`, `competency:add`, `competency:edit`, `competency:mine`, `competency:remove`, `courses:create`, `courses:detail`, `courses:edit`, `courses:list`, `courses:module_add`, `courses:module_delete`, `courses:module_edit`, `courses:participants`, `courses:publish`, `courses:unpublish`, `dashboards:trainer`, `feedback:course_summary`, `feedback:resource_summary`, `library:create`, `library:delete`, `library:detail`, `library:download`, `library:edit`, `library:list`, `library:publish`, `library:unpublish`, `logout`, `profiles:account_edit`, `profiles:private_file`, `profiles:profile_list`, `profiles:trainee_detail`, `profiles:trainer_detail`, `profiles:trainer_edit`, `trainer_home`

## ADMIN

`admin_approve_user`, `admin_change_role`, `admin_panel`, `admin_pending_list`, `admin_reject_user`, `admin_user_list`, `announcements:create`, `announcements:delete`, `announcements:edit`, `announcements:manage`, `announcements:publish`, `announcements:unpublish`, `assessments:course_list`, `assessments:create`, `assessments:delete`, `assessments:edit`, `assessments:manage_detail`, `assessments:participation`, `assessments:question_add`, `assessments:question_delete`, `assessments:question_edit`, `assessments:result`, `catalog:skill_create`, `catalog:skill_delete`, `catalog:skill_edit`, `catalog:subject_create`, `catalog:subject_deactivate`, `catalog:subject_edit`, `catalog:subject_list`, `catalog:subject_reactivate`, `certificates:download`, `competency:ranking`, `courses:create`, `courses:detail`, `courses:edit`, `courses:list`, `courses:module_add`, `courses:module_delete`, `courses:module_edit`, `courses:participants`, `courses:publish`, `courses:unpublish`, `dashboards:admin`, `feedback:course_summary`, `feedback:resource_summary`, `library:create`, `library:delete`, `library:detail`, `library:download`, `library:edit`, `library:list`, `library:publish`, `library:unpublish`, `logout`, `profiles:account_edit`, `profiles:private_file`, `profiles:profile_list`, `profiles:trainee_detail`, `profiles:trainer_detail`

## Built-in Django admin

Approved active ADMIN + is_staff required; login is the public exception. ADMIN_URL defaults to django-admin/. Named routes:

`admin:accounts_user_add`, `admin:accounts_user_change`, `admin:accounts_user_changelist`, `admin:accounts_user_delete`, `admin:accounts_user_history`, `admin:app_list`, `admin:auth_group_add`, `admin:auth_group_change`, `admin:auth_group_changelist`, `admin:auth_group_delete`, `admin:auth_group_history`, `admin:auth_user_password_change`, `admin:autocomplete`, `admin:index`, `admin:jsi18n`, `admin:logout`, `admin:password_change`, `admin:password_change_done`, `admin:view_on_site`

Unnamed redirects and catch-all routes are audited too.

## Plain dataclass contracts

- courses.selectors.station_map_for(trainee) -> tuple[Line, ...], each with stations tuple[Station, ...].
- announcements.selectors.board() -> category-keyed dict of tuples of BoardItem.
- assessments.selectors.next_deadlines_for(trainee, limit, subject_id=None) -> tuple[Departure, ...].
- dashboards.selectors.admin_dashboard() -> AdminDashboard; trainer_dashboard(trainer) -> TrainerDashboard.
- competency.selectors.rank_trainers_for(subject) -> tuple[RankedTrainer, ...].

Percent values are Decimal 0..100, not ratios, rounded half up to two places. Ranking score is 0..1 displayed to four places. Times are aware. PaperOption/PaperQuestion exclude correctness.

### Station (`apps/courses/dataclasses.py`)

`module_id: int`, `title: str`, `order: int`, `course_id: int`, `course_title: str`, `state: StationState`, `is_interchange: bool`

### Line (`apps/courses/dataclasses.py`)

`subject_id: int`, `subject_name: str`, `stations: tuple[Station, ...]`

### BoardItem (`apps/announcements/dataclasses.py`)

`id: int`, `title: str`, `body: str`, `category: Category`, `published_at: datetime`

### Departure (`apps/assessments/dataclasses.py`)

`questionnaire_id: int`, `title: str`, `course_title: str`, `subject_name: str`, `opens_at: datetime`, `deadline: datetime`, `status: DepartureStatus`, `attempts_left: int`

### ParticipationRow (`apps/assessments/dataclasses.py`)

`trainee_id: int`, `trainee_name: str`, `attempts_used: int`, `best_percent: Decimal`, `passed: bool`, `last_attempt_at: datetime | None`

### QuestionnaireStats (`apps/assessments/dataclasses.py`)

`enrolled: int`, `attempted: int`, `passed: int`, `average_best_percent: Decimal`, `pass_rate_percent: Decimal`

### PaperOption (`apps/assessments/dataclasses.py`)

`option_id: int`, `text: str`

### PaperQuestion (`apps/assessments/dataclasses.py`)

`question_id: int`, `text: str`, `order: int`, `marks: int`, `options: tuple[PaperOption, ...]`

### ResultQuestion (`apps/assessments/dataclasses.py`)

`question_id: int`, `text: str`, `marks: int`, `selected_text: str | None`, `is_correct: bool`, `correct_option: str | None`

### AttemptResult (`apps/assessments/dataclasses.py`)

`attempt_id: int`, `title: str`, `score: int`, `percent: Decimal`, `passed: bool`, `status: str`, `questions: tuple[ResultQuestion, ...]`

### QuestionInput (`apps/assessments/dataclasses.py`)

`text: str`, `options: tuple[str, ...]`, `correct_index: int`, `marks: int`

### LineLoad (`apps/dashboards/dataclasses.py`)

`subject_id: int`, `subject_name: str`, `enrollments: int`, `active_enrollments: int`

### AssessmentStats (`apps/dashboards/dataclasses.py`)

`questionnaires_total: int`, `submitted_attempts: int`, `average_best_percent: Decimal`, `pass_rate_percent: Decimal`

### ParticipationStats (`apps/dashboards/dataclasses.py`)

`enrolled_trainees: int`, `attempted_trainees: int`, `participation_rate_percent: Decimal`

### AdminDashboard (`apps/dashboards/dataclasses.py`)

`users_by_role: dict[str, int]`, `pending_approvals: int`, `courses_total: int`, `courses_published: int`, `enrollments_total: int`, `enrollments_by_status: dict[str, int]`, `line_load: tuple[LineLoad, ...]`, `certificates_total: int`, `certificates_by_grade: dict[str, int]`, `assessments: AssessmentStats`, `participation: ParticipationStats`

### CourseStats (`apps/dashboards/dataclasses.py`)

`course_id: int`, `title: str`, `is_published: bool`, `enrolled: int`, `active: int`, `completed: int`, `certificates: int`, `avg_rating: Decimal | None`, `rating_count: int`, `questionnaires: int`

### TrainerTotals (`apps/dashboards/dataclasses.py`)

`courses_total: int`, `courses_published: int`, `enrolled: int`, `active: int`, `completed: int`, `certificates: int`, `avg_rating: Decimal | None`, `rating_count: int`, `questionnaires: int`

### QuestionnaireLink (`apps/dashboards/dataclasses.py`)

`questionnaire_id: int`, `title: str`, `course_title: str`

### TrainerDashboard (`apps/dashboards/dataclasses.py`)

`courses: tuple[CourseStats, ...]`, `totals: TrainerTotals`, `questionnaires: tuple[QuestionnaireLink, ...]`

### RankedTrainer (`apps/competency/dataclasses.py`)

`trainer_id: int`, `name: str`, `proficiency: int`, `years_experience: int`, `avg_rating: Decimal | None`, `rating_count: int`, `courses_delivered: int`, `score: Decimal`, `rank: int`
