"""
Unit tests for postprocessing module.

Tests cover:
- Entity extraction from BIO labels
- City name reconstruction (hyphens, multi-word)
- Gazetteer validation (exact + fuzzy)
- Standalone fuzzy_match function
- Edge cases (empty input, invalid labels, length mismatch)
"""

import pytest
from src.nlp.postprocessing import (
    extract_entities,
    extract_all_entities,
    reconstruct_city_name,
    validate_against_gazetteer,
    fuzzy_match,
    validate_extraction,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def gazetteer():
    """Load gazetteer with default French cities."""
    from src.nlp.gazetteer import load_gazetteer
    return load_gazetteer()


# ---------------------------------------------------------------------------
# TestExtractEntities
# ---------------------------------------------------------------------------

class TestExtractEntities:
    def test_simple_extraction(self):
        tokens = ["Je", "veux", "aller", "de", "Paris", "à", "Lyon"]
        labels = ["O", "O", "O", "O", "B-ORIGIN", "O", "B-DEST"]
        origin, dest = extract_entities(tokens, labels)
        assert origin == "Paris"
        assert dest == "Lyon"

    def test_multi_word_with_hyphens(self):
        tokens = ["de", "Port", "-", "Boulet", "à", "Aix", "-", "en", "-", "Provence"]
        labels = ["O", "B-ORIGIN", "I-ORIGIN", "I-ORIGIN", "O", "B-DEST", "I-DEST", "I-DEST", "I-DEST", "I-DEST"]
        origin, dest = extract_entities(tokens, labels)
        assert origin == "Port-Boulet"
        assert dest == "Aix-en-Provence"

    def test_no_entities_returns_none(self):
        tokens = ["Bonjour", "comment", "allez", "-", "vous"]
        labels = ["O", "O", "O", "O", "O"]
        origin, dest = extract_entities(tokens, labels)
        assert origin is None
        assert dest is None

    def test_only_origin(self):
        tokens = ["Je", "pars", "de", "Paris"]
        labels = ["O", "O", "O", "B-ORIGIN"]
        origin, dest = extract_entities(tokens, labels)
        assert origin == "Paris"
        assert dest is None

    def test_only_destination(self):
        tokens = ["direction", "Lyon"]
        labels = ["O", "B-DEST"]
        origin, dest = extract_entities(tokens, labels)
        assert origin is None
        assert dest == "Lyon"

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            extract_entities(["Paris", "Lyon"], ["B-ORIGIN"])

    def test_single_token_city(self):
        tokens = ["billet", "Paris", "Lyon"]
        labels = ["O", "B-ORIGIN", "B-DEST"]
        origin, dest = extract_entities(tokens, labels)
        assert origin == "Paris"
        assert dest == "Lyon"


# ---------------------------------------------------------------------------
# TestReconstructCityName
# ---------------------------------------------------------------------------

class TestReconstructCityName:
    def test_single_word(self):
        assert reconstruct_city_name(["Paris"]) == "Paris"

    def test_hyphenated_city(self):
        assert reconstruct_city_name(["Port", "-", "Boulet"]) == "Port-Boulet"

    def test_multi_hyphen(self):
        assert reconstruct_city_name(["Aix", "-", "en", "-", "Provence"]) == "Aix-en-Provence"

    def test_empty_list(self):
        assert reconstruct_city_name([]) == ""

    def test_two_word_no_hyphen(self):
        assert reconstruct_city_name(["Le", "Mans"]) == "Le Mans"


# ---------------------------------------------------------------------------
# TestExtractAllEntities
# ---------------------------------------------------------------------------

class TestExtractAllEntities:
    def test_multiple_destinations(self):
        tokens = ["de", "Paris", "à", "Lyon", "via", "Dijon"]
        labels = ["O", "B-ORIGIN", "O", "B-DEST", "O", "B-DEST"]
        entities = extract_all_entities(tokens, labels)
        types = [e[1] for e in entities]
        names = [e[0] for e in entities]
        assert "ORIGIN" in types
        assert "Paris" in names
        assert "Lyon" in names

    def test_empty_returns_empty_list(self):
        tokens = ["Bonjour"]
        labels = ["O"]
        assert extract_all_entities(tokens, labels) == []


# ---------------------------------------------------------------------------
# TestValidateAgainstGazetteer
# ---------------------------------------------------------------------------

class TestValidateAgainstGazetteer:
    def test_exact_match(self, gazetteer):
        result = validate_against_gazetteer("Paris", gazetteer)
        assert result == "Paris"

    def test_case_insensitive(self, gazetteer):
        result = validate_against_gazetteer("paris", gazetteer)
        assert result is not None
        assert result.lower() == "paris"

    def test_fuzzy_match_misspelling(self, gazetteer):
        # "Pari" is 1 edit away from "Paris"
        result = validate_against_gazetteer("Pari", gazetteer)
        assert result is not None

    def test_unknown_city_returns_none(self, gazetteer):
        result = validate_against_gazetteer("Zzzzzzzzz", gazetteer)
        assert result is None

    def test_empty_string_returns_none(self, gazetteer):
        result = validate_against_gazetteer("", gazetteer)
        assert result is None

    def test_none_returns_none(self, gazetteer):
        result = validate_against_gazetteer(None, gazetteer)
        assert result is None

    def test_multiword_city(self, gazetteer):
        result = validate_against_gazetteer("Aix-en-Provence", gazetteer)
        assert result is not None


# ---------------------------------------------------------------------------
# TestFuzzyMatch
# ---------------------------------------------------------------------------

class TestFuzzyMatch:
    def test_exact_match(self):
        result = fuzzy_match("Paris", ["Paris", "Lyon", "Bordeaux"])
        assert result == "Paris"

    def test_one_edit_distance(self):
        result = fuzzy_match("Pari", ["Paris", "Lyon"])
        assert result == "Paris"

    def test_two_edit_distance(self):
        result = fuzzy_match("Lyone", ["Lyon", "Paris"])
        assert result == "Lyon"

    def test_no_match_beyond_max_distance(self):
        result = fuzzy_match("Zzz", ["Paris", "Lyon"], max_distance=2)
        assert result is None

    def test_empty_entity_returns_none(self):
        assert fuzzy_match("", ["Paris"]) is None

    def test_empty_candidates_returns_none(self):
        assert fuzzy_match("Paris", []) is None

    def test_picks_closest(self):
        # "Lyo" is 1 edit from "Lyon", 4 from "Paris"
        result = fuzzy_match("Lyo", ["Paris", "Lyon"])
        assert result == "Lyon"

    def test_case_insensitive(self):
        result = fuzzy_match("paris", ["Paris", "Lyon"])
        assert result == "Paris"


# ---------------------------------------------------------------------------
# TestValidateExtraction
# ---------------------------------------------------------------------------

class TestValidateExtraction:
    def test_both_present(self):
        assert validate_extraction("Paris", "Lyon") is True

    def test_missing_origin(self):
        assert validate_extraction(None, "Lyon") is False

    def test_missing_destination(self):
        assert validate_extraction("Paris", None) is False

    def test_both_none(self):
        assert validate_extraction(None, None) is False

    def test_empty_strings(self):
        assert validate_extraction("", "Lyon") is False
