import os
import aiofiles
from typing import BinaryIO
from .storage_provider import StorageProvider
from ..config import settings

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = os.path.join(os.getcwd(), base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_full_path(self, relative_path: str) -> str:
        return os.path.join(self.base_dir, relative_path)

    async def save_file(self, file: BinaryIO, path: str) -> str:
        full_path = self._get_full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        async with aiofiles.open(full_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024): # Read in chunks of 1MB
                await out_file.write(content)
                
        return full_path

    async def get_file(self, path: str) -> bytes:
        full_path = self._get_full_path(path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
            
        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()

    async def delete_file(self, path: str) -> bool:
        full_path = self._get_full_path(path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
