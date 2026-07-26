from fastapi import APIRouter

from .routes.analysis import router as analysis_router
from .routes.auth import router as auth_router
from .routes.chat import router as chat_router
from .routes.dashboard import router as dashboard_router
from .routes.health import router as health_router
from .routes.job_analysis import router as job_analysis_router
from .routes.metrics import router as metrics_router
from .routes.resume import router as resume_router
from .routes.resume_tailoring import export_router as export_router
from .routes.resume_tailoring import router as resume_tailoring_router
from .routes.users import router as users_router

router = APIRouter()

router.include_router(chat_router)
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(analysis_router)
router.include_router(job_analysis_router)
router.include_router(dashboard_router)
router.include_router(resume_router)
router.include_router(resume_tailoring_router)
router.include_router(export_router)
router.include_router(users_router)
router.include_router(metrics_router)
