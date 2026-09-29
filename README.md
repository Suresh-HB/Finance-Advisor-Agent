# Intelligent Personal Finance Advisor Agent

## Project Overview
This capstone project is a local, agentic AI personal finance advisor built with FastAPI, Streamlit, LangChain, and LangGraph. It reads and updates local CSV files, reasons through multi-step financial analysis, and returns personalized recommendations.

## Architecture
- API Layer (FastAPI): serves chat and financial data endpoints.
- Agent Layer (LangGraph + LangChain): understands request, selects tools, executes analysis, reasons, and generates advice.
- Tool Layer: single-responsibility tools for income, expenses, budget, savings, investments, goals, transactions, reporting, and CSV loading.
- Service Layer: financial computations, chart generation, report persistence, and conversation history management.
- Repository Layer: CSV-only data access with caching, filtering, totals calculation, and updates.
- Storage Layer: local CSV/JSON files only.

## Folder Structure
```text
finance-advisor/
  app/
    api/
    agents/
    graph/
    repository/
    services/
    tools/
    prompts/
    models/
    schemas/
    middleware/
    utils/
    storage/
      users.csv
      income.csv
      expenses.csv
      investments.csv
      goals.csv
      budgets.csv
      transactions.csv
      reports/
      conversation_history.json
    logs/
    main.py
  frontend/
    streamlit_app.py
  requirements.txt
  README.md
```

## Setup
1. Open PowerShell in the project root:
   ```powershell
   cd "C:\Users\Suresh\Desktop\COP-Final\Finance-Advisor-Agent"
   ```
2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Ensure the LLM endpoint is reachable:
   - Base URL: `http://98.90.16.11:11434/v1`
   - Model default in config: `llama3.2:latest`
5. Runtime mode:
   - Default is AI-first mode (`llm_enabled = True` in `app/config.py`).
   - Strict AI mode is disabled by default (`llm_strict_mode = False`), allowing graceful fallback during LLM outages.

## Run Instructions
1. Start FastAPI from the project root:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. In another terminal, start Streamlit:
   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run frontend/streamlit_app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --browser.gatherUsageStats false
   ```
3. Open:
   - API docs: `http://127.0.0.1:8000/docs`
   - Streamlit UI: `http://localhost:8501`

## API List
- `POST /chat`
- `GET /users`
- `GET /expenses`
- `GET /income`
- `GET /transactions`
- `GET /budgets`
- `GET /goals`
- `POST /upload-csv`
- `GET /health`

## Example Questions
- How much did I spend this month?
- Where am I spending the most money?
- How much can I save?
- Am I exceeding my monthly budget?
- Show my investment summary.
- How much emergency fund do I have?
- Can I afford a vacation costing 50000?
- Suggest ways to reduce expenses.
- Give me a monthly financial report.
- Analyze my spending habits.
- Provide personalized financial advice.
