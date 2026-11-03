# Capacity Connect: Frontend Brief (binding)

## 1. Mission and stage
The backend is complete and tagged backend-complete. The frontend is a SKIN and
PRESENTATION layer over the existing views. The approved design is the "Metro
Map" system (public name "Line"): subjects are lines, modules are stations,
announcements are a departure board, quizzes are tickets. Backend behaviour,
models, URL names and permissions must NOT change. A backend change is allowed
only to fix a real bug under the bug protocol (backend brief section 10).

## 2. Hard rules
- No new Python dependencies. No Node, no npm, no build step, no CSS framework
  (no Bootstrap, Tailwind), no JS framework, no CDN, no remote fonts or images,
  no analytics.
- Plain CSS with custom properties, plain JavaScript (small files, ES2020, no
  libraries). Everything served from our own static files.
- CSP stays strict (default-src 'self'; frame-ancestors 'none'; base-uri 'self';
  form-action 'self'). Allow only what is needed: style-src 'self', script-src
  'self', font-src 'self', img-src 'self' data:. NO inline <style>, NO style=""
  attributes, NO inline <script>, NO inline event handlers. Dynamic shapes use
  SVG attributes, <progress>/<meter>, or CSS classes from a fixed scale. Update
  the CSP setting with an ADR and a test that no template contains inline style
  or script.
- Templates only DISPLAY: they consume existing selectors and dataclasses
  (docs/URL_MAP.md). No queries, no business rules, no money/percent math in
  templates; format only.
- Keep the backend rules: functions <= 25 lines, hand-written Python modules <=
  250 lines. CSS files <= 400 lines each, JS files <= 150 lines each, templates
  <= 150 lines each; split into partials/includes. No duplicated markup: reuse
  components in templates/components/.
- Every file UTF-8, no BOM. Reports use the same 9-field format. No claim without
  evidence.

## 3. Structure
static/css/tokens.css (themes and scales), base.css (reset, typography, layout),
components.css (button, card, field, alert, table, badge, nav, ticket, board,
progress), pages/*.css (only page-specific layout); static/js/theme.js (theme
bootstrap + toggle), static/js/app.js (small progressive enhancements only);
static/fonts/ (self-hosted woff2 + OFL license files); templates/components/
for reusable partials. Pages must work fully WITHOUT JavaScript.

## 4. Design tokens (exact starting values)
Line colours (all themes): --line-1 #e76f51, --line-2 #2a6fdb, --line-3 #1fa97a.
Themes via [data-theme] on <html>:
- day:  --paper #f2efe6, --ink #14213d, --card #fffdf7, --muted #6b6a65
- night: --paper #0f1730, --ink #eef1ff, --card #18234a, --muted #9aa6d6
- sign: --paper #ffd93d, --ink #111111, --card #ffffff, --muted #444444
Default theme: day; if the user has not chosen and the system prefers dark use
night; a visible toggle (day / night / signage) persists the choice in
localStorage (wrapped in try/catch). A tiny external theme.js in <head> sets
data-theme before paint (no flash). All colours come from tokens, never literal
values in components. If a token pair fails contrast, ADJUST the token (for
example a darker text variant of a line colour), never the requirement.
Type: Bricolage Grotesque (headings, 600/800), Inter (body 400/600), Space Mono
(labels, board, ticket 400/700); font-display: swap; preload the two most used
woff2 files; fallbacks system-ui, ui-monospace. Spacing scale 4/8/12/16/24/32/48.
Radius 14px cards, 99px pills. Cards: 2px solid var(--ink) border, no shadows
except the ticket and board. Focus: 3px visible outline, never removed.

## 5. Components (match the approved design)
- App shell: skip link, header (logo roundel + name, role-aware nav, theme toggle,
  user menu with POST logout), <main id="main">, footer. Mobile nav collapses
  without JS (details/summary or CSS-only pattern).
- Departure board: dark panel (#0b0d10, text #ffd24a, mono) with rows TYPE |
  message | when; uses announcements.board().
- Station map: server-rendered SVG from station_map_for(); DONE = filled line
  colour, CURRENT = ring + pulsing halo (disabled under prefers-reduced-motion),
  LOCKED = hollow dashed; interchange = larger station; each station is a link
  with text labels and an accessible name that states the state; a plain list
  version is the accessible fallback under the SVG.
- Quiz ticket: ticket card with notches and a header (title, deadline, attempts
  left), progress as stops, one fieldset/legend per question with real radio
  inputs, large touch targets, a server-computed time-left (no JS needed;
  optional JS only displays a countdown, the server stays authoritative).
- Result page: pass/fail stamp, per-question right/wrong, correct answer ONLY
  when the backend provides it.
- Certificates list: formal card style (gold #b8892b accent) matching the PDF.
- Dashboards (control room, station master): stat tiles, line-load bars with
  <meter>/<progress>, participation heat strip using classes, data tables with
  captions and scope attributes. No chart library.
- Forms: visible labels, help text linked with aria-describedby, errors linked and
  announced (role=alert / aria-live), a summary of errors at the top.
- Messages, empty states, pagination, error pages (403, 404, 429, 500) restyled.

## 6. Accessibility (WCAG 2.2 AA)
lang on <html>; one h1 per page and no skipped heading levels; landmarks;
labels for every control; alt text (empty alt for decoration); visible focus;
keyboard-operable everything; target size >= 44px for primary actions on touch;
contrast >= 4.5:1 for text and >= 3:1 for UI components and graphics, verified
FOR EVERY THEME; never colour alone (state is also text/shape/pattern);
prefers-reduced-motion honoured; zoom to 200% without loss; no content that
requires hover.

## 7. Responsive
Mobile-first. Breakpoints 480 / 768 / 1024 / 1280. Test widths 375, 768 and 1280.
No horizontal page scroll; wide tables scroll inside their own container; the
station map scales via viewBox.

## 8. Testing rules (no browser library)
- Template/HTML tests with Python's html.parser (no dependency): lang present,
  one h1, heading order, every input has a label, images have alt, landmarks
  exist, no inline style/script/handlers, no external URLs (http/https) in
  templates or CSS (except in links to our own verification URL text), skip
  link first.
- Contrast test: parse the tokens from tokens.css for every theme and compute
  WCAG contrast ratios for the declared text/background pairs in pure Python.
- CSS lint-ish tests: no !important except in a documented reduced-motion /
  print block; no hard-coded colours outside tokens.css; file size limits.
- Rendering evidence: use headless Microsoft Edge or Chrome already installed on
  the machine (`msedge --headless --screenshot=...`, no dependency) to produce
  screenshots at 375, 768 and 1280 px, for the day, night and sign themes, into
  .local/screenshots/. If no browser is available say so. The user reviews them.
- All existing backend tests must stay green; the permission matrix and route
  audit must not change.

## 9. Frontend phases (one branch each, wait for "approved")
F0 design foundations (tokens, fonts, base layout, components, theme toggle,
   CSP update, error pages, test harness). F1 public pages (home with board,
   login, signup, verify). F2 trainee (landing, courses, station map, course
   detail, quiz ticket, results, certificates, profile, feedback). F3 trainer
   (landing, courses/modules, library, questionnaires/questions, participation,
   competencies, dashboard, feedback). F4 admin (control room, approvals,
   users, catalog, announcements, ranking, certificates). F5 responsive and
   accessibility sweep, final screenshots, frontend handoff report.

## 10. Reporting
Compact 9-field report, plus: list of new static files with sizes, test node
names, contrast table (pair | ratio | theme | pass), screenshot file list, and
anything that deviates from the design (with a reason).
