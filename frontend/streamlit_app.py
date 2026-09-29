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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #0f172a;
    }
    .stApp {
        background: #f4f7fb;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .stSidebar > div {
        background: #f8fafc;
        border-right: 1px solid #e2e8f0;
        color: #0f172a;
    }
    .stSidebar .stSelectbox label,
    .stSidebar .stTextInput label,
    .stSidebar .stRadio label {
        color: #334155 !important;
        font-weight: 600;
        font-size: 0.79rem;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }
    .stSidebar .stSelectbox div[role="combobox"],
    .stSidebar .stTextInput input,
    .stSidebar .stRadio div {
        background: #ffffff;
        color: #0f172a;
        border: 1px solid #dfe7f1;
        border-radius: 10px;
        box-shadow: none;
    }
    .title-card {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        color: white;
        border-radius: 18px;
        padding: 1.4rem 1.5rem;
        margin-bottom: 1.2rem;
        border: 1px solid rgba(148, 163, 184, 0.15);
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
    }
    .title-card h2 {
        margin: 0 0 0.35rem 0;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.04em;
    }
    .title-card p {
        margin: 0;
        font-size: 0.96rem;
        color: rgba(255,255,255,0.76);
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1rem 1.1rem;
        min-height: 125px;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
    }
    .metric-label {
        font-size: 0.74rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.15;
        letter-spacing: -0.04em;
    }
    .metric-delta {
        margin-top: 0.45rem;
        font-size: 0.78rem;
        color: #0f766e;
        font-weight: 600;
    }
    .panel-title {
        margin-top: 1.25rem;
        margin-bottom: 0.7rem;
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #0f172a;
    }
    .chat-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
    }
    .stButton > button {
        background: #0f172a;
        color: #ffffff;
        border: 1px solid #0f172a;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.62rem 1.1rem;
        box-shadow: none;
    }
    .stButton > button:hover {
        background: #1e293b;
        color: white;
    }
    .stTextArea textarea {
        border-radius: 12px;
        border: 1px solid #dfe7f1;
        background: #ffffff;
        min-height: 130px;
    }
    .stAlert {
        border-radius: 10px;
    }
    h3 {
        color: #0f172a;
        letter-spacing: -0.03em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="title-card"><h2>Intelligent Personal Finance Advisor Agent</h2><p>Agentic financial assistant with LangGraph reasoning and local CSV intelligence.</p></div>',
    unsafe_allow_html=True,
)

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


def render_metric_card(title: str, value: str, delta: str | None = None, accent: str = "primary") -> None:
    delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ""
    accent_style = (
        "background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);"
        if accent == "primary"
        else "background: linear-gradient(180deg, #ffffff 0%, #f5faf7 100%);"
    )
    st.markdown(
        f"""
        <div class="metric-card" style="{accent_style}">
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str) -> None:
    st.markdown(f'<div class="panel-title">{title}</div>', unsafe_allow_html=True)


def run_finance_chat(prompt: str, label: str = "Analyzing your finances...") -> dict:
    with st.spinner(label):
        return finance_agent.chat(selected_user, prompt)


def render_ai_page_insight(page_key: str, prompt: str) -> None:
    render_section_header("AI Insight")
    if st.button("Generate AI Insight", key=f"ai_insight_{page_key}"):
        try:
            result = run_finance_chat(prompt, "Generating financial insight...")
            st.write(result["answer"])
            with st.expander("AI Analysis JSON"):
                st.json(result["analysis"])
        except Exception as exc:
            st.error("AI insight is temporarily unavailable. Please try again in a moment.")
            st.caption(str(exc))

if page == "Dashboard":
    totals = container.repository.calculate_totals(selected_user, selected_month)
    emergency = finance.emergency_fund(selected_user)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Income", f"Rs {totals['total_income']:,.0f}", "This month", "primary")
    with c2:
        render_metric_card("Expenses", f"Rs {totals['total_expense']:,.0f}", "Spent", "primary")
    with c3:
        render_metric_card("Savings", f"Rs {totals['savings']:,.0f}", "Net saved", "primary")
    with c4:
        render_metric_card("Emergency Fund", f"Rs {emergency['emergency_fund']:,.0f}", "Protected", "secondary")

    charts = finance.create_charts(selected_user, selected_month)
    render_section_header("Monthly Expenses")
    if "monthly_expenses" in charts:
        st.pyplot(charts["monthly_expenses"])
    elif "expense_categories" in charts:
        st.pyplot(charts["expense_categories"])

    render_section_header("Income vs Expense")
    if "income_vs_expense" in charts:
        st.pyplot(charts["income_vs_expense"])

    render_ai_page_insight(
        "dashboard",
        f"Provide a dashboard summary for user {selected_user} for month {selected_month}. Include savings health, budget status, and one action.",
    )

if page == "Chat Assistant":
    render_section_header("Ask your advisor")
    st.markdown('<div class="chat-card">', unsafe_allow_html=True)
    question = st.text_area("Question", placeholder="How much did I spend this month?")
    if st.button("Analyze") and question.strip():
        try:
            result = run_finance_chat(question)
            st.markdown("### Advisor Response")
            st.write(result["answer"])
            st.markdown("### Analysis JSON")
            st.json(result["analysis"])
        except Exception as exc:
            st.error("The advisor is temporarily unavailable. Please try again in a moment.")
            st.info("If the issue continues, check the LLM endpoint availability.")
            st.caption(str(exc))
    st.markdown('</div>', unsafe_allow_html=True)

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
