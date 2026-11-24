import os
import time
import traceback
from datetime import datetime, timedelta

from agent import run

REPORT_TIME = os.getenv("REPORT_TIME", "09:00")
RUN_ON_START = os.getenv("RUN_ON_START", "false").lower() == "true"


def next_run() -> datetime:
    h, m = map(int, REPORT_TIME.split(":"))
    now = datetime.now()
    t = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return t if t > now else t + timedelta(days=1)


def safe_run() -> None:
    try:
        run()
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    print(f"Scheduler started. Daily report at {REPORT_TIME} ({os.getenv('TZ', 'UTC')})", flush=True)
    if RUN_ON_START:
        safe_run()
    while True:
        t = next_run()
        print(f"Next run: {t:%Y-%m-%d %H:%M}", flush=True)
        time.sleep(max((t - datetime.now()).total_seconds(), 1))
        safe_run()
