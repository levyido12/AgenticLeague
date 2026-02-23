import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/users": "http://localhost:8000",
      "/agents": "http://localhost:8000",
      "/leagues": "http://localhost:8000",
      "/leaderboard": "http://localhost:8000",
      "/jobs": "http://localhost:8000",
    },
  },
});
