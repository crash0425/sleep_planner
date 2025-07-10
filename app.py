import os
import openai
from flask import Flask, request, render_template, redirect
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Ensure plans directory exists
PLANS_DIR = "plans"
os.makedirs(PLANS_DIR, exist_ok=True)

def extract_field(fields, key, fallback=""):
    for field in fields:
        if field.get("key") == key:
            return field.get("value", fallback)
    return fallback

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/plan")
def plan():
    email = request.args.get("email", "").lower()
    if not email:
        return render_template("plan.html", plan="No email provided.")

    plan_path = os.path.join(PLANS_DIR, f"{email}.txt")
    if not os.path.exists(plan_path):
        return render_template("plan.html", plan="No plan found yet. Please fill out the form first.")

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = f.read()

    return render_template("plan.html", plan=plan)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json.get("data", {})
        fields = data.get("fields", [])

        start_time = extract_field(fields, "question_VPbyQ6")
        end_time = extract_field(fields, "question_P9by1x")
        workdays_ids = extract_field(fields, "question_ElZYd2", [])
        sleep_issue_ids = extract_field(fields, "question_rOJWaX", [])
        email = extract_field(fields, "question_479dJ5").lower()

        # Extract workday/sleep issue text from options
        workday_text = []
        sleep_issue_text = []

        for field in fields:
            if field.get("key") == "question_ElZYd2":
                id_to_text = {opt["id"]: opt["text"] for opt in field.get("options", [])}
                workday_text = [id_to_text.get(i, i) for i in workdays_ids]

            if field.get("key") == "question_rOJWaX":
                id_to_text = {opt["id"]: opt["text"] for opt in field.get("options", [])}
                sleep_issue_text = [id_to_text.get(i, i) for i in sleep_issue_ids]

        # Build the prompt
        prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {start_time}
Shift ends at: {end_time}
Workdays: {', '.join(workday_text)}
Sleep issues: {', '.join(sleep_issue_text)}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""

        print(f"📧 Email extracted: {email}")
        print(f"📝 Prompt sent to OpenAI:\n{prompt.strip()}")

        # Call OpenAI
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful sleep coach for shift workers."},
                {"role": "user", "content": prompt}
            ]
        )

        sleep_plan = response.choices[0].message.content.strip()

        # Save plan
        plan_path = os.path.join(PLANS_DIR, f"{email}.txt")
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(sleep_plan)

        print(f"✅ Sleep plan saved to: {plan_path}")
        return redirect(f"/plan?email={email}", code=302)

    except Exception as e:
        print("❌ Webhook error:", str(e))
        return "Webhook error", 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
