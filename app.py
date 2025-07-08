import os
import json
from flask import Flask, request, redirect, render_template, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import openai
from jinja2 import Template
from weasyprint import HTML

app = Flask(__name__)
CORS(app)
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set folder for saved plans
PLANS_DIR = "plans"
os.makedirs(PLANS_DIR, exist_ok=True)

# Simple in-memory storage for mapping email to latest plan file
user_plans = {}

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/plan", methods=["GET"])
def plan():
    latest_email = list(user_plans.keys())[-1] if user_plans else None
    if not latest_email:
        return render_template("plan.html", email=None, plan=None)

    latest_plan_path = user_plans[latest_email]
    if not os.path.exists(latest_plan_path):
        return render_template("plan.html", email=latest_email, plan=None)

    with open(latest_plan_path, "r") as f:
        content = f.read()
    return render_template("plan.html", email=latest_email, plan=content)

@app.route("/download", methods=["GET"])
def download_pdf():
    latest_email = list(user_plans.keys())[-1] if user_plans else None
    if not latest_email:
        return "No plan found", 404

    txt_path = user_plans[latest_email]
    if not os.path.exists(txt_path):
        return "No plan found", 404

    with open(txt_path, "r") as f:
        plan_text = f.read()

    html = render_template("pdf_template.html", plan_text=plan_text)
    pdf_path = txt_path.replace(".txt", ".pdf")
    HTML(string=html).write_pdf(pdf_path)

    return send_file(pdf_path, as_attachment=True)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("✅ Full incoming JSON:", json.dumps(data, indent=2))

    try:
        fields = data["data"]["fields"]
        answers = {f["key"]: f["value"] for f in fields}

        start = answers.get("question_VPbyQ6", "N/A")
        end = answers.get("question_P9by1x", "N/A")
        sleep_issue = next(
            (o["text"] for f in fields if f["key"] == "question_rOJWaX" for o in f.get("options", []) if o["id"] in f["value"]), "N/A"
        )
        work_days = [
            o["text"] for f in fields if f["key"] == "question_ElZYd2"
            for o in f.get("options", []) if o["id"] in f["value"]
        ]
        email = next((f["value"] for f in fields if f["key"] == "question_479dJ5"), None)

        prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {start}
Shift ends at: {end}
Workdays: {", ".join(work_days)}
Sleep issues: {sleep_issue}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""

        print("📧 Email extracted:", email)
        print("📝 Prompt sent to OpenAI:\n", prompt)

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        plan_text = response.choices[0].message.content.strip()

        if email:
            safe_email = email.replace("@", "_at_").replace(".", "_")
            file_path = os.path.join(PLANS_DIR, f"{safe_email}.txt")
            with open(file_path, "w") as f:
                f.write(plan_text)
            user_plans[email] = file_path

    except Exception as e:
        print("❌ Error processing webhook:", e)

    return redirect("/plan")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
