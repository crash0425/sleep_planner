import os
import json
from flask import Flask, request, redirect, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import openai

load_dotenv()
app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

PLANS_DIR = "plans"
os.makedirs(PLANS_DIR, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/plan")
def plan():
    email = request.args.get("email")
    if not email:
        return render_template("plan.html", plan=None, email=None)

    safe_email = email.replace("@", "_at_").replace(".", "_")
    plan_path = os.path.join(PLANS_DIR, f"{safe_email}.txt")

    if os.path.exists(plan_path):
        with open(plan_path, "r") as f:
            plan = f.read()
        return render_template("plan.html", plan=plan, email=email)
    else:
        return render_template("plan.html", plan=None, email=email)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("✅ Full incoming JSON:", json.dumps(data, indent=2))

    email = None
    shift_start = None
    shift_end = None
    workdays = []
    sleep_issues = []

    fields = data.get("data", {}).get("fields", [])
    for field in fields:
        label = field.get("label", "").lower()
        if field["type"] == "INPUT_EMAIL":
            email = field.get("value")
        elif "start" in label:
            shift_start = field.get("value")
        elif "end" in label:
            shift_end = field.get("value")
        elif field["type"] == "CHECKBOXES" and "days" in label:
            for option in field.get("options", []):
                if option.get("id") in field.get("value", []):
                    workdays.append(option.get("text"))
        elif field["type"] == "MULTIPLE_CHOICE":
            for option in field.get("options", []):
                if option.get("id") in field.get("value", []):
                    sleep_issues.append(option.get("text"))

    print(f"📧 Email extracted: {email}")
    print(f"📝 Prompt data -> start: {shift_start}, end: {shift_end}, workdays: {workdays}, issues: {sleep_issues}")

    if not email:
        return "No email provided.", 400

    # Build the prompt
    prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {shift_start}
Shift ends at: {shift_end}
Workdays: {', '.join(workdays)}
Sleep issues: {', '.join(sleep_issues)}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    plan_text = response["choices"][0]["message"]["content"]

    # Save plan to a user-specific file
    safe_email = email.replace("@", "_at_").replace(".", "_")
    plan_path = os.path.join(PLANS_DIR, f"{safe_email}.txt")
    with open(plan_path, "w") as f:
        f.write(plan_text)

    return redirect(f"/plan?email={email}")
