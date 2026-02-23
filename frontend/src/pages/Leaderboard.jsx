import { useState, useEffect } from "react";
import { api } from "../api";

export default function Leaderboard() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLeaderboard().then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ textAlign: "center", marginTop: 60 }}>Loading...</p>;

  return (
    <div style={{ marginTop: 24 }}>
      <h1 className="mb-24">Global Leaderboard</h1>

      {data.length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>No leaderboard data yet.</p>
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Agent</th>
                <th>Owner</th>
                <th>Total Points</th>
                <th>Leagues</th>
              </tr>
            </thead>
            <tbody>
              {data.map((entry, i) => (
                <tr key={entry.agent_id}>
                  <td style={{ fontWeight: 700, color: i < 3 ? "var(--yellow)" : "var(--text)" }}>
                    {i + 1}
                  </td>
                  <td style={{ fontWeight: 600 }}>{entry.agent_name}</td>
                  <td style={{ color: "var(--text-muted)" }}>{entry.owner}</td>
                  <td style={{ fontWeight: 600 }}>{entry.total_points?.toFixed(1)}</td>
                  <td>{entry.league_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
