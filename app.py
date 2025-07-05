import os
from flask import Flask, request, render_template, send_file
from dotenv import load_dotenv
from openai import OpenAI
from weasyprint import HTML
import tempfile

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def home():
    return "Sleep Plan Generator is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        print("✅ Full incoming JSON:", data)

        fields = {f['label'].strip(): f['value'] for f in data['data']['fields']}
        shift_start = fields.get("What time do you usually start your shift?")
        shift_end = fields.get("What time does your shift end?")
        workdays = fields.get("What days of the week do you work?", [])
        issue_id = fields.get("What’s your biggest sleep challenge right now?")[0]
        email = fields.get("Enter your email to receive your personalized plan")

        # Map issue ID to text
        issue_map = {
            "ae2dc1d9-16e7-4643-8af2-7349da2fd10a": "Falling asleep",
            "abc0482e-ddbe-4411-b672-91c12c7e96d5": "Staying asleep",
            "bc9c0553-5505-4bec-a453-de6cebccf457": "Waking too early",
            "1e69b4d3-76e7-4a6d-a298-0aca371fcf9a": "All of the above"
        }
        sleep_issue = issue_map.get(issue_id, "Not specified")

        prompt = f"""
        Act as a sleep optimization expert. Given the user's shift starts at {shift_start}, ends at {shift_end}, works on {workdays}, and their biggest sleep issue is: {sleep_issue}, create a personalized sleep plan.
        """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        plan = response.choices[0].message.content.strip()

        print("✅ GPT Response:", plan)

        # Save to temp HTML file for rendering
        with open("templates/plan.html", "w", encoding="utf-8") as f:
            f.write(render_template("plan_template.html", plan=plan))

        return render_template("plan_template.html", plan=plan)

    except Exception as e:
        print("❌ ERROR:", e)
        return "Something went wrong", 500

@app.route("/download-pdf", methods=["GET"])
def download_pdf():
    html = HTML("templates/plan.html")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        html.write_pdf(f.name)
        return send_file(f.name, as_attachment=True, download_name="sleep-plan.pdf")

if __name__ == "__main__":
    app.run(debug=True, port=10000)
