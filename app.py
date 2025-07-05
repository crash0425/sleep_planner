from flask import Flask, request, jsonify, render_template_string
import os
import openai

app = Flask(__name__)
openai.api_key = os.environ.get("OPENAI_API_KEY")

# In-memory store for plans (replace with a database in production)
plans = {}

@app.route("/", methods=["GET"])
def home():
    return "Sleep Planner is live!"

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

        email = next((f["value"] for f in fields if f["key"] == "question_479dJ5"), "unknown")

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
        print("✅ GPT Response:", result)

        # Save plan under respondent ID
        respondent_id = data["data"]["respondentId"]
        plans[respondent_id] = result

        # Return a URL with the respondent ID to view the plan
        return jsonify({"status": "success", "url": f"/plan/{respondent_id}"})

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/plan/<respondent_id>")
def show_plan(respondent_id):
    plan = plans.get(respondent_id, "No plan found.")
    return render_template_string(f"""
    <html>
      <head><title>Your Sleep Plan</title></head>
      <body style="font-family:sans-serif; padding: 20px;">
        <h2>Your Personalized Sleep Plan</h2>
        <pre style="white-space: pre-wrap;">{plan}</pre>
      </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
