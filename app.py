from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from transformers import pipeline
import json
import os
from functools import lru_cache

# -----------------------------
# Initialize app
# -----------------------------
app = Flask(__name__, static_folder="frontend")  # optional: serve frontend
CORS(app)  # allow frontend to call backend

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
# Load Hugging Face emotion model
# -----------------------------
print("Loading emotion model (this may take a moment)...")
emotion_classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=1
)
print("Model loaded.")

# -----------------------------
# Cached mood inference
# -----------------------------
@lru_cache(maxsize=1024)
def infer_mood_cached(text):
    result = emotion_classifier(text, top_k=1)
    # Handle possible nested list
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
# Optional: serve frontend
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
