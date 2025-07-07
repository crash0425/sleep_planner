import os
from flask import Flask, request, render_template, redirect, url_for
from dotenv import load_dotenv
import openai
from weasyprint import HTML

app = Flask(__name__)
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("✅ Full incoming JSON:", data)

    fields = data["data"]["fields"]
    email = None
    start_time = None
    end_time = None
    workdays = []
    sleep_issues = []

    for field in fields:
        key = field["key"]
        value = field["value"]
        if "email" in key.lower():
            email = value
        elif "start" in key.lower():
            start_time = value
        elif "end" in key.lower():
            end_time = value
        elif "work" in key.lower() and isinstance(value, list):
            workdays = value
        elif isinstance(value, list):  # Likely sleep challenge
            sleep_issues = value

    prompt = f"""
    Create a personalized sleep plan for a night shift worker.

    Shift starts at: {start_time}
    Shift ends at: {end_time}
    Workdays: {workdays}
    Sleep issues: {sleep_issues}

    Format it as a clear list with section titles and practical advice. 
    Use language that is warm, clear, and helpful.
    """

    print("📝 Prompt sent to OpenAI:\n", prompt)

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a compassionate sleep coach and medical expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    sleep_plan = response["choices"][0]["message"]["content"]
    print("💤 Sleep Plan:\n", sleep_plan)

    # Save to file so it can be rendered later
    with open("last_plan.txt", "w") as f:
        f.write(sleep_plan)

    return redirect(url_for("plan"))

@app.route("/plan")
def plan():
    try:
        with open("last_plan.txt", "r") as f:
            sleep_plan = f.read()
    except FileNotFoundError:
        sleep_plan = "No plan found yet. Please fill out the form first."

    return render_template("plan.html", sleep_plan=sleep_plan)

@app.route("/download-pdf")
def download_pdf():
    try:
        with open("last_plan.txt", "r") as f:
            sleep_plan = f.read()
    except FileNotFoundError:
        sleep_plan = "No plan found yet. Please fill out the form first."

    html = render_template("pdf_template.html", sleep_plan=sleep_plan)
    pdf = HTML(string=html).write_pdf()
    
    with open("sleep_plan.pdf", "wb") as f:
        f.write(pdf)

    return redirect(url_for("static", filename="sleep_plan.pdf"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
