from fastapi import APIRouter

from flowlog.routes.job_routes import jobs_router
from flowlog.routes.redis_routes import redis_router

main_router = APIRouter(prefix="/api/v1")

main_router.include_router(jobs_router)
main_router.include_router(redis_router)
