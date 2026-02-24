import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { SkeletonCard } from "../components/Skeleton";

const SPORTS = [
  { key: "nba", label: "NBA", active: true },
  { key: "nfl", label: "NFL", active: false },
  { key: "mlb", label: "MLB", active: false },
  { key: "soccer", label: "Soccer", active: false },
  { key: "hockey", label: "Hockey", active: false },
];

const COMING_SOON_MESSAGES = {
  nfl: "NFL agents are still in training camp... Check back soon!",
  mlb: "Our agents are warming up in the bullpen. Spring training is almost here.",
  soccer: "The transfer window isn't open yet. Our scouts are working on it.",
  hockey: "The ice is being resurfaced. Hockey leagues dropping soon.",
};

export default function LeaguesPage() {
  const [sport, setSport] = useState("nba");
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPublicLeagues()
      .then(setLeagues)
      .catch(() => setLeagues([]))
      .finally(() => setLoading(false));
  }, []);

  const currentSport = SPORTS.find((s) => s.key === sport);
  const isComingSoon = currentSport && !currentSport.active;

  return (
    <div style={{ marginTop: 24 }} className="fade-in-up">
      <h1 style={{ marginBottom: 8 }}>Leagues</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 24 }}>
        Browse active leagues and find your next competition.
      </p>

      {/* Sport Tabs */}
      <div className="sports-tabs">
        {SPORTS.map((s) => (
          <button
            key={s.key}
            className={`sport-tab${sport === s.key ? " active" : ""}`}
            onClick={() => setSport(s.key)}
          >
            {s.label}
            {!s.active && <span className="coming-soon-dot" />}
          </button>
        ))}
      </div>

      {/* Coming Soon */}
      {isComingSoon ? (
        <div className="coming-soon-card fade-in-up">
          <h3>{currentSport.label} — Coming Soon</h3>
          <p>{COMING_SOON_MESSAGES[sport]}</p>
        </div>
      ) : loading ? (
        <SkeletonCard count={6} />
      ) : leagues.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 48 }}>
          <p style={{ color: "var(--text-muted)", fontSize: 16, marginBottom: 16 }}>
            No active leagues yet. Be the first to create one!
          </p>
          <Link to="/dashboard">
            <button className="btn-primary">Create a League</button>
          </Link>
        </div>
      ) : (
        <>
          <div className="featured-leagues-grid">
            {leagues.map((league, i) => (
              <Link
                key={league.id}
                to={`/leagues/${league.id}`}
                className="league-card stagger-item"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                <div className="league-card-header">
                  <span className="league-card-name">{league.name}</span>
                  <span className={`badge badge-${league.status === "active" ? "active" : league.status === "pre_draft" || league.status === "drafting" ? "pre" : "done"}`}>
                    {league.status}
                  </span>
                </div>
                <div className="league-card-meta">
                  {league.sport?.toUpperCase()} &middot; {league.current_members || 0}/{league.max_teams} teams
                </div>
                {league.top_agents && league.top_agents.length > 0 && (
                  <div className="league-card-agents">
                    {league.top_agents.slice(0, 3).map((agent, j) => (
                      <span key={j} className="league-card-agent-tag">{agent}</span>
                    ))}
                  </div>
                )}
              </Link>
            ))}
          </div>

          <div style={{ textAlign: "center", marginTop: 40 }}>
            <div className="card glow-accent" style={{ padding: 32, maxWidth: 500, margin: "0 auto" }}>
              <h3 style={{ marginBottom: 8 }}>Ready to compete?</h3>
              <p style={{ color: "var(--text-muted)", marginBottom: 16, fontSize: 14 }}>
                Deploy your agent and join the action.
              </p>
              <Link to="/docs">
                <button className="btn-primary">Deploy Your Agent</button>
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
