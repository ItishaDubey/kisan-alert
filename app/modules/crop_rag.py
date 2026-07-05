from app.services.gemini import diagnose_with_vision, generate_advisory
from app.services.firestore import log_crop_case, get_or_create_farmer
from app.services.rag import retrieve_similar_diseases
from app.whatsapp import download_media, send_text
import os

RSK_WHATSAPP_NUMBER = os.getenv("RSK_DEMO_NUMBER", "")  # For demo: your own number
RSK_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

async def diagnose_crop(
    wa_id: str,
    language: str,
    text: str = "",
    image_id: str = "",
) -> str:
    """
    Diagnose crop disease from photo or text description.
    Log case to Firestore. Notify nearest RSK via WhatsApp.
    """
    farmer = await get_or_create_farmer(wa_id)
    district = farmer.get("district", "Unknown")

    if image_id:
        # Photo-based diagnosis via Gemini Vision
        image_bytes = await download_media(image_id)
        diagnosis = await diagnose_with_vision(image_bytes, text, language)
    else:
        # Text description via Gemini + RAG: retrieve similar known diseases
        # from the ICAR knowledge base and ground the prompt in them.
        matches = await retrieve_similar_diseases(text, top_k=3)
        if matches:
            reference_block = "\n".join(
                f"- {m['name']} ({m['crop']}): symptoms — {m['symptoms']} "
                f"cause — {m['cause']} remedy — {m['remedy']}"
                for m in matches
            )
        else:
            reference_block = "(no knowledge base entries available)"

        prompt = f"""
Farmer describes: "{text}"
Farmer's crop: {farmer.get('crop', 'unknown')}
Farmer's district: {district}

Reference: possible matches from the ICAR crop disease knowledge base, most similar first:
{reference_block}

Using the reference entries where relevant (they may not all apply — use judgment), diagnose the crop issue:
1. Most likely disease or pest (specific name in local and scientific)
2. Likely cause
3. Recommended remedy with exact product name, dosage, and application method
4. Safety precautions
5. When to expect improvement

Under 120 words."""
        diagnosis = await generate_advisory(prompt, language)

    # Log case to Firestore
    await log_crop_case(
        wa_id=wa_id,
        district=district,
        diagnosis=diagnosis,
        image_id=image_id,
    )

    # Notify RSK (for demo: sends to a configured WhatsApp number)
    await notify_rsk(wa_id, district, diagnosis)

    return diagnosis


async def notify_rsk(wa_id: str, district: str, diagnosis: str):
    """
    Send crop case details to the nearest Rythu Seva Kendra WhatsApp number.
    In production: look up RSK number by district from a Firestore lookup table.
    For demo: sends to RSK_DEMO_NUMBER (set to your own number for testing).
    """
    if not RSK_WHATSAPP_NUMBER:
        return

    notification = (
        f"🌾 Kisan Alert — New Crop Case\n\n"
        f"Farmer: {wa_id}\n"
        f"District: {district}\n\n"
        f"Diagnosis:\n{diagnosis}\n\n"
        f"Please arrange expert follow-up if needed."
    )

    await send_text(RSK_WHATSAPP_NUMBER, RSK_PHONE_NUMBER_ID, notification)
