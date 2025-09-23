import { Outlet, Link, useLocation } from "react-router-dom";

function App() {
  const location = useLocation();

  // Hide header + footer only on /mood route
  const hideLayout = location.pathname === "/mood";

  // Show minimal navbar on /cart
  const isCartPage = location.pathname === "/cart";

  // Helper for active link
  const isActive = (path) => location.pathname === path ? "active" : "";

  return (
    <div>
      {!hideLayout && (
        <header>
          <div className="logo">FoodMood AI</div>
          <nav aria-label="Main Navigation">
            {isCartPage ? (
              <>
                <Link to="/" className={isActive("/")}>Home</Link>
                <Link to="/mood" className={isActive("/mood")}>Mood AI</Link>
              </>
            ) : (
              <>
                <Link to="/" className={isActive("/")}>Home</Link>
                <Link to="/mood" className={isActive("/mood")}>Mood AI</Link>
                <Link to="/cart" className={isActive("/cart")}>Cart</Link>
                <a href="#about">About</a>
                <a href="#testimonials">Testimonials</a>
                <a href="#contact">Contact</a>
              </>
            )}
          </nav>
        </header>
      )}

      <main>
        <Outlet />
      </main>

      {!hideLayout && (
        <footer id="contact">
          <p>© 2025 FoodMood AI.</p>
          <p>
            Contact:{" "}
            <a href="mailto:support@foodmoodai.com">support@foodmoodai.com</a>
          </p>
          <div className="socials">
            <a href="#">Instagram</a> | <a href="#">Twitter</a> |{" "}
            <a href="#">Facebook</a>
          </div>
        </footer>
      )}
    </div>
  );
}

export default App;
