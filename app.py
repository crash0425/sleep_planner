from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/", methods=["GET"])
def index():
    return "Sleep Planner is live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        fields = data.get("data", {}).get("fields", [])

        shift_start = next((f["value"] for f in fields if f["key"] == "question_VPbyQ6"), "00:00")
        shift_end = next((f["value"] for f in fields if f["key"] == "question_P9by1x"), "08:00")
        sleep_challenge = next((f["value"][0] if isinstance(f["value"], list) else f["value"]
                                for f in fields if f["key"] == "question_rOJWaX"), "Staying asleep")
        email = next((f["value"] for f in fields if f["key"] == "question_479dJ5"), None)

        if not email:
            return jsonify({"error": "Missing email"}), 400

        prompt = (f"I'm a night shift worker. My shift starts at {shift_start} and ends at {shift_end}. "
                  f"My biggest sleep issue is: {sleep_challenge}. Generate a personalized sleep optimization plan "
                  f"with a daily routine, bedtime strategy, and tips for better recovery on off days.")

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a sleep coach for shift workers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=600
        )

        sleep_plan = response.choices[0].message.content

        # For now, return the plan (you can replace this with email logic)
        return jsonify({
            "status": "success",
            "email": email,
            "sleep_plan": sleep_plan
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=10000, host="0.0.0.0")
