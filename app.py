from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import requests
from functools import lru_cache
import razorpay
import hmac
import hashlib

# -----------------------------
# Initialize app
# -----------------------------
app = Flask(__name__, static_folder="frontend")
CORS(app)

# -----------------------------
# Load dishes + foods database
# -----------------------------
HERE = os.path.dirname(__file__)
DISHES_PATH = os.path.join(HERE, "dishes.json")
FOODS_PATH = os.path.join(HERE, "foods.json")

if not os.path.exists(DISHES_PATH):
    raise FileNotFoundError(f"{DISHES_PATH} not found.")
if not os.path.exists(FOODS_PATH):
    raise FileNotFoundError(f"{FOODS_PATH} not found.")

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
if not HF_API_KEY:
    raise RuntimeError("HF_API_KEY not set.")
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

# -----------------------------
# Razorpay config
# -----------------------------
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise RuntimeError("Razorpay credentials not set.")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

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

    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
        result = result[0]

    if isinstance(result, list) and all(isinstance(r, dict) for r in result):
        sorted_res = sorted(result, key=lambda x: x["score"], reverse=True)
        top_res = sorted_res[:top_k]
        moods = [(r["label"].lower(), float(r["score"])) for r in top_res]
        return moods
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

    if not valid_moods:
        valid_moods = [{"label": "neutral", "confidence": 1.0}]

    return jsonify({"moods": valid_moods, "dishes": recommended})

# -----------------------------
# API: Get all dishes
# -----------------------------
@app.route("/api/dishes")
def get_dishes():
    return jsonify(DISHES)

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
# API: Create Razorpay order
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

# -----------------------------
# API: Verify Razorpay payment
# -----------------------------
@app.route("/api/verify_payment", methods=["POST"])
def verify_payment():
    data = request.get_json(force=True)
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return jsonify({"error": "All payment fields are required"}), 400

    msg = f"{razorpay_order_id}|{razorpay_payment_id}"
    generated_signature = hmac.new(
        bytes(RAZORPAY_KEY_SECRET, 'utf-8'),
        msg=bytes(msg, 'utf-8'),
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
# Run app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
