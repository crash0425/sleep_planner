from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# Get your OpenRouter API key from environment variables
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = "openai/gpt-3.5-turbo"

@app.route("/")
def home():
    return "Sleep Planner API is live"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json

        # Extract fields from form submission
        fields = data.get("data", {}).get("fields", [])
        values = {field["label"].strip(): field.get("value") or field.get("valueArray", [None])[0] for field in fields}

        # Clean inputs
        start = values.get("What time do you usually start your shift?")
        end = values.get("What time does your shift end?")
        days = [f["label"].strip().replace("What days of the week do you work? (", "").replace(")", "")
                for f in fields if "What days of the week do you work?" in f["label"] and f["value"] == True]
        challenge = values.get("What’s your biggest sleep challenge right now?")
        email = values.get("Enter your email to receive your personalized plan")

        if not all([start, end, challenge, email]):
            return jsonify({"error": "Missing required fields"}), 400

        prompt = f"""You are a certified sleep expert. Create a personalized sleep improvement plan for someone who:
- Works night shifts from {start} to {end}
- Works on these days: {', '.join(days)}
- Their biggest sleep challenge is: {challenge}

The plan should include:
1. When to sleep and wake up
2. When to eat meals
3. When to take melatonin (if applicable)
4. Any tips to fall back asleep
5. Weekend and family time strategies
Respond in a friendly tone."""

        # Make request to OpenRouter
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        res.raise_for_status()
        response_text = res.json()["choices"][0]["message"]["content"]

        # Return plan as JSON (you can change to email response later)
        return jsonify({
            "email": email,
            "plan": response_text
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Required for Render to detect the port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
