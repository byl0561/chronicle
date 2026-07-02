from fastapi import APIRouter

from app.api import data, indicators, records, tabs

api_router = APIRouter(prefix="/api")
api_router.include_router(tabs.router)
api_router.include_router(indicators.router)
api_router.include_router(records.router)
api_router.include_router(data.router)
