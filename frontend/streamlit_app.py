from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.finance_agent import finance_agent
from app.config import config
from app.services.container import container
from app.tools.finance_tools import build_finance_tools
from app.utils.data_generator import generate_synthetic_data_if_missing


generate_synthetic_data_if_missing()

st.set_page_config(page_title="Finance Advisor", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
    html, body, [class*="css"]  {font-family: 'Space Grotesk', sans-serif;}
    .stApp {
        background: radial-gradient(circle at top left, #f9f5ec 0%, #f0f7ff 45%, #ffffff 100%);
    }
    .title-card {
        background: linear-gradient(120deg, #0f4c5c, #2a9d8f);
        color: white;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title-card"><h2>Intelligent Personal Finance Advisor Agent</h2><p>Agentic financial assistant with LangGraph reasoning and local CSV intelligence.</p></div>', unsafe_allow_html=True)

users = container.repository.get_users()
user_map = {f"{u['user_id']} - {u['name']}": u["user_id"] for u in users}
selected_user_label = st.sidebar.selectbox("Select User", list(user_map.keys()))
selected_user = user_map[selected_user_label]
selected_month = st.sidebar.text_input("Month (YYYY-MM)", value=datetime.today().strftime("%Y-%m"))

page = st.sidebar.radio(
    "Pages",
    [
        "Dashboard",
        "Chat Assistant",
        "Financial Reports",
        "Expense Analysis",
        "Budget Tracker",
        "Investment Summary",
        "Upload CSV",
        "Settings",
        "Analytics",
    ],
)

finance = container.finance_service
tools = build_finance_tools()


def render_ai_page_insight(page_key: str, prompt: str) -> None:
    st.markdown("### AI Insight")
    if st.button("Generate AI Insight", key=f"ai_insight_{page_key}"):
        try:
            result = finance_agent.chat(selected_user, prompt)
            st.write(result["answer"])
            with st.expander("AI Analysis JSON"):
                st.json(result["analysis"])
        except Exception as exc:
            st.error(f"AI insight unavailable: {exc}")

if page == "Dashboard":
    totals = container.repository.calculate_totals(selected_user, selected_month)
    emergency = finance.emergency_fund(selected_user)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Income", f"Rs {totals['total_income']:,.0f}")
    c2.metric("Expenses", f"Rs {totals['total_expense']:,.0f}")
    c3.metric("Savings", f"Rs {totals['savings']:,.0f}")
    c4.metric("Emergency Fund", f"Rs {emergency['emergency_fund']:,.0f}")

    charts = finance.create_charts(selected_user, selected_month)
    st.subheader("Monthly Expenses")
    if "monthly_expenses" in charts:
        st.pyplot(charts["monthly_expenses"])
    elif "expense_categories" in charts:
        st.pyplot(charts["expense_categories"])

    st.subheader("Income vs Expense")
    if "income_vs_expense" in charts:
        st.pyplot(charts["income_vs_expense"])

    render_ai_page_insight(
        "dashboard",
        f"Provide a dashboard summary for user {selected_user} for month {selected_month}. Include savings health, budget status, and one action.",
    )

if page == "Chat Assistant":
    st.subheader("Ask your advisor")
    question = st.text_area("Question", placeholder="How much did I spend this month?")
    if st.button("Analyze") and question.strip():
        try:
            result = finance_agent.chat(selected_user, question)
            st.markdown("### Advisor Response")
            st.write(result["answer"])
            st.markdown("### Analysis JSON")
            st.json(result["analysis"])
        except Exception as exc:
            st.error(f"AI request failed: {exc}")
            st.info("Try again in a few seconds. If this continues, check LLM endpoint availability.")

if page == "Financial Reports":
    st.subheader("Generate Monthly Report")
    if st.button("Generate Report"):
        report_raw = tools["financial_report_generator"].invoke(
            {"user_id": selected_user, "month": selected_month}
        )
        report_payload = json.loads(report_raw)
        report_data = pd.json_normalize([report_payload])
        st.success("Report generated and saved to app/storage/reports")
        st.dataframe(report_data.T)

    render_ai_page_insight(
        "financial_reports",
        f"Summarize this month's financial report priorities for user {selected_user} in month {selected_month}. Keep it concise and actionable.",
    )

if page == "Expense Analysis":
    st.subheader("Expense Breakdown")
    spending = finance.monthly_spending(selected_user, selected_month)
    st.metric("Total Spending", f"Rs {spending['total_spending']:,.0f}")
    st.dataframe(pd.DataFrame(spending["by_category"].items(), columns=["Category", "Amount"]))

    charts = finance.create_charts(selected_user, selected_month)
    if "expense_categories" in charts:
        st.pyplot(charts["expense_categories"])

    render_ai_page_insight(
        "expense_analysis",
        f"Analyze spending patterns for user {selected_user} in month {selected_month}. Identify top category risk and give two reduction suggestions.",
    )

if page == "Budget Tracker":
    st.subheader("Budget Status")
    budget = finance.budget_status(selected_user, selected_month)
    st.metric("Budget Limit", f"Rs {budget['budget_limit']:,.0f}")
    st.metric("Spent", f"Rs {budget['spent']:,.0f}")
    st.metric("Usage", f"{budget['usage_pct']:.1f}%")
    if budget["is_exceeded"]:
        st.error("Budget exceeded")
    else:
        st.success("Within budget")

    charts = finance.create_charts(selected_user, selected_month)
    if "budget_usage" in charts:
        st.pyplot(charts["budget_usage"])

    render_ai_page_insight(
        "budget_tracker",
        f"Review budget status for user {selected_user} in month {selected_month}. Explain whether spending is safe and what to do next week.",
    )

if page == "Investment Summary":
    st.subheader("Portfolio Snapshot")
    investments = finance.investment_summary(selected_user)
    st.metric("Total Investments", f"Rs {investments['total']:,.0f}")
    st.dataframe(pd.DataFrame(investments["by_asset"].items(), columns=["Asset", "Amount"]))

    charts = finance.create_charts(selected_user, selected_month)
    if "investment_allocation" in charts:
        st.pyplot(charts["investment_allocation"])

    render_ai_page_insight(
        "investment_summary",
        f"Summarize investment allocation for user {selected_user}. Mention diversification risk and one rebalance suggestion.",
    )

if page == "Upload CSV":
    st.subheader("Replace dataset CSV")
    file_type = st.selectbox(
        "File Type",
        ["users", "income", "expenses", "transactions", "budgets", "goals", "investments"],
    )
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded and st.button("Save CSV"):
        target = Path(config.storage_dir) / f"{file_type}.csv"
        target.write_bytes(uploaded.read())
        container.repository._cache.pop(file_type, None)
        container.repository._cache_mtime.pop(file_type, None)
        st.success(f"Saved {target}")

if page == "Settings":
    st.subheader("Runtime Settings")
    st.text_input("LLM Base URL", value=config.llm_base_url, disabled=True)
    st.text_input("LLM Model", value=config.llm_model, disabled=True)
    st.text_input("History File", value=str(config.history_file), disabled=True)

if page == "Analytics":
    st.subheader("Advanced Analytics")
    series = finance.monthly_series(selected_user)
    month_df = pd.DataFrame(
        {
            "Month": series["months"],
            "Income": series["income"],
            "Expense": series["expense"],
            "Savings": series["savings"],
        }
    )
    st.dataframe(month_df)

    charts = finance.create_charts(selected_user, selected_month)
    if "savings_trend" in charts:
        st.pyplot(charts["savings_trend"])

    recs = finance.personalized_recommendations(selected_user, selected_month)
    risks = finance.spending_risks(selected_user, selected_month)
    st.markdown("### Recommendations")
    for rec in recs:
        st.write(f"- {rec}")
    st.markdown("### Risks")
    if risks:
        for risk in risks:
            st.write(f"- {risk}")
    else:
        st.write("- No major risks detected.")

    render_ai_page_insight(
        "analytics",
        f"Provide an analytics insight for user {selected_user} in month {selected_month}, combining trend, risks, and next action.",
    )
