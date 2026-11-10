"""Rebuild a clearly synthetic HTML preview without requiring a MySQL server.

Runs the MySQL queries translated to DuckDB. For original SQL use test_mysql.py.
"""

import csv
import shutil
import tempfile
from datetime import date
from pathlib import Path

import test_sql

from olist_analytics.ingest import sha256
from olist_analytics.pipeline import write_json
from olist_analytics.report import make_report


def create_example():
    root = Path(__file__).resolve().parents[1]
    target = root / "examples/synthetic_report.html"
    target.parent.mkdir(exist_ok=True)
    engine = test_sql.SQLSemanticsTests
    engine.setUpClass()
    try:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            queries = []
            for path in sorted((root / "sql/analysis").glob("*.sql")):
                result = engine.db.execute(test_sql.translate(path.read_text()))
                columns = [x[0] for x in result.description]
                destination = output / f"{path.stem}.csv"
                with destination.open("w", encoding="utf-8-sig", newline="") as stream:
                    writer = csv.writer(stream)
                    writer.writerow(columns)
                    writer.writerows(result.fetchall())
                queries.append({"name": path.stem, "csv_sha256": sha256(destination)})
            checks = []
            for path in sorted((root / "sql/quality").glob("*.sql")):
                result = engine.db.execute(test_sql.translate(path.read_text()))
                names = [x[0] for x in result.description]
                checks.extend(dict(zip(names, row)) for row in result.fetchall())
            write_json(output / "quality.json", checks)
            write_json(
                output / "analysis_manifest.json",
                {
                    "generated_at_utc": "2026-11-03 (synthetic example)",
                    "start_inclusive": date(2017, 1, 1),
                    "end_exclusive": date(2017, 4, 1),
                    "min_orders": 1,
                    "import_manifest": {"data_origin": "synthetic"},
                    "execution_engine": "DuckDB via SQLGlot translation; NOT original MySQL",
                    "queries": queries,
                },
            )
            shutil.copyfile(make_report(output), target)
    finally:
        engine.tearDownClass()
    print(target)


if __name__ == "__main__":
    create_example()
