import ee
import os

def init_earth_engine():
    """Initialize Earth Engine with service account credentials."""
    credentials = ee.ServiceAccountCredentials(
        email=os.getenv("GEE_SERVICE_ACCOUNT_EMAIL"),
        key_file=os.getenv("GEE_SERVICE_ACCOUNT_KEY_FILE"),
    )
    ee.Initialize(credentials)


async def get_ndvi_and_soil_moisture(lat: float, lng: float) -> dict:
    """
    Get NDVI (crop health) and soil moisture for a lat/lng point.
    Uses Sentinel-2 for NDVI, ERA5 for soil moisture.
    Returns dict with ndvi (float -1 to 1), soil_moisture (float), stress_level (str).
    """
    try:
        init_earth_engine()
        point = ee.Geometry.Point([lng, lat])
        buffer = point.buffer(5000)  # 5km radius

        # NDVI from Sentinel-2
        s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
              .filterBounds(buffer)
              .filterDate(ee.Date(get_30_days_ago()), ee.Date.now())
              .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
              .median())

        ndvi = s2.normalizedDifference(["B8", "B4"])
        ndvi_val = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=buffer,
            scale=10,
        ).getInfo().get("nd", 0.5)

        # Soil moisture from ERA5
        era5 = (ee.ImageCollection("ECMWF/ERA5/DAILY")
                .filterBounds(buffer)
                .filterDate(ee.Date(get_7_days_ago()), ee.Date.now())
                .select("volumetric_soil_water_layer_1")
                .mean())

        sm_val = era5.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=buffer,
            scale=27830,
        ).getInfo().get("volumetric_soil_water_layer_1", 0.2)

        # Classify stress
        if ndvi_val < 0.2:
            stress = "high"
        elif ndvi_val < 0.4:
            stress = "moderate"
        else:
            stress = "low"

        return {
            "ndvi": round(ndvi_val, 3),
            "soil_moisture": round(sm_val, 3),
            "stress_level": stress,
        }

    except Exception as e:
        print(f"Earth Engine error: {e}")
        return {"ndvi": 0.5, "soil_moisture": 0.2, "stress_level": "unknown"}


def get_30_days_ago() -> str:
    from datetime import datetime, timedelta
    return (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

def get_7_days_ago() -> str:
    from datetime import datetime, timedelta
    return (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
