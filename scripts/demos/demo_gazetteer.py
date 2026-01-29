"""
Demo script for gazetteer module
"""
import sys
sys.path.insert(0, 'src')
from nlp.gazetteer import Gazetteer

print('=== Gazetteer Demo ===\n')

# Create gazetteer
gaz = Gazetteer()
print(f"Loaded gazetteer: {gaz}")
print(f"Stats: {gaz.get_stats()}\n")

# Test validation
print('1. Location validation:')
test_cities = ["Paris", "paris", "Lyon", "Gotham", "Marseille"]
for city in test_cities:
    valid = gaz.is_valid_location(city)
    canonical = gaz.get_canonical_name(city)
    print(f'   {city:15} -> Valid: {str(valid):5} | Canonical: {canonical}')
print()

# Test matching
print('2. Find locations in text:')
texts = [
    "Je veux aller de Paris a Lyon",
    "Train pour Marseille depuis Toulouse",
    "Port-Boulet vers Tours"
]
for text in texts:
    matches = gaz.find_matches(text)
    print(f'   "{text}"')
    print(f'   -> {matches}')
print()

# Test fuzzy matching
print('3. Fuzzy matching (misspellings):')
misspellings = ["Parris", "Lyyon", "Marsseille"]
for misspelling in misspellings:
    matches = gaz.fuzzy_match(misspelling, max_distance=3)
    top_matches = matches[:3] if len(matches) > 3 else matches
    print(f'   "{misspelling}" -> {top_matches}')
print()

print('Module gazetteer fonctionnel!')
