import { useState, useEffect } from "react";

function Mood() {
  const [text, setText] = useState("");
  const [dishes, setDishes] = useState([]);
  const [loading, setLoading] = useState(false);

  // Backend base URL from .env (fallback to local dev)
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

  // Load mood.css only on this page
  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/css/mood.css";
    document.head.appendChild(link);

    return () => {
      docum
      ent.head.removeChild(link);
    };
  }, []);

  // Call backend for suggestions
  async function suggestFood() {
    if (!text.trim()) {
      alert("Please describe your mood.");
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/suggest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) throw new Error("Error fetching suggestions");

      const data = await response.json();
      setDishes(data.dishes || []);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Add dish to local cart
  function addToCart(id, name, image) {
    let cart = JSON.parse(localStorage.getItem("cart")) || [];
    if (!cart.find((item) => item.id === id)) {
      cart.push({ id, name, image, quantity: 1 });
      localStorage.setItem("cart", JSON.stringify(cart));
      alert(`${name} added to cart`);
    } else {
      alert(`${name} is already in the cart`);
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
          <p style={{ opacity: 0.7 }}>No suggestions yet. Try describing your mood.</p>
        )}
        {dishes.map((dish) => (
          <div key={dish.id} className="card ai">
            <img src={dish.image} alt={dish.name} />
            <h3>{dish.name}</h3>
            <p>{dish.description}</p>
            <button onClick={() => addToCart(dish.id, dish.name, dish.image)}>
              Add to Cart
            </button>
          </div>
        ))}
      </div>

      {/* Floating Cart Button */}
      <button className="cart-btn" onClick={() => (window.location.href = "/cart")}>
        🛒
      </button>
    </section>
  );
}

export default Mood;
