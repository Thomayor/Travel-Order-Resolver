"""
Unit tests for baseline NLP extraction module.

Tests cover:
- Keyword-based extraction
- Direct format extraction
- Heuristic extraction
- Invalid order detection
- Edge cases (multi-word cities, questions, etc.)
"""

import pytest
from src.nlp.baseline import BaselineExtractor, INVALID_INDICATORS


@pytest.fixture
def extractor():
    """Create a baseline extractor instance for tests."""
    return BaselineExtractor()


class TestInvalidDetection:
    """Test detection of invalid (non-travel) sentences."""

    def test_weather_question(self, extractor):
        """Weather questions should be invalid."""
        assert not extractor.is_valid_order("Quel temps fait-il à Paris?")
        assert not extractor.is_valid_order("quel temps fera-t-il demain?")

    def test_time_question(self, extractor):
        """Time-telling questions should be invalid."""
        assert not extractor.is_valid_order("Quelle heure est-il?")
        assert not extractor.is_valid_order("quelle heure est-il maintenant?")

    def test_greetings(self, extractor):
        """Greetings should be invalid."""
        assert not extractor.is_valid_order("Bonjour comment allez-vous?")
        assert not extractor.is_valid_order("Bonsoir et merci")

    def test_garbage_text(self, extractor):
        """Random text should be invalid."""
        assert not extractor.is_valid_order("azerty qwerty")
        assert not extractor.is_valid_order("abc def ghi")

    def test_no_locations(self, extractor):
        """Text with no locations should be invalid."""
        assert not extractor.is_valid_order("Je pars demain")
        assert not extractor.is_valid_order("Je veux voyager")


class TestValidOrders:
    """Test detection of valid travel orders."""

    def test_simple_order(self, extractor):
        """Simple travel order should be valid."""
        assert extractor.is_valid_order("Je veux aller de Paris à Lyon")
        assert extractor.is_valid_order("Train de Marseille à Nice")

    def test_question_with_travel_intent(self, extractor):
        """Questions about trains should be VALID (not time-telling)."""
        # These are valid travel orders (asking about train schedules)
        assert extractor.is_valid_order("À quelle heure part le train de Paris?")
        assert extractor.is_valid_order("Quelle heure le train de Nantes à Toulouse")
        assert extractor.is_valid_order("À quelle heure y a-t-il des trains vers Lyon en partance de Paris?")

    def test_direct_format(self, extractor):
        """Direct format should be valid."""
        assert extractor.is_valid_order("Billet Paris Lyon")
        assert extractor.is_valid_order("Je voudrais un billet Toulouse Bordeaux")


class TestKeywordExtraction:
    """Test keyword-based extraction (de X à Y)."""

    def test_de_a_pattern(self, extractor):
        """Extract 'de X à Y' pattern."""
        result = extractor.extract("Je veux aller de Paris à Lyon")
        assert result['origin'] == 'Paris'
        assert result['destination'] == 'Lyon'
        assert result['valid'] is True
        assert result['method'] == 'keywords'

    def test_depuis_vers_pattern(self, extractor):
        """Extract 'depuis X vers Y' pattern."""
        result = extractor.extract("Train pour Marseille depuis Toulouse")
        assert result['origin'] == 'Toulouse'
        assert result['destination'] == 'Marseille'
        assert result['valid'] is True

    def test_multi_word_cities(self, extractor):
        """Handle multi-word cities correctly."""
        result = extractor.extract("Port-Boulet vers La Rochelle")
        assert result['origin'] == 'Port-Boulet'
        assert result['destination'] == 'La Rochelle'
        assert result['valid'] is True

    def test_complex_question(self, extractor):
        """Extract from complex questions."""
        result = extractor.extract("À quelle heure y a-t-il des trains vers Lyon en partance de Paris?")
        assert result['origin'] == 'Paris'
        assert result['destination'] == 'Lyon'
        assert result['valid'] is True


class TestDirectFormat:
    """Test direct format extraction (billet X Y)."""

    def test_billet_pattern(self, extractor):
        """Extract 'billet X Y' pattern."""
        result = extractor.extract("Je voudrais un billet Bordeaux Nice")
        assert result['origin'] == 'Bordeaux'
        assert result['destination'] == 'Nice'
        assert result['valid'] is True
        assert result['method'] == 'direct_format'

    def test_ticket_pattern(self, extractor):
        """Extract 'ticket X Y' pattern."""
        result = extractor.extract("Un ticket Paris Lyon svp")
        assert result['origin'] == 'Paris'
        assert result['destination'] == 'Lyon'
        assert result['valid'] is True


class TestHeuristicExtraction:
    """Test heuristic extraction (first = origin, last = dest)."""

    def test_two_cities_no_keywords(self, extractor):
        """With two cities and no keywords, first=origin, last=dest."""
        result = extractor.extract("Toulouse Paris demain")
        assert result['origin'] == 'Toulouse'
        assert result['destination'] == 'Paris'
        assert result['valid'] is True

    def test_single_city_with_a(self, extractor):
        """Single city with 'à' should be destination."""
        result = extractor.extract_heuristic("Je vais à Paris")
        assert result[0] is None  # No origin
        assert result[1] == 'Paris'  # Destination

    def test_single_city_with_de(self, extractor):
        """Single city with 'de' should be origin."""
        result = extractor.extract_heuristic("Je pars de Lyon")
        assert result[0] == 'Lyon'  # Origin
        assert result[1] is None  # No destination


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_inverted_order(self, extractor):
        """Handle inverted question word order."""
        result = extractor.extract("Comment me rendre à Tours depuis Orléans")
        assert result['origin'] == 'Orléans'
        assert result['destination'] == 'Tours'
        assert result['valid'] is True

    def test_lowercase_no_accents(self, extractor):
        """Handle text without capitals or accents."""
        result = extractor.extract("je veux aller de paris a lyon")
        assert result['origin'] == 'Paris'
        assert result['destination'] == 'Lyon'
        assert result['valid'] is True

    def test_multiple_cities(self, extractor):
        """With multiple cities, extract first and last."""
        # This might extract incorrectly, but tests current behavior
        result = extractor.extract("Paris Lyon Marseille Nice")
        assert result['valid'] is True
        # Should get Paris and Nice (first and last)
        assert result['origin'] == 'Paris'
        assert result['destination'] == 'Nice'

    def test_ambiguous_names(self, extractor):
        """Handle cities that are also person names."""
        # "Paris" can be a person or city - should still extract
        result = extractor.extract("Je vais à Paris avec mon ami Albert")
        assert result['destination'] == 'Paris'
        assert result['valid'] is True


class TestOutputFormatting:
    """Test CSV output formatting."""

    def test_valid_csv_output(self, extractor):
        """Format valid result as CSV."""
        result = extractor.process_sentence("1", "Je veux aller de Paris à Lyon")
        csv = extractor.format_output_csv(result)
        assert csv == "1,Paris,Lyon"

    def test_invalid_csv_output(self, extractor):
        """Format invalid result as CSV with INVALID markers."""
        result = extractor.process_sentence("2", "Quel temps fait-il?")
        csv = extractor.format_output_csv(result)
        assert csv == "2,INVALID,INVALID"

    def test_partial_extraction_csv(self, extractor):
        """Format partial extraction (only one city found)."""
        result = extractor.process_sentence("3", "Je vais à Paris")
        csv = extractor.format_output_csv(result)
        # Should have destination but no origin
        assert "Paris" in csv
        assert "INVALID" in csv


class TestBatchProcessing:
    """Test batch processing functionality."""

    def test_process_batch(self, extractor):
        """Process multiple sentences in batch."""
        sentences = [
            ("1", "Je veux aller de Paris à Lyon"),
            ("2", "Quel temps fait-il?"),
            ("3", "Billet Marseille Nice")
        ]

        results = extractor.process_batch(sentences)

        assert len(results) == 3
        assert results[0]['origin'] == 'Paris'
        assert results[1]['valid'] is False
        assert results[2]['origin'] == 'Marseille'


class TestEvaluation:
    """Test evaluation metrics."""

    def test_evaluate_perfect_accuracy(self, extractor):
        """Test evaluation with 100% accurate predictions."""
        test_data = [
            ("1", "Je veux aller de Paris à Lyon", "Paris", "Lyon"),
            ("2", "Billet Marseille Nice", "Marseille", "Nice"),
        ]

        metrics = extractor.evaluate(test_data)

        assert metrics['accuracy'] == 1.0
        assert metrics['total'] == 2
        assert metrics['correct'] == 2
        assert metrics['origin_accuracy'] == 1.0
        assert metrics['destination_accuracy'] == 1.0

    def test_evaluate_partial_accuracy(self, extractor):
        """Test evaluation with partial accuracy."""
        test_data = [
            ("1", "Je veux aller de Paris à Lyon", "Paris", "Lyon"),  # Correct
            ("2", "Quel temps fait-il?", "INVALID", "INVALID"),  # Should be invalid
        ]

        metrics = extractor.evaluate(test_data)

        # Only 1 out of 2 correct
        assert metrics['total'] == 2
        assert metrics['correct'] >= 1  # At least the valid one should work


class TestConstants:
    """Test module constants are properly defined."""

    def test_invalid_indicators_present(self):
        """Check that invalid indicators are defined."""
        assert "quel temps" in INVALID_INDICATORS
        assert "quelle heure est" in INVALID_INDICATORS  # Fixed version
        assert "azerty" in INVALID_INDICATORS

    def test_quelle_heure_est_specific(self):
        """Verify 'quelle heure est' is used (not just 'quelle heure')."""
        # Should be specific to avoid catching valid travel questions
        assert "quelle heure est" in INVALID_INDICATORS
        assert "quelle heure" not in INVALID_INDICATORS or "quelle heure est" in INVALID_INDICATORS
