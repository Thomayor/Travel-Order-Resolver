#!/usr/bin/env python3
"""
Split the 10K dataset into train/validation/test sets.

Split Ratios:
- Training: 70% (~7,000 sentences)
- Validation: 15% (~1,500 sentences)
- Test: 15% (~1,500 sentences)

Requirements:
- Stratified split to maintain class balance
- Random seed for reproducibility
- No data leakage between sets
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path


def split_dataset(
    input_file: str = "data/dataset_final.csv",
    output_dir: str = "data",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_seed: int = 42
):
    """
    Split dataset into train/val/test sets with stratification.

    Args:
        input_file: Path to the complete dataset CSV
        output_dir: Directory to save split files
        train_ratio: Proportion for training set (default: 0.70)
        val_ratio: Proportion for validation set (default: 0.15)
        test_ratio: Proportion for test set (default: 0.15)
        random_seed: Random seed for reproducibility (default: 42)
    """

    # Validate ratios
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
        f"Ratios must sum to 1.0 (got {train_ratio + val_ratio + test_ratio})"

    print(f"Loading dataset from {input_file}...")
    df = pd.read_csv(input_file, encoding='utf-8')

    print(f"Total samples: {len(df)}")
    print(f"  Valid orders: {df['is_valid'].sum()} ({df['is_valid'].sum()/len(df)*100:.1f}%)")
    print(f"  Invalid orders: {(~df['is_valid'].astype(bool)).sum()} ({(~df['is_valid'].astype(bool)).sum()/len(df)*100:.1f}%)")
    print()

    # Set random seed for reproducibility
    np.random.seed(random_seed)

    # Stratified split: separate valid and invalid orders
    df_valid = df[df['is_valid'] == 1].copy()
    df_invalid = df[df['is_valid'] == 0].copy()

    # Shuffle both groups
    df_valid = df_valid.sample(frac=1, random_state=random_seed).reset_index(drop=True)
    df_invalid = df_invalid.sample(frac=1, random_state=random_seed).reset_index(drop=True)

    # Calculate split sizes
    n_valid = len(df_valid)
    n_invalid = len(df_invalid)

    # First split: separate test set
    print(f"Splitting: {test_ratio*100:.0f}% test, {(1-test_ratio)*100:.0f}% train+val...")

    n_test_valid = int(n_valid * test_ratio)
    n_test_invalid = int(n_invalid * test_ratio)

    test_valid = df_valid[:n_test_valid]
    test_invalid = df_invalid[:n_test_invalid]
    test = pd.concat([test_valid, test_invalid], ignore_index=True).sample(frac=1, random_state=random_seed)

    remaining_valid = df_valid[n_test_valid:]
    remaining_invalid = df_invalid[n_test_invalid:]

    # Second split: separate validation from training
    adjusted_val_ratio = val_ratio / (train_ratio + val_ratio)
    print(f"Splitting train+val: {val_ratio*100:.0f}% val, {train_ratio*100:.0f}% train...")

    n_val_valid = int(len(remaining_valid) * adjusted_val_ratio)
    n_val_invalid = int(len(remaining_invalid) * adjusted_val_ratio)

    val_valid = remaining_valid[:n_val_valid]
    val_invalid = remaining_invalid[:n_val_invalid]
    val = pd.concat([val_valid, val_invalid], ignore_index=True).sample(frac=1, random_state=random_seed)

    train_valid = remaining_valid[n_val_valid:]
    train_invalid = remaining_invalid[n_val_invalid:]
    train = pd.concat([train_valid, train_invalid], ignore_index=True).sample(frac=1, random_state=random_seed)

    print()
    print("=" * 60)
    print("SPLIT RESULTS")
    print("=" * 60)

    # Create output directory if needed
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Save splits
    train_path = os.path.join(output_dir, "train.csv")
    val_path = os.path.join(output_dir, "val.csv")
    test_path = os.path.join(output_dir, "test.csv")

    train.to_csv(train_path, index=False, encoding='utf-8')
    val.to_csv(val_path, index=False, encoding='utf-8')
    test.to_csv(test_path, index=False, encoding='utf-8')

    print(f"\nFiles saved:")
    print(f"  {train_path}")
    print(f"  {val_path}")
    print(f"  {test_path}")
    print()

    # Print statistics
    def print_set_stats(name, dataset):
        total = len(dataset)
        valid = dataset['is_valid'].sum()
        invalid = (~dataset['is_valid'].astype(bool)).sum()
        avg_len_valid = dataset[dataset['is_valid'] == 1]['sentence'].str.split().str.len().mean()
        avg_len_invalid = dataset[dataset['is_valid'] == 0]['sentence'].str.split().str.len().mean()

        print(f"{name}:")
        print(f"  Total: {total:,} ({total/len(df)*100:.1f}% of dataset)")
        print(f"  Valid: {valid:,} ({valid/total*100:.1f}%)")
        print(f"  Invalid: {invalid:,} ({invalid/total*100:.1f}%)")
        print(f"  Avg sentence length (valid): {avg_len_valid:.1f} words")
        print(f"  Avg sentence length (invalid): {avg_len_invalid:.1f} words")
        print()

    print_set_stats("TRAIN SET", train)
    print_set_stats("VALIDATION SET", val)
    print_set_stats("TEST SET", test)

    # Verify no overlap (sanity check)
    train_ids = set(train['sentenceID'])
    val_ids = set(val['sentenceID'])
    test_ids = set(test['sentenceID'])

    assert len(train_ids & val_ids) == 0, "Data leakage: Train and Val overlap!"
    assert len(train_ids & test_ids) == 0, "Data leakage: Train and Test overlap!"
    assert len(val_ids & test_ids) == 0, "Data leakage: Val and Test overlap!"

    print("[OK] No data leakage detected (no overlap between sets)")
    print()

    # Generate statistics file
    stats_path = os.path.join(output_dir, "split_statistics.txt")
    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("DATASET SPLIT STATISTICS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Random seed: {random_seed}\n")
        f.write(f"Input file: {input_file}\n\n")

        f.write(f"Total dataset size: {len(df):,} sentences\n\n")

        f.write("Split Ratios:\n")
        f.write(f"  Train: {train_ratio*100:.0f}%\n")
        f.write(f"  Validation: {val_ratio*100:.0f}%\n")
        f.write(f"  Test: {test_ratio*100:.0f}%\n\n")

        f.write(f"Train Set ({len(train):,} sentences, {len(train)/len(df)*100:.1f}%):\n")
        f.write(f"  Valid: {train['is_valid'].sum():,} ({train['is_valid'].sum()/len(train)*100:.1f}%)\n")
        f.write(f"  Invalid: {(~train['is_valid'].astype(bool)).sum():,} ({(~train['is_valid'].astype(bool)).sum()/len(train)*100:.1f}%)\n\n")

        f.write(f"Validation Set ({len(val):,} sentences, {len(val)/len(df)*100:.1f}%):\n")
        f.write(f"  Valid: {val['is_valid'].sum():,} ({val['is_valid'].sum()/len(val)*100:.1f}%)\n")
        f.write(f"  Invalid: {(~val['is_valid'].astype(bool)).sum():,} ({(~val['is_valid'].astype(bool)).sum()/len(val)*100:.1f}%)\n\n")

        f.write(f"Test Set ({len(test):,} sentences, {len(test)/len(df)*100:.1f}%):\n")
        f.write(f"  Valid: {test['is_valid'].sum():,} ({test['is_valid'].sum()/len(test)*100:.1f}%)\n")
        f.write(f"  Invalid: {(~test['is_valid'].astype(bool)).sum():,} ({(~test['is_valid'].astype(bool)).sum()/len(test)*100:.1f}%)\n\n")

        f.write("Category Distribution (Valid Orders):\n")
        for category in sorted(train[train['is_valid'] == 1]['category'].unique()):
            train_count = (train['category'] == category).sum()
            val_count = (val['category'] == category).sum()
            test_count = (test['category'] == category).sum()
            total_count = (df['category'] == category).sum()

            f.write(f"  {category}:\n")
            f.write(f"    Train: {train_count} ({train_count/total_count*100:.1f}%)\n")
            f.write(f"    Val: {val_count} ({val_count/total_count*100:.1f}%)\n")
            f.write(f"    Test: {test_count} ({test_count/total_count*100:.1f}%)\n")

        f.write("\n[OK] Stratified split ensures balanced class distribution\n")
        f.write("[OK] No data leakage between sets\n")
        f.write("[OK] Random seed ensures reproducibility\n")

    print(f"Statistics saved to: {stats_path}")
    print()
    print("=" * 60)
    print("SPLIT COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    split_dataset()
