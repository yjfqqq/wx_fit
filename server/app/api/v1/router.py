from fastapi import APIRouter

from app.api.v1 import auth, export, foods, records, stats, subscribe, summary

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(records.router)
api_router.include_router(foods.router)
api_router.include_router(summary.router)
api_router.include_router(stats.router)
api_router.include_router(export.router)
api_router.include_router(subscribe.router)
