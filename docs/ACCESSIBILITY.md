# Accessibility verification

## Automated checks

- `test_seeded_named_html_routes` renders seeded pages through Django clients and checks the portal shell, heading order, labels, asset restrictions, ID references, link and button names, and table captions and scopes.
- `test_theme_contrast` checks declared token pairs in three themes.
- `test_all_motion_is_inside_no_preference_blocks` checks shipped motion declarations.
- `test_templates_have_no_inline_styles_scripts_or_handlers` and `test_static_file_budgets_and_local_css` check static policy and budgets.

## Browser evidence

Earlier phase reports include headless Edge viewport and theme checks, and a no-JavaScript quiz submission. F5 layout, zoom, forced colours, print output, text spacing and keyboard journeys remain pending.

## Manual checklist

Headless emulation is not a substitute for screen reader testing. Run this checklist with NVDA or another screen reader and a browser before submission.

- Login. Navigate from the skip link to the form. Trigger an error and verify the alert, its focus and the field association.
- Station map. Read the map description and the text list. Confirm station names, statuses and course links can be understood with the screen off.
- Quiz paper. Confirm the legend announces the question number and marks. Use arrow keys to select a radio and verify the time-left text and Submit button.
- Result. Confirm the status, score and review read in order, including the timeout explanation where present.
- Certificates. Read each certificate ID, course, grade and date. Confirm Download PDF has a meaningful destination.
- Admin approvals. Read table headings and row data. Open and close the reject disclosure. Confirm the Approve and Confirm reject actions are identifiable.
