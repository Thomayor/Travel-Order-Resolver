"""
Baseline Rule-Based NLP Module for Travel Order Extraction

This module implements a simple rule-based system to extract origin
and destination from French travel order sentences.

Expected Performance: 60-70% accuracy
"""

import re
from typing import Dict, List, Optional, Tuple
from .preprocessing import preprocess_for_matching, tokenize_french
from .gazetteer import Gazetteer, load_gazetteer


# Keywords for origin (will be preprocessed to match normalized text)
ORIGIN_KEYWORDS = [
    "de", "depuis", "en partance de", "au depart de",
    "en partant de", "a partir de", "depart"
]

# Keywords for destination (will be preprocessed to match normalized text)
DESTINATION_KEYWORDS = [
    "a", "vers", "pour", "jusqua", "en direction de",
    "direction", "arrivee"
]

# Common verbs in travel orders
TRAVEL_VERBS = [
    "aller", "partir", "voyager", "rendre", "déplacer",
    "veux", "voudrais", "souhaite", "aimerais", "dois"
]

# Words that indicate invalid orders
INVALID_INDICATORS = [
    "quel temps", "quelle heure est", "comment allez",
    "bonjour", "bonsoir", "merci", "azerty"
]


class BaselineExtractor:
    """
    Baseline rule-based extractor for travel orders.

    Uses keyword matching, gazetteer lookup, and heuristics
    to extract origin and destination from French sentences.
    """

    def __init__(self, gazetteer: Optional[Gazetteer] = None):
        """
        Initialize baseline extractor.

        Args:
            gazetteer: Optional gazetteer for location validation
        """
        self.gazetteer = gazetteer if gazetteer else load_gazetteer()

    def is_valid_order(self, text: str) -> bool:
        """
        Check if a sentence is a valid travel order.

        Args:
            text: Input sentence

        Returns:
            True if the sentence appears to be a valid travel order
        """
        text_normalized = preprocess_for_matching(text)

        # Check for invalid indicators
        for indicator in INVALID_INDICATORS:
            if indicator in text_normalized:
                return False

        # Check if at least one location is mentioned
        locations = self.gazetteer.find_matches(text_normalized)
        if len(locations) == 0:
            return False

        # Check if contains travel-related keywords
        has_travel_keyword = any(
            keyword in text_normalized
            for keyword in ORIGIN_KEYWORDS + DESTINATION_KEYWORDS + TRAVEL_VERBS
        )

        return has_travel_keyword or len(locations) >= 2

    def extract_with_keywords(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract origin and destination using keyword-based patterns.

        Args:
            text: Input sentence

        Returns:
            Tuple of (origin, destination) or (None, None)
        """
        text_normalized = preprocess_for_matching(text)
        tokens = text_normalized.split()

        origin = None
        destination = None

        # Find all locations in text
        all_locations = self.gazetteer.find_matches(text_normalized)
        if len(all_locations) == 0:
            return None, None

        # Pattern 1: "de X à Y" or "depuis X vers Y"
        for i, token in enumerate(tokens):
            # Look for origin keywords
            if token in ["de", "depuis"] and i + 1 < len(tokens):
                # Find next location after keyword
                for loc in all_locations:
                    loc_normalized = preprocess_for_matching(loc)
                    # Check if location appears after keyword
                    remaining_text = ' '.join(tokens[i+1:])
                    if loc_normalized in remaining_text and not origin:
                        origin = loc
                        break

            # Look for destination keywords
            if token in ["a", "vers", "pour"] and i + 1 < len(tokens):
                # Find next location after keyword
                for loc in all_locations:
                    loc_normalized = preprocess_for_matching(loc)
                    remaining_text = ' '.join(tokens[i+1:])
                    if loc_normalized in remaining_text and not destination:
                        destination = loc
                        break

        return origin, destination

    def extract_heuristic(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract using simple heuristics (first location = origin, last = destination).

        Args:
            text: Input sentence

        Returns:
            Tuple of (origin, destination) or (None, None)
        """
        text_normalized = preprocess_for_matching(text)
        locations = self.gazetteer.find_matches(text_normalized)

        if len(locations) == 0:
            return None, None
        elif len(locations) == 1:
            # Only one location - ambiguous
            # Check if preceded by "à", "vers", "pour" -> destination
            # Check if preceded by "de", "depuis" -> origin
            loc_normalized = preprocess_for_matching(locations[0])

            if any(f"{kw} {loc_normalized}" in text_normalized for kw in ["a", "vers", "pour"]):
                return None, locations[0]
            elif any(f"{kw} {loc_normalized}" in text_normalized for kw in ["de", "depuis"]):
                return locations[0], None
            else:
                # Default: single location is destination
                return None, locations[0]
        else:
            # Multiple locations: first = origin, last = destination
            return locations[0], locations[-1]

    def extract_direct_format(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract from direct format: "Je voudrais un billet X Y"

        Args:
            text: Input sentence

        Returns:
            Tuple of (origin, destination) or (None, None)
        """
        text_normalized = preprocess_for_matching(text)

        # Pattern: "billet X Y" or "ticket X Y"
        if "billet" in text_normalized or "ticket" in text_normalized:
            locations = self.gazetteer.find_matches(text_normalized)
            if len(locations) >= 2:
                # In direct format, typically: origin destination
                return locations[0], locations[1]

        return None, None

    def extract(self, text: str) -> Dict[str, Optional[str]]:
        """
        Main extraction method combining all strategies.

        Args:
            text: Input sentence

        Returns:
            Dictionary with 'origin', 'destination', 'valid', 'method' keys
        """
        # Check if valid order
        if not self.is_valid_order(text):
            return {
                'origin': None,
                'destination': None,
                'valid': False,
                'method': 'invalid'
            }

        # Strategy 1: Try keyword-based extraction
        origin, destination = self.extract_with_keywords(text)
        if origin and destination:
            return {
                'origin': origin,
                'destination': destination,
                'valid': True,
                'method': 'keywords'
            }

        # Strategy 2: Try direct format
        origin_direct, dest_direct = self.extract_direct_format(text)
        if origin_direct and dest_direct:
            return {
                'origin': origin_direct,
                'destination': dest_direct,
                'valid': True,
                'method': 'direct_format'
            }

        # Strategy 3: Use heuristics
        origin_heur, dest_heur = self.extract_heuristic(text)

        # Combine results
        final_origin = origin or origin_direct or origin_heur
        final_dest = destination or dest_direct or dest_heur

        if final_origin or final_dest:
            return {
                'origin': final_origin,
                'destination': final_dest,
                'valid': True,
                'method': 'heuristic'
            }

        # No extraction possible
        return {
            'origin': None,
            'destination': None,
            'valid': False,
            'method': 'failed'
        }

    def process_sentence(self, sentence_id: str, sentence: str) -> Dict:
        """
        Process a single sentence and return results.

        Args:
            sentence_id: Unique identifier for the sentence
            sentence: Input sentence text

        Returns:
            Dictionary with sentence_id, origin, destination, valid
        """
        result = self.extract(sentence)
        result['sentence_id'] = sentence_id
        result['sentence'] = sentence
        return result

    def process_batch(self, sentences: List[Tuple[str, str]]) -> List[Dict]:
        """
        Process a batch of sentences.

        Args:
            sentences: List of (sentence_id, sentence) tuples

        Returns:
            List of result dictionaries
        """
        results = []
        for sentence_id, sentence in sentences:
            result = self.process_sentence(sentence_id, sentence)
            results.append(result)
        return results

    def format_output_csv(self, result: Dict) -> str:
        """
        Format result as CSV line.

        Args:
            result: Result dictionary from process_sentence

        Returns:
            CSV-formatted string: "sentenceID,Origin,Destination"
        """
        sentence_id = result['sentence_id']
        origin = result['origin'] if result['origin'] else 'INVALID'
        destination = result['destination'] if result['destination'] else 'INVALID'

        return f"{sentence_id},{origin},{destination}"

    def evaluate(self, test_data: List[Tuple[str, str, str, str]]) -> Dict[str, float]:
        """
        Evaluate extractor performance on test data.

        Args:
            test_data: List of (id, sentence, true_origin, true_dest) tuples

        Returns:
            Dictionary with accuracy, precision, recall, f1 metrics
        """
        correct = 0
        total = len(test_data)

        origin_correct = 0
        dest_correct = 0

        for sentence_id, sentence, true_origin, true_dest in test_data:
            result = self.extract(sentence)

            # Check if both are correct
            if (result['origin'] == true_origin and
                result['destination'] == true_dest):
                correct += 1

            # Check individual accuracy
            if result['origin'] == true_origin:
                origin_correct += 1
            if result['destination'] == true_dest:
                dest_correct += 1

        accuracy = correct / total if total > 0 else 0
        origin_accuracy = origin_correct / total if total > 0 else 0
        dest_accuracy = dest_correct / total if total > 0 else 0

        return {
            'accuracy': accuracy,
            'total': total,
            'correct': correct,
            'origin_accuracy': origin_accuracy,
            'destination_accuracy': dest_accuracy
        }


def load_extractor(gazetteer_path: Optional[str] = None) -> BaselineExtractor:
    """
    Load and return a BaselineExtractor instance.

    Args:
        gazetteer_path: Optional path to custom gazetteer JSON

    Returns:
        BaselineExtractor instance
    """
    if gazetteer_path:
        gaz = load_gazetteer(gazetteer_path)
    else:
        gaz = load_gazetteer()

    return BaselineExtractor(gazetteer=gaz)


if __name__ == "__main__":
    # Example usage
    print("=== Baseline NLP Extractor Demo ===\n")

    # Create extractor
    extractor = BaselineExtractor()
    print("Extractor initialized with gazetteer\n")

    # Test sentences
    test_sentences = [
        ("1", "Je veux aller de Paris à Lyon"),
        ("2", "Train pour Marseille depuis Toulouse"),
        ("3", "Je voudrais un billet Bordeaux Nice"),
        ("4", "Comment me rendre à Tours depuis Orleans"),
        ("5", "Quel temps fait-il à Paris?"),  # Invalid
        ("6", "Je pars demain"),  # Invalid - no locations
        ("7", "Port-Boulet vers La Rochelle"),
        ("8", "À quelle heure y a-t-il des trains vers Lyon en partance de Paris?"),
    ]

    print("Processing sentences:\n")
    for sent_id, sentence in test_sentences:
        result = extractor.process_sentence(sent_id, sentence)
        print(f"[{sent_id}] {sentence}")
        print(f"    Origin: {result['origin']}")
        print(f"    Destination: {result['destination']}")
        print(f"    Valid: {result['valid']} | Method: {result['method']}")
        print(f"    CSV: {extractor.format_output_csv(result)}")
        print()

    print("✅ Baseline extractor functional!")
