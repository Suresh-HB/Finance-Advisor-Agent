from typing import Any, TypedDict


class FinanceAgentState(TypedDict, total=False):
    user_id: int
    user_message: str
    intent: str
    month: str | None
    search_query: str | None
    requested_amount: float | None
    selected_tools: list[str]
    analysis_results: dict[str, Any]
    reasoning: str
    final_answer: str
