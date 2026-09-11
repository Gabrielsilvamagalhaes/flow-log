from fastapi import APIRouter

from flowlog.routes.job_routes import jobs_router


main_router = APIRouter(prefix="/api/v1")

main_router.include_router(jobs_router)
