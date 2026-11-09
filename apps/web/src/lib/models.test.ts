import { describe, expect, it } from "vitest";

import type { ModelList, ModelSummary } from "@macropulse/shared-types";

import { modelState, modelSummaryText } from "@/lib/models";

function model(overrides: Partial<ModelSummary>): ModelSummary {
  return {
    id: "20261109T173231Z-h2-hist_gbm",
    run_id: "20261109T173231Z",
    horizon: 2,
    model_key: "hist_gbm",
    name: "HistGradientBoosting",
    role: "candidate",
    status: "evaluated",
    selected: true,
    unavailable_reason: null,
    created_at: "2026-11-09T17:32:31Z",
    target_version: "technical-recession-v1",
    feature_set_version: "core-asof-v2",
    training_rows: 702,
    training_events: 51,
    training_last_as_of: "2026-Q1",
    data_snapshot: "sha256:x",
    code_revision: "abc",
    artifact_available: true,
    headline: {},
    selection_note: "beats the prevalence baseline",
    heldout_check: { evaluated: true, beats_prevalence: false },
    ...overrides,
  };
}

describe("modelState", () => {
  it("reports nothing trained for an empty list, with the API's note", () => {
    const state = modelState({ run_id: null, items: [], note: "No model has been trained yet." } satisfies ModelList);
    expect(state.trained).toBe(false);
    expect(modelSummaryText(state)).toContain("No model has been trained yet");
  });

  it("names the published models and states a failed held-out check", () => {
    const list: ModelList = {
      run_id: "20261109T173231Z",
      note: "",
      items: [
        model({}),
        model({ id: "x-h4", horizon: 4, model_key: "logistic", name: "Logistic Regression" }),
        model({ id: "y", horizon: 4, model_key: "prevalence", role: "baseline", selected: false }),
      ],
    };
    const state = modelState(list);
    expect(state.published.map((p) => p.horizon)).toEqual([2, 4]);
    const text = modelSummaryText(state);
    expect(text).toContain("2Q: HistGradientBoosting · 4Q: Logistic Regression");
    expect(text).toContain("2Q and 4Q models do not beat the historical base rate");
  });

  it("does not claim a failure when the held-out check passed or was not evaluated", () => {
    const state = modelState({
      run_id: "r",
      note: "",
      items: [model({ heldout_check: { evaluated: true, beats_prevalence: true } }), model({ horizon: 4, heldout_check: null })],
    });
    expect(modelSummaryText(state)).not.toContain("do not beat");
    expect(state.published[1]?.beatsBaselineHeldout).toBeNull();
  });
});
