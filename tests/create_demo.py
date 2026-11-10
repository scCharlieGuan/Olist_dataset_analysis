"""Run from project root: python tests/create_demo.py. Does not touch MySQL."""

from pathlib import Path

from fixtures import write_fixture

if __name__ == "__main__":
    path = Path(__file__).resolve().parents[1] / "data/demo"
    write_fixture(path)
    print(f"Synthetic data only: {path}")
