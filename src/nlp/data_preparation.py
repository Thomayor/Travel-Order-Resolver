"""
Data Preparation Module for CamemBERT Token Classification

Converts word-level BIO NER data to subword-tokenized format for CamemBERT training.
Loads only the tokenizer (no model weights) for efficiency.
"""

import json
import argparse
import warnings
from pathlib import Path
from typing import Dict, List, Optional

LABEL2ID = {"O": 0, "B-ORIGIN": 1, "I-ORIGIN": 2, "B-DEST": 3, "I-DEST": 4}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}
DEFAULT_MODEL_NAME = "camembert-base"
MAX_LENGTH = 128
DEFAULT_DATA_DIR = "data/processed"


class DataPreparator:
    """
    Converts word-level NER data to subword-tokenized format for CamemBERT.

    Only loads the tokenizer (not model weights) to minimize memory usage.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, max_length: int = MAX_LENGTH):
        try:
            from transformers import CamembertTokenizerFast
        except ImportError as e:
            raise ImportError(
                "transformers package is required. Install with: pip install transformers"
            ) from e

        self.model_name = model_name
        self.max_length = max_length
        self.tokenizer = CamembertTokenizerFast.from_pretrained(model_name)

    def load_word_level_data(self, json_path: str) -> List[Dict]:
        """Load and validate word-level NER data from JSON file."""
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {json_path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        for i, example in enumerate(data):
            tokens = example.get("tokens", [])
            labels = example.get("labels", [])

            if len(tokens) != len(labels):
                raise ValueError(
                    f"Example {i}: token count ({len(tokens)}) != label count ({len(labels)})"
                )

            for label in labels:
                if label not in LABEL2ID:
                    raise ValueError(
                        f"Example {i}: unknown label '{label}'. Valid labels: {list(LABEL2ID.keys())}"
                    )

        return data

    def align_labels_with_tokens(self, tokens: List[str], word_labels: List[str]) -> Dict:
        """
        Tokenize words into subwords and align BIO labels.

        Special tokens ([CLS], [SEP]) and continuation subwords get label -100.
        """
        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_length,
            padding=False,
        )

        word_ids = encoding.word_ids()
        aligned_labels = []
        prev_word_id = None

        for word_id in word_ids:
            if word_id is None:
                aligned_labels.append(-100)
            elif word_id != prev_word_id:
                aligned_labels.append(LABEL2ID[word_labels[word_id]])
            else:
                aligned_labels.append(-100)
            prev_word_id = word_id

        return {
            "input_ids": encoding["input_ids"],
            "attention_mask": encoding["attention_mask"],
            "labels": aligned_labels,
        }

    def prepare_split(
        self,
        input_path: str,
        output_path: str,
        show_progress: bool = True,
    ) -> Dict:
        """
        Process a single data split: load, align, save as JSONL.

        Returns stats dict with num_examples, num_truncated, avg_subword_len, max_subword_len.
        """
        try:
            from datasets import Dataset
        except ImportError as e:
            raise ImportError(
                "datasets package is required. Install with: pip install datasets"
            ) from e

        data = self.load_word_level_data(input_path)

        processed = []
        num_truncated = 0
        subword_lengths = []

        for i, example in enumerate(data):
            if show_progress and i % 500 == 0:
                print(f"  Processing {i}/{len(data)}...")

            tokens = example["tokens"]
            labels = example["labels"]
            aligned = self.align_labels_with_tokens(tokens, labels)

            subword_len = len(aligned["input_ids"])
            subword_lengths.append(subword_len)

            # Check if truncated: more words than max_length could accommodate
            if len(tokens) > self.max_length - 2:
                num_truncated += 1

            processed.append(aligned)

        # Build HuggingFace Dataset
        dataset_dict = {
            "input_ids": [e["input_ids"] for e in processed],
            "attention_mask": [e["attention_mask"] for e in processed],
            "labels": [e["labels"] for e in processed],
        }
        dataset = Dataset.from_dict(dataset_dict)

        # Ensure output directory exists
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        dataset.to_json(str(out_path), force_ascii=False)

        stats = {
            "num_examples": len(data),
            "num_truncated": num_truncated,
            "avg_subword_len": sum(subword_lengths) / len(subword_lengths) if subword_lengths else 0,
            "max_subword_len": max(subword_lengths) if subword_lengths else 0,
        }

        if show_progress:
            print(f"  Saved {len(data)} examples to {output_path}")
            print(f"  Truncated: {num_truncated}, Avg subword len: {stats['avg_subword_len']:.1f}")

        return stats

    def prepare_all(
        self,
        data_dir: str = DEFAULT_DATA_DIR,
        splits: List[str] = None,
    ) -> Dict[str, Dict]:
        """Process all splits, skipping missing files with a warning."""
        if splits is None:
            splits = ["train", "val", "test"]

        data_dir = Path(data_dir)
        results = {}

        for split in splits:
            input_path = data_dir / f"{split}_ner.json"
            output_path = data_dir / f"{split}_tokens.json"

            if not input_path.exists():
                warnings.warn(f"Split '{split}' not found: {input_path} — skipping")
                continue

            print(f"Processing split: {split}")
            results[split] = self.prepare_split(str(input_path), str(output_path))

        return results


def prepare_split(
    input_path: str,
    output_path: str,
    model_name: str = DEFAULT_MODEL_NAME,
    max_length: int = MAX_LENGTH,
    show_progress: bool = True,
) -> Dict:
    """Convenience function to prepare a single split without managing DataPreparator."""
    preparator = DataPreparator(model_name=model_name, max_length=max_length)
    return preparator.prepare_split(input_path, output_path, show_progress=show_progress)


def prepare_all_splits(
    data_dir: str = DEFAULT_DATA_DIR,
    splits: Optional[List[str]] = None,
    model_name: str = DEFAULT_MODEL_NAME,
    max_length: int = MAX_LENGTH,
) -> Dict[str, Dict]:
    """Convenience function to prepare all splits without managing DataPreparator."""
    preparator = DataPreparator(model_name=model_name, max_length=max_length)
    return preparator.prepare_all(data_dir=data_dir, splits=splits)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare tokenized data for CamemBERT training")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="Directory with NER JSON files")
    parser.add_argument("--splits", nargs="+", default=["train", "val", "test"], help="Splits to process")
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME, help="CamemBERT tokenizer to use")
    parser.add_argument("--max-length", type=int, default=MAX_LENGTH, help="Max subword sequence length")
    args = parser.parse_args()

    print(f"Loading tokenizer: {args.model_name}")
    preparator = DataPreparator(model_name=args.model_name, max_length=args.max_length)
    results = preparator.prepare_all(data_dir=args.data_dir, splits=args.splits)

    print("\nSummary:")
    for split, stats in results.items():
        print(f"  {split}: {stats['num_examples']} examples, {stats['num_truncated']} truncated")
