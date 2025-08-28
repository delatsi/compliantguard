#!/bin/bash

# Generate deployment information with git hash, timestamp, and build info
# Usage: ./scripts/generate-deployment-info.sh [environment]

ENVIRONMENT=${1:-"local"}
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_HASH=$(git rev-parse HEAD)
GIT_SHORT_HASH=$(git rev-parse --short HEAD)
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
GIT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "")

echo "🚀 Generating deployment info for environment: $ENVIRONMENT"

# Generate frontend version info
cat > frontend/public/deployment-info.json << EOF
{
  "environment": "$ENVIRONMENT",
  "timestamp": "$TIMESTAMP",
  "git": {
    "hash": "$GIT_HASH",
    "shortHash": "$GIT_SHORT_HASH",
    "branch": "$GIT_BRANCH",
    "tag": "$GIT_TAG"
  },
  "build": {
    "node_version": "$(node --version)",
    "npm_version": "$(npm --version)"
  }
}
EOF

# Generate backend version info
cat > backend/deployment-info.json << EOF
{
  "environment": "$ENVIRONMENT",
  "timestamp": "$TIMESTAMP",
  "git": {
    "hash": "$GIT_HASH",
    "shortHash": "$GIT_SHORT_HASH",
    "branch": "$GIT_BRANCH",
    "tag": "$GIT_TAG"
  },
  "build": {
    "python_version": "$(python --version 2>&1)",
    "requirements_hash": "$(cd backend && python -c "import hashlib; print(hashlib.md5(open('requirements.txt').read().encode()).hexdigest())" 2>/dev/null || echo 'unknown')"
  }
}
EOF

echo "✅ Generated deployment info:"
echo "   - Environment: $ENVIRONMENT"
echo "   - Git Hash: $GIT_SHORT_HASH"
echo "   - Branch: $GIT_BRANCH"
echo "   - Timestamp: $TIMESTAMP"