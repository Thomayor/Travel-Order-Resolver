"""
Gazetteer Module for French Cities and Train Stations

This module provides functionality to load and match French city and station names.
Used for Named Entity Recognition in travel order sentences.
"""

import json
import csv
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
from .preprocessing import preprocess_for_matching, fuzzy_normalize


# Major French cities with train stations
MAJOR_FRENCH_CITIES = [
    # Top 50 French cities
    "Paris", "Lyon", "Marseille", "Toulouse", "Bordeaux", "Nice", "Nantes",
    "Strasbourg", "Montpellier", "Lille", "Rennes", "Reims", "Le Havre",
    "Saint-Étienne", "Toulon", "Grenoble", "Dijon", "Angers", "Nîmes",
    "Villeurbanne", "Clermont-Ferrand", "Limoges", "Tours", "Amiens",
    "Metz", "Besançon", "Perpignan", "Orléans", "Brest", "Mulhouse",
    "Caen", "Boulogne-Billancourt", "Rouen", "Nancy", "Argenteuil",
    "Saint-Denis", "Montreuil", "Roubaix", "Avignon", "Tourcoing",
    "Poitiers", "Nanterre", "Créteil", "Versailles", "Pau", "Courbevoie",
    "Vitry-sur-Seine", "Colombes", "Aulnay-sous-Bois", "Asnières-sur-Seine"
]

# Multi-word station names (with hyphens or spaces)
MULTI_WORD_STATIONS = [
    "Port-Boulet", "La Rochelle", "Le Havre", "Le Mans", "La Souterraine",
    "Aix-en-Provence", "Bourg-Saint-Maurice", "Bourg-en-Bresse",
    "Saint-Pierre-des-Corps", "Vitry-le-François", "Le Creusot",
    "Saint-Étienne", "Saint-Nazaire", "Saint-Malo", "Saint-Brieuc",
    "Aix-les-Bains", "Châlons-en-Champagne", "Nogent-sur-Marne"
]

# Cities that are also common person names
AMBIGUOUS_CITY_NAMES = {
    "Paris": "person_or_city",
    "Albert": "person_or_city",
    "Florence": "person_or_city",
    "Lourdes": "person_or_city",
    "Amiens": "city"  # Can be confused with "amis" (friends)
}

# Common misspellings and variations
CITY_ALIASES = {
    "paris": ["paris", "pari", "parris", "pariz"],
    "lyon": ["lyon", "lyons", "liyon", "lyone"],
    "marseille": ["marseille", "marceille", "marsseille", "marseile"],
    "toulouse": ["toulouse", "tolouse", "toulouze", "thoulose"],
    "bordeaux": ["bordeaux", "bordo", "bordeax", "borbeaux"],
    "nice": ["nice", "nise", "nices"],
    "lille": ["lille", "lile", "lilles"],
    "strasbourg": ["strasbourg", "straburg", "strassbourg"],
    "nantes": ["nantes", "nante", "nanthe"],
    "montpellier": ["montpellier", "montpelier", "montpellié"],
}


class Gazetteer:
    """
    Gazetteer for French cities and train stations.

    Provides methods to load, search, and match location names
    with support for variations, misspellings, and fuzzy matching.
    """

    def __init__(self):
        """Initialize gazetteer with default French cities."""
        self.cities: Set[str] = set()
        self.stations: Set[str] = set()
        self.aliases: Dict[str, List[str]] = {}
        self.normalized_to_original: Dict[str, str] = {}

        # Load default data
        self._load_default_cities()

    def _load_default_cities(self):
        """Load default list of major French cities."""
        for city in MAJOR_FRENCH_CITIES:
            self.add_city(city)

        for station in MULTI_WORD_STATIONS:
            self.add_station(station)

        # Add aliases
        self.aliases = CITY_ALIASES.copy()

    def add_city(self, city_name: str):
        """
        Add a city to the gazetteer.

        Args:
            city_name: Name of the city to add
        """
        self.cities.add(city_name)
        normalized = preprocess_for_matching(city_name)
        self.normalized_to_original[normalized] = city_name

    def add_station(self, station_name: str):
        """
        Add a train station to the gazetteer.

        Args:
            station_name: Name of the station to add
        """
        self.stations.add(station_name)
        normalized = preprocess_for_matching(station_name)
        self.normalized_to_original[normalized] = station_name

    def add_alias(self, city: str, alias: str):
        """
        Add an alias or variation for a city name.

        Args:
            city: Canonical city name
            alias: Alternative name or misspelling
        """
        city_normalized = preprocess_for_matching(city)
        if city_normalized not in self.aliases:
            self.aliases[city_normalized] = []
        self.aliases[city_normalized].append(alias)

    def is_valid_location(self, name: str) -> bool:
        """
        Check if a name is a valid city or station.

        Args:
            name: Location name to check

        Returns:
            True if the name is in the gazetteer
        """
        normalized = preprocess_for_matching(name)
        return normalized in self.normalized_to_original

    def get_canonical_name(self, name: str) -> Optional[str]:
        """
        Get the canonical (properly formatted) name for a location.

        Args:
            name: Location name (possibly misspelled or unnormalized)

        Returns:
            Canonical name if found, None otherwise
        """
        normalized = preprocess_for_matching(name)
        return self.normalized_to_original.get(normalized)

    def find_matches(self, text: str, min_length: int = 3) -> List[str]:
        """
        Find all location names mentioned in a text.

        Args:
            text: Text to search for location names
            min_length: Minimum length for a match

        Returns:
            List of canonical location names found
        """
        matches = []
        text_normalized = preprocess_for_matching(text)
        words = text_normalized.split()

        # Try to match single words
        for word in words:
            if len(word) >= min_length and word in self.normalized_to_original:
                canonical = self.normalized_to_original[word]
                if canonical not in matches:
                    matches.append(canonical)

        # Try to match multi-word names (2-4 words)
        for length in range(2, 5):
            for i in range(len(words) - length + 1):
                phrase = ' '.join(words[i:i+length])
                if phrase in self.normalized_to_original:
                    canonical = self.normalized_to_original[phrase]
                    if canonical not in matches:
                        matches.append(canonical)

        return matches

    def fuzzy_match(self, name: str, max_distance: int = 2) -> List[Tuple[str, int]]:
        """
        Find cities matching a name using fuzzy matching (Levenshtein distance).

        Args:
            name: Name to match (possibly misspelled)
            max_distance: Maximum edit distance to consider

        Returns:
            List of (canonical_name, distance) tuples, sorted by distance
        """
        from difflib import SequenceMatcher

        normalized = preprocess_for_matching(name)
        fuzzy = fuzzy_normalize(name)
        matches = []

        # Check all known locations
        for norm_name, canonical in self.normalized_to_original.items():
            # Calculate similarity
            similarity = SequenceMatcher(None, fuzzy, fuzzy_normalize(norm_name)).ratio()

            # If similarity is high enough (> 0.7), add to matches
            if similarity > 0.7:
                distance = int((1 - similarity) * 10)  # Convert to distance
                matches.append((canonical, distance))

        # Sort by distance (lower is better)
        matches.sort(key=lambda x: x[1])

        # Return only matches within max_distance
        return [(name, dist) for name, dist in matches if dist <= max_distance]

    def load_from_csv(self, filepath: str, city_column: str = 'city'):
        """
        Load cities from a CSV file.

        Args:
            filepath: Path to CSV file
            city_column: Name of the column containing city names
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if city_column in row:
                    self.add_city(row[city_column])

    def load_from_json(self, filepath: str):
        """
        Load gazetteer data from a JSON file.

        Expected format:
        {
            "cities": ["Paris", "Lyon", ...],
            "stations": ["Paris Gare du Nord", ...],
            "aliases": {
                "paris": ["paris", "pari", ...]
            }
        }

        Args:
            filepath: Path to JSON file
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Load cities
        if 'cities' in data:
            for city in data['cities']:
                self.add_city(city)

        # Load stations
        if 'stations' in data:
            for station in data['stations']:
                self.add_station(station)

        # Load aliases
        if 'aliases' in data:
            self.aliases.update(data['aliases'])

    def save_to_json(self, filepath: str):
        """
        Save gazetteer data to a JSON file.

        Args:
            filepath: Path to save JSON file
        """
        data = {
            'cities': sorted(list(self.cities)),
            'stations': sorted(list(self.stations)),
            'aliases': self.aliases
        }

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the gazetteer.

        Returns:
            Dictionary with counts of cities, stations, and aliases
        """
        return {
            'cities': len(self.cities),
            'stations': len(self.stations),
            'total_locations': len(self.normalized_to_original),
            'aliases': sum(len(v) for v in self.aliases.values())
        }

    def __len__(self) -> int:
        """Return total number of locations in gazetteer."""
        return len(self.normalized_to_original)

    def __contains__(self, name: str) -> bool:
        """Check if a name is in the gazetteer."""
        return self.is_valid_location(name)

    def __repr__(self) -> str:
        """String representation of gazetteer."""
        stats = self.get_stats()
        return (f"Gazetteer(cities={stats['cities']}, "
                f"stations={stats['stations']}, "
                f"total={stats['total_locations']})")


def load_gazetteer(filepath: Optional[str] = None) -> Gazetteer:
    """
    Load and return a Gazetteer instance with SNCF station names.

    Args:
        filepath: Optional path to JSON file to load additional data

    Returns:
        Gazetteer instance loaded from SNCF stations
    """
    import pandas as pd

    gaz = Gazetteer()

    # Load from SNCF stations_clean.csv using station_name (not city_name which is broken)
    stations_file = Path("data/processed/sncf/stations_clean.csv")
    if stations_file.exists():
        try:
            df = pd.read_csv(stations_file, encoding='utf-8')
            # Use station_name column (city_name is broken for Saint-* cities)
            for station_name in df['station_name'].dropna().unique():
                gaz.add_city(station_name)
        except Exception as e:
            print(f"Warning: Could not load gazetteer from {stations_file}: {e}")

    # Load additional data from JSON if provided
    if filepath and Path(filepath).exists():
        gaz.load_from_json(filepath)

    return gaz


if __name__ == "__main__":
    # Example usage
    print("=== Gazetteer Demo ===\n")

    # Create gazetteer
    gaz = Gazetteer()
    print(f"Loaded gazetteer: {gaz}")
    print(f"Stats: {gaz.get_stats()}\n")

    # Test validation
    print("1. Location validation:")
    test_cities = ["Paris", "paris", "Lyon", "Gotham", "Marseille"]
    for city in test_cities:
        valid = gaz.is_valid_location(city)
        canonical = gaz.get_canonical_name(city)
        print(f"   {city:15} -> Valid: {valid:5} | Canonical: {canonical}")
    print()

    # Test matching
    print("2. Find locations in text:")
    texts = [
        "Je veux aller de Paris à Lyon",
        "Train pour Marseille depuis Toulouse",
        "Port-Boulet vers Tours"
    ]
    for text in texts:
        matches = gaz.find_matches(text)
        print(f"   '{text}'")
        print(f"   -> {matches}")
    print()

    # Test fuzzy matching
    print("3. Fuzzy matching (misspellings):")
    misspellings = ["Parris", "Lyyon", "Marsseille"]
    for misspelling in misspellings:
        matches = gaz.fuzzy_match(misspelling, max_distance=3)
        print(f"   '{misspelling}' -> {matches[:3]}")  # Top 3 matches
    print()

    print("✅ Gazetteer module functional!")
