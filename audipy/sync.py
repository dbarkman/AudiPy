"""Fetch the Audible library and store it in the local SQLite database."""

from __future__ import annotations

import html
import re
import sqlite3
from datetime import datetime, timezone

from audipy import audible_client
from audipy.config import Config
from audipy.db import connect, set_meta
from audipy.normalize import normalize_name, normalize_title, parse_sequence

# response_groups needed to capture contributors, series, media (covers), price, listening
# progress, genres and ratings.
LIBRARY_RESPONSE_GROUPS = (
    "series,contributors,product_desc,media,price,"
    "listening_status,is_finished,percent_complete,rating,category_ladders"
)
SUMMARY_CHARS = 1000


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


def _genres(item: dict) -> str | None:
    ladders = [
        " > ".join(step["name"] for step in (lad.get("ladder") or []) if step.get("name"))
        for lad in (item.get("category_ladders") or [])
    ]
    return "; ".join(dict.fromkeys(l for l in ladders if l)) or None


def _rating(item: dict) -> tuple[float | None, int | None]:
    overall = (item.get("rating") or {}).get("overall_distribution") or {}
    count = overall.get("num_ratings")
    avg = overall.get("average_rating")
    return (round(float(avg), 2) if avg else None, int(count) if count else None)


def _summary(item: dict) -> str | None:
    raw = item.get("merchandising_summary") or ""
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return " ".join(text.split())[:SUMMARY_CHARS] or None


def _progress(item: dict) -> dict:
    status = item.get("listening_status") or {}
    finished = item.get("is_finished", status.get("is_finished"))
    percent = item.get("percent_complete", status.get("percent_complete"))
    return {
        "is_finished": None if finished is None else int(bool(finished)),
        "percent_complete": percent,
        "time_left_sec": status.get("time_remaining_seconds"),
        "last_listened_at": status.get("finished_at_timestamp"),
    }


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
        **_progress(item),
        "genres": _genres(item),
        "rating_avg": _rating(item)[0],
        "rating_count": _rating(item)[1],
        "summary": _summary(item),
        "authors": authors,
        "narrators": narrators,
        "series": series,
    }


def _store_book(conn: sqlite3.Connection, book: dict, synced_at: str) -> None:
    conn.execute(
        """INSERT INTO books
           (asin, title, subtitle, title_norm, runtime_min, language,
            release_date, purchase_date, cover_url, synced_at,
            is_finished, percent_complete, time_left_sec, last_listened_at,
            genres, rating_avg, rating_count, summary)
           VALUES (:asin, :title, :subtitle, :title_norm, :runtime_min, :language,
                   :release_date, :purchase_date, :cover_url, :synced_at,
                   :is_finished, :percent_complete, :time_left_sec, :last_listened_at,
                   :genres, :rating_avg, :rating_count, :summary)""",
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
