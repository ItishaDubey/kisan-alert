import googlemaps
import os

gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

async def resolve_district(location_text: str) -> tuple[float, float, str]:
    """Convert spoken village or district name to lat/lng. Returns (lat, lng, formatted_address)."""
    results = gmaps.geocode(f"{location_text}, India")
    if not results:
        return 20.5937, 78.9629, "India"  # Default to India center

    loc = results[0]["geometry"]["location"]
    address = results[0]["formatted_address"]
    return loc["lat"], loc["lng"], address
