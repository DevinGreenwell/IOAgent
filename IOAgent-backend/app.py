from flask import Flask, request, jsonify
import os
import openai
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    user_prompt = data.get("prompt", "")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_prompt}]
        )
        return jsonify(response.choices[0].message)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
