from app.services.geocoding import resolve_district
from app.services.earth_engine import get_ndvi_and_soil_moisture
from app.services.gemini import generate_advisory
from datetime import datetime

async def recommend_crop(district: str, language: str) -> str:
    """
    Cross-reference GEE satellite data with season and district
    to recommend suitable crops before sowing.
    """
    lat, lng, address = await resolve_district(district)
    satellite = await get_ndvi_and_soil_moisture(lat, lng)
    month = datetime.now().month
    season = "Kharif (June-Nov)" if 6 <= month <= 11 else "Rabi (Nov-Apr)"

    prompt = f"""
Farmer location: {address}
Current season: {season}
Satellite data:
- NDVI (vegetation health index): {satellite['ndvi']} (0=bare, 1=healthy vegetation)
- Soil moisture: {satellite['soil_moisture']} m³/m³
- Soil stress level: {satellite['stress_level']}

Based on this satellite data, current season, and typical crops for this region:
1. Top 2-3 recommended crops with brief reason for each
2. Any soil preparation advice based on the moisture reading
3. Groundwater caution if soil moisture indicates stress

Under 120 words. Be specific to this district and season."""

    return await generate_advisory(prompt, language)
