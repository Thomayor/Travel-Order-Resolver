"""
Training Script for CamemBERT NER Model

Fine-tunes CamemBERT on the Travel Order NER task.

Usage:
    python scripts/train_camembert.py

Hyperparameters (can be modified):
    - epochs: 20
    - batch_size: 16
    - learning_rate: 2e-5
    - warmup_ratio: 0.1
    - weight_decay: 0.01

Requirements:
    - Datasets must be converted to NER format first
    - Run: python scripts/convert_dataset_to_ner.py
"""

import sys
import argparse
from pathlib import Path

# Add src to path (3 levels up: train_camembert.py -> camembert -> scripts -> root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from nlp.transformer import CamembertNER


def main():
    parser = argparse.ArgumentParser(description='Train CamemBERT NER model')
    parser.add_argument('--train', type=str, default='data/processed/train_ner.json',
                        help='Path to training data')
    parser.add_argument('--val', type=str, default='data/processed/val_ner.json',
                        help='Path to validation data')
    parser.add_argument('--output', type=str, default='models/camembert-ner',
                        help='Output directory for model')
    parser.add_argument('--epochs', type=int, default=20,
                        help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=16,
                        help='Batch size per device')
    parser.add_argument('--learning-rate', type=float, default=2e-5,
                        help='Learning rate')
    parser.add_argument('--warmup-ratio', type=float, default=0.1,
                        help='Warmup ratio')
    parser.add_argument('--weight-decay', type=float, default=0.01,
                        help='Weight decay')

    args = parser.parse_args()

    # Resolve paths
    train_path = project_root / args.train
    val_path = project_root / args.val
    output_dir = project_root / args.output

    # Check if datasets exist
    if not train_path.exists():
        print(f"Error: Training data not found at {train_path}")
        print("\nPlease run the conversion script first:")
        print("  python scripts/convert_dataset_to_ner.py")
        sys.exit(1)

    if not val_path.exists():
        print(f"Error: Validation data not found at {val_path}")
        print("\nPlease run the conversion script first:")
        print("  python scripts/convert_dataset_to_ner.py")
        sys.exit(1)

    print("=" * 70)
    print("CamemBERT NER Training")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Train data: {train_path}")
    print(f"  Val data: {val_path}")
    print(f"  Output dir: {output_dir}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Learning rate: {args.learning_rate}")
    print(f"  Warmup ratio: {args.warmup_ratio}")
    print(f"  Weight decay: {args.weight_decay}")
    print()

    # Initialize model
    print("Initializing CamemBERT model...")
    model = CamembertNER(model_name="camembert-base")

    # Train
    try:
        trainer = model.train(
            train_path=str(train_path),
            val_path=str(val_path),
            output_dir=str(output_dir),
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            warmup_ratio=args.warmup_ratio,
            weight_decay=args.weight_decay
        )

        print("\n" + "=" * 70)
        print("Training completed successfully!")
        print("=" * 70)
        print(f"\nModel saved to: {output_dir}")
        print("\nTo evaluate the model, run:")
        print("  python scripts/evaluate_camembert.py")

    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
