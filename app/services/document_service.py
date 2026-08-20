import os
import uuid
import hashlib
from fastapi import UploadFile, HTTPException
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.case_document import DocumentCategory
from ..models.user import User
from ..models.case import Case
from ..repositories.document_repository import DocumentRepository
from ..core.storage_provider import StorageProvider
from app.services.notification_events import notification_events

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
    "image/png": ".png",
    "image/jpeg": ".jpg",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

class DocumentService:
    def __init__(self, document_repository: DocumentRepository, storage_provider: StorageProvider):
        self.repository = document_repository
        self.storage = storage_provider

    async def _get_user_role(self, user: User) -> str:
        from ..models.role import Role
        role = await self.repository.session.get(Role, user.role_id)
        return role.name if role else "unknown"

    async def _calculate_hash(self, file: UploadFile) -> str:
        sha256_hash = hashlib.sha256()
        # Read file in chunks to avoid high memory consumption
        await file.seek(0)
        while chunk := await file.read(8192):
            sha256_hash.update(chunk)
        await file.seek(0)
        return sha256_hash.hexdigest()

    async def upload_document(self, case_id: uuid.UUID, user: User, file: UploadFile, category: DocumentCategory, remarks: Optional[str] = None) -> dict:
        # Validate file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        await file.seek(0)
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file not allowed")
            
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File exceeds maximum size of {MAX_FILE_SIZE/(1024*1024)}MB")

        # Validate MIME type and Extension
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail="File type not supported")
            
        extension = ALLOWED_MIME_TYPES[file.content_type]
        
        # Calculate hash and check for duplicates
        file_hash = await self._calculate_hash(file)
        existing_doc = await self.repository.find_by_hash(case_id, file_hash)
        
        if existing_doc:
            raise HTTPException(status_code=409, detail="Duplicate file exists for this case")

        # Generate paths and names
        stored_filename = f"{uuid.uuid4()}{extension}"
        now = datetime.utcnow()
        path = f"{now.year}/{now.month:02d}/case_{case_id}/{stored_filename}"

        # Save file to storage
        storage_path = await self.storage.save_file(file, path)

        # Save to database
        document_data = {
            "case_id": case_id,
            "uploaded_by": user.id,
            "category": category,
            "original_filename": file.filename,
            "stored_filename": stored_filename,
            "mime_type": file.content_type,
            "extension": extension,
            "file_size": file_size,
            "storage_path": storage_path,
            "sha256_hash": file_hash,
            "remarks": remarks
        }
        
        document = await self.repository.create(document_data)
        
        # Load the case to get the client/advocate IDs for notification
        # This assumes self.repository.session is available or we can query it
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        result = await self.repository.session.execute(
            select(Case).options(selectinload(Case.client), selectinload(Case.advocate)).filter(Case.id == case_id)
        )
        case_obj = result.scalars().first()
        
        if case_obj:
            notify_id = None
            if user.id == case_obj.client_id and case_obj.advocate_id:
                notify_id = case_obj.advocate_id
            elif user.id == case_obj.advocate_id and case_obj.client_id:
                notify_id = case_obj.client_id
                
            if notify_id:
                await notification_events.handle_document_uploaded(
                    db=self.repository.session,
                    case_id=str(case_id),
                    case_number=case_obj.case_number,
                    uploader_name=f"{user.first_name} {user.last_name}",
                    document_name=file.filename,
                    notify_user_id=str(notify_id)
                )

        # Note: AI Processing must now be triggered manually via the API
        
        return document

    async def get_document(self, document_id: uuid.UUID, user: User) -> dict:
        document = await self.repository.get_by_id(document_id)
        if not document or document.is_deleted:
            raise HTTPException(status_code=404, detail="Document not found")
            
        role_name = await self._get_user_role(user)
        # Role-based access check
        if role_name == "client" and document.case.client_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this document")
        elif role_name == "advocate" and document.case.advocate_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to access this document")
            
        return document

    async def download_document(self, document_id: uuid.UUID, user: User) -> tuple:
        document = await self.get_document(document_id, user)
        try:
            file_bytes = await self.storage.get_file(document.storage_path)
        except FileNotFoundError:
             raise HTTPException(status_code=404, detail="File physically not found on server")
        return file_bytes, document.original_filename, document.mime_type

    async def list_case_documents(self, case_id: uuid.UUID, user: User, skip: int = 0, limit: int = 100) -> List[dict]:
        # Would typically need to verify case access here too
        # Simplifying for now assuming the endpoint handles basic case validation
        return await self.repository.list_by_case(case_id, skip, limit)

    async def get_all_documents(self, user: User, skip: int = 0, limit: int = 100) -> List[dict]:
        role_name = await self._get_user_role(user)
        if role_name not in ["admin", "advocate", "client"]:
            raise HTTPException(status_code=403, detail="Not authorized to view all documents")
            
        advocate_id = user.id if role_name == "advocate" else None
        client_id = user.id if role_name == "client" else None
        results = await self.repository.get_all_documents_with_status(skip, limit, advocate_id, client_id)
        docs = []
        for doc, ai_status in results:
            doc_dict = doc.__dict__.copy()
            doc_dict["ai_status"] = ai_status if ai_status else "NONE"
            if doc.case:
                if doc.case.client:
                    doc_dict["client_name"] = f"{doc.case.client.first_name or ''} {doc.case.client.last_name or ''}".strip()
                    doc_dict["client_id"] = doc.case.client.id
                if doc.case.advocate:
                    doc_dict["advocate_name"] = f"{doc.case.advocate.first_name or ''} {doc.case.advocate.last_name or ''}".strip()
                    doc_dict["advocate_id"] = doc.case.advocate.id
            docs.append(doc_dict)
        return docs

    async def delete_document(self, document_id: uuid.UUID, user: User) -> bool:
        document = await self.get_document(document_id, user)
        role_name = await self._get_user_role(user)
        
        # Check if user can delete (Admin, or uploader)
        if role_name != "admin" and document.uploaded_by != user.id:
             raise HTTPException(status_code=403, detail="Not authorized to delete this document")
             
        success = await self.repository.delete(document_id)
        return success

    async def restore_document(self, document_id: uuid.UUID, user: User) -> bool:
         role_name = await self._get_user_role(user)
         
         # Simplified: only admin can restore
         if role_name != "admin":
              raise HTTPException(status_code=403, detail="Not authorized to restore documents")
              
         success = await self.repository.restore(document_id)
         if not success:
             raise HTTPException(status_code=404, detail="Document not found or not deleted")
         return success
