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
HF_API_URL = "https://api-inference.huggingface.co/models/SamLowe/roberta-base-go_emotions"
HF_API_KEY = os.getenv("HF_API_KEY")  # must be set in environment
if not HF_API_KEY:
    raise RuntimeError("HF_API_KEY not set. Add it as an environment variable.")
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

# -----------------------------
# Cached mood inference
# -----------------------------
@lru_cache(maxsize=1024)
def infer_moods_cached(text, top_k=2):
    payload = {"inputs": text}
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=20)
    except Exception as e:
        raise RuntimeError(f"Hugging Face request failed: {str(e)}")

    if response.status_code != 200:
        raise RuntimeError(f"Hugging Face API error: {response.text}")

    try:
        result = response.json()
    except Exception:
        raise RuntimeError(f"Invalid JSON response from HF: {response.text}")

    # 🔹 Handle nested list case ([[...]])
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
        result = result[0]

    if isinstance(result, list) and all(isinstance(r, dict) for r in result):
        sorted_res = sorted(result, key=lambda x: x["score"], reverse=True)
        top_res = sorted_res[:top_k]
        moods = [(r["label"].lower(), float(r["score"])) for r in top_res]
        return moods

    # 🔹 Fallback: if API returns unexpected format
    return [("neutral", 1.0)]

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
        moods = infer_moods_cached(text, top_k=2)  # get top 2 moods
    except Exception as e:
        print("Error in mood inference:", str(e))
        return jsonify({"error": "model_error", "details": str(e)}), 500

    mood_to_taste = FOOD_DB.get("mood_to_taste", {})
    taste_to_food = FOOD_DB.get("taste_to_food", {})

    all_tastes = []
    all_foods = []
    valid_moods = []

    for label, score in moods:
        if label not in mood_to_taste:
            label = "neutral"

        valid_moods.append({"label": label, "confidence": round(score, 3)})

        tastes = mood_to_taste.get(label, ["comfort"])
        all_tastes.extend(tastes)
        for t in tastes:
            all_foods.extend(taste_to_food.get(t, []))

    # 🔹 Ensure fallback foods if none found
    if not all_foods:
        all_foods = taste_to_food.get("comfort", ["pizza", "burger", "pasta"])

    unique_foods = list(dict.fromkeys(all_foods))[:6]  # deduplicate & limit

    # 🔹 Ensure fallback moods if nothing valid
    if not valid_moods:
        valid_moods = [{"label": "neutral", "confidence": 1.0}]

    return jsonify({
        "moods": valid_moods,
        "tastes": list(dict.fromkeys(all_tastes)) or ["comfort"],
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
