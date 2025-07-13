import boto3
import json
import base64
import uuid
from datetime import datetime
from typing import Dict, Optional
from botocore.exceptions import ClientError
from fastapi import HTTPException
import structlog

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..core.config import settings

logger = structlog.get_logger()

class GCPCredentialService:
    """Secure GCP credential management with KMS encryption"""
    
    def __init__(self):
        self.kms_client = boto3.client('kms', region_name=settings.AWS_REGION)
        self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        self.creds_table = self.dynamodb.Table('compliantguard-gcp-credentials')
        self.kms_key_alias = 'alias/compliantguard-gcp-credentials'
    
    async def store_credentials(self, user_id: str, project_id: str, 
                              service_account_json: Dict) -> Dict:
        """
        Encrypt and securely store GCP service account credentials
        
        Args:
            user_id: User identifier
            project_id: GCP project ID
            service_account_json: Service account JSON key
            
        Returns:
            Dict with success status and project info
        """
        try:
            logger.info("storing_gcp_credentials", 
                       user_id=user_id, 
                       project_id=project_id,
                       service_account_email=service_account_json.get('client_email'))
            
            # Validate the service account and permissions
            await self._validate_service_account(service_account_json, project_id)
            
            # Encrypt credentials with KMS
            credentials_str = json.dumps(service_account_json)
            try:
                encrypted_response = self.kms_client.encrypt(
                    KeyId=self.kms_key_alias,
                    Plaintext=credentials_str.encode('utf-8')
                )
            except ClientError as e:
                logger.error("kms_encryption_failed", error=str(e))
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to encrypt credentials"
                )
            
            encrypted_blob = base64.b64encode(
                encrypted_response['CiphertextBlob']
            ).decode('utf-8')
            
            # Store in DynamoDB with encryption metadata
            credential_id = str(uuid.uuid4())
            item = {
                'user_id': user_id,
                'project_id': project_id,
                'credential_id': credential_id,
                'encrypted_credentials': encrypted_blob,
                'service_account_email': service_account_json['client_email'],
                'service_account_id': service_account_json.get('client_id', ''),
                'created_at': datetime.utcnow().isoformat(),
                'last_used': datetime.utcnow().isoformat(),
                'status': 'active',
                'encryption_key_id': encrypted_response['KeyId'],
                'metadata': {
                    'project_name': service_account_json.get('project_id', project_id),
                    'key_type': service_account_json.get('type', 'service_account'),
                    'created_by': user_id
                }
            }
            
            # Check if credentials already exist for this project
            try:
                existing = self.creds_table.get_item(
                    Key={'user_id': user_id, 'project_id': project_id}
                )
                if existing.get('Item'):
                    # Update existing credentials
                    logger.info("updating_existing_credentials", 
                               user_id=user_id, 
                               project_id=project_id)
                    item['updated_at'] = datetime.utcnow().isoformat()
            except ClientError:
                pass  # Item doesn't exist, will create new
            
            self.creds_table.put_item(Item=item)
            
            logger.info("gcp_credentials_stored_successfully", 
                       user_id=user_id, 
                       project_id=project_id,
                       credential_id=credential_id)
            
            return {
                "success": True,
                "project_id": project_id,
                "credential_id": credential_id,
                "service_account_email": service_account_json['client_email']
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("credential_storage_failed", 
                        user_id=user_id, 
                        project_id=project_id,
                        error=str(e))
            raise HTTPException(
                status_code=500, 
                detail="Failed to store GCP credentials"
            )
    
    async def get_credentials(self, user_id: str, project_id: str) -> Dict:
        """
        Decrypt and return GCP credentials for scanning
        
        Args:
            user_id: User identifier
            project_id: GCP project ID
            
        Returns:
            Decrypted service account credentials
        """
        try:
            logger.info("retrieving_gcp_credentials", 
                       user_id=user_id, 
                       project_id=project_id)
            
            # Get encrypted credentials from DynamoDB
            response = self.creds_table.get_item(
                Key={'user_id': user_id, 'project_id': project_id}
            )
            
            if 'Item' not in response:
                logger.warning("credentials_not_found", 
                              user_id=user_id, 
                              project_id=project_id)
                raise HTTPException(
                    status_code=404, 
                    detail="GCP credentials not found for this project"
                )
            
            item = response['Item']
            
            # Check credential status
            if item.get('status') != 'active':
                logger.warning("credentials_not_active", 
                              user_id=user_id, 
                              project_id=project_id,
                              status=item.get('status'))
                raise HTTPException(
                    status_code=403, 
                    detail="GCP credentials are not active"
                )
            
            # Decrypt with KMS
            try:
                encrypted_blob = base64.b64decode(item['encrypted_credentials'])
                decrypted_response = self.kms_client.decrypt(
                    CiphertextBlob=encrypted_blob
                )
            except ClientError as e:
                logger.error("kms_decryption_failed", 
                            user_id=user_id, 
                            project_id=project_id,
                            error=str(e))
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to decrypt credentials"
                )
            
            credentials_json = json.loads(
                decrypted_response['Plaintext'].decode('utf-8')
            )
            
            # Update last used timestamp
            self.creds_table.update_item(
                Key={'user_id': user_id, 'project_id': project_id},
                UpdateExpression='SET last_used = :timestamp',
                ExpressionAttributeValues={
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            
            logger.info("gcp_credentials_retrieved_successfully", 
                       user_id=user_id, 
                       project_id=project_id)
            
            return credentials_json
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("credential_retrieval_failed", 
                        user_id=user_id, 
                        project_id=project_id,
                        error=str(e))
            raise HTTPException(
                status_code=500, 
                detail="Failed to retrieve GCP credentials"
            )
    
    async def list_user_projects(self, user_id: str) -> list:
        """List all GCP projects configured for a user"""
        try:
            response = self.creds_table.query(
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id},
                ProjectionExpression='project_id, service_account_email, created_at, last_used, #status',
                ExpressionAttributeNames={'#status': 'status'}
            )
            
            projects = []
            for item in response.get('Items', []):
                projects.append({
                    'project_id': item['project_id'],
                    'service_account_email': item['service_account_email'],
                    'created_at': item['created_at'],
                    'last_used': item.get('last_used'),
                    'status': item.get('status', 'unknown')
                })
            
            return projects
            
        except Exception as e:
            logger.error("list_projects_failed", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=500, 
                detail="Failed to list GCP projects"
            )
    
    async def revoke_credentials(self, user_id: str, project_id: str) -> Dict:
        """Revoke GCP credentials for a project"""
        try:
            logger.info("revoking_gcp_credentials", 
                       user_id=user_id, 
                       project_id=project_id)
            
            # Update status to revoked
            self.creds_table.update_item(
                Key={'user_id': user_id, 'project_id': project_id},
                UpdateExpression='SET #status = :status, revoked_at = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'revoked',
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            
            logger.info("gcp_credentials_revoked", 
                       user_id=user_id, 
                       project_id=project_id)
            
            return {"success": True, "project_id": project_id}
            
        except Exception as e:
            logger.error("credential_revocation_failed", 
                        user_id=user_id, 
                        project_id=project_id,
                        error=str(e))
            raise HTTPException(
                status_code=500, 
                detail="Failed to revoke credentials"
            )
    
    async def _validate_service_account(self, creds: Dict, project_id: str) -> bool:
        """
        Validate service account has required permissions
        
        Args:
            creds: Service account credentials
            project_id: GCP project ID
            
        Returns:
            True if valid
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            logger.info("validating_service_account", 
                       project_id=project_id,
                       service_account_email=creds.get('client_email'))
            
            # Verify the project ID matches
            if creds.get('project_id') != project_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Service account project ({creds.get('project_id')}) doesn't match specified project ({project_id})"
                )
            
            # Create credentials object
            credentials = service_account.Credentials.from_service_account_info(creds)
            
            # Test Cloud Asset API access (primary requirement)
            try:
                service = build('cloudasset', 'v1', credentials=credentials)
                parent = f"projects/{project_id}"
                
                # Test with a small request to verify access
                request = service.assets().list(
                    parent=parent, 
                    pageSize=1,
                    assetTypes=['compute.googleapis.com/Instance']  # Just check VMs
                )
                response = request.execute()
                
                logger.info("service_account_validation_successful", 
                           project_id=project_id,
                           assets_found=len(response.get('assets', [])))
                
            except HttpError as e:
                if e.resp.status == 403:
                    raise HTTPException(
                        status_code=400,
                        detail="Service account lacks required 'Cloud Asset Viewer' permission"
                    )
                elif e.resp.status == 404:
                    raise HTTPException(
                        status_code=400,
                        detail="Project not found or Cloud Asset API not enabled"
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"GCP API error: {e.resp.reason}"
                    )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("service_account_validation_failed", 
                        project_id=project_id,
                        error=str(e))
            raise HTTPException(
                status_code=400,
                detail="Invalid service account credentials"
            )

# Global instance
gcp_credential_service = GCPCredentialService()