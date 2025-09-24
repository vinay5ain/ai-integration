import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

function Mood() {
  const [text, setText] = useState("");
  const [dishes, setDishes] = useState([]);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

  // Load mood.css dynamically
  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/css/mood.css";
    document.head.appendChild(link);
    return () => document.head.removeChild(link);
  }, []);

  // Fetch AI food suggestions from backend
  async function suggestFood() {
    if (!text.trim()) return alert("Please describe your mood.");
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/suggest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error("Error fetching suggestions");
      const data = await res.json();
      setDishes(data.dishes || []);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Add dish to backend cart
  async function addToCart(dish) {
    try {
      const res = await fetch(`${API_URL}/api/cart`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dish_id: dish.id,
          name: dish.name,
          image: dish.image,
          price: dish.price || 100,
          quantity: 1,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        alert(`${dish.name} added to cart`);
      } else {
        alert(data.error || "Failed to add to cart");
      }
    } catch (e) {
      alert(e.message);
    }
  }

  return (
    <section className="ai-section">
      <h2>AI Mood-based Food Suggestions</h2>

      <div className="input-group">
        <input
          type="text"
          placeholder="Describe your mood..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && suggestFood()}
        />
        <span className="search-icon" role="button" onClick={suggestFood}>
          🔍
        </span>
      </div>

      <div id="suggested" className="cards">
        {loading && <p>Loading...</p>}
        {!loading && dishes.length === 0 && (
          <p style={{ opacity: 0.7 }}>
            No suggestions yet. Try describing your mood.
          </p>
        )}
        {dishes.map((dish) => (
          <div key={dish.id || dish.name} className="card ai">
            <img src={dish.image || "/placeholder.png"} alt={dish.name} />
            <h3>{dish.name}</h3>
            <p>{dish.description}</p>
            <p>₹{dish.price || 100}</p>
            <button onClick={() => addToCart(dish)}>Add to Cart</button>
          </div>
        ))}
      </div>

      {/* Go to cart page */}
      <button className="cart-btn" onClick={() => navigate("/cart")}>
        🛒
      </button>
    </section>
  );
}

export default Mood;
