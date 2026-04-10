"""Global exception handlers for FastAPI — consistent JSON error responses."""

import logging
import traceback

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions with consistent JSON format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors with readable format."""
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(part) for part in err.get("loc", []))
            errors.append({
                "field": loc,
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            })

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "status_code": 422,
                "detail": "Error de validacion en los datos enviados.",
                "errors": errors,
                "path": str(request.url.path),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """
        Catch-all for unhandled exceptions.

        Prevents raw 500 HTML pages from leaking to clients.
        Logs full traceback for debugging, returns safe JSON to client.
        """
        logger.error(
            "Unhandled exception on %s %s: %s\n%s",
            request.method,
            request.url.path,
            str(exc),
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "status_code": 500,
                "detail": "Error interno del servidor. Por favor intente nuevamente.",
                "path": str(request.url.path),
            },
        )
