#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg import sql
from psycopg.types.json import Json


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = ROOT_DIR / ".env"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a historical SQLite Wikibook backup into the current PostgreSQL database."
    )
    parser.add_argument("sqlite_path", help="Path to the source SQLite .db file")
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Path to the env file containing DATABASE_URL (default: %(default)s)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Rows inserted per batch (default: %(default)s)",
    )
    return parser.parse_args()


def load_database_url(env_file: str) -> str:
    load_dotenv(env_file, override=False)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(f"DATABASE_URL is not configured in {env_file}")
    if database_url.startswith("postgresql+psycopg://"):
        database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def get_sqlite_tables(conn: sqlite3.Connection) -> set[str]:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cur.fetchall()}


def get_postgres_tables(conn: psycopg.Connection[Any]) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
        return [row[0] for row in cur.fetchall()]


def get_postgres_columns(conn: psycopg.Connection[Any], table: str) -> list[dict[str, str]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name, data_type, udt_name, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        return [
            {"name": row[0], "data_type": row[1], "udt_name": row[2], "max_length": row[3]}
            for row in cur.fetchall()
        ]


def get_sqlite_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cur = conn.execute(f'PRAGMA table_info("{table}")')
    return [row[1] for row in cur.fetchall()]


def get_table_dependencies(conn: psycopg.Connection[Any], tables: set[str]) -> dict[str, set[str]]:
    dependencies: dict[str, set[str]] = {table: set() for table in tables}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                tc.table_name AS child_table,
                ccu.table_name AS parent_table
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
               AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
               AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
            """
        )
        for child_table, parent_table in cur.fetchall():
            if child_table in tables and parent_table in tables and child_table != parent_table:
                dependencies[child_table].add(parent_table)
    return dependencies


def topo_sort_tables(dependencies: dict[str, set[str]]) -> list[str]:
    incoming = {table: set(parents) for table, parents in dependencies.items()}
    outgoing: dict[str, set[str]] = defaultdict(set)
    for table, parents in dependencies.items():
        for parent in parents:
            outgoing[parent].add(table)

    ready = deque(sorted(table for table, parents in incoming.items() if not parents))
    ordered: list[str] = []

    while ready:
        table = ready.popleft()
        ordered.append(table)
        for child in sorted(outgoing.get(table, set())):
            incoming[child].discard(table)
            if not incoming[child]:
                ready.append(child)

    if len(ordered) != len(dependencies):
        remaining = sorted(set(dependencies) - set(ordered))
        ordered.extend(remaining)

    return ordered


def transform_value(value: Any, column_type: dict[str, str]) -> Any:
    if value is None:
        return None

    data_type = column_type["data_type"]
    udt_name = column_type["udt_name"]

    if data_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}

    if data_type in {"json", "jsonb"} or udt_name in {"json", "jsonb"}:
        if isinstance(value, (dict, list, int, float, bool)):
            return Json(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            return Json(json.loads(stripped))

    return value


def truncate_all_public_tables(conn: psycopg.Connection[Any], tables: list[str]) -> None:
    if not tables:
        return
    with conn.cursor() as cur:
        identifiers = sql.SQL(", ").join(sql.Identifier(table) for table in tables)
        cur.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(identifiers))


def import_table(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg.Connection[Any],
    table: str,
    columns: list[dict[str, str]],
    chunk_size: int,
) -> tuple[int, int]:
    column_names = [column["name"] for column in columns]
    sqlite_query = sql.SQL("SELECT {} FROM {}").format(
        sql.SQL(", ").join(sql.Identifier(name) for name in column_names),
        sql.Identifier(table),
    ).as_string(pg_conn)

    sqlite_cur = sqlite_conn.execute(sqlite_query)

    insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(name) for name in column_names),
        sql.SQL(", ").join(sql.Placeholder() for _ in column_names),
    )

    inserted = 0
    skipped = 0
    while True:
        rows = sqlite_cur.fetchmany(chunk_size)
        if not rows:
            break

        payload = []
        for row in rows:
            payload.append(
                [transform_value(value, column) for value, column in zip(row, columns)]
            )

        try:
            with pg_conn.transaction():
                with pg_conn.cursor() as cur:
                    cur.executemany(insert_sql, payload)
            inserted += len(payload)
        except Exception as exc:
            for row_values in payload:
                try:
                    with pg_conn.transaction():
                        with pg_conn.cursor() as cur:
                            cur.execute(insert_sql, row_values)
                    inserted += 1
                except Exception as row_exc:
                    details = []
                    for column, value in zip(columns, row_values):
                        rendered = repr(value)
                        if len(rendered) > 120:
                            rendered = rendered[:117] + "..."
                        details.append(f"{column['name']}={rendered}")
                    skipped += 1
                    print(
                        f"[skip] table={table} reason={type(row_exc).__name__}: {row_exc} row={', '.join(details)}",
                        file=sys.stderr,
                    )

    return inserted, skipped


def reset_sequences(conn: psycopg.Connection[Any], tables: list[str]) -> None:
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                  AND column_default LIKE 'nextval%%'
                ORDER BY ordinal_position
                """,
                (table,),
            )
            sequence_columns = [row[0] for row in cur.fetchall()]
            for column_name in sequence_columns:
                cur.execute("SELECT pg_get_serial_sequence(%s, %s)", (f"public.{table}", column_name))
                sequence_name = cur.fetchone()[0]
                if not sequence_name:
                    continue
                cur.execute(
                    sql.SQL(
                        "SELECT setval(%s, COALESCE((SELECT MAX({column}) FROM {table}), 1), "
                        "COALESCE((SELECT MAX({column}) FROM {table}) IS NOT NULL, FALSE))"
                    ).format(
                        column=sql.Identifier(column_name),
                        table=sql.Identifier(table),
                    ),
                    (sequence_name,),
                )


def maybe_widen_varchar_columns(
    sqlite_conn: sqlite3.Connection,
    pg_conn: psycopg.Connection[Any],
    table_columns: dict[str, list[dict[str, str]]],
) -> None:
    with pg_conn.cursor() as cur:
        for table, columns in table_columns.items():
            for column in columns:
                max_length = column.get("max_length")
                if column["data_type"] != "character varying" or not max_length:
                    continue

                sqlite_cur = sqlite_conn.execute(
                    f'SELECT MAX(LENGTH(COALESCE("{column["name"]}", ""))) FROM "{table}"'
                )
                source_max = sqlite_cur.fetchone()[0] or 0
                if source_max <= max_length:
                    continue

                cur.execute(
                    sql.SQL("ALTER TABLE {} ALTER COLUMN {} TYPE VARCHAR({})").format(
                        sql.Identifier(table),
                        sql.Identifier(column["name"]),
                        sql.SQL(str(source_max)),
                    )
                )


def main() -> None:
    args = parse_args()
    sqlite_path = Path(args.sqlite_path).expanduser().resolve()
    if not sqlite_path.is_file():
        raise FileNotFoundError(f"SQLite backup not found: {sqlite_path}")

    database_url = load_database_url(args.env_file)

    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg.connect(database_url)
    pg_conn.autocommit = False

    try:
        sqlite_tables = get_sqlite_tables(sqlite_conn)
        pg_tables = get_postgres_tables(pg_conn)
        common_tables = set(sqlite_tables).intersection(pg_tables)
        if not common_tables:
            raise RuntimeError("No common tables were found between the SQLite backup and PostgreSQL schema")

        dependencies = get_table_dependencies(pg_conn, common_tables)
        ordered_tables = topo_sort_tables(dependencies)

        table_columns: dict[str, list[dict[str, str]]] = {}
        imported_counts: dict[str, int] = {}
        skipped_counts: dict[str, int] = {}

        for table in ordered_tables:
            sqlite_columns = set(get_sqlite_columns(sqlite_conn, table))
            postgres_columns = get_postgres_columns(pg_conn, table)
            shared_columns = [column for column in postgres_columns if column["name"] in sqlite_columns]
            if shared_columns:
                table_columns[table] = shared_columns

        maybe_widen_varchar_columns(sqlite_conn, pg_conn, table_columns)
        truncate_all_public_tables(pg_conn, pg_tables)

        for table in ordered_tables:
            columns = table_columns.get(table)
            if not columns:
                imported_counts[table] = 0
                skipped_counts[table] = 0
                continue
            imported_counts[table], skipped_counts[table] = import_table(
                sqlite_conn, pg_conn, table, columns, args.chunk_size
            )

        reset_sequences(pg_conn, pg_tables)
        pg_conn.commit()

        print(f"Imported SQLite backup: {sqlite_path}")
        for table in ordered_tables:
            inserted = imported_counts.get(table, 0)
            skipped = skipped_counts.get(table, 0)
            if skipped:
                print(f"{table}: inserted={inserted}, skipped={skipped}")
            else:
                print(f"{table}: inserted={inserted}")
    except Exception:
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    main()
