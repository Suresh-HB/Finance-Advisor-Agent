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
1. Create and activate a Python 3.12+ virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure the LLM endpoint is reachable:
   - Base URL: `http://34.207.216.209:11434/v1`
   - Model default in config: `llama3.2:latest`
4. Runtime mode:
   - Default is AI-first mode (`llm_enabled = True` in `app/config.py`).
   - Strict AI mode is enabled by default (`llm_strict_mode = True`), so chat responses are generated through the configured LLM path and silent deterministic fallback is minimized.
   - To allow deterministic fallback during LLM outages, set `llm_strict_mode = False`.

## Run Instructions
1. Start FastAPI:
   ```bash
   uvicorn app.main:app --reload
   ```
2. In another terminal, start Streamlit:
   ```bash
   streamlit run frontend/streamlit_app.py
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
