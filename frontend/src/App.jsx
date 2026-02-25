import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import LandingPage from "./pages/LandingPage";

const Login = lazy(() => import("./pages/Login"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const LeaguePage = lazy(() => import("./pages/LeaguePage"));
const LeaguesPage = lazy(() => import("./pages/LeaguesPage"));
const Leaderboard = lazy(() => import("./pages/Leaderboard"));
const DocsPage = lazy(() => import("./pages/DocsPage"));

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("token");
  return token ? children : <Navigate to="/login" />;
}

function PageLoader() {
  return (
    <div style={{ display: "flex", justifyContent: "center", padding: "80px 20px" }}>
      <div className="skeleton" style={{ width: 200, height: 24, borderRadius: 8 }} />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <div className="container">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/docs" element={<DocsPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/leagues" element={<LeaguesPage />} />
            <Route path="/leagues/:id" element={<LeaguePage />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
          </Routes>
        </Suspense>
      </div>
    </BrowserRouter>
  );
}
