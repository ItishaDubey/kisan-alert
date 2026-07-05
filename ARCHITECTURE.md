# Kisan Alert — Technical Architecture

This document describes the system **as actually built and deployed**, not the original build brief. See [KISAN_ALERT_TECH_SPEC.md](KISAN_ALERT_TECH_SPEC.md) for the original hackathon spec this was built from; several details below deviate from it based on what was learned during implementation (noted inline).

- **Live prototype:** https://kisan-alert-525940734641.asia-south1.run.app
- **WhatsApp test number:** [+1 (555) 611-9630](https://wa.me/15556119630)
- **Repo:** https://github.com/ItishaDubey/kisan-alert
- **GCP project:** `metal-density-494717-d2` (region: `asia-south1`)

---

## 1. What It Does

Farmers message a WhatsApp number with text, a voice note, or a crop photo. The system replies — in Hindi, Kannada, Marathi, or Telugu — with crop, weather, or crop-health advice, as either a short text or a synthesized voice note.

Three components:

| Component | Trigger | Stack |
|---|---|---|
| **Crop recommendation** | Farmer asks what to plant | Earth Engine (NDVI + soil moisture) → Gemini 2.5 Flash |
| **Dry-spell alerts** | Cloud Scheduler, daily | Open-Meteo → threshold check → proactive WhatsApp push |
| **Crop health diagnosis** | Farmer sends a photo or describes symptoms | Gemini Vision → Firestore case log → RSK WhatsApp notification |

---

## 2. High-Level Architecture

```
                         ┌─────────────────────────┐
  Farmer's WhatsApp ───► │  Meta WhatsApp Cloud API │
                         └────────────┬────────────┘
                                      │ webhook POST
                                      ▼
                      ┌───────────────────────────────┐
                      │   Cloud Run: kisan-alert        │
                      │   FastAPI, single container     │
                      │                                  │
                      │  POST /webhook  ──► 200 OK       │  (returns immediately,
                      │        │                          │   Meta requires <20s)
                      │        ▼ BackgroundTasks          │
                      │  process_webhook()                │
                      │        │                          │
                      │        ▼                          │
                      │  app/router.py::handle_message()   │
                      │   ├─ language selection             │
                      │   ├─ district capture                │
                      │   ├─ keyword intent classification    │
                      │   └─ route to module ─────────────┐   │
                      └────────────────────────────────────┼───┘
                                                            │
        ┌───────────────────┬──────────────────┬───────────┘
        ▼                   ▼                  ▼
  app/modules/         app/modules/       app/modules/
  weather.py           crop_recommend.py  crop_rag.py
        │                   │                  │
        ▼                   ▼                  ▼
  Open-Meteo API      Earth Engine API    app/services/rag.py
        │                   │              (Vertex AI text-embedding-004
        │                   │               → cosine similarity over
        │                   │               Firestore 'disease_kb')
        │                   │                  │
        └───────────┬───────┴──────────────────┘
                     ▼
              Gemini 2.5 Flash
           (app/services/gemini.py)
                     │
                     ▼
          reply text (or reply routed to Cloud TTS
          if > 100 chars → voice note)
                     │
                     ▼
         app/whatsapp.py → Meta Graph API → farmer

  Supporting services (used throughout):
    - Firestore          → farmer profiles, sessions, dedup, crop cases
    - Cloud Storage       → hosts TTS-generated OGG voice notes
    - Cloud Scheduler      → triggers POST /alerts/morning daily
    - Secret Manager        → all credentials injected as env vars at deploy time
```

---

## 3. Request Flow (Inbound Message)

1. Meta POSTs the message event to `POST /webhook`.
2. [webhook.py](app/webhook.py) returns `{"status": "ok"}` **immediately**, then hands the body to a `BackgroundTasks` job (`process_webhook`). This is required — Meta retries (causing duplicate sends) if the endpoint takes more than ~20s, and Gemini/TTS calls can be slow.
3. `process_webhook` dedupes on `message.id` against the Firestore `processed_messages` collection, then calls `router.handle_message`.
4. `router.py::handle_message` runs a fixed decision order — **this order matters and was the source of a real bug** (see §6):
   1. Interactive button reply (language selection) — handled first, unconditionally.
   2. First-time farmer with no language set → send language-select buttons, stop.
   3. Farmer has a language but no `district` on file → treat the next text reply as their village/district, geocode it, save it, stop.
   4. Otherwise: extract text (transcribing audio via Cloud STT if needed, or branching straight to Gemini Vision for images), classify intent by keyword match, route to the matching module, send the reply.
5. Replies over 100 characters are sent as a voice note (Cloud TTS → GCS → WhatsApp audio message); shorter replies are sent as plain text.
6. Any exception anywhere in this chain is caught and logged, never re-raised — the webhook must never signal failure back to Meta or it will retry.

**Crop disease diagnosis (text description, no photo) is retrieval-augmented:** [crop_rag.py](app/modules/crop_rag.py) embeds the farmer's message with Vertex AI's `text-embedding-004`, ranks it by cosine similarity against a small ICAR-style disease knowledge base ([app/data/icar_diseases.py](app/data/icar_diseases.py), pre-embedded once via `scripts/seed_rag.py` into the Firestore `disease_kb` collection), and includes the top 3 matches as grounding context in the Gemini prompt. See §6 for why this doesn't use a deployed Vertex AI Vector Search endpoint.

---

## 4. Tech Stack

| Layer | Choice |
|---|---|
| API framework | FastAPI on Cloud Run (serverless container, scales to zero) |
| LLM | Gemini 2.5 Flash (text + vision) via `google-generativeai` SDK |
| Speech-to-text | Cloud Speech-to-Text v2, Chirp 3 model |
| Text-to-speech | Cloud Text-to-Speech, Chirp 3 HD voices, OGG/OPUS output |
| Satellite data | Google Earth Engine (Sentinel-2 NDVI, ERA5 soil moisture) |
| Weather | Open-Meteo (free, no key) |
| Geocoding | Google Maps Geocoding API |
| Database | Firestore, Native mode, `asia-south1` |
| RAG (crop disease) | Vertex AI `text-embedding-004` (via ADC — no API key needed) + in-process cosine similarity over a Firestore-stored knowledge base; no deployed Vector Search endpoint (see §6) |
| File storage | Cloud Storage (public bucket, serves TTS audio to WhatsApp) |
| Messaging | WhatsApp Business Cloud API (Meta Graph API v19.0) |
| Scheduling | Cloud Scheduler → authenticated HTTP POST |
| Secrets | Google Secret Manager, mounted as env vars at deploy time |
| Deployment | `gcloud run deploy --source .` (Cloud Build compiles the Dockerfile) |

---

## 5. Data Model (Firestore)

| Collection | Key | Fields |
|---|---|---|
| `farmers` | `wa_id` (WhatsApp number) | `name`, `language`, `district`, `crop`, `is_new`, `opted_in_alerts` |
| `sessions` | `wa_id` | `last_query`, `last_intent`, `updated_at` |
| `crop_cases` | auto-id | `wa_id`, `district`, `diagnosis`, `image_id`, `rsk_notified` |
| `processed_messages` | `message_id` | `processed_at` — webhook dedup only |
| `disease_kb` | disease id (e.g. `wheat_rust`) | `crop`, `name`, `symptoms`, `cause`, `remedy`, `embedding` (768-dim vector) — seeded once via `scripts/seed_rag.py`, read by `app/services/rag.py` |

---

## 6. Design Decisions & Fixes Made During Build

These aren't in the original spec — they were discovered while getting the prototype actually working, and matter for anyone picking this codebase up:

- **Gemini requires a real API key, not ADC.** `google-generativeai` (the Generative Language API) rejects service-account/OAuth tokens outright with `403 ACCESS_TOKEN_SCOPE_INSUFFICIENT`, regardless of IAM role. `GEMINI_API_KEY` must come from [Google AI Studio](https://aistudio.google.com/app/apikey), stored in Secret Manager (`gemini-api-key`), and injected as an env var. This is a hard requirement, not an optimization.
- **Firestore/Storage clients must be lazy.** The original code built `firestore.Client()` and `storage.Client()` at module import time. That crashes the app at startup in any environment without live ADC (e.g. local dev without `gcloud auth application-default login`). Fixed with a `_LazyClient` wrapper in [firestore.py](app/services/firestore.py) that defers construction to first use.
- **Cloud Run only resolves `--set-secrets` at container startup**, not per-request. Rotating a secret (e.g. the WhatsApp access token) requires forcing a new revision (`gcloud run services update --update-secrets=...`) — updating Secret Manager alone does nothing until the container restarts.
- **Routing order bug:** the original logic checked "is this farmer new?" before checking "is this an interactive button reply?" — so a brand-new farmer's language-selection tap re-triggered the same language prompt forever instead of being processed. Fixed by handling interactive replies first, unconditionally, in `router.py`.
- **No district-capture flow existed.** `weather.py` and `crop_recommend.py` both require `farmer.district`, but nothing in the original router ever wrote it. Added a capture step: the first free-text reply from a farmer with no district on file is geocoded and saved, with a confirmation message, before normal intent routing resumes.
- **`print()` is buffered inside the container.** Errors were sometimes invisible in logs for several minutes after the actual failure. Fixed by flushing explicitly (`flush=True`, `traceback.print_exc()`) and setting `PYTHONUNBUFFERED=1` in the Dockerfile.
- **`.env.example` must never contain real values.** It's a committed template; secrets belong only in the gitignored `.env` (local) or Secret Manager (deployed).
- **The original spec's Vertex AI Vector Search plan was never actually wired up** — `seed_rag.py` only provisioned an empty Matching Engine index/endpoint, and `crop_rag.py` never queried it. A deployed Vector Search endpoint also takes 30-60+ minutes to spin up and bills hourly for the always-on machine regardless of traffic, which doesn't fit a hackathon prototype. Replaced with a lighter approach that's still genuinely Vertex AI-powered: embed the farmer's message with `text-embedding-004`, rank a small pre-embedded knowledge base by cosine similarity in Python, no deployed index. Vertex AI's own APIs (unlike the Gemini Generative Language API above) authenticate fine via ADC.

---

## 7. Deployment

```bash
gcloud run deploy kisan-alert \
  --source . \
  --region asia-south1 \
  --project=metal-density-494717-d2 \
  --allow-unauthenticated
```

Secrets are wired in via `--set-secrets` (see [scripts/deploy.sh](scripts/deploy.sh)); non-secret config via `--set-env-vars`. The morning dry-spell check is triggered by a Cloud Scheduler job hitting `POST /alerts/morning` with a shared-secret header (`X-Scheduler-Secret`).

- `GET /` — HTML landing page (hackathon submission URL)
- `GET /health` — `{"status": "ok", "service": "kisan-alert"}`, for monitoring
- `GET/POST /webhook` — Meta webhook verification + message ingestion
- `POST /alerts/morning` — Cloud Scheduler entry point

---

## 8. Known Limitations

- Intent classification is keyword-based and only matches **romanized** keywords (e.g. `"sinchai"`); messages typed in native script (Devanagari, Kannada, etc.) fall through to the Gemini general-chat path instead of the weather/disease/scheme modules.
- RSK (Rythu Seva Kendra) notification sends to a single hardcoded demo number, not a real per-district lookup table.
- No retry/backoff around Meta Graph API calls; a transient failure is logged and silently dropped, not queued for retry.
- The disease knowledge base (`app/data/icar_diseases.py`) has 10 entries covering major crops, not a comprehensive ICAR corpus — enough to demonstrate real retrieval-augmented grounding, not production coverage. Similarity search loads the whole KB into memory per query, which is fine at this size but wouldn't scale past a few thousand entries without a real vector index.
