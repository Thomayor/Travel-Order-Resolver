#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate statistical reports for the dataset
"""

import csv
import json
from collections import Counter

def analyze_dataset(csv_file):
    """Analyze a CSV dataset and return statistics"""

    phrases = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        phrases = list(reader)

    # Basic counts
    total = len(phrases)
    valid_count = sum(1 for p in phrases if p['is_valid'] == '1')
    invalid_count = total - valid_count

    # Category distribution
    categories = Counter(p['category'] for p in phrases)

    # Difficulty distribution
    difficulties = Counter(p['difficulty'] for p in phrases)

    # City usage (only for valid orders)
    cities = []
    for p in phrases:
        if p['is_valid'] == '1':
            if p['origin']:
                cities.append(p['origin'])
            if p['destination']:
                cities.append(p['destination'])

    city_usage = Counter(cities)

    # Sentence length statistics
    lengths = [len(p['sentence'].split()) for p in phrases]

    return {
        'total': total,
        'valid': valid_count,
        'invalid': invalid_count,
        'categories': dict(categories),
        'difficulties': dict(difficulties),
        'city_usage': dict(city_usage.most_common(20)),
        'sentence_length': {
            'min': min(lengths) if lengths else 0,
            'max': max(lengths) if lengths else 0,
            'avg': sum(lengths) / len(lengths) if lengths else 0
        }
    }

def main():
    """Generate all reports"""

    print("Generating reports...")

    # Analyze each dataset
    print("Analyzing invalid_orders.csv...")
    invalid_stats = analyze_dataset('data/invalid_orders.csv')

    print("Analyzing valid_orders_initial.csv...")
    valid_stats = analyze_dataset('data/valid_orders_initial.csv')

    print("Analyzing dataset_initial.csv...")
    full_stats = analyze_dataset('data/dataset_initial.csv')

    # Create JSON report
    report = {
        'generation_summary': {
            'total_phrases': full_stats['total'],
            'valid_phrases': full_stats['valid'],
            'invalid_phrases': full_stats['invalid'],
            'valid_percentage': full_stats['valid'] / full_stats['total'] * 100,
            'invalid_percentage': full_stats['invalid'] / full_stats['total'] * 100
        },
        'invalid_orders': {
            'total': invalid_stats['total'],
            'categories': invalid_stats['categories'],
            'difficulties': invalid_stats['difficulties'],
            'sentence_length': invalid_stats['sentence_length']
        },
        'valid_orders': {
            'total': valid_stats['total'],
            'categories': valid_stats['categories'],
            'difficulties': valid_stats['difficulties'],
            'top_20_cities': valid_stats['city_usage'],
            'sentence_length': valid_stats['sentence_length']
        },
        'merged_dataset': {
            'total': full_stats['total'],
            'valid': full_stats['valid'],
            'invalid': full_stats['invalid'],
            'categories': full_stats['categories'],
            'difficulties': full_stats['difficulties']
        }
    }

    # Write JSON report
    json_file = 'data/generation_report.json'
    print(f"\nWriting JSON report to {json_file}...")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("[OK] JSON report created")

    # Create text statistics file
    txt_file = 'data/statistics.txt'
    print(f"Writing statistics to {txt_file}...")

    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("TRAVEL ORDER RESOLVER - DATASET STATISTICS\n")
        f.write("=" * 70 + "\n\n")

        f.write("OVERALL SUMMARY\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total phrases: {full_stats['total']}\n")
        f.write(f"Valid orders: {full_stats['valid']} ({full_stats['valid']/full_stats['total']*100:.1f}%)\n")
        f.write(f"Invalid orders: {full_stats['invalid']} ({full_stats['invalid']/full_stats['total']*100:.1f}%)\n")
        f.write("\n")

        f.write("DISTRIBUTION BY VALIDITY\n")
        f.write("-" * 70 + "\n")
        f.write(f"Valid: {full_stats['valid']:,} phrases\n")
        f.write(f"Invalid: {full_stats['invalid']:,} phrases\n")
        f.write("\n")

        f.write("INVALID ORDERS - CATEGORY DISTRIBUTION\n")
        f.write("-" * 70 + "\n")
        for cat, count in sorted(invalid_stats['categories'].items()):
            percentage = count / invalid_stats['total'] * 100
            f.write(f"  {cat:30s}: {count:4d} ({percentage:5.1f}%)\n")
        f.write("\n")

        f.write("VALID ORDERS - CATEGORY DISTRIBUTION\n")
        f.write("-" * 70 + "\n")
        for cat, count in sorted(valid_stats['categories'].items()):
            percentage = count / valid_stats['total'] * 100
            f.write(f"  {cat:30s}: {count:4d} ({percentage:5.1f}%)\n")
        f.write("\n")

        f.write("DIFFICULTY DISTRIBUTION (VALID ORDERS)\n")
        f.write("-" * 70 + "\n")
        for diff, count in sorted(valid_stats['difficulties'].items()):
            percentage = count / valid_stats['total'] * 100
            f.write(f"  {diff:10s}: {count:4d} ({percentage:5.1f}%)\n")
        f.write("\n")

        f.write("TOP 20 CITIES USED (VALID ORDERS)\n")
        f.write("-" * 70 + "\n")
        for i, (city, count) in enumerate(sorted(valid_stats['city_usage'].items(), key=lambda x: x[1], reverse=True)[:20], 1):
            f.write(f"  {i:2d}. {city:25s}: {count:4d} occurrences\n")
        f.write("\n")

        f.write("SENTENCE LENGTH STATISTICS\n")
        f.write("-" * 70 + "\n")
        f.write(f"Invalid orders:\n")
        f.write(f"  Min length: {invalid_stats['sentence_length']['min']} words\n")
        f.write(f"  Max length: {invalid_stats['sentence_length']['max']} words\n")
        f.write(f"  Avg length: {invalid_stats['sentence_length']['avg']:.1f} words\n")
        f.write(f"\n")
        f.write(f"Valid orders:\n")
        f.write(f"  Min length: {valid_stats['sentence_length']['min']} words\n")
        f.write(f"  Max length: {valid_stats['sentence_length']['max']} words\n")
        f.write(f"  Avg length: {valid_stats['sentence_length']['avg']:.1f} words\n")
        f.write("\n")

        f.write("=" * 70 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 70 + "\n")

    print("[OK] Text statistics created")

    # Display summary
    print("\n" + "=" * 70)
    print("GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total phrases generated: {full_stats['total']:,}")
    print(f"  Valid:   {full_stats['valid']:,} ({full_stats['valid']/full_stats['total']*100:.1f}%)")
    print(f"  Invalid: {full_stats['invalid']:,} ({full_stats['invalid']/full_stats['total']*100:.1f}%)")
    print()
    print("Invalid categories:")
    for cat, count in sorted(invalid_stats['categories'].items()):
        print(f"  {cat:30s}: {count:4d}")
    print()
    print("Valid categories:")
    for cat, count in sorted(valid_stats['categories'].items()):
        print(f"  {cat:30s}: {count:4d}")
    print()
    print("Difficulty (valid orders):")
    for diff, count in sorted(valid_stats['difficulties'].items()):
        print(f"  {diff:10s}: {count:4d} ({count/valid_stats['total']*100:.1f}%)")
    print("=" * 70)

if __name__ == "__main__":
    main()
