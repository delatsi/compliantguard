#!/usr/bin/env python3

# Test minimal imports to debug the issue
import os
import sys
import json
from datetime import datetime

print("Basic imports successful")

try:
    from core.config import settings
    print("✅ core.config imported successfully")
    print(f"Environment: {settings.ENVIRONMENT}")
except Exception as e:
    print(f"❌ Failed to import core.config: {e}")

try:
    from core.auth import get_current_user
    print("✅ core.auth imported successfully")
except Exception as e:
    print(f"❌ Failed to import core.auth: {e}")

try:
    from routes.auth import router
    print("✅ routes.auth imported successfully")
except Exception as e:
    print(f"❌ Failed to import routes.auth: {e}")

# Simple handler for testing
def handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Test successful"})
    }

if __name__ == "__main__":
    handler({}, {})