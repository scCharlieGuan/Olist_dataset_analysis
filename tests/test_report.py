import csv
import tempfile
import unittest
from pathlib import Path

from olist_analytics.ingest import sha256
from olist_analytics.pipeline import write_json
from olist_analytics.report import LABELS, make_report


class ReportTests(unittest.TestCase):
    def fixture(self, output):
        queries = []
        for name in LABELS:
            path = output / f"{name}.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["category"])
                if name == "03_category_contribution":
                    writer.writerow(["<script>unsafe</script>"])
            queries.append({"name": name, "csv_sha256": sha256(path)})
        write_json(
            output / "analysis_manifest.json",
            {
                "start_inclusive": "2017-01-01",
                "end_exclusive": "2017-04-01",
                "generated_at_utc": "synthetic",
                "min_orders": 1,
                "import_manifest": {"data_origin": "synthetic"},
                "queries": queries,
            },
        )

    def test_synthetic_label_and_html_escaping(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            self.fixture(output)
            text = make_report(output).read_text()
            self.assertIn("合成样例验证", text)
            self.assertIn("&lt;script&gt;unsafe&lt;/script&gt;", text)
            self.assertNotIn("<script>unsafe</script>", text)

    def test_modified_csv_blocks_report(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            self.fixture(output)
            (output / "01_monthly_performance.csv").write_text("changed")
            with self.assertRaises(RuntimeError):
                make_report(output)
