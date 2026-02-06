"""
Demo Script for Travel Order Resolver Pipeline

This script demonstrates the end-to-end pipeline that integrates
NLP extraction with pathfinding to process travel orders.

Usage:
    python demo_pipeline.py

The script will:
1. Create sample input data with various test cases
2. Run the pipeline in both NLP and route modes
3. Display results and statistics
"""

import os
import csv
from pathlib import Path
from src.utils.pipeline import process_pipeline


def create_sample_input(file_path: str):
    """
    Create sample input file with various test cases.

    Test cases include:
    - Valid travel orders (simple format)
    - Valid travel orders (question format)
    - Valid travel orders (inverted order)
    - Invalid orders (not travel-related)
    - Edge cases (multi-word cities, accents)
    """
    test_sentences = [
        ("1", "Je veux aller de Paris à Lyon"),
        ("2", "Train pour Marseille depuis Toulouse"),
        ("3", "Comment aller à Bordeaux depuis Nantes?"),
        ("4", "Je voudrais un billet Lille Nice"),
        ("5", "À quelle heure y a-t-il des trains vers Strasbourg en partance de Paris?"),
        ("6", "Quel temps fait-il aujourd'hui?"),  # Invalid
        ("7", "Bonjour"),  # Invalid
        ("8", "Je veux aller de Aix-en-Provence à La Rochelle"),  # Multi-word cities
        ("9", "Billet de Béthune à Épernay s'il vous plaît"),  # Accents
        ("10", "Je pars demain"),  # Invalid - no locations
        ("11", "I want to go from Paris to Lyon"),  # English
    ]

    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['sentenceID', 'sentence'])
        writer.writerows(test_sentences)

    print(f"[OK] Created sample input file: {file_path}")
    print(f"  ({len(test_sentences)} test sentences)")
    print()


def print_results(output_file: str, mode: str):
    """Print results from output file."""
    print(f"\n{'=' * 70}")
    print(f"RESULTS ({mode.upper()} MODE)")
    print('=' * 70)

    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

        # Print header
        print(' | '.join(rows[0]))
        print('-' * 70)

        # Print data rows
        for row in rows[1:]:
            print(' | '.join(row))

    print('=' * 70)


def main():
    """Main demo function."""
    print("=" * 70)
    print("TRAVEL ORDER RESOLVER - PIPELINE DEMO")
    print("=" * 70)
    print()

    # Create data directory if needed
    data_dir = Path("data/demo")
    data_dir.mkdir(parents=True, exist_ok=True)

    # File paths
    input_file = str(data_dir / "input_demo.csv")
    output_nlp = str(data_dir / "output_nlp.csv")
    output_route = str(data_dir / "output_route.csv")

    # Step 1: Create sample input
    print("Step 1: Creating sample input data...")
    create_sample_input(input_file)

    # Step 2: Run pipeline in NLP mode
    print("Step 2: Running pipeline in NLP mode...")
    print("(Extracts origin and destination only)")
    print()

    stats_nlp = process_pipeline(
        input_file=input_file,
        output_file=output_nlp,
        mode='nlp'
    )

    # Display NLP results
    print_results(output_nlp, 'nlp')

    # Step 3: Run pipeline in route mode
    print("\n" + "=" * 70)
    print("Step 3: Running pipeline in ROUTE mode...")
    print("(Finds complete route with intermediate stops)")
    print()

    stats_route = process_pipeline(
        input_file=input_file,
        output_file=output_route,
        mode='route'
    )

    # Display route results
    print_results(output_route, 'route')

    # Step 4: Summary
    print("\n" + "=" * 70)
    print("DEMO SUMMARY")
    print("=" * 70)
    print(f"\nNLP Mode Statistics:")
    print(f"  Total sentences:     {stats_nlp['total']}")
    print(f"  Valid orders:        {stats_nlp['valid']}")
    print(f"  Invalid orders:      {stats_nlp['invalid']}")
    print(f"  Success rate:        {stats_nlp['valid']/stats_nlp['total']*100:.1f}%")

    print(f"\nRoute Mode Statistics:")
    print(f"  Total sentences:     {stats_route['total']}")
    print(f"  Valid orders:        {stats_route['valid']}")
    print(f"  Routes found:        {stats_route['success']}")
    print(f"  Success rate:        {stats_route['success']/stats_route['total']*100:.1f}%")

    print(f"\nOutput files saved to:")
    print(f"  NLP mode:   {output_nlp}")
    print(f"  Route mode: {output_route}")

    print("\n" + "=" * 70)
    print("[SUCCESS] DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Check output files in data/demo/")
    print("  2. Run with your own input: python -m src.utils.pipeline <input> <output> <mode>")
    print("  3. See tests/test_pipeline.py for more examples")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()
