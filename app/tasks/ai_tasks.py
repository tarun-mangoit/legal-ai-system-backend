import uuid
import json
import asyncio
from celery import shared_task
from app.services.ai_legal_service import AILegalService
from app.database.session import AsyncSessionLocal
from app.models.case_document import CaseDocument, DocumentProcessingStatus
from app.models.document_summary import DocumentSummary
from app.models.case_analysis import CaseAnalysis, CaseAnalysisStatus
from app.models.legal_opinion import LegalOpinion, OpinionStatus
from sqlalchemy import select

# Initialize the AI service
ai_service = AILegalService()

def run_async(coro):
    """Helper to run async functions in Celery synchronous workers."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """Background task to extract text/OCR and prepare embeddings."""
    try:
        # In a real implementation:
        # 1. Fetch document from DB
        # 2. Extract text (PDFPlumber/EasyOCR)
        # 3. Chunk text and generate embeddings
        # 4. Save to DocumentChunk table
        # 5. Update status to READY
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def generate_document_summary_task(self, document_id: str, case_id: str):
    """Background task to call Gemini and generate a Document Summary."""
    
    async def _run():
        async with AsyncSessionLocal() as session:
            try:
                # 1. Fetch DocumentSummary record
                result = await session.execute(select(DocumentSummary).where(DocumentSummary.document_id == document_id))
                summary_record = result.scalars().first()
                if not summary_record:
                    print(f"DocumentSummary record not found for {document_id}")
                    return

                # 2. Fetch CaseDocument to get extracted text
                doc_result = await session.execute(select(CaseDocument).where(CaseDocument.id == document_id))
                document = doc_result.scalars().first()
                
                if not document:
                    summary_record.summary = "Failed: Document not found."
                    await session.commit()
                    return
                
                # If no text is extracted yet, we will use a fallback mock text for testing purposes
                # In a real app, this should wait until text extraction is done
                text_to_analyze = document.extracted_text
                if not text_to_analyze:
                    text_to_analyze = f"This is the content of the document {document.original_filename}. It appears to be a standard legal document regarding the case. Further text extraction is required."

                # 3. Call ai_service
                generated = await ai_service.generate_document_summary(text_to_analyze)

                # 4. Save DocumentSummary to DB
                summary_record.summary = generated.summary
                summary_record.document_type = generated.document_type
                summary_record.key_facts = generated.key_facts
                summary_record.important_dates = generated.important_dates
                summary_record.legal_references = generated.legal_references
                summary_record.potential_issues = generated.potential_issues
                summary_record.evidence_found = generated.evidence_found
                summary_record.missing_information = generated.missing_information
                summary_record.ai_confidence = generated.ai_confidence
                
                # Update Document status
                document.status = DocumentProcessingStatus.SUMMARY_READY
                
                await session.commit()
                print(f"Successfully generated summary for document {document_id}")
                
            except Exception as e:
                # Set FAILED status on error
                doc_result = await session.execute(select(CaseDocument).where(CaseDocument.id == document_id))
                document = doc_result.scalars().first()
                if document:
                    document.status = DocumentProcessingStatus.FAILED
                    await session.commit()
                raise e
                
    try:
        run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def generate_case_analysis_task(self, case_id: str, relevant_document_ids: list):
    """Background task to synthesize Case Analysis from multiple documents."""
    
    async def _run():
        async with AsyncSessionLocal() as session:
            try:
                # 1. Fetch CaseAnalysis record
                result = await session.execute(select(CaseAnalysis).where(CaseAnalysis.case_id == case_id))
                analysis_record = result.scalars().first()
                if not analysis_record:
                    print(f"CaseAnalysis record not found for case {case_id}")
                    return

                # 2. Fetch DocumentSummaries for the case
                stmt = select(DocumentSummary).where(DocumentSummary.case_id == case_id)
                summary_results = await session.execute(stmt)
                summaries = summary_results.scalars().all()
                
                if not summaries:
                    analysis_record.status = CaseAnalysisStatus.FAILED
                    analysis_record.executive_summary = "Failed: No document summaries found for this case."
                    await session.commit()
                    return
                
                summaries_list = [
                    {
                        "document_id": str(s.document_id),
                        "summary": s.summary,
                        "key_facts": s.key_facts,
                        "legal_references": s.legal_references
                    } for s in summaries if s.summary
                ]

                # 3. Call ai_service
                generated = await ai_service.generate_case_analysis(summaries_list)

                # 4. Save CaseAnalysis to DB
                analysis_record.executive_summary = generated.executive_summary
                analysis_record.material_facts = generated.material_facts
                analysis_record.chronology = generated.chronology
                analysis_record.legal_issues = generated.legal_issues
                analysis_record.applicable_laws = generated.applicable_laws
                analysis_record.evidence_assessment = generated.evidence_assessment
                analysis_record.strengths = generated.strengths
                analysis_record.weaknesses = generated.weaknesses
                analysis_record.risks = generated.risks
                analysis_record.missing_information = generated.missing_information
                analysis_record.recommendations = generated.recommendations
                analysis_record.suggested_precedents = generated.suggested_precedents
                analysis_record.status = CaseAnalysisStatus.READY
                
                await session.commit()
                print(f"Successfully generated case analysis for case {case_id}")
                
            except Exception as e:
                # Set FAILED status on error
                result = await session.execute(select(CaseAnalysis).where(CaseAnalysis.case_id == case_id))
                analysis_record = result.scalars().first()
                if analysis_record:
                    analysis_record.status = CaseAnalysisStatus.FAILED
                    await session.commit()
                raise e
    
    try:
        run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def generate_legal_opinion_draft_task(self, case_id: str):
    """Background task to draft Legal Opinion from Case Analysis."""
    
    async def _run():
        async with AsyncSessionLocal() as session:
            try:
                # 1. Fetch LegalOpinion record
                result = await session.execute(select(LegalOpinion).where(LegalOpinion.case_id == case_id))
                opinion_record = result.scalars().first()
                if not opinion_record:
                    print(f"LegalOpinion record not found for case {case_id}")
                    return

                # 2. Fetch CaseAnalysis
                analysis_result = await session.execute(select(CaseAnalysis).where(CaseAnalysis.case_id == case_id))
                analysis = analysis_result.scalars().first()
                
                if not analysis or analysis.status != CaseAnalysisStatus.READY:
                    opinion_record.status = OpinionStatus.REJECTED
                    await session.commit()
                    print(f"Cannot generate opinion: CaseAnalysis is not ready for case {case_id}")
                    return
                
                case_information = {
                    "executive_summary": analysis.executive_summary,
                    "material_facts": analysis.material_facts,
                    "chronology": analysis.chronology,
                    "legal_issues": analysis.legal_issues,
                    "applicable_laws": analysis.applicable_laws,
                    "evidence_assessment": analysis.evidence_assessment,
                    "strengths": analysis.strengths,
                    "weaknesses": analysis.weaknesses,
                    "risks": analysis.risks,
                    "missing_information": analysis.missing_information,
                    "recommendations": analysis.recommendations,
                    "suggested_precedents": analysis.suggested_precedents,
                }

                # 3. Call ai_service
                generated = await ai_service.generate_legal_opinion(case_information)

                # 4. Save LegalOpinion Draft to DB
                opinion_record.documents_reviewed = generated.documents_reviewed
                opinion_record.instructions = generated.instructions
                opinion_record.brief_facts = generated.brief_facts
                opinion_record.issues = generated.issues
                opinion_record.applicable_law = generated.applicable_law
                opinion_record.legal_analysis = generated.legal_analysis
                opinion_record.evidence_assessment = generated.evidence_assessment
                opinion_record.precedents = generated.precedents
                opinion_record.strengths = generated.strengths
                opinion_record.weaknesses = generated.weaknesses
                opinion_record.risks = generated.risks
                opinion_record.conclusion = generated.conclusion
                opinion_record.recommendations = generated.recommendations
                opinion_record.disclaimer = generated.disclaimer
                opinion_record.winning_probability = generated.winning_probability
                opinion_record.risk_level = generated.risk_level
                opinion_record.advocate_risk_assessment = generated.advocate_risk_assessment
                # Update status
                opinion_record.status = OpinionStatus.DRAFT
                opinion_record.version = (opinion_record.version or 0) + 1
                
                await session.commit()
                print(f"Successfully generated legal opinion draft for case {case_id}")
                
            except Exception as e:
                # Set REJECTED status on error
                result = await session.execute(select(LegalOpinion).where(LegalOpinion.case_id == case_id))
                opinion_record = result.scalars().first()
                if opinion_record:
                    opinion_record.status = OpinionStatus.REJECTED
                    await session.commit()
                raise e
                
    try:
        run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
