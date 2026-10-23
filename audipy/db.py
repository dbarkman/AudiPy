"""Local SQLite storage for the synced library and generated recommendations.

Single-user tool: no users, OAuth, or encryption tables — just the book data.
The database lives at ``~/.audipy/audipy.db`` (see Config) and is created on
demand. Contributors and series are stored in join tables keyed by a normalized
name so "top authors/narrators/series" queries group name variants together.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    asin          TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    subtitle      TEXT,
    title_norm    TEXT NOT NULL,
    runtime_min   INTEGER,
    language      TEXT,
    release_date  TEXT,
    purchase_date TEXT,
    cover_url     TEXT,
    synced_at     TEXT NOT NULL,
    is_finished      INTEGER,               -- 1 finished, 0 not
    percent_complete REAL,
    time_left_sec    INTEGER,
    last_listened_at TEXT,                  -- Audible's listening_status timestamp
    genres           TEXT,                  -- "A > B > C; D > E", from category ladders
    rating_avg       REAL,                  -- public overall rating, not David's own
    rating_count     INTEGER,
    summary          TEXT                   -- publisher's blurb, tags stripped
);

CREATE TABLE IF NOT EXISTS book_authors (
    book_asin   TEXT NOT NULL REFERENCES books(asin) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    name_norm   TEXT NOT NULL,
    author_asin TEXT,
    PRIMARY KEY (book_asin, name_norm)
);

CREATE TABLE IF NOT EXISTS book_narrators (
    book_asin     TEXT NOT NULL REFERENCES books(asin) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    name_norm     TEXT NOT NULL,
    narrator_asin TEXT,
    PRIMARY KEY (book_asin, name_norm)
);

CREATE TABLE IF NOT EXISTS book_series (
    book_asin     TEXT NOT NULL REFERENCES books(asin) ON DELETE CASCADE,
    series_title  TEXT NOT NULL,
    series_norm   TEXT NOT NULL,
    series_asin   TEXT,
    sequence      TEXT,
    sequence_num  REAL,
    PRIMARY KEY (book_asin, series_norm)
);

CREATE TABLE IF NOT EXISTS recommendations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    rec_type        TEXT NOT NULL,          -- 'series' | 'author' | 'narrator'
    source_name     TEXT NOT NULL,          -- the series/author/narrator that triggered it
    source_norm     TEXT NOT NULL,
    asin            TEXT NOT NULL,
    title           TEXT NOT NULL,
    subtitle        TEXT,
    series_title    TEXT,
    sequence        TEXT,
    sequence_num    REAL,
    author_names    TEXT,
    narrator_names  TEXT,
    member_price    REAL,
    credit_price    REAL,
    purchase_method TEXT,                   -- 'cash' | 'credit'
    confidence      REAL,
    language        TEXT,
    cover_url       TEXT,
    generated_at    TEXT NOT NULL,
    release_date    TEXT,
    UNIQUE (rec_type, asin, source_norm)
);

CREATE INDEX IF NOT EXISTS idx_book_authors_norm   ON book_authors(name_norm);
CREATE INDEX IF NOT EXISTS idx_book_narrators_norm ON book_narrators(name_norm);
CREATE INDEX IF NOT EXISTS idx_book_series_norm    ON book_series(series_norm);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


# Columns added after the first release. CREATE TABLE IF NOT EXISTS leaves an existing table alone,
# so an old database gets them added here instead. Additive only: nothing is dropped or renamed.
ADDED_COLUMNS = {
    "books": {
        "is_finished": "INTEGER", "percent_complete": "REAL", "time_left_sec": "INTEGER",
        "last_listened_at": "TEXT", "genres": "TEXT", "rating_avg": "REAL",
        "rating_count": "INTEGER", "summary": "TEXT",
    },
    "recommendations": {"release_date": "TEXT"},
}


def _add_missing_columns(conn: sqlite3.Connection) -> None:
    for table, columns in ADDED_COLUMNS.items():
        have = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
        for name, kind in columns.items():
            if name not in have:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {kind}")


@contextmanager
def connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Open the SQLite database, ensuring the schema exists.

    Commits on clean exit, rolls back on exception, always closes.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.executescript(SCHEMA)
        _add_missing_columns(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None
