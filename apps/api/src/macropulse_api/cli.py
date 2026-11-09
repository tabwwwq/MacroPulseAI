"""`macropulse` command-line interface (database, OpenAPI export, dev server)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import uvicorn

from macropulse_api.config import REPO_ROOT, get_settings
from macropulse_api.db import build_engine, build_sessionmaker
from macropulse_api.main import create_app
from macropulse_api.migrate import current_revision, head_revision, upgrade
from macropulse_api.services.registry_sync import sync_registry


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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "db":
        handler = _cmd_db_upgrade if args.db_command == "upgrade" else _cmd_db_current
        return handler(args)
    if args.command == "openapi":
        return _cmd_openapi(args)
    return _cmd_serve(args)


if __name__ == "__main__":
    sys.exit(main())
