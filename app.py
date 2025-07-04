from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Set your OpenAI API key here
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/", methods=["GET"])
def index():
    return "Shift Sleep Planner is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        fields = data.get("data", {}).get("fields", [])

        # Extract form data
        shift_start = get_field_value(fields, "question_VPbyQ6")
        shift_end = get_field_value(fields, "question_P9by1x")
        challenge = get_field_value(fields, "question_rOJWaX")
        email = get_field_value(fields, "question_479dJ5")

        # Build the AI prompt
        prompt = f"""
        I work a night shift from {shift_start} to {shift_end}. My biggest sleep issue is: {challenge}.
        Generate a personalized, science-backed sleep optimization plan.
        Include timing for wind-down, light exposure, meals, and ideal sleep hours.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a sleep expert for night shift workers."},
                {"role": "user", "content": prompt}
            ]
        )

        plan = response["choices"][0]["message"]["content"]

        # For now, return the plan in response
        return jsonify({"plan": plan, "email": email})

    except Exception as e:
        return jsonify({"error": str(e)})


def get_field_value(fields, key):
    for field in fields:
        if field.get("key") == key:
            return field.get("value") or field.get("value", [None])[0]
    return None


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
