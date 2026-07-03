"""Fetch the Audible library and store it in the local SQLite database."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from audipy import audible_client
from audipy.config import Config
from audipy.db import connect, set_meta
from audipy.normalize import normalize_name, normalize_title, parse_sequence

# response_groups needed to capture contributors, series, media (covers) and price.
LIBRARY_RESPONSE_GROUPS = "series,contributors,product_desc,media,price"


def _largest_cover(product_images: dict | None) -> str | None:
    """Pick the highest-resolution cover URL from a product_images map."""
    if not isinstance(product_images, dict) or not product_images:
        return None
    # Keys are pixel sizes as strings ("500", "1024", …); take the biggest.
    try:
        best = max(product_images, key=lambda k: int(k))
    except (ValueError, TypeError):
        best = next(iter(product_images))
    return product_images.get(best)


def parse_book(item: dict) -> dict | None:
    """Convert a raw library item into structured book + contributor rows.

    Returns None for items without an ASIN (nothing we can key on).
    """
    asin = item.get("asin")
    if not asin:
        return None

    title = item.get("title") or ""
    authors = [
        {"name": a["name"], "name_norm": normalize_name(a["name"]), "asin": a.get("asin")}
        for a in (item.get("authors") or [])
        if a.get("name")
    ]
    narrators = [
        {"name": n["name"], "name_norm": normalize_name(n["name"]), "asin": n.get("asin")}
        for n in (item.get("narrators") or [])
        if n.get("name")
    ]
    series = [
        {
            "title": s["title"],
            "norm": normalize_name(s["title"]),
            "asin": s.get("asin"),
            "sequence": str(s["sequence"]) if s.get("sequence") is not None else None,
            "sequence_num": parse_sequence(s.get("sequence")),
        }
        for s in (item.get("series") or [])
        if s.get("title")
    ]

    return {
        "asin": asin,
        "title": title,
        "subtitle": item.get("subtitle"),
        "title_norm": normalize_title(title),
        "runtime_min": item.get("runtime_length_min"),
        "language": (item.get("language") or "").lower() or None,
        "release_date": item.get("release_date") or item.get("issue_date"),
        "purchase_date": item.get("purchase_date"),
        "cover_url": _largest_cover(item.get("product_images")),
        "authors": authors,
        "narrators": narrators,
        "series": series,
    }


def _store_book(conn: sqlite3.Connection, book: dict, synced_at: str) -> None:
    conn.execute(
        """INSERT INTO books
           (asin, title, subtitle, title_norm, runtime_min, language,
            release_date, purchase_date, cover_url, synced_at)
           VALUES (:asin, :title, :subtitle, :title_norm, :runtime_min, :language,
                   :release_date, :purchase_date, :cover_url, :synced_at)""",
        {**book, "synced_at": synced_at},
    )
    conn.executemany(
        "INSERT OR IGNORE INTO book_authors(book_asin, name, name_norm, author_asin)"
        " VALUES (?, ?, ?, ?)",
        [(book["asin"], a["name"], a["name_norm"], a["asin"]) for a in book["authors"]],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO book_narrators(book_asin, name, name_norm, narrator_asin)"
        " VALUES (?, ?, ?, ?)",
        [(book["asin"], n["name"], n["name_norm"], n["asin"]) for n in book["narrators"]],
    )
    conn.executemany(
        "INSERT OR IGNORE INTO book_series"
        "(book_asin, series_title, series_norm, series_asin, sequence, sequence_num)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        [
            (book["asin"], s["title"], s["norm"], s["asin"], s["sequence"], s["sequence_num"])
            for s in book["series"]
        ],
    )


def sync_library(config: Config) -> int:
    """Fetch the entire library and replace the local copy. Returns book count.

    A full replace keeps things simple and correct: removed/returned books
    disappear, and re-runs stay idempotent.
    """
    synced_at = datetime.now(timezone.utc).isoformat()
    count = 0
    with connect(config.db_file) as conn:
        conn.execute("DELETE FROM books")  # cascades to join tables
        for item in audible_client.iter_library_items(config, LIBRARY_RESPONSE_GROUPS):
            book = parse_book(item)
            if book is None:
                continue
            _store_book(conn, book, synced_at)
            count += 1
        set_meta(conn, "last_sync", synced_at)
        set_meta(conn, "book_count", str(count))
    return count
