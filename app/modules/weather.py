import httpx
from app.services.geocoding import resolve_district
from app.services.gemini import generate_advisory

async def get_weather_advisory(district: str, crop: str, language: str) -> str:
    """
    Fetch hyperlocal weather from Open-Meteo.
    Generate irrigation/fertilisation advisory via Gemini.
    """
    if not district:
        return get_no_location_message(language)

    lat, lng, address = await resolve_district(district)
    weather = await fetch_weather(lat, lng)

    prompt = f"""
Farmer location: {address}
Crop: {crop}
Current weather data:
- Rain probability next 6 hours: {weather['rain_prob_6h']}%
- Rain probability next 24 hours: {weather['rain_prob_24h']}%
- Temperature: {weather['temp']}°C
- Humidity: {weather['humidity']}%
- Soil moisture estimate: {weather['soil_moisture']}

Based on this data:
1. Should the farmer irrigate today? Give a clear yes/no with reason.
2. Any fertilisation guidance given the conditions?
3. Any crop-specific warning for {crop}?

Keep the response under 100 words. Be direct."""

    return await generate_advisory(prompt, language)


async def fetch_weather(lat: float, lng: float) -> dict:
    """Fetch from Open-Meteo — free, no API key required."""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lng}"
        f"&hourly=precipitation_probability,soil_moisture_0_to_1cm"
        f"&current=temperature_2m,relative_humidity_2m,precipitation_probability"
        f"&timezone=Asia/Kolkata"
        f"&forecast_days=2"
    )
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

    current = data.get("current", {})
    hourly = data.get("hourly", {})
    precip = hourly.get("precipitation_probability", [0] * 24)

    return {
        "temp": current.get("temperature_2m", 25),
        "humidity": current.get("relative_humidity_2m", 60),
        "rain_prob_6h": max(precip[:6]) if precip else 0,
        "rain_prob_24h": max(precip[:24]) if precip else 0,
        "soil_moisture": hourly.get("soil_moisture_0_to_1cm", [0.2])[0],
    }


async def check_dry_spell_risk(lat: float, lng: float) -> dict:
    """Used by the morning alert scheduler to check if a farmer needs a dry-spell alert."""
    weather = await fetch_weather(lat, lng)
    dry_spell = weather["rain_prob_24h"] < 20 and weather["soil_moisture"] < 0.15
    return {
        "dry_spell_risk": dry_spell,
        "rain_prob_24h": weather["rain_prob_24h"],
        "soil_moisture": weather["soil_moisture"],
    }


def get_no_location_message(language: str) -> str:
    messages = {
        "hi": "Kripaya apna gaon ya zila batayein, phir hum aapke liye weather advisory de sakte hain.",
        "kn": "Dayavittu nimma ooru athava jille hesaru helagiri, naantara weather advisory nidutteve.",
        "mr": "Krupaya tumche gaon kiva jilha sangaa, mag aamhi weather advisory deu.",
        "te": "Dayachesi meeru ooru leda jilla peru cheppandi, appudu weather advisory istamu.",
    }
    return messages.get(language, messages["hi"])
