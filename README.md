# FoodMood AI (ai-integration)

A small full‑stack demo that suggests foods based on user mood using a Hugging Face emotion model, with a Vite + React frontend and a Flask backend. Includes a simple Razorpay payment flow and static JSON datasets for food metadata.

## Overview
FoodMood AI accepts short user text describing mood and returns food suggestions mapped to detected emotions. It was built to demonstrate integrating a model inference API into a full‑stack web flow, mapping AI outputs to domain data, and wiring a minimal ordering/payment flow. The app is suitable as a learning/demo project for developers and recruiters evaluating full‑stack skills.

## Key facts (what the project actually does)
- Accepts user text and infers emotions via a Hugging Face model (SamLowe/roberta-base-go_emotions).
- Maps inferred moods → tastes → candidate foods using local JSON mappings (foods.json) and looks up dish metadata in dishes.json.
- Provides a simple in‑memory cart and ordering flow; order creation and signature verification use Razorpay APIs.
- Serves a Vite + React frontend build from Flask (static files in frontend-react/dist when built).

## Key Features (implemented)
- POST /api/suggest: infer moods and return recommended dishes.
- In‑memory cart: add, view, remove items (no persistent database; server memory only).
- Razorpay order creation (`/api/create_order`) and HMAC signature verification (`/api/verify_payment`).
- React SPA (Vite) with pages for Home, Mood (AI input), and Cart.
- Health check endpoint `/ping`.

## Tech Stack (actual)
- Frontend: React (Vite), react-router-dom
- Backend: Python, Flask, Flask-Cors
- AI/ML: Hugging Face Inference API (requests used to call the HF endpoint)
- Payments: razorpay Python SDK and frontend Razorpay widget
- Packaging / tooling: pip (requirements.txt), npm (frontend package.json), gunicorn listed in requirements

## How it works (workflow)
1. User types a mood phrase in the React UI (/mood).
2. Frontend POSTs { text } to backend `/api/suggest`.
3. Backend calls the Hugging Face inference API, caches results (lru_cache), maps mood labels to tastes and foods, and returns dish objects.
4. User adds dishes to cart; cart data is stored in the server process memory and returned by `/api/cart`.
5. Checkout calls `/api/create_order` (server-side Razorpay order creation). After client-side payment, the frontend sends Razorpay response to `/api/verify_payment` which verifies the HMAC signature and records the order in memory.

## Architecture
- Single Flask app provides REST endpoints and serves frontend static files (expects built files in frontend-react/dist).
- No persistent storage: dishes and mappings are read from JSON files; CART and ORDERS are Python lists in memory.
- External dependencies: Hugging Face Inference API for emotion detection; Razorpay for payments.

## Project structure (important files)
```
README.md
app.py                    # Flask app, routes, HF + Razorpay integration
requirements.txt          # Python dependencies
dishes.json               # dish metadata used for recommendations
foods.json                # mood->taste and taste->food mappings
render.yml                # Render configuration present in repo
frontend-react/           # React (Vite) frontend
  package.json
  src/
    App.jsx
    main.jsx
    pages/
      Home.jsx
      Mood.jsx
      Cart.jsx
    assets/
  index.html
  .env                    # contains VITE_API_URL (points to a configured deployment URL)
```

## Installation (local development)
Clone and prepare backend:

```bash
git clone https://github.com/vinay5ain/ai-integration.git
cd ai-integration
python -m venv venv
# activate the venv (Linux/macOS)
source venv/bin/activate
# on Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Frontend (dev or build):

```bash
cd frontend-react
npm install
# dev server (frontend only)
npm run dev
# build static assets for Flask to serve
npm run build
# this creates frontend-react/dist
```

Run backend (after setting env vars and optionally building frontend):

```bash
# from repo root
export HF_API_KEY="..."
export RAZORPAY_KEY_ID="..."
export RAZORPAY_KEY_SECRET="..."
export PORT=5000  # optional
python app.py
```

## Environment variables (names only)
- HF_API_KEY
- RAZORPAY_KEY_ID
- RAZORPAY_KEY_SECRET
- PORT (optional)
- Frontend: VITE_API_URL (see frontend-react/.env)

Do not add secrets to the repository. Use a local .env (excluded) or secret manager for deployments.

## API Documentation (based strictly on app.py)
- POST /api/suggest
  - Request: JSON { "text": "..." }
  - Response: { "moods": [{label, confidence}], "dishes": [dish, ...] }
  - Errors: 400 if text missing; 500 for external model errors.

- GET /api/cart
  - Response: Array of dish objects currently in server memory.

- POST /api/cart
  - Request: JSON { "id": "<dish_id>" }
  - Response: { "message": "added", "cart": [...] }
  - Notes: app.py expects the key `id` (dish id) when adding.

- DELETE /api/cart
  - Request: JSON { "id": "<dish_id>" }
  - Response: { "message": "removed", "cart": [...] }

- POST /api/create_order
  - Request: JSON { "amount": <number> }  # amount in INR (float)
  - Response: Razorpay order object

- POST /api/verify_payment
  - Request: JSON with razorpay_order_id, razorpay_payment_id, razorpay_signature
  - Behavior: verifies HMAC using RAZORPAY_KEY_SECRET, on success records order and clears cart

- GET /ping
  - Response: { "status": "ok" }

Note: The frontend code (frontend-react/src/pages) contains calls to endpoints with slightly different shapes and routes (see "Notes & known mismatches" below).

## Screenshots / Demo
- frontend-react/.env contains VITE_API_URL=https://ai-integration-vtev.onrender.com — this indicates the frontend was configured to use that host. The repo does not contain hosted screenshots. I did not verify external availability; the URL came from repository files.

## Notes & known mismatches (important)
While inspecting code I observed some mismatches between frontend expectations and backend implementation:
- Frontend Mood.jsx sends POST /api/cart with a body containing keys { dish_id, name, image, price, quantity } while backend /api/cart expects JSON with key `id` only. This means adding items from the UI to the backend cart may not work without aligning the request shape.
- Cart.jsx uses fetch to `/api/cart/${id}` with PUT and DELETE to update/remove items by path parameter — these path-based routes are not implemented in app.py (app.py uses /api/cart without path parameters). Frontend and backend routes should be aligned.

These are code-level inconsistencies present in the current repository and should be resolved before assuming the full end-to-end flow works as intended.

## Challenges & Learning (what this project demonstrates)
- Integrating 3rd-party model inference APIs and handling non-deterministic outputs and errors.
- Caching AI responses (functools.lru_cache) to reduce repeated inference calls.
- Mapping model outputs to domain-specific recommendations using local datasets.
- Basic payment integration and HMAC signature verification.
- Organizing a small full-stack project with a Vite React frontend and Flask backend.

## Future improvements (realistic, not implemented)
- Fix API contract mismatches between frontend and backend (request shapes and route paths).
- Persist carts and orders in a database (SQLite/Postgres/MongoDB) with per‑user data.
- Add user authentication and authorization for orders.
- Add tests (unit and integration) for backend endpoints and frontend components.
- Improve error handling and implement retries/timeout handling for HF API calls.
- Add a .env.example (no secrets) and document deployment steps (Render, Heroku, etc.).

## What this project demonstrates for my profile
- Full-stack development: React (frontend) + Flask (backend)
- Working with external APIs (Hugging Face inference, Razorpay)
- Backend API design and simple state management
- Ability to read, analyze and connect frontend-backend code (debugging and integration)

## Author
Repository owner: vinay5ain

