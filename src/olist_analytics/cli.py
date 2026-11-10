"""Usage: conda run -n ml python -m olist_analytics --help"""

import argparse
from pathlib import Path

from .benchmark import benchmark
from .config import Settings
from .db import connect, execute_files
from .ingest import load_csvs
from .pipeline import analyze, build_views, quality, write_json
from .report import make_report


def main():
    parser = argparse.ArgumentParser(description="Olist MySQL analytics")
    parser.add_argument(
        "command",
        choices=["init", "import", "check", "build", "analyze", "report", "benchmark", "run"],
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Project root containing sql/ and .env; editable install recommended",
    )
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument(
        "--include-geo", action="store_true", help="Import optional geolocation CSV"
    )
    args = parser.parse_args()
    root = args.root.resolve()
    data_dir = (root / args.data_dir).resolve()
    output = (root / args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.command == "report":
        print(make_report(output))
        return
    settings = Settings.load(root)
    with connect(settings) as connection:
        if args.command in {"init", "run"}:
            execute_files(connection, sorted((root / "sql").glob("0*.sql")))
        if args.command in {"import", "run"}:
            files = load_csvs(connection, data_dir, args.include_geo)
            write_json(
                output / "import_manifest.json",
                {
                    "data_origin": "synthetic"
                    if (data_dir / "SYNTHETIC_DATA.txt").exists()
                    else "user_supplied_olist_csv",
                    "files": files,
                },
            )
        if args.command in {"build", "run"}:
            build_views(connection, root, output)
        if args.command == "check":
            quality(connection, root, output)
        if args.command in {"analyze", "run"}:
            analyze(connection, settings, output)
        if args.command == "benchmark":
            benchmark(connection, settings, output)
    if args.command == "run":
        print(make_report(output))
    else:
        print(f"Completed: {args.command}. Results: {output}")


if __name__ == "__main__":
    main()
