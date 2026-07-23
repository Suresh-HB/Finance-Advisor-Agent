from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import config


class ReportService:
    def __init__(self, reports_dir: Path | None = None) -> None:
        self.reports_dir = Path(reports_dir or config.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def save_monthly_report(self, user_id: int, month: str, payload: dict[str, Any]) -> Path:
        filename = f"report_user_{user_id}_{month}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
        report_path = self.reports_dir / filename
        report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return report_path
