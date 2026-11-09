import {
  ChartSpline,
  Database,
  FileText,
  FlaskConical,
  Gauge,
  GitCompareArrows,
  Globe,
  LayoutDashboard,
  type LucideIcon,
  RotateCcwClock,
  SlidersHorizontal,
} from "lucide-react";

export type ModuleGroup = "Monitor" | "Models" | "Platform";

/**
 * `foundation`: the route exists and shows real API state, but its full feature set is scheduled.
 * `planned`:    the route exists only as an honest "not built yet" page — no simulated output.
 */
export type ModuleState = "foundation" | "planned";

export interface AppModule {
  id: string;
  href: string;
  label: string;
  group: ModuleGroup;
  icon: LucideIcon;
  phase: number;
  state: ModuleState;
  summary: string;
  capabilities: string[];
  prerequisites: string[];
}

export const MODULES: AppModule[] = [
  {
    id: "overview",
    href: "/",
    label: "Overview",
    group: "Monitor",
    icon: LayoutDashboard,
    phase: 4,
    state: "foundation",
    summary: "Economic-health dashboard for the selected country.",
    capabilities: [
      "KPI tiles for real GDP growth, inflation, unemployment and policy rate, each traced to a sourced observation",
      "Recession-risk timeline with historic downturn shading (only once a trained model exists)",
      "Latest-release timeline and data-coverage indicator",
    ],
    prerequisites: ["Observations ingested (Phase 3)"],
  },
  {
    id: "countries",
    href: "/countries",
    label: "Countries",
    group: "Monitor",
    icon: Globe,
    phase: 4,
    state: "foundation",
    summary: "Deep macro profile per country: growth, prices, labour, monetary, fiscal and data.",
    capabilities: [
      "Section tabs with line/bar and q/q vs y/y toggles where meaningful",
      "Date ranges, source tooltips, seasonal-adjustment and unit labels",
      "CSV/PNG export and a scrollable history table with explicit missing-data notes",
    ],
    prerequisites: ["Observations ingested (Phase 3)"],
  },
  {
    id: "compare",
    href: "/compare",
    label: "Compare",
    group: "Monitor",
    icon: GitCompareArrows,
    phase: 4,
    state: "foundation",
    summary: "Cross-country comparison of up to four countries on comparable units and spans.",
    capabilities: [
      "Aligned charts and table for growth, inflation, unemployment and debt where compatible",
      "Period selection, normalisation choices and a consistent baseline",
      "Policy-rate coverage that labels the shared euro area rate as shared",
    ],
    prerequisites: ["Observations ingested (Phase 3)"],
  },
  {
    id: "recession",
    href: "/recession",
    label: "Recession risk",
    group: "Models",
    icon: Gauge,
    phase: 6,
    state: "foundation",
    summary:
      "Estimated probability of a technical recession within the next 2 or 4 quarters at an explicit as-of date.",
    capabilities: [
      "Calibrated probability with model name, version, as-of date and data freshness",
      "Contributors via SHAP or permutation importance, with methodology and limitations",
      "An explicit 'model not trained' state — never a fabricated risk number",
    ],
    prerequisites: ["Observations ingested (Phase 3)", "Trained and evaluated model (Phase 5)"],
  },
  {
    id: "forecasts",
    href: "/forecasts",
    label: "Forecast studio",
    group: "Models",
    icon: ChartSpline,
    phase: 7,
    state: "foundation",
    summary: "Multi-step forecasts for GDP growth, inflation and unemployment with empirical intervals.",
    capabilities: [
      "Naive baselines plus a stronger challenger, evaluated with rolling backtests",
      "Historical actuals, dashed projections and empirically calibrated interval ribbons",
      "Error diagnostics and downloads; N/A rather than invented values",
    ],
    prerequisites: ["Observations ingested (Phase 3)", "Forecast backtests (Phase 7)"],
  },
  {
    id: "scenarios",
    href: "/scenarios",
    label: "Scenario lab",
    group: "Models",
    icon: SlidersHorizontal,
    phase: 7,
    state: "planned",
    summary: "Exploratory model sensitivity analysis — not a causal economic simulation.",
    capabilities: [
      "Sliders for inflation, unemployment, policy-rate and GDP shocks with bounded inputs",
      "Baseline vs scenario risk and feature-contribution deltas",
      "Out-of-distribution warnings, reset, save and export",
    ],
    prerequisites: ["Trained and evaluated model (Phase 5)"],
  },
  {
    id: "history",
    href: "/history",
    label: "Crisis time machine",
    group: "Models",
    icon: RotateCcwClock,
    phase: 8,
    state: "planned",
    summary: "Replay what a model could have known at a past as-of date versus what happened next.",
    capabilities: [
      "Strict temporal eligibility of features at the chosen as-of date",
      "Vintage-backed vs 'revised-data / release-lag approximation' labelling",
      "Predicted risk vs realised technical-recession outcome, including misses",
    ],
    prerequisites: ["Trained and evaluated model (Phase 5)", "As-of feature snapshots (Phase 5)"],
  },
  {
    id: "lab",
    href: "/lab",
    label: "ML laboratory",
    group: "Platform",
    icon: FlaskConical,
    phase: 6,
    state: "planned",
    summary: "Models, baselines, walk-forward evaluation, calibration and explanations.",
    capabilities: [
      "Comparison table with Brier score, log loss, ROC/PR-AUC (N/A when undefined) and calibration",
      "Split timeline, confusion matrix at a stated threshold and sample/event counts",
      "Reproducibility card: command, seed, dataset snapshot and model version",
    ],
    prerequisites: ["Trained and evaluated model (Phase 5)"],
  },
  {
    id: "data",
    href: "/data",
    label: "Data observatory",
    group: "Platform",
    icon: Database,
    phase: 4,
    state: "foundation",
    summary: "Source health, freshness, coverage and lineage of every stored observation.",
    capabilities: [
      "Source health cards with last successful fetch and failed syncs",
      "Coverage heatmap, missing observations and staleness markers",
      "Metadata explorer, lineage and CSV download",
    ],
    prerequisites: ["Observations ingested (Phase 3)"],
  },
  {
    id: "reports",
    href: "/reports",
    label: "Reports",
    group: "Platform",
    icon: FileText,
    phase: 9,
    state: "planned",
    summary: "Dated, source-cited PDF reports with methodology, limitations and as-of dates.",
    capabilities: [
      "Country overview, charts and current model estimates when available",
      "Data citations, freshness and uncertainty notes",
      "CSV/JSON export of the underlying chart data",
    ],
    prerequisites: ["Observations ingested (Phase 3)"],
  },
];

export const MODULE_GROUPS: ModuleGroup[] = ["Monitor", "Models", "Platform"];

export function getModule(id: string): AppModule {
  const found = MODULES.find((m) => m.id === id);
  if (!found) throw new Error(`Unknown module: ${id}`);
  return found;
}

export function moduleForPath(pathname: string): AppModule | undefined {
  if (pathname === "/") return MODULES[0];
  return MODULES.find((m) => m.href !== "/" && (pathname === m.href || pathname.startsWith(`${m.href}/`)));
}

/** Current build phase of the project; shown in the UI so readers know what is implemented. */
export const CURRENT_PHASE = { number: 2, name: "Production-grade UI system", total: 10 } as const;
