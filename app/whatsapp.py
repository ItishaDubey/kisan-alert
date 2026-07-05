import httpx
import os
from app.services.tts import text_to_ogg
from app.services.firestore import upload_audio_to_gcs

BASE_URL = "https://graph.facebook.com"
API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v19.0")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


def _headers():
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


async def send_text(wa_id: str, phone_number_id: str, text: str):
    url = f"{BASE_URL}/{API_VERSION}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": wa_id,
        "type": "text",
        "text": {"body": text[:4096]},  # WhatsApp text limit
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=_headers(), json=payload, timeout=10)
        r.raise_for_status()


async def send_voice_note(wa_id: str, phone_number_id: str, text: str, language: str):
    """Convert text to OGG via Cloud TTS, upload to GCS, send as voice note."""
    ogg_bytes = await text_to_ogg(text, language)
    public_url = await upload_audio_to_gcs(ogg_bytes, f"tts/{wa_id}_{int(__import__('time').time())}.ogg")

    url = f"{BASE_URL}/{API_VERSION}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": wa_id,
        "type": "audio",
        "audio": {"link": public_url, "voice": True},
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=_headers(), json=payload, timeout=10)
        r.raise_for_status()


async def send_interactive_language_select(wa_id: str, phone_number_id: str):
    url = f"{BASE_URL}/{API_VERSION}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": wa_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Welcome to Kisan Alert! Please select your language:\nभाषा चुनें / ಭಾಷೆ ಆಯ್ಕೆ / भाषा निवडा / భాష ఎంచుకోండి"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "lang_hi", "title": "हिंदी"}},
                    {"type": "reply", "reply": {"id": "lang_kn", "title": "ಕನ್ನಡ"}},
                    {"type": "reply", "reply": {"id": "lang_mr", "title": "मराठी"}},
                ]
            },
        },
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=_headers(), json=payload, timeout=10)
        r.raise_for_status()


async def download_media(media_id: str) -> bytes:
    """Download voice note or image bytes from Meta media URL."""
    # Step 1: Get media URL
    url = f"{BASE_URL}/{API_VERSION}/{media_id}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}, timeout=10)
        r.raise_for_status()
        media_url = r.json().get("url")

    # Step 2: Download the actual file
    async with httpx.AsyncClient() as client:
        r = await client.get(media_url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}, timeout=30)
        r.raise_for_status()
        return r.content
