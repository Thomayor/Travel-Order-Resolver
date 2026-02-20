#!/usr/bin/env python3
"""
Voice Recorder for CLI (Command-Line Interface)

Provides microphone recording functionality for voice-based input in terminal.
Used by main.py interactive mode with --voice flag.

Usage:
    from src.nlp.voice_recorder import record_voice_cli

    # Record audio from microphone
    audio_bytes = record_voice_cli(duration=5, sample_rate=16000)
"""

import io
import sys
import tempfile
from pathlib import Path
from typing import Optional


def record_voice_cli(
    duration: float = 5.0,
    sample_rate: int = 16000,
    channels: int = 1
) -> Optional[bytes]:
    """
    Enregistre l'audio depuis le microphone en ligne de commande.

    Affiche un compte à rebours pendant l'enregistrement et retourne
    les bytes audio au format WAV.

    Args:
        duration: Durée d'enregistrement en secondes (défaut: 5s)
        sample_rate: Taux d'échantillonnage en Hz (défaut: 16000 Hz)
        channels: Nombre de canaux audio (1=mono, 2=stéréo, défaut: 1)

    Returns:
        Bytes du fichier WAV, ou None si erreur/annulation

    Examples:
        >>> audio_bytes = record_voice_cli(duration=3.0)
        🎤 Enregistrement (3s)...
        3... 2... 1... ✓
        >>> len(audio_bytes)
        96044

    Note:
        Nécessite sounddevice et scipy installés:
        pip install sounddevice scipy
    """
    try:
        import sounddevice as sd
        import numpy as np
        from scipy.io import wavfile
    except ImportError as e:
        print("\n[ERREUR] Module manquant pour l'enregistrement audio:")
        print(f"  {e}")
        print("\nInstallez les dépendances avec:")
        print("  pip install sounddevice scipy")
        return None

    print(f"🎤 Enregistrement ({duration:.0f}s)... Parlez maintenant !")

    try:
        # Enregistrer l'audio
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            dtype='int16'
        )

        # Afficher compte à rebours
        for i in range(int(duration), 0, -1):
            print(f"  {i}...", end=" ", flush=True)
            sd.wait(int(sample_rate))  # Attendre 1 seconde

        # Attendre la fin de l'enregistrement
        sd.wait()
        print("✓")

        # Convertir en bytes WAV
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

            # Sauvegarder en WAV
            wavfile.write(temp_path, sample_rate, recording)

            # Lire les bytes
            with open(temp_path, 'rb') as f:
                audio_bytes = f.read()

            return audio_bytes

        finally:
            # Nettoyage
            if temp_path and Path(temp_path).exists():
                Path(temp_path).unlink(missing_ok=True)

    except KeyboardInterrupt:
        print("\n  → Enregistrement annulé")
        return None

    except Exception as e:
        print(f"\n[ERREUR] Échec de l'enregistrement: {e}")
        return None


def test_microphone() -> bool:
    """
    Teste si le microphone est accessible.

    Returns:
        True si le microphone fonctionne, False sinon

    Examples:
        >>> if test_microphone():
        ...     print("Microphone OK")
        ... else:
        ...     print("Microphone non disponible")
    """
    try:
        import sounddevice as sd
    except ImportError:
        return False

    try:
        # Essayer de lister les périphériques audio
        devices = sd.query_devices()

        # Vérifier s'il existe au moins un périphérique d'entrée
        for device in devices:
            if device['max_input_channels'] > 0:
                return True

        return False

    except Exception:
        return False


def list_audio_devices():
    """
    Affiche la liste des périphériques audio disponibles.

    Utile pour déboguer les problèmes de microphone.

    Examples:
        >>> list_audio_devices()
        Périphériques audio disponibles:
          0: Microsoft Sound Mapper - Input (2 in, 0 out)
          1: Microphone (Realtek High Definition Audio) (2 in, 0 out)
          ...
    """
    try:
        import sounddevice as sd
    except ImportError:
        print("[ERREUR] sounddevice non installé")
        print("  pip install sounddevice")
        return

    try:
        print("\nPériphériques audio disponibles:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            print(f"  {i}: {device['name']} "
                  f"({device['max_input_channels']} in, "
                  f"{device['max_output_channels']} out)")
        print()

    except Exception as e:
        print(f"[ERREUR] Impossible de lister les périphériques: {e}")


if __name__ == "__main__":
    # Test rapide du module
    print("=== Test du module voice_recorder ===\n")

    # Test microphone
    print("Test du microphone...")
    if test_microphone():
        print("  ✓ Microphone détecté\n")
    else:
        print("  ✗ Aucun microphone trouvé\n")
        sys.exit(1)

    # Lister périphériques
    list_audio_devices()

    # Test enregistrement
    print("Test d'enregistrement (3 secondes)...")
    audio_bytes = record_voice_cli(duration=3.0)

    if audio_bytes:
        print(f"\n✓ Enregistrement réussi: {len(audio_bytes)} bytes")

        # Tester la transcription (optionnel)
        try:
            from src.nlp.speech_to_text import transcribe_audio
            print("\nTest de transcription...")
            text = transcribe_audio(audio_bytes, language="fr-FR")
            print(f"  Transcription: '{text}'")
        except Exception as e:
            print(f"  Transcription non disponible: {e}")
    else:
        print("\n✗ Échec de l'enregistrement")
