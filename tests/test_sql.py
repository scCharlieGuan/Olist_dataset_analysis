"""Parse MySQL assets and verify SQL semantics against a tiny DuckDB fixture.

This fallback executes TRANSLATED queries; it does not claim MySQL compatibility.
The separate opt-in MySQL integration test executes the original SQL unchanged.
"""

import unittest
from pathlib import Path

import duckdb
import sqlglot
from fixtures import fixture_rows

from olist_analytics.catalog import SOURCES
from olist_analytics.ingest import convert

ROOT = Path(__file__).resolve().parents[1]


def translate(sql):
    for key, literal in {
        "@start_date": "DATE '2017-01-01'",
        "@end_date": "DATE '2017-04-01'",
        "@min_orders": "1",
        "@bench_start": "DATE '2017-01-01'",
        "@bench_end": "DATE '2017-01-08'",
    }.items():
        sql = sql.replace(key, literal)
    return sqlglot.transpile(sql, read="mysql", write="duckdb")[0]


class SQLSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = duckdb.connect()
        rows = fixture_rows()
        for source in SOURCES:
            columns = ["raw_row_id BIGINT"] + [
                f'"{name}" {dtype.replace("DATETIME", "TIMESTAMP")}'
                for name, dtype in source.columns
            ]
            cls.db.execute(f"CREATE TABLE raw_{source.name} (" + ",".join(columns) + ")")
            for index, row in enumerate(rows[source.name], 1):
                values = [index] + [
                    convert(row.get(name, ""), dtype) for name, dtype in source.columns
                ]
                cls.db.execute(
                    f"INSERT INTO raw_{source.name} VALUES (" + ",".join(["?"] * len(values)) + ")",
                    values,
                )
        for path in sorted((ROOT / "sql").glob("2*.sql")):
            cls.db.execute(translate(path.read_text()))

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def rows(self, name):
        result = self.db.execute(translate((ROOT / "sql" / name).read_text()))
        columns = [x[0] for x in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]

    def test_every_sql_asset_parses_as_mysql(self):
        for path in sorted((ROOT / "sql").rglob("*.sql")):
            with self.subTest(file=path.name):
                self.assertEqual(len(sqlglot.parse(path.read_text(), read="mysql")), 1)

    def test_no_fanout_and_latest_review(self):
        result = self.db.execute("SELECT * FROM v_order_fact ORDER BY order_id")
        columns = [x[0] for x in result.description]
        facts = [dict(zip(columns, row)) for row in result.fetchall()]
        self.assertEqual(len(facts), 6)
        self.assertEqual(float(facts[0]["item_gmv"]), 150)
        self.assertEqual(float(facts[0]["payment_value"]), 165)
        self.assertEqual(int(facts[0]["review_score"]), 2)
        self.assertEqual(int(facts[0]["seller_count"]), 2)
        self.assertEqual(int(facts[1]["is_late"]), 0)  # same calendar day, 18 hours later
        self.assertEqual(int(facts[2]["delivery_eligible"]), 0)  # NULL promise

    def test_calendar_growth_and_aov(self):
        rows = self.rows("analysis/01_monthly_performance.sql")
        self.assertEqual([r["orders"] for r in rows], [3, 0, 1])
        self.assertEqual(float(rows[0]["item_gmv"]), 200)
        self.assertAlmostEqual(float(rows[0]["avg_order_value"]), 66.67)
        self.assertIsNone(rows[0]["gmv_mom"])
        self.assertEqual(float(rows[1]["gmv_mom"]), -1)
        self.assertIsNone(rows[2]["gmv_mom"])

    def test_review_denominators(self):
        rows = self.rows("analysis/08_delay_reviews.sql")
        self.assertEqual(rows[0]["eligible_orders"], 2)
        self.assertEqual(rows[0]["reviewed_orders"], 1)
        self.assertEqual(float(rows[0]["review_coverage"]), 0.5)
        self.assertEqual(float(rows[1]["bad_review_rate"]), 1)
        self.assertEqual(rows[1]["reviewed_orders"], 2)

    def test_all_business_queries_execute(self):
        for path in sorted((ROOT / "sql/analysis").glob("*.sql")):
            with self.subTest(file=path.name):
                self.rows("analysis/" + path.name)

    def test_quality_and_reconciliation(self):
        for file in ["quality/01_raw_contracts.sql", "quality/02_reconciliation.sql"]:
            self.assertFalse(
                [r for r in self.rows(file) if r["severity"] == "FAIL" and r["violations"]]
            )

    def test_duplicate_dimension_is_blocked(self):
        self.db.execute("INSERT INTO raw_customers SELECT * FROM raw_customers LIMIT 1")
        try:
            checks = self.rows("quality/01_raw_contracts.sql")
            self.assertTrue(
                any(
                    r["check_name"] == "customers_duplicate_key" and r["violations"] for r in checks
                )
            )
        finally:
            self.db.execute(
                "DELETE FROM raw_customers WHERE rowid IN (SELECT MAX(rowid) FROM raw_customers)"
            )


if __name__ == "__main__":
    unittest.main()
