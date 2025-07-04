from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

@app.route("/")
def home():
    return "Sleep Planner is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        fields = data.get("data", {}).get("fields", [])

        start_time = next((f["value"] for f in fields if "start" in f["label"].lower()), None)
        end_time = next((f["value"] for f in fields if "end" in f["label"].lower()), None)
        sleep_issue = next((f["value"][0] if isinstance(f["value"], list) else f["value"]
                           for f in fields if "sleep challenge" in f["label"].lower()), None)
        email = next((f["value"] for f in fields if "email" in f["label"].lower()), None)

        prompt = f"""You are an expert sleep coach. Create a night shift sleep optimization plan.
        - Shift Start: {start_time}
        - Shift End: {end_time}
        - Main Issue: {sleep_issue}
        Output a bullet list plan."""

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={
                "model": "mistralai/mixtral-8x7b",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500
            }
        )

        sleep_plan = response.json()["choices"][0]["message"]["content"]

        # Send the sleep plan back to the user
        send_email(email, "Your Night Shift Sleep Plan", sleep_plan)

        return jsonify({"message": "Success", "plan": sleep_plan})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import smtplib
from email.message import EmailMessage

def send_email(to, subject, content):
    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
