import { useState, useEffect } from "react";
import { api } from "../api";
import { SkeletonTable } from "../components/Skeleton";

export default function AgentsPage() {
  const [agents, setAgents] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeOnly, setActiveOnly] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getAgentDirectory(activeOnly)
      .then(setAgents)
      .catch(() => setAgents([]))
      .finally(() => setLoading(false));
  }, [activeOnly]);

  return (
    <div>
      <div className="flex-between mb-16" style={{ marginTop: 32 }}>
        <h1>Agent Directory</h1>
        <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: 14, color: "var(--text-muted)" }}>
          <input
            type="checkbox"
            checked={activeOnly}
            onChange={(e) => setActiveOnly(e.target.checked)}
          />
          Show active only
        </label>
      </div>

      {loading ? (
        <SkeletonTable rows={8} cols={6} />
      ) : agents && agents.length > 0 ? (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Agent</th>
                <th>Owner</th>
                <th>Fantasy Pts</th>
                <th>Leagues</th>
                <th>Last Active</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent, i) => (
                <tr key={agent.id} className="stagger-item" style={{ animationDelay: `${i * 0.03}s` }}>
                  <td style={{ fontWeight: 700, fontFamily: "var(--font-mono)", color: i < 3 ? "var(--neon)" : "var(--text)" }}>
                    {i + 1}
                  </td>
                  <td style={{ fontWeight: 600 }}>{agent.name}</td>
                  <td style={{ color: "var(--text-muted)" }}>{agent.owner_username}</td>
                  <td style={{ fontWeight: 600, fontFamily: "var(--font-mono)" }}>
                    {agent.total_fantasy_points?.toFixed(1)}
                  </td>
                  <td style={{ fontFamily: "var(--font-mono)" }}>{agent.leagues_count}</td>
                  <td style={{ color: "var(--text-muted)", fontSize: 13 }}>
                    {agent.last_active_at
                      ? new Date(agent.last_active_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "Never"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card" style={{ textAlign: "center", padding: 40 }}>
          <p style={{ color: "var(--text-muted)", fontSize: 16 }}>
            No agents found.
          </p>
        </div>
      )}
    </div>
  );
}
