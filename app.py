from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import requests
from functools import lru_cache
import razorpay
import hmac
import hashlib

# -----------------------------
# Path to frontend build folder
# -----------------------------
HERE = os.path.dirname(__file__)
FRONTEND_BUILD = os.path.join(HERE, "frontend-react", "dist")  # <-- Correct path

# -----------------------------
# Initialize Flask
# -----------------------------
app = Flask(__name__, static_folder=FRONTEND_BUILD, static_url_path="")
CORS(app)

# -----------------------------
# Load dishes + foods database
# -----------------------------
DISHES_PATH = os.path.join(HERE, "dishes.json")
FOODS_PATH = os.path.join(HERE, "foods.json")

with open(DISHES_PATH, "r", encoding="utf-8") as f:
    DISHES = json.load(f)
with open(FOODS_PATH, "r", encoding="utf-8") as f:
    FOODS = json.load(f)

mood_to_taste = FOODS["mood_to_taste"]
taste_to_food = FOODS["taste_to_food"]

# -----------------------------
# Hugging Face API config
# -----------------------------
HF_API_URL = "https://api-inference.huggingface.co/models/SamLowe/roberta-base-go_emotions"
HF_API_KEY = os.getenv("HF_API_KEY")
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

# -----------------------------
# Razorpay config
# -----------------------------
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# -----------------------------
# Cached mood inference
# -----------------------------
@lru_cache(maxsize=1024)
def infer_moods_cached(text, top_k=2):
    payload = {"inputs": text}
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=20)
    if response.status_code != 200:
        raise RuntimeError(f"Hugging Face API error: {response.text}")
    result = response.json()
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
        result = result[0]
    if isinstance(result, list) and all(isinstance(r, dict) for r in result):
        sorted_res = sorted(result, key=lambda x: x["score"], reverse=True)
        top_res = sorted_res[:top_k]
        return [(r["label"].lower(), float(r["score"])) for r in top_res]
    return [("neutral", 1.0)]

# -----------------------------
# In-memory cart & orders
# -----------------------------
CART = []
ORDERS = []

# -----------------------------
# API: Suggest foods by mood
# -----------------------------
@app.route("/api/suggest", methods=["POST"])
def suggest():
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "text required"}), 400
    try:
        moods = infer_moods_cached(text, top_k=2)
    except Exception as e:
        return jsonify({"error": "model_error", "details": str(e)}), 500

    all_tastes = []
    valid_moods = []
    for label, score in moods:
        tastes = mood_to_taste.get(label, ["neutral"])
        all_tastes.extend(tastes)
        valid_moods.append({"label": label, "confidence": round(score, 3)})

    candidate_foods = []
    for taste in all_tastes:
        candidate_foods.extend(taste_to_food.get(taste, []))

    recommended = [dish for dish in DISHES if dish["name"] in candidate_foods]
    if not recommended:
        recommended = [dish for dish in DISHES if "comfort" in dish["tags"]]

    seen = set()
    unique_recommended = []
    for dish in recommended:
        if dish["id"] not in seen:
            unique_recommended.append(dish)
            seen.add(dish["id"])
    recommended = unique_recommended[:6]

    return jsonify({"moods": valid_moods, "dishes": recommended})

# -----------------------------
# API: Cart management
# -----------------------------
@app.route("/api/cart", methods=["GET", "POST", "DELETE"])
def manage_cart():
    global CART
    if request.method == "GET":
        return jsonify(CART)
    data = request.get_json(force=True)
    dish_id = data.get("id")
    if not dish_id:
        return jsonify({"error": "dish id required"}), 400
    if request.method == "POST":
        dish = next((d for d in DISHES if d["id"] == dish_id), None)
        if not dish:
            return jsonify({"error": "dish not found"}), 404
        CART.append(dish)
        return jsonify({"message": "added", "cart": CART})
    if request.method == "DELETE":
        CART = [d for d in CART if d["id"] != dish_id]
        return jsonify({"message": "removed", "cart": CART})

# -----------------------------
# API: Razorpay
# -----------------------------
@app.route("/api/create_order", methods=["POST"])
def create_order():
    data = request.get_json(force=True)
    amount = data.get("amount")
    if not amount:
        return jsonify({"error": "amount required"}), 400
    amount_in_paise = int(amount * 100)
    order = razorpay_client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "payment_capture": 1
    })
    return jsonify(order)

@app.route("/api/verify_payment", methods=["POST"])
def verify_payment():
    data = request.get_json(force=True)
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    msg = f"{razorpay_order_id}|{razorpay_payment_id}"
    generated_signature = hmac.new(
        bytes(RAZORPAY_KEY_SECRET, "utf-8"),
        msg=bytes(msg, "utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    if generated_signature == razorpay_signature:
        ORDERS.append({
            "order_id": razorpay_order_id,
            "payment_id": razorpay_payment_id,
            "cart": CART.copy()
        })
        CART.clear()
        return jsonify({"status": "success", "message": "Payment verified and order placed"})
    else:
        return jsonify({"status": "failed", "message": "Payment verification failed"}), 400

# -----------------------------
# Health check
# -----------------------------
@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})

# -----------------------------
# Serve React frontend
# -----------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    # Serve static files if they exist
    full_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    # Otherwise fallback to index.html
    return send_from_directory(app.static_folder, "index.html")

# -----------------------------
# Run Flask app
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
