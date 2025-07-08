import os
import json
from flask import Flask, request, render_template, redirect, url_for, send_file
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from weasyprint import HTML

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "defaultsecret")
CORS(app)

openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/plan")
def plan():
    try:
        with open("last_plan.txt", "r") as f:
            plan_text = f.read()
    except FileNotFoundError:
        plan_text = "No plan found yet. Please fill out the form first."
    return render_template("plan.html", plan=plan_text)

@app.route("/download")
def download_pdf():
    try:
        with open("last_plan.txt", "r") as f:
            plan_text = f.read()
    except FileNotFoundError:
        plan_text = "No plan found yet."

    rendered = render_template("pdf_template.html", plan=plan_text)
    HTML(string=rendered).write_pdf("plan.pdf")
    return send_file("plan.pdf", as_attachment=True)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("✅ Full incoming JSON:", json.dumps(data, indent=2))

    fields = data["data"]["fields"]
    field_map = {f["key"]: f["value"] for f in fields}

    shift_start = field_map.get("question_VPbyQ6", "Unknown")
    shift_end = field_map.get("question_P9by1x", "Unknown")

    # Workdays parsing
    weekdays_lookup = {
        "ebfd0676-3d34-4efa-9eb6-c45329cf313c": "Sunday",
        "321d03c1-e6a7-4533-aec9-810d289502a3": "Monday",
        "e64e11d2-c96f-4d99-9609-cdbc4d1ee0a3": "Tuesday",
        "2e2d5375-c4a7-47eb-a065-216a757ab5fd": "Wednesday",
        "37cad540-bf00-49c5-b529-30e672a9631b": "Thursday",
        "a7ddf202-bc5d-4cb4-9f71-ab9fdadf9276": "Friday",
        "f801558b-89e1-457f-8843-964ef59e3b71": "Saturday"
    }

    raw_days = field_map.get("question_ElZYd2", [])
    workdays = [weekdays_lookup.get(day, day) for day in raw_days]
    sleep_issues_ids = field_map.get("question_rOJWaX", [])
    sleep_issues_map = {
        "ae2dc1d9-16e7-4643-8af2-7349da2fd10a": "Falling asleep",
        "abc0482e-ddbe-4411-b672-91c12c7e96d5": "Staying asleep",
        "bc9c0553-5505-4bec-a453-de6cebccf457": "Waking too early",
        "1e69b4d3-76e7-4a6d-a298-0aca371fcf9a": "All of the above"
    }
    sleep_issues = [sleep_issues_map.get(issue, issue) for issue in sleep_issues_ids]

    prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {shift_start}
Shift ends at: {shift_end}
Workdays: {", ".join(workdays)}
Sleep issues: {", ".join(sleep_issues)}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""

    print("📝 Prompt sent to OpenAI:\n", prompt)

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    sleep_plan = response.choices[0].message.content.strip()

    with open("last_plan.txt", "w") as f:
        f.write(sleep_plan)

    return redirect(url_for("plan"))

if __name__ == "__main__":
    app.run(debug=True)
