#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove duplicates from generated datasets
"""

import csv
from collections import OrderedDict

def remove_duplicates(input_file, output_file):
    """Remove duplicate sentences while preserving order"""

    print(f"\nProcessing {input_file}...")

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        phrases = list(reader)

    print(f"  Original count: {len(phrases)}")

    # Track seen sentences (case-sensitive)
    seen = set()
    unique_phrases = []

    for phrase in phrases:
        sentence = phrase['sentence']
        if sentence not in seen:
            seen.add(sentence)
            unique_phrases.append(phrase)

    duplicates_removed = len(phrases) - len(unique_phrases)
    print(f"  Duplicates removed: {duplicates_removed}")
    print(f"  Final count: {len(unique_phrases)}")

    # Reassign sequential IDs
    for i, phrase in enumerate(unique_phrases, 1):
        phrase['sentenceID'] = i

    # Write to output
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_phrases)

    print(f"  Written to {output_file}")
    return len(unique_phrases)

def main():
    """Remove duplicates from all datasets"""

    print("Removing duplicates from datasets...")

    # Fix invalid orders
    invalid_count = remove_duplicates(
        'data/invalid_orders.csv',
        'data/invalid_orders.csv'
    )

    # Fix valid orders
    valid_count = remove_duplicates(
        'data/valid_orders_initial.csv',
        'data/valid_orders_initial.csv'
    )

    # Fix merged dataset
    merged_count = remove_duplicates(
        'data/dataset_initial.csv',
        'data/dataset_initial.csv'
    )

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Invalid orders: {invalid_count} unique phrases")
    print(f"Valid orders:   {valid_count} unique phrases")
    print(f"Merged dataset: {merged_count} unique phrases")
    print("=" * 70)

if __name__ == "__main__":
    main()
