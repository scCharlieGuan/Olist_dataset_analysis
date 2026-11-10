"""Actual measurements only. A temporary experiment index is removed in finally."""

from datetime import timedelta
from statistics import median
from time import perf_counter

from .db import fetch
from .pipeline import write_json


def benchmark(connection, settings, output, repeats=7):
    # A narrow fixed 7-day cohort is deliberately more selective than the full analysis period.
    start = settings.start
    end = min(start + timedelta(days=7), settings.end)
    with connection.cursor() as cursor:
        cursor.execute("SET @bench_start=%s, @bench_end=%s", (start, end))
    index = "idx_benchmark_status_purchase"
    indexes = fetch(connection, "SHOW INDEX FROM raw_orders")
    if any(row["Key_name"] == index for row in indexes):
        raise RuntimeError(f"{index} already exists; choose a fresh benchmark database")
    paths = sorted((settings.root / "sql/optimization").glob("*.sql"))
    queries = {p.stem: p.read_text(encoding="utf-8") for p in paths}
    report = {
        "start": start,
        "end": end,
        "repeats": repeats,
        "server": fetch(connection, "SELECT VERSION() AS version")[0],
        "existing_indexes": indexes,
        "stages": [],
    }

    def measure(stage):
        plans, timings, values = {}, {key: [] for key in queries}, {}
        for key, sql in queries.items():
            values[key] = fetch(connection, sql)  # warm cache
            plans[key] = fetch(connection, "EXPLAIN ANALYZE " + sql)
        if values["01_baseline"] != values["02_optimized"]:
            raise RuntimeError("Benchmark queries returned different results")
        for iteration in range(repeats):
            pairs = list(queries.items())
            if iteration % 2:
                pairs.reverse()
            for key, sql in pairs:
                started = perf_counter()
                actual = fetch(connection, sql)
                timings[key].append((perf_counter() - started) * 1000)
                if actual != values[key]:
                    raise RuntimeError("Data changed during benchmark; use an idle database")
        report["stages"].append(
            {
                "stage": stage,
                "results": values,
                "plans": plans,
                "milliseconds": timings,
                "median_ms": {k: median(v) for k, v in timings.items()},
            }
        )

    measure("before_index")
    created = False
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE INDEX {index} ON raw_orders (order_status, order_purchase_timestamp)"
            )
            created = True
            cursor.execute("ANALYZE TABLE raw_orders")
            cursor.fetchall()
        measure("after_index")
        if report["stages"][0]["results"] != report["stages"][1]["results"]:
            raise RuntimeError("Data changed between benchmark stages")
    finally:
        if created:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP INDEX {index} ON raw_orders")
    report["note"] = "Warm-cache client wall time including network; no speedup is guaranteed."
    write_json(output / "benchmark.json", report)
    return report
