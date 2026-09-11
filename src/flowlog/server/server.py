from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from flowlog.routes.error_routes import register_exception_handlers
from flowlog.routes.main_routes import main_router
from flowlog.server.database.connection import create_db_and_tables

# Init database
create_db_and_tables()

server = FastAPI()

server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(server)
server.include_router(main_router)
