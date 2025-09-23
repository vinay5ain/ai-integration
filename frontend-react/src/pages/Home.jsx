// src/pages/Home.jsx
import React, { useEffect } from "react";
import pizzaImg from "../assets/material/pizza.jpg";
import burgerImg from "../assets/material/burger.jpg";
import iceCreamImg from "../assets/material/ice-cream.jpg";
import coffeeImg from "../assets/material/coffee.jpg";
import lemonadeImg from "../assets/material/lemonade.jpg";
import veggiesImg from "../assets/material/bread.jpg";

function Home() {
  // Dynamically add CSS from public folder
  useEffect(() => {
    const link1 = document.createElement("link");
    link1.rel = "stylesheet";
    link1.href = "/css/index.css";
    document.head.appendChild(link1);

    const link2 = document.createElement("link");
    link2.rel = "stylesheet";
    link2.href = "/css/global.css";
    document.head.appendChild(link2);

    // Cleanup on unmount
    return () => {
      document.head.removeChild(link1);
      document.head.removeChild(link2);
    };
  }, []);

  return (
    <>
      <section className="hero" id="hero">
        <h1>Discover Foods Matching Your Mood</h1>
        <p>Type your mood, get personalized food suggestions instantly</p>
        <a href="/mood">
          <button>Try Mood AI</button>
        </a>
      </section>

      <section id="about" className="about">
        <h2>About FoodMood AI</h2>
        <p>
          FoodMood AI helps you discover meals that perfectly match your emotions.
          Whether you’re happy, sad, or craving comfort food, our AI suggests the right dish for you.
        </p>
      </section>

      <section className="features">
        <h2>How It Works</h2>
        <div className="steps">
          <div className="step">1. Enter your mood</div>
          <div className="step">2. Get personalized suggestions</div>
          <div className="step">3. Add to cart & enjoy</div>
        </div>
      </section>

      <section className="popular-foods">
        <h2>Popular Picks</h2>
        <div className="food-grid">
          <div className="food-item">
            <img src={pizzaImg} alt="Pizza" />
            <h3>Cheesy Pizza</h3>
            <p>Perfect for a happy, celebration mood.</p>
          </div>
          <div className="food-item">
            <img src={burgerImg} alt="Burger" />
            <h3>Juicy Burger</h3>
            <p>Great for casual, fun moods.</p>
          </div>
          <div className="food-item">
            <img src={iceCreamImg} alt="Ice Cream" />
            <h3>Ice Cream</h3>
            <p>Sweet escape for relaxed vibes.</p>
          </div>
          <div className="food-item">
            <img src={coffeeImg} alt="Coffee" />
            <h3>Coffee</h3>
            <p>Hot brewed coffee to energize your day.</p>
          </div>
        </div>
      </section>

      <section id="testimonials" className="testimonials">
        <h2>What Our Users Say</h2>
        <div className="testimonial">
          <p>"FoodMood AI always nails my cravings. Love it!"</p>
          <span>- Priya, Delhi</span>
        </div>
        <div className="testimonial">
          <p>"When I’m stressed, it suggests comfort food that actually helps."</p>
          <span>- Raj, Mumbai</span>
        </div>
      </section>
    </>
  );
}

export default Home;
