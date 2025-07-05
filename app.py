from flask import Flask, request, jsonify, render_template_string, send_file
import os
import openai
from weasyprint import HTML
from io import BytesIO

app = Flask(__name__)
openai.api_key = os.environ.get("OPENAI_API_KEY")

# In-memory store
plans = {}

@app.route("/", methods=["GET"])
def home():
    return "Sleep Planner is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        print("✅ Full incoming JSON:", data)

        fields = data["data"]["fields"]
        shift_start = next((f["value"] for f in fields if f["key"] == "question_VPbyQ6"), "00:00")
        shift_end = next((f["value"] for f in fields if f["key"] == "question_P9by1x"), "08:00")

        workdays_field = next((f for f in fields if f["key"] == "question_ElZYd2"), {})
        all_options = workdays_field.get("options", [])
        selected_ids = set(workdays_field.get("value", []))
        workdays = [opt["text"] for opt in all_options if opt["id"] in selected_ids]

        issue_field = next((f for f in fields if f["key"] == "question_rOJWaX"), {})
        selected_issue_id = issue_field.get("value", [None])[0]
        issue_text = next((opt["text"] for opt in issue_field.get("options", []) if opt["id"] == selected_issue_id), "Not specified")

        respondent_id = data["data"]["respondentId"]

        prompt = f"""You are a sleep expert. Create a personalized sleep plan for a night shift worker.
Shift: {shift_start} to {shift_end}
Workdays: {', '.join(workdays)}
Main issue: {issue_text}

Give a clear daily sleep routine, advice for winding down, and how to reset on off days."""

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful sleep optimization expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        result = response.choices[0].message.content
        plans[respondent_id] = result
        print("✅ GPT Response:", result)

        return jsonify({"status": "success", "url": f"/plan/{respondent_id}"})

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/plan/<respondent_id>")
def show_plan(respondent_id):
    plan = plans.get(respondent_id, "No plan found.")
    return render_template_string(f"""
    <html>
      <head>
        <title>Your Sleep Plan</title>
        <style>
          body {{
            font-family: 'Segoe UI', sans-serif;
            background-color: #f5f7fa;
            color: #333;
            padding: 40px;
            max-width: 800px;
            margin: auto;
          }}
          h1 {{
            color: #2c3e50;
          }}
          .plan {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            white-space: pre-wrap;
          }}
          .btn {{
            margin-top: 20px;
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 12px 20px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
          }}
          .btn:hover {{
            background: #2980b9;
          }}
        </style>
      </head>
      <body>
        <h1>Your Personalized Sleep Plan</h1>
        <div class="plan">{plan}</div>
        <a href="/download/{respondent_id}" class="btn">Download as PDF</a>
      </body>
    </html>
    """)

@app.route("/download/<respondent_id>")
def download_plan(respondent_id):
    plan = plans.get(respondent_id, "No plan found.")
    html_content = f"""
    <html>
      <head><meta charset="UTF-8"><style>body{{font-family:sans-serif; padding:40px;}}</style></head>
      <body><h1>Your Personalized Sleep Plan</h1><pre>{plan}</pre></body>
    </html>
    """
    pdf_io = BytesIO()
    HTML(string=html_content).write_pdf(pdf_io)
    pdf_io.seek(0)

    return send_file(pdf_io, download_name="sleep_plan.pdf", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
