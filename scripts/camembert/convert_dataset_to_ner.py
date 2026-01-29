"""
Dataset Conversion Script: CSV to NER Token Classification Format

Converts the Travel Order Resolver dataset from CSV format to token-level
NER format compatible with HuggingFace transformers.

Input: train.csv, val.csv, test.csv (pre-split stratified datasets)
       Each with columns (sentenceID, sentence, origin, destination, is_valid, difficulty, category, ...)
Output: train_ner.json, val_ner.json, test_ner.json with token-level labels

IMPORTANT: This script uses the pre-split datasets created by split_dataset.py
to maintain the stratified 33%/33%/34% difficulty distribution (easy/medium/hard).
Run split_dataset.py first to generate train/val/test splits.

Labels:
- B-ORIGIN: Beginning of origin city
- I-ORIGIN: Inside origin city (multi-word cities like "Port-Boulet")
- B-DEST: Beginning of destination city
- I-DEST: Inside destination city
- O: Outside (not part of origin or destination)
"""

import csv
import json
import re
import sys
from typing import List, Tuple, Dict
from pathlib import Path
from sklearn.model_selection import train_test_split

# Add src to path to import gazetteer (3 levels up: convert_dataset_to_ner.py -> camembert -> scripts -> root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from nlp.gazetteer import Gazetteer


def normalize_text_for_tokenization(text: str) -> str:
    """
    Normalize text while preserving structure for tokenization.
    Keep hyphens and spaces to match city names properly.
    """
    # Just basic cleanup, preserve hyphens and spaces
    text = text.strip()
    return text


def simple_tokenize(text: str) -> List[str]:
    """
    Simple whitespace + punctuation tokenizer.
    Splits on spaces and separates punctuation, keeping hyphens within words.

    Examples:
        "Port-Boulet" -> ["Port", "-", "Boulet"]
        "Aix-en-Provence" -> ["Aix", "-", "en", "-", "Provence"]
        "de Paris à Lyon" -> ["de", "Paris", "à", "Lyon"]
    """
    tokens = []
    # Split on spaces first
    words = text.split()

    for word in words:
        # Handle hyphens by splitting and keeping them
        if '-' in word:
            parts = word.split('-')
            for i, part in enumerate(parts):
                if part:  # Skip empty strings
                    tokens.append(part)
                if i < len(parts) - 1:  # Add hyphen between parts
                    tokens.append('-')
        else:
            # Handle other punctuation at word boundaries
            # Match word characters and separate trailing punctuation
            match = re.match(r"^([\w']+)([.,!?;:]+)?$", word)
            if match:
                tokens.append(match.group(1))
                if match.group(2):
                    tokens.append(match.group(2))
            else:
                tokens.append(word)

    return tokens


def normalize_city_name(city: str) -> str:
    """Normalize city name for matching (lowercase, strip)."""
    return city.lower().strip()


def find_entity_positions(tokens: List[str], entity: str, gaz: Gazetteer) -> List[Tuple[int, int]]:
    """
    Find all positions where entity appears in token list.
    Handles multi-word entities like "Port-Boulet" or "Aix-en-Provence".
    Uses fuzzy matching to handle misspellings.

    Returns list of (start_idx, end_idx) tuples.
    """
    if not entity:
        return []

    # Tokenize the entity the same way
    entity_tokens = simple_tokenize(entity)
    entity_normalized = [normalize_city_name(t) for t in entity_tokens]

    positions = []
    tokens_normalized = [normalize_city_name(t) for t in tokens]

    # Sliding window to find matches
    for i in range(len(tokens_normalized) - len(entity_normalized) + 1):
        window = tokens_normalized[i:i + len(entity_normalized)]

        # Try exact match first
        if window == entity_normalized:
            positions.append((i, i + len(entity_normalized)))
            continue

        # Try fuzzy match
        # Reconstruct full text from window (rejoin with appropriate separators)
        window_text = ''
        entity_text = ''
        for j, token in enumerate(tokens[i:i+len(entity_normalized)]):
            if token == '-':
                window_text += token
            else:
                window_text += token if j == 0 or tokens[i+j-1] == '-' else ' ' + token

        for j, token in enumerate(entity_tokens):
            if token == '-':
                entity_text += token
            else:
                entity_text += token if j == 0 or entity_tokens[j-1] == '-' else ' ' + token

        # Use gazetteer fuzzy match
        matches = gaz.fuzzy_match(window_text, max_distance=3)
        if matches:
            # Check if any match corresponds to the expected entity
            for match_city, match_dist in matches:
                if normalize_city_name(match_city) == normalize_city_name(entity_text):
                    positions.append((i, i + len(entity_normalized)))
                    break

    return positions


def create_labels(tokens: List[str], origin: str, destination: str, gaz: Gazetteer) -> List[str]:
    """
    Create BIO labels for tokens based on origin and destination.

    Strategy:
    1. Find all positions of origin and destination in tokens
    2. If multiple matches, use heuristic:
       - Origin appears first in sentence
       - Destination appears after origin
    3. Label with B-ORIGIN/I-ORIGIN and B-DEST/I-DEST
    """
    labels = ['O'] * len(tokens)

    # Find positions (with fuzzy matching for misspellings)
    origin_positions = find_entity_positions(tokens, origin, gaz)
    dest_positions = find_entity_positions(tokens, destination, gaz)

    # Select best match using heuristic
    selected_origin = None
    selected_dest = None

    if origin_positions:
        # Use first occurrence as origin
        selected_origin = origin_positions[0]

    if dest_positions:
        # Use last occurrence as destination (or first after origin)
        if selected_origin:
            # Find first dest after origin
            candidates = [pos for pos in dest_positions if pos[0] >= selected_origin[1]]
            if candidates:
                selected_dest = candidates[0]
            else:
                # If no dest after origin, might be inverted order - use last dest
                selected_dest = dest_positions[-1]
        else:
            # No origin found, use last dest
            selected_dest = dest_positions[-1]

    # Apply labels
    if selected_origin:
        start, end = selected_origin
        labels[start] = 'B-ORIGIN'
        for i in range(start + 1, end):
            labels[i] = 'I-ORIGIN'

    if selected_dest:
        start, end = selected_dest
        labels[start] = 'B-DEST'
        for i in range(start + 1, end):
            labels[i] = 'I-DEST'

    return labels


def convert_sentence_to_ner(sentence: str, origin: str, destination: str, is_valid: int, gaz: Gazetteer) -> Dict:
    """
    Convert a single sentence to NER format.

    For invalid sentences (is_valid=0), all tokens are labeled 'O'.
    """
    # Normalize and tokenize
    sentence = normalize_text_for_tokenization(sentence)
    tokens = simple_tokenize(sentence)

    # Create labels
    if is_valid == 0:
        # Invalid sentences: all tokens are 'O'
        labels = ['O'] * len(tokens)
    else:
        labels = create_labels(tokens, origin, destination, gaz)

    return {
        'tokens': tokens,
        'labels': labels
    }


def load_and_convert_dataset(csv_path: str) -> List[Dict]:
    """Load CSV and convert to NER format with fuzzy matching for misspellings."""
    # Initialize gazetteer for fuzzy matching
    gaz = Gazetteer()

    ner_data = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            sentence = row['sentence']
            origin = row.get('origin', '').strip()
            destination = row.get('destination', '').strip()
            is_valid = int(row.get('is_valid', 0))

            ner_example = convert_sentence_to_ner(sentence, origin, destination, is_valid, gaz)

            # Add metadata for analysis
            ner_example['metadata'] = {
                'sentenceID': row['sentenceID'],
                'origin': origin,
                'destination': destination,
                'is_valid': is_valid,
                'difficulty': row.get('difficulty', ''),
                'category': row.get('category', '')
            }

            ner_data.append(ner_example)

    return ner_data


def split_dataset(data: List[Dict], train_size=0.70, val_size=0.15, test_size=0.15, random_state=42):
    """
    Split dataset into train/val/test sets.

    Stratified split based on is_valid to maintain balance.
    """
    # Extract is_valid for stratification
    is_valid_labels = [example['metadata']['is_valid'] for example in data]

    # First split: separate test set (15%)
    train_val, test = train_test_split(
        data,
        test_size=test_size,
        random_state=random_state,
        stratify=is_valid_labels
    )

    # Second split: separate validation from training
    train_val_labels = [example['metadata']['is_valid'] for example in train_val]
    val_ratio = val_size / (train_size + val_size)  # 0.15 / 0.85 ≈ 0.176

    train, val = train_test_split(
        train_val,
        test_size=val_ratio,
        random_state=random_state,
        stratify=train_val_labels
    )

    return train, val, test


def save_ner_dataset(data: List[Dict], output_path: str):
    """Save NER dataset to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(data)} examples to {output_path}")


def print_statistics(data: List[Dict], split_name: str):
    """Print statistics about the NER dataset."""
    total = len(data)
    valid = sum(1 for ex in data if ex['metadata']['is_valid'] == 1)
    invalid = total - valid

    # Count labels
    label_counts = {'O': 0, 'B-ORIGIN': 0, 'I-ORIGIN': 0, 'B-DEST': 0, 'I-DEST': 0}
    total_tokens = 0

    for example in data:
        total_tokens += len(example['tokens'])
        for label in example['labels']:
            label_counts[label] += 1

    print(f"\n{split_name} Statistics:")
    print(f"  Total examples: {total}")
    print(f"  Valid orders: {valid} ({valid/total*100:.1f}%)")
    print(f"  Invalid orders: {invalid} ({invalid/total*100:.1f}%)")
    print(f"  Total tokens: {total_tokens}")
    print(f"  Label distribution:")
    for label, count in label_counts.items():
        print(f"    {label}: {count} ({count/total_tokens*100:.1f}%)")


def print_examples(data: List[Dict], n=3):
    """Print a few examples for verification."""
    print(f"\nSample Examples:")
    for i, example in enumerate(data[:n]):
        print(f"\nExample {i+1}:")
        print(f"  Tokens: {example['tokens']}")
        print(f"  Labels: {example['labels']}")
        print(f"  Origin: {example['metadata']['origin']}")
        print(f"  Destination: {example['metadata']['destination']}")
        print(f"  Valid: {example['metadata']['is_valid']}")


def main():
    """Main conversion pipeline."""
    print("Converting Travel Order Dataset to NER Format\n")

    # Paths
    project_root = Path(__file__).parent.parent
    train_csv_path = project_root / 'data' / 'train.csv'
    val_csv_path = project_root / 'data' / 'val.csv'
    test_csv_path = project_root / 'data' / 'test.csv'
    output_dir = project_root / 'data'

    # Check if split datasets exist
    if not train_csv_path.exists() or not val_csv_path.exists() or not test_csv_path.exists():
        print("Error: Split datasets not found!")
        print("Expected files:")
        print(f"  - {train_csv_path}")
        print(f"  - {val_csv_path}")
        print(f"  - {test_csv_path}")
        print("\nPlease run split_dataset.py first to create train/val/test splits")
        return

    # Load pre-split datasets (maintains stratified 33/33/34 difficulty distribution)
    print(f"Loading training data from {train_csv_path}")
    train = load_and_convert_dataset(str(train_csv_path))
    print(f"Loaded {len(train)} training examples")

    print(f"\nLoading validation data from {val_csv_path}")
    val = load_and_convert_dataset(str(val_csv_path))
    print(f"Loaded {len(val)} validation examples")

    print(f"\nLoading test data from {test_csv_path}")
    test = load_and_convert_dataset(str(test_csv_path))
    print(f"Loaded {len(test)} test examples")

    # Save splits
    train_path = output_dir / 'train_ner.json'
    val_path = output_dir / 'val_ner.json'
    test_path = output_dir / 'test_ner.json'

    save_ner_dataset(train, str(train_path))
    save_ner_dataset(val, str(val_path))
    save_ner_dataset(test, str(test_path))

    # Print statistics
    print_statistics(train, "TRAIN")
    print_statistics(val, "VALIDATION")
    print_statistics(test, "TEST")

    # Print examples
    print_examples(train, n=3)

    print("\nConversion complete!")
    print(f"\nOutput files:")
    print(f"  - {train_path}")
    print(f"  - {val_path}")
    print(f"  - {test_path}")


if __name__ == '__main__':
    main()
