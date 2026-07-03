"""Normalization helpers for matching names, titles, and series sequences.

The original tool matched authors/narrators/series by exact lowercased string,
so "A. G. Riddle" and "A.G. Riddle" were treated as different people and
recommendations were silently dropped. These helpers collapse those variants to
a single canonical key used for both deduplication and matching.
"""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_WHITESPACE = re.compile(r"\s+")


def normalize_name(name: str | None) -> str:
    """Canonical key for an author/narrator/series name.

    Lowercases, drops punctuation, collapses whitespace, and merges runs of
    single-letter tokens so initials match regardless of spacing/periods:

        "A. G. Riddle"  -> "ag riddle"
        "A.G. Riddle"   -> "ag riddle"
        "J. R. R. Tolkien" -> "jrr tolkien"
        "St. James"     -> "st james"
    """
    if not name:
        return ""
    text = _NON_ALNUM.sub(" ", name.lower())
    tokens = _WHITESPACE.sub(" ", text).strip().split(" ")
    if not tokens or tokens == [""]:
        return ""

    merged: list[str] = []
    run: list[str] = []
    for token in tokens:
        if len(token) == 1:
            run.append(token)
        else:
            if run:
                merged.append("".join(run))
                run = []
            merged.append(token)
    if run:
        merged.append("".join(run))
    return " ".join(merged)


def normalize_title(title: str | None) -> str:
    """Canonical key for a book title (for owned/duplicate detection)."""
    if not title:
        return ""
    text = _NON_ALNUM.sub(" ", title.lower())
    return _WHITESPACE.sub(" ", text).strip()


def parse_sequence(sequence: str | int | float | None) -> float | None:
    """Parse a series sequence ("1", "2.5", "1-2") into a sortable float.

    Returns None when there's no usable number (blank, or a range/prose we
    can't order). The raw value is preserved separately for display.
    """
    if sequence is None:
        return None
    if isinstance(sequence, (int, float)):
        return float(sequence)
    text = sequence.strip()
    if not text:
        return None
    # Take the leading number (handles "1", "2.5", and the low end of "1-2").
    match = re.match(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None
