import type { VintageReplay, VintageReplayInput } from "@macropulse/shared-types";

/** Test fixtures shaped like GET /api/history/vintage-replay (synthetic values, test-only). */

function input(
  feature: string,
  label: string,
  fromVintage: boolean,
  revised: number,
  vintage: number,
  period: string | null,
  vintagePeriod: string | null = period,
): VintageReplayInput {
  return {
    feature,
    label,
    from_vintage: fromVintage,
    revised_value: revised,
    revised_period: period,
    vintage_value: vintage,
    vintage_period: vintagePeriod,
    difference: vintage - revised,
  };
}

export const VINTAGE_REPLAY_FIXTURE: VintageReplay = {
  country: "US",
  horizon: 4,
  as_of: "2008-Q3",
  cutoff: "2008-09-30",
  vintage_date: "2008-09-30",
  archive_start: "1991-12-04",
  model_id: "20261112T120000Z-h4-logistic",
  fold_year: 2008,
  available: true,
  reason: null,
  reproduced: true,
  revised_probability: 0.12,
  vintage_probability: 0.315,
  vintage_band: "moderate",
  inputs: [
    input("gdp_qoq_1", "Real GDP q/q, latest quarter", true, -0.52, 0.71, "2008-Q2"),
    input("gdp_qoq_2", "Real GDP q/q, quarter before", true, 0.25, 0.25, "2008-Q1"),
    input("gdp_yoy_1", "Real GDP y/y", true, 1.01, 1.85, "2008-Q2"),
    input("gdp_neg_4", "Negative quarters in the last 4", true, 1, 0, "2008-Q2"),
    input("infl_yoy", "Inflation y/y", true, 5.37, 5.6, "2008-08"),
    input("infl_chg_6m", "Inflation change over 6 months", true, 1.07, 1.3, "2008-08"),
    input("unemp", "Unemployment rate", true, 6.1, 5.7, "2008-08", "2008-07"),
    input("unemp_chg_6m", "Unemployment change over 6 months", true, 1.1, 1.1, "2008-08", "2008-07"),
    input("rate", "Policy rate", false, 2, 2, "2008-08"),
    input("rate_chg_4q", "Policy rate change over 4 quarters", false, -3.25, -3.25, "2008-08"),
    input("term_spread", "Term spread (10y - 3m)", false, 2.14, 2.14, "2008-08"),
  ],
  note: "GDP, CPI inflation and unemployment as published on the cut-off date (ALFRED); market rates are not revised.",
  computed_at: "2026-11-12T12:00:00Z",
};

export const VINTAGE_REPLAY_UNAVAILABLE: VintageReplay = {
  ...VINTAGE_REPLAY_FIXTURE,
  as_of: "1990-Q4",
  cutoff: "1990-12-31",
  vintage_date: "1990-12-31",
  fold_year: 2000,
  available: false,
  reason: "ALFRED holds all three US vintages only from 1991-12-04; 1990-Q4 ended before that.",
  reproduced: null,
  vintage_probability: null,
  vintage_band: null,
  inputs: [],
};
