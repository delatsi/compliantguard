#!/bin/bash
# Quick script to sample violations from each source

echo "🔍 Sampling violations from each OPA policy source..."

PROJECT="medtelligence"

echo ""
echo "=== GCP Expanded HIPAA Violations (Sample) ==="
opa eval --input gcp_assets.json --data policies --format json 'data.gcp.expanded_hipaa.violations' | jq -r '.result[0].expressions[0].value | length'
echo "Total GCP violations:"
opa eval --input gcp_assets.json --data policies --format json 'data.gcp.expanded_hipaa.violations' | jq -r '.result[0].expressions[0].value | length'

echo ""
echo "First 3 GCP violations:"
opa eval --input gcp_assets.json --data policies --format json 'data.gcp.expanded_hipaa.violations' | jq -r '.result[0].expressions[0].value[0:3][]' | head -20

echo ""
echo "=== HIPAA Compliance Violations (Sample) ==="
echo "Total HIPAA violations:"
opa eval --input gcp_assets.json --data policies --format json 'data.hipaa.compliance.violations' | jq -r '.result[0].expressions[0].value | length'

echo ""
echo "First 3 HIPAA violations:"
opa eval --input gcp_assets.json --data policies --format json 'data.hipaa.compliance.violations' | jq -r '.result[0].expressions[0].value[0:3][]' | head -20

echo ""
echo "=== Themisguard Framework Violations (Sample) ==="
echo "Total Themisguard violations:"
opa eval --input gcp_assets.json --data policies --format json 'data.themisguard.startup_framework.violations' | jq -r '.result[0].expressions[0].value | length'

echo ""
echo "First 3 Themisguard violations:"
opa eval --input gcp_assets.json --data policies --format json 'data.themisguard.startup_framework.violations' | jq -r '.result[0].expressions[0].value[0:3][]' | head -20

echo ""
echo "=== Asset Type Distribution ==="
echo "What types of assets are being scanned:"
cat gcp_assets.json | jq -r 'group_by(.assetType) | map({type: .[0].assetType, count: length}) | sort_by(.count) | reverse[] | "\(.count) - \(.type)"' | head -10

echo ""
echo "=== Quick Pattern Analysis ==="
echo "Looking for common violation patterns..."

# Check for GKE-related violations
echo "GKE/Kubernetes related violations:"
opa eval --input gcp_assets.json --data policies --format json 'data.gcp.expanded_hipaa.violations' | jq -r '.result[0].expressions[0].value[]' | grep -i -c "gke\|kubernetes\|cluster" 2>/dev/null || echo "0"

# Check for storage violations  
echo "Storage related violations:"
opa eval --input gcp_assets.json --data policies --format json 'data.gcp.expanded_hipaa.violations' | jq -r '.result[0].expressions[0].value[]' | grep -i -c "storage\|bucket" 2>/dev/null || echo "0"

# Check for network violations
echo "Network related violations:"
opa eval --input gcp_assets.json --data policies --format json 'data.gcp.expanded_hipaa.violations' | jq -r '.result[0].expressions[0].value[]' | grep -i -c "network\|firewall\|vpc" 2>/dev/null || echo "0"
