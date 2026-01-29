#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate comprehensive statistics report for the 10K dataset
"""

import csv
import json
from collections import Counter


def load_dataset(filename):
    """Load CSV dataset"""
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def generate_statistics(dataset, dataset_name="Dataset"):
    """Generate comprehensive statistics"""

    stats = {
        'name': dataset_name,
        'total_count': len(dataset),
        'valid_count': 0,
        'invalid_count': 0,
        'categories': {},
        'difficulties': {},
        'sentence_lengths': [],
        'top_cities': Counter(),
    }

    for phrase in dataset:
        # Count valid vs invalid
        if phrase['is_valid'] == '1':
            stats['valid_count'] += 1

            # Track cities for valid orders
            if phrase['origin']:
                stats['top_cities'][phrase['origin']] += 1
            if phrase['destination']:
                stats['top_cities'][phrase['destination']] += 1
        else:
            stats['invalid_count'] += 1

        # Count categories
        category = phrase['category']
        stats['categories'][category] = stats['categories'].get(category, 0) + 1

        # Count difficulties
        difficulty = phrase.get('difficulty', '')
        if difficulty:
            stats['difficulties'][difficulty] = stats['difficulties'].get(difficulty, 0) + 1

        # Track sentence lengths
        sentence_length = len(phrase['sentence'].split())
        stats['sentence_lengths'].append(sentence_length)

    # Calculate percentages
    stats['valid_percentage'] = (stats['valid_count'] / stats['total_count']) * 100 if stats['total_count'] > 0 else 0
    stats['invalid_percentage'] = (stats['invalid_count'] / stats['total_count']) * 100 if stats['total_count'] > 0 else 0

    # Sentence length statistics
    if stats['sentence_lengths']:
        stats['min_length'] = min(stats['sentence_lengths'])
        stats['max_length'] = max(stats['sentence_lengths'])
        stats['avg_length'] = sum(stats['sentence_lengths']) / len(stats['sentence_lengths'])

    return stats


def print_text_report(stats_valid, stats_invalid, stats_combined):
    """Print human-readable text report"""

    report = []
    report.append("=" * 70)
    report.append("TRAVEL ORDER RESOLVER - 10K DATASET STATISTICS")
    report.append("=" * 70)
    report.append("")
    report.append("OVERALL SUMMARY")
    report.append("-" * 70)
    report.append(f"Total phrases: {stats_combined['total_count']:,}")
    report.append(f"Valid orders: {stats_combined['valid_count']:,} ({stats_combined['valid_percentage']:.1f}%)")
    report.append(f"Invalid orders: {stats_combined['invalid_count']:,} ({stats_combined['invalid_percentage']:.1f}%)")
    report.append("")

    # Invalid orders category distribution
    report.append("INVALID ORDERS - CATEGORY DISTRIBUTION")
    report.append("-" * 70)
    invalid_total = stats_invalid['total_count']
    for cat, count in sorted(stats_invalid['categories'].items()):
        pct = (count / invalid_total) * 100 if invalid_total > 0 else 0
        report.append(f"  {cat:30s}: {count:5d} ({pct:5.1f}%)")
    report.append("")

    # Valid orders category distribution
    report.append("VALID ORDERS - CATEGORY DISTRIBUTION")
    report.append("-" * 70)
    valid_total = stats_valid['total_count']
    for cat, count in sorted(stats_valid['categories'].items()):
        pct = (count / valid_total) * 100 if valid_total > 0 else 0
        report.append(f"  {cat:30s}: {count:5d} ({pct:5.1f}%)")
    report.append("")

    # Difficulty distribution
    report.append("DIFFICULTY DISTRIBUTION (VALID ORDERS)")
    report.append("-" * 70)
    for diff, count in sorted(stats_valid['difficulties'].items()):
        pct = (count / valid_total) * 100 if valid_total > 0 else 0
        report.append(f"  {diff:10s}: {count:5d} ({pct:5.1f}%)")
    report.append("")

    # Top 20 cities
    report.append("TOP 20 CITIES USED (VALID ORDERS)")
    report.append("-" * 70)
    for i, (city, count) in enumerate(stats_valid['top_cities'].most_common(20), 1):
        report.append(f"  {i:2d}. {city:25s}: {count:4d} occurrences")
    report.append("")

    # Sentence length statistics
    report.append("SENTENCE LENGTH STATISTICS")
    report.append("-" * 70)
    report.append("Invalid orders:")
    report.append(f"  Min length: {stats_invalid['min_length']} words")
    report.append(f"  Max length: {stats_invalid['max_length']} words")
    report.append(f"  Avg length: {stats_invalid['avg_length']:.1f} words")
    report.append("")
    report.append("Valid orders:")
    report.append(f"  Min length: {stats_valid['min_length']} words")
    report.append(f"  Max length: {stats_valid['max_length']} words")
    report.append(f"  Avg length: {stats_valid['avg_length']:.1f} words")
    report.append("")

    report.append("=" * 70)
    report.append("END OF REPORT")
    report.append("=" * 70)

    return "\n".join(report)


def save_json_report(stats_valid, stats_invalid, stats_combined, filename):
    """Save JSON format report"""

    report = {
        'dataset_name': '10K Travel Order Dataset',
        'version': '1.0',
        'summary': {
            'total': stats_combined['total_count'],
            'valid': stats_combined['valid_count'],
            'invalid': stats_combined['invalid_count'],
            'valid_percentage': round(stats_combined['valid_percentage'], 2),
            'invalid_percentage': round(stats_combined['invalid_percentage'], 2),
        },
        'valid_orders': {
            'count': stats_valid['total_count'],
            'categories': stats_valid['categories'],
            'difficulties': stats_valid['difficulties'],
            'top_20_cities': dict(stats_valid['top_cities'].most_common(20)),
            'sentence_length': {
                'min': stats_valid['min_length'],
                'max': stats_valid['max_length'],
                'avg': round(stats_valid['avg_length'], 2),
            }
        },
        'invalid_orders': {
            'count': stats_invalid['total_count'],
            'categories': stats_invalid['categories'],
            'sentence_length': {
                'min': stats_invalid['min_length'],
                'max': stats_invalid['max_length'],
                'avg': round(stats_invalid['avg_length'], 2),
            }
        }
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[OK] JSON report saved to: {filename}")


def main():
    """Generate reports for 10K dataset"""

    print("\n" + "=" * 70)
    print("GENERATING 10K DATASET STATISTICS")
    print("=" * 70 + "\n")

    # Load datasets
    print("Loading datasets...")
    valid_dataset = load_dataset('data/valid_orders_final.csv')
    invalid_dataset = load_dataset('data/invalid_orders_final.csv')
    combined_dataset = load_dataset('data/dataset_final.csv')
    print(f"  Valid: {len(valid_dataset)} phrases")
    print(f"  Invalid: {len(invalid_dataset)} phrases")
    print(f"  Combined: {len(combined_dataset)} phrases")

    # Generate statistics
    print("\nGenerating statistics...")
    stats_valid = generate_statistics(valid_dataset, "Valid Orders")
    stats_invalid = generate_statistics(invalid_dataset, "Invalid Orders")
    stats_combined = generate_statistics(combined_dataset, "Combined Dataset")

    # Save text report
    print("\nGenerating text report...")
    text_report = print_text_report(stats_valid, stats_invalid, stats_combined)
    with open('data/statistics_10k.txt', 'w', encoding='utf-8') as f:
        f.write(text_report)
    print("[OK] Text report saved to: data/statistics_10k.txt")

    # Save JSON report
    print("\nGenerating JSON report...")
    save_json_report(stats_valid, stats_invalid, stats_combined, 'data/generation_report_10k.json')

    # Print summary to console
    print("\n" + text_report)

    print("\n" + "=" * 70)
    print("REPORT GENERATION COMPLETE")
    print("=" * 70)
    print("\nGenerated files:")
    print("  - data/statistics_10k.txt")
    print("  - data/generation_report_10k.json")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
