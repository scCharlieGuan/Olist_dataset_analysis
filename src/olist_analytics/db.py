"""Small DB-API boundary. SQL assets contain one statement per file."""

from contextlib import contextmanager
from pathlib import Path

import pymysql

from .config import Settings


@contextmanager
def connect(settings: Settings):
    connection = pymysql.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        database=settings.database,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
        read_timeout=300,
        write_timeout=300,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION() AS version")
            version = cursor.fetchone()["version"]
            major, minor, patch = (int(x) for x in version.split("-")[0].split(".")[:3])
            if "mariadb" in version.lower() or (major, minor, patch) < (8, 0, 18):
                raise RuntimeError("MySQL 8.0.18+ required (recommended: MySQL 8.4 LTS)")
            cursor.execute(
                "SET SESSION sql_mode = "
                "'STRICT_ALL_TABLES,ONLY_FULL_GROUP_BY,NO_ZERO_DATE,"
                "NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'"
            )
            cursor.execute(
                "SET @start_date=%s, @end_date=%s, @min_orders=%s",
                (settings.start, settings.end, settings.min_orders),
            )
        yield connection
    finally:
        connection.close()


def fetch(connection, sql: str, params=None) -> list[dict]:
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return list(cursor.fetchall())


def execute_files(connection, paths: list[Path]) -> None:
    for path in paths:
        with connection.cursor() as cursor:
            cursor.execute(path.read_text(encoding="utf-8"))
