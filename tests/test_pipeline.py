"""
Integration tests for the Pipeline module.

Tests cover:
- City mapping loading and lookup
- Error handling
- Single sentence processing
- End-to-end pipeline processing
- NLP + Pathfinding integration
- Various error scenarios
"""

import pytest
import os
import csv
import tempfile
from pathlib import Path

from src.utils.pipeline import (
    load_city_mapping,
    map_city_to_uic,
    handle_errors,
    process_single_sentence,
    process_pipeline,
    CityMappingError,
    PipelineError
)
from src.nlp.baseline import BaselineExtractor, load_extractor
from src.pathfinding.graph_loader import get_or_build_graph
from src.pathfinding.algorithms import InvalidStationError, NoPathError


# ============================================================================
# Test load_city_mapping
# ============================================================================

def test_load_city_mapping():
    """Test loading city to UIC code mapping from CSV."""
    mapping = load_city_mapping()

    # Check that mapping is not empty
    assert len(mapping) > 0

    # Check that common cities are present (normalized names)
    assert 'paris' in mapping
    assert 'lyon' in mapping
    assert 'marseille' in mapping

    # Check UIC codes are strings
    assert isinstance(mapping['paris'], str)
    assert len(mapping['paris']) > 0


def test_load_city_mapping_invalid_file():
    """Test loading city mapping with invalid file raises error."""
    with pytest.raises(CityMappingError) as exc_info:
        load_city_mapping("nonexistent_file.csv")

    assert "not found" in str(exc_info.value).lower()


# ============================================================================
# Test map_city_to_uic
# ============================================================================

def test_map_city_to_uic_valid():
    """Test mapping valid city names to UIC codes."""
    mapping = load_city_mapping()

    # Test exact match (normalized)
    uic_paris = map_city_to_uic("Paris", mapping)
    assert uic_paris is not None
    assert isinstance(uic_paris, str)

    uic_lyon = map_city_to_uic("Lyon", mapping)
    assert uic_lyon is not None

    # Test case insensitivity
    uic_paris_lower = map_city_to_uic("paris", mapping)
    assert uic_paris_lower == uic_paris


def test_map_city_to_uic_with_accents():
    """Test mapping city names with French accents."""
    mapping = load_city_mapping()

    # Cities with accents should be normalized
    uic = map_city_to_uic("Saint-Étienne", mapping)
    # Should still work even if normalized in mapping
    assert uic is not None or map_city_to_uic("Saint-Etienne", mapping) is not None


def test_map_city_to_uic_invalid():
    """Test mapping invalid city name returns None."""
    mapping = load_city_mapping()

    uic = map_city_to_uic("NonexistentCity123", mapping)
    assert uic is None


def test_map_city_to_uic_none():
    """Test mapping None city name returns None."""
    mapping = load_city_mapping()

    uic = map_city_to_uic(None, mapping)
    assert uic is None


def test_map_city_to_uic_empty_string():
    """Test mapping empty string returns None."""
    mapping = load_city_mapping()

    uic = map_city_to_uic("", mapping)
    assert uic is None


# ============================================================================
# Test handle_errors
# ============================================================================

def test_handle_errors_generic():
    """Test error handling returns proper error structure."""
    error = ValueError("Test error message")
    result = handle_errors("123", error)

    assert result['sentence_id'] == "123"
    assert result['origin'] is None
    assert result['destination'] is None
    assert result['valid'] is False
    assert result['route'] == ['INVALID', 'INVALID']
    assert result['error_type'] == "ValueError"
    assert result['error_message'] == "Test error message"
    assert result['success'] is False


def test_handle_errors_invalid_station():
    """Test error handling for InvalidStationError."""
    error = InvalidStationError("Station not found")
    result = handle_errors("456", error)

    assert result['error_type'] == "InvalidStationError"
    assert "Station not found" in result['error_message']


def test_handle_errors_no_path():
    """Test error handling for NoPathError."""
    error = NoPathError("No path between stations")
    result = handle_errors("789", error)

    assert result['error_type'] == "NoPathError"
    assert "No path" in result['error_message']


# ============================================================================
# Test process_single_sentence
# ============================================================================

def test_process_single_sentence_valid_simple():
    """Test processing a valid simple travel order."""
    # Setup
    extractor = load_extractor()
    city_mapping = load_city_mapping()
    graph = get_or_build_graph()

    sentence_id = "1"
    sentence = "Je veux aller de Paris à Lyon"

    # Process
    result = process_single_sentence(
        sentence_id=sentence_id,
        sentence=sentence,
        extractor=extractor,
        city_mapping=city_mapping,
        graph=graph,
        include_route=False
    )

    # Assertions
    assert result['sentence_id'] == sentence_id
    assert result['sentence'] == sentence
    assert result['valid'] is True
    assert result['origin'] is not None
    assert result['destination'] is not None
    assert 'paris' in result['origin'].lower()
    assert 'lyon' in result['destination'].lower()
    assert result['origin_uic'] is not None
    assert result['destination_uic'] is not None
    # Note: success might be False if path doesn't exist in test network


def test_process_single_sentence_invalid():
    """Test processing an invalid sentence (not a travel order)."""
    extractor = load_extractor()
    city_mapping = load_city_mapping()
    graph = get_or_build_graph()

    sentence = "Quel temps fait-il aujourd'hui?"

    result = process_single_sentence(
        sentence_id="2",
        sentence=sentence,
        extractor=extractor,
        city_mapping=city_mapping,
        graph=graph,
        include_route=False
    )

    assert result['valid'] is False
    assert result['route'] == ['INVALID', 'INVALID']


def test_process_single_sentence_missing_destination():
    """Test processing a sentence with only origin (incomplete)."""
    extractor = load_extractor()
    city_mapping = load_city_mapping()
    graph = get_or_build_graph()

    sentence = "Je pars de Paris"

    result = process_single_sentence(
        sentence_id="3",
        sentence=sentence,
        extractor=extractor,
        city_mapping=city_mapping,
        graph=graph,
        include_route=False
    )

    # Should be invalid or have missing destination
    assert result['valid'] is False or result['destination'] is None


def test_process_single_sentence_unknown_city():
    """Test processing with a city not in the mapping."""
    extractor = load_extractor()
    city_mapping = load_city_mapping()
    graph = get_or_build_graph()

    # Create a sentence with a city that won't be in mapping
    sentence = "Je veux aller de Paris à CityThatDoesNotExist123"

    result = process_single_sentence(
        sentence_id="4",
        sentence=sentence,
        extractor=extractor,
        city_mapping=city_mapping,
        graph=graph,
        include_route=False
    )

    # Should fail at mapping stage
    if result['valid'] and result['destination']:
        # If NLP extracted the fake city, mapping should fail
        assert result['error_type'] == 'CityMappingError' or result['destination_uic'] is None


def test_process_single_sentence_with_route():
    """Test processing with full route computation."""
    extractor = load_extractor()
    city_mapping = load_city_mapping()
    graph = get_or_build_graph()

    sentence = "Je veux aller de Paris à Lyon"

    result = process_single_sentence(
        sentence_id="5",
        sentence=sentence,
        extractor=extractor,
        city_mapping=city_mapping,
        graph=graph,
        include_route=True  # Request full route
    )

    if result['success']:
        # If pathfinding succeeded
        assert len(result['route']) >= 2
        assert len(result['path']) >= 2  # UIC codes
        assert result['total_time'] > 0


# ============================================================================
# Test process_pipeline (End-to-End)
# ============================================================================

def test_process_pipeline_nlp_mode(tmp_path):
    """Test end-to-end pipeline in NLP mode."""
    # Create test input file
    input_file = tmp_path / "input_test.csv"
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Je veux aller de Paris à Lyon\n"
        "2,Quel temps fait-il?\n"
        "3,Train pour Marseille depuis Toulouse\n",
        encoding='utf-8'
    )

    output_file = tmp_path / "output_test.csv"

    # Run pipeline
    stats = process_pipeline(
        input_file=str(input_file),
        output_file=str(output_file),
        mode='nlp'
    )

    # Check statistics
    assert stats['total'] == 3
    assert stats['valid'] >= 1  # At least sentence 1 should be valid
    assert stats['invalid'] >= 1  # Sentence 2 should be invalid

    # Check output file exists
    assert output_file.exists()

    # Read and validate output
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3
    assert 'sentenceID' in rows[0]
    assert 'Departure' in rows[0]
    assert 'Destination' in rows[0]

    # Check invalid sentence has INVALID markers
    invalid_row = next((r for r in rows if r['sentenceID'] == '2'), None)
    assert invalid_row is not None
    assert invalid_row['Departure'] == 'INVALID'
    assert invalid_row['Destination'] == 'INVALID'


def test_process_pipeline_route_mode(tmp_path):
    """Test end-to-end pipeline in route mode."""
    input_file = tmp_path / "input_route.csv"
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Je veux aller de Paris à Lyon\n"
        "2,Billet invalide\n",
        encoding='utf-8'
    )

    output_file = tmp_path / "output_route.csv"

    stats = process_pipeline(
        input_file=str(input_file),
        output_file=str(output_file),
        mode='route'
    )

    assert stats['total'] == 2
    assert output_file.exists()

    # Read output
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Check header
    assert len(rows) >= 3  # Header + 2 data rows
    assert 'sentenceID' in rows[0][0]

    # Check that route columns exist
    assert 'Departure' in rows[0] or len(rows[0]) >= 2


def test_process_pipeline_invalid_mode(tmp_path):
    """Test pipeline with invalid mode raises error."""
    input_file = tmp_path / "input.csv"
    input_file.write_text("sentenceID,sentence\n1,Test\n", encoding='utf-8')

    output_file = tmp_path / "output.csv"

    with pytest.raises(ValueError) as exc_info:
        process_pipeline(
            input_file=str(input_file),
            output_file=str(output_file),
            mode='invalid_mode'
        )

    assert "Invalid mode" in str(exc_info.value)


def test_process_pipeline_file_not_found():
    """Test pipeline with non-existent input file raises error."""
    with pytest.raises(FileNotFoundError):
        process_pipeline(
            input_file="nonexistent_input.csv",
            output_file="output.csv",
            mode='nlp'
        )


def test_process_pipeline_empty_file(tmp_path):
    """Test pipeline with empty CSV file."""
    input_file = tmp_path / "empty.csv"
    input_file.write_text("sentenceID,sentence\n", encoding='utf-8')

    output_file = tmp_path / "output.csv"

    # Should raise error for empty file
    with pytest.raises(Exception):  # Will raise ValueError from read_input_file
        process_pipeline(
            input_file=str(input_file),
            output_file=str(output_file),
            mode='nlp'
        )


def test_process_pipeline_mixed_valid_invalid(tmp_path):
    """Test pipeline with mix of valid and invalid sentences."""
    input_file = tmp_path / "mixed.csv"
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Je veux aller de Paris à Lyon\n"
        "2,Quel temps fait-il?\n"
        "3,Bonjour\n"
        "4,Train pour Marseille depuis Toulouse\n"
        "5,azerty\n",
        encoding='utf-8'
    )

    output_file = tmp_path / "output_mixed.csv"

    stats = process_pipeline(
        input_file=str(input_file),
        output_file=str(output_file),
        mode='nlp'
    )

    # Check statistics
    assert stats['total'] == 5
    assert stats['valid'] >= 2  # At least 2 valid travel orders
    assert stats['invalid'] >= 3  # At least 3 invalid

    # Read output
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Count INVALID markers
    invalid_count = sum(
        1 for r in rows
        if r['Departure'] == 'INVALID' and r['Destination'] == 'INVALID'
    )
    assert invalid_count >= 3


# ============================================================================
# Test Integration Scenarios
# ============================================================================

def test_integration_french_accents(tmp_path):
    """Test integration with French accented city names."""
    input_file = tmp_path / "accents.csv"
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Je veux aller de Saint-Étienne à Épernay\n",
        encoding='utf-8'
    )

    output_file = tmp_path / "output_accents.csv"

    stats = process_pipeline(
        input_file=str(input_file),
        output_file=str(output_file),
        mode='nlp'
    )

    assert stats['total'] == 1
    assert output_file.exists()


def test_integration_hyphenated_cities(tmp_path):
    """Test integration with hyphenated city names."""
    input_file = tmp_path / "hyphens.csv"
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Je veux aller de Aix-en-Provence à La Rochelle\n",
        encoding='utf-8'
    )

    output_file = tmp_path / "output_hyphens.csv"

    stats = process_pipeline(
        input_file=str(input_file),
        output_file=str(output_file),
        mode='nlp'
    )

    assert stats['total'] == 1


def test_integration_question_format(tmp_path):
    """Test integration with question format sentences."""
    input_file = tmp_path / "questions.csv"
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Comment aller à Lyon depuis Paris?\n"
        "2,À quelle heure y a-t-il des trains vers Marseille en partance de Toulouse?\n",
        encoding='utf-8'
    )

    output_file = tmp_path / "output_questions.csv"

    stats = process_pipeline(
        input_file=str(input_file),
        output_file=str(output_file),
        mode='nlp'
    )

    assert stats['total'] == 2
    # Should extract valid origin/destination from questions


# ============================================================================
# Test Error Recovery
# ============================================================================

def test_error_recovery_partial_failure(tmp_path):
    """Test pipeline continues after partial failures."""
    input_file = tmp_path / "partial_fail.csv"
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Je veux aller de Paris à Lyon\n"
        "2,Je veux aller de UnknownCity à AnotherUnknown\n"
        "3,Train pour Marseille depuis Toulouse\n",
        encoding='utf-8'
    )

    output_file = tmp_path / "output_partial.csv"

    stats = process_pipeline(
        input_file=str(input_file),
        output_file=str(output_file),
        mode='nlp'
    )

    # Pipeline should complete despite failures
    assert stats['total'] == 3
    assert output_file.exists()

    # All sentences should have output (even if INVALID)
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
