"""Streaming CSV ingestion: strict types, parameterized inserts, all-or-nothing data load."""

import csv
import hashlib
import math
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .catalog import SOURCES


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def convert(value: str, dtype: str):
    # Empty CSV cells represent SQL NULL. Review text is otherwise preserved verbatim.
    if value == "":
        return None
    if dtype == "DATETIME":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", value):
            raise ValueError("Expected YYYY-MM-DD HH:MM:SS")
        result = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        if result.year < 1000:
            raise ValueError("MySQL DATETIME requires year >= 1000")
        return result
    if dtype == "INT":
        # Olist product measurements may serialize integers as e.g. '40.0'.
        if not re.fullmatch(r"-?\d+(?:\.0+)?", value):
            raise ValueError("Expected an integer-valued number")
        number = Decimal(value)
        if not -(2**31) <= number < 2**31:
            raise ValueError("INT overflow")
        result = int(number)
        if not -(2**31) <= result < 2**31:
            raise ValueError("INT overflow")
        return result
    if dtype == "DOUBLE":
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("Expected finite coordinate")
        return result
    if dtype.startswith("DECIMAL"):
        precision, scale = map(int, re.findall(r"\d+", dtype))
        try:
            result = Decimal(value)
            if (
                not result.is_finite()
                or abs(result) >= Decimal(10) ** (precision - scale)
                or result != result.quantize(Decimal(10) ** -scale)
            ):
                raise ValueError("DECIMAL would round or overflow")
            return result
        except InvalidOperation as error:
            raise ValueError("Invalid decimal") from error
    if dtype != "TEXT":
        limit = int(re.search(r"\d+", dtype).group())
        if len(value) > limit:
            raise ValueError("Text exceeds source contract")
    return value


def load_csvs(connection, data_dir: Path, include_geo: bool = False, batch_size: int = 1000):
    sources = [s for s in SOURCES if not s.optional or include_geo]
    missing = [s.filename for s in sources if not (data_dir / s.filename).is_file()]
    if missing:
        raise FileNotFoundError("Missing CSVs: " + ", ".join(missing))
    manifest = []
    try:
        with connection.cursor() as cursor:
            # Refuse append/reload even when the previous optional geo table is populated.
            for source in SOURCES:
                cursor.execute(f"SELECT COUNT(*) AS n FROM raw_{source.name}")
                if cursor.fetchone()["n"]:
                    raise RuntimeError("Import requires empty raw tables; use a fresh database")
            for source in sources:
                path = data_dir / source.filename
                before = sha256(path)
                names = [name for name, _ in source.columns]
                statement = (
                    f"INSERT INTO raw_{source.name} ("
                    + ",".join(f"`{name}`" for name in names)
                    + ") VALUES ("
                    + ",".join(["%s"] * len(names))
                    + ")"
                )
                count, batch = 0, []
                with path.open(encoding="utf-8-sig", newline="") as stream:
                    reader = csv.DictReader(stream)
                    if reader.fieldnames != names:
                        raise ValueError(f"{path.name}: unexpected CSV header; expected {names}")
                    for line, row in enumerate(reader, start=2):
                        try:
                            if None in row or any(v is None for v in row.values()):
                                raise ValueError("Wrong number of CSV fields")
                            batch.append(
                                tuple(convert(row[name], dtype) for name, dtype in source.columns)
                            )
                        except ValueError as error:
                            raise ValueError(f"{path.name} record {line}: {error}") from error
                        count += 1
                        if len(batch) >= batch_size:
                            cursor.executemany(statement, batch)
                            batch.clear()
                    if batch:
                        cursor.executemany(statement, batch)
                if sha256(path) != before:
                    raise RuntimeError(f"{path.name} changed during import")
                cursor.execute(f"SELECT COUNT(*) AS n FROM raw_{source.name}")
                if cursor.fetchone()["n"] != count or (not source.optional and count == 0):
                    raise RuntimeError(f"{path.name}: empty source or row count mismatch")
                manifest.append({"file": path.name, "sha256": before, "rows": count})
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return manifest
