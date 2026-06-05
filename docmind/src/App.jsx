import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { useState, useEffect } from "react";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ChatApp from "./ChatApp";

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem("token"),
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check token on mount
    setIsAuthenticated(!!localStorage.getItem("token"));
    setLoading(false);

    // Listen for storage changes from other tabs
    const handleStorageChange = (e) => {
      if (e.key === "token" || e.key === null) {
        setIsAuthenticated(!!localStorage.getItem("token"));
      }
    };
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <Router>
      <Routes>
        <Route
          path="/login"
          element={<Login setIsAuthenticated={setIsAuthenticated} />}
        />
        <Route path="/register" element={<Register />} />
        <Route
          path="/app"
          element={
            isAuthenticated ? <ChatApp /> : <Navigate to="/login" replace />
          }
        >
          <Route path="chat" element={<div />} /> {/* Placeholders, will be handled by ChatApp's Outlet */}
          <Route path="library" element={<div />} />
          <Route index element={<Navigate to="chat" replace />} />
        </Route>
        <Route
          path="/"
          element={
            <Navigate to={isAuthenticated ? "/app" : "/login"} replace />
          }
        />
      </Routes>
    </Router>
  );
}
