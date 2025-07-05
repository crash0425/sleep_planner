import os
import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify
import openai

app = Flask(__name__)

# ENV VARS REQUIRED: OPENAI_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD
openai.api_key = os.getenv("OPENAI_API_KEY")

# Util: send email
def send_email(to_email, subject, body):
    gmail_user = os.getenv("GMAIL_ADDRESS")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_pass)
        smtp.send_message(msg)

# Util: create prompt from form data
def generate_prompt(shift_start, shift_end, workdays, sleep_issues):
    days = ", ".join(workdays)
    issue = sleep_issues if isinstance(sleep_issues, str) else ", ".join(sleep_issues)
    return (
        f"I work the night shift from {shift_start} to {shift_end}, "
        f"on the following days: {days}. "
        f"My biggest sleep challenge is: {issue}. "
        f"Please create a personalized sleep routine and health guide tailored to my situation."
    )

@app.route("/")
def home():
    return "Sleep Planner is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    fields = {f["key"]: f for f in data["data"]["fields"]}

    # Extract form fields
    shift_start = fields["question_VPbyQ6"]["value"]
    shift_end = fields["question_P9by1x"]["value"]
    workdays = fields["question_ElZYd2"]["value"]
    sleep_issues = fields["question_rOJWaX"]["options"][0]["text"]  # Assuming only one selected
    email = fields["question_479dJ5"]["value"]

    # Generate GPT sleep plan
    prompt = generate_prompt(shift_start, shift_end, workdays, sleep_issues)
    print(f"🧠 Prompt: {prompt}")

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    sleep_plan = response.choices[0].message.content

    # Email the sleep plan
    send_email(
        to_email=email,
        subject="Your Personalized AI Sleep Plan",
        body=sleep_plan
    )

    return jsonify({"status": "success", "message": "Email sent!"})

if __name__ == "__main__":
    app.run(debug=True, port=10000)
