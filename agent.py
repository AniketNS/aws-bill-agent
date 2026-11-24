import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from tools import DECLARATIONS, TOOLS, send_telegram  # noqa: E402

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_STEPS = 10

SYSTEM = """You are an AWS cost reporting agent. Build a short daily report:
1. Call get_date_info first and use only the dates it returns.
2. Get total spend for the current period and for the same period last month, and the difference (USD and %).
3. Get spend for yesterday (yesterday to today).
4. Get the top 5 services by spend for the current period.
5. Send ONE message via send_telegram. Plain text only (no markdown symbols like * or _), emojis allowed.

Use exactly this layout (fill in the values, keep blank lines and emojis):

📊 AWS Daily Cost Report
🗓 <today, e.g. 24 Nov 2026>

💰 This month so far (<start> → <last day included>)
   $<amount>

📅 Same period last month
   $<amount>

<📈 if spend went up, 📉 if down, ➖ if equal> Change: <+/-$X> (<+/-Y%>)

🕒 Yesterday (<date>): $<amount>

🏆 Top 5 services
1️⃣ <service> — $<amount>
2️⃣ <service> — $<amount>
3️⃣ <service> — $<amount>
4️⃣ <service> — $<amount>
5️⃣ <service> — $<amount>

ℹ️ Cost data can lag up to 24h.

Round to 2 decimals. Shorten service names when obvious (e.g. 'Amazon Elastic Compute Cloud - Compute' -> 'EC2 - Compute'). If last month's amount is 0, write 'n/a' for the percentage."""


def run() -> None:
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options=types.HttpOptions(api_version="v1beta"),
    )
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM,
        tools=[types.Tool(function_declarations=DECLARATIONS)],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    contents = [types.Content(role="user", parts=[types.Part(text="Send me today's AWS cost report.")])]
    sent = False

    for _ in range(MAX_STEPS):
        resp = client.models.generate_content(model=MODEL, contents=contents, config=config)
        contents.append(resp.candidates[0].content)
        calls = resp.function_calls
        if not calls:
            if not sent and resp.text:
                send_telegram(resp.text)
            return

        parts = []
        for call in calls:
            print(f"-> {call.name}({dict(call.args or {})})")
            try:
                result = TOOLS[call.name](**(call.args or {}))
                sent = sent or call.name == "send_telegram"
            except Exception as e:
                result = {"error": str(e)}
            parts.append(types.Part.from_function_response(name=call.name, response={"result": result}))
        contents.append(types.Content(role="user", parts=parts))

    print("Stopped: max steps reached")


if __name__ == "__main__":
    run()
