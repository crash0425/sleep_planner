from flask import Flask, request, render_template_string, send_file
from weasyprint import HTML
from io import BytesIO
import json
import datetime

app = Flask(__name__)

@app.route('/', methods=['GET'])
def landing_page():
    return "✅ AI Sleep Planner is running."

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print("✅ Full incoming JSON:", json.dumps(data, indent=2))

        # Extract relevant form responses
        fields = data['data']['fields']
        shift_start = next(f['value'] for f in fields if 'start your shift' in f['label'].lower())
        shift_end = next(f['value'] for f in fields if 'shift end' in f['label'].lower())
        days_worked_ids = next(f['value'] for f in fields if f['key'].startswith('question_ElZYd2') and isinstance(f['value'], list))
        days_options = next(f['options'] for f in fields if f['key'].startswith('question_ElZYd2') and isinstance(f['value'], list))
        days_worked = [opt['text'] for opt in days_options if opt['id'] in days_worked_ids]
        challenge = next(f['options'] for f in fields if 'sleep challenge' in f['label'].lower())
        selected_challenge_id = next(f['value'][0] for f in fields if 'sleep challenge' in f['label'].lower())
        challenge_text = next(opt['text'] for opt in challenge if opt['id'] == selected_challenge_id)
        email = next(f['value'] for f in fields if f['type'] == 'INPUT_EMAIL')

        print(f"📅 Shift: {shift_start} - {shift_end}")
        print(f"🗓️ Workdays: {days_worked}")
        print(f"😴 Issue: {challenge_text}")
        print(f"📧 Email: {email}")

        sleep_plan_html = render_template_string(SLEEP_PLAN_TEMPLATE,
                                                 shift_start=shift_start,
                                                 shift_end=shift_end,
                                                 days_worked=", ".join(days_worked),
                                                 challenge=challenge_text,
                                                 email=email)

        pdf_file = HTML(string=sleep_plan_html).write_pdf()
        buffer = BytesIO(pdf_file)

        # Save PDF in memory and serve download link
        pdf_storage[email] = buffer
        return sleep_plan_html

    except Exception as e:
        print("❌ ERROR:", e)
        return "❌ Failed to generate sleep plan", 500


@app.route('/download/<email>')
def download_pdf(email):
    buffer = pdf_storage.get(email)
    if not buffer:
        return "❌ PDF not found", 404
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='sleep_plan.pdf', mimetype='application/pdf')

# Temporary in-memory storage
pdf_storage = {}

# Basic HTML template for the sleep plan (landing page style)
SLEEP_PLAN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Your Personalized Sleep Plan</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f0f4f8;
            margin: 0;
            padding: 2rem;
            color: #333;
        }
        .container {
            background: white;
            max-width: 700px;
            margin: auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
        }
        a.button {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #2c3e50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
        .info {
            margin-bottom: 20px;
        }
        ul {
            margin-left: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛌 Your Personalized AI Sleep Plan</h1>
        <div class="info">
            <strong>Shift:</strong> {{ shift_start }} – {{ shift_end }}<br>
            <strong>Workdays:</strong> {{ days_worked }}<br>
            <strong>Sleep Issue:</strong> {{ challenge }}<br>
            <strong>Email:</strong> {{ email }}
        </div>
        <h2>📋 Sleep Routine</h2>
        <ul>
            <li>Go to sleep around 1–2 hours after your shift ends (~13:00).</li>
            <li>Wake up around 21:00 to align with your night shift schedule.</li>
            <li>Take a short 20–30 minute nap before your shift if needed.</li>
        </ul>
        <h2>🧘 Wind-Down Routine</h2>
        <ul>
            <li>Avoid screens and bright light before bed.</li>
            <li>Try relaxing habits like reading, meditation, or warm showers.</li>
            <li>Make your room dark and quiet using curtains, masks, or white noise.</li>
        </ul>
        <h2>🔁 Resetting on Days Off</h2>
        <ul>
            <li>Keep your sleep times consistent, or shift them gradually.</li>
            <li>Get bright light in the morning, dim lights in the evening.</li>
            <li>Do light exercise and avoid heavy meals near bedtime.</li>
        </ul>
        <a class="button" href="/download/{{ email }}">⬇️ Download PDF</a>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
