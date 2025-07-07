import os
from flask import Flask, request, render_template_string
import openai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Sleep Plan</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            max-width: 700px;
            margin: 40px auto;
            background: #f4f4f8;
            padding: 20px;
            border-radius: 10px;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.05);
        }
        .label {
            font-weight: bold;
            color: #555;
        }
    </style>
</head>
<body>
    <h1>Your Personalized AI Sleep Plan</h1>
    <div class="section">
        <p><span class="label">Shift:</span> {{ shift_start }} – {{ shift_end }}</p>
        <p><span class="label">Workdays:</span> {{ workdays|join(', ') }}</p>
        <p><span class="label">Sleep Challenge:</span> {{ challenge }}</p>
        <p><span class="label">Email:</span> {{ email }}</p>
    </div>
    <div class="section">
        <h2>Recommended Sleep Plan</h2>
        <p>{{ plan }}</p>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return "AI Sleep Planner is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        fields = {field['key']: field['value'] for field in data["data"]["fields"]}

        start_time = fields.get("question_VPbyQ6")
        end_time = fields.get("question_P9by1x")
        workdays_ids = fields.get("question_ElZYd2", [])
        challenge = fields.get("question_rOJWaX", [""])[0]
        email = fields.get("question_479dJ5", "")

        workday_lookup = {
            "ebfd0676-3d34-4efa-9eb6-c45329cf313c": "Sunday",
            "321d03c1-e6a7-4533-aec9-810d289502a3": "Monday",
            "e64e11d2-c96f-4d99-9609-cdbc4d1ee0a3": "Tuesday",
            "2e2d5375-c4a7-47eb-a065-216a757ab5fd": "Wednesday",
            "37cad540-bf00-49c5-b529-30e672a9631b": "Thursday",
            "a7ddf202-bc5d-4cb4-9f71-ab9fdadf9276": "Friday",
            "f801558b-89e1-457f-8843-964ef59e3b71": "Saturday"
        }
        workdays = [workday_lookup.get(day_id, "Unknown") for day_id in workdays_ids]

        prompt = f"""
        You are a sleep coach. Create a personalized sleep routine for someone who works night shifts.
        They work from {start_time} to {end_time} on {', '.join(workdays)}.
        Their biggest sleep challenge is: {challenge}.
        Provide a clear, practical routine that includes:
        - Wind-down tips
        - Sleep and wake times
        - How to transition on days off
        """

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a sleep expert helping shift workers sleep better."},
                {"role": "user", "content": prompt}
            ]
        )

        plan_text = response.choices[0].message.content.strip()

        return render_template_string(
            HTML_TEMPLATE,
            shift_start=start_time,
            shift_end=end_time,
            workdays=workdays,
            challenge=challenge,
            email=email,
            plan=plan_text
        )

    except Exception as e:
        return f"❌ ERROR: {e}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
