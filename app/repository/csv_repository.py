from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.config import config
from app.middleware.error_handler import CSVFileMissingError, InvalidCSVError, UserNotFoundError
from app.utils.logger import logger
from app.utils.validators import ensure_non_negative, ensure_required_columns


class CSVRepository:
    def __init__(self, storage_dir: Path | None = None) -> None:
        self.storage_dir = Path(storage_dir or config.storage_dir)
        self._cache: dict[str, pd.DataFrame] = {}
        self._cache_mtime: dict[str, float] = {}

    def _file_path(self, table: str) -> Path:
        return self.storage_dir / f"{table}.csv"

    def _load_csv(self, table: str) -> pd.DataFrame:
        path = self._file_path(table)
        if not path.exists():
            raise CSVFileMissingError(f"CSV file not found: {path}")

        mtime = path.stat().st_mtime
        if table in self._cache and self._cache_mtime.get(table) == mtime:
            return self._cache[table]

        try:
            df = pd.read_csv(path)
        except Exception as exc:
            raise InvalidCSVError(f"Unable to load CSV {table}: {exc}") from exc

        self._cache[table] = df
        self._cache_mtime[table] = mtime
        return df

    def _filter_month(self, df: pd.DataFrame, date_column: str, month: str | None) -> pd.DataFrame:
        if not month:
            return df.copy()
        working = df.copy()
        working[date_column] = pd.to_datetime(working[date_column], errors="coerce")
        return working[working[date_column].dt.strftime("%Y-%m") == month]

    def _as_records(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        return df.fillna("").to_dict(orient="records")

    def get_users(self) -> list[dict[str, Any]]:
        df = self._load_csv("users")
        ensure_required_columns(df, ["user_id", "name"], "users")
        return self._as_records(df)

    def get_user_by_id(self, user_id: int) -> dict[str, Any]:
        df = self._load_csv("users")
        match = df[df["user_id"] == user_id]
        if match.empty:
            raise UserNotFoundError(f"User ID {user_id} not found")
        return self._as_records(match)[0]

    def get_income(self, user_id: int | None = None, month: str | None = None) -> list[dict[str, Any]]:
        df = self._load_csv("income")
        ensure_required_columns(df, ["user_id", "date", "amount"], "income")
        ensure_non_negative(df["amount"], "income.amount")
        if user_id is not None:
            df = df[df["user_id"] == user_id]
        df = self._filter_month(df, "date", month)
        return self._as_records(df)

    def get_expenses(self, user_id: int | None = None, month: str | None = None) -> list[dict[str, Any]]:
        df = self._load_csv("expenses")
        ensure_required_columns(df, ["user_id", "date", "category", "amount"], "expenses")
        ensure_non_negative(df["amount"], "expenses.amount")
        if user_id is not None:
            df = df[df["user_id"] == user_id]
        df = self._filter_month(df, "date", month)
        return self._as_records(df)

    def get_transactions(
        self,
        user_id: int | None = None,
        month: str | None = None,
        query: str | None = None,
    ) -> list[dict[str, Any]]:
        df = self._load_csv("transactions")
        ensure_required_columns(
            df,
            ["user_id", "date", "type", "category", "description", "amount"],
            "transactions",
        )
        ensure_non_negative(df["amount"], "transactions.amount")
        if user_id is not None:
            df = df[df["user_id"] == user_id]
        df = self._filter_month(df, "date", month)
        if query:
            q = query.lower().strip()
            df = df[
                df["category"].astype(str).str.lower().str.contains(q)
                | df["description"].astype(str).str.lower().str.contains(q)
            ]
        return self._as_records(df)

    def get_budgets(self, user_id: int | None = None, month: str | None = None) -> list[dict[str, Any]]:
        df = self._load_csv("budgets")
        ensure_required_columns(df, ["user_id", "month", "budget_limit"], "budgets")
        ensure_non_negative(df["budget_limit"], "budgets.budget_limit")
        if user_id is not None:
            df = df[df["user_id"] == user_id]
        if month:
            df = df[df["month"] == month]
        return self._as_records(df)

    def get_savings(self, user_id: int | None = None, month: str | None = None) -> list[dict[str, Any]]:
        df = self._load_csv("savings")
        ensure_required_columns(df, ["user_id", "month", "amount"], "savings")
        ensure_non_negative(df["amount"], "savings.amount")
        if user_id is not None:
            df = df[df["user_id"] == user_id]
        if month:
            df = df[df["month"] == month]
        return self._as_records(df)

    def get_goals(self, user_id: int | None = None) -> list[dict[str, Any]]:
        df = self._load_csv("goals")
        ensure_required_columns(
            df, ["user_id", "goal_name", "target_amount", "current_amount"], "goals"
        )
        ensure_non_negative(df["target_amount"], "goals.target_amount")
        ensure_non_negative(df["current_amount"], "goals.current_amount")
        if user_id is not None:
            df = df[df["user_id"] == user_id]
        return self._as_records(df)

    def get_investments(self, user_id: int | None = None) -> list[dict[str, Any]]:
        df = self._load_csv("investments")
        ensure_required_columns(df, ["user_id", "asset_type", "amount"], "investments")
        ensure_non_negative(df["amount"], "investments.amount")
        if user_id is not None:
            df = df[df["user_id"] == user_id]
        return self._as_records(df)

    def calculate_totals(self, user_id: int, month: str | None = None) -> dict[str, float]:
        income = pd.DataFrame(self.get_income(user_id=user_id, month=month))
        expenses = pd.DataFrame(self.get_expenses(user_id=user_id, month=month))

        total_income = float(income["amount"].sum()) if not income.empty else 0.0
        total_expense = float(expenses["amount"].sum()) if not expenses.empty else 0.0

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "savings": total_income - total_expense,
            "savings_rate": ((total_income - total_expense) / total_income * 100.0)
            if total_income > 0
            else 0.0,
        }

    def update_csv(self, table: str, records: list[dict[str, Any]]) -> None:
        if not records:
            return
        path = self._file_path(table)
        if not path.exists():
            raise CSVFileMissingError(f"CSV file not found: {path}")

        current = self._load_csv(table)
        incoming = pd.DataFrame(records)
        updated = pd.concat([current, incoming], ignore_index=True)
        updated.to_csv(path, index=False)

        logger.info("Updated table %s with %s records", table, len(records))
        self._cache.pop(table, None)
        self._cache_mtime.pop(table, None)
