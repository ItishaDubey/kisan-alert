from google.cloud import speech_v2 as speech
from google.cloud.speech_v2.types import cloud_speech
from app.whatsapp import download_media
import os

PROJECT_ID = os.getenv("GCP_PROJECT_ID")

LANGUAGE_MAP = {
    "hi": "hi-IN",
    "kn": "kn-IN",
    "mr": "mr-IN",
    "te": "te-IN",
    "ta": "ta-IN",
    "bn": "bn-IN",
}

async def transcribe_audio(media_id: str, language: str = "hi") -> str:
    """Download OGG voice note from WhatsApp and transcribe via Cloud STT Chirp 3."""
    audio_bytes = await download_media(media_id)

    client = speech.SpeechClient()

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=[LANGUAGE_MAP.get(language, "hi-IN"), "en-IN"],
        model="chirp_2",
    )

    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{PROJECT_ID}/locations/global/recognizers/_",
        config=config,
        content=audio_bytes,
    )

    response = client.recognize(request=request)

    transcript = ""
    for result in response.results:
        transcript += result.alternatives[0].transcript + " "

    return transcript.strip()
