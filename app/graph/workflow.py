from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from app.config import config
from app.graph.state import FinanceAgentState
from app.middleware.error_handler import LLMTimeoutError
from app.prompts.templates import FINAL_ANSWER_PROMPT, SYSTEM_PROMPT, TOOL_SELECTION_PROMPT
from app.services.container import container
from app.tools.finance_tools import build_finance_tools
from app.utils.logger import logger


def _extract_month(text: str) -> str | None:
    match = re.search(r"(20\d{2})-(0[1-9]|1[0-2])", text)
    if match:
        return match.group(0)
    return datetime.today().strftime("%Y-%m")


def _normalize_month(raw_month: str | None, fallback: str) -> str:
    if not raw_month:
        return fallback
    match = re.search(r"(20\d{2})-(0[1-9]|1[0-2])", str(raw_month))
    if match:
        return match.group(0)
    return fallback


def _extract_amount(text: str) -> float | None:
    match = re.search(r"(\d{4,7}(?:\.\d+)?)", text.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _parse_json_from_llm_text(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw, flags=re.IGNORECASE)
    if fenced:
        try:
            parsed = json.loads(fenced.group(1))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    first_obj = re.search(r"\{[\s\S]*\}", raw)
    if first_obj:
        try:
            parsed = json.loads(first_obj.group(0))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
    return None


def _heuristic_tool_selection(user_message: str) -> dict[str, Any]:
    m = user_message.lower()
    tools: list[str] = []

    if "spend" in m or "expense" in m or "category" in m:
        tools.append("expense_analyzer")
    if "save" in m or "savings" in m:
        tools.append("savings_calculator")
    if "budget" in m:
        tools.append("budget_checker")
    if "invest" in m:
        tools.append("investment_summary")
    if "goal" in m or "emergency" in m:
        tools.append("goal_progress")
    if "transaction" in m or "search" in m:
        tools.append("transaction_search")
    if "report" in m:
        tools.append("financial_report_generator")
    if "income" in m:
        tools.append("income_analyzer")
    if "afford" in m or "vacation" in m:
        tools.append("affordability_checker")

    if not tools:
        tools = ["expense_analyzer", "savings_calculator", "budget_checker"]

    unique_tools = list(dict.fromkeys(tools))
    return {
        "intent": "financial_advice",
        "tools": unique_tools,
        "month": _extract_month(user_message),
        "search_query": None,
        "requested_amount": _extract_amount(user_message),
    }


def _is_greeting_message(text: str) -> bool:
    normalized = re.sub(r"[^a-z ]", "", text.lower()).strip()
    greeting_terms = {
        "hi",
        "hello",
        "hey",
        "hii",
        "hola",
        "good morning",
        "good evening",
        "good afternoon",
    }
    return normalized in greeting_terms


class FinanceWorkflow:
    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            model=config.llm_model,
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
            timeout=config.llm_timeout_seconds,
            max_retries=config.llm_max_retries,
            temperature=0.2,
        )
        self.tools = build_finance_tools()
        self.repository = container.repository
        self.llm_enabled = config.llm_enabled
        self.llm_strict_mode = config.llm_strict_mode
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(FinanceAgentState)

        workflow.add_node("understand_request", self.understand_request)
        workflow.add_node("select_tools", self.select_tools)
        workflow.add_node("execute_analysis", self.execute_analysis)
        workflow.add_node("reasoning", self.reasoning)
        workflow.add_node("generate_advice", self.generate_advice)

        workflow.add_edge(START, "understand_request")
        workflow.add_edge("understand_request", "select_tools")
        workflow.add_edge("select_tools", "execute_analysis")
        workflow.add_edge("execute_analysis", "reasoning")
        workflow.add_edge("reasoning", "generate_advice")
        workflow.add_edge("generate_advice", END)

        return workflow.compile()

    def understand_request(self, state: FinanceAgentState) -> FinanceAgentState:
        state["month"] = _extract_month(state["user_message"])
        state["requested_amount"] = _extract_amount(state["user_message"])
        return state

    def select_tools(self, state: FinanceAgentState) -> FinanceAgentState:
        tool_names = ", ".join(self.tools.keys())
        prompt = TOOL_SELECTION_PROMPT.format(tool_names=tool_names, user_message=state["user_message"])

        parsed: dict[str, Any] | None = None
        if self.llm_enabled:
            try:
                response = self.llm.invoke([
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ])
                raw = response.content if isinstance(response.content, str) else str(response.content)
                parsed_candidate = _parse_json_from_llm_text(raw)
                if parsed_candidate is None:
                    raise ValueError("LLM output did not contain valid JSON")
                parsed = parsed_candidate
            except Exception as exc:
                logger.error("Tool selection via LLM failed: %s", exc)
                if self.llm_strict_mode:
                    raise LLMTimeoutError("LLM tool selection failed. Please retry in a moment.") from exc

        if parsed is None:
            parsed = _heuristic_tool_selection(state["user_message"])

        state["intent"] = parsed.get("intent", "financial_advice")
        state["selected_tools"] = [
            t for t in parsed.get("tools", []) if t in self.tools
        ] or ["expense_analyzer", "savings_calculator"]
        state["search_query"] = parsed.get("search_query")
        fallback_month = state.get("month") or datetime.today().strftime("%Y-%m")
        state["month"] = _normalize_month(parsed.get("month"), fallback_month)
        state["requested_amount"] = parsed.get("requested_amount") or state.get("requested_amount")
        return state

    def _latest_user_month(self, user_id: int) -> str | None:
        try:
            rows = self.repository.get_expenses(user_id=user_id)
            if not rows:
                return None
            months: list[str] = []
            for row in rows:
                date_str = str(row.get("date", ""))
                match = re.search(r"(20\d{2})-(0[1-9]|1[0-2])", date_str)
                if match:
                    months.append(match.group(0))
            return max(months) if months else None
        except Exception:
            return None

    def _tool_args(self, tool_name: str, state: FinanceAgentState) -> dict[str, Any]:
        user_id = state["user_id"]
        month = state.get("month")
        valid_month = bool(month and re.match(r"^20\d{2}-(0[1-9]|1[0-2])$", month))
        effective_month = month if valid_month else datetime.today().strftime("%Y-%m")

        # If selected month has no financial rows, use the latest available month for that user.
        if effective_month:
            try:
                has_expense = bool(self.repository.get_expenses(user_id=user_id, month=effective_month))
                has_income = bool(self.repository.get_income(user_id=user_id, month=effective_month))
                if not (has_expense or has_income):
                    effective_month = self._latest_user_month(user_id) or effective_month
            except Exception:
                effective_month = self._latest_user_month(user_id) or effective_month

        if tool_name in {"income_analyzer", "expense_analyzer", "budget_checker", "savings_calculator"}:
            return {"user_id": user_id, "month": effective_month}
        if tool_name in {"investment_summary", "goal_progress"}:
            return {"user_id": user_id}
        if tool_name == "affordability_checker":
            return {
                "user_id": user_id,
                "month": effective_month or datetime.today().strftime("%Y-%m"),
                "amount": float(state.get("requested_amount") or 50000.0),
            }
        if tool_name == "transaction_search":
            return {
                "user_id": user_id,
                "query": state.get("search_query") or "payment",
                "month": effective_month,
            }
        if tool_name == "financial_report_generator":
            return {
                "user_id": user_id,
                "month": effective_month or datetime.today().strftime("%Y-%m"),
            }
        if tool_name == "csv_loader":
            return {"table": "transactions"}
        return {}

    def execute_analysis(self, state: FinanceAgentState) -> FinanceAgentState:
        results: dict[str, Any] = {}
        for tool_name in state.get("selected_tools", []):
            tool = self.tools[tool_name]
            args = self._tool_args(tool_name, state)
            try:
                results[tool_name] = json.loads(tool.invoke(args))
            except Exception as exc:
                results[tool_name] = {"error": str(exc)}

        state["analysis_results"] = results
        return state

    def reasoning(self, state: FinanceAgentState) -> FinanceAgentState:
        analysis = state.get("analysis_results", {})
        bullets: list[str] = []

        expense = analysis.get("expense_analyzer")
        if isinstance(expense, dict):
            total_spend = float(expense.get("total_spending", 0.0))
            by_category = expense.get("by_category", {})
            if isinstance(by_category, dict) and by_category:
                top = max(by_category.items(), key=lambda x: x[1])
                bullets.append(f"Top spending category is {top[0]} with Rs {float(top[1]):,.0f}.")
            bullets.append(f"Total spending in selected period is Rs {total_spend:,.0f}.")

        savings = analysis.get("savings_calculator") or analysis.get("income_analyzer")
        if isinstance(savings, dict):
            rate = float(savings.get("savings_rate", 0.0))
            bullets.append(f"Savings rate is {rate:.1f} percent.")
            if rate < 20:
                bullets.append("Savings rate is below the 20 percent target; expense optimization is recommended.")

        budget = analysis.get("budget_checker")
        if isinstance(budget, dict) and "is_exceeded" in budget:
            if bool(budget.get("is_exceeded")):
                bullets.append("Budget limit is exceeded for the selected month.")
            else:
                bullets.append("Budget is currently under control for the selected month.")

        if not bullets:
            bullets.append("Using available tool outputs to generate practical recommendations.")

        state["reasoning"] = "\n".join(f"- {b}" for b in bullets[:4])
        return state

    def generate_advice(self, state: FinanceAgentState) -> FinanceAgentState:
        analysis_compact = json.dumps(state.get("analysis_results", {}), default=str)
        analysis_compact = analysis_compact[:3500]
        prompt = FINAL_ANSWER_PROMPT.format(
            user_message=state["user_message"],
            analysis_json=analysis_compact,
        )
        if not self.llm_enabled:
            state["final_answer"] = self._fallback_advice(state)
            return state

        try:
            response = self.llm.invoke([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt + "\n\nReasoning context:\n" + state.get("reasoning", "")},
            ])
            state["final_answer"] = response.content if isinstance(response.content, str) else str(response.content)
        except Exception as exc:
            logger.error("LLM response generation failed: %s", exc)
            if self.llm_strict_mode:
                raise LLMTimeoutError("LLM response generation failed. Please retry.") from exc
            state["final_answer"] = self._fallback_advice(state)
        return state

    def _greeting_response(self, user_message: str) -> str:
        if not self.llm_enabled:
            return (
                "Hello. I am your Intelligent Personal Finance Advisor. "
                "You can ask things like: how much you spent this month, "
                "whether you are over budget, affordability for a purchase, "
                "or request a monthly financial report."
            )

        greeting_prompt = (
            "The user sent a greeting. Reply with a short friendly greeting and one sentence "
            "explaining the finance help you can provide. User message: "
            f"{user_message}"
        )
        try:
            response = self.llm.invoke([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": greeting_prompt},
            ])
            return response.content if isinstance(response.content, str) else str(response.content)
        except Exception as exc:
            logger.error("Greeting generation via LLM failed: %s", exc)
            if self.llm_strict_mode:
                raise LLMTimeoutError("LLM greeting generation failed. Please retry.") from exc
            return (
                "Hello. I am your Intelligent Personal Finance Advisor. "
                "You can ask things like: how much you spent this month, "
                "whether you are over budget, affordability for a purchase, "
                "or request a monthly financial report."
            )

    def _fallback_advice(self, state: FinanceAgentState) -> str:
        analysis = state.get("analysis_results", {})
        key_points: list[str] = []

        report_block = analysis.get("financial_report_generator")
        if isinstance(report_block, dict):
            nested = report_block.get("report", {})
            if isinstance(nested, dict):
                totals = nested.get("totals", {})
                spending = nested.get("spending", {})
                budget = nested.get("budget", {})
                if isinstance(totals, dict):
                    income = float(totals.get("total_income", 0.0))
                    expense = float(totals.get("total_expense", 0.0))
                    sv = float(totals.get("savings", 0.0))
                    rate = float(totals.get("savings_rate", 0.0))
                    key_points.append(
                        f"Income: Rs {income:,.0f}, Expense: Rs {expense:,.0f}, Savings: Rs {sv:,.0f}, Savings Rate: {rate:.1f}%"
                    )

                if isinstance(spending, dict):
                    by_category = spending.get("by_category", {})
                    if isinstance(by_category, dict) and by_category:
                        top = max(by_category.items(), key=lambda x: x[1])
                        key_points.append(
                            f"Highest spend category: {top[0]} at Rs {float(top[1]):,.0f}."
                        )

                if isinstance(budget, dict) and "is_exceeded" in budget:
                    if bool(budget.get("is_exceeded")):
                        key_points.append("You are exceeding your monthly budget. Reduce discretionary categories first.")
                    else:
                        key_points.append("You are currently within budget.")

        savings = analysis.get("savings_calculator") or analysis.get("income_analyzer")
        if isinstance(savings, dict):
            income = float(savings.get("total_income", 0.0))
            expense = float(savings.get("total_expense", 0.0))
            sv = float(savings.get("savings", income - expense))
            rate = float(savings.get("savings_rate", 0.0))
            key_points.append(
                f"Income: Rs {income:,.0f}, Expense: Rs {expense:,.0f}, Savings: Rs {sv:,.0f}, Savings Rate: {rate:.1f}%"
            )

        budget = analysis.get("budget_checker")
        if isinstance(budget, dict) and "is_exceeded" in budget:
            if budget.get("is_exceeded"):
                key_points.append("You are exceeding your monthly budget. Reduce discretionary categories first.")
            else:
                key_points.append("You are currently within budget.")

        expenses = analysis.get("expense_analyzer")
        if isinstance(expenses, dict):
            by_category = expenses.get("by_category", {})
            if isinstance(by_category, dict) and by_category:
                top = max(by_category.items(), key=lambda x: x[1])
                key_points.append(f"Highest spend category: {top[0]} at Rs {float(top[1]):,.0f}.")

        investments = analysis.get("investment_summary")
        if isinstance(investments, dict) and "total" in investments:
            key_points.append(f"Total investments: Rs {float(investments.get('total', 0.0)):,.0f}.")

        afford = analysis.get("affordability_checker")
        if isinstance(afford, dict) and "can_afford" in afford:
            requested = float(afford.get("requested_amount", 0.0))
            available = float(afford.get("available_estimate", 0.0))
            if bool(afford.get("can_afford")):
                key_points.append(
                    f"Affordability check: You can afford Rs {requested:,.0f} with estimated available Rs {available:,.0f}."
                )
            else:
                key_points.append(
                    f"Affordability check: You may not afford Rs {requested:,.0f}; estimated available is Rs {available:,.0f}."
                )

        if not key_points:
            key_points.append("Financial analysis is available, but no strong signal was detected from selected tools.")

        next_action = (
            "Next action: target a 20%+ savings rate, cap your top expense category, and review weekly transactions."
        )
        return "\n".join(["Financial Summary:"] + [f"- {k}" for k in key_points] + [next_action])

    def run(self, user_id: int, user_message: str) -> dict[str, Any]:
        if _is_greeting_message(user_message):
            return {
                "answer": self._greeting_response(user_message),
                "analysis": {},
                "reasoning": "Greeting detected. Returned LLM-generated onboarding response.",
                "selected_tools": [],
            }

        initial_state: FinanceAgentState = {
            "user_id": user_id,
            "user_message": user_message,
            "analysis_results": {},
            "selected_tools": [],
        }
        result = self.graph.invoke(initial_state)
        return {
            "answer": result.get("final_answer", "No response generated."),
            "analysis": result.get("analysis_results", {}),
            "reasoning": result.get("reasoning", ""),
            "selected_tools": result.get("selected_tools", []),
        }
