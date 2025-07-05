import os
from flask import Flask, request, jsonify
import openai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Load environment variables
openai.api_key = os.environ.get("OPENAI_API_KEY")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")  # Your Gmail address
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")  # Gmail App Password

# Flask setup
app = Flask(__name__)

# Logging
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def home():
    return "✅ Sleep Planner Webhook is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        logging.info("✅ Full incoming JSON: %s", data)

        fields = {field["label"].strip(): field["value"] for field in data["data"]["fields"]}

        start_time = fields.get("What time do you usually start your shift?")
        end_time = fields.get("What time does your shift end?")
        days = fields.get("What days of the week do you work?")
        challenge = fields.get("What’s your biggest sleep challenge right now?")
        email = fields.get("Enter your email to receive your personalized plan")

        prompt = f"""
        You are a sleep coach. Create a personalized sleep plan for someone who works night shifts.

        Shift: {start_time} to {end_time}
        Workdays: {days}
        Main issue: {challenge}
        """

        logging.info("📅 Shift: %s - %s", start_time, end_time)
        logging.info("🗓️ Workdays: %s", days)
        logging.info("😴 Issue: %s", challenge)
        logging.info("📧 Email: %s", email)

        # Call OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful sleep coach."},
                {"role": "user", "content": prompt}
            ]
        )

        reply = response["choices"][0]["message"]["content"]
        logging.info("✅ GPT Response: %s", reply)

        # Send email with Gmail App Password
        send_email(to=email, subject="Your Personalized AI Sleep Plan", body=reply)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logging.error("❌ ERROR: %s", str(e))
        return jsonify({"error": str(e)}), 500

def send_email(to, subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        ser
