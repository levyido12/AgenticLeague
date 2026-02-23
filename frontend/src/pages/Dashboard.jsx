import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Dashboard() {
  const navigate = useNavigate();
  const [agents, setAgents] = useState([]);
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(null); // "agent" | "league" | "join" | null
  const [form, setForm] = useState({});
  const [error, setError] = useState("");
  const [newAgentKey, setNewAgentKey] = useState("");

  useEffect(() => { load(); }, []);

  async function load() {
    try {
      const [a, l] = await Promise.all([api.getAgents(), api.getLeagues()]);
      setAgents(a);
      setLeagues(l);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  async function createAgent(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await api.createAgent(form);
      setNewAgentKey(data.api_key);
      setForm({});
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function createLeague(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await api.createLeague({
        ...form,
        sport: "nba",
        max_teams: parseInt(form.max_teams || "10"),
      });
      setShowCreate(null);
      setForm({});
      navigate(`/leagues/${data.id}`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function joinLeague(e) {
    e.preventDefault();
    setError("");
    try {
      // Find league by invite code
      const league = leagues.find((l) => l.invite_code === form.invite_code);
      if (!league) throw new Error("League not found with that invite code");
      await api.joinLeague(league.id, { agent_id: form.agent_id });
      setShowCreate(null);
      setForm({});
      navigate(`/leagues/${league.id}`);
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) return <p style={{ textAlign: "center", marginTop: 60 }}>Loading...</p>;

  return (
    <div style={{ marginTop: 24 }}>
      <div className="flex-between mb-24">
        <h1>Dashboard</h1>
        <div className="flex">
          <button className="btn-primary" onClick={() => { setShowCreate("agent"); setError(""); setNewAgentKey(""); }}>
            New Agent
          </button>
          <button className="btn-secondary" onClick={() => { setShowCreate("league"); setError(""); }}>
            Create League
          </button>
          <button className="btn-secondary" onClick={() => { setShowCreate("join"); setError(""); }}>
            Join League
          </button>
        </div>
      </div>

      {/* New Agent Key Display */}
      {newAgentKey && (
        <div className="card mb-24" style={{ borderColor: "var(--green)" }}>
          <h3 className="mb-8" style={{ color: "var(--green)" }}>Agent Created!</h3>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 8 }}>
            Save this API key — it won't be shown again:
          </p>
          <code style={{
            display: "block", background: "var(--bg)", padding: 12, borderRadius: 8,
            wordBreak: "break-all", fontSize: 13,
          }}>
            {newAgentKey}
          </code>
          <button className="btn-secondary mt-16" onClick={() => setNewAgentKey("")} style={{ fontSize: 13 }}>
            Done
          </button>
        </div>
      )}

      {/* Create/Join Forms */}
      {showCreate === "agent" && !newAgentKey && (
        <div className="card mb-24">
          <h3 className="mb-16">Create Agent</h3>
          <form onSubmit={createAgent}>
            <div className="form-group">
              <label>Agent Name</label>
              <input value={form.name || ""} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            {error && <p className="error">{error}</p>}
            <div className="flex">
              <button className="btn-primary" type="submit">Create</button>
              <button className="btn-secondary" type="button" onClick={() => setShowCreate(null)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {showCreate === "league" && (
        <div className="card mb-24">
          <h3 className="mb-16">Create League</h3>
          <form onSubmit={createLeague}>
            <div className="form-group">
              <label>League Name</label>
              <input value={form.name || ""} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Max Teams</label>
              <input type="number" min="6" max="14" value={form.max_teams || "10"}
                onChange={(e) => setForm({ ...form, max_teams: e.target.value })} />
            </div>
            {error && <p className="error">{error}</p>}
            <div className="flex">
              <button className="btn-primary" type="submit">Create</button>
              <button className="btn-secondary" type="button" onClick={() => setShowCreate(null)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {showCreate === "join" && (
        <div className="card mb-24">
          <h3 className="mb-16">Join League</h3>
          <form onSubmit={joinLeague}>
            <div className="form-group">
              <label>Invite Code</label>
              <input value={form.invite_code || ""} onChange={(e) => setForm({ ...form, invite_code: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Agent</label>
              <select value={form.agent_id || ""} onChange={(e) => setForm({ ...form, agent_id: e.target.value })} required>
                <option value="">Select an agent</option>
                {agents.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
            </div>
            {error && <p className="error">{error}</p>}
            <div className="flex">
              <button className="btn-primary" type="submit">Join</button>
              <button className="btn-secondary" type="button" onClick={() => setShowCreate(null)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Agents */}
      <h2 className="mb-16">Your Agents</h2>
      {agents.length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>No agents yet. Create one to get started.</p>
      ) : (
        <div className="grid grid-3 mb-24">
          {agents.map((agent) => (
            <div className="card" key={agent.id}>
              <h3>{agent.name}</h3>
              <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
                Created {new Date(agent.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Leagues */}
      <h2 className="mb-16">Leagues</h2>
      {leagues.length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>No leagues yet.</p>
      ) : (
        <div className="grid grid-2 mb-24">
          {leagues.map((league) => (
            <Link to={`/leagues/${league.id}`} key={league.id} style={{ textDecoration: "none", color: "inherit" }}>
              <div className="card" style={{ cursor: "pointer" }}>
                <div className="flex-between mb-8">
                  <h3>{league.name}</h3>
                  <span className={`badge badge-${league.status === "active" ? "active" : league.status === "pre_draft" || league.status === "drafting" ? "pre" : "done"}`}>
                    {league.status}
                  </span>
                </div>
                <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
                  {league.sport.toUpperCase()} · {league.current_members}/{league.max_teams} teams
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
