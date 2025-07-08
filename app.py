import os
import json
from flask import Flask, request, render_template, redirect
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "your-default-secret-key")
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Ensure plans directory exists
if not os.path.exists("plans"):
    os.makedirs("plans")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/plan")
def show_plan():
    email = request.args.get("email")
    if not email:
        return render_template("plan.html", email=None, plan=None)

    filename = f"plans/{email}.txt"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            plan = f.read()
        return render_template("plan.html", email=email, plan=plan)
    else:
        return render_template("plan.html", email=email, plan=None)


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        print("✅ Full incoming JSON:", json.dumps(data, indent=2))

        fields = data["data"]["fields"]
        start_time = get_value(fields, "question_VPbyQ6")
        end_time = get_value(fields, "question_P9by1x")
        workdays = get_checkbox_labels(fields, "question_ElZYd2")
        sleep_issues = get_option_labels(fields, "question_rOJWaX")
        email = get_value(fields, "question_479dJ5")

        if not email:
            print("❌ Email not found in form data.")
            return "Missing email", 400

        prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {start_time}
Shift ends at: {end_time}
Workdays: {', '.join(workdays)}
Sleep issues: {', '.join(sleep_issues)}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""

        print("📧 Email extracted:", email)
        print("📝 Prompt sent to OpenAI:\n", prompt)

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
        )

        sleep_plan = response["choices"][0]["message"]["content"]

        # Save plan to file
        with open(f"plans/{email}.txt", "w") as f:
            f.write(sleep_plan)

        return redirect(f"/plan?email={email}")
    except Exception as e:
        print("❌ Webhook error:", str(e))
        return "Error processing webhook", 500


@app.route("/debug-files")
def debug_files():
    try:
        files = os.listdir("plans")
        return f"Files in /plans: {files}"
    except Exception as e:
        return f"Error listing plans folder: {str(e)}"


def get_value(fields, key):
    for field in fields:
        if field["key"] == key:
            return field["value"]
    return None


def get_checkbox_labels(fields, checkbox_key):
    for field in fields:
        if field["key"] == checkbox_key and "options" in field:
            return [opt["text"] for opt in field["options"] if opt["id"] in field["value"]]
    return []


def get_option_labels(fields, question_key):
    for field in fields:
        if field["key"] == question_key and "options" in field:
            return [opt["text"] for opt in field["options"] if opt["id"] in field["value"]]
    return []


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)
