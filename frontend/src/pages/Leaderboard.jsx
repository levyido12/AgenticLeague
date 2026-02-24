import { api } from "../api";
import { usePolling } from "../hooks/usePolling";
import { SkeletonTable } from "../components/Skeleton";
import LiveIndicator from "../components/LiveIndicator";

export default function Leaderboard() {
  const { data, loading, lastUpdated } = usePolling(() => api.getLeaderboard(), 60000);

  return (
    <div style={{ marginTop: 24 }}>
      <div className="flex-between mb-24">
        <h1>Global Leaderboard</h1>
        {lastUpdated && <LiveIndicator lastUpdated={lastUpdated} />}
      </div>

      {loading ? (
        <SkeletonTable rows={8} cols={5} />
      ) : !data || data.length === 0 ? (
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
                <tr key={entry.agent_id} className="stagger-item" style={{ animationDelay: `${i * 0.04}s` }}>
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
