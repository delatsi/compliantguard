#!/bin/bash
# Quick test to verify Firebase API detection

echo "🔍 Quick Firebase detection test..."

PROJECT_ID="medtelligence"

echo "1. Checking if firebaserules.googleapis.com is enabled..."
gcloud services list --enabled --project=$PROJECT_ID --filter="name:firebaserules.googleapis.com" --format="value(name)"

echo ""
echo "2. Getting all enabled APIs with 'firebase' in the name..."
gcloud services list --enabled --project=$PROJECT_ID --format="value(name)" | grep -i firebase

echo ""
echo "3. Getting all enabled APIs with 'storage' in the name..."
gcloud services list --enabled --project=$PROJECT_ID --format="value(name)" | grep -i storage

echo ""
echo "4. Getting all enabled APIs with 'auth' or 'identity' in the name..."
gcloud services list --enabled --project=$PROJECT_ID --format="value(name)" | grep -E "(auth|identity)"

echo ""
echo "5. Testing the exact command the Firebase scanner uses..."
gcloud services list --enabled --project=$PROJECT_ID --format=json | jq -r '.[].name' | grep -i firebase || echo "No firebase APIs found"

echo ""
echo "6. Raw output of services list (first 5 lines)..."
gcloud services list --enabled --project=$PROJECT_ID --format=json | jq -r '.[].name' | head -5
