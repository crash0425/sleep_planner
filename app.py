from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Sleep Planner API is live!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        print("📥 Incoming webhook data:", data)

        fields = data.get("data", {}).get("fields", [])
        print("📦 Extracted fields:", fields)

        # Helper to extract field by label
        def get_field_value(label):
            for field in fields:
                if field.get("label", "").strip().lower().startswith(label.strip().lower()):
                    return field.get("value")
            return None

        start_time = get_field_value("What time do you usually start your shift?")
        end_time = get_field_value("What time does your shift end?")
        sleep_issue = get_field_value("What’s your biggest sleep challenge right now?")
        email = get_field_value("Enter your email to receive your personalized plan")

        # Logging extracted values
        print("🕒 Start Time:", start_time)
        print("🕓 End Time:", end_time)
        print("😴 Sleep Issue:", sleep_issue)
        print("📧 Email:", email)

        if not all([start_time, end_time, sleep_issue, email]):
            return jsonify({"error": "Missing one or more required fields."}), 400

        # Compose prompt
        prompt = f"""You are a sleep expert helping a night shift worker build a sleep routine.
Here are the details:
- Shift Start: {start_time}
- Shift End: {end_time}
- Biggest Sleep Challenge: {sleep_issue}

Please write a personalized, practical AI-generated sleep optimization plan for this person that includes pre-shift wind-down tips, sleep timing, light management, and optional supplements."""

        # Prepare OpenRouter request
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        if not OPENROUTER_API_KEY:
            return jsonify({"error": "Missing OpenRouter API Key"}), 500

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sleep-planner.onrender.com",
            "X-Title": "AI Sleep Planner"
        }

        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a sleep optimization expert."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000
        }

        print("📡 Sending request to OpenRouter...")
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()

        plan = response.json()["choices"][0]["message"]["content"]
        print("✅ AI Plan Generated:", plan)

        # Respond with plan
        return jsonify({"plan": plan})

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
