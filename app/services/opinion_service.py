import uuid
from datetime import datetime
from fastapi import HTTPException
from ..repositories.opinion_repository import LegalOpinionRepository, OpinionRevisionRepository, OpinionCommentRepository
from ..models.legal_opinion import LegalOpinion, OpinionRevision, OpinionComment, OpinionStatus
from ..schemas.legal_opinion import LegalOpinionCreate, LegalOpinionUpdate, OpinionCommentCreate
from app.services.notification_events import notification_events
from app.models.case import Case

class OpinionService:
    def __init__(self, 
                 opinion_repo: LegalOpinionRepository, 
                 revision_repo: OpinionRevisionRepository,
                 comment_repo: OpinionCommentRepository):
        self.opinion_repo = opinion_repo
        self.revision_repo = revision_repo
        self.comment_repo = comment_repo

    async def get_opinion(self, opinion_id: uuid.UUID) -> LegalOpinion:
        opinion = await self.opinion_repo.get_by_id(opinion_id)
        if not opinion:
            raise HTTPException(status_code=404, detail="Opinion not found")
        return opinion

    async def get_all_opinions(self, skip: int = 0, limit: int = 100) -> list[LegalOpinion]:
        return await self.opinion_repo.get_all(skip, limit)

    async def get_opinion_by_case(self, case_id: uuid.UUID) -> LegalOpinion:
        opinion = await self.opinion_repo.get_by_case_id(case_id)
        if not opinion:
            raise HTTPException(status_code=404, detail="Opinion not found for this case")
        return opinion

    async def create_draft(self, data: LegalOpinionCreate, user_id: uuid.UUID) -> LegalOpinion:
        # Check if one already exists
        existing = await self.opinion_repo.get_by_case_id(data.case_id)
        if existing:
            raise HTTPException(status_code=400, detail="Opinion already exists for this case")

        new_opinion = LegalOpinion(
            case_id=data.case_id,
            advocate_id=data.advocate_id or user_id,
            summary=data.summary,
            legal_analysis=data.legal_analysis,
            facts=data.facts,
            issues=data.issues,
            applicable_laws=data.applicable_laws,
            recommendations=data.recommendations,
            winning_probability=data.winning_probability,
            risk_level=data.risk_level,
            status=OpinionStatus.DRAFT
        )
        
        created = await self.opinion_repo.create(new_opinion)
        
        # Create initial revision
        await self._create_revision(created.id, user_id, "Initial Draft")
        
        return await self.get_opinion(created.id)

    async def update_opinion(self, opinion_id: uuid.UUID, data: LegalOpinionUpdate, user_id: uuid.UUID) -> LegalOpinion:
        opinion = await self.get_opinion(opinion_id)
        
        if opinion.is_final:
            raise HTTPException(status_code=400, detail="Cannot edit a finalized opinion")

        update_data = data.model_dump(exclude_unset=True, exclude={"changes_summary"})
        update_data['status'] = OpinionStatus.DRAFT # Reset status if updated
        
        updated = await self.opinion_repo.update(opinion_id, update_data)
        
        # Create revision if explicitly requested via changes_summary or we can just autosave silently.
        # For autosave, we might not want a revision every time, but for this sprint we'll track it if changes_summary is provided.
        summary = data.changes_summary or "Autosaved Draft"
        await self._create_revision(opinion_id, user_id, summary)
        
        return await self.get_opinion(opinion_id)

    async def finalize_opinion(self, opinion_id: uuid.UUID, user_id: uuid.UUID) -> LegalOpinion:
        opinion = await self.get_opinion(opinion_id)
        
        if opinion.is_final:
            raise HTTPException(status_code=400, detail="Opinion is already finalized")
            
        # Validation for required fields before finalization
        required_fields = ['summary', 'legal_analysis', 'facts', 'recommendations', 'winning_probability', 'risk_level']
        for field in required_fields:
            if getattr(opinion, field) is None:
                raise HTTPException(status_code=400, detail=f"Cannot finalize: {field} is required")

        update_data = {
            "status": OpinionStatus.FINALIZED,
            "is_final": True,
            "finalized_at": datetime.utcnow()
        }
        
        updated = await self.opinion_repo.update(opinion_id, update_data)
        await self._create_revision(opinion_id, user_id, "Finalized Opinion")
        
        # Trigger notification
        try:
            from sqlalchemy import select
            result = await self.opinion_repo.session.execute(select(Case).where(Case.id == opinion.case_id))
            case_obj = result.scalars().first()
            if case_obj and case_obj.client_id:
                await notification_events.handle_opinion_finalized(
                    db=self.opinion_repo.session,
                    user_id=str(case_obj.client_id),
                    case_id=str(opinion.case_id),
                    case_number=case_obj.case_number
                )
        except Exception as e:
            import logging
            logging.error(f"Failed to trigger opinion finalized notification: {e}")
            
        return await self.get_opinion(opinion_id)

    async def add_comment(self, opinion_id: uuid.UUID, data: OpinionCommentCreate, user_id: uuid.UUID) -> OpinionComment:
        # Ensure opinion exists
        await self.get_opinion(opinion_id)
        
        comment = OpinionComment(
            opinion_id=opinion_id,
            author_id=user_id,
            comment=data.comment
        )
        return await self.comment_repo.create(comment)
        
    async def _create_revision(self, opinion_id: uuid.UUID, user_id: uuid.UUID, summary: str):
        latest_num = await self.revision_repo.get_latest_revision_number(opinion_id)
        revision = OpinionRevision(
            opinion_id=opinion_id,
            revision_number=latest_num + 1,
            changed_by=user_id,
            changes_summary=summary
        )
        await self.revision_repo.create(revision)
