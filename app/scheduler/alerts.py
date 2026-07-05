from fastapi import APIRouter, Request, HTTPException
from app.services.firestore import get_opted_in_farmers
from app.services.geocoding import resolve_district
from app.modules.weather import check_dry_spell_risk
from app.whatsapp import send_text
import os

router = APIRouter()
SCHEDULER_SECRET = os.getenv("SCHEDULER_SECRET", "")


@router.post("/morning")
async def morning_alerts(request: Request):
    # Authenticate Cloud Scheduler
    auth = request.headers.get("X-Scheduler-Secret", "")
    if auth != SCHEDULER_SECRET:
        raise HTTPException(status_code=403)

    farmers = await get_opted_in_farmers()
    sent = 0

    for farmer in farmers:
        try:
            district = farmer.get("district", "")
            if not district:
                continue

            lat, lng, _ = await resolve_district(district)
            risk = await check_dry_spell_risk(lat, lng)

            if risk["dry_spell_risk"]:
                lang = farmer.get("language", "hi")
                message = get_dry_spell_alert(district, risk, lang)
                phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
                await send_text(farmer["wa_id"], phone_number_id, message)
                sent += 1

        except Exception as e:
            print(f"Alert error for {farmer.get('wa_id')}: {e}")
            continue

    return {"sent": sent, "total": len(farmers)}


def get_dry_spell_alert(district: str, risk: dict, language: str) -> str:
    alerts = {
        "hi": f"🌾 Kisan Alert: {district} mein agli 24 ghante mein barish ki sambhavna sirf {risk['rain_prob_24h']}% hai. Soil moisture bhi kam hai. Aaj sinchai karne ka sahi samay hai.",
        "kn": f"🌾 Kisan Alert: {district} nalli modala 24 gantegala mele male sambhavane kevala {risk['rain_prob_24h']}%. Neeru haakvudu indu sahaya aaguttade.",
        "mr": f"🌾 Kisan Alert: {district} madhe pudchya 24 taasaat paausa hoNyaachi shakyata fakt {risk['rain_prob_24h']}% aahe. Aaj paaNi dya.",
        "te": f"🌾 Kisan Alert: {district} lo tarvata 24 gantallo varsham padE sambhavana kevalam {risk['rain_prob_24h']}%. Neeru pinchukovaDaniki idi manchisamu.",
    }
    return alerts.get(language, alerts["hi"])
