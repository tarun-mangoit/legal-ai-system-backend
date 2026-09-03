from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.case import Case
from app.schemas.ai_chat import (
    CaseChatRequest, CaseChatResponse, 
    DocumentChatRequest, DocumentChatResponse,
    AIConversationResponse
)
from app.services.case_ai_chat_service import CaseAIChatService
from app.services.document_ai_chat_service import DocumentAIChatService
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter()

async def check_case_access(db: Session, case_id: UUID, current_user: User):
    from app.models.role import Role
    role = await db.get(Role, current_user.role_id)
    role_name = role.name if role else None
    
    if role_name not in ["admin", "advocate"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use AI chat")
    
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalars().first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        
    if role_name == "advocate" and case.advocate_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this case")
    
    return case

@router.post("/cases/{case_id}/ai/chat", response_model=CaseChatResponse)
async def chat_with_case(
    case_id: UUID, 
    request: CaseChatRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    await check_case_access(db, case_id, current_user)
    
    service = CaseAIChatService(db)
    try:
        conv_id, msg_id, answer, sources = await service.process_message(
            case_id=case_id,
            user_id=current_user.id,
            message=request.message,
            conversation_id=request.conversation_id
        )
        return CaseChatResponse(
            conversation_id=conv_id,
            message_id=msg_id,
            answer=answer,
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/cases/{case_id}/documents/ai/chat", response_model=DocumentChatResponse)
async def chat_with_documents(
    case_id: UUID, 
    request: DocumentChatRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    await check_case_access(db, case_id, current_user)
    
    if not request.document_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No documents selected for chat")
        
    service = DocumentAIChatService(db)
    try:
        conv_id, msg_id, answer, sources = await service.process_message(
            case_id=case_id,
            user_id=current_user.id,
            message=request.message,
            document_ids=request.document_ids,
            conversation_id=request.conversation_id
        )
        return DocumentChatResponse(
            conversation_id=conv_id,
            message_id=msg_id,
            answer=answer,
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/cases/{case_id}/ai/conversations", response_model=List[AIConversationResponse])
async def get_conversations(
    case_id: UUID, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    await check_case_access(db, case_id, current_user)
    from app.models.ai_conversation import AIConversation
    result = await db.execute(
        select(AIConversation)
        .options(selectinload(AIConversation.messages))
        .where(AIConversation.case_id == case_id, AIConversation.user_id == current_user.id)
    )
    conversations = result.scalars().unique().all()
    return conversations
