#!/usr/bin/env python3
"""
Unit tests for Speech-to-Text module

Tests cover:
- Audio validation
- API key configuration detection
- Error handling for empty/invalid audio
- Mock API calls (to avoid actual API usage in tests)

Usage:
    pytest tests/test_speech_to_text.py -v
"""

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from src.nlp.speech_to_text import (
    transcribe_audio,
    is_api_key_configured,
    validate_audio_bytes,
    _transcribe_api,
    _transcribe_local
)


# ──────────────────────────────────────────────────────────────────────────────
# Test Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_wav_audio():
    """Mock WAV audio bytes (valid header)"""
    # WAV header: RIFF....WAVE
    header = b'RIFF' + b'\x00' * 4 + b'WAVE'
    return header + b'\x00' * 1000  # Add padding to reach min size


@pytest.fixture
def mock_mp3_audio():
    """Mock MP3 audio bytes (valid header)"""
    # MP3 header: ID3 or 0xFF 0xFB
    header = b'ID3'
    return header + b'\x00' * 1000  # Add padding to reach min size


@pytest.fixture
def mock_small_audio():
    """Mock audio bytes that's too small"""
    return b'RIFF' + b'\x00' * 4 + b'WAVE' + b'\x00' * 100  # Only 116 bytes


# ──────────────────────────────────────────────────────────────────────────────
# Test: Audio Validation
# ──────────────────────────────────────────────────────────────────────────────

def test_validate_audio_bytes_empty():
    """Test validation rejects empty audio"""
    is_valid, error = validate_audio_bytes(None)
    assert not is_valid
    assert "vide" in error.lower()


def test_validate_audio_bytes_too_small(mock_small_audio):
    """Test validation rejects audio that's too small"""
    is_valid, error = validate_audio_bytes(mock_small_audio, min_size=1000)
    assert not is_valid
    assert "trop court" in error.lower()


def test_validate_audio_bytes_invalid_format():
    """Test validation rejects unknown format"""
    invalid_audio = b'INVALID' + b'\x00' * 1000
    is_valid, error = validate_audio_bytes(invalid_audio)
    assert not is_valid
    assert "format" in error.lower()


def test_validate_audio_bytes_valid_wav(mock_wav_audio):
    """Test validation accepts valid WAV audio"""
    is_valid, error = validate_audio_bytes(mock_wav_audio)
    assert is_valid
    assert error == ""


def test_validate_audio_bytes_valid_mp3(mock_mp3_audio):
    """Test validation accepts valid MP3 audio"""
    is_valid, error = validate_audio_bytes(mock_mp3_audio)
    assert is_valid
    assert error == ""


# ──────────────────────────────────────────────────────────────────────────────
# Test: API Key Configuration
# ──────────────────────────────────────────────────────────────────────────────

def test_is_api_key_configured_with_key():
    """Test API key detection when key is set"""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key'}):
        assert is_api_key_configured() is True


def test_is_api_key_configured_without_key():
    """Test API key detection when key is not set"""
    with patch.dict(os.environ, {}, clear=True):
        assert is_api_key_configured() is False


# ──────────────────────────────────────────────────────────────────────────────
# Test: Transcribe Audio (Error Handling)
# ──────────────────────────────────────────────────────────────────────────────

def test_transcribe_audio_empty_bytes():
    """Test transcription raises ValueError for empty audio"""
    with pytest.raises(ValueError, match="vide"):
        transcribe_audio(b"")


def test_transcribe_audio_none_bytes():
    """Test transcription raises ValueError for None audio"""
    with pytest.raises(ValueError, match="vide"):
        transcribe_audio(None)


# ──────────────────────────────────────────────────────────────────────────────
# Test: Transcribe API (Mocked)
# ──────────────────────────────────────────────────────────────────────────────

@patch('src.nlp.speech_to_text.openai.OpenAI')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake_audio')
@patch('src.nlp.speech_to_text.Path.unlink')
@patch('src.nlp.speech_to_text.tempfile.NamedTemporaryFile')
def test_transcribe_audio_api_success(mock_tempfile, mock_unlink, mock_file, mock_openai_class, mock_wav_audio):
    """Test successful transcription via API"""
    # Mock temporary file
    mock_temp = MagicMock()
    mock_temp.name = '/tmp/test_audio.wav'
    mock_tempfile.return_value.__enter__.return_value = mock_temp

    # Mock OpenAI client
    mock_client = MagicMock()
    mock_transcript = MagicMock()
    mock_transcript.text = "Je veux aller de Paris à Lyon"
    mock_client.audio.transcriptions.create.return_value = mock_transcript
    mock_openai_class.return_value = mock_client

    # Call function
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key'}):
        result = transcribe_audio(mock_wav_audio, api_key='sk-test-key', use_local=False)

    # Assertions
    assert result == "Je veux aller de Paris à Lyon"
    mock_openai_class.assert_called_once_with(api_key='sk-test-key')
    mock_client.audio.transcriptions.create.assert_called_once()


@patch('src.nlp.speech_to_text.Path.unlink')
@patch('src.nlp.speech_to_text.tempfile.NamedTemporaryFile')
def test_transcribe_audio_api_missing_key(mock_tempfile, mock_unlink, mock_wav_audio):
    """Test transcription raises error when API key is missing"""
    # Mock temporary file
    mock_temp = MagicMock()
    mock_temp.name = '/tmp/test_audio.wav'
    mock_tempfile.return_value.__enter__.return_value = mock_temp

    # Clear environment
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Clé API OpenAI manquante"):
            transcribe_audio(mock_wav_audio, api_key=None, use_local=False)


@patch('src.nlp.speech_to_text.openai.OpenAI')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake_audio')
@patch('src.nlp.speech_to_text.Path.unlink')
@patch('src.nlp.speech_to_text.tempfile.NamedTemporaryFile')
def test_transcribe_audio_api_authentication_error(mock_tempfile, mock_unlink, mock_file, mock_openai_class, mock_wav_audio):
    """Test transcription handles authentication errors"""
    # Mock temporary file
    mock_temp = MagicMock()
    mock_temp.name = '/tmp/test_audio.wav'
    mock_tempfile.return_value.__enter__.return_value = mock_temp

    # Mock OpenAI client to raise AuthenticationError
    import openai
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.side_effect = openai.AuthenticationError("Invalid API key")
    mock_openai_class.return_value = mock_client

    # Call function
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-invalid-key'}):
        with pytest.raises(Exception, match="Clé API OpenAI invalide"):
            transcribe_audio(mock_wav_audio, api_key='sk-invalid-key', use_local=False)


# ──────────────────────────────────────────────────────────────────────────────
# Test: Transcribe Local (Mocked)
# ──────────────────────────────────────────────────────────────────────────────

@patch('src.nlp.speech_to_text.whisper.load_model')
@patch('src.nlp.speech_to_text.Path.unlink')
@patch('src.nlp.speech_to_text.tempfile.NamedTemporaryFile')
def test_transcribe_audio_local_success(mock_tempfile, mock_unlink, mock_whisper_load, mock_wav_audio):
    """Test successful transcription via local Whisper"""
    # Mock temporary file
    mock_temp = MagicMock()
    mock_temp.name = '/tmp/test_audio.wav'
    mock_tempfile.return_value.__enter__.return_value = mock_temp

    # Mock Whisper model
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "Je veux aller de Paris à Lyon"}
    mock_whisper_load.return_value = mock_model

    # Call function
    result = transcribe_audio(mock_wav_audio, use_local=True)

    # Assertions
    assert result == "Je veux aller de Paris à Lyon"
    mock_whisper_load.assert_called_once_with("base")
    mock_model.transcribe.assert_called_once()


@patch('src.nlp.speech_to_text.Path.unlink')
@patch('src.nlp.speech_to_text.tempfile.NamedTemporaryFile')
def test_transcribe_audio_local_import_error(mock_tempfile, mock_unlink, mock_wav_audio):
    """Test transcription raises ImportError when whisper module is missing"""
    # Mock temporary file
    mock_temp = MagicMock()
    mock_temp.name = '/tmp/test_audio.wav'
    mock_tempfile.return_value.__enter__.return_value = mock_temp

    # Mock import error
    with patch('src.nlp.speech_to_text.whisper', side_effect=ImportError):
        with pytest.raises(ImportError, match="Module 'whisper' non installé"):
            transcribe_audio(mock_wav_audio, use_local=True)


# ──────────────────────────────────────────────────────────────────────────────
# Test: Cleanup (Temporary Files)
# ──────────────────────────────────────────────────────────────────────────────

@patch('src.nlp.speech_to_text.openai.OpenAI')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake_audio')
@patch('src.nlp.speech_to_text.Path')
@patch('src.nlp.speech_to_text.tempfile.NamedTemporaryFile')
def test_transcribe_audio_cleanup_on_success(mock_tempfile, mock_path, mock_file, mock_openai_class, mock_wav_audio):
    """Test temporary file is cleaned up after successful transcription"""
    # Mock temporary file
    mock_temp = MagicMock()
    mock_temp.name = '/tmp/test_audio.wav'
    mock_tempfile.return_value.__enter__.return_value = mock_temp

    # Mock Path
    mock_path_instance = MagicMock()
    mock_path.return_value = mock_path_instance
    mock_path_instance.exists.return_value = True

    # Mock OpenAI client
    mock_client = MagicMock()
    mock_transcript = MagicMock()
    mock_transcript.text = "Test transcription"
    mock_client.audio.transcriptions.create.return_value = mock_transcript
    mock_openai_class.return_value = mock_client

    # Call function
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key'}):
        transcribe_audio(mock_wav_audio, api_key='sk-test-key', use_local=False)

    # Assert cleanup was called
    mock_path_instance.unlink.assert_called_once_with(missing_ok=True)


@patch('src.nlp.speech_to_text.openai.OpenAI')
@patch('builtins.open', new_callable=mock_open, read_data=b'fake_audio')
@patch('src.nlp.speech_to_text.Path')
@patch('src.nlp.speech_to_text.tempfile.NamedTemporaryFile')
def test_transcribe_audio_cleanup_on_error(mock_tempfile, mock_path, mock_file, mock_openai_class, mock_wav_audio):
    """Test temporary file is cleaned up even after error"""
    # Mock temporary file
    mock_temp = MagicMock()
    mock_temp.name = '/tmp/test_audio.wav'
    mock_tempfile.return_value.__enter__.return_value = mock_temp

    # Mock Path
    mock_path_instance = MagicMock()
    mock_path.return_value = mock_path_instance
    mock_path_instance.exists.return_value = True

    # Mock OpenAI client to raise error
    import openai
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.side_effect = openai.APIError("API Error")
    mock_openai_class.return_value = mock_client

    # Call function and expect error
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key'}):
        with pytest.raises(Exception):
            transcribe_audio(mock_wav_audio, api_key='sk-test-key', use_local=False)

    # Assert cleanup was still called
    mock_path_instance.unlink.assert_called_once_with(missing_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Integration Note
# ──────────────────────────────────────────────────────────────────────────────

"""
NOTE: These tests use mocks to avoid making actual API calls to OpenAI.

For real integration testing with actual audio files:
1. Set OPENAI_API_KEY in your environment
2. Create sample WAV files
3. Run manual integration tests (not automated)

Example manual test:
    import wave
    import numpy as np

    # Create a simple test WAV file
    with wave.open('test.wav', 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(np.zeros(16000 * 2, dtype=np.int16).tobytes())

    # Test transcription
    with open('test.wav', 'rb') as f:
        audio_bytes = f.read()

    text = transcribe_audio(audio_bytes, language="fr")
    print(f"Transcription: {text}")
"""
