from flask import Flask, request, jsonify
import os
import openai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Set OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

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

        print("📅 Shift:", shift_start, "-", shift_end)
        print("🗓️ Workdays:", workdays)
        print("😴 Issue:", issue_text)
        print("📧 Email:", email)

        # Prompt
        prompt = f"""You are a sleep expert. Create a personalized sleep plan for a night shift worker.
Shift: {shift_start} to {shift_end}
Workdays: {', '.join(workdays)}
Main issue: {issue_text}

Give a clear daily sleep routine, advice for winding down, and how to reset on off days."""

        # OpenAI API Call using updated SDK
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

        send_email(email, result)

        return jsonify({"status": "success", "plan": result})

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


def send_email(to_address, body):
    sender_email = os.environ["EMAIL_ADDRESS"]
    app_password = os.environ["EMAIL_APP_PASSWORD"]
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Personalized Sleep Plan"
    message["From"] = sender_email
    message["To"] = to_address

    part = MIMEText(body, "plain")
    message.attach(part)

    try:
        with smtplib.SMTP("smtp.office365.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to_address, message.as_string())
            print("✅ Email sent successfully!")
    except Exception as e:
        print("❌ Email sending failed:", str(e))
        raise e


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
