# Firebase Asset Discovery Methods

echo "=== Firebase Project Discovery ==="

# 1. List all Firebase projects (requires Firebase CLI)
firebase projects:list

# 2. Get Firebase project config from GCP project
gcloud projects list --format="table(projectId,name)" | while read project name; do
    echo "Checking project: $project"
    
    # Check if Firebase is enabled for this project
    gcloud services list --enabled --project=$project --filter="name:firebase" --format="value(name)"
    
    # Check for Firebase APIs
    gcloud services list --enabled --project=$project --filter="name~firebase" --format="table(name,title)"
done

echo "=== Firebase Service Discovery ==="

# 3. Check for Firebase services via gcloud
for project in $(gcloud projects list --format="value(projectId)"); do
    echo "Project: $project"
    
    # Firebase Authentication
    gcloud identity providers list --project=$project 2>/dev/null || echo "No Firebase Auth"
    
    # Firebase Hosting
    gcloud firebase hosting sites list --project=$project 2>/dev/null || echo "No Firebase Hosting"
    
    # App Engine (often used with Firebase)
    gcloud app describe --project=$project 2>/dev/null || echo "No App Engine"
    
    # Check for Firestore (Native mode)
    gcloud firestore databases list --project=$project 2>/dev/null || echo "No Firestore"
    
done

echo "=== Other Hidden Google Services ==="

# 4. Google Workspace / Gmail / Drive APIs
for project in $(gcloud projects list --format="value(projectId)"); do
    echo "Checking Google Workspace APIs for project: $project"
    
    # Gmail API
    gcloud services list --enabled --project=$project --filter="name:gmail.googleapis.com" --format="value(name)"
    
    # Drive API  
    gcloud services list --enabled --project=$project --filter="name:drive.googleapis.com" --format="value(name)"
    
    # Calendar API
    gcloud services list --enabled --project=$project --filter="name:calendar-json.googleapis.com" --format="value(name)"
    
    # Sheets API
    gcloud services list --enabled --project=$project --filter="name:sheets.googleapis.com" --format="value(name)"
    
    # Analytics
    gcloud services list --enabled --project=$project --filter="name:analytics.googleapis.com" --format="value(name)"
done

echo "=== API Keys and OAuth Clients Discovery ==="

# 5. Find API keys and OAuth configurations
for project in $(gcloud projects list --format="value(projectId)"); do
    echo "API Keys for project: $project"
    gcloud alpha services api-keys list --project=$project 2>/dev/null || echo "No API keys found"
    
    echo "OAuth clients for project: $project"  
    gcloud alpha identity providers list --project=$project 2>/dev/null || echo "No OAuth providers"
done

echo "=== Firebase CLI-based Discovery ==="

# 6. Firebase-specific discovery (requires Firebase CLI installation)
if command -v firebase &> /dev/null; then
    # Login to Firebase (interactive)
    # firebase login
    
    # List all accessible projects
    firebase projects:list
    
    # For each project, get detailed info
    for project in $(firebase projects:list --format=json | jq -r '.[] | .id'); do
        echo "Firebase project: $project"
        
        # Switch to project
        firebase use $project
        
        # List Firebase features
        firebase projects:info
        
        # List hosting sites
        firebase hosting:sites:list 2>/dev/null || echo "No hosting sites"
        
        # List functions
        firebase functions:list 2>/dev/null || echo "No functions"
        
    done
else
    echo "Firebase CLI not installed. Install with: npm install -g firebase-tools"
fi
