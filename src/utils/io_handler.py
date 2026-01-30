"""
I/O Handler Module for Travel Order Resolver

This module provides input/output utilities for reading travel order requests
and writing extraction results to CSV files with proper UTF-8 encoding.

Functions:
    read_input_file: Read and parse input CSV file
    write_nlp_output: Write NLP extraction results (Departure, Destination)
    write_route_output: Write complete route with intermediate stops
    format_route: Format a route list as comma-separated string
    validate_utf8: Validate UTF-8 encoding of a file
"""

import csv
import os
from typing import List, Dict


class UTF8ValidationError(Exception):
    """Exception raised when a file is not properly UTF-8 encoded."""
    pass


def validate_utf8(file_path: str) -> None:
    """
    Validate that a file is properly UTF-8 encoded.

    This function attempts to read the entire file with UTF-8 encoding.
    If decoding fails, it raises a UTF8ValidationError with details about
    the encoding issue.

    Args:
        file_path: Path to the file to validate

    Raises:
        FileNotFoundError: If the file does not exist
        UTF8ValidationError: If the file is not properly UTF-8 encoded

    Example:
        >>> validate_utf8('data/input.csv')  # Raises exception if not UTF-8
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read entire file to detect encoding issues
            f.read()
    except UnicodeDecodeError as e:
        raise UTF8ValidationError(
            f"File '{file_path}' is not properly UTF-8 encoded. "
            f"Error at byte position {e.start}: {e.reason}. "
            f"Please ensure the file is saved with UTF-8 encoding."
        ) from e


def read_input_file(file_path: str) -> List[Dict[str, str]]:
    """
    Read and parse a CSV input file containing travel order sentences.

    Expected CSV format (UTF-8 encoded):
        sentenceID,sentence
        1,"Je voudrais un billet de Paris à Lyon"
        2,"Comment aller à Marseille depuis Toulouse?"

    Args:
        file_path: Path to the input CSV file

    Returns:
        List of dictionaries with keys 'sentenceID' and 'sentence'

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the CSV format is invalid (missing required columns)
        UnicodeDecodeError: If the file is not UTF-8 encoded

    Example:
        >>> data = read_input_file('input.csv')
        >>> print(data[0])
        {'sentenceID': '1', 'sentence': 'Je voudrais un billet de Paris à Lyon'}
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)

            # Validate required columns exist
            if reader.fieldnames is None:
                raise ValueError(f"Empty CSV file: {file_path}")

            required_columns = {'sentenceID', 'sentence'}
            if not required_columns.issubset(reader.fieldnames):
                raise ValueError(
                    f"Invalid CSV format in '{file_path}'. "
                    f"Required columns: {required_columns}, "
                    f"Found columns: {set(reader.fieldnames)}"
                )

            # Read all rows
            data = list(reader)

            if not data:
                raise ValueError(f"CSV file is empty (no data rows): {file_path}")

            return data

    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            e.encoding,
            e.object,
            e.start,
            e.end,
            f"File '{file_path}' is not UTF-8 encoded. {e.reason}"
        ) from e


def write_nlp_output(results: List[Dict[str, str]], file_path: str) -> None:
    """
    Write NLP extraction results to a CSV file (simple format).

    Output format (UTF-8 encoded):
        sentenceID,Departure,Destination
        1,Paris,Lyon
        2,Toulouse,Marseille
        3,INVALID,INVALID

    Args:
        results: List of dictionaries with keys 'sentenceID', 'departure', 'destination'
        file_path: Path to the output CSV file

    Raises:
        ValueError: If results list is empty or missing required keys
        OSError: If the file cannot be written

    Example:
        >>> results = [
        ...     {'sentenceID': '1', 'departure': 'Paris', 'destination': 'Lyon'},
        ...     {'sentenceID': '2', 'departure': 'INVALID', 'destination': 'INVALID'}
        ... ]
        >>> write_nlp_output(results, 'output.csv')
    """
    if not results:
        raise ValueError("Results list is empty, nothing to write")

    # Validate first row has required keys
    required_keys = {'sentenceID', 'departure', 'destination'}
    if not required_keys.issubset(results[0].keys()):
        raise ValueError(
            f"Invalid results format. Required keys: {required_keys}, "
            f"Found keys: {set(results[0].keys())}"
        )

    # Create parent directory if it doesn't exist
    parent_dir = os.path.dirname(file_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    # Write CSV with UTF-8 encoding
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['sentenceID', 'Departure', 'Destination']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        for result in results:
            writer.writerow({
                'sentenceID': result['sentenceID'],
                'Departure': result['departure'],
                'Destination': result['destination']
            })


def write_route_output(results: List[Dict[str, any]], file_path: str) -> None:
    """
    Write complete route results to a CSV file (with intermediate stops).

    Output format (UTF-8 encoded):
        sentenceID,Departure,Step1,Step2,...,Destination
        1,Paris,Lyon
        2,Toulouse,Montpellier,Marseille
        3,Paris,Dijon,Lyon,Marseille

    Args:
        results: List of dictionaries with keys 'sentenceID' and 'route' (list of cities)
        file_path: Path to the output CSV file

    Raises:
        ValueError: If results list is empty or missing required keys
        OSError: If the file cannot be written

    Example:
        >>> results = [
        ...     {'sentenceID': '1', 'route': ['Paris', 'Lyon']},
        ...     {'sentenceID': '2', 'route': ['Toulouse', 'Montpellier', 'Marseille']}
        ... ]
        >>> write_route_output(results, 'output.csv')
    """
    if not results:
        raise ValueError("Results list is empty, nothing to write")

    # Validate first row has required keys
    required_keys = {'sentenceID', 'route'}
    if not required_keys.issubset(results[0].keys()):
        raise ValueError(
            f"Invalid results format. Required keys: {required_keys}, "
            f"Found keys: {set(results[0].keys())}"
        )

    # Validate route is a list
    if not isinstance(results[0]['route'], list):
        raise ValueError(
            f"'route' must be a list of cities, got {type(results[0]['route'])}"
        )

    # Create parent directory if it doesn't exist
    parent_dir = os.path.dirname(file_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    # Determine maximum route length to create column headers
    max_route_length = max(len(result['route']) for result in results)

    # Build fieldnames: sentenceID, Departure, Step1, Step2, ..., Destination
    # Note: For a 2-city route (Paris → Lyon), we only need Departure and Destination
    # For 3+ cities, we need intermediate steps
    if max_route_length == 2:
        fieldnames = ['sentenceID', 'Departure', 'Destination']
    else:
        fieldnames = ['sentenceID', 'Departure']
        # Add intermediate steps (Step1, Step2, ..., Step(n-2))
        for i in range(1, max_route_length - 1):
            fieldnames.append(f'Step{i}')
        fieldnames.append('Destination')

    # Write CSV with UTF-8 encoding
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)

        # Write header
        writer.writerow(fieldnames)

        # Write each route
        for result in results:
            route = result['route']
            route_str = format_route(route)
            row = [result['sentenceID']] + route

            # Pad with empty strings if route is shorter than max_route_length
            while len(row) < len(fieldnames):
                row.append('')

            writer.writerow(row)


def format_route(route: List[str]) -> str:
    """
    Format a route (list of cities) as a comma-separated string.

    Args:
        route: List of city names representing a route

    Returns:
        Comma-separated string of cities

    Raises:
        ValueError: If route is empty

    Example:
        >>> format_route(['Paris', 'Lyon'])
        'Paris,Lyon'
        >>> format_route(['Toulouse', 'Montpellier', 'Marseille'])
        'Toulouse,Montpellier,Marseille'
    """
    if not route:
        raise ValueError("Route list is empty, cannot format")

    if not isinstance(route, list):
        raise ValueError(f"Route must be a list, got {type(route)}")

    return ','.join(route)
