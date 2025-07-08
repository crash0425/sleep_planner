import os
import json
from flask import Flask, request, render_template, redirect, send_file
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/plan")
def plan():
    email = request.args.get("email")
    if not email:
        return render_template("plan.html", plan_text="No email provided.")

    # Sanitize email to avoid invalid filenames
    safe_email = email.replace("@", "_at_").replace(".", "_dot_")
    filename = f"last_plan_{safe_email}.txt"

    if not os.path.exists(filename):
        return render_template("plan.html", plan_text="No plan found yet. Please fill out the form first.")

    with open(filename, "r") as f:
        plan_text = f.read()

    return render_template("plan.html", plan_text=plan_text)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("✅ Full incoming JSON:", json.dumps(data, indent=2))

    try:
        fields = data["data"]["fields"]
        email = ""
        start_time = ""
        end_time = ""
        workdays = []
        sleep_issue = ""

        for field in fields:
            if "email" in field["key"].lower():
                email = field["value"]
            elif "start" in field["label"].lower():
                start_time = field["value"]
            elif "end" in field["label"].lower():
                end_time = field["value"]
            elif "work" in field["label"].lower() and isinstance(field["value"], list):
                workdays = []
                for option in field.get("options", []):
                    if option["id"] in field["value"]:
                        workdays.append(option["text"])
            elif "sleep challenge" in field["label"].lower():
                for option in field.get("options", []):
                    if option["id"] in field["value"]:
                        sleep_issue = option["text"]

        print("📧 Email extracted:", email)

        prompt = f"""
Create a personalized sleep plan for a night shift worker.
Shift starts at: {start_time}
Shift ends at: {end_time}
Workdays: {', '.join(workdays)}
Sleep issues: {sleep_issue}
Format it as a clear list with section titles and practical advice. 
Use language that is warm, clear, and helpful.
"""

        print("📝 Prompt sent to OpenAI:\n", prompt)

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        plan_text = response.choices[0].message.content.strip()

        # Save to personalized file
        safe_email = email.replace("@", "_at_").replace(".", "_dot_")
        with open(f"last_plan_{safe_email}.txt", "w") as f:
            f.write(plan_text)

        return redirect(f"/plan?email={email}")

    except Exception as e:
        print("❌ Error in webhook:", e)
        return "Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
