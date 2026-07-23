import pandas as pd

from app.middleware.error_handler import FinancialValueError


def ensure_required_columns(df: pd.DataFrame, required: list[str], table_name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise FinancialValueError(
            f"Missing columns in {table_name}: {', '.join(missing)}"
        )


def ensure_non_negative(series: pd.Series, field_name: str) -> None:
    if (series < 0).any():
        raise FinancialValueError(f"Negative values found in field: {field_name}")
