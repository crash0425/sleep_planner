import os
from flask import Flask, request, render_template, redirect, url_for
import openai
import json
import traceback

app = Flask(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")

# Make sure this folder exists
PLANS_DIR = "plans"
os.makedirs(PLANS_DIR, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/plan")
def show_plan():
    email = request.args.get("email")
    if not email:
        return "Missing email", 400

    plan_path = os.path.join(PLANS_DIR, f"{email}.txt")
    if not os.path.exists(plan_path):
        return render_template("plan.html", plan=None)

    with open(plan_path, "r") as f:
        plan = f.read()
    return render_template("plan.html", plan=plan)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        payload = request.get_json()
        print("✅ Full incoming JSON:", json.dumps(payload, indent=2))

        fields = payload["data"]["fields"]

        # Print all field keys and values for debugging
        for f in fields:
            print(f"Key: {f['key']}, Value: {f.get('value')}")

        # Extract values
        email = next(f for f in fields if f["key"] == "question_479dJ5")["value"]
        shift_start = next(f for f in fields if f["key"] == "question_VPbyQ6")["value"]
        shift_end = next(f for f in fields if f["key"] == "question_P9by1x")["value"]
        workdays = next(f for f in fields if f["key"] == "question_ElZYd2")["options"]
        sleep_issues = next(f for f in fields if f["key"] == "question_rOJWaX")["options"]

        workdays_text = ", ".join([d["text"] for d in workdays])
        sleep_issues_text = ", ".join([s["text"] for s in sleep_issues])

        # Build prompt
        prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {shift_start}
Shift ends at: {shift_end}
Workdays: {workdays_text}
Sleep issues: {sleep_issues_text}
Format it as a clear list with section titles and practical advice.
Use language that is warm, clear, and helpful.
"""

        print("📝 Prompt sent to OpenAI:\n", prompt)

        # Call OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a sleep coach who helps night shift workers."},
                {"role": "user", "content": prompt}
            ]
        )

        plan_text = response.choices[0].message["content"]

        # Save to file
        with open(os.path.join(PLANS_DIR, f"{email}.txt"), "w") as f:
            f.write(plan_text)

        print(f"✅ Plan saved for {email}")
        return redirect(f"/plan?email={email}")

    except Exception as e:
        print("❌ Webhook error:", str(e))
        traceback.print_exc()
        return "Error", 500

if __name__ == "__main__":
    app.run(debug=True, port=10000)
