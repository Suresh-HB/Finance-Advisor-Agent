# Basic Walkthrough: Intelligent Personal Finance Advisor Agent

This guide explains the project from zero and helps you run a full demo locally.

## 1) What this project is

This is a local Agentic AI personal finance assistant.

It can:
- Read finance data from CSV files
- Analyze expenses, budgets, savings, goals, and investments
- Answer natural-language finance questions
- Generate monthly JSON reports
- Show dashboards in Streamlit

No external database is used.
All data is stored in local CSV and JSON files.

## 2) Project map (simple view)

- `app/api/`: FastAPI endpoints
- `app/graph/`: LangGraph workflow (agent steps)
- `app/tools/`: LangChain tools (one tool, one responsibility)
- `app/repository/`: CSV data access layer
- `app/services/`: business logic and chart generation
- `app/storage/`: all CSV/JSON files
- `frontend/`: Streamlit dashboard UI
- `demo/run_demo.py`: quick API walkthrough script

## 3) How the agent works

The workflow is:
- Understand user request
- Select tools
- Execute analysis
- Reason over results
- Generate advice

This is implemented in `app/graph/workflow.py`.

## 4) Run the project

From project root (`finance-advisor`):

```powershell
c:/Users/Suresh/Desktop/COP-Final/Finance-Advisor-Agent/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir c:/Users/Suresh/Desktop/COP-Final/Finance-Advisor-Agent
```

In another terminal:

```powershell
c:/Users/Suresh/Desktop/COP-Final/Finance-Advisor-Agent/.venv/Scripts/python.exe -m streamlit run c:/Users/Suresh/Desktop/COP-Final/Finance-Advisor-Agent/frontend/streamlit_app.py --server.port 8501 --server.headless true
```

Open:
- API docs: `http://127.0.0.1:8000/docs`
- UI: `http://localhost:8501`

## 5) Run the demo script

With backend running:

```powershell
c:/Users/Suresh/Desktop/COP-Final/Finance-Advisor-Agent/.venv/Scripts/python.exe demo/run_demo.py
```

The script will:
- Check health
- Read users
- Get expenses for user 1
- Run two chat prompts
- Print compact outputs

## 6) Try these chat questions

- How much did I spend this month?
- Where am I spending the most money?
- Am I exceeding my monthly budget?
- Can I afford a vacation costing 50000?
- Give me a monthly financial report.

## 7) Data files used

- `app/storage/users.csv`
- `app/storage/income.csv`
- `app/storage/expenses.csv`
- `app/storage/transactions.csv`
- `app/storage/budgets.csv`
- `app/storage/savings.csv`
- `app/storage/goals.csv`
- `app/storage/investments.csv`
- `app/storage/conversation_history.json`

## 8) Beginner troubleshooting

If API is not reachable:
- Make sure port 8000 is free
- Restart uvicorn command

If Streamlit is not reachable:
- Make sure port 8501 is free
- Restart streamlit command

If chat seems slow:
- The project currently runs in deterministic mode by default (`llm_enabled = False` in `app/config.py`) for stable local performance.

## 9) What to present in a demo interview

You can present in this order:
- Architecture and clean layering
- Repository pattern for CSV-only persistence
- Tool-based agent reasoning
- Live chat + dashboard walkthrough
- Report generation and local file outputs
