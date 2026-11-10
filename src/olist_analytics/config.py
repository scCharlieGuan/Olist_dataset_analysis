"""Central configuration; .env never overrides explicitly exported variables."""

import os
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    user: str
    password: str = field(repr=False)
    database: str
    start: date
    end: date
    min_orders: int
    root: Path

    @classmethod
    def load(cls, root: Path) -> "Settings":
        load_dotenv(root / ".env", override=False)
        database = os.getenv("MYSQL_DATABASE", "olist_analytics")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", database):
            raise ValueError("MYSQL_DATABASE must be a simple ASCII identifier")
        start = date.fromisoformat(os.getenv("ANALYSIS_START", "2017-01-01"))
        end = date.fromisoformat(os.getenv("ANALYSIS_END", "2018-09-01"))
        if start >= end or start.day != 1 or end.day != 1:
            raise ValueError("Analysis boundaries must be ascending first-of-month dates")
        if (end.year - start.year) * 12 + end.month - start.month > 1000:
            raise ValueError("Analysis range exceeds the MySQL recursive CTE limit")
        minimum = int(os.getenv("MIN_ORDERS", "30"))
        if minimum < 1:
            raise ValueError("MIN_ORDERS must be positive")
        return cls(
            os.getenv("MYSQL_HOST", "127.0.0.1"),
            int(os.getenv("MYSQL_PORT", "3306")),
            os.getenv("MYSQL_USER", "olist"),
            os.getenv("MYSQL_PASSWORD", ""),
            database,
            start,
            end,
            minimum,
            root,
        )
