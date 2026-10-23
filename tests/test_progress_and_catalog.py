import sqlite3
from datetime import date

import pytest

from audipy import catalog
from audipy.config import Config
from audipy.db import connect
from audipy.sync import _store_book, parse_book


def _item(**over):
    item = {
        "asin": "B0TEST0001", "title": "Echoes of Empire", "language": "English",
        "authors": [{"name": "Mark Wayne McGinnis"}], "narrators": [{"name": "Eric Martin"}],
        "series": [{"title": "Empire", "sequence": "3"}],
        "listening_status": {"is_finished": False, "percent_complete": 76.0,
                             "time_remaining_seconds": 10310,
                             "finished_at_timestamp": "2026-10-15T16:17:03.895Z"},
        "is_finished": False, "percent_complete": 76.0,
        "rating": {"overall_distribution": {"average_rating": 4.8330, "num_ratings": 659}},
        "category_ladders": [
            {"ladder": [{"name": "Science Fiction & Fantasy"}, {"name": "Science Fiction"}]},
            {"ladder": [{"name": "Science Fiction & Fantasy"}, {"name": "Science Fiction"}]},
            {"ladder": [{"name": "Science Fiction & Fantasy"}, {"name": "Military"}]}],
        "merchandising_summary": "<p>The war &amp; the <b>empire</b>.</p>",
    }
    item.update(over)
    return item


def test_progress_genres_rating_and_summary_are_captured():
    book = parse_book(_item())
    assert (book["is_finished"], book["percent_complete"], book["time_left_sec"]) == (0, 76.0, 10310)
    assert book["last_listened_at"] == "2026-10-15T16:17:03.895Z"
    assert book["genres"] == ("Science Fiction & Fantasy > Science Fiction; "
                              "Science Fiction & Fantasy > Military")
    assert (book["rating_avg"], book["rating_count"]) == (4.83, 659)
    assert book["summary"] == "The war & the empire ."


def test_a_book_without_the_new_groups_still_parses():
    bare = {"asin": "B0TEST0002", "title": "Old"}
    book = parse_book(bare)
    assert book["is_finished"] is None and book["genres"] is None and book["summary"] is None


def test_an_old_database_gains_the_new_columns(tmp_path):
    db = tmp_path / "old.db"
    raw = sqlite3.connect(db)
    raw.executescript("""CREATE TABLE books (asin TEXT PRIMARY KEY, title TEXT NOT NULL,
        subtitle TEXT, title_norm TEXT NOT NULL, runtime_min INTEGER, language TEXT,
        release_date TEXT, purchase_date TEXT, cover_url TEXT, synced_at TEXT NOT NULL);
        INSERT INTO books VALUES ('A', 't', NULL, 't', 1, 'english', NULL, NULL, NULL, 'x');""")
    raw.close()
    with connect(db) as conn:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(books)")}
        rec_cols = {r["name"] for r in conn.execute("PRAGMA table_info(recommendations)")}
        assert {"is_finished", "genres", "summary"} <= cols and "release_date" in rec_cols
        assert conn.execute("SELECT title FROM books").fetchone()["title"] == "t"
        _store_book(conn, parse_book(_item()), "now")


class FakeClient:
    def __init__(self, products):
        self.products, self.calls = products, []

    def get(self, endpoint, **params):
        self.calls.append((endpoint, params))
        return {"products": self.products}

    def post(self, *a, **k):  # pragma: no cover - must never be reached
        pytest.fail("catalog search must never POST")


def _product(asin, title, release, **over):
    p = {"asin": asin, "title": title, "language": "english", "release_date": release,
         "authors": [{"name": "Brandon Sanderson"}], "narrators": [{"name": "Michael Kramer"}],
         "series": [{"title": "Stormlight", "sequence": "6"}],
         "price": {"lowest_price": {"type": "member", "base": 14.090000152}, "credit_price": 1.0}}
    p.update(over)
    return p


def test_search_marks_owned_and_upcoming_and_only_reads(tmp_path):
    cfg = Config(home=tmp_path)
    with connect(cfg.db_file) as conn:
        _store_book(conn, parse_book(_item(asin="OWNED", title="Owned One")), "now")
    client = FakeClient([
        _product("NEW", "Wind and Truth II", "2027-01-05"),
        _product("OWNED", "Owned One", "2025-01-01"),
        _product("ES", "Spanish", "2026-12-01", language="spanish"),
        _product("OTHER", "Not his", "2026-11-01", authors=[{"name": "Someone Else"}]),
    ])
    out = catalog.search(cfg, "author", "Brandon  Sanderson", client=client, today=date(2026, 10, 23))
    assert [(e["asin"], e["upcoming"], e["owned"]) for e in out] == [("NEW", True, False), ("OWNED", False, True)]
    assert out[0]["member_price"] == 14.09
    endpoint, params = client.calls[0]
    assert endpoint == "1.0/catalog/products" and params["author"] == "Brandon Sanderson"
    assert params["products_sort_by"] == "-ReleaseDate"


def test_series_lookups_carry_the_sequence(tmp_path):
    cfg = Config(home=tmp_path)
    out = catalog.search(cfg, "series", "Stormlight", client=FakeClient([_product("S6", "Book 6", "2027-01-01")]),
                         today=date(2026, 10, 23))
    assert out[0]["sequence"] == "6" and out[0]["sequence_num"] == 6.0


@pytest.mark.parametrize("kind,name", [("publisher", "Tor"), ("author", "   ")])
def test_bad_input_is_refused(tmp_path, kind, name):
    cfg = Config(home=tmp_path)
    with pytest.raises(ValueError):
        catalog.search(cfg, kind, name, client=FakeClient([]))
