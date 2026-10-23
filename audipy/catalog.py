"""Look up titles in the Audible catalog by author, narrator or series, newest first.

Read-only: one GET to the catalog endpoint, nothing else. Owned books are marked from the local
database, so "is there anything new" is answerable without buying, wishlisting or touching the
library.
"""

from __future__ import annotations

from datetime import date

from audible import Client

from audipy.config import Config
from audipy.db import connect
from audipy.normalize import normalize_name, normalize_title
from audipy.recommend import (
    CATALOG_ENDPOINT,
    _credit_price,
    _matched_series,
    _member_price,
    _names,
    _verify,
)
from audipy.sync import _rating, _summary

GROUPS = "series,contributors,product_desc,product_attrs,price,rating"
KINDS = {"author": ("author", "authors"), "narrator": ("narrator", "narrators"),
         "series": ("title", "series")}
MAX_RESULTS = 50


def _owned(config: Config) -> tuple[set[str], set[str]]:
    with connect(config.db_file) as conn:
        rows = conn.execute("SELECT asin, title_norm FROM books").fetchall()
    return {r["asin"] for r in rows}, {r["title_norm"] for r in rows if r["title_norm"]}


def to_entry(product: dict, kind: str, name_norm: str, owned_asins: set[str],
             owned_titles: set[str], config: Config, today: date) -> dict:
    released = product.get("release_date") or product.get("issue_date")
    price = _member_price(product)
    seq_raw, seq_num = _matched_series(product, name_norm) if kind == "series" else (None, None)
    avg, count = _rating(product)
    return {
        "asin": product.get("asin"),
        "title": product.get("title") or "",
        "subtitle": product.get("subtitle"),
        "authors": _names(product, "authors"),
        "narrators": _names(product, "narrators"),
        "series": [f"{s.get('title')} #{s.get('sequence')}" if s.get("sequence") else s.get("title")
                   for s in (product.get("series") or []) if s.get("title")],
        "sequence": seq_raw,
        "sequence_num": seq_num,
        "release_date": released,
        "upcoming": bool(released and released > today.isoformat()),
        "owned": product.get("asin") in owned_asins
                 or normalize_title(product.get("title")) in owned_titles,
        "member_price": round(price, 2) if price is not None else None,
        "credit_price": _credit_price(product),
        "purchase_method": "cash" if price is not None and price < config.max_price else "credit",
        "rating_avg": avg,
        "rating_count": count,
        "runtime_min": product.get("runtime_length_min"),
        "language": (product.get("language") or "").lower() or None,
        "summary": _summary(product),
    }


def search(config: Config, kind: str, name: str, *, client: Client | None = None,
           limit: int = 25, today: date | None = None) -> list[dict]:
    """Titles by/narrated by/in `name`, newest release first, in the configured language."""
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    clean = " ".join(name.split())[:120]
    if not clean:
        raise ValueError("name is empty")
    param, verify_key = KINDS[kind]
    if client is None:
        from audipy.audible_client import get_client

        client = get_client(config)
    resp = client.get(CATALOG_ENDPOINT, num_results=MAX_RESULTS, response_groups=GROUPS,
                      products_sort_by="-ReleaseDate", **{param: clean})
    products = resp.get("products", []) if isinstance(resp, dict) else []
    owned_asins, owned_titles = _owned(config)
    norm = normalize_name(clean)
    entries = [
        to_entry(p, kind, norm, owned_asins, owned_titles, config, today or date.today())
        for p in products
        if p.get("asin")
        and (p.get("language") or "").lower() == config.language
        and not p.get("is_purchasability_suppressed")
        and _verify(p, verify_key, norm)
    ]
    return entries[: max(1, min(limit, MAX_RESULTS))]
