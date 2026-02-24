export function SkeletonTable({ rows = 5, cols = 5 }) {
  return (
    <div className="card">
      <table>
        <thead>
          <tr>
            {Array.from({ length: cols }).map((_, i) => (
              <th key={i}><div className="skeleton" style={{ height: 12, width: "60%" }} /></th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, r) => (
            <tr key={r}>
              {Array.from({ length: cols }).map((_, c) => (
                <td key={c}>
                  <div className="skeleton" style={{ height: 14, width: c === 0 ? "30%" : "70%" }} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SkeletonCard({ count = 3 }) {
  return (
    <div className="grid grid-3">
      {Array.from({ length: count }).map((_, i) => (
        <div className="card" key={i}>
          <div className="skeleton" style={{ height: 18, width: "60%", marginBottom: 12 }} />
          <div className="skeleton" style={{ height: 14, width: "40%", marginBottom: 8 }} />
          <div className="skeleton" style={{ height: 14, width: "80%" }} />
        </div>
      ))}
    </div>
  );
}
