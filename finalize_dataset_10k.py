#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finalize 10K dataset by adjusting counts to exactly 7,000 valid + 3,000 invalid
"""

import csv
import random

# Import from existing generators for creating additional invalid phrases
from generate_invalid_orders import (
    generate_no_intent,
    generate_incomplete,
    generate_garbage,
    generate_ambiguous
)


def trim_to_exact_count(input_file, output_file, target_count, seed=42):
    """Trim dataset to exact count by removing random entries"""

    print(f"\nTrimming {input_file} to exactly {target_count} entries...")

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        phrases = list(reader)

    current_count = len(phrases)
    print(f"  Current: {current_count} phrases")

    if current_count == target_count:
        print(f"  [OK] Already at target count!")
        return phrases
    elif current_count < target_count:
        print(f"  [ERROR] Current count ({current_count}) is less than target ({target_count})")
        return phrases
    else:
        # Randomly sample to get exact count
        random.seed(seed)
        selected = random.sample(phrases, target_count)

        # Sort by original sentenceID to maintain some ordering
        selected.sort(key=lambda x: int(x['sentenceID']))

        # Reassign sequential IDs
        for i, phrase in enumerate(selected, 1):
            phrase['sentenceID'] = i

        # Write to output
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(selected)

        print(f"  [OK] Trimmed to {len(selected)} phrases")
        print(f"  [OK] Written to: {output_file}")

        return selected


def expand_to_exact_count(input_file, output_file, target_count, seed=42):
    """Expand invalid orders dataset to exact count by generating more phrases"""

    print(f"\nExpanding {input_file} to exactly {target_count} entries...")

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        phrases = list(reader)

    current_count = len(phrases)
    print(f"  Current: {current_count} phrases")

    if current_count == target_count:
        print(f"  [OK] Already at target count!")
        return phrases
    elif current_count > target_count:
        print(f"  [WARNING] Current count ({current_count}) exceeds target ({target_count})")
        print(f"  Trimming instead...")
        return trim_to_exact_count(input_file, output_file, target_count, seed)
    else:
        needed = target_count - current_count
        print(f"  Need to generate {needed} additional phrases")

        # Generate additional phrases proportionally
        # Distribution: no_intent 33%, incomplete 33%, garbage 17%, ambiguous 17%
        no_intent_count = int(needed * 0.33)
        incomplete_count = int(needed * 0.33)
        garbage_count = int(needed * 0.17)
        ambiguous_count = needed - (no_intent_count + incomplete_count + garbage_count)

        print(f"  Generating:")
        print(f"    - no_intent: {no_intent_count}")
        print(f"    - incomplete: {incomplete_count}")
        print(f"    - garbage: {garbage_count}")
        print(f"    - ambiguous: {ambiguous_count}")

        # Set seed for reproducibility
        random.seed(seed)

        additional = []

        # Generate each category
        if no_intent_count > 0:
            no_intent_phrases, _ = generate_no_intent(no_intent_count)
            additional.extend(no_intent_phrases)

        if incomplete_count > 0:
            incomplete_phrases, _ = generate_incomplete(incomplete_count)
            additional.extend(incomplete_phrases)

        if garbage_count > 0:
            garbage_phrases, _ = generate_garbage(garbage_count)
            additional.extend(garbage_phrases)

        if ambiguous_count > 0:
            ambiguous_phrases, _ = generate_ambiguous(ambiguous_count)
            additional.extend(ambiguous_phrases)

        # Combine with existing
        all_phrases = phrases + additional

        # Remove any duplicates that may have been generated
        seen = set()
        unique_phrases = []
        for phrase in all_phrases:
            sentence = phrase['sentence']
            if sentence not in seen:
                seen.add(sentence)
                unique_phrases.append(phrase)

        print(f"  Generated {len(additional)} new phrases")
        print(f"  After dedup: {len(unique_phrases)} unique phrases")

        # If still short after dedup, generate a few more
        while len(unique_phrases) < target_count:
            extra_needed = target_count - len(unique_phrases)
            print(f"  Still need {extra_needed} more (due to duplicates)...")
            extra, _ = generate_garbage(extra_needed + 10)  # Generate a few extra

            for phrase in extra:
                sentence = phrase['sentence']
                if sentence not in seen and len(unique_phrases) < target_count:
                    seen.add(sentence)
                    unique_phrases.append(phrase)

        # Trim to exact count if we went over
        if len(unique_phrases) > target_count:
            unique_phrases = unique_phrases[:target_count]

        # Reassign sequential IDs
        for i, phrase in enumerate(unique_phrases, 1):
            phrase['sentenceID'] = i

        # Write to output
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_phrases)

        print(f"  [OK] Final count: {len(unique_phrases)} phrases")
        print(f"  [OK] Written to: {output_file}")

        return unique_phrases


def merge_final_dataset(valid_file, invalid_file, output_file, seed=42):
    """Merge valid and invalid datasets and shuffle"""

    print(f"\n{'='*70}")
    print("MERGING FINAL DATASET")
    print('='*70)

    with open(valid_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        valid = list(reader)

    with open(invalid_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        invalid = list(reader)

    print(f"Valid orders: {len(valid)}")
    print(f"Invalid orders: {len(invalid)}")
    print(f"Total: {len(valid) + len(invalid)}")

    # Combine and shuffle
    all_phrases = valid + invalid
    random.seed(seed)
    random.shuffle(all_phrases)

    # Reassign sequential IDs
    for i, phrase in enumerate(all_phrases, 1):
        phrase['sentenceID'] = i

    # Write merged dataset
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_phrases)

    print(f"\n[OK] Final dataset written to: {output_file}")

    return all_phrases


def main():
    """Finalize 10K dataset"""

    print("\n" + "="*70)
    print("FINALIZING 10K DATASET")
    print("="*70)
    print("\nAdjusting counts to exactly:")
    print("  - Valid orders: 7,000")
    print("  - Invalid orders: 3,000")
    print("  - Total: 10,000")
    print("="*70)

    # Adjust valid orders to exactly 7,000
    valid = trim_to_exact_count(
        'data/valid_orders_10k_dedup.csv',
        'data/valid_orders_final.csv',
        7000,
        seed=42
    )

    # Adjust invalid orders to exactly 3,000
    invalid = expand_to_exact_count(
        'data/invalid_orders_10k_dedup.csv',
        'data/invalid_orders_final.csv',
        3000,
        seed=42
    )

    # Merge into final dataset
    final = merge_final_dataset(
        'data/valid_orders_final.csv',
        'data/invalid_orders_final.csv',
        'data/dataset_final.csv',
        seed=42
    )

    print("\n" + "="*70)
    print("FINALIZATION COMPLETE")
    print("="*70)
    print("\nFinal files:")
    print("  1. data/valid_orders_final.csv   (7,000 sentences)")
    print("  2. data/invalid_orders_final.csv (3,000 sentences)")
    print("  3. data/dataset_final.csv        (10,000 sentences - shuffled)")
    print("\nNext steps:")
    print("  1. Run: python3 generate_report.py")
    print("  2. Update documentation")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
