import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { usePolling } from "../hooks/usePolling";
import { SkeletonTable } from "../components/Skeleton";
import LiveIndicator from "../components/LiveIndicator";

function StandingsTab({ leagueId }) {
  const { data: standings, loading, lastUpdated } = usePolling(
    () => api.getStandings(leagueId),
    45000
  );

  if (loading) return <SkeletonTable rows={6} cols={7} />;
  if (!standings || !standings.length) return <p style={{ color: "var(--text-muted)" }}>No standings data yet.</p>;

  return (
    <div>
      <div style={{ marginBottom: 12, display: "flex", justifyContent: "flex-end" }}>
        <LiveIndicator lastUpdated={lastUpdated} />
      </div>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Agent</th>
            <th>W</th>
            <th>L</th>
            <th>T</th>
            <th>PF</th>
            <th>PA</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((s, i) => (
            <tr key={s.agent_id} className="stagger-item" style={{ animationDelay: `${i * 0.04}s` }}>
              <td>{i + 1}</td>
              <td style={{ fontWeight: 600 }}>{s.agent_name}</td>
              <td className="win">{s.wins}</td>
              <td className="loss">{s.losses}</td>
              <td className="tie">{s.ties}</td>
              <td>{s.points_for?.toFixed(1)}</td>
              <td>{s.points_against?.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MatchupsTab({ leagueId }) {
  const [week, setWeek] = useState(1);
  const { data: matchups, loading, lastUpdated } = usePolling(
    () => api.getMatchups(leagueId, week),
    45000
  );

  return (
    <div>
      <div className="flex-between mb-16">
        <div className="flex">
          <button className="btn-secondary" onClick={() => setWeek(Math.max(1, week - 1))} disabled={week <= 1}>
            Prev
          </button>
          <span style={{ fontWeight: 600, minWidth: 80, textAlign: "center" }}>Week {week}</span>
          <button className="btn-secondary" onClick={() => setWeek(week + 1)}>Next</button>
        </div>
        {lastUpdated && <LiveIndicator lastUpdated={lastUpdated} />}
      </div>

      {loading ? <SkeletonTable rows={3} cols={3} /> : !matchups || matchups.length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>No matchups for this week.</p>
      ) : (
        <div className="grid grid-2">
          {matchups.map((m, i) => (
            <div className="card stagger-item" key={m.id || i} style={{ animationDelay: `${i * 0.06}s` }}>
              <div className="flex-between">
                <div>
                  <p style={{ fontWeight: 600 }}>{m.home_agent_name}</p>
                  <p style={{ fontSize: 24, fontWeight: 700 }}>{m.home_score?.toFixed(1) ?? "—"}</p>
                </div>
                <span style={{ color: "var(--text-muted)", fontSize: 13 }}>vs</span>
                <div style={{ textAlign: "right" }}>
                  <p style={{ fontWeight: 600 }}>{m.away_agent_name}</p>
                  <p style={{ fontSize: 24, fontWeight: 700 }}>{m.away_score?.toFixed(1) ?? "—"}</p>
                </div>
              </div>
              {m.winner_id && (
                <p style={{ textAlign: "center", marginTop: 8, fontSize: 13, color: "var(--green)" }}>
                  Winner: {m.winner_id === m.home_agent_id ? m.home_agent_name : m.away_agent_name}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function RosterTab({ leagueId }) {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAvailablePlayers(leagueId).then(setPlayers).catch(() => {}).finally(() => setLoading(false));
  }, [leagueId]);

  if (loading) return <SkeletonTable rows={10} cols={3} />;

  return (
    <div>
      <h3 className="mb-16">Available Players</h3>
      {players.length === 0 ? (
        <p style={{ color: "var(--text-muted)" }}>No available players.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Player</th>
              <th>Team</th>
              <th>Position</th>
            </tr>
          </thead>
          <tbody>
            {players.slice(0, 50).map((p, i) => (
              <tr key={p.id} className="stagger-item" style={{ animationDelay: `${i * 0.02}s` }}>
                <td style={{ fontWeight: 600 }}>{p.name}</td>
                <td>{p.real_team}</td>
                <td>{p.position?.replace(/nba:/g, "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {players.length > 50 && (
        <p style={{ color: "var(--text-muted)", marginTop: 12, fontSize: 13 }}>
          Showing 50 of {players.length} available players
        </p>
      )}
    </div>
  );
}

export default function LeaguePage() {
  const { id } = useParams();
  const [league, setLeague] = useState(null);
  const [tab, setTab] = useState("standings");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLeague(id).then(setLeague).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <SkeletonTable rows={6} cols={5} />;
  if (!league) return <p style={{ textAlign: "center", marginTop: 60, color: "var(--red)" }}>League not found</p>;

  const tabs = [
    { key: "standings", label: "Standings" },
    { key: "matchups", label: "Matchups" },
    { key: "players", label: "Players" },
  ];

  return (
    <div style={{ marginTop: 24 }} className="fade-in-up">
      <div className="flex-between mb-8">
        <h1>{league.name}</h1>
        <span className={`badge badge-${league.status === "active" ? "active" : league.status === "pre_draft" || league.status === "drafting" ? "pre" : "done"}`}>
          {league.status}
        </span>
      </div>
      <p style={{ color: "var(--text-muted)", marginBottom: 24, fontSize: 14 }}>
        {league.sport.toUpperCase()} · {league.current_members}/{league.max_teams} teams
        {league.invite_code && <> · Invite: <code>{league.invite_code}</code></>}
      </p>

      {/* Tabs */}
      <div className="flex mb-24" style={{ borderBottom: "1px solid var(--border)", gap: 0 }}>
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              background: "none",
              borderRadius: 0,
              borderBottom: tab === t.key ? "2px solid var(--accent)" : "2px solid transparent",
              color: tab === t.key ? "var(--text)" : "var(--text-muted)",
              padding: "10px 20px",
              fontWeight: tab === t.key ? 600 : 400,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "standings" && <StandingsTab leagueId={id} />}
      {tab === "matchups" && <MatchupsTab leagueId={id} />}
      {tab === "players" && <RosterTab leagueId={id} />}
    </div>
  );
}
