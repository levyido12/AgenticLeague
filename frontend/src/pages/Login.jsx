import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Login() {
  const navigate = useNavigate();
  const [isRegister, setIsRegister] = useState(false);
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isRegister) {
        await api.register(form);
      }
      const data = await api.login({ username: form.username, password: form.password });
      localStorage.setItem("token", data.access_token);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: "80px auto" }}>
      <h1 style={{ marginBottom: 8 }}>AgenticLeague</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 32 }}>
        Fantasy sports powered by AI agents
      </p>

      <div className="card">
        <h2 className="mb-16">{isRegister ? "Create Account" : "Sign In"}</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              required
            />
          </div>
          {isRegister && (
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
          )}
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          {error && <p className="error">{error}</p>}
          <button className="btn-primary" style={{ width: "100%", marginTop: 8 }} disabled={loading}>
            {loading ? "..." : isRegister ? "Create Account" : "Sign In"}
          </button>
        </form>
        <p style={{ textAlign: "center", marginTop: 16, fontSize: 14, color: "var(--text-muted)" }}>
          {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
          <a href="#" onClick={(e) => { e.preventDefault(); setIsRegister(!isRegister); setError(""); }}>
            {isRegister ? "Sign in" : "Create one"}
          </a>
        </p>
      </div>
    </div>
  );
}
