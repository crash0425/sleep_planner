import os
import json
from flask import Flask, request, render_template_string, send_file
from datetime import datetime
from io import BytesIO
from jinja2 import Template
from weasyprint import HTML

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Personalized Sleep Plan</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f7f9;
            margin: 0;
            padding: 2rem;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 2rem;
            max-width: 700px;
            margin: auto;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2b2d42;
        }
        p, li {
            font-size: 16px;
            line-height: 1.6;
        }
        .section {
            margin-bottom: 2rem;
        }
        .download {
            text-align: center;
            margin-top: 2rem;
        }
        .download a {
            display: inline-block;
            background: #007bff;
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 5px;
            text-decoration: none;
            transition: background 0.3s;
        }
        .download a:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Your Personalized Sleep Plan</h1>
        <div class="section">
            <strong>📅 Shift:</strong> {{ shift_start }} - {{ shift_end }}<br>
            <strong>🗓️ Workdays:</strong> {{ workdays|join(", ") }}<br>
            <strong>😴 Issue:</strong> {{ issue }}<br>
            <strong>📧 Email:</strong> {{ email }}
        </div>
        <div class="section">
            {{ response|safe }}
        </div>
        <div class="download">
            <a href="/download/{{ response_id }}" target="_blank">Download as PDF</a>
        </div>
    </div>
</body>
</html>
"""

responses = {}

def generate_sleep_plan(shift_start, shift_end, workdays, issue):
    # Placeholder logic – customize as needed
    return f"""
    <h2>Sleep Routine</h2>
    <ul>
        <li>Sleep between {shift_end} and 21:00 (9:00 PM) to get 8 hours of sleep.</li>
        <li>Try to keep this consistent even on your off days: {', '.join(workdays)}.</li>
        <li>Your biggest challenge is: <strong>{issue}</strong>.</li>
    </ul>
    <h2>Winding Down</h2>
    <ul>
        <li>Create a dark, quiet, cool room to sleep.</li>
        <li>Use earplugs, blackout curtains, and white noise if needed.</li>
        <li>Have a relaxing routine before sleep like reading, warm bath, or gentle music.</li>
    </ul>
    <h2>Resetting on Off Days</h2>
    <ul>
        <li>Use bright light when awake and avoid screens before bed.</li>
        <li>Eat light at night and avoid caffeine before sleep.</li>
    </ul>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("✅ Full incoming JSON:", json.dumps(data, indent=2))

    fields = {field['label'].strip(): field['value'] for field in data['data']['fields'] if 'value' in field}

    shift_start = fields.get('What time do you usually start your shift?')
    shift_end = fields.get('What time does your shift end?')
    workdays = fields.get('What days of the week do you work?', [])
    issue = fields.get('What’s your biggest sleep challenge right now?', [])[0] if isinstance(fields.get('What’s your biggest sleep challenge right now?'), list) else ''
    email = fields.get('Enter your email to receive your personalized plan')
    response_id = data['data']['responseId']

    response_html = generate_sleep_plan(shift_start, shift_end, workdays, issue)

    html = Template(HTML_TEMPLATE).render(
        shift_start=shift_start,
        shift_end=shift_end,
        workdays=workdays,
        issue=issue,
        email=email,
        response=response_html,
        response_id=response_id
    )

    responses[response_id] = html

    return html

@app.route('/download/<response_id>')
def download(response_id):
    html_content = responses.get(response_id)
    if not html_content:
        return "Not found", 404

    pdf = HTML(string=html_content).write_pdf()
    return send_file(BytesIO(pdf), download_name="sleep_plan.pdf", as_attachment=True)

@app.route('/')
def index():
    return "<h1>Sleep Plan Generator is Live</h1>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
