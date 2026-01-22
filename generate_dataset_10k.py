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
    generate_easy_orders,
    generate_medium_orders,
    generate_hard_orders
)

from generate_invalid_orders import (
    generate_no_intent,
    generate_incomplete,
    generate_garbage,
    generate_ambiguous
)


def generate_valid_orders_7k():
    """
    Generate ~7,275 valid orders (to get 7,000 after deduplication)

    NEW ARCHITECTURE: 3 functions by difficulty level
    - Easy: 2,400 -> 2,310 after dedup (33%)
    - Medium: 2,400 -> 2,310 after dedup (33%)
    - Hard: 2,475 -> 2,380 after dedup (34%)

    Distribution: 33% easy / 33% medium / 34% hard
    """

    print("=" * 70)
    print("GENERATING 7,275 VALID ORDERS (target 7,000 after dedup)")
    print("Distribution: 33% easy / 33% medium / 34% hard")
    print("=" * 70)

    all_phrases = []

    # Generate easy orders (2,400 → 2,310 after dedup)
    print("\n[EASY] Generating easy-difficulty orders (2,400)...")
    easy, next_id = generate_easy_orders(count=2400, start_id=1)
    all_phrases.extend(easy)
    print(f"      Generated {len(easy)} phrases")

    # Generate medium orders (2,400 → 2,310 after dedup)
    print("\n[MEDIUM] Generating medium-difficulty orders (2,400)...")
    medium, next_id = generate_medium_orders(count=2400, start_id=next_id)
    all_phrases.extend(medium)
    print(f"      Generated {len(medium)} phrases")

    # Generate hard orders (2,475 → 2,380 after dedup)
    print("\n[HARD] Generating hard-difficulty orders (2,475)...")
    hard, next_id = generate_hard_orders(count=2475, start_id=next_id)
    all_phrases.extend(hard)
    print(f"      Generated {len(hard)} phrases")

    # Reassign sequential IDs
    for i, phrase in enumerate(all_phrases, 1):
        phrase['sentenceID'] = i

    print(f"\n[OK] Total valid phrases generated: {len(all_phrases)}")
    print(f"     Expected after dedup: ~7,000")
    print(f"     Distribution: {len(easy)} easy / {len(medium)} medium / {len(hard)} hard")

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
