from audipy.sync import _largest_cover, parse_book


def _library_item(**overrides):
    item = {
        "asin": "B09CVBWLZT",
        "title": "Overlord, Vol. 1",
        "subtitle": "The Undead King",
        "authors": [{"asin": "B00J1ZJ362", "name": "Kugane Maruyama"}, {"asin": None, "name": "so-bin"}],
        "narrators": [{"asin": None, "name": "Chris Guerrero"}],
        "series": [{"asin": "B09CZ4HYBX", "sequence": "1", "title": "Overlord"}],
        "runtime_length_min": 481,
        "release_date": "2021-09-14",
        "issue_date": "2021-09-14",
        "purchase_date": "2026-05-10T14:36:18.736Z",
        "language": "English",
        "product_images": {"500": "img500.jpg", "1024": "img1024.jpg"},
    }
    item.update(overrides)
    return item


class TestParseBook:
    def test_core_fields(self):
        book = parse_book(_library_item())
        assert book["asin"] == "B09CVBWLZT"
        assert book["title"] == "Overlord, Vol. 1"
        assert book["runtime_min"] == 481
        assert book["language"] == "english"  # lowercased
        assert book["title_norm"] == "overlord vol 1"

    def test_no_asin_is_skipped(self):
        assert parse_book(_library_item(asin=None)) is None

    def test_contributors_normalized(self):
        book = parse_book(_library_item())
        assert [a["name"] for a in book["authors"]] == ["Kugane Maruyama", "so-bin"]
        assert book["authors"][0]["name_norm"] == "kugane maruyama"
        assert book["narrators"][0]["name"] == "Chris Guerrero"

    def test_series_sequence_parsed(self):
        book = parse_book(_library_item())
        series = book["series"][0]
        assert series["title"] == "Overlord"
        assert series["sequence"] == "1"
        assert series["sequence_num"] == 1.0

    def test_missing_contributors_default_empty(self):
        book = parse_book(_library_item(authors=None, narrators=None, series=None))
        assert book["authors"] == []
        assert book["narrators"] == []
        assert book["series"] == []

    def test_release_date_falls_back_to_issue_date(self):
        book = parse_book(_library_item(release_date=None))
        assert book["release_date"] == "2021-09-14"


class TestLargestCover:
    def test_picks_highest_resolution(self):
        assert _largest_cover({"500": "a", "1024": "b", "252": "c"}) == "b"

    def test_none_and_empty(self):
        assert _largest_cover(None) is None
        assert _largest_cover({}) is None
