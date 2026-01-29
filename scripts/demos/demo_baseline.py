"""
Demo script for baseline NLP extraction
"""
import sys
sys.path.insert(0, 'src')
from nlp.baseline import BaselineExtractor

print('=== Baseline NLP Extractor Demo ===\n')

# Create extractor
extractor = BaselineExtractor()
print(f"Extractor initialized with {len(extractor.gazetteer)} locations\n")

# Test sentences
test_sentences = [
    ("1", "Je veux aller de Paris a Lyon"),
    ("2", "Train pour Marseille depuis Toulouse"),
    ("3", "Je voudrais un billet Bordeaux Nice"),
    ("4", "Comment me rendre a Tours depuis Orleans"),
    ("5", "Quel temps fait-il a Paris?"),  # Invalid
    ("6", "Je pars demain"),  # Invalid - no locations
    ("7", "Port-Boulet vers La Rochelle"),
    ("8", "A quelle heure y a-t-il des trains vers Lyon en partance de Paris?"),
    ("9", "Toulouse Paris demain"),
    ("10", "azerty qwerty"),  # Invalid - garbage
]

print("Processing sentences:\n")
print("-" * 80)

for sent_id, sentence in test_sentences:
    result = extractor.process_sentence(sent_id, sentence)

    print(f"\n[{sent_id}] {sentence}")
    print(f"    Origin:      {result['origin']}")
    print(f"    Destination: {result['destination']}")
    print(f"    Valid:       {result['valid']:5} | Method: {result['method']}")
    print(f"    CSV:         {extractor.format_output_csv(result)}")

print("\n" + "-" * 80)
print("\nModule baseline fonctionnel!")
