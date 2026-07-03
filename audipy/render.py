"""Render recommendations to the terminal and to plain-text report files."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path

from rich.console import Console

from audipy.config import Config
from audipy.db import connect, get_meta

# Display metadata per recommendation type, in priority order.
TYPES = [
    ("series", "📚 Missing books in your series", "the next books in series you own"),
    ("author", "✍️  More by your authors", "more books by authors you read"),
    ("narrator", "🎧 Discover via your narrators", "books read by narrators you trust"),
]

REPORT_FILES = {
    "series": "missing_books_in_my_series.txt",
    "author": "missing_books_by_my_authors.txt",
    "narrator": "missing_books_by_my_narrators.txt",
}


def _order_clause(rec_type: str) -> str:
    if rec_type == "series":
        # Continuations in reading order; unnumbered last.
        return "source_name, sequence_num IS NULL, sequence_num, title"
    # Shopping lists: cheapest first so cash deals rise to the top.
    return "source_name, member_price IS NULL, member_price, title"


def _grouped(conn: sqlite3.Connection, rec_type: str,
             cash_only: bool) -> dict[str, list[sqlite3.Row]]:
    where = "rec_type = ?"
    params: list = [rec_type]
    if cash_only:
        where += " AND purchase_method = ?"
        params.append("cash")
    sql = f"SELECT * FROM recommendations WHERE {where} ORDER BY {_order_clause(rec_type)}"
    grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in conn.execute(sql, params):
        grouped[row["source_name"]].append(row)
    return grouped


def _price_tag(row: sqlite3.Row) -> str:
    price = row["member_price"]
    if price is None:
        return "🎫 credit (price n/a)"
    money = f"${price:.2f}"
    return f"💰 {money} cash" if row["purchase_method"] == "cash" else f"🎫 {money} credit"


def _book_label(rec_type: str, row: sqlite3.Row) -> str:
    if rec_type == "series" and row["sequence"]:
        return f"#{row['sequence']} {row['title']}"
    return row["title"]


def print_report(config: Config, console: Console, rec_type: str = "all",
                 cash_only: bool = False) -> None:
    """Print recommendations to the terminal, grouped by source."""
    wanted = [t for t in TYPES if rec_type in ("all", t[0])]
    with connect(config.db_file) as conn:
        last = get_meta(conn, "last_recommend")
        if last is None:
            console.print("[yellow]No recommendations yet.[/] Run [bold]audipy recommend[/].")
            return
        for rtype, heading, blurb in wanted:
            grouped = _grouped(conn, rtype, cash_only)
            total = sum(len(v) for v in grouped.values())
            console.rule(f"[bold]{heading}[/]  [dim]({total} — {blurb})[/]")
            if not grouped:
                console.print("[dim]  Nothing found.[/]\n")
                continue
            for source, rows in grouped.items():
                console.print(f"\n[bold cyan]{source}[/]")
                for row in rows:
                    console.print(f"  • {_book_label(rtype, row)}  [dim]{_price_tag(row)}[/]")
            console.print()


def save_reports(config: Config, out_dir: Path) -> list[Path]:
    """Write plain-text shopping-list reports (one per type). Returns paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with connect(config.db_file) as conn:
        for rtype, heading, blurb in TYPES:
            grouped = _grouped(conn, rtype, cash_only=False)
            lines = [heading, blurb, "=" * 60, ""]
            for source, rows in grouped.items():
                lines.append(f"{source}:")
                for row in rows:
                    lines.append(f"  - {_book_label(rtype, row)}  ({_price_tag(row)})")
                lines.append("")
            path = out_dir / REPORT_FILES[rtype]
            path.write_text("\n".join(lines), encoding="utf-8")
            written.append(path)
    return written
