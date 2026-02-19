#!/usr/bin/env python3
"""
Speech-to-Text Module using Google Speech Recognition (FREE)

Provides audio transcription for voice-based travel order input.
Uses Google's free Speech Recognition API - no API key required!

Usage:
    from src.nlp.speech_to_text import transcribe_audio

    # Transcribe audio bytes
    text = transcribe_audio(audio_bytes, language="fr-FR")
"""

import io
import tempfile
from pathlib import Path
from typing import Optional


def transcribe_audio(
    audio_bytes: bytes,
    language: str = "fr-FR",
    **kwargs  # Ignore unused parameters for compatibility
) -> str:
    """
    Transcrit un fichier audio en texte via Google Speech Recognition (GRATUIT).

    Args:
        audio_bytes: Bytes du fichier audio (WAV/MP3/M4A)
        language: Code langue BCP-47 (fr-FR, en-US, etc.)
        **kwargs: Paramètres ignorés (compatibilité avec ancienne interface)

    Returns:
        Texte transcrit (str)

    Raises:
        ValueError: Si audio_bytes est vide ou None
        Exception: Si erreur de transcription

    Examples:
        >>> # Transcription simple
        >>> text = transcribe_audio(audio_bytes, language="fr-FR")
        >>> print(text)
        'Je veux aller de Paris à Lyon'

    Note:
        Cette fonction utilise l'API gratuite de Google Speech Recognition.
        Quota : ~50 requêtes/jour (largement suffisant pour un usage personnel).
    """
    # Validation
    if not audio_bytes or len(audio_bytes) == 0:
        raise ValueError("Audio bytes vide ou None")

    try:
        import speech_recognition as sr
    except ImportError:
        raise ImportError(
            "Module 'speech_recognition' non installé. "
            "Installez-le avec: pip install SpeechRecognition"
        )

    # Sauvegarder temporairement l'audio sur disque
    temp_path = None
    try:
        # Créer fichier temporaire
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name

        # Charger l'audio avec SpeechRecognition
        recognizer = sr.Recognizer()

        with sr.AudioFile(temp_path) as source:
            # Ajuster pour le bruit ambiant
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Enregistrer l'audio
            audio_data = recognizer.record(source)

        # Transcription via Google Speech Recognition (GRATUIT)
        try:
            text = recognizer.recognize_google(audio_data, language=language)
            return text.strip()

        except sr.UnknownValueError:
            raise Exception(
                "Impossible de comprendre l'audio. "
                "Parlez plus clairement ou réduisez le bruit ambiant."
            )
        except sr.RequestError as e:
            raise Exception(
                f"Erreur de connexion à Google Speech Recognition: {e}. "
                "Vérifiez votre connexion internet."
            )

    finally:
        # Nettoyage du fichier temporaire
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink(missing_ok=True)


def is_api_key_configured() -> bool:
    """
    Vérifie si une configuration est nécessaire.

    Returns:
        True (toujours True car Google Speech Recognition est gratuit et sans clé)

    Note:
        Cette fonction retourne toujours True pour compatibilité avec l'ancienne
        interface qui nécessitait une clé API OpenAI. Google Speech Recognition
        ne nécessite pas de clé API.
    """
    return True  # Toujours disponible, pas de clé API requise


def validate_audio_bytes(audio_bytes: bytes, min_size: int = 1000) -> tuple[bool, str]:
    """
    Valide que les bytes audio sont exploitables.

    Args:
        audio_bytes: Bytes du fichier audio
        min_size: Taille minimale en bytes (défaut: 1KB)

    Returns:
        (is_valid, error_message)
        - (True, "") si valide
        - (False, "raison") si invalide

    Examples:
        >>> is_valid, error = validate_audio_bytes(audio_bytes)
        >>> if not is_valid:
        ...     print(f"Audio invalide: {error}")
    """
    if not audio_bytes:
        return False, "Audio vide (None)"

    if len(audio_bytes) < min_size:
        return False, f"Audio trop court ({len(audio_bytes)} bytes, min: {min_size})"

    # Vérification basique du format (header WAV/MP3)
    # WAV commence par "RIFF....WAVE"
    # MP3 commence par "ID3" ou 0xFF 0xFB
    if len(audio_bytes) >= 12:
        header = audio_bytes[:12]
        is_wav = header[:4] == b'RIFF' and header[8:12] == b'WAVE'
        is_mp3 = header[:3] == b'ID3' or (header[0] == 0xFF and (header[1] & 0xE0) == 0xE0)

        if not (is_wav or is_mp3):
            return False, "Format audio non reconnu (attendu: WAV ou MP3)"

    return True, ""


# ──────────────────────────────────────────────────────────────────────────────
# Alternative locale (Whisper open source) - OPTIONNEL
# ──────────────────────────────────────────────────────────────────────────────

def transcribe_audio_whisper_local(audio_bytes: bytes, language: str = "fr") -> str:
    """
    Transcription via Whisper local (modèle open source) - OPTIONNEL.

    Cette méthode nécessite :
    - Installation : pip install openai-whisper
    - GPU recommandé (sinon très lent sur CPU)
    - ~75 MB de téléchargement (modèle 'base')

    Args:
        audio_bytes: Bytes du fichier audio
        language: Code langue ISO (fr, en, etc.)

    Returns:
        Texte transcrit

    Note:
        Cette fonction est fournie comme alternative offline, mais Google
        Speech Recognition (fonction principale) est plus simple et rapide.
    """
    try:
        import whisper
    except ImportError:
        raise ImportError(
            "Module 'whisper' non installé. "
            "Installez-le avec: pip install openai-whisper"
        )

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name

        # Charger modèle (base = bon compromis vitesse/précision)
        model = whisper.load_model("base")

        # Transcription
        result = model.transcribe(temp_path, language=language)
        return result["text"].strip()

    finally:
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink(missing_ok=True)
