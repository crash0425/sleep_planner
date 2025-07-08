import os
import json
from flask import Flask, request, render_template, redirect
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Set secret key for session handling
app.secret_key = os.getenv("FLASK_SECRET_KEY", "changeme")

# Setup OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Ensure the plans folder exists
os.makedirs("plans", exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/plan")
def plan():
    email = request.args.get("email")
    if not email:
        return render_template("plan.html", plan="No email provided.")

    plan_path = f"plans/{email}.txt"
    if os.path.exists(plan_path):
        with open(plan_path, "r") as f:
            sleep_plan = f.read()
    else:
        sleep_plan = "No plan found yet. Please fill out the form first."

    return render_template("plan.html", plan=sleep_plan)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("✅ Full incoming JSON:", json.dumps(data, indent=2))

        fields = data["data"]["fields"]
        form_data = {field["key"]: field for field in fields}

        start_time = form_data.get("question_VPbyQ6", {}).get("value", "None")
        end_time = form_data.get("question_P9by1x", {}).get("value", "None")

        weekdays_raw = form_data.get("question_ElZYd2", {}).get("options", [])
        weekdays_ids = form_data.get("question_ElZYd2", {}).get("value", [])
        weekdays = [opt["text"] for opt in weekdays_raw if opt["id"] in weekdays_ids]

        sleep_issue_ids = form_data.get("question_rOJWaX", {}).get("value", [])
        sleep_issue_opts = form_data.get("question_rOJWaX", {}).get("options", [])
        sleep_issues = [opt["text"] for opt in sleep_issue_opts if opt["id"] in sleep_issue_ids]

        email = form_data.get("question_479dJ5", {}).get("value", "").strip()

        prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {start_time}
Shift ends at: {end_time}
Workdays: {', '.join(weekdays)}
Sleep issues: {', '.join(sleep_issues)}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""

        print("📝 Prompt sent to OpenAI:\n", prompt)

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a sleep coach for shift workers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        sleep_plan = response.choices[0].message.content.strip()

        # Save to file
        if email:
            with open(f"plans/{email}.txt", "w") as f:
                f.write(sleep_plan)

        return redirect(f"/plan?email={email}")

    except Exception as e:
        print("❌ Error in webhook:", str(e))
        return "Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
