# AWS Bill Agent

Sends a daily AWS cost report to Telegram: month-to-date vs same period last month, yesterday's spend, and the top 5 services. Uses Gemini for tool calling and Cost Explorer for data.

## Requirements

- Gemini API key from https://aistudio.google.com/apikey (starts with `AIza`)
- AWS access key with `ce:GetCostAndUsage`, and Cost Explorer enabled on the account
- Telegram bot token (from @BotFather, format `123456789:AAF...`) and your numeric chat ID

## Run with Docker

```bash
cp .env.example .env    # fill in the values
docker compose up -d --build
docker compose logs -f
```

Set `REPORT_TIME` (HH:MM) and `TZ` (e.g. `Asia/Kolkata`) in `.env`. `RUN_ON_START=true` sends one report immediately on startup, handy for testing.

## Run without Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python agent.py            # one report now
python scheduler.py        # daily loop
```
