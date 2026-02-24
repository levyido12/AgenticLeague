export default function LiveIndicator({ lastUpdated }) {
  const timeStr = lastUpdated
    ? lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : null;

  return (
    <div className="flex" style={{ gap: 8, fontSize: 13, color: "var(--text-muted)" }}>
      <span className="live-dot" />
      <span style={{ color: "var(--green)", fontWeight: 600 }}>Live</span>
      {timeStr && <span>Updated {timeStr}</span>}
    </div>
  );
}
