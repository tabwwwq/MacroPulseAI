import type { Revisions } from "@macropulse/shared-types";

/** Test fixture shaped like GET /api/vintages/revisions (synthetic values, test-only). */
export const REVISIONS_FIXTURE: Revisions = {
  country: "US",
  indicator: { id: "real_gdp_qoq", name: "Real GDP growth (q/q)", unit: "%" },
  transform: "Quarter-on-quarter % change of real GDP levels (not annualised).",
  revision_unit: "pp",
  series: {
    series_id: "fred:GDPC1:GDPC1:US",
    dataset: "GDPC1",
    source_url: "https://api.stlouisfed.org/fred/series/observations?series_id=GDPC1&api_key=REDACTED",
    retrieved_at: "2026-11-12T08:00:00Z",
    rows: 4426,
    vintages: 420,
    first_vintage: "1991-12-04",
    last_vintage: "2026-10-29",
  },
  archive_start: "1991-12-04",
  points: [
    { period: "1990-Q1", first_published: "1992-12-22", first_value: 1.1, latest_value: 1.0, revision: -0.1, first_release: false },
    { period: "2022-Q1", first_published: "2022-04-28", first_value: -0.36, latest_value: -0.25, revision: 0.11, first_release: true },
    { period: "2022-Q2", first_published: "2022-07-28", first_value: -0.23, latest_value: 0.14, revision: 0.37, first_release: true },
    { period: "2022-Q3", first_published: "2022-10-27", first_value: 0.65, latest_value: null, revision: null, first_release: true },
    { period: "2020-Q2", first_published: "2020-07-30", first_value: -9.49, latest_value: -7.88, revision: 1.61, first_release: true },
  ],
  summary: { count: 3, mean_abs_revision: 0.6967, max_abs_revision: 1.61, max_abs_period: "2020-Q2", sign_changes: ["2022-Q2"] },
  technical_signals: [
    { period: "2020-Q2", published: "2020-07-30", as_first_known: true, in_latest_data: true, first_values: [-1.26, -9.49], latest_values: [-1.32, -7.88] },
    { period: "2022-Q2", published: "2022-07-28", as_first_known: true, in_latest_data: false, first_values: [-0.4, -0.23], latest_values: [-0.25, 0.14] },
    { period: "2001-Q3", published: "2001-10-31", as_first_known: false, in_latest_data: true, first_values: [0.1, -0.1], latest_values: [-0.3, -0.4] },
  ],
  computed_at: "2026-11-12T08:01:00Z",
  note: "First release: the value derived from the first vintage in which the period appeared.",
};
