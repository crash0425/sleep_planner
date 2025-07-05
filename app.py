from flask import Flask, request, jsonify
import os
import openai

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")  # use your OpenAI or OpenRouter key
MODEL = "gpt-3.5-turbo"

@app.route("/")
def home():
    return "Sleep Planner is live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        # Log raw payload for debugging
        print("Received data:", data)

        fields = data.get("data", {}).get("fields", [])
        answers = {}

        for field in fields:
            key = field.get("key")
            value = field.get("value")
            if key and value:
                answers[key] = value

        email = answers.get("question_479dJ5", "noemail@example.com")
        start = answers.get("question_VPbyQ6", "00:00")
        end = answers.get("question_P9by1x", "08:00")
        sleep_issue = answers.get("question_rOJWaX", "Not specified")

        # Build a prompt
        prompt = (
            f"I'm a night shift worker. My shift starts at {start} and ends at {end}. "
            f"My biggest sleep issue is: {sleep_issue}. Create a personalized sleep improvement plan for me."
        )

        print("Prompt to OpenAI:", prompt)

        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a sleep optimization expert."},
                {"role": "user", "content": prompt}
            ]
        )

        plan = response['choices'][0]['message']['content']
        print("Generated Plan:", plan)

        return jsonify({"email": email, "plan": plan})

    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
