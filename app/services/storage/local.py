import os
import aiofiles
from .provider import StorageProvider

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_path: str = "uploads/reports"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    async def save_file(self, content: bytes, path: str) -> str:
        full_path = os.path.join(self.base_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(content)
        return full_path

    async def get_file(self, path: str) -> bytes:
        full_path = os.path.join(self.base_path, path)
        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()

    async def delete_file(self, path: str) -> bool:
        full_path = os.path.join(self.base_path, path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False
