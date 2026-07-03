from audipy.normalize import normalize_name, normalize_title, parse_sequence


class TestNormalizeName:
    def test_initial_variants_collapse(self):
        # The headline bug: these were treated as different authors.
        assert normalize_name("A. G. Riddle") == normalize_name("A.G. Riddle")
        assert normalize_name("A. G. Riddle") == normalize_name("AG Riddle")

    def test_multiple_initials(self):
        assert normalize_name("J. R. R. Tolkien") == normalize_name("J.R.R. Tolkien")
        assert normalize_name("J.R.R. Tolkien") == "jrr tolkien"

    def test_punctuation_and_case(self):
        assert normalize_name("St. James") == normalize_name("St James")
        assert normalize_name("O'Brien") == "obrien"

    def test_distinct_names_stay_distinct(self):
        assert normalize_name("Ann Cleeves") != normalize_name("Anne Cleeves")
        assert normalize_name("John Scalzi") != normalize_name("John Scalza")

    def test_empty_and_none(self):
        assert normalize_name(None) == ""
        assert normalize_name("") == ""
        assert normalize_name("   ") == ""


class TestNormalizeTitle:
    def test_case_and_punctuation(self):
        assert normalize_title("Make Time!") == "make time"
        assert normalize_title("  The  Martian ") == "the martian"

    def test_none(self):
        assert normalize_title(None) == ""


class TestParseSequence:
    def test_plain_numbers(self):
        assert parse_sequence("1") == 1.0
        assert parse_sequence("12") == 12.0

    def test_decimal(self):
        assert parse_sequence("2.5") == 2.5

    def test_range_takes_low_end(self):
        assert parse_sequence("1-2") == 1.0

    def test_numeric_inputs(self):
        assert parse_sequence(3) == 3.0
        assert parse_sequence(0) == 0.0  # a legitimate 0, not dropped to None

    def test_unparseable(self):
        assert parse_sequence(None) is None
        assert parse_sequence("") is None
        assert parse_sequence("Prequel") is None
