#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate valid travel orders dataset (7,000 phrases)

NEW ARCHITECTURE: 3 functions by difficulty level
- generate_easy_orders(): 200 templates → 2,310 sentences (33%)
- generate_medium_orders(): 200 templates → 2,310 sentences (33%)
- generate_hard_orders(): 200 templates → 2,380 sentences (34%)

Distribution: 33% easy / 33% medium / 34% hard
"""

import csv
import random

# Cities for France (top 30 + complex cases)
MAIN_CITIES = [
    "Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes",
    "Strasbourg", "Montpellier", "Bordeaux", "Lille", "Rennes",
    "Reims", "Saint-Étienne", "Le Havre", "Toulon", "Grenoble",
    "Dijon", "Angers", "Nîmes", "Villeurbanne", "Le Mans",
    "Aix-en-Provence", "Clermont-Ferrand", "Brest", "Tours",
    "Amiens", "Limoges", "Annecy", "Perpignan", "Metz"
]

COMPOUND_CITIES = [
    "Port-Boulet", "Bourg-en-Bresse", "Aix-en-Provence",
    "Saint-Étienne", "La Roche-sur-Yon", "Salon-de-Provence",
    "Aix-les-Bains", "Boulogne-sur-Mer", "Châlons-en-Champagne"
]

AMBIGUOUS_NAMES = ["Albert", "Florence", "Paris", "Lourdes", "Rémy", "Clément"]

# Common misspellings
MISSPELLINGS = {
    "Paris": ["Pari", "Paric", "Pariss", "Pariis", "Pariz"],
    "Lyon": ["Lion", "Lyo", "Lionne", "Lione", "Lyhon"],
    "Marseille": ["Marsel", "Marseile", "Marceille", "Marseiye", "Marsei"],
    "Toulouse": ["Tolouse", "Toulouze", "Toulouse", "Tolooze", "Touluse"],
    "Nice": ["Nise", "Nices", "Nisse", "Niice", "Nicce"],
    "Bordeaux": ["Bordo", "Bordeau", "Bordeaus", "Bordau", "Bord"],
    "Lille": ["Lile", "Lilles", "Lill", "Lile", "Lyl"],
    "Nantes": ["Nante", "Nantess", "Nantez", "Nantte", "Nante"],
    "Tours": ["Tour", "Tourz", "Toure", "Touurs", "Toor"],
    "Rennes": ["Rene", "Renss", "Renn", "Rene", "Raines"],
    "Strasbourg": ["Strasborg", "Strasbourge", "Strazburg", "Strasboure"],
    "Montpellier": ["Montpelier", "Montpellié", "Montpellie", "Monpelier"],
}

def misspell(city):
    """Return a misspelled version of a city name"""
    if city in MISSPELLINGS:
        return random.choice(MISSPELLINGS[city])
    # Generic misspelling: remove last letter or double a letter
    if len(city) > 4:
        if random.random() < 0.5:
            return city[:-1]
        else:
            idx = random.randint(1, len(city)-2)
            return city[:idx] + city[idx] + city[idx:]
    return city


def generate_easy_orders(count=2400, start_id=1):
    """Generate easy-difficulty travel orders (200 templates)

    Args:
        count: Number of sentences to generate (default 2400 for 2310 after dedup)
        start_id: Starting sentence ID

    Returns:
        (phrases, next_id): List of phrase dicts and next available ID

    Templates:
        - 80 standard with clear structure ("Je veux aller de X à Y")
        - 40 direct format ("Billet X Y", "Train X Y")
        - 80 lowercase but clear structure
    """

    # Standard templates with clear structure (80 templates)
    templates_standard = [
        ("Je voudrais un billet de {origin} à {dest}", "standard"),
        ("Un aller simple de {origin} à {dest}", "standard"),
        ("Je veux aller de {origin} à {dest}", "standard"),
        ("Un billet {origin} {dest} s'il vous plaît", "standard"),
        ("Je souhaite me rendre à {dest} depuis {origin}", "standard"),
        ("Comment aller de {origin} à {dest}", "standard"),
        ("Quel est le prix d'un billet de {origin} à {dest}", "standard"),
        ("Y a-t-il un train de {origin} vers {dest}", "standard"),
        ("Je cherche un train de {origin} à {dest}", "standard"),
        ("Pouvez-vous me donner les horaires de {origin} à {dest}", "standard"),
        ("Un train de {origin} pour {dest}", "standard"),
        ("Je dois me rendre de {origin} à {dest}", "standard"),
        ("Trajet de {origin} vers {dest}", "standard"),
        ("Départ {origin} arrivée {dest}", "standard"),
        ("De {origin} vers {dest} s'il vous plaît", "standard"),
        ("Pourriez-vous me réserver un billet de {origin} à {dest}", "standard"),
        ("Je souhaiterais obtenir un billet de {origin} à {dest}", "standard"),
        ("Il me faudrait un titre de transport de {origin} à {dest}", "standard"),
        ("Je prends le train de {origin} à {dest}", "standard"),
        ("Mon trajet est de {origin} à {dest}", "standard"),
        ("C'est pour un voyage de {origin} à {dest}", "standard"),
        ("Le billet de {origin} à {dest} coûte combien", "standard"),
        ("Il y a des trains de {origin} à {dest}", "standard"),
        ("Les horaires de {origin} à {dest} svp", "standard"),
        ("Je voudrais voyager de {origin} à {dest}", "standard"),
        ("Un aller de {origin} à {dest} merci", "standard"),
        ("Pour aller de {origin} à {dest}", "standard"),
        ("Depuis {origin} vers {dest}", "standard"),
        ("Train au départ de {origin} pour {dest}", "standard"),
        ("Voyage de {origin} à {dest}", "standard"),
        ("Aller de {origin} à {dest}", "standard"),
        ("De {origin} jusqu'à {dest}", "standard"),
        ("Un ticket de {origin} à {dest}", "standard"),
        ("Place dans le train de {origin} à {dest}", "standard"),
        ("Réservation de {origin} à {dest}", "standard"),
        ("Partir de {origin} et aller à {dest}", "standard"),
        ("Je pars de {origin} pour {dest}", "standard"),
        ("Direction {dest} depuis {origin}", "standard"),
        ("Itinéraire de {origin} à {dest}", "standard"),
        ("Route de {origin} vers {dest}", "standard"),
        ("Je me rends de {origin} à {dest}", "standard"),
        ("Transport de {origin} à {dest}", "standard"),
        ("Aller chercher un billet de {origin} à {dest}", "standard"),
        ("Il me faut un billet de {origin} à {dest}", "standard"),
        ("Besoin d'un billet de {origin} à {dest}", "standard"),
        ("Je vais de {origin} à {dest}", "standard"),
        ("Pour me rendre de {origin} à {dest}", "standard"),
        ("De {origin} à {dest} en train", "standard"),
        ("Trajet en train de {origin} à {dest}", "standard"),
        ("Aller en train de {origin} à {dest}", "standard"),
        ("Le train de {origin} à {dest}", "standard"),
        ("Prendre le train de {origin} à {dest}", "standard"),
        ("Je souhaite partir de {origin} vers {dest}", "standard"),
        ("Voyager de {origin} vers {dest}", "standard"),
        ("Un voyage de {origin} à {dest}", "standard"),
        ("Depuis {origin} jusqu'à {dest}", "standard"),
        ("Au départ de {origin} vers {dest}", "standard"),
        ("En partant de {origin} vers {dest}", "standard"),
        ("Je désire aller de {origin} à {dest}", "standard"),
        ("J'aimerais aller de {origin} à {dest}", "standard"),
        ("Pour voyager de {origin} à {dest}", "standard"),
        ("Aller simple de {origin} vers {dest}", "standard"),
        ("Un trajet de {origin} vers {dest}", "standard"),
        ("Départ de {origin} destination {dest}", "standard"),
        ("Origine {origin} destination {dest}", "standard"),
        ("De {origin} pour aller à {dest}", "standard"),
        ("Partir de {origin} direction {dest}", "standard"),
        ("Train de {origin} direction {dest}", "standard"),
        ("Je veux partir de {origin} à {dest}", "standard"),
        ("Rejoindre {dest} depuis {origin}", "standard"),
        ("Aller vers {dest} depuis {origin}", "standard"),
        ("Me rendre à {dest} de {origin}", "standard"),
        ("Partir à {dest} de {origin}", "standard"),
        ("Voyage depuis {origin} vers {dest}", "standard"),
        ("Trajet depuis {origin} vers {dest}", "standard"),
        ("De {origin} en direction de {dest}", "standard"),
        ("Au départ de {origin} pour {dest}", "standard"),
        ("Je dois partir de {origin} à {dest}", "standard"),
        ("J'ai besoin d'aller de {origin} à {dest}", "standard"),
        ("Faut que j'aille de {origin} à {dest}", "standard"),
    ]

    # Direct format templates (40 templates)
    templates_direct = [
        ("Billet {origin} {dest}", "no_markers"),
        ("Train {origin} {dest}", "no_markers"),
        ("Trajet {origin} {dest}", "no_markers"),
        ("{origin} {dest} s'il vous plaît", "no_markers"),
        ("{origin} {dest} demain", "no_markers"),
        ("Un billet {origin} {dest}", "no_markers"),
        ("Réservation {origin} {dest}", "no_markers"),
        ("{origin} {dest} aujourd'hui", "no_markers"),
        ("{origin} {dest} ce soir", "no_markers"),
        ("{origin} {dest} aller simple", "no_markers"),
        ("Place {origin} {dest}", "no_markers"),
        ("Ticket {origin} {dest}", "no_markers"),
        ("{origin} {dest} svp", "no_markers"),
        ("{origin} {dest} merci", "no_markers"),
        ("Transport {origin} {dest}", "no_markers"),
        ("{origin} {dest} direct", "no_markers"),
        ("{origin} {dest} rapide", "no_markers"),
        ("{origin} {dest} pour demain", "no_markers"),
        ("{origin} {dest} ce matin", "no_markers"),
        ("{origin} {dest} cet après-midi", "no_markers"),
        ("Voyage {origin} {dest}", "no_markers"),
        ("{origin} {dest} maintenant", "no_markers"),
        ("{origin} {dest} tout de suite", "no_markers"),
        ("{origin} {dest} bientôt", "no_markers"),
        ("{origin} {dest} prochain train", "no_markers"),
        ("Départ {origin} {dest}", "no_markers"),
        ("Aller {origin} {dest}", "no_markers"),
        ("{origin} {dest} merci beaucoup", "no_markers"),
        ("{origin} {dest} s'il te plaît", "no_markers"),
        ("{origin} {dest} TGV", "no_markers"),
        ("{origin} {dest} train", "no_markers"),
        ("{origin} {dest} direct svp", "no_markers"),
        ("{origin} {dest} aller", "no_markers"),
        ("{origin} {dest} simple", "no_markers"),
        ("Billet svp {origin} {dest}", "no_markers"),
        ("Train svp {origin} {dest}", "no_markers"),
        ("{origin} {dest} voyager", "no_markers"),
        ("{origin} {dest} partir", "no_markers"),
        ("{origin} {dest} réserver", "no_markers"),
        ("{origin} {dest} horaires", "no_markers"),
    ]

    # Lowercase templates with clear structure (80 templates)
    templates_lowercase = [
        ("je voudrais un billet de {origin} a {dest}", "no_capitals"),
        ("je veux aller de {origin} a {dest}", "no_capitals"),
        ("un billet {origin} {dest} sil vous plait", "no_capitals"),
        ("comment aller de {origin} a {dest}", "no_capitals"),
        ("je souhaite me rendre a {dest} depuis {origin}", "no_capitals"),
        ("trajet de {origin} vers {dest}", "no_capitals"),
        ("billet {origin} {dest}", "no_capitals"),
        ("je dois aller de {origin} a {dest}", "no_capitals"),
        ("de {origin} vers {dest}", "no_capitals"),
        ("un train de {origin} a {dest}", "no_capitals"),
        ("je prends un billet de {origin} a {dest}", "no_capitals"),
        ("cest pour aller de {origin} a {dest}", "no_capitals"),
        ("train {origin} {dest} sil vous plait", "no_capitals"),
        ("je dois me rendre de {origin} a {dest}", "no_capitals"),
        ("partir de {origin} vers {dest}", "no_capitals"),
        ("aller de {origin} a {dest}", "no_capitals"),
        ("un aller simple de {origin} a {dest}", "no_capitals"),
        ("je vais de {origin} a {dest}", "no_capitals"),
        ("voyage de {origin} a {dest}", "no_capitals"),
        ("depuis {origin} jusqua {dest}", "no_capitals"),
        ("pour aller de {origin} a {dest}", "no_capitals"),
        ("train au depart de {origin} pour {dest}", "no_capitals"),
        ("je cherche un train de {origin} a {dest}", "no_capitals"),
        ("reservation de {origin} a {dest}", "no_capitals"),
        ("un ticket de {origin} a {dest}", "no_capitals"),
        ("direction {dest} depuis {origin}", "no_capitals"),
        ("itineraire de {origin} a {dest}", "no_capitals"),
        ("route de {origin} vers {dest}", "no_capitals"),
        ("transport de {origin} a {dest}", "no_capitals"),
        ("il me faut un billet de {origin} a {dest}", "no_capitals"),
        ("besoin dun billet de {origin} a {dest}", "no_capitals"),
        ("pour me rendre de {origin} a {dest}", "no_capitals"),
        ("de {origin} a {dest} en train", "no_capitals"),
        ("trajet en train de {origin} a {dest}", "no_capitals"),
        ("aller en train de {origin} a {dest}", "no_capitals"),
        ("le train de {origin} a {dest}", "no_capitals"),
        ("prendre le train de {origin} a {dest}", "no_capitals"),
        ("je souhaite partir de {origin} vers {dest}", "no_capitals"),
        ("voyager de {origin} vers {dest}", "no_capitals"),
        ("un voyage de {origin} a {dest}", "no_capitals"),
        ("au depart de {origin} vers {dest}", "no_capitals"),
        ("en partant de {origin} vers {dest}", "no_capitals"),
        ("je desire aller de {origin} a {dest}", "no_capitals"),
        ("jaimerais aller de {origin} a {dest}", "no_capitals"),
        ("pour voyager de {origin} a {dest}", "no_capitals"),
        ("aller simple de {origin} vers {dest}", "no_capitals"),
        ("un trajet de {origin} vers {dest}", "no_capitals"),
        ("depart de {origin} destination {dest}", "no_capitals"),
        ("origine {origin} destination {dest}", "no_capitals"),
        ("de {origin} pour aller a {dest}", "no_capitals"),
        ("partir de {origin} direction {dest}", "no_capitals"),
        ("train de {origin} direction {dest}", "no_capitals"),
        ("je veux partir de {origin} a {dest}", "no_capitals"),
        ("rejoindre {dest} depuis {origin}", "no_capitals"),
        ("aller vers {dest} depuis {origin}", "no_capitals"),
        ("me rendre a {dest} de {origin}", "no_capitals"),
        ("partir a {dest} de {origin}", "no_capitals"),
        ("voyage depuis {origin} vers {dest}", "no_capitals"),
        ("trajet depuis {origin} vers {dest}", "no_capitals"),
        ("de {origin} en direction de {dest}", "no_capitals"),
        ("au depart de {origin} pour {dest}", "no_capitals"),
        ("je dois partir de {origin} a {dest}", "no_capitals"),
        ("jai besoin daller de {origin} a {dest}", "no_capitals"),
        ("faut que jaille de {origin} a {dest}", "no_capitals"),
        ("un billet de {origin} vers {dest}", "no_capitals"),
        ("je vais prendre le train de {origin} a {dest}", "no_capitals"),
        ("cest pour un voyage de {origin} a {dest}", "no_capitals"),
        ("aller chercher un billet de {origin} a {dest}", "no_capitals"),
        ("place dans le train de {origin} a {dest}", "no_capitals"),
        ("partir de {origin} et aller a {dest}", "no_capitals"),
        ("je pars de {origin} pour {dest}", "no_capitals"),
        ("mon trajet est de {origin} a {dest}", "no_capitals"),
        ("les horaires de {origin} a {dest} svp", "no_capitals"),
        ("il y a des trains de {origin} a {dest}", "no_capitals"),
        ("le billet de {origin} a {dest} coute combien", "no_capitals"),
        ("y a-t-il un train de {origin} vers {dest}", "no_capitals"),
        ("pouvez-vous me donner les horaires de {origin} a {dest}", "no_capitals"),
        ("depart {origin} arrivee {dest}", "no_capitals"),
        ("un aller de {origin} a {dest} merci", "no_capitals"),
        ("je voudrais voyager de {origin} a {dest}", "no_capitals"),
    ]

    # Combine all templates (200 total)
    all_templates = templates_standard + templates_direct + templates_lowercase

    phrases = []
    sentence_id = start_id

    for _ in range(count):
        template, category = random.choice(all_templates)
        origin = random.choice(MAIN_CITIES)
        dest = random.choice([c for c in MAIN_CITIES if c != origin])

        sentence = template.format(origin=origin, dest=dest)

        # Lowercase for no_capitals category
        if category == "no_capitals":
            sentence = sentence.lower()

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': origin,
            'destination': dest,
            'is_valid': 1,
            'difficulty': 'easy',
            'category': category,
            'notes': ''
        })
        sentence_id += 1

    return phrases, sentence_id


def generate_medium_orders(count=2400, start_id=1):
    """Generate medium-difficulty travel orders (200 templates)

    Args:
        count: Number of sentences to generate (default 2400 for 2310 after dedup)
        start_id: Starting sentence ID

    Returns:
        (phrases, next_id): List of phrase dicts and next available ID

    Templates:
        - 40 questions about routes
        - 50 inverted order ("à Y depuis X")
        - 20 no markers with context
        - 40 additional information (time, passengers)
        - 50 compound names with hyphen variations
    """

    # Question templates (40 templates)
    templates_questions = [
        ("Quand part le prochain train de {origin} vers {dest}", "standard"),
        ("À quelle heure y a-t-il des trains de {origin} à {dest}", "standard"),
        ("Combien coûte un billet de train de {origin} à {dest}", "standard"),
        ("Quel est le temps de trajet de {origin} à {dest}", "standard"),
        ("Quel est l'horaire des trains au départ de {origin} pour {dest}", "standard"),
        ("Y a-t-il des trains directs de {origin} à {dest}", "standard"),
        ("À quelle heure part le premier train de {origin} pour {dest}", "standard"),
        ("À quelle heure arrive le dernier train de {origin} à {dest}", "standard"),
        ("Combien de temps dure le trajet de {origin} à {dest}", "standard"),
        ("Quels sont les horaires de {origin} à {dest}", "standard"),
        ("Combien ça coûte un billet de {origin} à {dest}", "standard"),
        ("Il y a combien de trains de {origin} à {dest}", "standard"),
        ("Quelle est la durée du trajet de {origin} à {dest}", "standard"),
        ("Quel prix pour un billet de {origin} à {dest}", "standard"),
        ("Quand puis-je partir de {origin} vers {dest}", "standard"),
        ("À quelle heure je peux partir de {origin} pour {dest}", "standard"),
        ("Combien de trains par jour de {origin} à {dest}", "standard"),
        ("Quel est le tarif de {origin} à {dest}", "standard"),
        ("C'est combien pour aller de {origin} à {dest}", "standard"),
        ("Vous avez des trains de {origin} vers {dest}", "standard"),
        ("Il existe des trains de {origin} à {dest}", "standard"),
        ("Est-ce qu'il y a des trains de {origin} vers {dest}", "standard"),
        ("Peut-on aller de {origin} à {dest} en train", "standard"),
        ("Comment se rendre de {origin} à {dest}", "standard"),
        ("Quelle est la meilleure façon d'aller de {origin} à {dest}", "standard"),
        ("Pouvez-vous m'indiquer les horaires de {origin} à {dest}", "standard"),
        ("Je voudrais connaître les horaires de {origin} à {dest}", "standard"),
        ("Y a-t-il un train direct de {origin} vers {dest}", "standard"),
        ("Les trains de {origin} à {dest} sont à quelle heure", "standard"),
        ("Quelle heure le train de {origin} à {dest}", "standard"),
        ("Combien de temps entre {origin} et {dest}", "standard"),
        ("C'est long le trajet de {origin} à {dest}", "standard"),
        ("Faut combien de temps pour aller de {origin} à {dest}", "standard"),
        ("Il faut combien de temps de {origin} à {dest}", "standard"),
        ("Vous avez les horaires de {origin} à {dest}", "standard"),
        ("Je peux avoir les horaires de {origin} à {dest}", "standard"),
        ("Quel est le prochain train de {origin} à {dest}", "standard"),
        ("Il reste des places de {origin} à {dest}", "standard"),
        ("C'est possible de réserver de {origin} à {dest}", "standard"),
        ("Je peux réserver un billet de {origin} à {dest}", "standard"),
    ]

    # Inverted order templates (50 templates)
    templates_inverted = [
        ("Je veux aller à {dest} en partant de {origin}", "inverted_order"),
        ("Comment se rendre à {dest} si on part de {origin}", "inverted_order"),
        ("Pour aller à {dest} depuis {origin}", "inverted_order"),
        ("À {dest} en partance de {origin}", "inverted_order"),
        ("Vers {dest} au départ de {origin}", "inverted_order"),
        ("Direction {dest} en partant de {origin}", "inverted_order"),
        ("Cap sur {dest} depuis {origin}", "inverted_order"),
        ("Je me rends à {dest} en provenance de {origin}", "inverted_order"),
        ("Trajet vers {dest} au départ de {origin}", "inverted_order"),
        ("Pour me rendre à {dest} je pars de {origin}", "inverted_order"),
        ("Pour arriver à {dest} je pars d'où si je suis à {origin}", "inverted_order"),
        ("Destination {dest} avec un départ de {origin}", "inverted_order"),
        ("Aller à {dest} en quittant {origin}", "inverted_order"),
        ("Rejoindre {dest} depuis {origin} comment faire", "inverted_order"),
        ("L'itinéraire vers {dest} au départ de {origin}", "inverted_order"),
        ("Je souhaite aller à {dest} depuis {origin}", "inverted_order"),
        ("Je voudrais me rendre à {dest} en partant de {origin}", "inverted_order"),
        ("Arriver à {dest} depuis {origin}", "inverted_order"),
        ("Partir pour {dest} depuis {origin}", "inverted_order"),
        ("Me rendre à {dest} au départ de {origin}", "inverted_order"),
        ("Voyager vers {dest} depuis {origin}", "inverted_order"),
        ("Aller jusqu'à {dest} en partant de {origin}", "inverted_order"),
        ("Rejoindre {dest} au départ de {origin}", "inverted_order"),
        ("Pour rejoindre {dest} depuis {origin}", "inverted_order"),
        ("Vers {dest} en provenance de {origin}", "inverted_order"),
        ("À destination de {dest} depuis {origin}", "inverted_order"),
        ("En direction de {dest} au départ de {origin}", "inverted_order"),
        ("Se rendre à {dest} depuis {origin}", "inverted_order"),
        ("Pour atteindre {dest} depuis {origin}", "inverted_order"),
        ("Accéder à {dest} depuis {origin}", "inverted_order"),
        ("Je dois rejoindre {dest} depuis {origin}", "inverted_order"),
        ("Il faut que j'aille à {dest} depuis {origin}", "inverted_order"),
        ("Je pars pour {dest} depuis {origin}", "inverted_order"),
        ("Mon but est {dest} depuis {origin}", "inverted_order"),
        ("Ma destination est {dest} depuis {origin}", "inverted_order"),
        ("Atteindre {dest} en partant de {origin}", "inverted_order"),
        ("Me déplacer vers {dest} depuis {origin}", "inverted_order"),
        ("Aller vers {dest} au départ de {origin}", "inverted_order"),
        ("Pour aller vers {dest} depuis {origin}", "inverted_order"),
        ("Destination finale {dest} départ {origin}", "inverted_order"),
        ("Arrivée {dest} départ {origin}", "inverted_order"),
        ("Voyage vers {dest} départ {origin}", "inverted_order"),
        ("Route vers {dest} depuis {origin}", "inverted_order"),
        ("Trajet jusqu'à {dest} depuis {origin}", "inverted_order"),
        ("Pour me déplacer à {dest} depuis {origin}", "inverted_order"),
        ("Aller retrouver {dest} depuis {origin}", "inverted_order"),
        ("Comment rejoindre {dest} depuis {origin}", "inverted_order"),
        ("Partir vers {dest} au départ de {origin}", "inverted_order"),
        ("Je vais vers {dest} depuis {origin}", "inverted_order"),
        ("En route pour {dest} depuis {origin}", "inverted_order"),
    ]

    # No markers with context (20 templates)
    templates_no_markers_context = [
        ("{origin} {dest} demain matin", "no_markers"),
        ("{origin} {dest} ce week-end", "no_markers"),
        ("{origin} {dest} la semaine prochaine", "no_markers"),
        ("{origin} {dest} lundi prochain", "no_markers"),
        ("{origin} {dest} vendredi soir", "no_markers"),
        ("{origin} {dest} samedi", "no_markers"),
        ("{origin} {dest} dimanche", "no_markers"),
        ("{origin} {dest} en urgence", "no_markers"),
        ("{origin} {dest} rapidement", "no_markers"),
        ("{origin} {dest} dès que possible", "no_markers"),
        ("{origin} {dest} pour affaires", "no_markers"),
        ("{origin} {dest} pour le travail", "no_markers"),
        ("{origin} {dest} en vacances", "no_markers"),
        ("{origin} {dest} pour les vacances", "no_markers"),
        ("{origin} {dest} voir la famille", "no_markers"),
        ("{origin} {dest} aller-retour", "no_markers"),
        ("{origin} {dest} première classe", "no_markers"),
        ("{origin} {dest} deuxième classe", "no_markers"),
        ("{origin} {dest} tarif réduit", "no_markers"),
        ("{origin} {dest} plein tarif", "no_markers"),
    ]

    # Additional information templates (40 templates)
    templates_additional_info = [
        ("Je voudrais un billet de {origin} à {dest} pour demain", "additional_info"),
        ("Un billet {origin} {dest} pour 2 adultes", "additional_info"),
        ("Combien coûte un billet de {origin} à {dest}", "additional_info"),
        ("Quel est le prix d'un aller simple de {origin} à {dest}", "additional_info"),
        ("Je veux aller de {origin} à {dest} demain matin", "additional_info"),
        ("Un billet {origin} {dest} pour ce soir", "additional_info"),
        ("Deux billets de {origin} à {dest} s'il vous plaît", "additional_info"),
        ("Je voudrais partir de {origin} à {dest} lundi prochain", "additional_info"),
        ("Un aller-retour {origin} {dest} pour la semaine prochaine", "additional_info"),
        ("Billet {origin} {dest} pour 3 personnes", "additional_info"),
        ("Billet {origin} {dest} pour 3 voyageurs", "additional_info"),
        ("Je veux partir de {origin} à {dest} vendredi soir", "additional_info"),
        ("Tarif réduit de {origin} à {dest} pour étudiants", "additional_info"),
        ("Combien coûte {origin} {dest} en première classe", "additional_info"),
        ("Réservation {origin} {dest} pour le mois prochain", "additional_info"),
        ("Un billet {origin} {dest} pour 4 personnes", "additional_info"),
        ("Je voudrais un billet {origin} {dest} pour samedi", "additional_info"),
        ("Un aller {origin} {dest} pour dimanche", "additional_info"),
        ("Billet {origin} {dest} pour ce week-end", "additional_info"),
        ("Aller-retour {origin} {dest} pour deux", "additional_info"),
        ("Je veux partir de {origin} vers {dest} après-demain", "additional_info"),
        ("Billet {origin} {dest} en urgence", "additional_info"),
        ("Train {origin} {dest} dès que possible", "additional_info"),
        ("Billet {origin} {dest} pour la famille", "additional_info"),
        ("Un billet {origin} {dest} tarif jeune", "additional_info"),
        ("Réservation {origin} {dest} pour senior", "additional_info"),
        ("Billet {origin} {dest} carte de réduction", "additional_info"),
        ("Train {origin} {dest} pour les vacances", "additional_info"),
        ("Billet {origin} {dest} pour affaires", "additional_info"),
        ("Un aller {origin} {dest} pour le travail", "additional_info"),
        ("Je dois aller de {origin} à {dest} en début de semaine", "additional_info"),
        ("Billet {origin} {dest} pour fin de semaine", "additional_info"),
        ("Train {origin} {dest} milieu de journée", "additional_info"),
        ("Billet {origin} {dest} tôt le matin", "additional_info"),
        ("Train {origin} {dest} en soirée", "additional_info"),
        ("Billet {origin} {dest} pour un groupe", "additional_info"),
        ("Réservation {origin} {dest} groupe de 5", "additional_info"),
        ("Billet {origin} {dest} pour voyage scolaire", "additional_info"),
        ("Train {origin} {dest} avec vélo", "additional_info"),
        ("Billet {origin} {dest} avec animal", "additional_info"),
    ]

    # Compound names templates (50 templates) - with hyphen variations
    templates_compound = [
        ("Je veux aller de {origin} à {compound}", "compound_name"),
        ("Un billet de {origin} pour {compound}", "compound_name"),
        ("Comment aller à {compound} depuis {origin}", "compound_name"),
        ("Trajet {origin} {compound}", "compound_name"),
        ("De {origin} vers {compound}", "compound_name"),
        ("Je souhaite me rendre à {compound} en partant de {origin}", "compound_name"),
        ("Billet {origin} {compound}", "compound_name"),
        ("Train de {origin} à {compound}", "compound_name"),
        ("Je veux aller de {compound} à {dest}", "compound_name"),
        ("Un billet de {compound} pour {dest}", "compound_name"),
        ("Comment aller à {dest} depuis {compound}", "compound_name"),
        ("Trajet {compound} {dest}", "compound_name"),
        ("De {compound} vers {dest}", "compound_name"),
        ("Je souhaite me rendre à {dest} en partant de {compound}", "compound_name"),
        ("Billet {compound} {dest}", "compound_name"),
        ("Train de {compound} à {dest}", "compound_name"),
        ("Aller à {compound} depuis {origin}", "compound_name"),
        ("Pour aller à {compound} depuis {origin}", "compound_name"),
        ("Direction {compound} depuis {origin}", "compound_name"),
        ("Rejoindre {compound} depuis {origin}", "compound_name"),
        ("Partir pour {compound} depuis {origin}", "compound_name"),
        ("Me rendre à {compound} depuis {origin}", "compound_name"),
        ("Voyage de {origin} à {compound}", "compound_name"),
        ("Itinéraire de {origin} à {compound}", "compound_name"),
        ("Route de {origin} vers {compound}", "compound_name"),
        ("Je pars de {origin} pour {compound}", "compound_name"),
        ("Départ {origin} arrivée {compound}", "compound_name"),
        ("Un aller simple de {origin} à {compound}", "compound_name"),
        ("Réservation de {origin} à {compound}", "compound_name"),
        ("Transport de {origin} à {compound}", "compound_name"),
        ("Je dois aller de {origin} à {compound}", "compound_name"),
        ("Pour me rendre de {origin} à {compound}", "compound_name"),
        ("Aller de {compound} vers {dest}", "compound_name"),
        ("Pour aller de {compound} vers {dest}", "compound_name"),
        ("Direction {dest} depuis {compound}", "compound_name"),
        ("Rejoindre {dest} depuis {compound}", "compound_name"),
        ("Partir pour {dest} depuis {compound}", "compound_name"),
        ("Me rendre à {dest} depuis {compound}", "compound_name"),
        ("Voyage de {compound} à {dest}", "compound_name"),
        ("Itinéraire de {compound} à {dest}", "compound_name"),
        ("Route de {compound} vers {dest}", "compound_name"),
        ("Je pars de {compound} pour {dest}", "compound_name"),
        ("Départ {compound} arrivée {dest}", "compound_name"),
        ("Un aller simple de {compound} à {dest}", "compound_name"),
        ("Réservation de {compound} à {dest}", "compound_name"),
        ("Transport de {compound} à {dest}", "compound_name"),
        ("Je dois aller de {compound} à {dest}", "compound_name"),
        ("Pour me rendre de {compound} à {dest}", "compound_name"),
        ("Je veux aller de {origin} vers {compound}", "compound_name"),
        ("Je veux aller de {compound} vers {dest}", "compound_name"),
    ]

    # Combine all templates (200 total)
    all_templates = (templates_questions + templates_inverted +
                     templates_no_markers_context + templates_additional_info +
                     templates_compound)

    phrases = []
    sentence_id = start_id

    for _ in range(count):
        template, category = random.choice(all_templates)

        # Handle compound names
        if category == "compound_name" and "{compound}" in template:
            compound = random.choice(COMPOUND_CITIES)
            if random.random() < 0.3:
                # Remove hyphens
                compound_display = compound.replace("-", " ")
            else:
                compound_display = compound

            # Randomly choose if compound is origin or destination
            if "{origin}" in template and "{compound}" in template:
                origin = random.choice(MAIN_CITIES)
                dest = compound_display
                actual_dest = compound
                sentence = template.format(origin=origin, compound=compound_display)
            else:  # {compound} and {dest}
                origin = compound
                dest = random.choice(MAIN_CITIES)
                actual_dest = dest
                sentence = template.format(compound=compound_display, dest=dest)
        else:
            origin = random.choice(MAIN_CITIES)
            dest = random.choice([c for c in MAIN_CITIES if c != origin])
            actual_dest = dest
            sentence = template.format(origin=origin, dest=dest)

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': origin if category != "compound_name" or "{origin}" in template else compound,
            'destination': actual_dest,
            'is_valid': 1,
            'difficulty': 'medium',
            'category': category,
            'notes': 'compound name no hyphen' if category == "compound_name" and "-" not in sentence else ''
        })
        sentence_id += 1

    return phrases, sentence_id


def generate_hard_orders(count=2475, start_id=1):
    """Generate hard-difficulty travel orders (200 templates)

    Args:
        count: Number of sentences to generate (default 2475 for 2380 after dedup)
        start_id: Starting sentence ID

    Returns:
        (phrases, next_id): List of phrase dicts and next available ID

    Templates:
        - 100 with spelling errors
        - 60 with strong name ambiguities
        - 40 complex questions requiring inference
    """

    # Misspelling templates (100 templates)
    templates_misspelling = [
        ("Je veu aler de {origin} a {dest}", "misspelling"),
        ("Un bilet {origin} {dest}", "misspelling"),
        ("Comment aler a {dest} depuis {origin}", "misspelling"),
        ("Trajet {origin} {dest}", "misspelling"),
        ("Je voudrai un bilet de {origin} a {dest}", "misspelling"),
        ("Commen aler de {origin} a {dest}", "misspelling"),
        ("Je souhaite me rendr a {dest} depui {origin}", "misspelling"),
        ("Bilet {origin} {dest}", "misspelling"),
        ("Je doi aller de {origin} a {dest}", "misspelling"),
        ("Un aller simpl de {origin} a {dest}", "misspelling"),
        ("Je veu partir de {origin} a {dest}", "misspelling"),
        ("Commen me rendre de {origin} a {dest}", "misspelling"),
        ("Je voudrai un tiket de {origin} a {dest}", "misspelling"),
        ("Un biyet {origin} {dest}", "misspelling"),
        ("Comman aller de {origin} a {dest}", "misspelling"),
        ("Je veux ale de {origin} a {dest}", "misspelling"),
        ("Bilet de trin de {origin} a {dest}", "misspelling"),
        ("Je souhet aller de {origin} a {dest}", "misspelling"),
        ("Un biye de {origin} a {dest}", "misspelling"),
        ("Traje de {origin} a {dest}", "misspelling"),
        ("Je veu me rendr a {dest} depuis {origin}", "misspelling"),
        ("Reservation {origin} {dest}", "misspelling"),
        ("Coment aller de {origin} ver {dest}", "misspelling"),
        ("Je voudré un billet de {origin} a {dest}", "misspelling"),
        ("Bilet train {origin} {dest}", "misspelling"),
        ("Allé de {origin} a {dest}", "misspelling"),
        ("Je veu prendr le train de {origin} a {dest}", "misspelling"),
        ("Un bilet de trin de {origin} a {dest}", "misspelling"),
        ("Commen me rendr a {dest} depuis {origin}", "misspelling"),
        ("Je doi partir de {origin} ver {dest}", "misspelling"),
        ("Trin {origin} {dest}", "misspelling"),
        ("Je voudrai ale de {origin} a {dest}", "misspelling"),
        ("Un biye simpl de {origin} a {dest}", "misspelling"),
        ("Comant se rendre de {origin} a {dest}", "misspelling"),
        ("Je ve aller de {origin} a {dest}", "misspelling"),
        ("Bilet de {origin} ver {dest}", "misspelling"),
        ("Je souhaite partir de {origin} a {dest}", "misspelling"),
        ("Un trin de {origin} a {dest}", "misspelling"),
        ("Comen aller de {origin} a {dest}", "misspelling"),
        ("Je voudrai un biet de {origin} a {dest}", "misspelling"),
        ("Reservation trin {origin} {dest}", "misspelling"),
        ("Je ve prendr le train de {origin} a {dest}", "misspelling"),
        ("Un biye de trin de {origin} a {dest}", "misspelling"),
        ("Traje en trin de {origin} a {dest}", "misspelling"),
        ("Je doi me rendre de {origin} a {dest}", "misspelling"),
        ("Bilet pour {origin} {dest}", "misspelling"),
        ("Je souhet me rendre a {dest} depuis {origin}", "misspelling"),
        ("Un tiket de {origin} a {dest}", "misspelling"),
        ("Comman se rendre de {origin} a {dest}", "misspelling"),
        ("Je veu allé de {origin} a {dest}", "misspelling"),
        ("Bilet de trein de {origin} a {dest}", "misspelling"),
        ("Je voudrai partir de {origin} a {dest}", "misspelling"),
        ("Un biye train {origin} {dest}", "misspelling"),
        ("Comen me rendre de {origin} a {dest}", "misspelling"),
        ("Je ve partir de {origin} a {dest}", "misspelling"),
        ("Trein {origin} {dest}", "misspelling"),
        ("Je souhaite ale de {origin} a {dest}", "misspelling"),
        ("Un bilet de trein de {origin} a {dest}", "misspelling"),
        ("Comant aller de {origin} ver {dest}", "misspelling"),
        ("Je doi ale de {origin} a {dest}", "misspelling"),
        ("Reservation de {origin} a {dest}", "misspelling"),
        ("Je veu me rendr de {origin} a {dest}", "misspelling"),
        ("Un trin de {origin} ver {dest}", "misspelling"),
        ("Coment se rendre de {origin} a {dest}", "misspelling"),
        ("Je voudré aller de {origin} a {dest}", "misspelling"),
        ("Bilet simple {origin} {dest}", "misspelling"),
        ("Je ve me rendre de {origin} a {dest}", "misspelling"),
        ("Un biye de trein de {origin} a {dest}", "misspelling"),
        ("Comen partir de {origin} a {dest}", "misspelling"),
        ("Je veu partir de {origin} ver {dest}", "misspelling"),
        ("Tiket {origin} {dest}", "misspelling"),
        ("Je souhet partir de {origin} a {dest}", "misspelling"),
        ("Un bilet pour {origin} {dest}", "misspelling"),
        ("Comman aller de {origin} ver {dest}", "misspelling"),
        ("Je doi partir de {origin} a {dest}", "misspelling"),
        ("Trin de {origin} a {dest}", "misspelling"),
        ("Je voudrai me rendre de {origin} a {dest}", "misspelling"),
        ("Un biye pour {origin} {dest}", "misspelling"),
        ("Coment aller de {origin} a {dest}", "misspelling"),
        ("Je ve aller de {origin} ver {dest}", "misspelling"),
        ("Bilet de trin {origin} {dest}", "misspelling"),
        ("Je souhaite me rendre de {origin} a {dest}", "misspelling"),
        ("Un tiket de train de {origin} a {dest}", "misspelling"),
        ("Comen se rendre de {origin} a {dest}", "misspelling"),
        ("Je veu aller de {origin} ver {dest}", "misspelling"),
        ("Traje {origin} {dest}", "misspelling"),
        ("Je doi me rendr de {origin} a {dest}", "misspelling"),
        ("Un bilet trin {origin} {dest}", "misspelling"),
        ("Comant partir de {origin} a {dest}", "misspelling"),
        ("Je voudré partir de {origin} a {dest}", "misspelling"),
        ("Reservation trin de {origin} a {dest}", "misspelling"),
        ("Je ve partir de {origin} ver {dest}", "misspelling"),
        ("Un biye de {origin} ver {dest}", "misspelling"),
        ("Coment me rendre de {origin} a {dest}", "misspelling"),
        ("Je veu me rendr a {dest} de {origin}", "misspelling"),
        ("Bilet pour trin {origin} {dest}", "misspelling"),
        ("Je souhet aller de {origin} ver {dest}", "misspelling"),
        ("Un tiket {origin} {dest}", "misspelling"),
        ("Comen aller de {origin} ver {dest}", "misspelling"),
    ]

    # Name ambiguity templates (60 templates)
    templates_ambiguity = [
        ("Avec mes amis {name1} et {name2}, je voudrais aller de {origin} à {dest}", "name_ambiguity"),
        ("Je voyage avec {name1} et {name2} de {origin} vers {dest}", "name_ambiguity"),
        ("{name1}, {name2} et moi voulons aller de {origin} à {dest}", "name_ambiguity"),
        ("Je vais à {dest} voir {name1} et {name2} en partant de {origin}", "name_ambiguity"),
        ("Mon ami {name1} et moi allons de {origin} à {dest}", "name_ambiguity"),
        ("Retrouver {name1} et {name2} à {dest} en partant de {origin}", "name_ambiguity"),
        ("Avec {name1}, {name2} et {name3} on va de {origin} à {dest}", "name_ambiguity"),
        ("Je dois rejoindre {name1} et {name2} à {dest} depuis {origin}", "name_ambiguity"),
        ("{name1} et {name2} m'attendent à {dest} je pars de {origin}", "name_ambiguity"),
        ("Moi, {name1} et {name2} voulons rejoindre {dest} depuis {origin}", "name_ambiguity"),
        ("On va voir {name1} à {dest} en partant de {origin}", "name_ambiguity"),
        ("Rejoindre {name1} et {name2} à {dest} depuis {origin}", "name_ambiguity"),
        ("Avec mes amis {name1}, {name2} et {name3} je vais de {origin} à {dest}", "name_ambiguity"),
        ("{name1}, {name2} et moi devons aller de {origin} à {dest}", "name_ambiguity"),
        ("Je pars avec {name1} et {name2} de {origin} vers {dest}", "name_ambiguity"),
        ("Aller à {dest} voir {name1} et {name2} depuis {origin}", "name_ambiguity"),
        ("Retrouver {name1} à {dest} en partant de {origin}", "name_ambiguity"),
        ("{name1} et {name2} veulent aller de {origin} à {dest}", "name_ambiguity"),
        ("On rejoint {name1} et {name2} à {dest} depuis {origin}", "name_ambiguity"),
        ("Avec mon ami {name1} je vais de {origin} à {dest}", "name_ambiguity"),
        ("{name1}, {name2} et moi partons de {origin} pour {dest}", "name_ambiguity"),
        ("Je dois voir {name1} et {name2} à {dest} en partant de {origin}", "name_ambiguity"),
        ("Voyage avec {name1} et {name2} de {origin} à {dest}", "name_ambiguity"),
        ("{name1} et moi voulons aller de {origin} à {dest}", "name_ambiguity"),
        ("Retrouver mes amis {name1} et {name2} à {dest} depuis {origin}", "name_ambiguity"),
        ("avec mes amis {name1} et {name2} je voudrais aller de {origin} a {dest}", "name_ambiguity"),
        ("on va voir {name1} et {name2} a {dest} en partant de {origin}", "name_ambiguity"),
        ("{name1}, {name2} et moi voulons aller de {origin} a {dest}", "name_ambiguity"),
        ("avec {name1}, {name2} et {name3} on va de {origin} a {dest}", "name_ambiguity"),
        ("je voyage avec {name1} et {name2} de {origin} vers {dest}", "name_ambiguity"),
        ("retrouver {name1} et {name2} a {dest} en partant de {origin}", "name_ambiguity"),
        ("avec mon ami {name1} je vais de {origin} a {dest}", "name_ambiguity"),
        ("moi, {name1} et {name2} voulons rejoindre {dest} depuis {origin}", "name_ambiguity"),
        ("{name1} et {name2} mattendent a {dest} je pars de {origin}", "name_ambiguity"),
        ("je dois rejoindre {name1} et {name2} a {dest} depuis {origin}", "name_ambiguity"),
        ("on rejoint {name1} et {name2} a {dest} depuis {origin}", "name_ambiguity"),
        ("{name1} et {name2} veulent aller de {origin} a {dest}", "name_ambiguity"),
        ("aller a {dest} voir {name1} et {name2} depuis {origin}", "name_ambiguity"),
        ("{name1}, {name2} et moi devons aller de {origin} a {dest}", "name_ambiguity"),
        ("je pars avec {name1} et {name2} de {origin} vers {dest}", "name_ambiguity"),
        ("avec mes amis {name1}, {name2} et {name3} je vais de {origin} a {dest}", "name_ambiguity"),
        ("retrouver mes amis {name1} et {name2} a {dest} depuis {origin}", "name_ambiguity"),
        ("{name1} et moi voulons aller de {origin} a {dest}", "name_ambiguity"),
        ("voyage avec {name1} et {name2} de {origin} a {dest}", "name_ambiguity"),
        ("je dois voir {name1} et {name2} a {dest} en partant de {origin}", "name_ambiguity"),
        ("{name1}, {name2} et moi partons de {origin} pour {dest}", "name_ambiguity"),
        ("avec mon ami {name1} je vais de {origin} a {dest}", "name_ambiguity"),
        ("on va voir {name1} a {dest} en partant de {origin}", "name_ambiguity"),
        ("rejoindre {name1} a {dest} depuis {origin}", "name_ambiguity"),
        ("avec mes amis {name1} et {name2}, je vais de {origin} a {dest}", "name_ambiguity"),
        ("{name1} et {name2} mont dit daller a {dest} depuis {origin}", "name_ambiguity"),
        ("je veux retrouver {name1} et {name2} a {dest} depuis {origin}", "name_ambiguity"),
        ("avec {name1} et {name2} on part de {origin} vers {dest}", "name_ambiguity"),
        ("{name1}, {name2} et {name3} veulent aller de {origin} a {dest}", "name_ambiguity"),
        ("je dois aller voir {name1} a {dest} en partant de {origin}", "name_ambiguity"),
        ("avec mes copains {name1} et {name2} on va de {origin} a {dest}", "name_ambiguity"),
        ("{name1} et {name2} sont a {dest} je pars de {origin}", "name_ambiguity"),
        ("retrouver {name1} a {dest} depuis {origin}", "name_ambiguity"),
        ("avec mon copain {name1} on va de {origin} a {dest}", "name_ambiguity"),
        ("{name1} et {name2} habitent a {dest} je pars de {origin}", "name_ambiguity"),
    ]

    # Complex question templates (40 templates)
    templates_complex = [
        ("Quel est le moyen le plus rapide pour aller de {origin} à {dest}", "complex_question"),
        ("Combien de temps faut-il pour aller de {origin} à {dest}", "complex_question"),
        ("Y a-t-il des trains directs entre {origin} et {dest}", "complex_question"),
        ("Quelle est la durée du trajet de {origin} à {dest}", "complex_question"),
        ("Combien de correspondances entre {origin} et {dest}", "complex_question"),
        ("Quel est le train le plus rapide de {origin} à {dest}", "complex_question"),
        ("À quelle heure part le premier train de {origin} pour {dest}", "complex_question"),
        ("À quelle heure arrive le dernier train de {origin} à {dest}", "complex_question"),
        ("Quel est le trajet optimal pour {origin} {dest}", "complex_question"),
        ("Faut-il prévoir des changements entre {origin} et {dest}", "complex_question"),
        ("Le train le plus économique de {origin} vers {dest}", "complex_question"),
        ("Combien d'heures minimum entre {origin} et {dest}", "complex_question"),
        ("Les trains directs existent entre {origin} et {dest}", "complex_question"),
        ("Quel est le meilleur moment pour partir de {origin} vers {dest}", "complex_question"),
        ("Comment optimiser le trajet de {origin} à {dest}", "complex_question"),
        ("Y a-t-il des réductions pour {origin} {dest}", "complex_question"),
        ("Quel est le tarif le moins cher de {origin} à {dest}", "complex_question"),
        ("Faut-il réserver à l'avance pour {origin} {dest}", "complex_question"),
        ("Quelle est la fréquence des trains de {origin} à {dest}", "complex_question"),
        ("Peut-on avoir un train direct de {origin} vers {dest}", "complex_question"),
        ("Quel est le temps de correspondance entre {origin} et {dest}", "complex_question"),
        ("Y a-t-il beaucoup de monde sur {origin} {dest}", "complex_question"),
        ("Est-ce qu'il faut changer de train entre {origin} et {dest}", "complex_question"),
        ("Combien ça coûte en moyenne de {origin} à {dest}", "complex_question"),
        ("Quelle est la meilleure option pour {origin} {dest}", "complex_question"),
        ("Faut-il préférer le TGV ou le train normal pour {origin} {dest}", "complex_question"),
        ("Y a-t-il des trains de nuit de {origin} à {dest}", "complex_question"),
        ("Quel est le wagon le plus confortable pour {origin} {dest}", "complex_question"),
        ("Est-ce rentable de prendre le train de {origin} à {dest}", "complex_question"),
        ("Combien de temps d'avance faut-il pour {origin} {dest}", "complex_question"),
        ("Y a-t-il souvent des retards sur {origin} {dest}", "complex_question"),
        ("Quelle classe choisir pour {origin} {dest}", "complex_question"),
        ("Faut-il obligatoirement réserver pour {origin} {dest}", "complex_question"),
        ("Quel est le meilleur tarif pour {origin} {dest}", "complex_question"),
        ("Y a-t-il des promotions pour {origin} {dest}", "complex_question"),
        ("Combien de trains par jour entre {origin} et {dest}", "complex_question"),
        ("Quel est le train le plus confortable de {origin} à {dest}", "complex_question"),
        ("Faut-il arriver en avance pour {origin} {dest}", "complex_question"),
        ("Y a-t-il des services à bord pour {origin} {dest}", "complex_question"),
        ("Quel est le meilleur jour pour voyager de {origin} à {dest}", "complex_question"),
    ]

    # Combine all templates (200 total)
    all_templates = templates_misspelling + templates_ambiguity + templates_complex

    phrases = []
    sentence_id = start_id

    for _ in range(count):
        template, category = random.choice(all_templates)

        # Handle different categories
        if category == "misspelling":
            origin = random.choice(MAIN_CITIES)
            dest = random.choice([c for c in MAIN_CITIES if c != origin])

            # Apply misspellings
            if random.random() < 0.7:
                origin_misspelled = misspell(origin)
            else:
                origin_misspelled = origin.lower()

            if random.random() < 0.7:
                dest_misspelled = misspell(dest)
            else:
                dest_misspelled = dest.lower()

            sentence = template.format(origin=origin_misspelled, dest=dest_misspelled)

            # Lowercase for some
            if random.random() < 0.6:
                sentence = sentence.lower()

        elif category == "name_ambiguity":
            origin = random.choice(MAIN_CITIES)
            dest = random.choice([c for c in MAIN_CITIES if c != origin])

            # Choose distractor names
            name1 = random.choice(AMBIGUOUS_NAMES)
            name2 = random.choice([n for n in AMBIGUOUS_NAMES if n != name1])
            name3 = random.choice([n for n in AMBIGUOUS_NAMES if n not in [name1, name2]])

            # Format sentence
            if "{name3}" in template:
                sentence = template.format(origin=origin, dest=dest, name1=name1, name2=name2, name3=name3)
            elif "{name2}" in template:
                sentence = template.format(origin=origin, dest=dest, name1=name1, name2=name2)
            else:
                sentence = template.format(origin=origin, dest=dest, name1=name1)

            # Lowercase for harder cases (already in template for some)
            if "lowercase" not in template and random.random() < 0.3:
                sentence = sentence.lower()

        else:  # complex_question
            origin = random.choice(MAIN_CITIES)
            dest = random.choice([c for c in MAIN_CITIES if c != origin])
            sentence = template.format(origin=origin, dest=dest)

        phrases.append({
            'sentenceID': sentence_id,
            'sentence': sentence,
            'origin': origin,
            'destination': dest,
            'is_valid': 1,
            'difficulty': 'hard',
            'category': category,
            'notes': 'spelling errors' if category == "misspelling" else
                     'multiple name distractors' if category == "name_ambiguity" else ''
        })
        sentence_id += 1

    return phrases, sentence_id


def main():
    """Generate complete valid orders dataset with new architecture"""

    print("=" * 70)
    print("GENERATING VALID ORDERS DATASET - NEW ARCHITECTURE")
    print("=" * 70)
    print("\nArchitecture: 3 functions by difficulty")
    print("  - generate_easy_orders(): 200 templates")
    print("  - generate_medium_orders(): 200 templates")
    print("  - generate_hard_orders(): 200 templates")
    print("=" * 70)

    all_phrases = []

    # Generate easy orders
    print("\n[EASY] Generating easy-difficulty orders (2,400)...")
    easy, next_id = generate_easy_orders(count=2400, start_id=1)
    all_phrases.extend(easy)
    print(f"[OK] Generated {len(easy)} easy phrases")

    # Generate medium orders
    print("\n[MEDIUM] Generating medium-difficulty orders (2,400)...")
    medium, next_id = generate_medium_orders(count=2400, start_id=next_id)
    all_phrases.extend(medium)
    print(f"[OK] Generated {len(medium)} medium phrases")

    # Generate hard orders
    print("\n[HARD] Generating hard-difficulty orders (2,475)...")
    hard, next_id = generate_hard_orders(count=2475, start_id=next_id)
    all_phrases.extend(hard)
    print(f"[OK] Generated {len(hard)} hard phrases")

    # Reassign sequential IDs
    for i, phrase in enumerate(all_phrases, 1):
        phrase['sentenceID'] = i

    # Write to CSV
    output_file = 'data/valid_orders_initial.csv'
    print(f"\nWriting to {output_file}...")

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['sentenceID', 'sentence', 'origin', 'destination', 'is_valid', 'difficulty', 'category', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_phrases)

    print(f"[OK] Generated {len(all_phrases)} valid phrases")
    print(f"     Distribution: {len(easy)} easy / {len(medium)} medium / {len(hard)} hard")

    # Statistics
    categories = {}
    difficulties = {}
    for phrase in all_phrases:
        cat = phrase['category']
        categories[cat] = categories.get(cat, 0) + 1
        diff = phrase['difficulty']
        difficulties[diff] = difficulties.get(diff, 0) + 1

    print("\nDistribution by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    print("\nDistribution by difficulty:")
    for diff, count in sorted(difficulties.items()):
        pct = (count / len(all_phrases)) * 100
        print(f"  {diff}: {count} ({pct:.1f}%)")

    return all_phrases


if __name__ == "__main__":
    main()
