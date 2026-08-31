import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import NotificationChannel, NotificationCategory
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class NotificationEventHandler:
    """Handles business events and triggers appropriate notifications."""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service

    def _get_case_url(self, case_id: str = None) -> str:
        return f"/cases/{case_id}" if case_id else "/cases"

    async def handle_user_registered(self, db: AsyncSession, user_id: str, email: str, name: str):
        logger.info(f"Event: UserRegistered for user {user_id}")
        await self.notification_service.send_templated_notification(
            db=db,
            user_id=user_id,
            channel=NotificationChannel.EMAIL,
            template_name="Welcome Email",
            context={"name": name, "email": email},
            priority=1
        )
        
    async def handle_case_created(self, db: AsyncSession, user_id: str, case_number: str, title: str):
        logger.info(f"Event: CaseCreated for case {case_number}")
        # Notify via In-App
        await self.notification_service.send_notification(
            db=db,
            user_id=user_id,
            channel=NotificationChannel.IN_APP,
            title="Case Created Successfully",
            message=f"Your case '{title}' ({case_number}) has been created.",
            priority=0,
            category=NotificationCategory.CASE,
            action_url=self._get_case_url(case_number)
        )
        # Notify via Email
        await self.notification_service.send_templated_notification(
            db=db,
            user_id=user_id,
            channel=NotificationChannel.EMAIL,
            template_name="Case Created",
            context={"case_number": case_number, "title": title},
            priority=0,
            category=NotificationCategory.CASE
        )
        
        # Notify Admins
        await self.notification_service.notify_admins(
            db=db,
            title="New Case Submitted",
            message=f"A new case '{title}' ({case_number}) has been submitted and requires review.",
            priority=1,
            channel=NotificationChannel.IN_APP,
            category=NotificationCategory.CASE,
            action_url="/admin/cases"
        )
        await self.notification_service.notify_admins(
            db=db,
            title="New Case Submitted",
            message=f"A new case '{title}' ({case_number}) has been submitted and requires review.",
            priority=1,
            channel=NotificationChannel.EMAIL,
            category=NotificationCategory.CASE,
            action_url="/admin/cases"
        )

    async def handle_document_uploaded(self, db: AsyncSession, case_id: str, case_number: str, uploader_name: str, document_name: str, notify_user_id: str):
        logger.info(f"Event: DocumentUploaded for case {case_number}")
        await self.notification_service.send_notification(
            db=db,
            user_id=notify_user_id,
            channel=NotificationChannel.IN_APP,
            title="New Document Uploaded",
            message=f"{uploader_name} uploaded '{document_name}' to case {case_number}.",
            priority=0,
            category=NotificationCategory.DOCUMENT,
            action_url=f"/cases/{case_id}/documents"
        )
        await self.notification_service.send_templated_notification(
            db=db,
            user_id=notify_user_id,
            channel=NotificationChannel.EMAIL,
            template_name="Document Uploaded",
            context={"case_number": case_number, "uploader_name": uploader_name, "document_name": document_name},
            priority=0,
            category=NotificationCategory.DOCUMENT
        )

    async def handle_payment_required(self, db: AsyncSession, user_id: str, case_id: str, case_number: str, title: str, amount: float):
        logger.info(f"Event: PaymentRequired for case {case_number}")
        # Notify via In-App
        await self.notification_service.send_notification(
            db=db,
            user_id=user_id,
            channel=NotificationChannel.IN_APP,
            title="Payment Required",
            message=f"Your case '{title}' ({case_number}) has been reviewed. A fee of ₹{amount:,.2f} is required to proceed.",
            priority=1,
            category=NotificationCategory.SYSTEM,
            action_url=self._get_case_url(case_id)
        )
        # Notify via Email
        await self.notification_service.send_templated_notification(
            db=db,
            user_id=user_id,
            channel=NotificationChannel.EMAIL,
            template_name="Payment Required",
            context={"case_number": case_number, "title": title, "amount": f"₹{amount:,.2f}"},
            priority=1,
            category=NotificationCategory.SYSTEM
        )

    async def handle_payment_success(self, db: AsyncSession, user_id: str, amount: float, reference: str, case_number: str = None):
        logger.info(f"Event: PaymentSuccess for ref {reference}")
        
        context = {"payment_amount": str(amount), "reference": reference}
        if case_number:
            context["case_number"] = case_number
            
        await self.notification_service.send_templated_notification(
            db=db,
            user_id=user_id,
            channel=NotificationChannel.EMAIL,
            template_name="Payment Success",
            context=context,
            priority=2
        )
        
        client_msg = f"We have received your payment of ${amount}."
        if case_number:
            client_msg = f"We have received your payment of ${amount} for case {case_number}."
            
        await self.notification_service.send_notification(
            db=db,
            user_id=user_id,
            channel=NotificationChannel.IN_APP,
            title="Payment Successful",
            message=client_msg,
            priority=2
        )
        
        admin_msg = f"A payment of ${amount} (Ref: {reference}) has been successfully received."
        if case_number:
            admin_msg = f"A payment of ${amount} (Ref: {reference}) has been successfully received for case {case_number}."
            
        # Notify Admins
        await self.notification_service.notify_admins(
            db=db,
            title="Payment Received",
            message=admin_msg,
            priority=2,
            channel=NotificationChannel.IN_APP,
            category=NotificationCategory.PAYMENT,
            action_url="/admin/payments"
        )
        await self.notification_service.notify_admins(
            db=db,
            title="Payment Received",
            message=admin_msg,
            priority=2,
            channel=NotificationChannel.EMAIL,
            category=NotificationCategory.PAYMENT,
            action_url="/admin/payments"
        )

    async def handle_report_generated(self, db: AsyncSession, user_id: str, report_name: str, case_number: str):
        logger.info(f"Event: ReportGenerated for {report_name}")
        await self.notification_service.send_templated_notification(
            db=db,
            user_id=user_id,
            channel=NotificationChannel.EMAIL,
            template_name="Report Ready",
            context={"report_name": report_name, "case_number": case_number},
            priority=1
        )
        await self.notification_service.send_notification(
            db=db,
            user_id=user_id,
            channel=NotificationChannel.IN_APP,
            title="Report Ready",
            message=f"Your legal report '{report_name}' is ready to view.",
            priority=1,
            category=NotificationCategory.REPORT,
            action_url=f"/cases/{case_number}/report"
        )

    async def handle_password_reset(self, db: AsyncSession, user_id: str, email: str, reset_link: str):
        logger.info(f"Event: PasswordReset for {email}")
        await self.notification_service.send_templated_notification(
            db=db,
            user_id=user_id,
            channel=NotificationChannel.EMAIL,
            template_name="Password Reset",
            context={"reset_link": reset_link},
            priority=2,
            category=NotificationCategory.AUTHENTICATION
        )

    async def handle_case_assigned(self, db: AsyncSession, case_id: str, case_number: str, advocate_id: str, advocate_name: str, client_id: str):
        logger.info(f"Event: CaseAssigned for {case_number}")
        # Notify Advocate
        await self.notification_service.send_notification(
            db=db, user_id=advocate_id, channel=NotificationChannel.IN_APP,
            title="New Case Assigned", message=f"You have been assigned to case {case_number}.",
            priority=1, category=NotificationCategory.CASE, action_url=self._get_case_url(case_id)
        )
        await self.notification_service.send_templated_notification(
            db=db, user_id=advocate_id, channel=NotificationChannel.EMAIL,
            template_name="Case Assigned", context={"case_number": case_number, "role": "Advocate"},
            priority=1, category=NotificationCategory.CASE
        )
        # Notify Client
        await self.notification_service.send_notification(
            db=db, user_id=client_id, channel=NotificationChannel.IN_APP,
            title="Advocate Assigned", message=f"{advocate_name} has been assigned to your case {case_number}.",
            priority=1, category=NotificationCategory.CASE, action_url=self._get_case_url(case_id)
        )
        await self.notification_service.send_templated_notification(
            db=db, user_id=client_id, channel=NotificationChannel.EMAIL,
            template_name="Case Assigned", context={"case_number": case_number, "role": "Client", "advocate_name": advocate_name},
            priority=1, category=NotificationCategory.CASE
        )

    async def handle_ai_processing_completed(self, db: AsyncSession, user_id: str, case_id: str, case_number: str):
        logger.info(f"Event: AIProcessingCompleted for {case_number}")
        await self.notification_service.send_notification(
            db=db, user_id=user_id, channel=NotificationChannel.IN_APP,
            title="Analysis Complete", message=f"Analysis finished for case {case_number}.",
            priority=0, category=NotificationCategory.AI, action_url=self._get_case_url(case_id)
        )

    async def handle_opinion_finalized(self, db: AsyncSession, user_id: str, case_id: str, case_number: str):
        logger.info(f"Event: OpinionFinalized for {case_number}")
        await self.notification_service.send_notification(
            db=db, user_id=user_id, channel=NotificationChannel.IN_APP,
            title="Legal Opinion Finalized", message=f"The legal opinion for {case_number} is ready.",
            priority=1, category=NotificationCategory.LEGAL_OPINION, action_url=self._get_case_url(case_id)
        )

    async def handle_payment_failed(self, db: AsyncSession, user_id: str, amount: float, reason: str):
        logger.info(f"Event: PaymentFailed for user {user_id}")
        await self.notification_service.send_notification(
            db=db, user_id=user_id, channel=NotificationChannel.IN_APP,
            title="Payment Failed", message=f"Your payment of ${amount} failed: {reason}",
            priority=2, category=NotificationCategory.PAYMENT, action_url="/client/payments"
        )

    async def handle_refund_processed(self, db: AsyncSession, user_id: str, amount: float):
        logger.info(f"Event: RefundProcessed for user {user_id}")
        await self.notification_service.send_notification(
            db=db, user_id=user_id, channel=NotificationChannel.IN_APP,
            title="Refund Processed", message=f"A refund of ${amount} has been processed to your account.",
            priority=1, category=NotificationCategory.PAYMENT, action_url="/client/payments"
        )

# Global Instance
from app.services.notification_service import NotificationService, TemplateService
from app.repositories.notification_repository import NotificationRepository, NotificationPreferenceRepository, NotificationTemplateRepository
notification_service = NotificationService(NotificationRepository(), NotificationPreferenceRepository(), TemplateService(NotificationTemplateRepository()))
notification_events = NotificationEventHandler(notification_service)
