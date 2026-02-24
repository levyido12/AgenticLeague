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
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="flex">
          <Link to="/" className="navbar-logo">
            <span className="bracket">[</span>AgenticLeague<span className="bracket">]</span>
          </Link>
          <Link to="/leagues" className="navbar-link">Leagues</Link>
          <Link to="/leaderboard" className="navbar-link">Leaderboard</Link>
          <Link to="/docs" className="navbar-link">Docs</Link>
        </div>
        <div className="flex">
          {token ? (
            <>
              <Link to="/dashboard" className="navbar-link">Dashboard</Link>
              <button className="btn-secondary" onClick={logout} style={{ padding: "6px 14px", fontSize: 13 }}>
                Logout
              </button>
            </>
          ) : (
            <Link to="/login">
              <button className="btn-primary" style={{ padding: "6px 14px", fontSize: 13 }}>
                Sign Up
              </button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
