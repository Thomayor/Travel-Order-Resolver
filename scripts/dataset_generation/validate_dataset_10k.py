#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate the 10K dataset for duplicates and integrity
"""

import csv
import sys
from collections import Counter


def check_duplicates(filename):
    """Check for duplicate sentences in a dataset"""

    print(f"\n{'='*70}")
    print(f"CHECKING DUPLICATES IN: {filename}")
    print('='*70)

    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        phrases = list(reader)

    # Check for duplicate sentences
    sentences = [p['sentence'] for p in phrases]
    sentence_counts = Counter(sentences)
    duplicates = {s: count for s, count in sentence_counts.items() if count > 1}

    print(f"\nTotal phrases: {len(phrases)}")
    print(f"Unique phrases: {len(sentence_counts)}")
    print(f"Duplicate sentences: {len(duplicates)}")

    if duplicates:
        print(f"\n[WARNING] Found {len(duplicates)} sentences that appear multiple times:")
        for i, (sentence, count) in enumerate(sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:20], 1):
            print(f"  {i}. ({count}x) {sentence[:60]}...")

        if len(duplicates) > 20:
            print(f"  ... and {len(duplicates) - 20} more duplicates")

        return False, len(duplicates)
    else:
        print("\n[OK] No duplicate sentences found!")
        return True, 0


def check_file_integrity(filename, expected_count, expected_valid, expected_invalid):
    """Check file structure and counts"""

    print(f"\n{'='*70}")
    print(f"CHECKING FILE INTEGRITY: {filename}")
    print('='*70)

    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        phrases = list(reader)

    # Check required columns
    required_columns = ['sentenceID', 'sentence', 'origin', 'destination',
                        'is_valid', 'difficulty', 'category', 'notes']

    actual_columns = set(phrases[0].keys()) if phrases else set()
    missing_columns = set(required_columns) - actual_columns

    print(f"\n[✓] Columns check:")
    if missing_columns:
        print(f"    [ERROR] Missing columns: {missing_columns}")
        return False
    else:
        print(f"    [OK] All required columns present")

    # Check counts
    print(f"\n[✓] Count check:")
    print(f"    Total phrases: {len(phrases)} (expected: {expected_count})")

    valid_count = sum(1 for p in phrases if p['is_valid'] == '1')
    invalid_count = sum(1 for p in phrases if p['is_valid'] == '0')

    print(f"    Valid orders: {valid_count} (expected: {expected_valid})")
    print(f"    Invalid orders: {invalid_count} (expected: {expected_invalid})")

    if len(phrases) != expected_count:
        print(f"    [WARNING] Count mismatch!")

    # Check sequential IDs
    print(f"\n[✓] ID sequence check:")
    ids = [int(p['sentenceID']) for p in phrases]
    expected_ids = list(range(1, len(phrases) + 1))

    if ids == expected_ids:
        print(f"    [OK] IDs are sequential (1 to {len(phrases)})")
    else:
        print(f"    [ERROR] IDs are not sequential")
        return False

    # Category distribution
    print(f"\n[✓] Category distribution:")
    categories = Counter(p['category'] for p in phrases)
    for cat, count in sorted(categories.items()):
        pct = (count / len(phrases)) * 100
        print(f"    {cat:25s}: {count:5d} ({pct:5.1f}%)")

    return True


def remove_duplicates(input_file, output_file):
    """Remove duplicate sentences from dataset"""

    print(f"\n{'='*70}")
    print(f"REMOVING DUPLICATES")
    print('='*70)
    print(f"\nInput:  {input_file}")
    print(f"Output: {output_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        phrases = list(reader)

    # Track seen sentences
    seen = set()
    unique_phrases = []
    duplicates_removed = 0

    for phrase in phrases:
        sentence = phrase['sentence']
        if sentence not in seen:
            seen.add(sentence)
            unique_phrases.append(phrase)
        else:
            duplicates_removed += 1

    # Reassign sequential IDs
    for i, phrase in enumerate(unique_phrases, 1):
        phrase['sentenceID'] = i

    # Write deduplicated dataset
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_phrases)

    print(f"\n[OK] Deduplication complete:")
    print(f"    Original: {len(phrases)} phrases")
    print(f"    Removed:  {duplicates_removed} duplicates")
    print(f"    Final:    {len(unique_phrases)} unique phrases")
    print(f"\n[OK] Written to: {output_file}")

    return unique_phrases


def main():
    """Validate and clean 10K dataset"""

    print("\n" + "="*70)
    print("10K DATASET VALIDATION AND CLEANUP")
    print("="*70)

    files_to_check = [
        ('data/valid_orders_10k.csv', 7000, 7000, 0),
        ('data/invalid_orders_10k.csv', 3000, 0, 3000),
        ('data/dataset_10k.csv', 10000, 7000, 3000)
    ]

    for filename, total, valid, invalid in files_to_check:
        # Check for duplicates
        no_duplicates, dup_count = check_duplicates(filename)

        # Check integrity
        check_file_integrity(filename, total, valid, invalid)

        # If duplicates found, create cleaned version
        if not no_duplicates and dup_count > 0:
            output_file = filename.replace('.csv', '_dedup.csv')
            remove_duplicates(filename, output_file)

    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("  1. Review any duplicates found above")
    print("  2. Use *_dedup.csv files if duplicates were removed")
    print("  3. Run: python3 generate_report.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
