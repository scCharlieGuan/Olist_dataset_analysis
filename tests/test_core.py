import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from fixtures import write_fixture

from olist_analytics.catalog import SOURCES, schema_sql
from olist_analytics.ingest import convert, load_csvs


class FakeCursor:
    def __init__(self):
        self.counts = {}
        self.table = ""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql):
        self.table = sql.split("FROM ")[1]

    def fetchone(self):
        return {"n": self.counts.get(self.table, 0)}

    def executemany(self, sql, batch):
        self.table = sql.split()[2]
        self.counts[self.table] = self.counts.get(self.table, 0) + len(batch)


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class IngestionTests(unittest.TestCase):
    def test_exact_types_and_nulls(self):
        self.assertIsNone(convert("", "DATETIME"))
        self.assertEqual(convert("01234", "VARCHAR(5)"), "01234")
        self.assertEqual(convert("100.25", "DECIMAL(14,2)"), Decimal("100.25"))
        self.assertEqual(convert("40.0", "INT"), 40)
        self.assertEqual(convert("-23.123456789012345", "DOUBLE"), -23.123456789012345)
        self.assertEqual(convert("2017-01-01 00:00:00", "DATETIME"), datetime(2017, 1, 1))
        self.assertEqual(convert("a, b\nc", "TEXT"), "a, b\nc")

    def test_reject_lossy_values(self):
        for value, dtype in [
            ("1.001", "DECIMAL(14,2)"),
            ("NaN", "DECIMAL(14,2)"),
            ("1e999", "DECIMAL(14,2)"),
            ("1.5", "INT"),
            ("2147483648", "INT"),
            ("0000-00-00", "DATETIME"),
            ("2017-02-30 00:00:00", "DATETIME"),
            ("123456", "VARCHAR(5)"),
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                convert(value, dtype)

    def test_atomic_import_and_refusal_to_append(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_fixture(directory)
            connection = FakeConnection()
            manifest = load_csvs(connection, directory, batch_size=2)
            self.assertTrue(connection.committed)
            self.assertEqual(
                next(x for x in manifest if x["file"] == "olist_orders_dataset.csv")["rows"], 6
            )
            with self.assertRaises(RuntimeError):
                load_csvs(connection, directory)
            self.assertTrue(connection.rolled_back)

    def test_bad_later_file_rolls_back(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_fixture(directory)
            path = directory / "olist_order_reviews_dataset.csv"
            path.write_text("unexpected,header\n1,2\n", encoding="utf-8")
            connection = FakeConnection()
            with self.assertRaises(ValueError):
                load_csvs(connection, directory)
            self.assertFalse(connection.committed)
            self.assertTrue(connection.rolled_back)

    def test_checked_in_schema_matches_catalog(self):
        root = Path(__file__).resolve().parents[1]
        for index, source in enumerate(SOURCES, 1):
            self.assertEqual(
                (root / f"sql/{index:02}_raw_{source.name}.sql").read_text(), schema_sql(source)
            )


if __name__ == "__main__":
    unittest.main()
