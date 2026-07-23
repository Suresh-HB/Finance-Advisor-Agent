from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.utils.logger import logger


class CSVFileMissingError(Exception):
    pass


class InvalidCSVError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class LLMTimeoutError(Exception):
    pass


class FinancialValueError(Exception):
    pass


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CSVFileMissingError)
    async def handle_missing_csv(_: Request, exc: CSVFileMissingError) -> JSONResponse:
        logger.error("Missing CSV: %s", exc)
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InvalidCSVError)
    async def handle_invalid_csv(_: Request, exc: InvalidCSVError) -> JSONResponse:
        logger.error("Invalid CSV: %s", exc)
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(UserNotFoundError)
    async def handle_user_not_found(_: Request, exc: UserNotFoundError) -> JSONResponse:
        logger.error("User not found: %s", exc)
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(LLMTimeoutError)
    async def handle_llm_timeout(_: Request, exc: LLMTimeoutError) -> JSONResponse:
        logger.error("LLM timeout: %s", exc)
        return JSONResponse(status_code=504, content={"detail": str(exc)})

    @app.exception_handler(FinancialValueError)
    async def handle_value_error(_: Request, exc: FinancialValueError) -> JSONResponse:
        logger.error("Financial value error: %s", exc)
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unexpected error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
