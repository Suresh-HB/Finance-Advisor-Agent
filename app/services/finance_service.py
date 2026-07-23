from __future__ import annotations

from collections import defaultdict
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from app.repository.csv_repository import CSVRepository


class FinanceService:
    def __init__(self, repository: CSVRepository) -> None:
        self.repository = repository

    def monthly_spending(self, user_id: int, month: str | None = None) -> dict[str, Any]:
        expenses = pd.DataFrame(self.repository.get_expenses(user_id=user_id, month=month))
        total = float(expenses["amount"].sum()) if not expenses.empty else 0.0
        by_category = (
            expenses.groupby("category")["amount"].sum().sort_values(ascending=False).to_dict()
            if not expenses.empty
            else {}
        )
        return {"total_spending": total, "by_category": by_category}

    def income_vs_expense(self, user_id: int, month: str | None = None) -> dict[str, float]:
        return self.repository.calculate_totals(user_id=user_id, month=month)

    def budget_status(self, user_id: int, month: str) -> dict[str, Any]:
        totals = self.repository.calculate_totals(user_id=user_id, month=month)
        budgets = self.repository.get_budgets(user_id=user_id, month=month)
        budget_limit = float(budgets[0]["budget_limit"]) if budgets else 0.0
        spent = totals["total_expense"]
        usage_pct = (spent / budget_limit * 100.0) if budget_limit > 0 else 0.0
        return {
            "month": month,
            "budget_limit": budget_limit,
            "spent": spent,
            "is_exceeded": spent > budget_limit if budget_limit > 0 else False,
            "usage_pct": usage_pct,
        }

    def investment_summary(self, user_id: int) -> dict[str, Any]:
        investments = pd.DataFrame(self.repository.get_investments(user_id=user_id))
        if investments.empty:
            return {"total": 0.0, "by_asset": {}}

        by_asset = investments.groupby("asset_type")["amount"].sum().to_dict()
        total = float(investments["amount"].sum())
        return {"total": total, "by_asset": by_asset}

    def goal_progress(self, user_id: int) -> list[dict[str, Any]]:
        goals = self.repository.get_goals(user_id=user_id)
        output: list[dict[str, Any]] = []
        for goal in goals:
            target = float(goal["target_amount"])
            current = float(goal["current_amount"])
            output.append(
                {
                    **goal,
                    "progress_pct": (current / target * 100.0) if target > 0 else 0.0,
                }
            )
        return output

    def monthly_series(self, user_id: int) -> dict[str, Any]:
        income_df = pd.DataFrame(self.repository.get_income(user_id=user_id))
        expense_df = pd.DataFrame(self.repository.get_expenses(user_id=user_id))

        if income_df.empty:
            return {"months": [], "income": [], "expense": [], "savings": []}

        income_df["month"] = pd.to_datetime(income_df["date"]).dt.strftime("%Y-%m")
        expense_df["month"] = pd.to_datetime(expense_df["date"]).dt.strftime("%Y-%m")

        income_map = income_df.groupby("month")["amount"].sum().to_dict()
        expense_map = expense_df.groupby("month")["amount"].sum().to_dict()
        months = sorted(set(income_map.keys()) | set(expense_map.keys()))

        income_vals = [float(income_map.get(m, 0.0)) for m in months]
        expense_vals = [float(expense_map.get(m, 0.0)) for m in months]
        savings_vals = [inc - exp for inc, exp in zip(income_vals, expense_vals)]

        return {
            "months": months,
            "income": income_vals,
            "expense": expense_vals,
            "savings": savings_vals,
        }

    def can_afford(self, user_id: int, month: str, amount: float) -> dict[str, Any]:
        totals = self.repository.calculate_totals(user_id=user_id, month=month)
        emergency_goal = [g for g in self.goal_progress(user_id) if g["goal_name"] == "Emergency Fund"]
        emergency_fund = float(emergency_goal[0]["current_amount"]) if emergency_goal else 0.0

        available = max(0.0, totals["savings"]) + emergency_fund * 0.2
        return {
            "requested_amount": amount,
            "available_estimate": available,
            "can_afford": available >= amount,
        }

    def spending_risks(self, user_id: int, month: str | None = None) -> list[str]:
        spending = self.monthly_spending(user_id=user_id, month=month)
        totals = self.repository.calculate_totals(user_id=user_id, month=month)
        warnings: list[str] = []

        if totals["total_income"] > 0 and totals["savings_rate"] < 15:
            warnings.append("Savings rate is below 15 percent, which increases financial risk.")

        category_map = spending["by_category"]
        total_spending = spending["total_spending"]
        for category, value in category_map.items():
            if total_spending > 0 and (value / total_spending) > 0.35:
                warnings.append(f"High concentration in {category} expenses.")

        return warnings

    def create_charts(self, user_id: int, month: str | None = None) -> dict[str, plt.Figure]:
        charts: dict[str, plt.Figure] = {}
        spending = self.monthly_spending(user_id=user_id, month=month)
        series = self.monthly_series(user_id=user_id)
        budget_info = self.budget_status(user_id, month) if month else None
        investments = self.investment_summary(user_id=user_id)

        fig1, ax1 = plt.subplots(figsize=(7, 4))
        cats = list(spending["by_category"].keys())
        vals = list(spending["by_category"].values())
        ax1.bar(cats, vals, color="#1f77b4")
        ax1.set_title("Expense Categories")
        ax1.tick_params(axis="x", rotation=35)
        charts["expense_categories"] = fig1

        fig2, ax2 = plt.subplots(figsize=(7, 4))
        ax2.plot(series["months"], series["income"], label="Income", marker="o")
        ax2.plot(series["months"], series["expense"], label="Expense", marker="o")
        ax2.set_title("Income vs Expense")
        ax2.legend()
        ax2.tick_params(axis="x", rotation=35)
        charts["income_vs_expense"] = fig2

        fig3, ax3 = plt.subplots(figsize=(7, 4))
        ax3.plot(series["months"], series["savings"], label="Savings", marker="o", color="#2ca02c")
        ax3.set_title("Savings Trend")
        ax3.tick_params(axis="x", rotation=35)
        charts["savings_trend"] = fig3

        month_table = self.monthly_expense_table(user_id=user_id)
        if month_table:
            fig_monthly, ax_monthly = plt.subplots(figsize=(7, 4))
            months = [row["month"] for row in month_table]
            amounts = [row["amount"] for row in month_table]
            ax_monthly.bar(months, amounts, color="#ff7f0e")
            ax_monthly.set_title("Monthly Expenses")
            ax_monthly.tick_params(axis="x", rotation=35)
            charts["monthly_expenses"] = fig_monthly

        if budget_info:
            fig4, ax4 = plt.subplots(figsize=(5, 4))
            ax4.bar(["Spent", "Remaining"], [budget_info["spent"], max(0, budget_info["budget_limit"] - budget_info["spent"])], color=["#d62728", "#17becf"])
            ax4.set_title("Budget Usage")
            charts["budget_usage"] = fig4

        if investments["by_asset"]:
            fig5, ax5 = plt.subplots(figsize=(6, 4))
            ax5.pie(investments["by_asset"].values(), labels=investments["by_asset"].keys(), autopct="%1.1f%%")
            ax5.set_title("Investment Allocation")
            charts["investment_allocation"] = fig5

        return charts

    def monthly_expense_table(self, user_id: int) -> list[dict[str, Any]]:
        expenses = pd.DataFrame(self.repository.get_expenses(user_id=user_id))
        if expenses.empty:
            return []
        expenses["month"] = pd.to_datetime(expenses["date"]).dt.strftime("%Y-%m")
        grouped = expenses.groupby("month")["amount"].sum().reset_index()
        return grouped.to_dict(orient="records")

    def emergency_fund(self, user_id: int) -> dict[str, float]:
        goals = self.goal_progress(user_id)
        ef = [g for g in goals if g["goal_name"] == "Emergency Fund"]
        if not ef:
            return {"emergency_fund": 0.0}
        return {"emergency_fund": float(ef[0]["current_amount"])}

    def personalized_recommendations(self, user_id: int, month: str | None = None) -> list[str]:
        recs: list[str] = []
        totals = self.repository.calculate_totals(user_id=user_id, month=month)
        spending = self.monthly_spending(user_id=user_id, month=month)
        top_category = ""
        top_value = 0.0
        for category, value in spending["by_category"].items():
            if value > top_value:
                top_category = category
                top_value = float(value)

        if totals["savings_rate"] < 20:
            recs.append("Increase monthly savings to at least 20 percent by reducing discretionary spending.")
        if top_category:
            recs.append(f"Set a category cap for {top_category}; it is currently your largest spend bucket.")
        if totals["total_expense"] > totals["total_income"] * 0.85:
            recs.append("Your expenses are too close to income; build a larger monthly buffer.")
        if not recs:
            recs.append("Your finances look balanced. Continue investing surplus cash consistently.")

        return recs
