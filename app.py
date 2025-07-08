import os
from flask import Flask, request, render_template, redirect, url_for
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "defaultsecret")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Store plans by email in-memory (optional: use a database or file for persistence)
plans = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/plan")
def show_plan():
    email = request.args.get("email", "").strip()
    plan = plans.get(email)

    if not email:
        message = "No email provided."
    elif not plan:
        message = "No plan found yet. Please fill out the form first."
    else:
        message = None

    return render_template("plan.html", email=email, plan=plan, message=message)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("✅ Full incoming JSON:", json.dumps(data, indent=2))

    try:
        fields = data["data"]["fields"]
    except (KeyError, TypeError):
        return "Invalid payload", 400

    form_data = {field["key"]: field for field in fields}

    # Extract values
    shift_start = form_data.get("question_VPbyQ6", {}).get("value", "")
    shift_end = form_data.get("question_P9by1x", {}).get("value", "")
    work_days = [
        opt["text"] for opt in form_data.get("question_ElZYd2", {}).get("options", [])
        if opt["id"] in form_data.get("question_ElZYd2", {}).get("value", [])
    ]
    sleep_issues = [
        opt["text"] for opt in form_data.get("question_rOJWaX", {}).get("options", [])
        if opt["id"] in form_data.get("question_rOJWaX", {}).get("value", [])
    ]
    email = form_data.get("question_479dJ5", {}).get("value", "").strip()
    print("📧 Email extracted:", email)

    if not email:
        return "Email is required", 400

    # Build prompt
    prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {shift_start or 'Unknown'}
Shift ends at: {shift_end or 'Unknown'}
Workdays: {', '.join(work_days) if work_days else 'Not specified'}
Sleep issues: {', '.join(sleep_issues) if sleep_issues else 'Not specified'}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""

    print("📝 Prompt sent to OpenAI:\n", prompt)

    # Call OpenAI
    try:
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a compassionate sleep coach."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        plan_text = chat_response.choices[0].message.content
    except Exception as e:
        print("❌ OpenAI error:", str(e))
        return "Failed to generate sleep plan", 500

    # Store the plan
    plans[email] = plan_text
    print("✅ Sleep plan saved for", email)

    return redirect(url_for("show_plan", email=email))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
