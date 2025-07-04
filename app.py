from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Replace with your real OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_answer(fields, question_key):
    for field in fields:
        if field.get("key") == question_key:
            return field.get("value")
    return None

@app.route("/", methods=["GET"])
def home():
    return "🧠 AI Sleep Planner is live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        fields = data["data"]["fields"]

        start_time = extract_answer(fields, "question_VPbyQ6")
        end_time = extract_answer(fields, "question_P9by1x")
        challenge = extract_answer(fields, "question_rOJWaX")
        email = extract_answer(fields, "question_479dJ5")

        # Convert checkbox values (days of week)
        work_days = []
        for field in fields:
            if field["key"].startswith("question_ElZYd2_") and field["value"] == True:
                day = field["label"].split("(")[-1].replace(")", "").strip()
                work_days.append(day)

        # Format the prompt
        prompt = f"""
        I am a night shift worker. I work from {start_time} to {end_time} on {', '.join(work_days)}.
        My biggest sleep challenge is: {challenge}.
        Create a personalized weekly sleep schedule to help me feel rested.
        """

        # Call GPT
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        plan = response["choices"][0]["message"]["content"]
        return f"<h2>Your Personalized AI Sleep Plan</h2><pre>{plan}</pre>"

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
