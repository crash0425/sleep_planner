@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        print("Webhook received:", json.dumps(data, indent=2))

        # Extract email and other fields
        fields = data["data"]["fields"]
        values = {f["label"].strip(): f["value"] for f in fields if "value" in f}
        print("Extracted values:", values)

        start_time = values.get("What time do you usually start your shift?")
        end_time = values.get("What time does your shift end?")
        challenge = values.get("What’s your biggest sleep challenge right now?")
        email = values.get("Enter your email to receive your personalized plan")

        # Validate required fields
        if not email:
            return "Missing email", 400

        prompt = f"""
        Create a personalized night shift sleep optimization plan.
        Shift starts at {start_time} and ends at {end_time}.
        Main sleep issue: {challenge}.
        Make it practical and easy to follow.
        """

        print("Sending to GPT:", prompt)

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            }
        )

        gpt_data = response.json()
        print("GPT response:", json.dumps(gpt_data, indent=2))

        plan = gpt_data["choices"][0]["message"]["content"]

        return jsonify({
            "email": email,
            "plan": plan
        })

    except Exception as e:
        print("Error occurred:", e)
        return "Internal Server Error", 500
