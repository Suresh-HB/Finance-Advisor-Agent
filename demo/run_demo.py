from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8000"


def get_json(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    print_section("Finance Advisor Demo")
    print("Starting API walkthrough...")

    try:
        health = get_json("/health")
        print_section("1) Health Check")
        print(json.dumps(health, indent=2))

        users = get_json("/users")
        print_section("2) Users")
        print(json.dumps(users, indent=2))

        expenses = get_json("/expenses?user_id=1")
        print_section("3) Expenses (User 1)")
        print(f"Rows: {len(expenses.get('data', []))}")
        if expenses.get("data"):
            print("Sample:")
            print(json.dumps(expenses["data"][0], indent=2))

        savings = get_json("/savings?user_id=1")
        print_section("4) Savings (User 1)")
        print(f"Rows: {len(savings.get('data', []))}")
        if savings.get("data"):
            print("Latest:")
            print(json.dumps(savings["data"][-1], indent=2))

        prompt_1 = {
            "user_id": 1,
            "message": "How much did I spend this month and where am I overspending?",
        }
        start = time.time()
        chat_1 = post_json("/chat", prompt_1)
        elapsed_1 = round(time.time() - start, 2)

        print_section("5) Chat Demo: Spending Analysis")
        print(f"Latency: {elapsed_1}s")
        print("Answer:")
        print(chat_1.get("answer", ""))
        print("Analysis Keys:", list((chat_1.get("analysis") or {}).keys()))

        prompt_2 = {
            "user_id": 1,
            "message": "Can I afford a vacation costing 50000 this month?",
        }
        start = time.time()
        chat_2 = post_json("/chat", prompt_2)
        elapsed_2 = round(time.time() - start, 2)

        print_section("6) Chat Demo: Affordability")
        print(f"Latency: {elapsed_2}s")
        print("Answer:")
        print(chat_2.get("answer", ""))
        print("Analysis Keys:", list((chat_2.get("analysis") or {}).keys()))

        print_section("Demo Complete")
        print("Project is running correctly.")
        print("Next: open http://localhost:8501 for Streamlit dashboard.")

    except urllib.error.URLError as exc:
        print_section("Demo Failed")
        print("Could not connect to API.")
        print("Start backend first:")
        print(
            "c:/Users/Suresh/Desktop/COP-Final/Finance-Advisor-Agent/.venv/Scripts/python.exe -m uvicorn "
            "app.main:app --host 127.0.0.1 --port 8000 --app-dir "
            "c:/Users/Suresh/Desktop/COP-Final/Finance-Advisor-Agent"
        )
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
