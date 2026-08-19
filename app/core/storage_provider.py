from abc import ABC, abstractmethod
from typing import BinaryIO

class StorageProvider(ABC):
    @abstractmethod
    async def save_file(self, file: BinaryIO, path: str) -> str:
        """
        Save a file to the specified path in the storage.
        Returns the absolute storage path.
        """
        pass
    
    @abstractmethod
    async def get_file(self, path: str) -> bytes:
        """
        Retrieve a file from storage as bytes.
        """
        pass
    
    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """
        Delete a file from storage. Returns True if successful.
        """
        pass
