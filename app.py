import os
from flask import Flask, request, render_template, send_file
from dotenv import load_dotenv
import openai
import json
from datetime import datetime
from weasyprint import HTML

load_dotenv()

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_info(payload):
    shift_start = ""
    shift_end = ""
    workdays = []
    sleep_issue = ""
    email = ""

    for field in payload["data"]["fields"]:
        if field["key"] == "question_VPbyQ6":
            shift_start = field["value"]
        elif field["key"] == "question_P9by1x":
            shift_end = field["value"]
        elif field["key"] == "question_ElZYd2":
            workdays = [opt["text"] for opt in field.get("options", []) if opt["id"] in field.get("value", [])]
        elif field["key"] == "question_rOJWaX":
            sleep_issue = next((opt["text"] for opt in field.get("options", []) if opt["id"] in field.get("value", [])), "")
        elif field["key"] == "question_479dJ5":
            email = field["value"]

    return shift_start, shift_end, workdays, sleep_issue, email

def generate_sleep_plan(shift_start, shift_end, workdays, sleep_issue):
    prompt = (
        f"You are a sleep coach helping someone who works night shift.\n"
        f"Their shift is from {shift_start} to {shift_end}.\n"
        f"They work on {', '.join(workdays)}.\n"
        f"Their biggest sleep problem is: {sleep_issue}.\n"
        f"Write a detailed, easy-to-follow night shift sleep plan that addresses their problem. "
        f"Include suggestions for wake/sleep times, environment tips, and how to reset on off days."
    )

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800,
    )

    return response.choices[0].message.content.strip()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/plan")
def plan():
    with open("last_plan.txt", "r") as f:
        sleep_plan = f.read()
    return render_template("plan.html", sleep_plan=sleep_plan)

@app.route("/download-pdf")
def download_pdf():
    with open("last_plan.txt", "r") as f:
        sleep_plan = f.read()
    html = render_template("plan.html", sleep_plan=sleep_plan)
    HTML(string=html).write_pdf("/tmp/sleep_plan.pdf")
    return send_file("/tmp/sleep_plan.pdf", as_attachment=True)

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json()
    shift_start, shift_end, workdays, sleep_issue, email = extract_info(payload)

    print("📅 Shift:", shift_start, "-", shift_end)
    print("🗓️ Workdays:", workdays)
    print("😴 Issue:", sleep_issue)
    print("📧 Email:", email)

    sleep_plan = generate_sleep_plan(shift_start, shift_end, workdays, sleep_issue)

    with open("last_plan.txt", "w") as f:
        f.write(sleep_plan)

    print("✅ GPT Response:", sleep_plan[:300], "...")  # Preview
    return "", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
