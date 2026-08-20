from fastapi import APIRouter

from .endpoints.auth import router as auth_router
from .endpoints.admin import router as admin_router
# from .users.router import router as users_router
from .endpoints.clients import router as clients_router
from .endpoints.advocates import router as advocates_router
from .endpoints.dashboard import router as dashboard_router
from .endpoints.cases import router as cases_router
from .endpoints.documents import router as documents_router
from .endpoints.document_processing import router as document_processing_router
from .endpoints.opinions import router as opinions_router
# from .ai.router import router as ai_router
from .endpoints.reports import router as reports_router
from .endpoints.citations import router as citations_router
from .endpoints.payments import router as payments_router
from .endpoints.notifications import router as notifications_router
from .endpoints.notification_templates import router as notification_templates_router
from .endpoints.messages import router as messages_router
from .endpoints.blogs import router as blogs_router
from .endpoints.pages import router as pages_router
from .testimonials.router import router as testimonials_router
from .endpoints.contact import router as contact_router
from .endpoints.services import router as services_router
from .endpoints.practice_areas import router as practice_areas_router
from .endpoints.hero_sliders import router as hero_sliders_router
from .endpoints.settings import router as settings_router
from .endpoints.section_content import router as section_content_router
from .endpoints.seo import router as seo_router
api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
# api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(clients_router, prefix="/clients", tags=["Clients"])
api_router.include_router(advocates_router, prefix="/advocates", tags=["Advocates"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(cases_router, prefix="/cases", tags=["Cases"])
api_router.include_router(messages_router, prefix="/cases", tags=["Messages"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(document_processing_router, prefix="/document-processing", tags=["Document Processing"])
api_router.include_router(opinions_router, prefix="/opinions", tags=["Opinions"])
# api_router.include_router(ai_router, prefix="/cases/{case_id}/ai", tags=["AI"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(citations_router, prefix="/citations", tags=["Citations"])
api_router.include_router(payments_router, prefix="/payments", tags=["Payments"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(notification_templates_router, prefix="/notification-templates", tags=["Notification Templates"])
api_router.include_router(blogs_router, prefix="/blogs", tags=["Blogs"])
api_router.include_router(pages_router, prefix="/pages", tags=["Pages"])
api_router.include_router(testimonials_router, prefix="/testimonials", tags=["Testimonials"])
from .public_cases.router import router as public_cases_router
api_router.include_router(public_cases_router, prefix="/public-cases", tags=["Public Cases"])
api_router.include_router(contact_router, prefix="/contact", tags=["Contact"])
api_router.include_router(settings_router, prefix="/settings", tags=["Settings"])
api_router.include_router(services_router, prefix="/services", tags=["Services"])
api_router.include_router(practice_areas_router, prefix="/practice-areas", tags=["Practice Areas"])
api_router.include_router(hero_sliders_router, prefix="/hero-sliders", tags=["Hero Sliders"])
api_router.include_router(section_content_router, prefix="/section-content", tags=["Section Content"])
api_router.include_router(seo_router, prefix="/seo", tags=["SEO"])
