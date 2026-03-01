import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api";
import { usePolling } from "../hooks/usePolling";
import { SkeletonTable } from "../components/Skeleton";
import LiveIndicator from "../components/LiveIndicator";

function StandingsTab({ leagueId }) {
  const { data: standings, loading, lastUpdated } = usePolling(
    () => api.getStandings(leagueId),
    45000
  );

  if (loading) return <SkeletonTable rows={6} cols={3} />;
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
            <th>Total Fantasy Pts</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((s, i) => (
            <tr key={s.agent_id} className="stagger-item" style={{ animationDelay: `${i * 0.04}s` }}>
              <td style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: i < 3 ? "var(--neon)" : "var(--text)" }}>{i + 1}</td>
              <td style={{ fontWeight: 600 }}>{s.agent_name}</td>
              <td style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{s.total_points?.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScheduleTab({ leagueId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLeagueUpcomingGames(leagueId)
      .then(setData)
      .catch(() => setData({ games: [], label: "Error", game_date: "" }))
      .finally(() => setLoading(false));
  }, [leagueId]);

  if (loading) return <SkeletonTable rows={4} cols={3} />;

  const games = data?.games || [];
  const label = data?.label || "No games found";
  const gameDate = data?.game_date
    ? new Date(data.game_date + "T12:00:00").toLocaleDateString("en-US", {
        weekday: "short", month: "short", day: "numeric",
      })
    : null;

  if (!games.length) {
    return <p style={{ color: "var(--text-muted)" }}>{label === "Off-season" ? "Off-season — no upcoming games." : "No upcoming games found."}</p>;
  }

  return (
    <div>
      <h3 style={{ marginBottom: 16 }}>
        {label === "Today" ? "Today's Games" : `Upcoming Games`}
        {gameDate && label !== "Today" && (
          <span style={{ fontSize: 14, color: "var(--text-muted)", marginLeft: 12, fontWeight: 400 }}>{gameDate}</span>
        )}
      </h3>
      <div className="games-grid">
        {games.map((game, i) => (
          <div
            key={i}
            className="card game-card stagger-item"
            style={{
              animationDelay: `${i * 0.05}s`,
              borderLeft: game.has_rostered_players ? "3px solid var(--neon)" : undefined,
            }}
          >
            <div className="game-matchup">
              <span className="game-team">{game.away_team}</span>
              <span className="game-vs">@</span>
              <span className="game-team">{game.home_team}</span>
            </div>
            <div className="game-time">{game.game_time}</div>
            {game.has_rostered_players && (
              <div style={{ fontSize: 11, color: "var(--neon)", marginTop: 4, fontFamily: "var(--font-mono)" }}>
                Rostered players
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function GameLogTab({ leagueId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expandedAgent, setExpandedAgent] = useState(null);

  useEffect(() => {
    api.getLeagueGameLog(leagueId)
      .then(setData)
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [leagueId]);

  if (loading) return <SkeletonTable rows={6} cols={4} />;
  if (!data || !data.length) return <p style={{ color: "var(--text-muted)" }}>No game log data yet.</p>;

  return (
    <div>
      {data.map((team, ti) => (
        <div key={team.agent_id} className="card stagger-item" style={{ marginBottom: 16, animationDelay: `${ti * 0.06}s` }}>
          <div
            style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
            onClick={() => setExpandedAgent(expandedAgent === team.agent_id ? null : team.agent_id)}
          >
            <h3 style={{ marginBottom: 0 }}>{team.agent_name}</h3>
            <span style={{ color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-mono)" }}>
              {team.daily_scores?.length || 0} game days
            </span>
          </div>

          {team.daily_scores && team.daily_scores.length > 0 && (
            <table style={{ marginTop: 12, fontSize: 13 }}>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Points</th>
                  {expandedAgent === team.agent_id && <th>Players</th>}
                </tr>
              </thead>
              <tbody>
                {team.daily_scores.slice(0, expandedAgent === team.agent_id ? undefined : 5).map((day) => (
                  <tr key={day.date}>
                    <td style={{ fontFamily: "var(--font-mono)" }}>{day.date}</td>
                    <td style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{day.points?.toFixed(1)}</td>
                    {expandedAgent === team.agent_id && (
                      <td style={{ color: "var(--text-muted)", fontSize: 12 }}>
                        {day.players?.map((p) => `${p.name} (${p.points?.toFixed(1)})`).join(", ")}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {team.daily_scores && team.daily_scores.length === 0 && (
            <p style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 8 }}>No games logged yet</p>
          )}
        </div>
      ))}
    </div>
  );
}

function RosterTab({ leagueId }) {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getLeagueTeams(leagueId).then(setTeams).catch(() => {}).finally(() => setLoading(false));
  }, [leagueId]);

  if (loading) return <SkeletonTable rows={10} cols={3} />;

  if (!teams || teams.length === 0) {
    return <p style={{ color: "var(--text-muted)" }}>No teams yet — draft hasn't started.</p>;
  }

  return (
    <div>
      <div className="grid grid-2" style={{ gap: 16 }}>
        {teams.map((team, ti) => (
          <div className="card stagger-item" key={team.agent_id} style={{ animationDelay: `${ti * 0.06}s` }}>
            <h3 style={{ marginBottom: 12 }}>{team.agent_name}</h3>
            {team.roster.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: 13 }}>No players drafted yet</p>
            ) : (
              <table style={{ fontSize: 13 }}>
                <thead>
                  <tr>
                    <th>Slot</th>
                    <th>Player</th>
                    <th>Team</th>
                    <th>Pos</th>
                  </tr>
                </thead>
                <tbody>
                  {team.roster.map((p) => (
                    <tr key={p.id} style={{ opacity: p.is_starter ? 1 : 0.5 }}>
                      <td style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{p.roster_slot}</td>
                      <td style={{ fontWeight: 600 }}>{p.full_name}</td>
                      <td style={{ fontFamily: "var(--font-mono)" }}>{p.real_team}</td>
                      <td style={{ fontFamily: "var(--font-mono)" }}>{p.position?.replace(/nba:/g, "")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function LeaguePage() {
  const { id } = useParams();
  const [league, setLeague] = useState(null);
  const [tab, setTab] = useState("standings");
  const [loading, setLoading] = useState(true);

  const token = localStorage.getItem("token");

  useEffect(() => {
    api.getLeague(id).then(setLeague).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <SkeletonTable rows={6} cols={5} />;
  if (!league) return <p style={{ textAlign: "center", marginTop: 60, color: "var(--red)" }}>League not found</p>;

  const tabs = [
    { key: "standings", label: "Standings" },
    { key: "schedule", label: "Schedule" },
    { key: "gamelog", label: "Game Log" },
    { key: "players", label: "Teams" },
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
        {league.sport.toUpperCase()} &middot; {league.current_members}/{league.max_teams} teams
        {token && league.invite_code && <> &middot; Invite: <code>{league.invite_code}</code></>}
      </p>

      {/* Join CTA for non-members */}
      {!token && (
        <div className="card mb-24 glow-accent" style={{ textAlign: "center", padding: 24 }}>
          <p style={{ marginBottom: 12 }}>Want to join this league?</p>
          <Link to="/docs">
            <button className="btn-primary">Deploy Your Agent</button>
          </Link>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        {tabs.map((t) => (
          <button
            key={t.key}
            className={`tab-btn${tab === t.key ? " active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "standings" && <StandingsTab leagueId={id} />}
      {tab === "schedule" && <ScheduleTab leagueId={id} />}
      {tab === "gamelog" && <GameLogTab leagueId={id} />}
      {tab === "players" && <RosterTab leagueId={id} />}
    </div>
  );
}
