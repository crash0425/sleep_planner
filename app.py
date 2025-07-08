import os
from flask import Flask, request, render_template, send_file
from flask_cors import CORS
import openai
import json
import traceback

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")
PORT = int(os.environ.get("PORT", 10000))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/plan")
def plan():
    email = request.args.get("email", "").strip().lower()
    if not email:
        return render_template("plan.html", plan="No email provided.")

    file_path = f"plans/{email}.txt"
    if not os.path.exists(file_path):
        return render_template("plan.html", plan="No plan found yet. Please fill out the form first.")
    
    with open(file_path, "r", encoding="utf-8") as f:
        plan_text = f.read()
    return render_template("plan.html", plan=plan_text)


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("✅ Full incoming JSON:", json.dumps(data, indent=2))

        fields = data["data"]["fields"]
        email = ""
        shift_start = ""
        shift_end = ""
        workdays = []
        sleep_issues = ""

        for field in fields:
            key = field.get("key", "").lower()
            label = field.get("label", "").lower()
            value = field.get("value")

            if "email" in key or "email" in label:
                email = value.strip().lower()
                print("📧 Email extracted:", email)

            elif "start your shift" in label:
                shift_start = value

            elif "end" in label:
                shift_end = value

            elif "what days of the week" in label and isinstance(value, list):
                day_map = {opt["id"]: opt["text"] for opt in field.get("options", [])}
                workdays = [day_map.get(v, v) for v in value]

            elif "sleep challenge" in label and isinstance(value, list):
                for option in field.get("options", []):
                    if option["id"] == value[0]:
                        sleep_issues = option["text"]

        prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {shift_start}
Shift ends at: {shift_end}
Workdays: {', '.join(workdays)}
Sleep issues: {sleep_issues}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""
        print("📝 Prompt sent to OpenAI:\n", prompt)

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful sleep coach."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        result = response["choices"][0]["message"]["content"]
        print("✅ Sleep plan generated.")

        os.makedirs("plans", exist_ok=True)
        if email:
            with open(f"plans/{email}.txt", "w", encoding="utf-8") as f:
                f.write(result)

        return "", 302, {"Location": f"/plan?email={email}"}

    except Exception as e:
        print("❌ Error in webhook:", str(e))
        traceback.print_exc()
        return "Error processing form", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
