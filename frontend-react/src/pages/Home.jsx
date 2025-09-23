// src/pages/Home.jsx
import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import pizzaImg from "../assets/material/pizza.jpg";
import burgerImg from "../assets/material/burger.jpg";
import iceCreamImg from "../assets/material/ice-cream.jpg";
import coffeeImg from "../assets/material/coffee.jpg";

function Home() {
  // Dynamically load CSS from public folder
  useEffect(() => {
    const linkIndex = document.createElement("link");
    linkIndex.rel = "stylesheet";
    linkIndex.href = "/css/index.css";

    const linkGlobal = document.createElement("link");
    linkGlobal.rel = "stylesheet";
    linkGlobal.href = "/css/global.css";

    document.head.appendChild(linkIndex);
    document.head.appendChild(linkGlobal);

    return () => {
      document.head.removeChild(linkIndex);
      document.head.removeChild(linkGlobal);
    };
  }, []);

  const popularFoods = [
    { img: pizzaImg, name: "Cheesy Pizza", desc: "Perfect for a happy, celebration mood." },
    { img: burgerImg, name: "Juicy Burger", desc: "Great for casual, fun moods." },
    { img: iceCreamImg, name: "Ice Cream", desc: "Sweet escape for relaxed vibes." },
    { img: coffeeImg, name: "Coffee", desc: "Hot brewed coffee to energize your day." },
  ];

  return (
    <>
      {/* Hero Section */}
      <section className="hero" id="hero">
        <div className="hero-content">
          <h1>Discover Foods Matching Your Mood</h1>
          <p>
            Type your mood and get personalized food suggestions instantly. 
            Our AI understands your emotions and recommends the perfect dish.
          </p>
          <Link to="/mood" className="hero-btn">
            <button type="button">Try Mood AI</button>
          </Link>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="about">
        <h2>About FoodMood AI</h2>
        <p>
          FoodMood AI helps you discover meals that perfectly match your emotions. 
          Whether you’re happy, sad, or craving comfort food, our AI suggests the ideal dish for you.
        </p>
      </section>

      {/* How It Works */}
      <section className="features">
        <h2>How It Works</h2>
        <div className="steps">
          <div className="step">
            <span className="step-number">1</span>
            <p>Enter your mood</p>
          </div>
          <div className="step">
            <span className="step-number">2</span>
            <p>Get personalized suggestions</p>
          </div>
          <div className="step">
            <span className="step-number">3</span>
            <p>Add to cart & enjoy</p>
          </div>
        </div>
      </section>

      {/* Popular Foods */}
      <section className="popular-foods">
        <h2>Popular Picks</h2>
        <div className="food-grid">
          {popularFoods.map((food, index) => (
            <div key={index} className="food-item">
              <img src={food.img} alt={food.name} />
              <h3>{food.name}</h3>
              <p>{food.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="testimonials">
        <h2>What Our Users Say</h2>
        <div className="testimonial-grid">
          <div className="testimonial">
            <p>"FoodMood AI always nails my cravings. Love it!"</p>
            <span>- Priya, Delhi</span>
          </div>
          <div className="testimonial">
            <p>"When I’m stressed, it suggests comfort food that actually helps."</p>
            <span>- Raj, Mumbai</span>
          </div>
        </div>
      </section>
    </>
  );
}

export default Home;
