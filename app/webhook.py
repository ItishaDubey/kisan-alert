from fastapi import APIRouter, Request, Query, BackgroundTasks, HTTPException, Response
from app.router import handle_message
from app.services.firestore import is_duplicate, mark_processed
import os
import hmac, hashlib

router = APIRouter()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")  # For payload signature verification

@router.get("")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Forbidden")

@router.post("")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    # Always return 200 immediately
    body = await request.json()
    background_tasks.add_task(process_webhook, body)
    return {"status": "ok"}

async def process_webhook(body: dict):
    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return  # Status update or other event, not a message

        message = messages[0]
        message_id = message.get("id")
        wa_id = message.get("from")  # Farmer's WhatsApp number
        msg_type = message.get("type")  # text | audio | image | interactive

        # Deduplication
        if await is_duplicate(message_id):
            return
        await mark_processed(message_id)

        phone_number_id = value.get("metadata", {}).get("phone_number_id")
        contact_name = value.get("contacts", [{}])[0].get("profile", {}).get("name", "")

        await handle_message(
            wa_id=wa_id,
            message=message,
            msg_type=msg_type,
            phone_number_id=phone_number_id,
            contact_name=contact_name,
        )
    except Exception as e:
        print(f"Error processing webhook: {e}")
        # Never raise — return silently so Meta doesn't retry
