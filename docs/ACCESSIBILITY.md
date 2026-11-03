# Accessibility verification

## Automated checks

- `test_seeded_named_html_routes` renders seeded pages through Django clients and checks the portal shell, heading order, labels, asset restrictions, ID references, link and button names, and table captions and scopes.
- `test_theme_contrast` checks declared token pairs in three themes.
- `test_all_motion_is_inside_no_preference_blocks` checks shipped motion declarations.
- `test_templates_have_no_inline_styles_scripts_or_handlers` and `test_static_file_budgets_and_local_css` check static policy and budgets.

## Browser evidence

- Headless Edge measured 23 pages at seven widths in Day, Night and Signage. A 640 px CSS viewport at device scale 2 modeled the reflow of a 1280 px layout at 200%. This is a reflow proxy rather than native browser zoom.
- Forced-colours captures cover home, login, station map, quiz paper and both Control room pages. The station map reported zero animations with reduced motion enabled.
- Browser PDF output covers the certificate list, assessment result and public verification result.
- Test-only text spacing ran on home, login, station map, quiz paper and Admin dashboard. Scroll and overflow-hidden text checks passed.
- With JavaScript disabled, Edge verified the system dark theme, narrow and wide navigation, the station text list, an actual quiz submission, and announcement creation and confirmed deletion. Tab sequences were captured for the four representative journeys.

Screen readers, real devices, Firefox, Safari, Android and iOS were outside this run. The browser checks sampled form submissions and did not submit every portal form with scripting disabled.

## Manual checklist

Headless emulation is not a substitute for screen reader testing. Run this checklist with NVDA or another screen reader and a browser before submission.

- Login. Navigate from the skip link to the form. Trigger an error and verify the alert, its focus and the field association.
- Station map. Read the map description and the text list. Confirm station names, statuses and course links can be understood with the screen off.
- Quiz paper. Confirm the legend announces the question number and marks. Use arrow keys to select a radio and verify the time-left text and Submit button.
- Result. Confirm the status, score and review read in order, including the timeout explanation where present.
- Certificates. Read each certificate ID, course, grade and date. Confirm Download PDF has a meaningful destination.
- Admin approvals. Read table headings and row data. Open and close the reject disclosure. Confirm the Approve and Confirm reject actions are identifiable.
