"""
CamemBERT Transformer Module for Travel Order NER

This module implements a fine-tuned CamemBERT model for Named Entity Recognition
to extract origin and destination cities from French travel order sentences.

Expected Performance: 85%+ accuracy (vs 70% baseline)
"""

import json
import torch
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from transformers import (
    CamembertForTokenClassification,
    CamembertTokenizerFast,
    Trainer,
    TrainingArguments,
    DataCollatorForTokenClassification,
    EvalPrediction
)
from datasets import Dataset
from evaluate import load as load_metric


class CamembertNER:
    """
    CamemBERT-based Named Entity Recognition model for travel orders.

    Fine-tunes CamemBERT on token classification task with 5 labels:
    - B-ORIGIN: Beginning of origin city
    - I-ORIGIN: Inside origin city
    - B-DEST: Beginning of destination city
    - I-DEST: Inside destination city
    - O: Outside (not part of any entity)
    """

    # Label mappings
    LABEL2ID = {
        "O": 0,
        "B-ORIGIN": 1,
        "I-ORIGIN": 2,
        "B-DEST": 3,
        "I-DEST": 4
    }

    ID2LABEL = {
        0: "O",
        1: "B-ORIGIN",
        2: "I-ORIGIN",
        3: "B-DEST",
        4: "I-DEST"
    }

    def __init__(self, model_name: str = "camembert-base", model_path: Optional[str] = None):
        """
        Initialize CamemBERT NER model.

        Args:
            model_name: Pretrained model name (default: "camembert-base")
            model_path: Path to fine-tuned model (if loading existing model)
        """
        self.tokenizer = CamembertTokenizerFast.from_pretrained(
            model_path if model_path else model_name
        )

        if model_path:
            # Load fine-tuned model
            self.model = CamembertForTokenClassification.from_pretrained(model_path)
        else:
            # Initialize new model for training
            self.model = CamembertForTokenClassification.from_pretrained(
                model_name,
                num_labels=5,
                id2label=self.ID2LABEL,
                label2id=self.LABEL2ID
            )

        # Move to GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        # Load gazetteer for post-processing validation
        from .gazetteer import load_gazetteer
        self.gazetteer = load_gazetteer()

        print(f"Initialized CamemBERT NER on device: {self.device}")

    def load_ner_dataset(self, json_path: str) -> Dataset:
        """
        Load NER dataset from JSON file and convert to HuggingFace Dataset.

        Args:
            json_path: Path to NER JSON file (train/val/test)

        Returns:
            HuggingFace Dataset
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract tokens and labels
        dataset_dict = {
            'tokens': [example['tokens'] for example in data],
            'labels': [[self.LABEL2ID[label] for label in example['labels']] for example in data],
            'metadata': [example.get('metadata', {}) for example in data]
        }

        return Dataset.from_dict(dataset_dict)

    def tokenize_and_align_labels(self, examples: Dict) -> Dict:
        """
        Tokenize text and align labels with subword tokens.

        CamemBERT uses SentencePiece tokenization which can split words into subwords.
        We need to align the original word-level labels with the subword tokens.

        Strategy:
        - First subword of a word gets the original label
        - Subsequent subwords get -100 (ignored in loss calculation)

        Args:
            examples: Batch of examples with 'tokens' and 'labels'

        Returns:
            Tokenized examples with aligned labels
        """
        # Tokenize with is_split_into_words=True since we already have tokens
        tokenized_inputs = self.tokenizer(
            examples['tokens'],
            truncation=True,
            is_split_into_words=True,
            padding=False,  # Don't pad here, DataCollator will handle it
            max_length=128  # Max sequence length
        )

        labels = []
        for i, label in enumerate(examples['labels']):
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            previous_word_idx = None
            label_ids = []

            for word_idx in word_ids:
                # Special tokens have a word id that is None
                if word_idx is None:
                    label_ids.append(-100)
                # First token of each word gets the label
                elif word_idx != previous_word_idx:
                    label_ids.append(label[word_idx])
                # Subsequent tokens of the same word get -100
                else:
                    label_ids.append(-100)

                previous_word_idx = word_idx

            labels.append(label_ids)

        tokenized_inputs["labels"] = labels
        return tokenized_inputs

    def compute_metrics(self, pred: EvalPrediction) -> Dict:
        """
        Compute metrics for evaluation.

        Metrics:
        - Precision, Recall, F1 for each label
        - Overall accuracy

        Args:
            pred: Predictions from Trainer

        Returns:
            Dictionary of metrics
        """
        predictions, labels = pred.predictions, pred.label_ids

        # Get predicted labels (argmax)
        predictions = np.argmax(predictions, axis=2)

        # Remove ignored index (special tokens)
        true_predictions = [
            [self.ID2LABEL[p] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        true_labels = [
            [self.ID2LABEL[l] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]

        # Load seqeval metric
        metric = load_metric("seqeval")
        results = metric.compute(predictions=true_predictions, references=true_labels)

        return {
            "precision": results["overall_precision"],
            "recall": results["overall_recall"],
            "f1": results["overall_f1"],
            "accuracy": results["overall_accuracy"],
        }

    def train(
        self,
        train_path: str,
        val_path: str,
        output_dir: str = "models/camembert-ner",
        num_epochs: int = 4,
        batch_size: int = 16,
        learning_rate: float = 2e-5,
        warmup_ratio: float = 0.1,
        weight_decay: float = 0.01
    ):
        """
        Fine-tune CamemBERT on NER task.

        Args:
            train_path: Path to training NER JSON
            val_path: Path to validation NER JSON
            output_dir: Directory to save model checkpoints
            num_epochs: Number of training epochs (default: 4)
            batch_size: Batch size per device (default: 16)
            learning_rate: Learning rate (default: 2e-5)
            warmup_ratio: Warmup ratio (default: 0.1)
            weight_decay: Weight decay (default: 0.01)
        """
        print(f"\nLoading datasets...")
        train_dataset = self.load_ner_dataset(train_path)
        val_dataset = self.load_ner_dataset(val_path)

        print(f"Train examples: {len(train_dataset)}")
        print(f"Validation examples: {len(val_dataset)}")

        # Tokenize datasets
        print("\nTokenizing datasets...")
        train_dataset = train_dataset.map(
            self.tokenize_and_align_labels,
            batched=True,
            remove_columns=train_dataset.column_names
        )
        val_dataset = val_dataset.map(
            self.tokenize_and_align_labels,
            batched=True,
            remove_columns=val_dataset.column_names
        )

        # Data collator for dynamic padding
        data_collator = DataCollatorForTokenClassification(
            tokenizer=self.tokenizer,
            padding=True
        )

        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            eval_strategy="epoch",
            save_strategy="epoch",
            learning_rate=learning_rate,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            num_train_epochs=num_epochs,
            weight_decay=weight_decay,
            warmup_ratio=warmup_ratio,
            logging_dir=f"{output_dir}/logs",
            logging_steps=50,
            load_best_model_at_end=True,
            metric_for_best_model="f1",
            save_total_limit=3,  # Keep only 3 best checkpoints
            fp16=torch.cuda.is_available(),  # Mixed precision if GPU available
            report_to=["tensorboard"],  # Log to TensorBoard
            push_to_hub=False
        )

        # Initialize Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
            compute_metrics=self.compute_metrics
        )

        # Train
        print(f"\nStarting training for {num_epochs} epochs...")
        print(f"Device: {self.device}")
        print(f"Batch size: {batch_size}")
        print(f"Learning rate: {learning_rate}")

        trainer.train()

        # Save final model
        print(f"\nSaving model to {output_dir}")
        trainer.save_model(output_dir)
        self.tokenizer.save_pretrained(output_dir)

        print("Training complete!")

        return trainer

    def predict(self, text: str) -> Tuple[List[str], List[str], Optional[str], Optional[str]]:
        """
        Predict origin and destination from text.

        Args:
            text: Input sentence

        Returns:
            Tuple of (tokens, labels, origin, destination)
        """
        # Simple tokenization
        tokens = text.split()

        # Tokenize with model tokenizer
        inputs = self.tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)

        # Predict
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=2)

        # Convert predictions to labels
        predicted_labels = []
        word_ids = inputs.word_ids(batch_index=0)
        previous_word_idx = None

        for idx, word_idx in enumerate(word_ids):
            if word_idx is None:
                continue
            if word_idx != previous_word_idx:
                label_id = predictions[0][idx].item()
                predicted_labels.append(self.ID2LABEL[label_id])
            previous_word_idx = word_idx

        # Extract entities using post-processing
        from .postprocessing import extract_entities, validate_against_gazetteer
        origin_raw, destination_raw = extract_entities(tokens, predicted_labels)

        # Validate and correct entities with fuzzy matching (Levenshtein ≤ 2)
        # This handles residual misspellings: "parisi" → "Paris"
        # If validation fails (ambiguous like "aix"), keep raw entity for suggestion system
        origin = validate_against_gazetteer(origin_raw, self.gazetteer) if origin_raw else None
        if origin is None and origin_raw:
            origin = origin_raw  # Keep raw entity for suggest_city() in CLI

        destination = validate_against_gazetteer(destination_raw, self.gazetteer) if destination_raw else None
        if destination is None and destination_raw:
            destination = destination_raw  # Keep raw entity for suggest_city() in CLI

        return tokens, predicted_labels, origin, destination

    def evaluate_on_test(self, test_path: str, output_path: Optional[str] = None) -> Dict:
        """
        Evaluate model on test set.

        Args:
            test_path: Path to test NER JSON
            output_path: Optional path to save detailed results

        Returns:
            Dictionary of metrics
        """
        print(f"\nLoading test dataset from {test_path}")
        test_dataset = self.load_ner_dataset(test_path)

        print(f"Test examples: {len(test_dataset)}")

        # Tokenize
        test_dataset = test_dataset.map(
            self.tokenize_and_align_labels,
            batched=True,
            remove_columns=test_dataset.column_names
        )

        # Data collator
        data_collator = DataCollatorForTokenClassification(
            tokenizer=self.tokenizer,
            padding=True
        )

        # Trainer for evaluation
        trainer = Trainer(
            model=self.model,
            data_collator=data_collator,
            compute_metrics=self.compute_metrics
        )

        # Evaluate
        print("\nEvaluating...")
        results = trainer.evaluate(test_dataset)

        print("\nTest Results:")
        for key, value in results.items():
            print(f"  {key}: {value:.4f}")

        # Save results if requested
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to {output_path}")

        return results


def load_pretrained_model(model_path: str) -> CamembertNER:
    """
    Load a fine-tuned CamemBERT NER model.

    Args:
        model_path: Path to saved model directory

    Returns:
        CamembertNER instance with loaded model
    """
    return CamembertNER(model_path=model_path)


if __name__ == '__main__':
    # Demo: Initialize model
    print("CamemBERT NER Module")
    print("=" * 50)

    ner_model = CamembertNER()

    # Check if datasets exist
    project_root = Path(__file__).parent.parent.parent
    train_path = project_root / 'data' / 'train_ner.json'
    val_path = project_root / 'data' / 'val_ner.json'

    if train_path.exists() and val_path.exists():
        print("\nDatasets found!")
        print(f"Train: {train_path}")
        print(f"Val: {val_path}")
        print("\nTo train the model, run:")
        print("  python scripts/train_camembert.py")
    else:
        print("\nDatasets not found. Please run:")
        print("  python scripts/convert_dataset_to_ner.py")
