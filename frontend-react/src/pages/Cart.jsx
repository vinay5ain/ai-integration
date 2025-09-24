import { useEffect, useState } from "react";

function Cart() {
  const [items, setItems] = useState([]);
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

  // Load cart.css dynamically
  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/css/cart.css";
    document.head.appendChild(link);
    return () => document.head.removeChild(link);
  }, []);

  // Fetch cart from backend
  async function loadCart() {
    try {
      const res = await fetch(`${API_URL}/api/cart`);
      if (!res.ok) throw new Error("Failed to load cart");
      const data = await res.json();
      setItems(data);
    } catch (e) {
      alert(e.message);
    }
  }

  useEffect(() => {
    loadCart();
  }, []);

  // Remove item from backend
  async function removeItem(id) {
    try {
      const res = await fetch(`${API_URL}/api/cart/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to remove item");
      const data = await res.json();
      setItems(data.cart || []);
    } catch (e) {
      alert(e.message);
    }
  }

  // Update quantity in backend
  async function updateQuantity(id, change) {
    const item = items.find((it) => it.id === id);
    if (!item) return;
    const newQty = Math.max(1, item.quantity + change);

    try {
      const res = await fetch(`${API_URL}/api/cart/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ quantity: newQty }),
      });
      if (!res.ok) throw new Error("Failed to update quantity");
      const data = await res.json();
      setItems(items.map((it) => (it.id === id ? { ...it, quantity: newQty } : it)));
    } catch (e) {
      alert(e.message);
    }
  }

  // Checkout via backend + Razorpay
  async function checkout() {
    if (items.length === 0) {
      alert("Cart is empty.");
      return;
    }

    const amount = items.reduce((sum, item) => sum + item.price * item.quantity, 0);

    try {
      const orderRes = await fetch(`${API_URL}/api/create_order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount }),
      });
      const orderData = await orderRes.json();

      const options = {
        key: import.meta.env.VITE_RAZORPAY_KEY || "rzp_test_RJh8bVllLjVPa8",
        amount: orderData.amount,
        currency: orderData.currency,
        name: "FoodMood AI",
        description: "Order Payment",
        order_id: orderData.id,
        handler: async function (response) {
          const verifyRes = await fetch(`${API_URL}/api/verify_payment`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(response),
          });
          const verifyData = await verifyRes.json();
          if (verifyData.status === "success") {
            alert("Payment Successful!");
            setItems([]);
          } else {
            alert("Payment Verification Failed.");
          }
        },
        theme: { color: "#4a90e2" },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (e) {
      alert(e.message);
    }
  }

  return (
    <section id="cart">
      <h2>Your Cart</h2>
      <ul id="cart-items">
        {items.length === 0 ? (
          <li>Your cart is empty.</li>
        ) : (
          items.map((item) => (
            <li key={item.id}>
              <img src={item.image} alt={item.name} style={{ width: "50px", marginRight: "8px" }} />
              {item.name} - ₹{item.price} x {item.quantity} = ₹{item.price * item.quantity}
              <button onClick={() => updateQuantity(item.id, -1)}>-</button>
              <button onClick={() => updateQuantity(item.id, 1)}>+</button>
              <button onClick={() => removeItem(item.id)}>Remove</button>
            </li>
          ))
        )}
      </ul>
      {items.length > 0 && (
        <button id="checkoutBtn" onClick={checkout}>
          Checkout
        </button>
      )}
    </section>
  );
}

export default Cart;
