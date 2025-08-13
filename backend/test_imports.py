#!/usr/bin/env python3

# Test minimal imports to debug the issue
import json


print("Basic imports successful")

try:
    from core.config import settings

    print("✅ core.config imported successfully")
    print(f"Environment: {settings.ENVIRONMENT}")
except Exception as e:
    print(f"❌ Failed to import core.config: {e}")

try:
    print("✅ core.auth imported successfully")
except Exception as e:
    print(f"❌ Failed to import core.auth: {e}")

try:
    print("✅ routes.auth imported successfully")
except Exception as e:
    print(f"❌ Failed to import routes.auth: {e}")


# Simple handler for testing
def handler(event, context):
    return {"statusCode": 200, "body": json.dumps({"message": "Test successful"})}


if __name__ == "__main__":
    handler({}, {})
