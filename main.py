#!/usr/bin/env python3
"""
Travel Order Resolver - Main CLI Entry Point

This is the main command-line interface for the Travel Order Resolver system.
It integrates NLP extraction with pathfinding to process French travel orders.

Usage:
    python main.py --input input.csv --output output.csv
    python main.py --input input.csv --output output.csv --mode full-pipeline
    python main.py --input input.csv --output output.csv --model camembert
    python main.py --interactive
    python main.py --interactive --model camembert

Arguments:
    --input, -i         Input CSV file (sentenceID,sentence)
    --output, -o        Output CSV file
    --mode, -m          Processing mode: nlp-only or full-pipeline (default: nlp-only)
    --model             NLP model: baseline or camembert (default: baseline)
    --model-path        Path to CamemBERT model directory (default: models/camembert-ner)
    --interactive, -I   Interactive mode: enter sentences directly in terminal
    --verbose, -v       Enable verbose logging
    --help, -h          Show this help message

Examples:
    # Baseline extraction
    python main.py -i data/input.csv -o data/output.csv

    # CamemBERT extraction (96.76% accuracy)
    python main.py -i data/input.csv -o data/output.csv --model camembert

    # Full pipeline with CamemBERT
    python main.py -i data/input.csv -o data/output.csv --model camembert -m full-pipeline

    # Interactive mode
    python main.py --interactive
    python main.py -I --model camembert
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.pipeline import (
    process_pipeline, load_nlp_model, _extract, DEFAULT_MODEL_PATH,
    load_city_mapping, map_city_to_uic
)
from src.pathfinding.graph_loader import get_or_build_graph, get_station_info
from src.pathfinding.algorithms import dijkstra, InvalidStationError, NoPathError


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        verbose: Enable verbose (DEBUG) logging

    Returns:
        Configured logger instance
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create application logger
    logger = logging.getLogger('travel_order_resolver')
    logger.setLevel(log_level)

    return logger


def validate_input_file(input_file: str, logger: logging.Logger) -> bool:
    """
    Validate that input file exists and is readable.

    Args:
        input_file: Path to input file
        logger: Logger instance

    Returns:
        True if valid, False otherwise
    """
    input_path = Path(input_file)

    # Check if file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_file}")
        return False

    # Check if file is readable
    if not input_path.is_file():
        logger.error(f"Input path is not a file: {input_file}")
        return False

    # Check file extension
    if input_path.suffix.lower() != '.csv':
        logger.warning(f"Input file does not have .csv extension: {input_file}")
        logger.warning("Proceeding anyway, but ensure file is CSV format")

    # Check if file is empty
    if input_path.stat().st_size == 0:
        logger.error(f"Input file is empty: {input_file}")
        return False

    logger.info(f"Input file validated: {input_file}")
    return True


def validate_output_file(output_file: str, logger: logging.Logger) -> bool:
    """
    Validate that output file path is writable.

    Args:
        output_file: Path to output file
        logger: Logger instance

    Returns:
        True if valid, False otherwise
    """
    output_path = Path(output_file)

    # Check if parent directory exists
    parent_dir = output_path.parent
    if not parent_dir.exists():
        logger.info(f"Creating output directory: {parent_dir}")
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}")
            return False

    # Check if output file already exists
    if output_path.exists():
        logger.warning(f"Output file already exists and will be overwritten: {output_file}")

    # Check file extension
    if output_path.suffix.lower() != '.csv':
        logger.warning(f"Output file does not have .csv extension: {output_file}")

    logger.info(f"Output file path validated: {output_file}")
    return True


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Travel Order Resolver - Process French travel orders with NLP and pathfinding',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract origin and destination only
  python main.py -i data/input.csv -o data/output.csv

  # Find complete routes with pathfinding
  python main.py -i data/input.csv -o data/output.csv -m full-pipeline

  # Verbose mode for debugging
  python main.py -i data/input.csv -o data/output.csv -v

For more information, see docs/PIPELINE_INTEGRATION.md
        """
    )

    # Input/output arguments (required unless --interactive)
    parser.add_argument(
        '--input', '-i',
        type=str,
        default=None,
        metavar='FILE',
        help='Input CSV file (format: sentenceID,sentence)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        metavar='FILE',
        help='Output CSV file'
    )

    # Optional arguments
    parser.add_argument(
        '--mode', '-m',
        type=str,
        choices=['nlp-only', 'full-pipeline'],
        default='nlp-only',
        help='Processing mode (default: nlp-only)'
    )

    parser.add_argument(
        '--model',
        type=str,
        choices=['baseline', 'camembert'],
        default='baseline',
        help='NLP model to use (default: baseline)'
    )

    parser.add_argument(
        '--model-path',
        type=str,
        default=DEFAULT_MODEL_PATH,
        metavar='PATH',
        help=f'Path to CamemBERT model directory (default: {DEFAULT_MODEL_PATH})'
    )

    parser.add_argument(
        '--interactive', '-I',
        action='store_true',
        help='Interactive mode: enter sentences directly in terminal (no CSV needed)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Travel Order Resolver v1.0.0'
    )

    return parser.parse_args()


def map_mode_to_pipeline(cli_mode: str) -> str:
    """
    Map CLI mode to pipeline mode.

    Args:
        cli_mode: CLI mode (nlp-only or full-pipeline)

    Returns:
        Pipeline mode (nlp or route)
    """
    mode_mapping = {
        'nlp-only': 'nlp',
        'full-pipeline': 'route'
    }
    return mode_mapping[cli_mode]


def run_interactive(model_type: str, model_path: str, logger: logging.Logger) -> int:
    """
    Interactive mode: process sentences entered directly in the terminal.
    Shows NLP extraction AND full train route.

    Args:
        model_type: 'baseline' or 'camembert'
        model_path: Path to CamemBERT model (only used when model_type='camembert')
        logger: Logger instance

    Returns:
        Exit code (0 for success, 1 for error)
    """
    print(f"Loading NLP model: {model_type}...")
    try:
        model = load_nlp_model(model_type, model_path)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        print(f"\n[ERROR] Failed to load model: {e}")
        return 1

    print("Loading railway network...")
    try:
        city_mapping = load_city_mapping()
        graph = get_or_build_graph()
    except Exception as e:
        logger.error(f"Failed to load railway network: {e}")
        print(f"\n[ERROR] Failed to load railway network: {e}")
        return 1

    print(f"\nReady ({model_type} model + SNCF network loaded)")
    print("Enter French travel order sentences.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            sentence = input("Sentence: ").strip()

            if not sentence:
                continue

            if sentence.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            result = _extract(sentence, model, model_type)
            origin = result.get('origin')
            destination = result.get('destination')
            valid = result.get('valid', False)

            print()
            if not valid or not origin or not destination:
                print("  Result: INVALID (not a travel order or missing cities)")
                print()
                continue

            print(f"  Origin:      {origin}")
            print(f"  Destination: {destination}")

            # Pathfinding
            origin_uic = map_city_to_uic(origin, city_mapping)
            dest_uic = map_city_to_uic(destination, city_mapping)

            if not origin_uic:
                print(f"  Route:  [city '{origin}' not found in SNCF network]")
            elif not dest_uic:
                print(f"  Route:  [city '{destination}' not found in SNCF network]")
            else:
                try:
                    path, total_time = dijkstra(graph, origin_uic, dest_uic)
                    # Convert UIC codes to city names
                    route = []
                    for uic in path:
                        info = get_station_info(graph, uic)
                        if info:
                            route.append(info.get('city_name', info['station_name']))
                        else:
                            route.append(uic)
                    print(f"  Route:  {' -> '.join(route)}")
                    print(f"  Time:   {total_time:.0f} min")
                except (InvalidStationError, NoPathError) as e:
                    print(f"  Route:  [no path found: {e}]")

            print()

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}\n")

    return 0


def main() -> int:
    """
    Main entry point for the CLI application.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(args.verbose)

    # Print header
    print("=" * 70)
    print("TRAVEL ORDER RESOLVER")
    print("=" * 70)
    print()

    # Interactive mode: no CSV needed
    if args.interactive:
        return run_interactive(args.model, args.model_path, logger)

    # Validate input/output for CSV mode
    if not args.input or not args.output:
        logger.error("--input and --output are required unless --interactive is used")
        print("[ERROR] --input and --output are required unless --interactive is used")
        return 1

    logger.info("Validating input file...")
    if not validate_input_file(args.input, logger):
        logger.error("Input validation failed")
        return 1

    logger.info("Validating output path...")
    if not validate_output_file(args.output, logger):
        logger.error("Output validation failed")
        return 1

    # Map CLI mode to pipeline mode
    pipeline_mode = map_mode_to_pipeline(args.mode)

    # Print configuration
    print(f"Configuration:")
    print(f"  Input:       {args.input}")
    print(f"  Output:      {args.output}")
    print(f"  Mode:        {args.mode} ({pipeline_mode})")
    print(f"  NLP model:   {args.model}")
    if args.model == 'camembert':
        print(f"  Model path:  {args.model_path}")
    print(f"  Verbose:     {args.verbose}")
    print()

    # Run pipeline
    try:
        logger.info(f"Starting pipeline in {args.mode} mode with {args.model} model...")

        stats = process_pipeline(
            input_file=args.input,
            output_file=args.output,
            mode=pipeline_mode,
            nlp_model=args.model,
            model_path=args.model_path,
        )

        # Print success message
        print()
        print("=" * 70)
        print("PROCESSING COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print()
        print(f"Results:")
        print(f"  Total sentences:  {stats['total']}")
        print(f"  Valid orders:     {stats['valid']} ({stats['valid']/stats['total']*100:.1f}%)")
        print(f"  Invalid orders:   {stats['invalid']} ({stats['invalid']/stats['total']*100:.1f}%)")
        if pipeline_mode == 'route':
            print(f"  Routes found:     {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
        print()
        print(f"Output saved to: {args.output}")
        print()

        logger.info("Pipeline completed successfully")
        return 0

    except KeyboardInterrupt:
        print()
        logger.warning("Processing interrupted by user")
        return 1

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print()
        print(f"[ERROR] File not found: {e}")
        return 1

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        print()
        print(f"[ERROR] Invalid input: {e}")
        return 1

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print()
        print(f"[ERROR] An unexpected error occurred: {e}")
        print()
        print("For more details, run with --verbose flag")
        return 1


if __name__ == "__main__":
    sys.exit(main())
