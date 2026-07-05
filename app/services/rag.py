"""Lightweight RAG over the ICAR-style disease knowledge base.

Uses Vertex AI's text-embedding model (authenticates via ADC — unlike the
Gemini Generative Language API, Vertex AI's own APIs accept service-account
credentials directly, no API key needed). Embeddings are precomputed once by
scripts/seed_rag.py and stored in Firestore; at query time we embed the
farmer's message and rank the small corpus by cosine similarity in-process,
which avoids running an always-on Vertex AI Vector Search endpoint.
"""
import os
import math

import vertexai
from vertexai.language_models import TextEmbeddingModel

from app.services.firestore import db

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
KB_COLLECTION = "disease_kb"

_embedding_model = None
_initialized = False


def _get_embedding_model():
    global _embedding_model, _initialized
    if not _initialized:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        _initialized = True
    if _embedding_model is None:
        _embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    return _embedding_model


def embed_text(text: str) -> list[float]:
    model = _get_embedding_model()
    embeddings = model.get_embeddings([text])
    return embeddings[0].values


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def retrieve_similar_diseases(query_text: str, top_k: int = 3) -> list[dict]:
    """Embed the farmer's query and return the top_k most similar disease
    entries from the knowledge base (empty list if the KB hasn't been seeded)."""
    query_vector = embed_text(query_text)

    docs = list(db.collection(KB_COLLECTION).stream())
    if not docs:
        return []

    scored = []
    for doc in docs:
        data = doc.to_dict()
        similarity = _cosine_similarity(query_vector, data["embedding"])
        scored.append((similarity, data))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [data for _, data in scored[:top_k]]
