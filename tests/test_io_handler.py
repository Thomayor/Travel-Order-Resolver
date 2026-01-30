"""
Unit tests for the I/O Handler module.

Tests cover:
- Reading valid/invalid CSV files
- Writing NLP output (simple format)
- Writing route output (with intermediate stops)
- UTF-8 encoding validation
- Error handling for edge cases
"""

import pytest
import os
import csv
from src.utils.io_handler import (
    read_input_file,
    write_nlp_output,
    write_route_output,
    format_route,
    validate_utf8,
    UTF8ValidationError
)


# ============================================================================
# Test read_input_file
# ============================================================================

def test_read_input_file_valid(tmp_path):
    """Test reading a valid input CSV file."""
    # Create test file
    input_file = tmp_path / "input.csv"
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Je voudrais un billet de Paris à Lyon\n"
        "2,Comment aller à Marseille depuis Toulouse?\n",
        encoding='utf-8'
    )

    # Read file
    data = read_input_file(str(input_file))

    # Assertions
    assert len(data) == 2
    assert data[0]['sentenceID'] == '1'
    assert data[0]['sentence'] == 'Je voudrais un billet de Paris à Lyon'
    assert data[1]['sentenceID'] == '2'
    assert data[1]['sentence'] == 'Comment aller à Marseille depuis Toulouse?'


def test_read_input_file_with_accents(tmp_path):
    """Test reading a file with French accents and special characters."""
    input_file = tmp_path / "input_accents.csv"
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Je veux aller de Aix-en-Provence à Saint-Étienne\n"
        "2,Billet de Béthune à Épernay s'il vous plaît\n",
        encoding='utf-8'
    )

    data = read_input_file(str(input_file))

    assert len(data) == 2
    assert 'Aix-en-Provence' in data[0]['sentence']
    assert 'Saint-Étienne' in data[0]['sentence']
    assert 'Béthune' in data[1]['sentence']
    assert 'Épernay' in data[1]['sentence']


def test_read_input_file_not_found():
    """Test reading a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError) as exc_info:
        read_input_file("nonexistent_file.csv")

    assert "Input file not found" in str(exc_info.value)


def test_read_input_file_missing_columns(tmp_path):
    """Test reading a file with missing required columns raises ValueError."""
    input_file = tmp_path / "invalid.csv"
    input_file.write_text(
        "id,text\n"
        "1,Some text\n",
        encoding='utf-8'
    )

    with pytest.raises(ValueError) as exc_info:
        read_input_file(str(input_file))

    assert "Invalid CSV format" in str(exc_info.value)
    assert "sentenceID" in str(exc_info.value)
    assert "sentence" in str(exc_info.value)


def test_read_input_file_empty_file(tmp_path):
    """Test reading an empty CSV file raises ValueError."""
    input_file = tmp_path / "empty.csv"
    input_file.write_text("", encoding='utf-8')

    with pytest.raises(ValueError) as exc_info:
        read_input_file(str(input_file))

    assert "Empty CSV file" in str(exc_info.value)


def test_read_input_file_no_data_rows(tmp_path):
    """Test reading a CSV with headers but no data rows raises ValueError."""
    input_file = tmp_path / "no_data.csv"
    input_file.write_text(
        "sentenceID,sentence\n",
        encoding='utf-8'
    )

    with pytest.raises(ValueError) as exc_info:
        read_input_file(str(input_file))

    assert "empty (no data rows)" in str(exc_info.value)


def test_read_input_file_invalid_encoding(tmp_path):
    """Test reading a file with non-UTF8 encoding raises UnicodeDecodeError."""
    input_file = tmp_path / "invalid_encoding.csv"
    # Write file with Latin-1 encoding (not UTF-8)
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Texte avec des caractères spéciaux\n",
        encoding='latin-1'
    )

    with pytest.raises(UnicodeDecodeError) as exc_info:
        read_input_file(str(input_file))

    assert "not UTF-8 encoded" in str(exc_info.value)


# ============================================================================
# Test write_nlp_output
# ============================================================================

def test_write_nlp_output_valid(tmp_path):
    """Test writing valid NLP output (simple format)."""
    output_file = tmp_path / "output.csv"
    results = [
        {'sentenceID': '1', 'departure': 'Paris', 'destination': 'Lyon'},
        {'sentenceID': '2', 'departure': 'Toulouse', 'destination': 'Marseille'}
    ]

    write_nlp_output(results, str(output_file))

    # Read and verify output
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]['sentenceID'] == '1'
    assert rows[0]['Departure'] == 'Paris'
    assert rows[0]['Destination'] == 'Lyon'
    assert rows[1]['sentenceID'] == '2'
    assert rows[1]['Departure'] == 'Toulouse'
    assert rows[1]['Destination'] == 'Marseille'


def test_write_nlp_output_with_invalid(tmp_path):
    """Test writing NLP output with INVALID entries."""
    output_file = tmp_path / "output_invalid.csv"
    results = [
        {'sentenceID': '1', 'departure': 'Paris', 'destination': 'Lyon'},
        {'sentenceID': '2', 'departure': 'INVALID', 'destination': 'INVALID'}
    ]

    write_nlp_output(results, str(output_file))

    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[1]['Departure'] == 'INVALID'
    assert rows[1]['Destination'] == 'INVALID'


def test_write_nlp_output_empty_results():
    """Test writing empty results raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        write_nlp_output([], "output.csv")

    assert "Results list is empty" in str(exc_info.value)


def test_write_nlp_output_missing_keys(tmp_path):
    """Test writing results with missing keys raises ValueError."""
    output_file = tmp_path / "output.csv"
    results = [
        {'sentenceID': '1', 'origin': 'Paris'}  # Missing 'departure' and 'destination'
    ]

    with pytest.raises(ValueError) as exc_info:
        write_nlp_output(results, str(output_file))

    assert "Invalid results format" in str(exc_info.value)
    assert "departure" in str(exc_info.value)


def test_write_nlp_output_creates_directory(tmp_path):
    """Test that write_nlp_output creates parent directories if they don't exist."""
    output_file = tmp_path / "subdir" / "output.csv"
    results = [
        {'sentenceID': '1', 'departure': 'Paris', 'destination': 'Lyon'}
    ]

    write_nlp_output(results, str(output_file))

    assert output_file.exists()
    assert output_file.parent.exists()


def test_write_nlp_output_with_accents(tmp_path):
    """Test writing NLP output with French accents."""
    output_file = tmp_path / "output_accents.csv"
    results = [
        {'sentenceID': '1', 'departure': 'Aix-en-Provence', 'destination': 'Saint-Étienne'},
        {'sentenceID': '2', 'departure': 'Béthune', 'destination': 'Épernay'}
    ]

    write_nlp_output(results, str(output_file))

    # Read and verify accents are preserved
    with open(output_file, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'Aix-en-Provence' in content
    assert 'Saint-Étienne' in content
    assert 'Béthune' in content
    assert 'Épernay' in content


# ============================================================================
# Test write_route_output
# ============================================================================

def test_write_route_output_two_cities(tmp_path):
    """Test writing route output with 2 cities (no intermediate stops)."""
    output_file = tmp_path / "route.csv"
    results = [
        {'sentenceID': '1', 'route': ['Paris', 'Lyon']},
        {'sentenceID': '2', 'route': ['Toulouse', 'Marseille']}
    ]

    write_route_output(results, str(output_file))

    # Read and verify output
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Check header
    assert rows[0] == ['sentenceID', 'Departure', 'Destination']

    # Check data
    assert rows[1] == ['1', 'Paris', 'Lyon']
    assert rows[2] == ['2', 'Toulouse', 'Marseille']


def test_write_route_output_three_cities(tmp_path):
    """Test writing route output with 3 cities (1 intermediate stop)."""
    output_file = tmp_path / "route_3.csv"
    results = [
        {'sentenceID': '1', 'route': ['Paris', 'Dijon', 'Lyon']},
        {'sentenceID': '2', 'route': ['Toulouse', 'Montpellier', 'Marseille']}
    ]

    write_route_output(results, str(output_file))

    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Check header
    assert rows[0] == ['sentenceID', 'Departure', 'Step1', 'Destination']

    # Check data
    assert rows[1] == ['1', 'Paris', 'Dijon', 'Lyon']
    assert rows[2] == ['2', 'Toulouse', 'Montpellier', 'Marseille']


def test_write_route_output_five_cities(tmp_path):
    """Test writing route output with 5 cities (3 intermediate stops)."""
    output_file = tmp_path / "route_5.csv"
    results = [
        {'sentenceID': '1', 'route': ['Paris', 'Dijon', 'Lyon', 'Valence', 'Marseille']}
    ]

    write_route_output(results, str(output_file))

    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Check header
    assert rows[0] == ['sentenceID', 'Departure', 'Step1', 'Step2', 'Step3', 'Destination']

    # Check data
    assert rows[1] == ['1', 'Paris', 'Dijon', 'Lyon', 'Valence', 'Marseille']


def test_write_route_output_variable_lengths(tmp_path):
    """Test writing route output with routes of different lengths."""
    output_file = tmp_path / "route_variable.csv"
    results = [
        {'sentenceID': '1', 'route': ['Paris', 'Lyon']},
        {'sentenceID': '2', 'route': ['Toulouse', 'Montpellier', 'Marseille']},
        {'sentenceID': '3', 'route': ['Paris', 'Dijon', 'Lyon', 'Marseille']}
    ]

    write_route_output(results, str(output_file))

    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Header should accommodate the longest route (4 cities)
    assert rows[0] == ['sentenceID', 'Departure', 'Step1', 'Step2', 'Destination']

    # Check data (shorter routes should have empty cells)
    assert rows[1][:3] == ['1', 'Paris', 'Lyon']  # Only 2 cities
    assert rows[2] == ['2', 'Toulouse', 'Montpellier', 'Marseille', '']  # 3 cities
    assert rows[3] == ['3', 'Paris', 'Dijon', 'Lyon', 'Marseille']  # 4 cities


def test_write_route_output_empty_results():
    """Test writing empty route results raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        write_route_output([], "output.csv")

    assert "Results list is empty" in str(exc_info.value)


def test_write_route_output_missing_keys(tmp_path):
    """Test writing route results with missing keys raises ValueError."""
    output_file = tmp_path / "route.csv"
    results = [
        {'sentenceID': '1', 'path': ['Paris', 'Lyon']}  # Missing 'route' key
    ]

    with pytest.raises(ValueError) as exc_info:
        write_route_output(results, str(output_file))

    assert "Invalid results format" in str(exc_info.value)
    assert "route" in str(exc_info.value)


def test_write_route_output_invalid_route_type(tmp_path):
    """Test writing route with non-list route raises ValueError."""
    output_file = tmp_path / "route.csv"
    results = [
        {'sentenceID': '1', 'route': 'Paris,Lyon'}  # String instead of list
    ]

    with pytest.raises(ValueError) as exc_info:
        write_route_output(results, str(output_file))

    assert "'route' must be a list" in str(exc_info.value)


# ============================================================================
# Test format_route
# ============================================================================

def test_format_route_two_cities():
    """Test formatting a route with 2 cities."""
    route = ['Paris', 'Lyon']
    result = format_route(route)
    assert result == 'Paris,Lyon'


def test_format_route_three_cities():
    """Test formatting a route with 3 cities."""
    route = ['Toulouse', 'Montpellier', 'Marseille']
    result = format_route(route)
    assert result == 'Toulouse,Montpellier,Marseille'


def test_format_route_five_cities():
    """Test formatting a route with 5 cities."""
    route = ['Paris', 'Dijon', 'Lyon', 'Valence', 'Marseille']
    result = format_route(route)
    assert result == 'Paris,Dijon,Lyon,Valence,Marseille'


def test_format_route_empty_list():
    """Test formatting an empty route raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        format_route([])

    assert "Route list is empty" in str(exc_info.value)


def test_format_route_not_a_list():
    """Test formatting a non-list route raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        format_route("Paris,Lyon")

    assert "Route must be a list" in str(exc_info.value)


# ============================================================================
# Test validate_utf8
# ============================================================================

def test_validate_utf8_valid_file(tmp_path):
    """Test validating a valid UTF-8 file succeeds."""
    test_file = tmp_path / "valid_utf8.csv"
    test_file.write_text(
        "sentenceID,sentence\n"
        "1,Je veux aller de Paris à Lyon\n"
        "2,Billet de Béthune à Épernay\n",
        encoding='utf-8'
    )

    # Should not raise any exception
    validate_utf8(str(test_file))


def test_validate_utf8_file_not_found():
    """Test validating a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError) as exc_info:
        validate_utf8("nonexistent.csv")

    assert "File not found" in str(exc_info.value)


def test_validate_utf8_invalid_encoding(tmp_path):
    """Test validating a file with invalid encoding raises UTF8ValidationError."""
    test_file = tmp_path / "invalid_utf8.csv"
    # Write with Latin-1 encoding
    test_file.write_text(
        "sentenceID,sentence\n"
        "1,Texte avec caractères spéciaux\n",
        encoding='latin-1'
    )

    with pytest.raises(UTF8ValidationError) as exc_info:
        validate_utf8(str(test_file))

    assert "not properly UTF-8 encoded" in str(exc_info.value)


def test_validate_utf8_with_accents(tmp_path):
    """Test validating a UTF-8 file with French accents succeeds."""
    test_file = tmp_path / "accents.csv"
    test_file.write_text(
        "sentenceID,sentence\n"
        "1,Je veux aller à Aix-en-Provence depuis Saint-Étienne\n"
        "2,Billet de Béthune à Épernay s'il vous plaît\n",
        encoding='utf-8'
    )

    # Should not raise any exception
    validate_utf8(str(test_file))


def test_validate_utf8_empty_file(tmp_path):
    """Test validating an empty UTF-8 file succeeds."""
    test_file = tmp_path / "empty.csv"
    test_file.write_text("", encoding='utf-8')

    # Should not raise any exception (empty file is valid UTF-8)
    validate_utf8(str(test_file))


# ============================================================================
# Integration tests
# ============================================================================

def test_full_workflow_nlp_output(tmp_path):
    """Test complete workflow: read input -> write NLP output."""
    # Create input file
    input_file = tmp_path / "input.csv"
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Je voudrais un billet de Paris à Lyon\n"
        "2,Comment aller à Marseille depuis Toulouse?\n",
        encoding='utf-8'
    )

    # Read input
    data = read_input_file(str(input_file))

    # Simulate NLP extraction (simplified)
    results = [
        {'sentenceID': data[0]['sentenceID'], 'departure': 'Paris', 'destination': 'Lyon'},
        {'sentenceID': data[1]['sentenceID'], 'departure': 'Toulouse', 'destination': 'Marseille'}
    ]

    # Write output
    output_file = tmp_path / "output.csv"
    write_nlp_output(results, str(output_file))

    # Verify output exists and is valid
    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]['Departure'] == 'Paris'
    assert rows[1]['Destination'] == 'Marseille'


def test_full_workflow_route_output(tmp_path):
    """Test complete workflow: read input -> write route output."""
    # Create input file
    input_file = tmp_path / "input.csv"
    input_file.write_text(
        "sentenceID,sentence\n"
        "1,Je veux aller de Paris à Marseille\n",
        encoding='utf-8'
    )

    # Read input
    data = read_input_file(str(input_file))

    # Simulate pathfinding (simplified)
    results = [
        {'sentenceID': data[0]['sentenceID'], 'route': ['Paris', 'Lyon', 'Marseille']}
    ]

    # Write output
    output_file = tmp_path / "output.csv"
    write_route_output(results, str(output_file))

    # Verify output
    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert rows[0] == ['sentenceID', 'Departure', 'Step1', 'Destination']
    assert rows[1] == ['1', 'Paris', 'Lyon', 'Marseille']
