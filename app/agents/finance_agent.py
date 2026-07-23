from __future__ import annotations

from app.graph.workflow import FinanceWorkflow
from app.services.container import container


class FinanceAdvisorAgent:
    def __init__(self) -> None:
        self.workflow = FinanceWorkflow()
        self.history = container.history_service

    def chat(self, user_id: int, message: str) -> dict:
        result = self.workflow.run(user_id=user_id, user_message=message)
        self.history.append(
            user_id=user_id,
            user_message=message,
            assistant_answer=result["answer"],
            analysis=result["analysis"],
        )
        return result


finance_agent = FinanceAdvisorAgent()
