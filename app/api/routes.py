from __future__ import annotations

from pathlib import Path
import io

from fastapi import APIRouter, File, Query, UploadFile
import pandas as pd

from app.agents.finance_agent import finance_agent
from app.config import config
from app.middleware.error_handler import InvalidCSVError
from app.schemas.requests import ChatRequest
from app.schemas.responses import ChatResponse, GenericDataResponse, HealthResponse
from app.services.container import container


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    container.repository.get_user_by_id(payload.user_id)
    result = finance_agent.chat(user_id=payload.user_id, message=payload.message)
    return ChatResponse(user_id=payload.user_id, answer=result["answer"], analysis=result["analysis"])


@router.get("/users", response_model=GenericDataResponse)
def get_users() -> GenericDataResponse:
    return GenericDataResponse(data=container.repository.get_users())


@router.get("/expenses", response_model=GenericDataResponse)
def get_expenses(
    user_id: int | None = Query(default=None),
    month: str | None = Query(default=None),
) -> GenericDataResponse:
    return GenericDataResponse(data=container.repository.get_expenses(user_id=user_id, month=month))


@router.get("/income", response_model=GenericDataResponse)
def get_income(
    user_id: int | None = Query(default=None),
    month: str | None = Query(default=None),
) -> GenericDataResponse:
    return GenericDataResponse(data=container.repository.get_income(user_id=user_id, month=month))


@router.get("/transactions", response_model=GenericDataResponse)
def get_transactions(
    user_id: int | None = Query(default=None),
    month: str | None = Query(default=None),
    query: str | None = Query(default=None),
) -> GenericDataResponse:
    return GenericDataResponse(
        data=container.repository.get_transactions(user_id=user_id, month=month, query=query)
    )


@router.get("/budgets", response_model=GenericDataResponse)
def get_budgets(
    user_id: int | None = Query(default=None),
    month: str | None = Query(default=None),
) -> GenericDataResponse:
    return GenericDataResponse(data=container.repository.get_budgets(user_id=user_id, month=month))


@router.get("/savings", response_model=GenericDataResponse)
def get_savings(
    user_id: int | None = Query(default=None),
    month: str | None = Query(default=None),
) -> GenericDataResponse:
    return GenericDataResponse(data=container.repository.get_savings(user_id=user_id, month=month))


@router.get("/goals", response_model=GenericDataResponse)
def get_goals(user_id: int | None = Query(default=None)) -> GenericDataResponse:
    return GenericDataResponse(data=container.repository.get_goals(user_id=user_id))


@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), file_type: str = Query(...)) -> dict:
    allowed = {"users", "income", "expenses", "transactions", "budgets", "goals", "investments", "savings"}
    if file_type not in allowed:
        return {"status": "error", "detail": f"file_type must be one of {sorted(allowed)}"}

    save_path = Path(config.storage_dir) / f"{file_type}.csv"
    content = await file.read()
    try:
        pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise InvalidCSVError(f"Uploaded file is not a valid CSV: {exc}") from exc

    save_path.write_bytes(content)
    container.repository._cache.pop(file_type, None)
    container.repository._cache_mtime.pop(file_type, None)

    return {"status": "ok", "path": str(save_path)}


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=config.app_version)
