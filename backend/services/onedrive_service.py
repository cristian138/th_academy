from config import settings
import logging
import aiohttp
import os
from typing import Optional
from azure.identity.aio import ClientSecretCredential

logger = logging.getLogger(__name__)

class OneDriveService:
    def __init__(self):
        if settings.azure_client_id and settings.azure_client_secret and settings.azure_tenant_id:
            self.credential = ClientSecretCredential(
                tenant_id=settings.azure_tenant_id,
                client_id=settings.azure_client_id,
                client_secret=settings.azure_client_secret
            )
            self.enabled = True
        else:
            self.enabled = False
            logger.warning("OneDrive service disabled: Azure credentials not configured")
    
    async def get_access_token(self) -> Optional[str]:
        """Get access token for Microsoft Graph API"""
        if not self.enabled:
            return None
        
        try:
            token = await self.credential.get_token("https://graph.microsoft.com/.default")
            return token.token
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            return None
    
    async def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        folder_path: str = "SportsAdmin"
    ) -> Optional[dict]:
        """Upload file to OneDrive"""
        if not self.enabled:
            logger.info(f"File would be uploaded: {file_name}")
            return {"id": f"mock_{file_name}", "webUrl": "#"}
        
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return None
            
            # Construct upload path
            upload_path = f"/me/drive/root:/{folder_path}/{file_name}:/content"
            upload_url = f"https://graph.microsoft.com/v1.0{upload_path}"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/octet-stream"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.put(upload_url, data=file_content, headers=headers) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        logger.info(f"File uploaded successfully: {file_name}")
                        return result
                    else:
                        logger.error(f"Upload failed with status {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None
    
    async def get_file_url(self, file_id: str) -> Optional[str]:
        """Get download URL for a file"""
        if not self.enabled:
            return f"#mock_url_{file_id}"
        
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return None
            
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("webUrl")
                    return None
        except Exception as e:
            logger.error(f"Error getting file URL: {e}")
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file from OneDrive"""
        if not self.enabled:
            logger.info(f"File would be deleted: {file_id}")
            return True
        
        try:
            access_token = await self.get_access_token()
            if not access_token:
                return False
            
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    return response.status == 204
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

onedrive_service = OneDriveService()
