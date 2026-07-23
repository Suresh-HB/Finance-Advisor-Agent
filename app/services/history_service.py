from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import config


class ConversationHistoryService:
    def __init__(self, history_file: Path | None = None) -> None:
        self.history_file = Path(history_file or config.history_file)

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.history_file.exists():
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            self.history_file.write_text("[]", encoding="utf-8")
        with self.history_file.open("r", encoding="utf-8") as f:
            return json.load(f)

    def append(
        self,
        user_id: int,
        user_message: str,
        assistant_answer: str,
        analysis: dict[str, Any],
    ) -> None:
        history = self._read_all()
        history.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "user_message": user_message,
                "assistant_answer": assistant_answer,
                "analysis": analysis,
            }
        )
        with self.history_file.open("w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    def get_by_user(self, user_id: int, limit: int = 20) -> list[dict[str, Any]]:
        history = self._read_all()
        user_history = [item for item in history if item.get("user_id") == user_id]
        return user_history[-limit:]
