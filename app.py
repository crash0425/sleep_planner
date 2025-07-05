from flask import Flask, request, jsonify
import openai
import smtplib
from email.mime.text import MIMEText
import os

app = Flask(__name__)

# Set your OpenAI API Key (or OpenRouter key)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set your Gmail credentials
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")  # e.g. "yourname@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # App password, not your real Gmail password

@app.route("/", methods=["GET"])
def index():
    return "Sleep Planner is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        fields = data['data']['fields']
        
        # Extract specific fields
        answers = {f['label'].strip(): f['value'] for f in fields if 'value' in f}
        
        start_time = answers.get("What time do you usually start your shift?")
        end_time = answers.get("What time does your shift end?")
        challenge = answers.get("What’s your biggest sleep challenge right now?")
        email = answers.get("Enter your email to receive your personalized plan")

        # Compose GPT prompt
        prompt = f"""
        I work night shift starting at {start_time} and ending at {end_time}.
        My biggest sleep challenge is: {challenge}.
        Create a short, personalized sleep optimization plan for a shift worker like me.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        sleep_plan = response.choices[0].message.content.strip()

        # Email the plan
        send_email(to=email, subject="Your Personalized Sleep Plan", body=sleep_plan)

        return jsonify({"status": "success", "plan": sleep_plan}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_email(to, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
