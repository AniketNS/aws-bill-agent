import os
from datetime import date, timedelta

import boto3
import requests

ce = boto3.client("ce", region_name="us-east-1")


def _shift_month(d: date, months: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 + months, 12)
    m += 1
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    last_day = (nxt - timedelta(days=1)).day
    return date(y, m, min(d.day, last_day))


def get_date_info() -> dict:
    today = date.today()
    start = today.replace(day=1)
    if today.day == 1:
        start = _shift_month(start, -1)
    return {
        "today": str(today),
        "yesterday": str(today - timedelta(days=1)),
        "current_period_start": str(start),
        "current_period_end_exclusive": str(today),
        "last_month_period_start": str(_shift_month(start, -1)),
        "last_month_period_end_exclusive": str(_shift_month(today, -1)),
    }


def get_cost(start_date: str, end_date: str) -> dict:
    r = ce.get_cost_and_usage(
        TimePeriod={"Start": start_date, "End": end_date},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    total = sum(float(x["Total"]["UnblendedCost"]["Amount"]) for x in r["ResultsByTime"])
    return {"start": start_date, "end_exclusive": end_date, "total_usd": round(total, 2)}


def get_top_services(start_date: str, end_date: str, n: int = 5) -> dict:
    costs: dict[str, float] = {}
    token = None
    while True:
        kwargs = dict(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        if token:
            kwargs["NextPageToken"] = token
        r = ce.get_cost_and_usage(**kwargs)
        for period in r["ResultsByTime"]:
            for g in period["Groups"]:
                amt = float(g["Metrics"]["UnblendedCost"]["Amount"])
                costs[g["Keys"][0]] = costs.get(g["Keys"][0], 0) + amt
        token = r.get("NextPageToken")
        if not token:
            break
    top = sorted(costs.items(), key=lambda kv: kv[1], reverse=True)[: int(n)]
    return {"top_services": [{"service": k, "usd": round(v, 2)} for k, v in top]}


def send_telegram(message: str) -> dict:
    r = requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
        json={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": message[:4096]},
        timeout=15,
    )
    r.raise_for_status()
    return {"sent": True}


TOOLS = {
    "get_date_info": get_date_info,
    "get_cost": get_cost,
    "get_top_services": get_top_services,
    "send_telegram": send_telegram,
}

_DATE = {"type": "STRING", "description": "YYYY-MM-DD"}
DECLARATIONS = [
    {
        "name": "get_date_info",
        "description": "Get today's date and the exact date ranges to use for the current period and the same period last month.",
    },
    {
        "name": "get_cost",
        "description": "Total AWS spend in USD between start_date (inclusive) and end_date (exclusive).",
        "parameters": {
            "type": "OBJECT",
            "properties": {"start_date": _DATE, "end_date": _DATE},
            "required": ["start_date", "end_date"],
        },
    },
    {
        "name": "get_top_services",
        "description": "Top N AWS services by spend between start_date (inclusive) and end_date (exclusive).",
        "parameters": {
            "type": "OBJECT",
            "properties": {"start_date": _DATE, "end_date": _DATE, "n": {"type": "INTEGER"}},
            "required": ["start_date", "end_date"],
        },
    },
    {
        "name": "send_telegram",
        "description": "Send the final report to the user on Telegram. Call this once at the end.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"message": {"type": "STRING"}},
            "required": ["message"],
        },
    },
]
