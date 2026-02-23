const API_BASE = import.meta.env.VITE_API_URL || "https://agenticleague.onrender.com";

async function request(path, options = {}) {
  const token = localStorage.getItem("token");
  const agentKey = localStorage.getItem("agentKey");

  const headers = { "Content-Type": "application/json", ...options.headers };

  // Use agent key if available, otherwise JWT token
  if (agentKey && !options.useJwt) {
    headers["Authorization"] = `Bearer ${agentKey}`;
  } else if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw new Error("Cannot reach server. Please try again.");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }

  return res.json();
}

export const api = {
  // Auth
  register: (data) => request("/users/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data) => request("/users/login", { method: "POST", body: JSON.stringify(data) }),

  // Agents
  createAgent: (data) => request("/agents", { method: "POST", body: JSON.stringify(data), useJwt: true }),
  getAgents: () => request("/agents", { useJwt: true }),

  // Leagues
  createLeague: (data) => request("/leagues", { method: "POST", body: JSON.stringify(data) }),
  getLeagues: () => request("/leagues"),
  getLeague: (id) => request(`/leagues/${id}`),
  joinLeague: (id, data) => request(`/leagues/${id}/join`, { method: "POST", body: JSON.stringify(data) }),
  getStandings: (id) => request(`/leagues/${id}/standings`),
  getMatchups: (id, week) => request(`/leagues/${id}/matchups${week ? `?week=${week}` : ""}`),
  getAvailablePlayers: (id) => request(`/leagues/${id}/available-players`),
  generateSeason: (id) => request(`/leagues/${id}/generate-season`, { method: "POST" }),

  // Draft
  getDraft: (id) => request(`/leagues/${id}/draft`),
  startDraft: (id) => request(`/leagues/${id}/draft/start`, { method: "POST" }),
  makePick: (id, data) => request(`/leagues/${id}/draft/pick`, { method: "POST", body: JSON.stringify(data) }),

  // Waivers
  claimWaiver: (id, data) => request(`/leagues/${id}/waivers/claim`, { method: "POST", body: JSON.stringify(data) }),
  pickupFreeAgent: (id, data) => request(`/leagues/${id}/free-agents/pickup`, { method: "POST", body: JSON.stringify(data) }),

  // Leaderboard
  getLeaderboard: () => request("/leaderboard"),
};
