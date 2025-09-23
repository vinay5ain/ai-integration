import { useEffect, useState } from "react";

function Cart() {
  const [items, setItems] = useState([]);

  // Load only cart.css
  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/css/cart.css";
    document.head.appendChild(link);

    return () => {
      document.head.removeChild(link);
    };
  }, []);

  // Load cart from localStorage
  function loadCart() {
    const cart = JSON.parse(localStorage.getItem("cart")) || [];
    setItems(cart);
  }

  useEffect(() => {
    loadCart();
  }, []);

  function removeItem(id) {
    const newCart = items.filter((item) => item.id !== id);
    localStorage.setItem("cart", JSON.stringify(newCart));
    setItems(newCart);
  }

  async function checkout() {
    if (items.length === 0) {
      alert("Cart is empty.");
      return;
    }

    // Total amount in INR
    const amount = items.reduce((sum, item) => sum + (item.price || 100), 0); // default 100 if no price

    // Create Razorpay order via backend
    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
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
        // Verify payment on backend
        const verifyRes = await fetch(`${API_URL}/api/verify_payment`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(response),
        });
        const verifyData = await verifyRes.json();
        if (verifyData.status === "success") {
          alert("Payment Successful!");
          localStorage.removeItem("cart");
          setItems([]);
        } else {
          alert("Payment Verification Failed.");
        }
      },
      theme: { color: "#4a90e2" },
    };

    // Razorpay SDK must be included in public/index.html
    const rzp = new window.Razorpay(options);
    rzp.open();
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
              {item.name} - ₹{item.price || 100}
              <button onClick={() => removeItem(item.id)}>Remove</button>
            </li>
          ))
        )}
      </ul>
      <button id="checkoutBtn" onClick={checkout}>
        Checkout
      </button>
    </section>
  );
}

export default Cart;
