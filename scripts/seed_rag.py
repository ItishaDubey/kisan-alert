"""One-time script: load ICAR disease vectors into a Vertex AI Vector Search index.

Run once, then set VERTEX_AI_INDEX_ENDPOINT and VERTEX_AI_DEPLOYED_INDEX_ID
in .env from the values printed at the end of this script.
"""
import os
from google.cloud import aiplatform

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")


def main():
    aiplatform.init(project=PROJECT_ID, location=LOCATION)

    index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
        display_name="icar-disease-index",
        dimensions=768,
        approximate_neighbors_count=10,
        distance_measure_type="DOT_PRODUCT_DISTANCE",
    )

    endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
        display_name="icar-disease-endpoint",
        public_endpoint_enabled=True,
    )

    deployed_index_id = "icar_disease_deployed"
    endpoint.deploy_index(index=index, deployed_index_id=deployed_index_id)

    print(f"VERTEX_AI_INDEX_ENDPOINT={endpoint.resource_name}")
    print(f"VERTEX_AI_DEPLOYED_INDEX_ID={deployed_index_id}")


if __name__ == "__main__":
    main()
