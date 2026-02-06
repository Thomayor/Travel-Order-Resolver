#!/usr/bin/env python3
"""
Travel Order Resolver - Main CLI Entry Point

This is the main command-line interface for the Travel Order Resolver system.
It integrates NLP extraction with pathfinding to process French travel orders.

Usage:
    python main.py --input input.csv --output output.csv
    python main.py --input input.csv --output output.csv --mode nlp-only
    python main.py --input input.csv --output output.csv --mode full-pipeline --verbose

Arguments:
    --input, -i       Input CSV file (sentenceID,sentence)
    --output, -o      Output CSV file
    --mode, -m        Processing mode: nlp-only or full-pipeline (default: nlp-only)
    --verbose, -v     Enable verbose logging
    --help, -h        Show this help message

Examples:
    # Extract origin and destination only
    python main.py -i data/input.csv -o data/output.csv

    # Find complete routes with pathfinding
    python main.py -i data/input.csv -o data/output.csv -m full-pipeline

    # Verbose mode for debugging
    python main.py -i data/input.csv -o data/output.csv -v
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.pipeline import process_pipeline


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

    # Required arguments
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        metavar='FILE',
        help='Input CSV file (format: sentenceID,sentence)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
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

    # Validate input file
    logger.info("Validating input file...")
    if not validate_input_file(args.input, logger):
        logger.error("Input validation failed")
        return 1

    # Validate output file
    logger.info("Validating output path...")
    if not validate_output_file(args.output, logger):
        logger.error("Output validation failed")
        return 1

    # Map CLI mode to pipeline mode
    pipeline_mode = map_mode_to_pipeline(args.mode)

    # Print configuration
    print(f"Configuration:")
    print(f"  Input:  {args.input}")
    print(f"  Output: {args.output}")
    print(f"  Mode:   {args.mode} ({pipeline_mode})")
    print(f"  Verbose: {args.verbose}")
    print()

    # Run pipeline
    try:
        logger.info(f"Starting pipeline in {args.mode} mode...")

        stats = process_pipeline(
            input_file=args.input,
            output_file=args.output,
            mode=pipeline_mode
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
