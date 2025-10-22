"""
Routes initialization - Organized route modules
"""
from fastapi import APIRouter
from .general import router as general_router
from .articles import router as articles_router
from .parties import router as parties_router
from .figures import router as figures_router
from .scraping import router as scraping_router
from .analysis import router as analysis_router
from .stored_analysis import router as stored_analysis_router
from .debug import router as debug_router

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(general_router, tags=["General"])
router.include_router(articles_router, tags=["Articles"])
router.include_router(parties_router, tags=["Political Parties"])
router.include_router(figures_router, tags=["Figure Profiles"])  # No prefix - direct /party/... access
router.include_router(scraping_router, tags=["Scraping"])
router.include_router(analysis_router, tags=["Analysis"])
router.include_router(stored_analysis_router, tags=["Stored Analysis"])
router.include_router(debug_router, tags=["Debug"])  # Debug endpoints to view stored articles

__all__ = ["router"]
