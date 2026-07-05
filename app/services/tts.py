from google.cloud import texttospeech
import os

VOICE_MAP = {
    "hi": ("hi-IN", "hi-IN-Chirp3-HD-Aoede"),
    "kn": ("kn-IN", "kn-IN-Chirp3-HD-Aoede"),
    "mr": ("mr-IN", "mr-IN-Chirp3-HD-Aoede"),
    "te": ("te-IN", "te-IN-Chirp3-HD-Aoede"),
    "ta": ("ta-IN", "ta-IN-Chirp3-HD-Aoede"),
}

async def text_to_ogg(text: str, language: str = "hi") -> bytes:
    """Convert advisory text to OGG/OPUS bytes for WhatsApp voice note."""
    client = texttospeech.TextToSpeechClient()

    lang_code, voice_name = VOICE_MAP.get(language, VOICE_MAP["hi"])

    synthesis_input = texttospeech.SynthesisInput(text=text[:5000])

    voice = texttospeech.VoiceSelectionParams(
        language_code=lang_code,
        name=voice_name,
    )

    # WhatsApp voice notes require OGG/OPUS
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.OGG_OPUS,
        speaking_rate=0.9,  # Slightly slower — clearer for farmers
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    return response.audio_content
