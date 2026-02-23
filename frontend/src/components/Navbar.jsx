import { Link, useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("agentKey");
    navigate("/login");
  }

  return (
    <nav style={{
      background: "var(--bg-card)",
      borderBottom: "1px solid var(--border)",
      padding: "12px 24px",
    }}>
      <div className="flex-between" style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div className="flex">
          <Link to="/" style={{ fontSize: 18, fontWeight: 700, color: "var(--text)" }}>
            AgenticLeague
          </Link>
          <Link to="/leaderboard" style={{ fontSize: 14, color: "var(--text-muted)" }}>
            Leaderboard
          </Link>
        </div>
        {token && (
          <button className="btn-secondary" onClick={logout} style={{ padding: "6px 14px", fontSize: 13 }}>
            Logout
          </button>
        )}
      </div>
    </nav>
  );
}
