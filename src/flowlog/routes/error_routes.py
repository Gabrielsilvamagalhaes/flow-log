from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(404)
    async def not_found_handler(req: Request, exception):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": str(exception.detail) or "Recurso não encontrado",
            },
        )

    @app.exception_handler(400)
    async def bad_reqeuest_handler(req: Request, exception):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad Request",
                "message": str(exception.detail) or "Error de validação",
            },
        )
