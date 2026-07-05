from app.services.gemini import classify_intent, generate_advisory
from app.services.stt import transcribe_audio
from app.services.firestore import get_or_create_farmer, update_session, update_farmer_language
from app.whatsapp import send_text, send_voice_note, send_interactive_language_select
from app.modules.weather import get_weather_advisory
from app.modules.crop_rag import diagnose_crop
from app.modules.crop_recommend import recommend_crop
from app.modules.schemes import answer_scheme_query

INTENTS = {
    "weather": ["sinchai", "barish", "irrigat", "rain", "water", "baarish", "neer"],
    "crop_disease": ["patti", "leaf", "yellow", "pest", "spray", "bimari", "disease", "rot"],
    "crop_recommend": ["kya ugao", "which crop", "sow", "plant", "fasal", "seed", "beej"],
    "scheme": ["pm-kisan", "pmfby", "kcc", "yojana", "scheme", "paisa", "money", "insurance"],
}

async def handle_message(wa_id, message, msg_type, phone_number_id, contact_name):
    farmer = await get_or_create_farmer(wa_id, contact_name)
    language = farmer.get("language", "hi")  # Default Hindi

    # First-time users: ask language preference
    if farmer.get("is_new"):
        await send_interactive_language_select(wa_id, phone_number_id)
        return

    # Handle interactive button reply (language selection)
    if msg_type == "interactive":
        selected = message.get("interactive", {}).get("button_reply", {}).get("id", "")
        lang_map = {"lang_hi": "hi", "lang_kn": "kn", "lang_mr": "mr", "lang_te": "te"}
        if selected in lang_map:
            await update_farmer_language(wa_id, lang_map[selected])
            await send_text(wa_id, phone_number_id, get_welcome_message(lang_map[selected]))
            return

    # Extract text from message
    if msg_type == "text":
        user_text = message.get("text", {}).get("body", "")

    elif msg_type == "audio":
        # Download OGG from Meta, transcribe via Cloud STT
        audio_id = message.get("audio", {}).get("id")
        user_text = await transcribe_audio(audio_id, language)

    elif msg_type == "image":
        # Crop disease via photo — diagnose directly
        image_id = message.get("image", {}).get("id")
        caption = message.get("image", {}).get("caption", "")
        reply_text = await diagnose_crop(
            wa_id=wa_id,
            image_id=image_id,
            text=caption,
            language=language,
        )
        await send_voice_note(wa_id, phone_number_id, reply_text, language)
        return

    else:
        return  # Unsupported type

    if not user_text:
        return

    # Classify intent
    intent = classify_intent_simple(user_text)

    # Update session
    await update_session(wa_id, {"last_query": user_text, "last_intent": intent})

    # Route to module
    district = farmer.get("district", "")
    crop = farmer.get("crop", "wheat")

    if intent == "weather":
        reply = await get_weather_advisory(district, crop, language)
    elif intent == "crop_disease":
        reply = await diagnose_crop(wa_id=wa_id, text=user_text, language=language)
    elif intent == "crop_recommend":
        reply = await recommend_crop(district, language)
    elif intent == "scheme":
        reply = await answer_scheme_query(user_text, language)
    else:
        reply = await generate_advisory(user_text, language)

    # Send voice note for long replies, text for short ones
    if len(reply) > 100:
        await send_voice_note(wa_id, phone_number_id, reply, language)
    else:
        await send_text(wa_id, phone_number_id, reply)


def classify_intent_simple(text: str) -> str:
    """Fast keyword-based intent classification before calling Gemini."""
    text_lower = text.lower()
    for intent, keywords in INTENTS.items():
        if any(kw in text_lower for kw in keywords):
            return intent
    return "general"


def get_welcome_message(lang: str) -> str:
    messages = {
        "hi": "Namaste! Kisan Alert mein aapka swagat hai. Apna fasal, gaon, aur sawaal batayein.",
        "kn": "Namaskara! Kisan Alert ge swagata. Nimma bele, hooru, mattu prashneya helagiri.",
        "mr": "Namaskar! Kisan Alert madhe swagat ahe. Tumchi pik, gaon, ani prashna sangaa.",
        "te": "Namaskaram! Kisan Alert ki swaagatam. Meeru pandu, ooru, mariyu prashna cheppandi.",
    }
    return messages.get(lang, messages["hi"])
