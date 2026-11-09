"""`macropulse` command-line interface (database, OpenAPI export, dev server)."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import uvicorn

from macropulse_api.config import REPO_ROOT, get_settings
from macropulse_api.db import build_engine, build_sessionmaker
from macropulse_api.errors import ApiError
from macropulse_api.main import create_app
from macropulse_api.migrate import current_revision, head_revision, upgrade
from macropulse_api.services.registry_sync import sync_registry
from macropulse_api.services.sync import run_sync
from macropulse_api.services.training import heldout_check, train
from macropulse_economics.connectors import CONNECTORS
from macropulse_economics.connectors.http import Fetcher, make_client


def _cmd_db_upgrade(_args: argparse.Namespace) -> int:
    settings = get_settings()
    engine = build_engine(settings.database_url)
    try:
        upgrade(engine)
        with build_sessionmaker(engine)() as session:
            n_countries, n_sources = sync_registry(session)
        print(
            f"database at revision {current_revision(engine)} ({engine.dialect.name}); "
            f"registry synced: {n_countries} countries, {n_sources} sources"
        )
    finally:
        engine.dispose()
    return 0


def _cmd_db_current(_args: argparse.Namespace) -> int:
    engine = build_engine(get_settings().database_url)
    try:
        print(f"current={current_revision(engine)} head={head_revision()}")
    finally:
        engine.dispose()
    return 0


def _cmd_openapi(args: argparse.Namespace) -> int:
    schema = create_app().openapi()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # LF on every OS so CI can diff the committed schema byte-for-byte.
    out.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"wrote {out} ({len(schema.get('paths', {}))} paths)")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    uvicorn.run(
        "macropulse_api.main:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
        # Watch only Python sources (not node_modules / .next) when reloading.
        reload_dirs=[
            str(REPO_ROOT / "apps" / "api" / "src"),
            str(REPO_ROOT / "packages" / "economics" / "src"),
        ]
        if args.reload
        else None,
        log_config=None,
    )
    return 0


def _cmd_data_sync(args: argparse.Namespace) -> int:
    engine = build_engine(get_settings().database_url)
    try:
        if current_revision(engine) != head_revision():
            print(
                "Database is not migrated. Run `uv run macropulse db upgrade` first.",
                file=sys.stderr,
            )
            return 2
        with make_client() as client:
            report = run_sync(
                build_sessionmaker(engine),
                Fetcher(client),
                sources=args.source or None,
                countries=args.country or None,
            )
    finally:
        engine.dispose()

    width = max((len(o.series_id) for o in report.outcomes), default=20)
    for o in report.outcomes:
        state = "ok  " if o.ok else "FAIL"
        span = f"{o.first} .. {o.last}" if o.ok else (o.error or "")
        warn = f"  ({o.warnings} warning(s))" if o.warnings else ""
        print(f"{state} {o.series_id:<{width}} {o.rows:>6} rows  {span}{warn}")
    for source, (run_id, status) in sorted(report.runs.items()):
        print(f"run {run_id:>4}  {source:<9} {status}")
    if report.skipped:
        print(f"skipped {len(report.skipped)} mapping(s): " + "; ".join(report.skipped))
    total = sum(o.rows for o in report.outcomes)
    print(f"{total} observations upserted from {len(report.outcomes)} series")
    return 0 if all(status == "succeeded" for _, status in report.runs.values()) else 1


def git_revision() -> str | None:
    """Short commit hash (+ "-dirty" when the tree has changes), or None without git."""
    git = shutil.which("git")
    if git is None:
        return None
    try:
        sha = subprocess.run(  # noqa: S603 - fixed arguments, resolved git binary
            [git, "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()
        dirty = subprocess.run(  # noqa: S603
            [git, "status", "--porcelain"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return f"{sha}-dirty" if dirty else sha


def _fmt(value: float | None, digits: int = 3) -> str:
    return "N/A" if value is None else f"{value:.{digits}f}"


def _cmd_train(args: argparse.Namespace) -> int:
    engine = build_engine(get_settings().database_url)
    try:
        if current_revision(engine) != head_revision():
            print(
                "Database is not migrated. Run `uv run macropulse db upgrade` first.",
                file=sys.stderr,
            )
            return 2
        horizons = tuple(sorted(set(args.horizon or [2, 4])))
        command = "uv run macropulse train " + " ".join(sys.argv[2:])
        try:
            report = train(
                build_sessionmaker(engine),
                horizons=horizons,
                seed=args.seed,
                artifacts_root=None if args.no_artifacts else REPO_ROOT / "models" / "artifacts",
                command=command.strip(),
                code_revision=git_revision(),
            )
        except ApiError as exc:
            print(f"{exc.code}: {exc.message}", file=sys.stderr)
            return 2
    finally:
        engine.dispose()

    panel = report.panel
    print(f"run {report.run_id} · data {report.data_snapshot} · {len(panel.rows)} as-of rows")
    for iso, reason in report.skipped.items():
        print(f"  skipped {iso}: {reason}")
    for iso, runs in panel.events.items():
        spans = ", ".join(f"{a}..{b}" for a, b in runs) or "none"
        print(f"  {iso}: GDP observed to {panel.last_observed[iso]}; technical recessions: {spans}")
    for h, result in report.horizons.items():
        status = dict(panel.label_status[h])
        skipped = "; ".join(result.notes) or "no skipped folds"
        print(f"\nH={h}: labels {status}; folds {len(result.folds)}; {skipped}")
        cols = ("n", "ev", "brier", "skill", "logloss", "rocauc", "prauc", "rec@.5")
        widths = (5, 4, 8, 8, 8, 8, 8, 8)
        print(
            f"  {'model':<16}{'split':<13}"
            + "".join(f"{c:>{w}}" for c, w in zip(cols, widths, strict=True))
        )
        for key, res in result.results.items():
            if not res.available:
                print(f"  {key:<16}unavailable: {res.unavailable_reason}")
                continue
            for split, m in res.metrics.items():
                v = m.values
                mark = " *" if key == result.selected else ""
                cells = [
                    _fmt(v.get("brier")),
                    _fmt(v.get("brier_skill")),
                    _fmt(v.get("log_loss")),
                    _fmt(v.get("roc_auc")),
                    _fmt(v.get("pr_auc")),
                    _fmt(v.get("recall"), 2),
                ]
                print(
                    f"  {key:<16}{split:<13}{m.n:>5}{m.events:>4}"
                    + "".join(f"{c:>8}" for c in cells)
                    + mark
                )
        print(f"  published: {result.selected} - {result.selection_note}")
        check = heldout_check(result)
        if check.get("evaluated") and not check.get("beats_prevalence"):
            print(
                f"  WARNING: on the held-out years the published model does NOT beat the "
                f"prevalence "
                f"baseline (Brier skill {_fmt(check.get('brier_skill'))}, "
                f"{check.get('events')} events in {check.get('n')} rows)."
            )
        print(
            f"  final fit of {result.selected}: {result.final_n} rows, "
            f"{result.final_events} events, labels to as-of {result.final_last_as_of}"
        )
        for p in result.live:
            print(f"    current estimate {p.country} as of {p.as_of}: {p.probability:.1%}")
    if report.artifact_dir:
        print(f"\nartifacts: {report.artifact_dir}")
    print(f"{len(report.version_ids)} model versions stored")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="macropulse", description="MacroPulse AI backend CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    db = sub.add_parser("db", help="database migrations")
    db_sub = db.add_subparsers(dest="db_command", required=True)
    db_sub.add_parser("upgrade", help="migrate to head and sync the country/source registry")
    db_sub.add_parser("current", help="show current and head revisions")

    openapi = sub.add_parser("openapi", help="export the OpenAPI schema as JSON")
    openapi.add_argument("--out", default="packages/shared-types/openapi.json")

    serve = sub.add_parser("serve", help="run the API with uvicorn")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")

    sync = sub.add_parser("data-sync", help="fetch official series into the database")
    sync.add_argument("--source", action="append", choices=sorted(CONNECTORS), help="repeatable")
    sync.add_argument("--country", action="append", help="ISO alpha-2, repeatable")

    tr = sub.add_parser("train", help="walk-forward backtest and fit technical-recession models")
    tr.add_argument("--horizon", action="append", type=int, choices=[2, 4], help="repeatable")
    tr.add_argument("--seed", type=int, default=42)
    tr.add_argument("--no-artifacts", action="store_true", help="store metrics only")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "db":
        handler = _cmd_db_upgrade if args.db_command == "upgrade" else _cmd_db_current
        return handler(args)
    if args.command == "openapi":
        return _cmd_openapi(args)
    if args.command == "data-sync":
        return _cmd_data_sync(args)
    if args.command == "train":
        return _cmd_train(args)
    return _cmd_serve(args)


if __name__ == "__main__":
    sys.exit(main())
