import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))  # Or use ADC — see note below

# NOTE: On Cloud Run, use Application Default Credentials (ADC) not API key.
# ADC is automatic when the Cloud Run service account has the right IAM roles.
# For local dev, set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON.

FLASH = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

SYSTEM_PROMPT = """You are Kisan Alert, an agricultural advisory assistant for small and marginal farmers in India.
Always respond in the farmer's language. Keep responses concise — under 120 words.
Be specific: give exact measurements, dosages, and timing. Never give vague advice.
Frame advice as a recommendation, not a command. Acknowledge the farmer's existing knowledge."""


async def generate_advisory(prompt: str, language: str = "hi") -> str:
    model = genai.GenerativeModel(
        model_name=FLASH,
        system_instruction=SYSTEM_PROMPT,
    )
    lang_instruction = f"\nRespond in {'Hindi' if language == 'hi' else 'Kannada' if language == 'kn' else 'Marathi' if language == 'mr' else 'Telugu'}."
    response = model.generate_content(prompt + lang_instruction)
    return response.text


async def generate_with_search_grounding(prompt: str, language: str = "hi") -> str:
    """Use Gemini with Google Search Grounding for live scheme data."""
    model = genai.GenerativeModel(
        model_name=FLASH,
        system_instruction=SYSTEM_PROMPT,
        tools=["google_search_retrieval"],
    )
    lang_instruction = f"\nRespond in {'Hindi' if language == 'hi' else 'Kannada' if language == 'kn' else 'Marathi' if language == 'mr' else 'Telugu'}. Only cite verified government sources."
    response = model.generate_content(prompt + lang_instruction)
    return response.text


async def diagnose_with_vision(image_bytes: bytes, text_context: str, language: str = "hi") -> str:
    """Send crop image to Gemini Vision for disease diagnosis."""
    import PIL.Image
    import io

    model = genai.GenerativeModel(model_name=FLASH, system_instruction=SYSTEM_PROMPT)
    image = PIL.Image.open(io.BytesIO(image_bytes))

    lang_map = {"hi": "Hindi", "kn": "Kannada", "mr": "Marathi", "te": "Telugu"}
    prompt = f"""This is a photo of a crop sent by a farmer.
Farmer's description (if any): {text_context}
Identify:
1. The crop type (if visible)
2. The disease or pest (specific name)
3. The likely cause
4. The remedy with exact dosage and timing
5. Any safety warnings

Respond in {lang_map.get(language, 'Hindi')} in under 150 words. Be specific."""

    response = model.generate_content([prompt, image])
    return response.text


def classify_intent(text: str) -> str:
    """Lightweight intent classification — call only when keyword matching fails."""
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite-preview-06-17")
    prompt = f"""Classify this farmer message into exactly one of: weather, crop_disease, crop_recommend, scheme, general
Message: "{text}"
Reply with only the category word, nothing else."""
    response = model.generate_content(prompt)
    return response.text.strip().lower()
