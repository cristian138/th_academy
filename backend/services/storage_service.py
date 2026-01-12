from config import settings
import logging
import os
import uuid
from typing import Optional
import aiofiles

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.storage_type = settings.storage_type
        self.storage_path = settings.storage_path
        
        # Create storage directories if using local storage
        if self.storage_type == "local":
            self._ensure_directories()
    
    def _ensure_directories(self):
        """Create storage directories if they don't exist"""
        directories = [
            os.path.join(self.storage_path, 'contracts'),
            os.path.join(self.storage_path, 'documents'),
            os.path.join(self.storage_path, 'bills'),
            os.path.join(self.storage_path, 'vouchers')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        logger.info(f"Storage directories ensured at {self.storage_path}")
    
    async def upload_file(
        self,
        file_content: bytes,
        file_name: str,
        folder_path: str = "general"
    ) -> Optional[dict]:
        """Upload file to storage"""
        
        if self.storage_type == "local":
            return await self._upload_local(file_content, file_name, folder_path)
        else:
            # Future: implement OneDrive/SharePoint upload
            logger.error("OneDrive storage not yet implemented")
            return None
    
    async def _upload_local(
        self,
        file_content: bytes,
        file_name: str,
        folder_path: str
    ) -> Optional[dict]:
        """Upload file to local storage"""
        try:
            # Map folder paths to local directories
            folder_mapping = {
                "SportsAdmin/Contracts": "contracts",
                "SportsAdmin/Documents": "documents",
                "SportsAdmin/Bills": "bills",
                "SportsAdmin/Vouchers": "vouchers"
            }
            
            local_folder = folder_mapping.get(folder_path, "general")
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file_name)[1]
            stored_filename = f"{file_id}{file_extension}"
            
            file_path = os.path.join(self.storage_path, local_folder, stored_filename)
            
            # Write file asynchronously
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            logger.info(f"File uploaded successfully: {file_path}")
            
            return {
                "id": file_id,
                "name": file_name,
                "path": file_path,
                "webUrl": f"/api/files/{local_folder}/{file_id}{file_extension}"
            }
            
        except Exception as e:
            logger.error(f"Error uploading file to local storage: {e}")
            return None
    
    async def get_file_url(self, file_id: str) -> Optional[str]:
        """Get download URL for a file"""
        # For local storage, return API endpoint
        return f"/api/files/download/{file_id}"
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete file from storage"""
        try:
            # Search for file in all directories
            for directory in ['contracts', 'documents', 'bills', 'vouchers']:
                dir_path = os.path.join(self.storage_path, directory)
                if os.path.exists(dir_path):
                    for filename in os.listdir(dir_path):
                        if filename.startswith(file_id):
                            file_path = os.path.join(dir_path, filename)
                            os.remove(file_path)
                            logger.info(f"File deleted: {file_path}")
                            return True
            
            logger.warning(f"File not found: {file_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    async def get_file_path(self, file_id: str) -> Optional[str]:
        """Get file path for a file ID"""
        try:
            for directory in ['contracts', 'documents', 'bills', 'vouchers']:
                dir_path = os.path.join(self.storage_path, directory)
                if os.path.exists(dir_path):
                    for filename in os.listdir(dir_path):
                        if filename.startswith(file_id):
                            return os.path.join(dir_path, filename)
            return None
        except Exception as e:
            logger.error(f"Error getting file path: {e}")
            return None

storage_service = StorageService()
