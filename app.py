from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Set your OpenAI API key here
openai.api_key = os.getenv("OPENAI_API_KEY")  # make sure this is set in Render

@app.route("/")
def home():
    return "Sleep Planner is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        print("Full incoming JSON:", data)  # Debug print

        fields = data.get("data", {}).get("fields", [])
        print("Extracted fields:", fields)  # Debug print

        # Extract form values with fallbacks
        shift_start = next((f.get("value") for f in fields if f.get("key") == "question_VPbyQ6"), "00:00")
        shift_end = next((f.get("value") for f in fields if f.get("key") == "question_P9by1x"), "08:00")
        sleep_challenge = next(
            (
                f.get("value")[0] if isinstance(f.get("value"), list) else f.get("value")
                for f in fields if f.get("key") == "question_rOJWaX"
            ),
            "Staying asleep"
        )
        email = next((f.get("value") for f in fields if f.get("key") == "question_479dJ5"), None)

        if not email:
            return jsonify({"error": "Missing email field"}), 400

        prompt = (
            f"I'm a night shift worker. My shift starts at {shift_start} and ends at {shift_end}. "
            f"My biggest sleep issue is: {sleep_challenge}. Generate a personalized sleep optimization plan."
        )

        print("Sending prompt to OpenAI:", prompt)  # Debug print

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

        return jsonify({
            "status": "success",
            "email": email,
            "sleep_plan": sleep_plan
        })

    except Exception as e:
        print("ERROR:", str(e))  # Debug print
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
