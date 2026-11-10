"""Ordered SQL execution, quality gates, and auditable result exports."""

import csv
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from .db import execute_files, fetch
from .ingest import sha256


def json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=json_default) + "\n",
        encoding="utf-8",
    )


def quality(connection, root: Path, output: Path, include_fact: bool = True) -> list[dict]:
    paths = sorted((root / "sql/quality").glob("*.sql"))
    if not include_fact:
        paths = [p for p in paths if p.name.startswith("01_")]
    rows = [row for path in paths for row in fetch(connection, path.read_text(encoding="utf-8"))]
    write_json(output / "quality.json", rows)
    failures = [r["check_name"] for r in rows if r["severity"] == "FAIL" and r["violations"]]
    if failures:
        raise RuntimeError("Data quality gate failed: " + ", ".join(failures))
    return rows


def build_views(connection, root: Path, output: Path) -> None:
    quality(connection, root, output, include_fact=False)
    execute_files(connection, sorted((root / "sql").glob("2*.sql")))
    quality(connection, root, output)


def analyze(connection, settings, output: Path) -> None:
    # A standalone analyze also rechecks DQ, preventing use of stale unsafe joins.
    # Invalidate the previous successful export before replacing any result files.
    (output / "analysis_manifest.json").unlink(missing_ok=True)
    quality(connection, settings.root, output)
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "database": settings.database,
        "start_inclusive": settings.start,
        "end_exclusive": settings.end,
        "min_orders": settings.min_orders,
        "server_version": fetch(connection, "SELECT VERSION() AS version")[0]["version"],
        "queries": [],
        "quality_sha256": sha256(output / "quality.json"),
    }
    import_path = output / "import_manifest.json"
    if import_path.exists():
        metadata["import_manifest"] = json.loads(import_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    # Read-only snapshot makes all report tables consistent within this export.
    connection.rollback()
    with connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        cursor.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY")
    try:
        for path in sorted((settings.root / "sql/analysis").glob("*.sql")):
            with connection.cursor() as cursor:
                cursor.execute(path.read_text(encoding="utf-8"))
                rows = list(cursor.fetchall())
                columns = [d[0] for d in cursor.description]
            destination = output / f"{path.stem}.csv"
            with destination.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
            metadata["queries"].append(
                {
                    "name": path.stem,
                    "rows": len(rows),
                    "sql_sha256": sha256(path),
                    "csv_sha256": sha256(destination),
                }
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    write_json(output / "analysis_manifest.json", metadata)
