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
 * `built`:      the page works on stored official data (verified in the browser and by tests).
 * `foundation`: the route exists and shows real API state, but its full feature set is scheduled.
 * `planned`:    the route exists only as an honest "not built yet" page — no simulated output.
 */
export type ModuleState = "built" | "foundation" | "planned";

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
    state: "built",
    summary: "Economic-health dashboard for the selected country.",
    capabilities: [
      "KPI tiles with the latest stored value, change, source flag and provenance tooltip",
      "Real GDP growth (NBER reference shading for the US), inflation and unemployment charts",
      "Latest stored periods and data-coverage indicator; recession risk once a model exists (Phase 5)",
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
    state: "built",
    summary: "Deep macro profile per country: growth, prices, labour, monetary, fiscal and data.",
    capabilities: [
      "Section tabs with line/bar toggles, q/q and y/y growth as separate documented series",
      "History windows, source and quality notes, adjustment and unit labels, as-of cut-off",
      "CSV/PNG export, table view and a lineage table with raw-row downloads",
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
    state: "built",
    summary: "Cross-country comparison of up to four countries on comparable units and spans.",
    capabilities: [
      "Aligned charts and a latest-value table for growth, inflation, unemployment, debt and policy rate",
      "History window, as-published or spread-vs-baseline normalisation on common periods",
      "Comparability warnings for different sources, frequencies and the shared euro area rate",
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
    state: "built",
    summary:
      "Estimated probability of a technical recession within the next 2 or 4 quarters at an explicit as-of date.",
    capabilities: [
      "Live inference from stored data and the saved artifact, with model version, as-of date and freshness",
      "Feature contributions (exact log-odds for logistic, local sensitivity otherwise), track record and limitations",
      "Walk-forward risk timeline with realised technical recessions; 'model not trained' state when absent",
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
    state: "built",
    summary: "Models, baselines, walk-forward evaluation, calibration and explanations.",
    capabilities: [
      "Comparison table with Brier score, skill, ROC/PR-AUC (N/A when undefined) for every model and split",
      "Calibration, ROC and PR curves, confusion matrix at 0.5, per-country metrics and fold timeline",
      "Reproducibility card: command, seed, code revision, dataset snapshot and model version",
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
    state: "built",
    summary: "Source health, freshness, coverage and lineage of every stored observation.",
    capabilities: [
      "Source health with last successful fetch and failed syncs",
      "Per-series lineage: exact request, rows, span, fetch time and latest quality checks",
      "Coverage matrix and raw-row CSV downloads with per-row provenance",
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
export const CURRENT_PHASE = { number: 6, name: "Explainable risk & ML lab", total: 10 } as const;
