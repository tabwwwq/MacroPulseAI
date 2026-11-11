"""Credential-free demo: export and import a snapshot of genuine stored official observations.

A snapshot holds, per native series, exactly what a live sync stored: the observations with their
status flags, the request URL, the source's update stamp and the original retrieval time. Loading
it runs the normal sync pipeline (validation, quality checks, ingestion runs) with a fetch function
that reads the snapshot instead of the network; the ingestion runs are marked `mode = "snapshot"`
with the capture time, so freshness and the UI banner say what the data is. No value is created.
"""

from __future__ import annotations

import gzip
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from macropulse_api.config import REPO_ROOT
from macropulse_api.db import as_utc
from macropulse_api.models import Observation
from macropulse_api.services.sync import SyncReport, run_sync
from macropulse_economics.connectors.base import (
    ConnectorError,
    FetchedObservation,
    FetchResult,
    SeriesRequest,
)
from macropulse_economics.connectors.http import Fetcher, make_client

FORMAT = "macropulse-snapshot/1"
DEFAULT_SNAPSHOT = REPO_ROOT / "data" / "demo" / "snapshot-2026-11-09.json.gz"


def export_snapshot(session: Session, path: Path) -> dict[str, Any]:
    """Write every stored native series to a gzipped JSON snapshot; return its header."""
    rows = session.scalars(
        select(Observation).order_by(Observation.series_id, Observation.period_start)
    ).all()
    if not rows:
        raise ValueError("No observations stored: run a live `macropulse data-sync` first.")
    by_series: dict[str, list[Observation]] = defaultdict(list)
    for r in rows:
        by_series[r.series_id].append(r)
    series = []
    for sid, obs in sorted(by_series.items()):
        latest = max(obs, key=lambda r: (as_utc(r.retrieved_at), r.period_start))
        retrieved = as_utc(latest.retrieved_at)
        series.append(
            {
                "series_id": sid,
                "source_id": latest.source_id,
                "dataset": latest.dataset,
                "series_key": latest.series_key,
                "geo": latest.geo,
                "url": latest.source_url,
                "retrieved_at": retrieved.isoformat() if retrieved else None,
                "source_updated_at": latest.source_updated_at,
                "observations": [[o.period, o.value, o.obs_status] for o in obs],
            }
        )
    stamps = [s["retrieved_at"] for s in series if s["retrieved_at"]]
    header = {
        "format": FORMAT,
        "captured_at": max(stamps) if stamps else None,
        "series_count": len(series),
        "observation_count": len(rows),
        "note": (
            "Genuine official observations as stored by a live MacroPulse sync, for an offline, "
            "credential-free demo. Not live data. Sources and terms: data/demo/README.md."
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({**header, "series": series}, separators=(",", ":"), ensure_ascii=False)
    with gzip.GzipFile(path, "wb", compresslevel=9, mtime=0) as fh:
        fh.write(payload.encode("utf-8"))
    return header


def read_snapshot(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rb") as fh:
        data: dict[str, Any] = json.loads(fh.read().decode("utf-8"))
    if data.get("format") != FORMAT:
        raise ValueError(f"{path} is not a {FORMAT} file")
    return data


def load_snapshot(
    factory: sessionmaker[Session], path: Path = DEFAULT_SNAPSHOT
) -> tuple[SyncReport, datetime]:
    """Import a snapshot through the normal sync pipeline, marked as snapshot data."""
    data = read_snapshot(path)
    captured = datetime.fromisoformat(data["captured_at"])
    by_id = {s["series_id"]: s for s in data["series"]}

    def snapshot_fetch(_fetcher: Fetcher, req: SeriesRequest) -> FetchResult:
        entry = by_id.get(req.series_id)
        if entry is None:
            raise ConnectorError(f"{req.series_id}: not in the demo snapshot")
        observations = [FetchedObservation(p, float(v), s) for p, v, s in entry["observations"]]
        return FetchResult(
            req,
            observations,
            entry["url"],
            datetime.fromisoformat(entry["retrieved_at"]),
            entry.get("source_updated_at"),
        )

    # The fetch function never touches the network; the client only satisfies the interface.
    with make_client() as client:
        report = run_sync(
            factory,
            Fetcher(client),
            fetch=snapshot_fetch,
            mode="snapshot",
            snapshot_taken_at=captured,
        )
    return report, captured
