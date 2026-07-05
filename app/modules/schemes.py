from app.services.gemini import generate_with_search_grounding

async def answer_scheme_query(query: str, language: str) -> str:
    """Answer PM-KISAN, PMFBY, KCC queries using Gemini Search Grounding."""
    prompt = f"""
A farmer is asking about a government agricultural scheme: "{query}"

Using only verified government sources (pmkisan.gov.in, pmfby.gov.in, official GOI sites):
1. Answer the specific question directly
2. State the current installment amount or coverage amount
3. Give the enrollment deadline if applicable
4. Mention one action the farmer should take

Do NOT make up amounts, dates, or eligibility criteria. If unsure, say so.
Under 100 words."""

    return await generate_with_search_grounding(prompt, language)
