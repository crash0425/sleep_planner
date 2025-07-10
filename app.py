import os
from flask import Flask, request, render_template, redirect
from dotenv import load_dotenv
import openai
import json

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key")

# Make sure the plans folder exists
os.makedirs("plans", exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/plan")
def show_plan():
    email = request.args.get("email", "").lower()
    filename = os.path.join("plans", f"{email}.txt")

    if os.path.exists(filename):
        with open(filename, "r") as f:
            plan = f.read()
        return render_template("plan.html", plan=plan, email=email)
    else:
        return render_template("plan.html", plan=None, email=email)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        print("✅ Full incoming JSON:", json.dumps(data, indent=2))

        fields = data["data"]["fields"]

        # Extract relevant values
        shift_start = next(f["value"] for f in fields if f["key"] == "question_VPbyQ6")
        shift_end = next(f["value"] for f in fields if f["key"] == "question_P9by1x")
        workdays_ids = next(f["value"] for f in fields if f["key"] == "question_ElZYd2")
        workdays_options = next(f["options"] for f in fields if f["key"] == "question_ElZYd2")
        sleep_issue_ids = next(f["value"] for f in fields if f["key"] == "question_rOJWaX")
        sleep_issue_options = next(f["options"] for f in fields if f["key"] == "question_rOJWaX")
        email = next(f["value"] for f in fields if f["key"] == "question_479dJ5").lower()

        # Convert IDs to labels
        workdays = [opt["text"] for opt in workdays_options if opt["id"] in workdays_ids]
        sleep_issues = [opt["text"] for opt in sleep_issue_options if opt["id"] in sleep_issue_ids]

        prompt = f"""
        Create a personalized sleep plan for a night shift worker.
        Shift starts at: {shift_start}
        Shift ends at: {shift_end}
        Workdays: {', '.join(workdays)}
        Sleep issues: {', '.join(sleep_issues)}
        Format it as a clear list with section titles and practical advice. 
        Use language that is warm, clear, and helpful.
        """

        print(f"📧 Email extracted: {email}")
        print(f"📝 Prompt sent to OpenAI:\n{prompt.strip()}")

        # Chat completion
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        plan_text = response.choices[0].message.content.strip()

        # Save plan to file
        filepath = os.path.join("plans", f"{email}.txt")
        with open(filepath, "w") as f:
            f.write(plan_text)
        print(f"✅ Sleep plan saved to: {filepath}")

        return redirect(f"/plan?email={email}")

    except Exception as e:
        print("❌ Webhook error:", str(e))
        return "Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
