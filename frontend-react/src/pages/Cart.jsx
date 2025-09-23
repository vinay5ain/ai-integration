// src/pages/Cart.jsx
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

  async function fetchCart() {
    const res = await fetch("/api/cart");
    const data = await res.json();
    setItems(data);
  }

  async function removeItem(id) {
    await fetch("/api/cart", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    fetchCart();
  }

  useEffect(() => {
    fetchCart();
  }, []);

  async function checkout() {
    if (items.length === 0) {
      alert("Cart is empty.");
      return;
    }
    const amount = items.reduce((sum, item) => sum + item.price, 0);
    const orderRes = await fetch("/api/create_order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount }),
    });
    const orderData = await orderRes.json();

    const options = {
      key: "rzp_test_RJh8bVllLjVPa8",
      amount: orderData.amount,
      currency: orderData.currency,
      name: "FoodMood AI",
      description: "Order Payment",
      order_id: orderData.id,
      handler: async function (response) {
        const verifyRes = await fetch("/api/verify_payment", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(response),
        });
        const verifyData = await verifyRes.json();
        if (verifyData.status === "success") {
          alert("Payment Successful!");
        } else {
          alert("Payment Verification Failed.");
        }
        fetchCart();
      },
      theme: { color: "#4a90e2" },
    };

    // Razorpay SDK must be loaded in public/index.html
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
              {item.name} - ₹{item.price}
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
