import os
from flask import Flask, request, jsonify, render_template, redirect, session
import openai
from datetime import datetime
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ac0#uga3q!&4gnti#c$t$6z$)a+99l(3hsap$!@uer#l1z=0ni")
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

def parse_tally_response(data):
    fields = data.get("fields", [])
    shift_start, shift_end, workdays, sleep_issues = None, None, [], []
    for field in fields:
        key = field.get("key")
        value = field.get("value")
        if "start" in key:
            shift_start = value
        elif "end" in key:
            shift_end = value
        elif "work" in key and isinstance(value, list):
            workdays = [opt["text"] for opt in field.get("options", []) if opt["id"] in value]
        elif "sleep challenge" in key.lower() or "sleep" in key.lower():
            sleep_issues = [opt["text"] for opt in field.get("options", []) if opt["id"] in value]
    return shift_start, shift_end, workdays, sleep_issues

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("\n✅ Full incoming JSON:", data)
    
    response_data = data.get("data", {})
    shift_start, shift_end, workdays, sleep_issues = parse_tally_response(response_data)

    prompt = f"""
    Create a personalized sleep plan for a night shift worker.
    Shift starts at: {shift_start}
    Shift ends at: {shift_end}
    Workdays: {', '.join(workdays)}
    Sleep issues: {', '.join(sleep_issues)}
    Format it as a clear list with section titles and practical advice. 
    Use language that is warm, clear, and helpful.
    """

    print("\n📝 Prompt sent to OpenAI:\n", prompt)

    try:
        completion = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a compassionate sleep coach for night shift workers."},
                {"role": "user", "content": prompt}
            ]
        )
        plan_text = completion.choices[0].message.content
    except Exception as e:
        print("OpenAI error:", e)
        return "Error generating plan", 500

    session["plan_text"] = plan_text

    return redirect("/plan")

@app.route("/plan")
def plan():
    plan_text = session.get("plan_text")
    return render_template("plan.html", plan=plan_text)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=10000, host="0.0.0.0")
