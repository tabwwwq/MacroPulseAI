Second review of pdf.py (lead), after rendering real reports and looking at every page.
All tests pass; these are layout bugs. Fix them and return the complete file. Do not change anything
else (the lead has already fixed `_make_table`; keep its current version exactly).

A. Orphaned chart headings: the `Heading3` of a chart stays at the bottom of one page while its image
   moves to the next page (seen for "Real GDP growth (q/q)" and "Policy rate"). Wrap each chart's
   heading, image (or the "No data for this chart." paragraph), note and source caption in one
   `KeepTogether([...])` (from `reportlab.platypus`).
B. Forecast table is wider than the frame: its column fractions add up to 1.04 (0.22 + 0.18 + 0.18 +
   0.14 + 0.14 + 0.09 + 0.09), so it sticks out of the left margin, and the 9 % "Coverage" column
   breaks the header word ("Covera ge"). Use fractions that sum to exactly 1.00:
   Indicator 0.19, Model 0.16, Origin → Target 0.18, Forecast 0.13, 80 % interval 0.13,
   Coverage 0.10, RMSE vs naive 0.11. Add an assertion-free check yourself: every table's widths must
   sum to `_FRAME_WIDTH`.
G. Bullets: wrapped lines start under the bullet instead of under the text. Give the bullet style a
   hanging indent: `leftIndent=10, bulletIndent=0` (keep font sizes as they are).
