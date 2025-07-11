from google.cloud import asset_v1
from google.oauth2 import service_account
from google.protobuf.json_format import MessageToDict
import os
import json

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
CREDS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not PROJECT_ID or not CREDS_PATH:
    raise EnvironmentError("Set GCP_PROJECT_ID and GOOGLE_APPLICATION_CREDENTIALS environment variables.")

credentials = service_account.Credentials.from_service_account_file(CREDS_PATH)
client = asset_v1.AssetServiceClient(credentials=credentials)

scope = f"projects/{PROJECT_ID}"

request = asset_v1.ListAssetsRequest(
    parent=scope,
    content_type=asset_v1.ContentType.RESOURCE,
    page_size=1000,
)

response = client.list_assets(request=request)

# Fix: Use MessageToDict to convert protobuf messages to dictionaries
assets = [MessageToDict(asset._pb) for asset in response]

with open("gcp_assets.json", "w") as f:
    json.dump(assets, f, indent=2)

print(f"✅ Exported {len(assets)} assets to gcp_assets.json")
