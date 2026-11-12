# Local model as a delegated worker

MacroPulse can hand scoped coding tasks to an open-weight model running on the developer's own GPU.
The lead (Claude Code) writes the brief and the tests, the local model writes one file, and the lead
reviews, runs the checks and either sends feedback or corrects the file. Nothing the model writes is
accepted without that review.

## Setup used (verified 2026-11-11)

| Part | Choice |
|---|---|
| GPU | AMD Radeon RX 7800 XT, 16 GB VRAM (Windows 11) |
| Runtime | llama.cpp `b12259`, official Windows **Vulkan** build (`llama-b12259-bin-win-vulkan-x64.zip`, SHA-256 checked against the GitHub release digest) |
| Model | `unsloth/Qwen3.8-27B-GGUF`, file `Qwen3.8-27B-UD-Q3_K_XL.gguf` (13.15 GB, SHA-256 checked against Hugging Face), Apache-2.0 |
| Fit | the whole model on the GPU; 32k context |

Start the server (localhost only):

```powershell
llama-server.exe -m <path>\Qwen3.8-27B-UD-Q3_K_XL.gguf --alias qwen3.8-27b `
  --host 127.0.0.1 --port 8080 -ngl 99 -c 32768 -np 1 -fa on --jinja --no-webui
```

- Keep the **f16 KV cache** (no `--cache-type-k/v q8_0`): on Vulkan, flash attention over a q8_0 KV
  cache falls back to the CPU and prompt processing drops to single digits of tokens per second.
- Measured with the f16 cache: prompt processing about 410 to 560 tokens/s, generation about 30 tokens/s
  (13 to 14 tokens/s once the context is long).

## Two ways to delegate

### 1. Single-file tasks (recommended): `scripts/agents/local_task.py`

```powershell
uv run --no-project python scripts/agents/local_task.py --name report-csv `
  --brief .agents/briefs/report-csv.md `
  --context apps/api/src/macropulse_api/reports/content.py apps/api/tests/test_report_render.py `
  --output apps/api/src/macropulse_api/reports/csv_export.py
# after review / failing tests:
uv run --no-project python scripts/agents/local_task.py ... --feedback .agents/feedback/report-csv-1.md
```

- The brief, the context files and (for a revision) the current file plus the review feedback go in
  one request; the model must answer with the complete file in one code block.
- The script writes **only** `--output` (inside the repository, never `.git`, `.venv` or
  `node_modules`), refuses cut-off answers, logs every run to `.agents/local-runs/` (git-ignored) and
  records it in the Obsidian vault (`60 Agents/Codex runs/… local-*`).

### 2. Agentic Codex on the local model: `codex-task.ps1 -Local`

`scripts/agents/codex-task.ps1 -Local` points Codex CLI at the local server (Responses API) with
per-call `-c` overrides; `~/.codex/config.toml` is not changed. It works (a read-only smoke task was
answered correctly), but on a real task the 27B model spent 31 minutes reading and searching files
without writing anything before the run was interrupted. Use it only for small read-only questions.

## What happened on Phase 9 (the report builder)

The lead wrote the content contract, the content builder, the API and all tests; the local model
wrote the four renderer/view files.

| File | Rounds | Model time | Problems found in review |
|---|---|---|---|
| `reports/charts.py` | 2 | 55 s + 55 s | Round 1 plotted points at integer positions instead of dates (bands and bars misaligned) and called a non-existent `canvas.close()`; round 2 fixed both. Lead fixed the `Axes` type annotations. |
| `reports/csv_export.py` | 1 | 32 s | None. |
| `reports/pdf.py` | 3 | 180 s + 213 s + 208 s | Module-level global for header/footer (not thread-safe), notes interleaved in narrow columns, table widths summing to 104 %, orphaned headings. Lead fixed a ragged-row / misaligned `SPAN` bug the tests did not catch, heading `keepWithNext`, and dropped the meaningless SDMX flag "A". |
| `views/reports-view.tsx` | 1 | 56 s | Used a non-existent button variant (`default`; the model flagged its own doubt). Lead fixed it. |

Lessons: specification tests plus a visual check of the real output caught every problem; the model
was reliable on small, fully specified files and needed review on anything with layout or
concurrency concerns. It never touched files outside its brief in single-file mode.

## What happened on the visual refresh (2026-11-11)

The lead designed the tokens, surfaces, shell and chart theme; the local model wrote five
self-contained files from briefs in `.agents/briefs/` (`sparkline`, `gauge`, `pulse-line`,
`chart-theme-tests`, `design-doc`).

| File | Rounds | Model time | Problems found in review |
|---|---|---|---|
| `charts/sparkline.tsx` | 2 | 64 s + 70 s | Round 1: 7/9 specification tests; y computed while min/max were still being discovered, gaps detected with the wrong index, `useId` after an early return (the model's notes claimed otherwise). Round 2 fixed all three but introduced `undefined + 1`; lead fixed that and replaced the end circle (distorted when the SVG is stretched) by a round-capped stroke. |
| `model/probability-gauge.tsx` | 1 | 81 s | Logic correct on the first try. The brief's own viewBox was too small for the tick labels and the end labels sat on their tick marks — the lead's specification errors, fixed by the lead. |
| `ui/pulse-line.tsx` | 1 | 80 s | 5/5 specification tests, but the gradient and the blur filter shared one id and the filter was referenced without `url(#…)` — invisible to the tests, found by reading the code. |
| `charts/theme.test.ts` | 1 | 82 s | None; 12 tests with hand-computed values, accepted as written. |
| `docs/DESIGN.md` | 1 | 173 s | Faithful to the sources; "Used by" entries the model could not see were left blank (as instructed) and completed in review. |

Tooling bug found on the way: twice the model wrapped a code file in a four-backtick fence *and* a
three-backtick fence, and `local_task.py` wrote the inner fence into the file. `unwrap()` now strips
such an inner fence for non-Markdown outputs (`scripts/tests/test_local_task.py`).

Lesson confirmed: specification tests catch arithmetic, not rendering — every visual component was
also checked in the browser and by reading the SVG.

## What happened on the ALFRED vintages (2026-11-12)

| File | Rounds | Model time | Problems found in review |
|---|---|---|---|
| `connectors/alfred.py` | 1 | 98 s | 18/18 specification tests on the first try. Review found two things the tests did not: pagination advanced by `page_size` instead of the rows received (a server that caps `limit` would make it skip rows silently) and non-string JSON fields raised `TypeError` instead of `ConnectorError`. Lead fixed both and added tests. |
| `vintages.py` | 1 | 117 s | All specification tests on the first try; the indexed and the plain lookup were two copies of the same rule — lead merged them into one helper; mypy needed the summary rewritten to keep `revision` narrowed. |
| `lib/revisions.ts` | 1 | 55 s | 7/7 on the first try; accepted as written (one defensive extra branch). |

The lead wrote the storage, migration, API, CLI, the card and every test. The real data review caught
what no test could: ALFRED's 1992 vintage back-filled real GDP to 1947, so "first appearance in the
archive" is not a first release — fixed with a 120-day publication window.

## What happened on the vintage replay (2026-11-12)

| File | Rounds | Model time | Problems found in review |
|---|---|---|---|
| `vintages.py` (`vintage_series`) | 1 | 239 s | 8/8 specification tests on the first try, but two rules of the brief were not followed: each level was picked twice (as value and again as base) instead of once, and an unknown transform was rejected only when the series had a value. Lead rewrote the loop to pick every level once and to check the transform first. |
| `model/vintage-replay-card.tsx` | 1 | 232 s | 5/5 specification tests on the first try. Review found what the tests could not: `JSX.Element` (no global `JSX` namespace in React 19, so `tsc` fails), `React.ReactNode` without an import, an unused `cn` import (ESLint) and unescaped apostrophes in JSX text. Lead fixed all four and gave the card an accessible name for axe. |

The lead wrote the fold re-fit, the API service, schema, route, the hook, the fixtures, every test
and the history-page integration. Real-data review: every replayed US quarter reproduced its stored
estimate before the first-release inputs were scored.

