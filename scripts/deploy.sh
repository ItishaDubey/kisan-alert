#!/bin/bash
set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="asia-south1"
SERVICE_NAME="kisan-alert"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "Building and deploying $SERVICE_NAME to Cloud Run in $REGION..."

# Build and push image
gcloud builds submit --tag $IMAGE

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION" \
  --set-secrets "WHATSAPP_ACCESS_TOKEN=whatsapp-access-token:latest,WHATSAPP_VERIFY_TOKEN=whatsapp-verify-token:latest,GOOGLE_MAPS_API_KEY=google-maps-api-key:latest,SCHEDULER_SECRET=scheduler-secret:latest"

echo "Done. Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
