Historical interim report, superseded by [the final backend handoff](BACKEND_HANDOFF_REPORT.md). The results and pending decision below describe that earlier checkpoint.

PHASE / TASK: T1 Testing stage (interim report)

STATUS: Needs decision

GOAL: Verify backend requirements and user journeys before final handoff.

WHAT CHANGED: B7 merged into main and tagged b7-approved; phase/t1-testing created. First carry-over commit ce88e50 adds demo professional history, proxy deployment warnings/tests, explicit non-debug DEMO_PASSWORD guard and quiz-paper query budget. Reviewer-approved R4 subject discovery fix is c333c5c. HTTP happy/failure journeys added in 98d992d; BUG 024 renders previously invisible authentication form errors in 7a88e7c. Requirements/security evidence is in TEST_REPORT.md; role URLs and dataclass contracts are in URL_MAP.md.

HOW IT WAS VERIFIED: Full suite: 1978 passed in 23.35s; coverage run: 1978 passed in 23.45s; TOTAL 3817 statements, zero missed, 522 branches, zero partial, 100%. Ruff check passes; 356 files formatted. makemigrations --check: No changes detected. Fresh migrations, Django check and pip check pass. Go-live check --deploy: System check identified no issues (0 silenced). No size/UTF-8/BOM violations. Fresh clone: 1978 passed in 27.57s; independent coverage is 100%. Reverse: 1978 passed in 25.29s; consecutive normal runs: 1978 in 26.35s and 25.14s. Per-app counts sum to 1978. All 20 mutation checks cause failures and are reverted. Four J1/J2 journey nodes pass. Query take 10/10; participants 4/4. Seed first/second qualifications 3/3, experiences 3/3, external certificates 2/2; every stored row/value unchanged. Full commands, 20-row mutation table, per-app counts, requirement table, security mapping and limits: docs/TEST_REPORT.md. Raw transcripts: .local/reports/.

DECISIONS AND ASSUMPTIONS: ADRs 068–070 record carry-over, R4 approval and HTTP bootstrap/setup interpretation. User quotation (2026-11-02): "Add subject filter, then continue (Recommended)". Other judgments are proposed by agent. J3 clarification is pending: published course/resource details and trainer profiles are intentionally shared, so an unrelated approved user is allowed to read them. Recommended classification preserves shared reads and requires 403/404 for ownership-restricted routes.

KNOWN ISSUES / RISKS: J3 generic HTTP isolation walk has not run; testing and final handoff are incomplete until the pending classification decision. R14 usability/device/accessibility is not verified and belongs to frontend. PostgreSQL, multi-process/load behavior, real-server deployment and external services are not tested. SQLite locking, non-transactional filesystem operations, best-effort cache throttles, limited non-Latin PDF fonts and current-name/PDF-snapshot differences remain documented. Behind one trusted reverse proxy set TRUSTED_PROXY_COUNT=1 or visitors share the proxy IP and throttle each other. HSTS is 3600 s; include-subdomains and preload are intentionally off until HTTPS is verified; strict go-live env passes zero warnings.

DEMO STEPS: On phase/t1-testing, follow README setup, seed_demo_data and runserver. Development password Demo-Connect-2026!; demo logins are printed. Visit My assessments and filter by subject. Qualifications/experience/external files now populate approved demo profiles. Non-debug forced seeding requires explicit DEMO_PASSWORD.

NEXT: Resolve the pending J3 shared-read classification, complete that journey and rerun affected verification; then deliver the final BACKEND HANDOFF REPORT. No testing-branch merge/tag or frontend work.
