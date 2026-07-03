"""Generate book recommendations from your synced library.

Three kinds, in priority order:

1. series   — unowned books in series you already own (continue what you started)
2. author   — more books by authors you own
3. narrator — books read by narrators you trust (discovery)

Improvements over the original: source names are matched with normalized keys
(so name variants don't drop matches), series sequence is captured for gap/
new-release awareness, and the top-N limits come from config instead of a
hardcoded 5.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from audible import Client

from audipy.config import Config
from audipy.db import connect, set_meta
from audipy.normalize import normalize_name, parse_sequence

CATALOG_ENDPOINT = "1.0/catalog/products"
# Results per catalog search. Most authors/series have far fewer; Audible caps
# a single page at 50 for this endpoint.
CATALOG_RESULTS = 50

AUTHOR_GROUPS = "contributors,product_desc,media,price"
NARRATOR_GROUPS = "contributors,product_desc,media,price"
SERIES_GROUPS = "series,contributors,product_desc,media,price"

# Confidence per recommendation type (series continuations are the surest bet).
CONFIDENCE = {"series": 1.0, "author": 0.8, "narrator": 0.6}

ProgressFn = Callable[[str, int, int], None]


@dataclass
class Source:
    """A top author/narrator/series to generate recommendations from."""

    name: str  # display name
    norm: str  # normalized match key


def _top_sources(conn: sqlite3.Connection, table: str, name_col: str,
                 norm_col: str, limit: int) -> list[Source]:
    rows = conn.execute(
        f"""SELECT MIN({name_col}) AS name, {norm_col} AS norm
            FROM {table}
            GROUP BY {norm_col}
            ORDER BY COUNT(DISTINCT book_asin) DESC, name
            LIMIT ?""",
        (limit,),
    ).fetchall()
    return [Source(name=r["name"], norm=r["norm"]) for r in rows]


def _owned(conn: sqlite3.Connection) -> tuple[set[str], set[str]]:
    """Return (owned ASINs, owned normalized titles) for duplicate detection."""
    asins = {r["asin"] for r in conn.execute("SELECT asin FROM books")}
    titles = {
        r["title_norm"] for r in conn.execute("SELECT title_norm FROM books") if r["title_norm"]
    }
    return asins, titles


def _member_price(product: dict) -> float | None:
    price = product.get("price") or {}
    lowest = price.get("lowest_price") or {}
    if lowest.get("type") == "member":
        return lowest.get("base")
    return None


def _credit_price(product: dict) -> float | None:
    return (product.get("price") or {}).get("credit_price")


def _names(product: dict, key: str) -> str | None:
    values = [c["name"] for c in (product.get(key) or []) if c.get("name")]
    return ", ".join(values) or None


def _matched_series(product: dict, source_norm: str) -> tuple[str | None, float | None]:
    """Return (raw sequence, numeric sequence) for the matching series, if any."""
    for series in product.get("series") or []:
        if normalize_name(series.get("title")) == source_norm:
            seq = series.get("sequence")
            return (str(seq) if seq is not None else None, parse_sequence(seq))
    return None, None


def _catalog_search(client: Client, response_groups: str, **params) -> list[dict]:
    resp = client.get(
        CATALOG_ENDPOINT, num_results=CATALOG_RESULTS, response_groups=response_groups, **params
    )
    return resp.get("products", []) if isinstance(resp, dict) else []


def _is_candidate(product: dict, language: str, owned_asins: set[str],
                  owned_titles: set[str]) -> bool:
    """Keep only purchasable, right-language books you don't already own."""
    if (product.get("language") or "").lower() != language:
        return False
    if product.get("is_purchasability_suppressed"):
        return False
    asin = product.get("asin")
    if asin and asin in owned_asins:
        return False
    title_norm = normalize_name(product.get("title"))
    if title_norm and title_norm in owned_titles:
        return False
    return True


def _build_row(rec_type: str, source: Source, product: dict, config: Config,
               generated_at: str) -> dict:
    price = _member_price(product)
    method = "cash" if price is not None and price < config.max_price else "credit"
    seq_raw, seq_num = _matched_series(product, source.norm)
    return {
        "rec_type": rec_type,
        "source_name": source.name,
        "source_norm": source.norm,
        "asin": product.get("asin"),
        "title": product.get("title") or "",
        "subtitle": product.get("subtitle"),
        "series_title": (product.get("series") or [{}])[0].get("title")
        if product.get("series")
        else None,
        "sequence": seq_raw,
        "sequence_num": seq_num,
        "author_names": _names(product, "authors"),
        "narrator_names": _names(product, "narrators"),
        "member_price": price,
        "credit_price": _credit_price(product),
        "purchase_method": method,
        "confidence": CONFIDENCE[rec_type],
        "language": (product.get("language") or "").lower() or None,
        "cover_url": None,
        "generated_at": generated_at,
    }


def _store_rows(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executemany(
        """INSERT INTO recommendations
           (rec_type, source_name, source_norm, asin, title, subtitle, series_title,
            sequence, sequence_num, author_names, narrator_names, member_price,
            credit_price, purchase_method, confidence, language, cover_url, generated_at)
           VALUES
           (:rec_type, :source_name, :source_norm, :asin, :title, :subtitle, :series_title,
            :sequence, :sequence_num, :author_names, :narrator_names, :member_price,
            :credit_price, :purchase_method, :confidence, :language, :cover_url, :generated_at)
           ON CONFLICT(rec_type, asin, source_norm) DO UPDATE SET
            member_price = excluded.member_price,
            credit_price = excluded.credit_price,
            purchase_method = excluded.purchase_method,
            sequence = excluded.sequence,
            sequence_num = excluded.sequence_num,
            generated_at = excluded.generated_at""",
        rows,
    )


# Each recommendation type: (rec_type, source table, catalog param, response_groups,
# whether the matching contributor/series must be verified on each product).
_PLANS = [
    ("series", "book_series", "series_title", "series_norm", "title", SERIES_GROUPS, "series"),
    ("author", "book_authors", "name", "name_norm", "author", AUTHOR_GROUPS, "authors"),
    ("narrator", "book_narrators", "name", "name_norm", "narrator", NARRATOR_GROUPS, "narrators"),
]


def _verify(product: dict, verify_key: str, source_norm: str) -> bool:
    """Confirm the product really is by/narrated-by/in the source (normalized)."""
    if verify_key == "series":
        return any(
            normalize_name(s.get("title")) == source_norm for s in (product.get("series") or [])
        )
    return any(
        normalize_name(c.get("name")) == source_norm for c in (product.get(verify_key) or [])
    )


def generate(config: Config, progress: ProgressFn | None = None) -> dict[str, int]:
    """Generate all recommendations, replacing any previous set. Returns counts."""
    generated_at = datetime.now(timezone.utc).isoformat()
    limits = {
        "series": config.top_series,
        "author": config.top_authors,
        "narrator": config.top_narrators,
    }
    counts = {"series": 0, "author": 0, "narrator": 0}

    with connect(config.db_file) as conn:
        owned_asins, owned_titles = _owned(conn)
        client = None  # created lazily so an empty library fails fast before auth
        conn.execute("DELETE FROM recommendations")

        for rec_type, table, name_col, norm_col, param, groups, verify_key in _PLANS:
            sources = _top_sources(conn, table, name_col, norm_col, limits[rec_type])
            for idx, source in enumerate(sources, start=1):
                if progress:
                    progress(rec_type, idx, len(sources))
                if client is None:
                    from audipy.audible_client import get_client

                    client = get_client(config)
                products = _catalog_search(client, groups, **{param: source.name})
                rows = [
                    _build_row(rec_type, source, p, config, generated_at)
                    for p in products
                    if _is_candidate(p, config.language, owned_asins, owned_titles)
                    and _verify(p, verify_key, source.norm)
                    and p.get("asin")
                ]
                if rows:
                    _store_rows(conn, rows)
                    counts[rec_type] += len(rows)

        set_meta(conn, "last_recommend", generated_at)
    return counts
