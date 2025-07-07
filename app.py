import os
import json
from flask import Flask, request, render_template_string, send_file
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
from weasyprint import HTML

load_dotenv()

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LANDING_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Sleep Planner for Night Shift</title>
    <style>
        body {
            font-family: sans-serif;
            background-color: #0c1e2c;
            color: #ffffff;
            text-align: center;
            padding: 50px;
        }
        .container {
            max-width: 600px;
            margin: auto;
            background: #1c3a4d;
            padding: 30px;
            border-radius: 10px;
        }
        a.button {
            display: inline-block;
            background: #00bcd4;
            color: #fff;
            padding: 12px 24px;
            border-radius: 5px;
            text-decoration: none;
            margin-top: 20px;
        }
        a.button:hover {
            background: #0097a7;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛌 AI Sleep Planner</h1>
        <p>Your personalized sleep plan has been created.</p>
        <a href="/download" class="button">📥 Download Sleep Plan PDF</a>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(LANDING_HTML)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("✅ Full incoming JSON:", json.dumps(data, indent=2))

    try:
        fields = data["data"]["fields"]
        shift_start = next(f for f in fields if f["key"] == "question_VPbyQ6")["value"]
        shift_end = next(f for f in fields if f["key"] == "question_P9by1x")["value"]
        days_worked = next(f for f in fields if f["key"] == "question_ElZYd2")["value"]
        sleep_issue = next(f for f in fields if f["key"] == "question_rOJWaX")["options"][0]["text"]
        email = next(f for f in fields if f["key"] == "question_479dJ5")["value"]
    except Exception as e:
        return f"Error parsing fields: {e}", 400

    prompt = f"""
You are a sleep expert. Based on this info, write a 1-page personalized night shift sleep plan:
- Shift: {shift_start} to {shift_end}
- Workdays: {days_worked}
- Sleep issues: {sleep_issue}
- Email: {email}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    sleep_plan_text = response.choices[0].message.content.strip()

    HTML(string=f"<h1>AI Sleep Plan</h1><p>{sleep_plan_text.replace('\n', '<br>')}</p>").write_pdf("sleep_plan.pdf")

    return "✅ Plan generated and PDF saved.", 200

@app.route("/download")
def download():
    if os.path.exists("sleep_plan.pdf"):
        return send_file("sleep_plan.pdf", as_attachment=True)
    else:
        return "❌ No sleep plan PDF found. Submit the form first.", 404

if __name__ == "__main__":
    app.run(debug=True, port=10000)
