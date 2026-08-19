from abc import ABC, abstractmethod

class StorageProvider(ABC):
    @abstractmethod
    async def save_file(self, content: bytes, path: str) -> str:
        pass

    @abstractmethod
    async def get_file(self, path: str) -> bytes:
        pass
    
    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        pass
