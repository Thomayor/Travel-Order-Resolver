#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate the generated dataset against specifications
"""

import csv
import sys
from collections import Counter

class DatasetValidator:
    """Validator for travel order dataset"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_file_structure(self, filename, expected_count):
        """Validate CSV file structure and count"""
        print(f"\nValidating {filename}...")

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                phrases = list(reader)

                # Check count
                actual_count = len(phrases)
                if actual_count != expected_count:
                    self.errors.append(
                        f"{filename}: Expected {expected_count} phrases, got {actual_count}"
                    )
                else:
                    print(f"  [OK] Count: {actual_count} phrases")

                # Check required columns
                required_columns = ['sentenceID', 'sentence', 'origin', 'destination',
                                    'is_valid', 'difficulty', 'category', 'notes']

                if not phrases:
                    self.errors.append(f"{filename}: File is empty")
                    return phrases

                actual_columns = set(phrases[0].keys())
                missing_columns = set(required_columns) - actual_columns

                if missing_columns:
                    self.errors.append(
                        f"{filename}: Missing columns: {missing_columns}"
                    )
                else:
                    print(f"  [OK] All required columns present")

                # Check for duplicates
                sentences = [p['sentence'] for p in phrases]
                duplicates = [s for s, count in Counter(sentences).items() if count > 1]

                if duplicates:
                    self.errors.append(
                        f"{filename}: Found {len(duplicates)} duplicate sentences"
                    )
                    if len(duplicates) <= 5:
                        for dup in duplicates:
                            self.errors.append(f"  Duplicate: {dup}")
                else:
                    print(f"  [OK] No duplicate sentences")

                # Check sequential IDs
                ids = [int(p['sentenceID']) for p in phrases]
                expected_ids = list(range(1, len(phrases) + 1))

                if ids != expected_ids:
                    self.errors.append(f"{filename}: IDs are not sequential")
                else:
                    print(f"  [OK] Sequential IDs")

                return phrases

        except FileNotFoundError:
            self.errors.append(f"{filename}: File not found")
            return []
        except Exception as e:
            self.errors.append(f"{filename}: Error reading file: {str(e)}")
            return []

    def validate_invalid_orders(self, phrases):
        """Validate invalid orders dataset"""
        print("\nValidating invalid orders content...")

        # Expected distribution
        expected_categories = {
            'no_intent': 1000,
            'incomplete_origin': 400,
            'incomplete_dest': 400,
            'incomplete_grammar': 200,
            'garbage': 500,
            'ambiguous': 500
        }

        # Count categories
        actual_categories = Counter(p['category'] for p in phrases)

        # Check distribution (allow ±5% tolerance)
        tolerance = 0.05
        for cat, expected in expected_categories.items():
            actual = actual_categories.get(cat, 0)
            lower = expected * (1 - tolerance)
            upper = expected * (1 + tolerance)

            if actual < lower or actual > upper:
                self.warnings.append(
                    f"Invalid orders: Category '{cat}' has {actual} phrases, "
                    f"expected ~{expected} (±5%)"
                )
            else:
                print(f"  [OK] {cat}: {actual} (target: {expected})")

        # Check all are marked invalid
        invalid_count = sum(1 for p in phrases if p['is_valid'] == '0')
        if invalid_count != len(phrases):
            self.errors.append(
                f"Invalid orders: {len(phrases) - invalid_count} phrases marked as valid"
            )
        else:
            print(f"  [OK] All phrases marked as invalid")

        # Check origin/destination are empty
        non_empty_origin = sum(1 for p in phrases if p['origin'])
        non_empty_dest = sum(1 for p in phrases if p['destination'])

        if non_empty_origin > 0:
            self.errors.append(
                f"Invalid orders: {non_empty_origin} phrases have non-empty origin"
            )
        else:
            print(f"  [OK] All origins are empty")

        if non_empty_dest > 0:
            self.errors.append(
                f"Invalid orders: {non_empty_dest} phrases have non-empty destination"
            )
        else:
            print(f"  [OK] All destinations are empty")

    def validate_valid_orders(self, phrases):
        """Validate valid orders dataset"""
        print("\nValidating valid orders content...")

        # Expected distribution
        expected_categories = {
            'standard': 800,
            'inverted_order': 400,
            'no_markers': 300,
            'name_ambiguity': 500,
            'compound_name': 250,
            'misspelling': 300,
            'no_capitals': 250,
            'additional_info': 150,
            'complex_question': 50
        }

        # Count categories
        actual_categories = Counter(p['category'] for p in phrases)

        # Check distribution (allow ±5% tolerance)
        tolerance = 0.05
        for cat, expected in expected_categories.items():
            actual = actual_categories.get(cat, 0)
            lower = expected * (1 - tolerance)
            upper = expected * (1 + tolerance)

            if actual < lower or actual > upper:
                self.warnings.append(
                    f"Valid orders: Category '{cat}' has {actual} phrases, "
                    f"expected ~{expected} (±5%)"
                )
            else:
                print(f"  [OK] {cat}: {actual} (target: {expected})")

        # Check all are marked valid
        valid_count = sum(1 for p in phrases if p['is_valid'] == '1')
        if valid_count != len(phrases):
            self.errors.append(
                f"Valid orders: {len(phrases) - valid_count} phrases marked as invalid"
            )
        else:
            print(f"  [OK] All phrases marked as valid")

        # Check origin/destination are not empty
        empty_origin = sum(1 for p in phrases if not p['origin'])
        empty_dest = sum(1 for p in phrases if not p['destination'])

        if empty_origin > 0:
            self.errors.append(
                f"Valid orders: {empty_origin} phrases have empty origin"
            )
        else:
            print(f"  [OK] All origins are filled")

        if empty_dest > 0:
            self.errors.append(
                f"Valid orders: {empty_dest} phrases have empty destination"
            )
        else:
            print(f"  [OK] All destinations are filled")

        # Check difficulty distribution (30% easy, 50% medium, 20% hard)
        difficulties = Counter(p['difficulty'] for p in phrases)
        total = len(phrases)

        expected_difficulties = {
            'easy': (total * 0.30, 0.05),    # 30% ±5%
            'medium': (total * 0.50, 0.05),  # 50% ±5%
            'hard': (total * 0.20, 0.05)     # 20% ±5%
        }

        for diff, (expected, tolerance) in expected_difficulties.items():
            actual = difficulties.get(diff, 0)
            lower = expected * (1 - tolerance)
            upper = expected * (1 + tolerance)

            if actual < lower or actual > upper:
                self.warnings.append(
                    f"Valid orders: Difficulty '{diff}' has {actual} phrases, "
                    f"expected ~{int(expected)} (±5%)"
                )
            else:
                print(f"  [OK] {diff}: {actual} (target: {int(expected)})")

    def validate_merged_dataset(self, phrases):
        """Validate merged dataset"""
        print("\nValidating merged dataset...")

        # Check 70/30 split
        valid_count = sum(1 for p in phrases if p['is_valid'] == '1')
        invalid_count = len(phrases) - valid_count

        expected_valid = 3000
        expected_invalid = 3000

        if valid_count != expected_valid:
            self.errors.append(
                f"Merged dataset: Expected {expected_valid} valid phrases, got {valid_count}"
            )
        else:
            print(f"  [OK] Valid count: {valid_count}")

        if invalid_count != expected_invalid:
            self.errors.append(
                f"Merged dataset: Expected {expected_invalid} invalid phrases, got {invalid_count}"
            )
        else:
            print(f"  [OK] Invalid count: {invalid_count}")

    def print_report(self):
        """Print validation report"""
        print("\n" + "=" * 70)
        print("VALIDATION REPORT")
        print("=" * 70)

        if not self.errors and not self.warnings:
            print("\n[SUCCESS] All validations passed!")
            return True

        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  ! {warning}")

        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  X {error}")
            print("\n[FAILED] Validation failed with errors")
            return False

        print("\n[PASSED] Validation passed with warnings")
        return True

def main():
    """Run validation"""
    validator = DatasetValidator()

    print("=" * 70)
    print("DATASET VALIDATION")
    print("=" * 70)

    # Validate invalid orders
    invalid_phrases = validator.validate_file_structure(
        'data/invalid_orders.csv',
        expected_count=3000
    )
    if invalid_phrases:
        validator.validate_invalid_orders(invalid_phrases)

    # Validate valid orders
    valid_phrases = validator.validate_file_structure(
        'data/valid_orders_initial.csv',
        expected_count=3000
    )
    if valid_phrases:
        validator.validate_valid_orders(valid_phrases)

    # Validate merged dataset
    merged_phrases = validator.validate_file_structure(
        'data/dataset_initial.csv',
        expected_count=6000
    )
    if merged_phrases:
        validator.validate_merged_dataset(merged_phrases)

    # Print report
    success = validator.print_report()

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
