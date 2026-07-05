from google.cloud import firestore, storage
import os
import time

BUCKET = os.getenv("GCS_AUDIO_BUCKET", "kisan-alert-audio")

FARMERS = os.getenv("FIRESTORE_COLLECTION_FARMERS", "farmers")
SESSIONS = os.getenv("FIRESTORE_COLLECTION_SESSIONS", "sessions")
CASES = os.getenv("FIRESTORE_COLLECTION_CASES", "crop_cases")
DEDUP = "processed_messages"

_db = None
_storage_client = None


def _get_db():
    global _db
    if _db is None:
        _db = firestore.Client(project=os.getenv("GCP_PROJECT_ID"))
    return _db


def _get_storage_client():
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()
    return _storage_client


class _LazyClient:
    """Defers GCP client construction until first attribute access, so importing
    this module doesn't require credentials (e.g. running locally without ADC)."""

    def __init__(self, getter):
        self._getter = getter

    def __getattr__(self, name):
        return getattr(self._getter(), name)


db = _LazyClient(_get_db)
storage_client = _LazyClient(_get_storage_client)


async def get_or_create_farmer(wa_id: str, name: str = "") -> dict:
    doc_ref = db.collection(FARMERS).document(wa_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    # New farmer
    farmer = {
        "wa_id": wa_id,
        "name": name,
        "language": "hi",
        "district": "",
        "crop": "wheat",
        "is_new": True,
        "opted_in_alerts": False,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    doc_ref.set(farmer)
    return farmer


async def update_farmer(wa_id: str, data: dict):
    db.collection(FARMERS).document(wa_id).update(data)


async def update_farmer_language(wa_id: str, language: str):
    db.collection(FARMERS).document(wa_id).update({
        "language": language,
        "is_new": False,
    })


async def update_session(wa_id: str, data: dict):
    data["updated_at"] = firestore.SERVER_TIMESTAMP
    db.collection(SESSIONS).document(wa_id).set(data, merge=True)


async def get_session(wa_id: str) -> dict:
    doc = db.collection(SESSIONS).document(wa_id).get()
    return doc.to_dict() if doc.exists else {}


async def log_crop_case(wa_id: str, district: str, diagnosis: str, image_id: str = ""):
    """Log crop health case for RSK notification."""
    db.collection(CASES).add({
        "wa_id": wa_id,
        "district": district,
        "diagnosis": diagnosis,
        "image_id": image_id,
        "rsk_notified": False,
        "created_at": firestore.SERVER_TIMESTAMP,
    })


async def is_duplicate(message_id: str) -> bool:
    doc = db.collection(DEDUP).document(message_id).get()
    return doc.exists


async def mark_processed(message_id: str):
    db.collection(DEDUP).document(message_id).set({
        "processed_at": firestore.SERVER_TIMESTAMP
    })


async def upload_audio_to_gcs(audio_bytes: bytes, blob_name: str) -> str:
    """Upload OGG bytes to GCS and return public URL."""
    bucket = storage_client.bucket(BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(audio_bytes, content_type="audio/ogg")
    blob.make_public()
    return blob.public_url


async def get_opted_in_farmers() -> list:
    """Get all farmers who have opted in for morning alerts."""
    farmers = db.collection(FARMERS).where("opted_in_alerts", "==", True).stream()
    return [f.to_dict() for f in farmers]
