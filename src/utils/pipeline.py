"""
End-to-End Pipeline for Travel Order Resolver

This module integrates the NLP extraction module with the pathfinding module
to provide a complete travel order processing pipeline.

Pipeline Flow:
1. Read input CSV file
2. For each sentence:
   - Extract origin and destination (NLP)
   - Map city names to UIC station codes
   - Find route using pathfinding (if valid)
   - Handle errors at each step
3. Write results to output CSV

Functions:
    process_pipeline: Main entry point for end-to-end processing
    process_single_sentence: Process one sentence through the pipeline
    handle_errors: Centralized error handling
    map_city_to_uic: Map city name to station UIC code

Ticket: KAN-XX - Integrate NLP and pathfinding modules
"""

import csv
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# NLP module imports
from src.nlp.baseline import BaselineExtractor, load_extractor
from src.nlp.preprocessing import preprocess_for_matching

# Pathfinding module imports
from src.pathfinding.graph_loader import get_or_build_graph, get_station_info
from src.pathfinding.algorithms import dijkstra, InvalidStationError, NoPathError

# I/O module imports
from src.utils.io_handler import read_input_file, write_nlp_output, write_route_output


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class CityMappingError(PipelineError):
    """Raised when city name cannot be mapped to UIC code."""
    pass


def load_city_mapping(mapping_file: str = "data/processed/sncf/city_station_mapping.csv") -> Dict[str, str]:
    """
    Load city name to UIC code mapping from CSV.

    The mapping file contains normalized city names mapped to their
    corresponding UIC station codes. If a city has multiple stations,
    the first one in the file is used.

    Args:
        mapping_file: Path to city_station_mapping.csv

    Returns:
        Dictionary mapping normalized city name to UIC code

    Example:
        >>> mapping = load_city_mapping()
        >>> print(mapping['paris'])
        '87686006'  # Paris Gare de Lyon
    """
    mapping = {}

    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                city = row['city_name_normalized'].strip().lower()
                uic = row['uic_code'].split(';')[0].strip()  # Take first UIC if multiple

                # Only add if not already in mapping (prefer first occurrence)
                if city not in mapping:
                    mapping[city] = uic

        logger.info(f"Loaded {len(mapping)} city-to-station mappings")
        return mapping

    except FileNotFoundError:
        logger.error(f"City mapping file not found: {mapping_file}")
        raise CityMappingError(f"City mapping file not found: {mapping_file}")

    except Exception as e:
        logger.error(f"Error loading city mapping: {e}")
        raise CityMappingError(f"Error loading city mapping: {e}")


def map_city_to_uic(city_name: str, city_mapping: Dict[str, str]) -> Optional[str]:
    """
    Map city name to UIC station code.

    This function normalizes the city name (lowercase, accents removed)
    and looks it up in the city mapping dictionary.

    Args:
        city_name: City name as extracted by NLP module
        city_mapping: Dictionary from load_city_mapping()

    Returns:
        UIC code as string, or None if not found

    Example:
        >>> mapping = load_city_mapping()
        >>> uic = map_city_to_uic("Paris", mapping)
        >>> print(uic)
        '87686006'
        >>> uic = map_city_to_uic("ParisXYZ", mapping)
        >>> print(uic)
        None
    """
    if not city_name:
        return None

    # Normalize city name (same as NLP preprocessing)
    normalized = preprocess_for_matching(city_name)

    # Look up in mapping
    return city_mapping.get(normalized)


def handle_errors(sentence_id: str, error: Exception) -> Dict:
    """
    Centralized error handling for pipeline.

    This function logs errors and returns a standardized error result
    dictionary that can be used for output formatting.

    Args:
        sentence_id: Unique identifier for the sentence
        error: Exception that occurred

    Returns:
        Dictionary with error information:
        {
            'sentence_id': str,
            'origin': None,
            'destination': None,
            'valid': False,
            'route': ['INVALID', 'INVALID'],
            'error_type': str,
            'error_message': str
        }

    Example:
        >>> try:
        ...     # Some operation
        ...     raise ValueError("Invalid input")
        ... except Exception as e:
        ...     result = handle_errors("123", e)
        >>> print(result['error_type'])
        'ValueError'
    """
    error_type = type(error).__name__
    error_message = str(error)

    logger.error(f"[{sentence_id}] {error_type}: {error_message}")

    return {
        'sentence_id': sentence_id,
        'origin': None,
        'destination': None,
        'valid': False,
        'route': ['INVALID', 'INVALID'],
        'path': [],
        'total_time': 0,
        'error_type': error_type,
        'error_message': error_message,
        'success': False
    }


def process_single_sentence(
    sentence_id: str,
    sentence: str,
    extractor: BaselineExtractor,
    city_mapping: Dict[str, str],
    graph,
    include_route: bool = False
) -> Dict:
    """
    Process a single sentence through the complete pipeline.

    Pipeline steps:
    1. Extract origin and destination using NLP
    2. Map city names to UIC codes
    3. Find route using pathfinding
    4. Return structured result

    Args:
        sentence_id: Unique identifier for the sentence
        sentence: Input sentence text
        extractor: BaselineExtractor instance
        city_mapping: City to UIC code mapping
        graph: NetworkX graph with railway network
        include_route: If True, compute full route with intermediate stops

    Returns:
        Dictionary with processing results:
        {
            'sentence_id': str,
            'sentence': str,
            'origin': Optional[str],           # City name from NLP
            'destination': Optional[str],      # City name from NLP
            'origin_uic': Optional[str],       # UIC code for origin
            'destination_uic': Optional[str],  # UIC code for destination
            'valid': bool,                     # True if valid travel order
            'route': List[str],                # [origin, dest] or [origin, step1, ..., dest]
            'path': List[str],                 # UIC codes path
            'total_time': float,               # Travel time in minutes
            'success': bool,                   # True if route found
            'error_type': Optional[str],       # Error type if failed
            'error_message': Optional[str]     # Error message if failed
        }

    Example:
        >>> extractor = load_extractor()
        >>> mapping = load_city_mapping()
        >>> graph = get_or_build_graph()
        >>> result = process_single_sentence("1", "Je veux aller de Paris à Lyon",
        ...                                   extractor, mapping, graph)
        >>> print(result['valid'], result['success'])
        True True
    """
    logger.info(f"[{sentence_id}] Processing: {sentence}")

    result = {
        'sentence_id': sentence_id,
        'sentence': sentence,
        'origin': None,
        'destination': None,
        'origin_uic': None,
        'destination_uic': None,
        'valid': False,
        'route': ['INVALID', 'INVALID'],
        'path': [],
        'total_time': 0,
        'success': False,
        'error_type': None,
        'error_message': None
    }

    try:
        # Step 1: Extract origin and destination using NLP
        nlp_result = extractor.extract(sentence)
        result['origin'] = nlp_result.get('origin')
        result['destination'] = nlp_result.get('destination')
        result['valid'] = nlp_result.get('valid', False)

        logger.debug(f"[{sentence_id}] NLP extraction: origin={result['origin']}, dest={result['destination']}, valid={result['valid']}")

        # If not a valid travel order, return early
        if not result['valid'] or not result['origin'] or not result['destination']:
            logger.info(f"[{sentence_id}] Invalid travel order or missing locations")
            result['route'] = ['INVALID', 'INVALID']
            return result

        # Step 2: Map city names to UIC codes
        origin_uic = map_city_to_uic(result['origin'], city_mapping)
        dest_uic = map_city_to_uic(result['destination'], city_mapping)

        result['origin_uic'] = origin_uic
        result['destination_uic'] = dest_uic

        # Check if mapping was successful
        if not origin_uic:
            logger.warning(f"[{sentence_id}] Origin city '{result['origin']}' not found in station mapping")
            result['error_type'] = 'CityMappingError'
            result['error_message'] = f"Origin city '{result['origin']}' not found in station database"
            return result

        if not dest_uic:
            logger.warning(f"[{sentence_id}] Destination city '{result['destination']}' not found in station mapping")
            result['error_type'] = 'CityMappingError'
            result['error_message'] = f"Destination city '{result['destination']}' not found in station database"
            return result

        logger.debug(f"[{sentence_id}] UIC mapping: {origin_uic} -> {dest_uic}")

        # Step 3: Find route using pathfinding
        if include_route:
            # Find full path with intermediate stops
            path, total_time = dijkstra(graph, origin_uic, dest_uic)

            # Convert UIC codes to city names for route
            route = []
            for uic in path:
                station_info = get_station_info(graph, uic)
                if station_info:
                    # Use city name, not station name
                    route.append(station_info.get('city_name', station_info['station_name']))
                else:
                    route.append(uic)  # Fallback to UIC if info not found

            result['route'] = route
            result['path'] = path
            result['total_time'] = total_time
            result['success'] = True

            logger.info(f"[{sentence_id}] Route found: {' → '.join(route[:3])}{'...' if len(route) > 3 else ''} ({total_time:.0f} min)")

        else:
            # Simple validation: check if path exists (for NLP-only output)
            try:
                path, total_time = dijkstra(graph, origin_uic, dest_uic)
                result['route'] = [result['origin'], result['destination']]
                result['path'] = path
                result['total_time'] = total_time
                result['success'] = True

                logger.info(f"[{sentence_id}] Path exists: {result['origin']} → {result['destination']} ({total_time:.0f} min)")

            except (InvalidStationError, NoPathError) as e:
                # Path doesn't exist, but we still output the NLP result
                logger.warning(f"[{sentence_id}] No path found, but outputting NLP result: {e}")
                result['route'] = [result['origin'], result['destination']]
                result['success'] = False
                result['error_type'] = type(e).__name__
                result['error_message'] = str(e)

    except InvalidStationError as e:
        result['error_type'] = 'InvalidStationError'
        result['error_message'] = str(e)
        logger.error(f"[{sentence_id}] Invalid station: {e}")

    except NoPathError as e:
        result['error_type'] = 'NoPathError'
        result['error_message'] = str(e)
        logger.error(f"[{sentence_id}] No path found: {e}")

    except UnicodeDecodeError as e:
        result['error_type'] = 'EncodingError'
        result['error_message'] = f"Encoding error: {e}"
        logger.error(f"[{sentence_id}] Encoding error: {e}")

    except Exception as e:
        result['error_type'] = type(e).__name__
        result['error_message'] = str(e)
        logger.error(f"[{sentence_id}] Unexpected error: {e}", exc_info=True)

    return result


def process_pipeline(
    input_file: str,
    output_file: str,
    mode: str = 'nlp',
    cache_path: str = "models/train_network.pkl",
    stations_file: str = "data/processed/sncf/stations_clean.csv",
    connections_file: str = "data/processed/sncf/connections_final_fixed.csv",
    mapping_file: str = "data/processed/sncf/city_station_mapping.csv"
) -> Dict[str, int]:
    """
    Main pipeline entry point: process input file and write results.

    This function orchestrates the complete travel order processing pipeline:
    1. Load NLP extractor, graph, and city mapping
    2. Read input CSV file
    3. Process each sentence
    4. Write results to output CSV

    Args:
        input_file: Path to input CSV (sentenceID,sentence)
        output_file: Path to output CSV
        mode: Processing mode:
            - 'nlp': Only NLP extraction (sentenceID,Departure,Destination)
            - 'route': Full route with pathfinding (sentenceID,Departure,Step1,...,Destination)
        cache_path: Path to cached graph (optional)
        stations_file: Path to stations CSV (used if graph not cached)
        connections_file: Path to connections CSV (used if graph not cached)
        mapping_file: Path to city-to-station mapping CSV

    Returns:
        Dictionary with processing statistics:
        {
            'total': int,           # Total sentences processed
            'valid': int,           # Valid travel orders
            'invalid': int,         # Invalid orders
            'success': int,         # Successful route finding
            'errors': int,          # Errors during processing
            'nlp_errors': int,      # NLP extraction failures
            'mapping_errors': int,  # City mapping failures
            'pathfinding_errors': int  # Pathfinding failures
        }

    Raises:
        FileNotFoundError: If input file not found
        ValueError: If invalid mode specified
        PipelineError: If critical error during processing

    Example:
        >>> stats = process_pipeline(
        ...     input_file='data/input.csv',
        ...     output_file='data/output.csv',
        ...     mode='nlp'
        ... )
        >>> print(f"Processed {stats['total']} sentences, {stats['success']} successful")
    """
    logger.info("=" * 70)
    logger.info("TRAVEL ORDER RESOLVER - PIPELINE")
    logger.info("=" * 70)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Mode: {mode}")
    logger.info("")

    # Validate mode
    if mode not in ['nlp', 'route']:
        raise ValueError(f"Invalid mode '{mode}'. Must be 'nlp' or 'route'")

    # Initialize statistics
    stats = {
        'total': 0,
        'valid': 0,
        'invalid': 0,
        'success': 0,
        'errors': 0,
        'nlp_errors': 0,
        'mapping_errors': 0,
        'pathfinding_errors': 0
    }

    try:
        # Step 1: Load resources
        logger.info("Loading resources...")

        # Load NLP extractor
        logger.info("  Loading NLP extractor...")
        extractor = load_extractor()

        # Load city mapping
        logger.info("  Loading city-to-station mapping...")
        city_mapping = load_city_mapping(mapping_file)

        # Load graph
        logger.info("  Loading railway network graph...")
        graph = get_or_build_graph(
            cache_path=cache_path,
            stations_file=stations_file,
            connections_file=connections_file
        )

        logger.info("✓ Resources loaded successfully")
        logger.info("")

        # Step 2: Read input file
        logger.info("Reading input file...")
        input_data = read_input_file(input_file)
        stats['total'] = len(input_data)
        logger.info(f"✓ Read {stats['total']} sentences")
        logger.info("")

        # Step 3: Process each sentence
        logger.info("Processing sentences...")
        results = []

        for row in input_data:
            sentence_id = row['sentenceID']
            sentence = row['sentence']

            # Process through pipeline
            result = process_single_sentence(
                sentence_id=sentence_id,
                sentence=sentence,
                extractor=extractor,
                city_mapping=city_mapping,
                graph=graph,
                include_route=(mode == 'route')
            )

            results.append(result)

            # Update statistics
            if result['valid']:
                stats['valid'] += 1
            else:
                stats['invalid'] += 1

            if result['success']:
                stats['success'] += 1

            if result['error_type']:
                stats['errors'] += 1

                # Classify error type
                if not result['valid']:
                    stats['nlp_errors'] += 1
                elif 'Mapping' in result['error_type']:
                    stats['mapping_errors'] += 1
                else:
                    stats['pathfinding_errors'] += 1

        logger.info("")
        logger.info("✓ Processing complete")
        logger.info("")

        # Step 4: Write results
        logger.info("Writing results...")

        if mode == 'nlp':
            # Simple NLP output format
            nlp_results = [
                {
                    'sentenceID': r['sentence_id'],
                    'departure': r['origin'] if r['origin'] else 'INVALID',
                    'destination': r['destination'] if r['destination'] else 'INVALID'
                }
                for r in results
            ]
            write_nlp_output(nlp_results, output_file)

        elif mode == 'route':
            # Full route output format
            route_results = [
                {
                    'sentenceID': r['sentence_id'],
                    'route': r['route']
                }
                for r in results
            ]
            write_route_output(route_results, output_file)

        logger.info(f"✓ Results written to: {output_file}")
        logger.info("")

        # Step 5: Print statistics
        logger.info("=" * 70)
        logger.info("PROCESSING STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total sentences:        {stats['total']}")
        logger.info(f"Valid travel orders:    {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
        logger.info(f"Invalid orders:         {stats['invalid']} ({stats['invalid']/stats['total']*100:.1f}%)")
        logger.info(f"Successful routes:      {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
        logger.info(f"Total errors:           {stats['errors']}")
        logger.info(f"  - NLP errors:         {stats['nlp_errors']}")
        logger.info(f"  - Mapping errors:     {stats['mapping_errors']}")
        logger.info(f"  - Pathfinding errors: {stats['pathfinding_errors']}")
        logger.info("=" * 70)

        return stats

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise

    except Exception as e:
        logger.error(f"Critical pipeline error: {e}", exc_info=True)
        raise PipelineError(f"Pipeline failed: {e}") from e


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m src.utils.pipeline <input_file> <output_file> [mode]")
        print("  mode: 'nlp' (default) or 'route'")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else 'nlp'

    try:
        stats = process_pipeline(input_file, output_file, mode)
        print("\n✓ Pipeline completed successfully!")
        sys.exit(0)

    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        sys.exit(1)
