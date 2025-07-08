import os
import json
import openai
from flask import Flask, request, render_template, send_file, redirect
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")
tally_webhook_secret = os.environ.get("TALLY_SECRET")

# Ensure the plans directory exists
if not os.path.exists("plans"):
    os.makedirs("plans")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/plan")
def view_plan():
    email = request.args.get("email")
    if not email:
        return render_template("plan.html", email=None, plan=None)

    filepath = f"plans/{email}.txt"
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            plan = f.read()
        return render_template("plan.html", email=email, plan=plan)
    else:
        return render_template("plan.html", email=email, plan=None)

@app.route("/plan/download")
def download_plan():
    email = request.args.get("email")
    if not email:
        return "Email is required to download the plan.", 400

    filepath = f"plans/{email}.txt"
    if not os.path.exists(filepath):
        return "Plan not found.", 404

    return send_file(filepath, as_attachment=True, download_name=f"{email}_sleep_plan.txt")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("✅ Full incoming JSON:", json.dumps(data, indent=2))

        fields = data["data"]["fields"]
        email = ""
        shift_start = ""
        shift_end = ""
        workdays = []
        sleep_issues = ""

        # Parse fields from form
        for field in fields:
            key = field["key"]
            value = field.get("value")

            if key == "question_479dJ5":
                email = value
            elif key == "question_VPbyQ6":
                shift_start = value
            elif key == "question_P9by1x":
                shift_end = value
            elif key == "question_ElZYd2" and isinstance(value, list):
                options = field.get("options", [])
                workdays = [opt["text"] for opt in options if opt["id"] in value]
            elif key == "question_rOJWaX":
                selected_ids = value
                options = field.get("options", [])
                for opt in options:
                    if opt["id"] in selected_ids:
                        sleep_issues = opt["text"]

        print(f"📧 Email extracted: {email}")
        print(f"🕒 Shift: {shift_start} to {shift_end}")
        print(f"📆 Workdays: {', '.join(workdays)}")
        print(f"💤 Sleep Issues: {sleep_issues}")

        # Ensure required info exists
        if not email:
            print("❌ No email found. Aborting.")
            return "Missing email.", 400

        # Create prompt for OpenAI
        prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {shift_start}
Shift ends at: {shift_end}
Workdays: {', '.join(workdays)}
Sleep issues: {sleep_issues}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""
        print("📝 Prompt sent to OpenAI:\n", prompt)

        # Call OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        plan = response.choices[0].message.content

        # Save plan
        plan_path = f"plans/{email}.txt"
        print(f"💾 Saving plan to: {plan_path}")
        try:
            with open(plan_path, "w") as f:
                f.write(plan)
        except Exception as e:
            print(f"❌ Error saving plan: {e}")
            return "Error saving plan.", 500

        # Redirect user
        return redirect(f"/plan?email={email}")

    except Exception as e:
        print("❌ Webhook error:", e)
        return "Internal error", 500

# For Render.com compatibility
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
