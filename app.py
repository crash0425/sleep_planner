import os
import json
from flask import Flask, request, render_template, redirect
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

# Load .env if running locally
load_dotenv()

app = Flask(__name__)
CORS(app)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

PLAN_FOLDER = "plans"
os.makedirs(PLAN_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/plan")
def plan():
    email = request.args.get("email", "").strip().lower()
    if not email:
        return "No email provided.", 400

    filename = os.path.join(PLAN_FOLDER, f"{email}.txt")
    if os.path.exists(filename):
        with open(filename, "r") as f:
            plan_text = f.read()
        return render_template("plan.html", email=email, plan=plan_text)
    else:
        return render_template("plan.html", email=email, plan=None)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("✅ Full incoming JSON:", json.dumps(data, indent=2))

        # Extract form fields
        fields = data["data"]["fields"]
        field_map = {field["key"]: field for field in fields}

        start = field_map["question_VPbyQ6"]["value"]
        end = field_map["question_P9by1x"]["value"]
        days_raw = field_map["question_ElZYd2"]["options"]
        selected_ids = field_map["question_ElZYd2"]["value"]
        issue_id = field_map["question_rOJWaX"]["value"][0]
        email = field_map["question_479dJ5"]["value"].strip().lower()

        days = [d["text"] for d in days_raw if d["id"] in selected_ids]
        issue_text = next((i["text"] for i in field_map["question_rOJWaX"]["options"] if i["id"] == issue_id), "N/A")

        print("📧 Email extracted:", email)

        prompt = (
            f"Create a personalized sleep plan for a night shift worker.\n"
            f"Shift starts at: {start}\n"
            f"Shift ends at: {end}\n"
            f"Workdays: {', '.join(days)}\n"
            f"Sleep issues: {issue_text}\n"
            f"Format it as a clear list with section titles and practical advice. "
            f"Use language that is warm, clear, and helpful."
        )

        print("📝 Prompt sent to OpenAI:\n", prompt)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful sleep coach."},
                {"role": "user", "content": prompt}
            ]
        )

        plan_text = response.choices[0].message.content.strip()

        # Save the plan
        filename = os.path.join(PLAN_FOLDER, f"{email}.txt")
        with open(filename, "w") as f:
            f.write(plan_text)

        print("✅ Plan saved:", filename)
        return redirect(f"/plan?email={email}")

    except Exception as e:
        print("❌ Webhook error:\n", e)
        return "Internal server error", 500

# Optional: Debug endpoint to see saved plans
@app.route("/debug-files")
def debug_files():
    return "<br>".join(os.listdir(PLAN_FOLDER))
