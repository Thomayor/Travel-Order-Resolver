"""
Demo Script for CamemBERT NER Model

Interactive demo to test the trained CamemBERT model on custom sentences.

Usage:
    python scripts/demo_camembert.py
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from nlp.transformer import load_pretrained_model


def demo_interactive():
    """Interactive demo - test model on user input."""
    model_path = project_root / 'models' / 'camembert-ner'

    if not model_path.exists():
        print("Error: Model not found!")
        print(f"Expected location: {model_path}")
        print("\nPlease train the model first:")
        print("  python scripts/train_camembert.py")
        sys.exit(1)

    print("=" * 70)
    print("CamemBERT NER Model - Interactive Demo")
    print("=" * 70)
    print(f"\nLoading model from: {model_path}")

    model = load_pretrained_model(str(model_path))

    print("\nModel loaded successfully!")
    print("\nType French travel order sentences to extract origin and destination.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            # Get user input
            sentence = input("Enter sentence: ").strip()

            if sentence.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            if not sentence:
                continue

            # Predict
            tokens, labels, origin, destination = model.predict(sentence)

            # Display results
            print(f"\nTokens: {tokens}")
            print(f"Labels: {labels}")
            print(f"\nExtracted:")
            print(f"  Origin:      {origin or 'NOT FOUND'}")
            print(f"  Destination: {destination or 'NOT FOUND'}")

            if origin and destination:
                print(f"\nResult: {origin} -> {destination}")
            else:
                print(f"\nResult: INVALID (missing origin or destination)")

            print()

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


def demo_examples():
    """Demo with predefined examples."""
    model_path = project_root / 'models' / 'camembert-ner'

    if not model_path.exists():
        print("Error: Model not found!")
        print(f"Expected location: {model_path}")
        print("\nPlease train the model first:")
        print("  python scripts/train_camembert.py")
        sys.exit(1)

    print("=" * 70)
    print("CamemBERT NER Model - Example Predictions")
    print("=" * 70)
    print(f"\nLoading model from: {model_path}")

    model = load_pretrained_model(str(model_path))

    print("\nModel loaded successfully!\n")

    # Test examples
    examples = [
        "Je veux aller de Paris à Lyon",
        "Un billet de Marseille à Bordeaux s'il vous plaît",
        "Direction Toulouse en partant de Lille",
        "Avec mon ami Albert je voudrais aller de Reims à Tours",
        "billet Port-Boulet Aix-en-Provence",
        "Je veux aller de Bordeau à Limogees",  # Misspellings
        "Bonjour comment allez-vous",  # Invalid
    ]

    for i, sentence in enumerate(examples, 1):
        print(f"Example {i}: {sentence}")

        try:
            tokens, labels, origin, destination = model.predict(sentence)

            if origin and destination:
                print(f"  Result: {origin} -> {destination}")
            else:
                print(f"  Result: INVALID")
        except Exception as e:
            print(f"  Error: {e}")

        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Demo CamemBERT NER model')
    parser.add_argument('--mode', type=str, choices=['interactive', 'examples'],
                        default='examples',
                        help='Demo mode (default: examples)')

    args = parser.parse_args()

    if args.mode == 'interactive':
        demo_interactive()
    else:
        demo_examples()


if __name__ == '__main__':
    main()
