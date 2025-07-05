import os
from flask import Flask, request, abort, render_template_string
from dotenv import load_dotenv
import openai
from weasyprint import HTML
from datetime import datetime

load_dotenv()

app = Flask(__name__)

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TALLY_SECRET = os.getenv("TALLY_SECRET")

openai.api_key = OPENAI_API_KEY

# HTML template with download button
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Your Night Shift Sleep Plan</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #0c1b2a;
            color: white;
            max-width: 800px;
            margin: auto;
            padding: 40px;
        }
        h1 { color: #00d4ff; }
        .container { background-color: #112d42; padding: 20px; border-radius: 10px; }
        a.download-button {
            display: inline-block;
            background-color: #00d4ff;
            color: #0c1b2a;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <h1>Your Personalized Sleep Plan</h1>
    <div class="container">
        <p>{{ plan | safe }}</p>
    </div>
    <a class="download-button" href="/download?text={{ plan|urlencode }}" target="_blank">⬇️ Download PDF</a>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return "👋 Sleep Planner is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    # Validate Tally webhook secret
    incoming_secret = request.headers.get("X-Tally-Secret")
    if TALLY_SECRET and incoming_secret != TALLY_SECRET:
        abort(403)

    data = request.get_json()
    fields = data.get("data", {}).get("fields", [])

    # Extract values
    start = next((f["value"] for f in fields if "start" in f["label"].lower()), None)
    end = next((f["value"] for f in fields if "end" in f["label"].lower()), None)
    email = next((f["value"] for f in fields if "email" in f["label"].lower()), None)
    days = []
    for f in fields:
        if "days" in f["label"].lower() and isinstance(f["value"], list):
            options = f.get("options", [])
            days = [o["text"] for o in options if o["id"] in f["value"]]
            break
    issue = next((f.get("options", [{}])[0]["text"] for f in fields if "challenge" in f["label"].lower()), "N/A")

    # Format prompt
    prompt = (
        f"You are a sleep specialist helping night shift workers. "
        f"Their shift is from {start} to {end}. "
        f"They work on: {', '.join(days)}. "
        f"Their biggest sleep challenge is: {issue}. "
        f"Create a 3-part personalized sleep plan that includes (1) a sleep schedule, (2) tips to improve rest, and (3) advice for resetting on off days. "
        f"Be warm, practical, and avoid generic advice."
    )

    # Call OpenAI
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    sleep_plan = response.choices[0].message.content

    return render_template_string(HTML_TEMPLATE, plan=sleep_plan)

@app.route("/download", methods=["GET"])
def download_pdf():
    text = request.args.get("text", "")
    if not text:
        abort(400)
    html = render_template_string(HTML_TEMPLATE, plan=text)
    pdf = HTML(string=html).write_pdf()
    return (
        pdf,
        200,
        {
            "Content-Type": "application/pdf",
            "Content-Disposition": f"attachment; filename=sleep-plan-{datetime.utcnow().isoformat()}.pdf",
        },
    )

if __name__ == "__main__":
    app.run(debug=True, port=10000)
