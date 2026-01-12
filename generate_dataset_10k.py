#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate expanded dataset with 10,000 total sentences (7,000 valid + 3,000 invalid)

This script generates a larger dataset by scaling up the existing generation functions
while maintaining the same quality and category proportions.

Target distribution:
- Valid orders: 7,000 (70%)
- Invalid orders: 3,000 (30%)
"""

import csv
import random
import sys
import os

# Import from existing generators
from generate_valid_orders import (
    generate_standard,
    generate_inverted_order,
    generate_no_markers,
    generate_name_ambiguities,
    generate_compound_names,
    generate_misspellings,
    generate_no_capitals,
    generate_additional_info,
    generate_complex_questions
)

from generate_invalid_orders import (
    generate_no_intent,
    generate_incomplete,
    generate_garbage,
    generate_ambiguous
)


def generate_valid_orders_7k():
    """
    Generate ~7,300 valid orders (to get 7,000 after deduplication)

    Adjusted for ~3.5% duplication rate:
    - standard: 800 (26.7%) -> 1,940 (26.6%)
    - inverted_order: 400 (13.3%) -> 970 (13.3%)
    - no_markers: 300 (10%) -> 730 (10%)
    - name_ambiguities: 500 (16.7%) -> 1,220 (16.7%)
    - compound_names: 250 (8.3%) -> 605 (8.3%)
    - misspellings: 300 (10%) -> 730 (10%)
    - no_capitals: 250 (8.3%) -> 605 (8.3%)
    - additional_info: 150 (5%) -> 365 (5%)
    - complex_questions: 50 (1.7%) -> 135 (1.9%)

    Total: 7,300 -> ~7,000 after dedup
    """

    print("=" * 70)
    print("GENERATING 7,300 VALID ORDERS (target 7,000 after dedup)")
    print("=" * 70)

    all_phrases = []

    # Generate each category with scaled counts (compensating for duplicates)
    print("\n[1/9] Generating standard phrases (1,940)...")
    standard, next_id = generate_standard(1940)
    all_phrases.extend(standard)
    print(f"      Generated {len(standard)} phrases")

    print("\n[2/9] Generating inverted order phrases (970)...")
    inverted, next_id = generate_inverted_order(970, start_id=next_id)
    all_phrases.extend(inverted)
    print(f"      Generated {len(inverted)} phrases")

    print("\n[3/9] Generating no markers phrases (730)...")
    no_markers, next_id = generate_no_markers(730, start_id=next_id)
    all_phrases.extend(no_markers)
    print(f"      Generated {len(no_markers)} phrases")

    print("\n[4/9] Generating name ambiguities phrases (1,220)...")
    name_ambig, next_id = generate_name_ambiguities(1220, start_id=next_id)
    all_phrases.extend(name_ambig)
    print(f"      Generated {len(name_ambig)} phrases")

    print("\n[5/9] Generating compound names phrases (605)...")
    compound, next_id = generate_compound_names(605, start_id=next_id)
    all_phrases.extend(compound)
    print(f"      Generated {len(compound)} phrases")

    print("\n[6/9] Generating misspellings phrases (730)...")
    misspell_phrases, next_id = generate_misspellings(730, start_id=next_id)
    all_phrases.extend(misspell_phrases)
    print(f"      Generated {len(misspell_phrases)} phrases")

    print("\n[7/9] Generating no capitals phrases (605)...")
    no_caps, next_id = generate_no_capitals(605, start_id=next_id)
    all_phrases.extend(no_caps)
    print(f"      Generated {len(no_caps)} phrases")

    print("\n[8/9] Generating additional info phrases (365)...")
    additional, next_id = generate_additional_info(365, start_id=next_id)
    all_phrases.extend(additional)
    print(f"      Generated {len(additional)} phrases")

    print("\n[9/9] Generating complex questions phrases (135)...")
    complex_q, next_id = generate_complex_questions(135, start_id=next_id)
    all_phrases.extend(complex_q)
    print(f"      Generated {len(complex_q)} phrases")

    # Reassign sequential IDs
    for i, phrase in enumerate(all_phrases, 1):
        phrase['sentenceID'] = i

    print(f"\n[OK] Total valid phrases generated: {len(all_phrases)}")

    return all_phrases


def generate_invalid_orders_3k():
    """
    Generate ~4,600 invalid orders (to get 3,000 after deduplication)

    Adjusted for ~35% duplication rate:
    - no_intent: 1,000 (33.3%) -> 1,530 (33.3%)
    - incomplete: 1,000 (33.3%) -> 1,530 (33.3%)
    - garbage: 500 (16.7%) -> 770 (16.7%)
    - ambiguous: 500 (16.7%) -> 770 (16.7%)

    Total: 4,600 -> ~3,000 after dedup
    """

    print("\n" + "=" * 70)
    print("GENERATING 4,600 INVALID ORDERS (target 3,000 after dedup)")
    print("=" * 70)

    all_phrases = []

    # Generate each category with scaled counts (compensating for duplicates)
    print("\n[1/4] Generating no_intent phrases (1,530)...")
    no_intent, next_id = generate_no_intent(1530)
    all_phrases.extend(no_intent)
    print(f"      Generated {len(no_intent)} phrases")

    print("\n[2/4] Generating incomplete phrases (1,530)...")
    incomplete, next_id = generate_incomplete(1530, start_id=next_id)
    all_phrases.extend(incomplete)
    print(f"      Generated {len(incomplete)} phrases")

    print("\n[3/4] Generating garbage phrases (770)...")
    garbage, next_id = generate_garbage(770, start_id=next_id)
    all_phrases.extend(garbage)
    print(f"      Generated {len(garbage)} phrases")

    print("\n[4/4] Generating ambiguous phrases (770)...")
    ambiguous, next_id = generate_ambiguous(770, start_id=next_id)
    all_phrases.extend(ambiguous)
    print(f"      Generated {len(ambiguous)} phrases")

    # Reassign sequential IDs
    for i, phrase in enumerate(all_phrases, 1):
        phrase['sentenceID'] = i

    print(f"\n[OK] Total invalid phrases generated: {len(all_phrases)}")

    return all_phrases


def save_to_csv(phrases, output_file):
    """Save phrases to CSV file"""

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(phrases)

    print(f"[OK] Written to {output_file}")


def print_statistics(phrases, title):
    """Print category and difficulty statistics"""

    print(f"\n{title}")
    print("-" * 70)

    # Category distribution
    categories = {}
    for phrase in phrases:
        cat = phrase['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("\nDistribution by category:")
    for cat, count in sorted(categories.items()):
        pct = (count / len(phrases)) * 100
        print(f"  {cat:25s}: {count:5d} ({pct:5.1f}%)")

    # Difficulty distribution (for valid orders)
    if phrases and phrases[0]['is_valid'] == 1:
        difficulties = {}
        for phrase in phrases:
            diff = phrase['difficulty']
            difficulties[diff] = difficulties.get(diff, 0) + 1

        print("\nDistribution by difficulty:")
        for diff, count in sorted(difficulties.items()):
            pct = (count / len(phrases)) * 100
            print(f"  {diff:10s}: {count:5d} ({pct:5.1f}%)")


def merge_and_shuffle(valid_phrases, invalid_phrases, output_file):
    """Merge valid and invalid, shuffle, and save combined dataset"""

    print("\n" + "=" * 70)
    print("MERGING AND SHUFFLING DATASETS")
    print("=" * 70)

    all_phrases = valid_phrases + invalid_phrases

    # Shuffle with fixed seed for reproducibility
    random.seed(42)
    random.shuffle(all_phrases)

    # Reassign sequential IDs
    for i, phrase in enumerate(all_phrases, 1):
        phrase['sentenceID'] = i

    # Save merged dataset
    save_to_csv(all_phrases, output_file)

    print(f"\n[OK] Merged dataset: {len(all_phrases)} total phrases")
    print(f"     - Valid: {len(valid_phrases)} ({len(valid_phrases)/len(all_phrases)*100:.1f}%)")
    print(f"     - Invalid: {len(invalid_phrases)} ({len(invalid_phrases)/len(all_phrases)*100:.1f}%)")

    return all_phrases


def main():
    """Generate complete 10K dataset"""

    print("\n" + "=" * 70)
    print("TRAVEL ORDER RESOLVER - 10K DATASET GENERATION")
    print("=" * 70)
    print("\nTarget (after deduplication):")
    print("  - Total: 10,000 sentences")
    print("  - Valid orders: 7,000 (70%)")
    print("  - Invalid orders: 3,000 (30%)")
    print("\nGeneration (before deduplication):")
    print("  - Valid: ~7,300 (to compensate for ~3.5% duplicates)")
    print("  - Invalid: ~4,600 (to compensate for ~35% duplicates)")
    print("=" * 70)

    # Generate valid orders
    valid_phrases = generate_valid_orders_7k()
    save_to_csv(valid_phrases, 'data/valid_orders_10k.csv')
    print_statistics(valid_phrases, "VALID ORDERS STATISTICS")

    # Generate invalid orders
    invalid_phrases = generate_invalid_orders_3k()
    save_to_csv(invalid_phrases, 'data/invalid_orders_10k.csv')
    print_statistics(invalid_phrases, "INVALID ORDERS STATISTICS")

    # Merge and shuffle
    all_phrases = merge_and_shuffle(valid_phrases, invalid_phrases, 'data/dataset_10k.csv')

    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print("\nGenerated files (before deduplication):")
    print("  1. data/valid_orders_10k.csv    (~7,300 sentences)")
    print("  2. data/invalid_orders_10k.csv  (~4,600 sentences)")
    print("  3. data/dataset_10k.csv         (~11,900 sentences - shuffled)")
    print("\nNext steps:")
    print("  1. Run: python3 validate_dataset_10k.py  (removes duplicates)")
    print("  2. Use the *_dedup.csv files (should have ~10,000 total)")
    print("  3. Run: python3 generate_report.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
