"""One-time script: embed the ICAR-style disease knowledge base
(app/data/icar_diseases.py) via Vertex AI's text-embedding model and store
the vectors in Firestore for retrieval by app/services/rag.py.

Run once after deploying, or whenever app/data/icar_diseases.py changes:
    python scripts/seed_rag.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

import vertexai
from vertexai.language_models import TextEmbeddingModel
from google.cloud import firestore

from app.data.icar_diseases import DISEASES

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
KB_COLLECTION = "disease_kb"


def main():
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    db = firestore.Client(project=PROJECT_ID)

    for entry in DISEASES:
        embed_source = (
            f"{entry['name']} ({entry['crop']}). "
            f"Symptoms: {entry['symptoms']} "
            f"Cause: {entry['cause']}"
        )
        vector = model.get_embeddings([embed_source])[0].values

        db.collection(KB_COLLECTION).document(entry["id"]).set({
            **entry,
            "embedding": vector,
        })
        print(f"Seeded: {entry['id']} ({len(vector)}-dim)")

    print(f"\nDone. {len(DISEASES)} entries written to Firestore collection '{KB_COLLECTION}'.")


if __name__ == "__main__":
    main()
