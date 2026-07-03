import dataclasses

import pytest

from audipy import recommend
from audipy.config import Config
from audipy.db import connect
from audipy.recommend import (
    Source,
    _build_row,
    _credit_price,
    _is_candidate,
    _member_price,
    _verify,
    generate,
)
from audipy.sync import _store_book, parse_book


def _product(**overrides):
    product = {
        "asin": "NEW1",
        "title": "A New Adventure",
        "language": "english",
        "authors": [{"name": "Craig Alanson"}],
        "narrators": [{"name": "R.C. Bray"}],
        "series": [{"title": "Convergence", "sequence": "6"}],
        "price": {"lowest_price": {"type": "member", "base": 9.99}, "credit_price": 1.0},
    }
    product.update(overrides)
    return product


class TestPrice:
    def test_member_price(self):
        assert _member_price(_product()) == 9.99

    def test_member_price_missing_when_not_member_type(self):
        p = _product(price={"lowest_price": {"type": "list", "base": 20.0}})
        assert _member_price(p) is None

    def test_member_price_null(self):
        assert _member_price(_product(price=None)) is None

    def test_credit_price(self):
        assert _credit_price(_product()) == 1.0


class TestPurchaseMethod:
    def _method(self, price, max_price=12.66):
        config = dataclasses.replace(_dummy_config(), max_price=max_price)
        row = _build_row("author", Source("Craig Alanson", "craig alanson"),
                         _product(price={"lowest_price": {"type": "member", "base": price}}),
                         config, "2026-07-02")
        return row["purchase_method"]

    def test_below_threshold_is_cash(self):
        assert self._method(12.17) == "cash"

    def test_at_threshold_is_credit(self):
        assert self._method(12.66) == "credit"

    def test_above_threshold_is_credit(self):
        assert self._method(18.35) == "credit"

    def test_no_price_is_credit(self):
        config = _dummy_config()
        row = _build_row("author", Source("X", "x"), _product(price=None), config, "t")
        assert row["purchase_method"] == "credit"


class TestCandidateFilter:
    def test_owned_by_asin_excluded(self):
        assert not _is_candidate(_product(asin="OWNED"), "english", {"OWNED"}, set())

    def test_owned_by_title_excluded(self):
        assert not _is_candidate(_product(), "english", set(), {"a new adventure"})

    def test_wrong_language_excluded(self):
        assert not _is_candidate(_product(language="german"), "english", set(), set())

    def test_suppressed_excluded(self):
        assert not _is_candidate(
            _product(is_purchasability_suppressed=True), "english", set(), set()
        )

    def test_valid_candidate_kept(self):
        assert _is_candidate(_product(), "english", set(), set())


class TestVerify:
    def test_author_variant_matches(self):
        # Normalized matching: catalog "A.G. Riddle" matches owned "A. G. Riddle".
        p = _product(authors=[{"name": "A.G. Riddle"}])
        assert _verify(p, "authors", "ag riddle")

    def test_series_match(self):
        assert _verify(_product(), "series", "convergence")

    def test_no_match(self):
        assert not _verify(_product(), "authors", "someone else")


def _dummy_config(home=None):
    return Config(home=home, marketplace="us", max_price=12.66, language="english")


def _seed_library(config, items):
    with connect(config.db_file) as conn:
        for item in items:
            book = parse_book(item)
            _store_book(conn, book, "2026-07-02")


class FakeClient:
    """Stands in for the Audible API client; returns products by search param."""

    def __init__(self, by_param):
        self.by_param = by_param

    def get(self, endpoint, num_results=None, response_groups=None, **params):
        (key, value), = params.items()
        return {"products": self.by_param.get(value, [])}


class TestGenerateIntegration:
    def test_end_to_end(self, tmp_path, monkeypatch):
        config = _dummy_config(home=tmp_path)
        # Owned library: two books in "Convergence" by Craig Alanson (own #1, #2).
        _seed_library(config, [
            {"asin": "OWN1", "title": "Aftermath", "authors": [{"name": "Craig Alanson"}],
             "narrators": [{"name": "R.C. Bray"}],
             "series": [{"title": "Convergence", "sequence": "1"}], "language": "english"},
            {"asin": "OWN2", "title": "Second Wave", "authors": [{"name": "Craig Alanson"}],
             "narrators": [{"name": "R.C. Bray"}],
             "series": [{"title": "Convergence", "sequence": "2"}], "language": "english"},
        ])

        fake = FakeClient({
            # Series search by title="Convergence": one owned (#1) + one new (#6).
            "Convergence": [
                _product(asin="OWN1", title="Aftermath", series=[{"title": "Convergence", "sequence": "1"}]),
                _product(asin="NEW6", title="Dead World", series=[{"title": "Convergence", "sequence": "6"}]),
            ],
            # Author search: the new book again + a German book (filtered out).
            "Craig Alanson": [
                _product(asin="NEW6", title="Dead World", series=[{"title": "Convergence", "sequence": "6"}]),
                _product(asin="DE1", title="Fremdsprache", language="german"),
            ],
            # Narrator search: a book by a different author, in English.
            "R.C. Bray": [
                _product(asin="NAR1", title="Bray Reads This", authors=[{"name": "Other Author"}]),
            ],
        })
        monkeypatch.setattr("audipy.audible_client.get_client", lambda cfg: fake)

        counts = generate(config)
        assert counts["series"] == 1  # only the unowned #6, not the owned #1
        assert counts["author"] == 1  # new book kept, German filtered out
        assert counts["narrator"] == 1

        with connect(config.db_file) as conn:
            rows = conn.execute(
                "SELECT rec_type, asin, sequence FROM recommendations ORDER BY rec_type"
            ).fetchall()
        by_type = {r["rec_type"]: r for r in rows}
        assert by_type["series"]["asin"] == "NEW6"
        assert by_type["series"]["sequence"] == "6"
        assert by_type["author"]["asin"] == "NEW6"
        assert by_type["narrator"]["asin"] == "NAR1"


@pytest.mark.parametrize("rec_type,expected", [("series", 1.0), ("author", 0.8), ("narrator", 0.6)])
def test_confidence_values(rec_type, expected):
    assert recommend.CONFIDENCE[rec_type] == expected
