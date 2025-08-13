from typing import Any, Dict, List

from google.cloud import asset_v1
from google.oauth2 import service_account
from google.protobuf.json_format import MessageToDict

from ..core.config import settings


class GCPAssetService:
    def __init__(self):
        self.credentials = None
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize GCP Asset client with service account credentials"""
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            self.credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            self.client = asset_v1.AssetServiceClient(credentials=self.credentials)

    async def get_project_assets(self, project_id: str) -> Dict[str, Any]:
        """Get all assets for a GCP project"""
        if not self.client:
            raise Exception(
                "GCP client not initialized. Check GOOGLE_APPLICATION_CREDENTIALS."
            )

        scope = f"projects/{project_id}"

        request = asset_v1.ListAssetsRequest(
            parent=scope,
            content_type=asset_v1.ContentType.RESOURCE,
            page_size=1000,
        )

        try:
            response = self.client.list_assets(request=request)

            # Convert protobuf messages to dictionaries
            assets = [MessageToDict(asset._pb) for asset in response]

            return {
                "project_id": project_id,
                "assets": assets,
                "total_count": len(assets),
            }

        except Exception as e:
            raise Exception(f"Failed to get GCP assets: {e}")

    async def get_project_iam_policy(self, project_id: str) -> Dict[str, Any]:
        """Get IAM policy for a GCP project"""
        if not self.client:
            raise Exception("GCP client not initialized.")

        try:
            # This would require additional GCP IAM API calls
            # For now, return empty policy - can be enhanced later
            return {"project_id": project_id, "iam_policy": {}}

        except Exception as e:
            raise Exception(f"Failed to get IAM policy: {e}")

    async def get_project_firewall_rules(self, project_id: str) -> List[Dict[str, Any]]:
        """Get firewall rules for a GCP project"""
        if not self.client:
            raise Exception("GCP client not initialized.")

        # This would require Compute Engine API
        # For now, return empty list - can be enhanced later
        return []

    async def get_project_storage_buckets(
        self, project_id: str
    ) -> List[Dict[str, Any]]:
        """Get storage buckets for a GCP project"""
        if not self.client:
            raise Exception("GCP client not initialized.")

        # This would require Cloud Storage API
        # For now, return empty list - can be enhanced later
        return []
