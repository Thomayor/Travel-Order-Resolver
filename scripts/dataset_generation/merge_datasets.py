#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge valid and invalid datasets into a single shuffled dataset
"""

import csv
import random

def main():
    """Merge and shuffle datasets"""

    print("Merging datasets...")

    # Read invalid orders
    invalid_phrases = []
    with open('data/invalid_orders.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        invalid_phrases = list(reader)

    print(f"Loaded {len(invalid_phrases)} invalid phrases")

    # Read valid orders
    valid_phrases = []
    with open('data/valid_orders_initial.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        valid_phrases = list(reader)

    print(f"Loaded {len(valid_phrases)} valid phrases")

    # Combine
    all_phrases = invalid_phrases + valid_phrases
    print(f"Total: {len(all_phrases)} phrases")

    # Shuffle
    print("Shuffling...")
    random.shuffle(all_phrases)

    # Reassign sequential IDs
    for i, phrase in enumerate(all_phrases, 1):
        phrase['sentenceID'] = i

    # Write merged dataset
    output_file = 'data/dataset_initial.csv'
    print(f"Writing to {output_file}...")

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_phrases)

    print(f"[OK] Created merged dataset with {len(all_phrases)} phrases")

    # Statistics
    valid_count = sum(1 for p in all_phrases if p['is_valid'] == '1')
    invalid_count = sum(1 for p in all_phrases if p['is_valid'] == '0')

    print(f"\nDistribution:")
    print(f"  Valid: {valid_count} ({valid_count/len(all_phrases)*100:.1f}%)")
    print(f"  Invalid: {invalid_count} ({invalid_count/len(all_phrases)*100:.1f}%)")

if __name__ == "__main__":
    main()
