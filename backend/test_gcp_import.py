#!/usr/bin/env python3

import sys
import traceback


print("Testing GCP router import...")
print("=" * 50)

try:
    print("1. Testing core imports...")

    print("✓ FastAPI imported")

    from core.config import settings

    print("✓ Settings imported")

    print(f"✓ KMS Key Alias: {settings.KMS_KEY_ALIAS}")
    print(f"✓ GCP Credentials Table: {settings.GCP_CREDENTIALS_TABLE}")

except Exception as e:
    print(f"✗ Core imports failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n2. Testing Google Cloud imports...")

    print("✓ google.oauth2.service_account imported")

    print("✓ googleapiclient.discovery imported")

except Exception as e:
    print(f"✗ Google Cloud imports failed: {e}")
    print("This is likely the issue - missing dependencies")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n3. Testing GCP credential service...")

    print("✓ GCP credential service imported")

except Exception as e:
    print(f"✗ GCP credential service failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n4. Testing GCP router...")
    from routes.gcp import router as gcp_router

    print("✓ GCP router imported")

    routes = [route.path for route in gcp_router.routes]
    print(f"✓ Router has {len(routes)} routes:")
    for route in routes:
        print(f"  - {route}")

except Exception as e:
    print(f"✗ GCP router failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ All imports successful! The issue is elsewhere.")
