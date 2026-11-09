import type { ModelList } from "@macropulse/shared-types";

export interface PublishedModel {
  horizon: number;
  name: string;
  isBaseline: boolean;
  /** `null` when the held-out check could not be evaluated. */
  beatsBaselineHeldout: boolean | null;
}

export interface ModelState {
  trained: boolean;
  runId: string | null;
  published: PublishedModel[];
  note: string;
}

/** What has actually been trained, read from `/api/models` — never assumed. */
export function modelState(list: ModelList | undefined): ModelState {
  if (!list || list.items.length === 0) {
    return { trained: false, runId: null, published: [], note: list?.note ?? "Model status unknown." };
  }
  const published = list.items
    .filter((m) => m.selected)
    .map((m) => {
      const check = m.heldout_check as { evaluated?: boolean; beats_prevalence?: boolean } | null;
      return {
        horizon: m.horizon,
        name: m.name,
        isBaseline: m.role === "baseline",
        beatsBaselineHeldout: check?.evaluated ? Boolean(check.beats_prevalence) : null,
      };
    })
    .sort((a, b) => a.horizon - b.horizon);
  return { trained: true, runId: list.run_id, published, note: list.note };
}

/** One honest sentence about the published models, for status tiles. */
export function modelSummaryText(state: ModelState): string {
  if (!state.trained) return "No model has been trained yet (`uv run macropulse train`).";
  const parts = state.published.map((p) => `${p.horizon}Q: ${p.name}`).join(" · ");
  const failing = state.published.filter((p) => p.beatsBaselineHeldout === false).map((p) => `${p.horizon}Q`);
  const caveat = failing.length
    ? ` On the 2015+ held-out years the ${failing.join(" and ")} model${failing.length > 1 ? "s do" : " does"} not beat the historical base rate.`
    : "";
  return `Trained run ${state.runId} — ${parts}.${caveat}`;
}
