import os
from flask import Flask, request, redirect, render_template
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
CORS(app)

LAST_PLAN_FILE = "last_plan.txt"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("✅ Full incoming JSON:", json.dumps(data, indent=2))

    try:
        fields = data["data"]["fields"]
    except KeyError:
        print("❌ Missing 'fields' in JSON payload.")
        return "Invalid data", 400

    # Extract shift start and end
    shift_start = next((f["value"] for f in fields if f["key"] == "question_VPbyQ6"), None)
    shift_end = next((f["value"] for f in fields if f["key"] == "question_P9by1x"), None)

    # Extract workdays
    workdays_field = next((f for f in fields if f["key"] == "question_ElZYd2"), None)
    workdays = []
    if workdays_field:
        id_to_day = {opt["id"]: opt["text"] for opt in workdays_field.get("options", [])}
        workdays = [id_to_day[wid] for wid in workdays_field.get("value", []) if wid in id_to_day]

    # Extract sleep issues
    issues_field = next((f for f in fields if f["key"] == "question_rOJWaX"), None)
    sleep_issues = []
    if issues_field:
        id_to_issue = {opt["id"]: opt["text"] for opt in issues_field.get("options", [])}
        sleep_issues = [id_to_issue[iid] for iid in issues_field.get("value", []) if iid in id_to_issue]

    if not (shift_start and shift_end and workdays and sleep_issues):
        print("❌ Missing required info. Skipping plan generation.")
        return redirect("/plan")

    # Build prompt
    prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {shift_start}
Shift ends at: {shift_end}
Workdays: {', '.join(workdays)}
Sleep issues: {', '.join(sleep_issues)}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""

    print("📝 Prompt sent to OpenAI:\n", prompt)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    sleep_plan = response.choices[0].message.content.strip()

    with open(LAST_PLAN_FILE, "w", encoding="utf-8") as f:
        f.write(sleep_plan)

    return redirect("/plan")

@app.route("/plan")
def plan():
    if not os.path.exists(LAST_PLAN_FILE):
        return render_template("plan.html", sleep_plan=None)
    
    with open(LAST_PLAN_FILE, "r", encoding="utf-8") as f:
        sleep_plan = f.read()

    return render_template("plan.html", sleep_plan=sleep_plan)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
