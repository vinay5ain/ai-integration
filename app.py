from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import requests
from functools import lru_cache

# -----------------------------
# Initialize app
# -----------------------------
app = Flask(__name__, static_folder="frontend")  # serve frontend
CORS(app)

# -----------------------------
# Load food database
# -----------------------------
HERE = os.path.dirname(__file__)
FOOD_JSON_PATH = os.path.join(HERE, "foods.json")

if not os.path.exists(FOOD_JSON_PATH):
    raise FileNotFoundError(f"{FOOD_JSON_PATH} not found. Make sure foods.json exists.")

with open(FOOD_JSON_PATH, "r", encoding="utf-8") as f:
    FOOD_DB = json.load(f)

# -----------------------------
# Hugging Face API config
# -----------------------------
HF_API_URL = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
HF_API_KEY = os.getenv("HF_API_KEY")  # set this in Render dashboard
if not HF_API_KEY:
    raise RuntimeError("HF_API_KEY not set. Add it as an environment variable.")
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

# -----------------------------
# Cached mood inference
# -----------------------------
@lru_cache(maxsize=1024)
def infer_mood_cached(text):
    payload = {"inputs": text}
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=20)
    except Exception as e:
        raise RuntimeError(f"Hugging Face request failed: {str(e)}")

    # Log status and response snippet for debugging
    print("HF status:", response.status_code)
    print("HF response:", response.text[:500])  # first 500 chars

    if response.status_code != 200:
        raise RuntimeError(f"Hugging Face API error: {response.text}")

    try:
        result = response.json()
    except Exception:
        raise RuntimeError(f"Invalid JSON response from HF: {response.text}")

    # Handle nested list output
    if isinstance(result, list) and isinstance(result[0], list):
        res = result[0][0]
    else:
        res = result[0]

    label = res.get("label", "neutral").lower()
    score = float(res.get("score", 0.0))
    return label, score

# -----------------------------
# API route to suggest foods
# -----------------------------
@app.route("/api/suggest", methods=["POST"])
def suggest():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "text required"}), 400

    try:
        label, confidence = infer_mood_cached(text)
    except Exception as e:
        print("Error in mood inference:", str(e))
        return jsonify({"error": "model_error", "details": str(e)}), 500

    # Map mood -> tastes -> foods
    mood_to_taste = FOOD_DB.get("mood_to_taste", {})
    tastes = mood_to_taste.get(label, ["comfort"])

    taste_to_food = FOOD_DB.get("taste_to_food", {})
    foods = []
    for t in tastes:
        foods.extend(taste_to_food.get(t, []))

    unique_foods = list(dict.fromkeys(foods))[:6]  # deduplicate & limit

    return jsonify({
        "mood": label,
        "confidence": round(confidence, 3),
        "tastes": tastes,
        "foods": unique_foods
    })

# -----------------------------
# Health check route
# -----------------------------
@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})

# -----------------------------
# Serve frontend
# -----------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

# -----------------------------
# Run the app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
