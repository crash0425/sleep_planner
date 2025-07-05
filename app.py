from flask import Flask, request, jsonify
import os
import openai

app = Flask(__name__)

# Set your API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "Sleep Planner is live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # Try to parse the incoming JSON
        data = request.get_json(force=True)
        print("✅ Full incoming JSON:", data)

        fields = data["data"]["fields"]

        # Extract values safely
        shift_start = next((f["value"] for f in fields if f["key"] == "question_VPbyQ6"), "00:00")
        shift_end = next((f["value"] for f in fields if f["key"] == "question_P9by1x"), "08:00")
        workdays = [f["label"].split(" (")[-1].replace(")", "") 
                    for f in fields if f["key"].startswith("question_ElZYd2_") and f.get("value") == True]
        sleep_issue = next((f["value"][0] if isinstance(f["value"], list) else f["value"]
                            for f in fields if f["key"] == "question_rOJWaX"), "Not specified")
        email = next((f["value"] for f in fields if f["key"] == "question_479dJ5"), "unknown")

        print("📅 Shift:", shift_start, "-", shift_end)
        print("🗓️ Workdays:", workdays)
        print("😴 Issue:", sleep_issue)
        print("📧 Email:", email)

        # Construct prompt
        prompt = f"""You are a sleep expert. Create a personalized sleep plan for a night shift worker.
Shift: {shift_start} to {shift_end}
Workdays: {', '.join(workdays)}
Main issue: {sleep_issue}

Give a clear daily sleep routine, advice for winding down, and how to reset on off days.
"""

        # Ask GPT-4 (or GPT-3.5)
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful sleep optimization expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )

        result = response['choices'][0]['message']['content']
        print("✅ GPT Response:", result)

        return jsonify({"status": "success", "plan": result})

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"error": "Failed to process webhook", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
