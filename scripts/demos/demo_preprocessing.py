"""
Demo script for preprocessing module
"""
import sys
sys.path.insert(0, 'src')
from nlp.preprocessing import *

print('=== Demonstration du Module de Pretraitement ===\n')

# Test 1: Normalisation de base
print('1. Normalisation de base:')
text1 = '  JE VEUX ALLER A PARIS  '
print(f'   Original: "{text1}"')
print(f'   Resultat: "{normalize_text(text1)}"')
print()

# Test 2: Suppression des accents
print('2. Suppression des accents:')
text2 = 'À quelle heure pour Sète?'  # AVEC accents
print(f'   Original: "{text2}"')
print(f'   Resultat: "{remove_accents(text2)}"')
print()

# Test 3: Normalisation des tirets
print('3. Normalisation des tirets (differents types):')
text3 = 'Port–Boulet—Aix—en—Provence'  # En dash (–) et em dash (—)
print(f'   Original: "{text3}"')
print(f'   Resultat: "{normalize_hyphens(text3)}"')
print()

# Test 4: Pipeline complet
print('4. Pipeline complet de pretraitement:')
text4 = '  À quelle heure pour Port–Boulet depuis Tours?  '  # AVEC accents et en dash
print(f'   Original: "{text4}"')
print(f'   Resultat: "{preprocess_for_matching(text4)}"')
print()

# Test 5: Tokenisation
print('5. Tokenisation francaise:')
text5 = 'Je veux aller de Paris à Lyon'  # AVEC accent
print(f'   Original: "{text5}"')
print(f'   Tokens: {tokenize_french(text5)}')
print()

# Test 6: Noms multi-mots
print('6. Separation noms multi-mots:')
cities = ['Port-Boulet', 'Aix-en-Provence', 'La Rochelle']
for city in cities:
    print(f'   {city} => {split_multi_word_name(city)}')
print()

# Test 7: Fuzzy matching
print('7. Normalisation agressive (fuzzy matching):')
text7 = 'Aix-en-Provence'
print(f'   Original: "{text7}"')
print(f'   Fuzzy: "{fuzzy_normalize(text7)}"')
print()

print('\nModule de pretraitement fonctionnel!')
