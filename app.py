import os
import json
from flask import Flask, request, render_template, redirect, send_file
from dotenv import load_dotenv
from openai import OpenAI
from weasyprint import HTML

app = Flask(__name__)
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("✅ Full incoming JSON:", json.dumps(data, indent=2))

    fields = data["data"]["fields"]

    # Extract time fields
    start = next((f["value"] for f in fields if "start" in f["label"].lower()), None)
    end = next((f["value"] for f in fields if "end" in f["label"].lower()), None)

    # Extract workdays
    days_field = next((f for f in fields if f["type"] == "CHECKBOXES" and "days" in f["label"].lower()), None)
    selected_day_ids = days_field["value"] if days_field else []
    day_labels = [opt["text"] for opt in days_field["options"] if opt["id"] in selected_day_ids]

    # Extract sleep issues
    challenge_field = next((f for f in fields if f["type"] == "MULTIPLE_CHOICE" and "challenge" in f["label"].lower()), None)
    challenge_ids = challenge_field["value"] if challenge_field else []
    challenge_labels = [opt["text"] for opt in challenge_field["options"] if opt["id"] in challenge_ids]

    # If required fields are missing, skip processing
    if not start or not end or not day_labels:
        print("⚠️ Missing required fields. Skipping sleep plan generation.")
        return "Missing required input fields. Sleep plan not generated.", 400

    # Prompt for OpenAI
    prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {start}
Shift ends at: {end}
Workdays: {', '.join(day_labels)}
Sleep issues: {', '.join(challenge_labels)}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""
    print("📝 Prompt sent to OpenAI:\n", prompt)

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a compassionate sleep coach and medical expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        sleep_plan = response.choices[0].message.content
        print("💤 Sleep Plan:\n", sleep_plan)
    except Exception as e:
        return f"OpenAI error: {e}", 500

    # Save plan
    with open("last_plan.txt", "w") as f:
        f.write(sleep_plan)

    return redirect("/plan")

@app.route("/plan")
def plan():
    try:
        with open("last_plan.txt", "r") as f:
            sleep_plan = f.read()
    except FileNotFoundError:
        sleep_plan = "No plan found yet. Please fill out the form first."

    return render_template("plan.html", sleep_plan=sleep_plan)

@app.route("/download")
def download():
    try:
        with open("last_plan.txt", "r") as f:
            sleep_plan = f.read()
    except FileNotFoundError:
        return "No sleep plan to download.", 404

    rendered = render_template("pdf_template.html", sleep_plan=sleep_plan)
    HTML(string=rendered).write_pdf("sleep_plan.pdf")
    return send_file("sleep_plan.pdf", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
