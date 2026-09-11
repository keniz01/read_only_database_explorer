import logging

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from config.app_logger import logger
from exceptions.sql_statement_execution_exception import SqlStatementExecutionError


def raise_sql_execution_exception(
    message: str, error: Exception, include_traceback: bool = False
) -> None:
    """
    Raise a SqlStatementExecutionError with a formatted error message.

    Args:
        message: Contextual message about the error.
        error: The caught exception.
        include_traceback: If True, appends the full traceback to the message.

    """
    root_cause = error.__cause__ or error
    formatted_message = f"""
[SqlStatementExecutionError]
{message}
↳ Caused by {type(root_cause).__name__}: {root_cause}
""".strip()

    logging.error(message, exc_info=True)
    raise SqlStatementExecutionError(formatted_message) from error


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Translate an HTTP exception into a structured JSON error response."""
    logger.warning(f"⚠️ HTTPException: {exc.detail} | Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "path": request.url.path,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Translate a request validation error into a structured JSON response."""
    logger.error(f"🛑 ValidationError at {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors(),
            "path": request.url.path,
        },
    )
