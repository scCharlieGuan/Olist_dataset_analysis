"""Opt-in original-MySQL integration. Requires an EMPTY dedicated database ending _test.

RUN_MYSQL_TESTS=1 python -m unittest discover -s tests -v
This test loads fixture rows and deletes those rows afterwards; it never drops tables.
"""

import os
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

from fixtures import write_fixture

from olist_analytics.benchmark import benchmark
from olist_analytics.catalog import SOURCES
from olist_analytics.config import Settings
from olist_analytics.db import connect, execute_files, fetch
from olist_analytics.ingest import load_csvs
from olist_analytics.pipeline import analyze, build_views
from olist_analytics.report import make_report

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    os.getenv("RUN_MYSQL_TESTS") == "1", "Opt-in: dedicated MySQL test DB required"
)
class MySQLIntegrationTest(unittest.TestCase):
    def test_end_to_end_original_mysql(self):
        settings = Settings.load(ROOT)
        if not settings.database.endswith("_test"):
            self.fail("Refusing to modify a database whose name does not end in _test")
        settings = replace(settings, start=date(2017, 1, 1), end=date(2017, 4, 1), min_orders=1)
        with connect(settings) as connection, tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            execute_files(connection, sorted((ROOT / "sql").glob("0*.sql")))
            for source in SOURCES:
                self.assertEqual(
                    fetch(connection, f"SELECT COUNT(*) AS n FROM raw_{source.name}")[0]["n"],
                    0,
                    "Test database must be empty",
                )
            write_fixture(directory)
            try:
                load_csvs(connection, directory)
                build_views(connection, ROOT, directory)
                facts = fetch(connection, "SELECT * FROM v_order_fact ORDER BY order_id")
                self.assertEqual(len(facts), 6)
                self.assertEqual(float(facts[0]["item_gmv"]), 150)
                self.assertEqual(float(facts[0]["payment_value"]), 165)
                self.assertEqual(facts[0]["review_score"], 2)
                self.assertEqual(facts[1]["is_late"], 0)
                monthly = fetch(
                    connection, (ROOT / "sql/analysis/01_monthly_performance.sql").read_text()
                )
                self.assertEqual([r["orders"] for r in monthly], [3, 0, 1])
                analyze(connection, settings, directory)
                self.assertTrue(make_report(directory).is_file())
                result = benchmark(connection, settings, directory, repeats=2)
                self.assertEqual(len(result["stages"]), 2)
                with self.assertRaises(RuntimeError):
                    load_csvs(connection, directory)
            finally:
                connection.rollback()
                with connection.cursor() as cursor:
                    for source in reversed(SOURCES):
                        cursor.execute(f"DELETE FROM raw_{source.name}")
                connection.commit()
