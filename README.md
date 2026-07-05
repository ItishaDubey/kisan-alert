# Kisan Alert 🌾

WhatsApp-based agricultural advisory system for small and marginal farmers.
Built on Google Cloud for Code for Communities Hackathon 2026.

## What it does

Farmers send a WhatsApp message — text, voice note, or crop photo.
Kisan Alert replies in under 4 seconds in Hindi, Kannada, Marathi, or Telugu.

**Component 1 — Crop recommendation:** Google Earth Engine NDVI + soil moisture
+ Gemini 2.5 Flash — pre-sowing crop advice specific to district and season.

**Component 2 — Dry-spell alerts:** Open-Meteo 1km weather grid + Cloud Scheduler
— proactive WhatsApp alerts when dry-spell risk crosses threshold.

**Component 3 — Crop health + RSK follow-up:** Photo or voice note — Gemini Vision
diagnosis — logged in Firestore — nearest Rythu Seva Kendra notified via WhatsApp.

## Tech stack

- FastAPI on Google Cloud Run (serverless)
- Gemini 2.5 Flash + Gemini Vision
- Cloud STT Chirp 3 (voice note transcription)
- Cloud TTS Chirp 3 HD (voice note replies)
- Google Earth Engine (NDVI, soil moisture)
- Open-Meteo (hyperlocal weather)
- Google Maps Geocoding
- Firestore (farmer profiles, session state)
- WhatsApp Business Cloud API

## Setup

### 1. Prerequisites
- GCP project with billing enabled
- Meta developer account with WhatsApp Business App
- Google Maps API key
- Earth Engine service account

### 2. Clone and configure
```bash
git clone https://github.com/ItishaDubey/kisan-alert
cd kisan-alert
cp .env.example .env
# Fill in all values in .env
```

### 3. Local development
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
# Use ngrok for WhatsApp webhook testing: ngrok http 8080
```

### 4. Deploy to Cloud Run
```bash
bash scripts/deploy.sh
```

## WhatsApp webhook setup

1. Deploy to Cloud Run first to get your HTTPS URL
2. Meta App Dashboard → WhatsApp → Configuration
3. Webhook URL: `https://YOUR-CLOUD-RUN-URL/webhook`
4. Verify token: same as `WHATSAPP_VERIFY_TOKEN` in your env
5. Subscribe to: `messages`

## Cloud Scheduler setup (morning alerts)

```bash
gcloud scheduler jobs create http kisan-morning-alerts \
  --schedule="45 0 * * *" \
  --uri="https://YOUR-CLOUD-RUN-URL/alerts/morning" \
  --message-body='{}' \
  --headers="X-Scheduler-Secret=YOUR_SECRET,Content-Type=application/json" \
  --time-zone="Asia/Kolkata"
```
