# Frontend handoff

| Phase | Delivered |
|---|---|
| F0 and F0.1 | Local assets, strict CSP, three themes, app shell and contrast baseline |
| F1 | Public home, departure board, login, signup and certificate verification |
| F2a | Trainee learning pages and serpentine station map |
| F2b | Trainee assessments, feedback, certificates and profiles |
| F3a | Trainer course, module, library and competency management |
| F3b | Trainer authoring, participation, analytics and feedback summaries |
| F4 | Admin Control room, accounts, catalog, announcements and ranking |
| F5 | Seeded portal template audit, reduced-motion source guard and record print styles |

## Components

| Component | Purpose | Direct consumers |
|---|---|---|
| `admin_account_status.html` | Account state badge | `templates/accounts/admin_pending_list.html`, `templates/accounts/admin_user_list.html` |
| `admin_approval_actions.html` | Approval and rejection forms | `templates/accounts/admin_pending_list.html`, `templates/accounts/admin_user_list.html` |
| `assets.html` | Local assets and preload links | `templates/base.html`, `templates/components/error_shell.html` |
| `board.html` | Departure board wrapper | `templates/styleguide.html`, `templates/announcements/home.html` |
| `board_category.html` | Visible departure category label | `templates/announcements/manage.html`, `templates/components/board_row.html` |
| `board_row.html` | Departure row and Admin preview | `templates/announcements/manage.html`, `templates/components/board.html` |
| `confirm_delete.html` | Native confirmation and POST form | `templates/announcements/manage.html`, `templates/assessments/manage_detail.html`, `templates/catalog/list.html`, `templates/competency/mine.html`, `templates/courses/module_table.html`, `templates/feedback/mine.html`, `templates/library/detail.html`, `templates/profiles/trainee.html` |
| `course_metadata.html` | Course subject, trainer and dates | `templates/courses/detail.html`, `templates/courses/list.html` |
| `date_field.html` | Date input format hint | No direct include |
| `empty_state.html` | Shared empty state | `templates/styleguide.html` |
| `error_shell.html` | Standalone error page shell | `templates/403.html`, `templates/404.html`, `templates/429.html`, `templates/500.html`, `templates/certificates/not_found.html` |
| `error_summary.html` | Linked validation errors | `templates/accounts/login.html`, `templates/accounts/signup.html`, `templates/assessments/take.html`, `templates/certificates/verify_form.html`, `templates/components/feedback_fields.html`, `templates/components/form_fields.html` |
| `feedback_fields.html` | Rating radios and comment | `templates/shared/form.html` |
| `form_field.html` | Bound field group | `templates/accounts/login.html`, `templates/accounts/signup.html`, `templates/components/feedback_fields.html`, `templates/components/form_fields.html` |
| `form_fields.html` | Shared form fields and errors | `templates/styleguide.html`, `templates/competency/ranking.html`, `templates/shared/form.html` |
| `header.html` | Portal header and account menu | `templates/base.html` |
| `library_pagination.html` | Library filter-aware pagination | `templates/library/list.html` |
| `library_upload.html` | Per-kind private upload help | No direct include |
| `messages.html` | Domain and success alerts | `templates/base.html` |
| `metro_illustration.html` | Decorative public hero map | `templates/announcements/home.html` |
| `nav.html` | Role-aware navigation | `templates/components/header.html` |
| `page_header.html` | Reusable heading and lead | `templates/styleguide.html` |
| `pagination.html` | Reusable paging controls | `templates/styleguide.html` |
| `profile_upload.html` | Private profile upload help | No direct include |
| `public_styles.html` | Public stylesheet include | `templates/accounts/login.html`, `templates/accounts/signup.html`, `templates/announcements/home.html`, `templates/certificates/verify.html`, `templates/certificates/verify_form.html` |
| `publication_badge.html` | Publication state text | `templates/announcements/manage.html`, `templates/courses/detail.html`, `templates/courses/list.html`, `templates/dashboards/trainer.html`, `templates/library/detail.html`, `templates/library/list.html` |
| `role_options.html` | Signup radio cards | `templates/accounts/signup.html` |
| `sample_station_map.html` | Styleguide station example | `templates/styleguide.html` |
| `sample_ticket.html` | Styleguide ticket example | `templates/styleguide.html` |
| `staff_stats_styles.html` | Staff chart stylesheet include | `templates/assessments/participation.html`, `templates/dashboards/admin.html`, `templates/dashboards/trainer.html`, `templates/feedback/summary.html` |
| `stat_tile.html` | Labelled numeric display | `templates/styleguide.html`, `templates/assessments/participation.html`, `templates/dashboards/admin.html`, `templates/dashboards/trainer.html`, `templates/feedback/summary.html` |
| `station_map.html` | Interactive SVG and text list | `templates/courses/station_map.html` |
| `text_input.html` | Labelled bound text input | `templates/accounts/login.html`, `templates/certificates/verify_form.html` |
| `theme_control.html` | Theme selector | `templates/components/header.html` |
| `trainee_styles.html` | Shared form and trainee stylesheet include | `templates/assessments/mine.html`, `templates/assessments/take.html`, `templates/certificates/mine.html`, `templates/shared/form.html` |

## Static assets

| Asset | Bytes |
|---|---:|
| `static/css/base.css` | 1,915 |
| `static/css/components.css` | 6,523 |
| `static/css/pages/learning.css` | 1,204 |
| `static/css/pages/public.css` | 2,705 |
| `static/css/pages/staff-stats.css` | 1,012 |
| `static/css/pages/styleguide.css` | 237 |
| `static/css/pages/trainee.css` | 413 |
| `static/css/print.css` | 541 |
| `static/css/tokens.css` | 3,178 |
| `static/fonts/bricolage-grotesque-latin-600-normal.woff2` | 22,456 |
| `static/fonts/bricolage-grotesque-latin-800-normal.woff2` | 21,844 |
| `static/fonts/bricolage-grotesque-OFL.txt` | 4,401 |
| `static/fonts/inter-latin-400-normal.woff2` | 23,664 |
| `static/fonts/inter-latin-600-normal.woff2` | 24,452 |
| `static/fonts/inter-OFL.txt` | 4,477 |
| `static/fonts/SOURCES.md` | 2,142 |
| `static/fonts/space-mono-latin-400-normal.woff2` | 16,520 |
| `static/fonts/space-mono-latin-700-normal.woff2` | 16,724 |
| `static/fonts/space-mono-OFL.txt` | 4,726 |
| `static/js/app.js` | 165 |
| `static/js/theme.js` | 1,322 |

## Theme colours

| Colour token | Day | Night | Signage |
|---|---|---|---|
| `--accent` | `#254e9d` | `#b1ccff` | `#162d67` |
| `--alert` | `#9c3029` | `#ffafa0` | `#7b2019` |
| `--badge-fill` | `var(--card)` | `var(--card)` | `var(--card)` |
| `--badge-text` | `var(--ink)` | `var(--ink)` | `var(--ink)` |
| `--board` | `#0b0d10` | `#0b0d10` | `#0b0d10` |
| `--board-label` | `var(--board-text)` | `var(--board-text)` | `var(--board-text)` |
| `--board-text` | `#ffd24a` | `#ffd24a` | `#ffd24a` |
| `--card` | `#fffdf7` | `#18234a` | `#ffffff` |
| `--focus` | `var(--ink)` | `var(--ink)` | `var(--ink)` |
| `--gold` | `#b8892b` | `#b8892b` | `#b8892b` |
| `--gold-text` | `#77550d` | `#ffda8a` | `#77550d` |
| `--ink` | `#14213d` | `#eef1ff` | `#111111` |
| `--line-1` | `#cd563d` | `#e76f51` | `#bd4c34` |
| `--line-2` | `#2a6fdb` | `#2a6fdb` | `#2a6fdb` |
| `--line-3` | `#16815d` | `#1fa97a` | `#127b55` |
| `--muted` | `#6b6a65` | `#9aa6d6` | `#444444` |
| `--paper` | `#f2efe6` | `#0f1730` | `#ffd93d` |
| `--primary-fill` | `var(--ink)` | `var(--ink)` | `var(--ink)` |
| `--primary-text` | `var(--card)` | `var(--card)` | `var(--card)` |
| `--secondary-fill` | `var(--card)` | `var(--card)` | `var(--card)` |
| `--secondary-text` | `var(--ink)` | `var(--ink)` | `var(--ink)` |
| `--success` | `#17614a` | `#8af0bd` | `#134d38` |

## Contrast ratios

| Pair | Minimum | Day | Night | Signage |
|---|---:|---:|---:|---:|
| ink / paper | 4.5 | 13.89 | 15.74 | 13.71 |
| ink / card | 4.5 | 15.70 | 13.54 | 18.88 |
| muted / paper | 4.5 | 4.71 | 7.42 | 7.07 |
| muted / card | 4.5 | 5.33 | 6.39 | 9.74 |
| accent / paper | 4.5 | 6.88 | 10.92 | 9.50 |
| accent / card | 4.5 | 7.78 | 9.40 | 13.08 |
| alert / paper | 4.5 | 6.37 | 10.03 | 7.39 |
| alert / card | 4.5 | 7.20 | 8.63 | 10.18 |
| success / paper | 4.5 | 6.42 | 12.89 | 7.10 |
| success / card | 4.5 | 7.26 | 11.09 | 9.78 |
| board-text / board | 4.5 | 13.50 | 13.50 | 13.50 |
| gold / card | 3 | 3.10 | 4.83 | 3.16 |
| gold-text / card | 4.5 | 6.68 | 11.35 | 6.80 |
| line-1 / paper | 3 | 3.66 | 5.73 | 3.59 |
| line-1 / card | 3 | 4.13 | 4.93 | 4.94 |
| line-2 / paper | 3 | 4.16 | 3.71 | 3.47 |
| line-2 / card | 3 | 4.70 | 3.19 | 4.78 |
| line-3 / paper | 3 | 4.22 | 5.92 | 3.82 |
| line-3 / card | 3 | 4.77 | 5.09 | 5.26 |
| focus / paper | 3 | 13.89 | 15.74 | 13.71 |
| focus / card | 3 | 15.70 | 13.54 | 18.88 |
| ink / paper | 3 | 13.89 | 15.74 | 13.71 |
| primary-text / primary-fill | 4.5 | 15.70 | 13.54 | 18.88 |
| secondary-text / secondary-fill | 4.5 | 15.70 | 13.54 | 18.88 |
| board-label / board | 4.5 | 13.50 | 13.50 | 13.50 |
| badge-text / badge-fill | 4.5 | 15.70 | 13.54 | 18.88 |
| success / badge-fill | 4.5 | 7.26 | 11.09 | 9.78 |
| accent / badge-fill | 4.5 | 7.78 | 9.40 | 13.08 |

## Content Security Policy

```text
default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; style-src 'self'; script-src 'self'; font-src 'self'; img-src 'self' data:
```

## Known limitations and deferred backend work

See ADR 086 in [Decisions](DECISIONS.md). Each item requires explicit approval before backend work begins.

- Linked library resources on course detail.
- Course-list pagination.
- Module-order freeze flag on course detail.
- An alert for invalid role changes.
- Pending approval filters and pagination.
- Video captions and transcripts.

F5 browser evidence and fresh-clone verification are pending. The local contact sheets are review evidence from earlier phases.
