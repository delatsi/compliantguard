# Detailed Firebase Discovery for project medtelligence

echo "🔍 Detailed Firebase scan for project: medtelligence"
echo "Project ID: 668668923572"

# Set the project
gcloud config set project medtelligence

echo "=== All Firebase-related APIs ==="
gcloud services list --enabled --filter="name~firebase" --format="table(name,title)"

echo "=== Firestore/Database Services ==="
gcloud services list --enabled --filter="name~(firestore|database)" --format="table(name,title)"

echo "=== Storage Services ==="
gcloud services list --enabled --filter="name~storage" --format="table(name,title)"

echo "=== Authentication Services ==="
gcloud services list --enabled --filter="name~(auth|identity)" --format="table(name,title)"

echo "=== Check for Firestore databases ==="
gcloud firestore databases list --project=medtelligence 2>/dev/null || echo "No Firestore databases or access denied"

echo "=== Check for Firebase projects via API ==="
# Try to get Firebase project info
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     "https://firebase.googleapis.com/v1beta1/projects/medtelligence" 2>/dev/null || echo "No Firebase project API access"

echo "=== Check App Engine (often used with Firebase) ==="
gcloud app describe --project=medtelligence 2>/dev/null || echo "No App Engine app"

echo "=== Check Cloud Functions (Firebase Functions) ==="
gcloud functions list --project=medtelligence 2>/dev/null || echo "No Cloud Functions"

echo "=== Check for Firebase Hosting ==="
# Look for Firebase Hosting in enabled services
gcloud services list --enabled --filter="name~hosting" --format="table(name,title)"

echo "=== Check for Firebase-related IAM service accounts ==="
gcloud iam service-accounts list --filter="email~firebase" --format="table(email,displayName)"

echo "=== Check for Firebase-related secrets ==="
gcloud secrets list --filter="name~firebase" --format="table(name)" 2>/dev/null || echo "No secrets or access denied"

echo "=== Firebase Rules Service Details ==="
# Since we know firebaserules.googleapis.com is enabled
echo "Firebase Rules API is enabled - this suggests active Firebase usage"
echo "Common Firebase services that use rules:"
echo "  - Cloud Firestore"
echo "  - Firebase Realtime Database" 
echo "  - Cloud Storage for Firebase"

echo "=== Try Firebase CLI (if available) ==="
if command -v firebase &> /dev/null; then
    echo "Firebase CLI found, checking project info..."
    firebase use medtelligence 2>/dev/null || echo "Cannot switch to Firebase project"
    firebase projects:info 2>/dev/null || echo "No Firebase project info available"
else
    echo "Firebase CLI not installed"
    echo "Install with: npm install -g firebase-tools"
    echo "Then run: firebase login && firebase use medtelligence"
fi

echo "=== Check for client-side Firebase config in your assets ==="
echo "Looking for Firebase config in K8s resources..."

# Check if any configmaps or secrets contain Firebase configuration
cat gcp_assets.json | jq '.[] | select(.assetType == "v1/ConfigMap") | .resource.data.data' 2>/dev/null | grep -i firebase || echo "No Firebase config in ConfigMaps"

cat gcp_assets.json | jq '.[] | select(.assetType == "v1/Secret") | .resource.data.metadata.name' 2>/dev/null | grep -i firebase || echo "No Firebase secrets in K8s"

echo "=== Summary ==="
echo "✅ Firebase Rules API is enabled"
echo "🔍 This indicates Firebase services are being used"
echo "📋 Common Firebase services with security rules:"
echo "   - Cloud Firestore (NoSQL database)"
echo "   - Firebase Realtime Database"
echo "   - Cloud Storage for Firebase"
echo ""
echo "🚨 HIPAA Implications:"
echo "   - Firebase services can handle PHI if configured correctly"
echo "   - Client-side access requires careful security rules"
echo "   - Real-time data sync needs audit logging"
echo "   - Authentication must be properly configured"
