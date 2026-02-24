import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";

// Terminal log lines that cycle through
const TERMINAL_LINES = [
  { text: "Scanning player performance data...", type: "info" },
  { text: "LeBron James: 28pts / 8reb / 11ast", type: "data" },
  { text: "Fantasy score calculated: 67.3", type: "success" },
  { text: "Analyzing waiver wire targets...", type: "info" },
  { text: "Probability of breakout game: 84%", type: "success" },
  { text: "Nikola Jokic triple-double detected", type: "data" },
  { text: "Roster optimization complete", type: "success" },
  { text: "Matchup advantage: +12.4 projected", type: "data" },
  { text: "Scouting report generated", type: "info" },
  { text: "Draft pick recommendation: A. Edwards", type: "success" },
  { text: "Injury alert: monitoring status...", type: "warning" },
  { text: "League standings updated", type: "info" },
  { text: "Stephen Curry: 3PT% trending up", type: "data" },
  { text: "Agent strategy: aggressive waivers", type: "success" },
  { text: "Weekly projection: 847.2 fantasy pts", type: "data" },
];

// SVG trajectory paths for ball/player movement
const TRAJECTORIES = [
  "M 50 300 Q 200 50 400 250 T 750 200",
  "M 100 400 Q 300 100 500 350 T 800 150",
  "M 0 250 Q 150 400 350 200 Q 550 50 750 300",
  "M 80 100 Q 250 350 450 150 T 720 280",
];

function TrajectoryLine({ d, delay, color }) {
  return (
    <motion.path
      d={d}
      fill="none"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      initial={{ pathLength: 0, opacity: 0 }}
      animate={{ pathLength: 1, opacity: [0, 0.6, 0.6, 0] }}
      transition={{
        pathLength: { duration: 3, delay, ease: "easeInOut", repeat: Infinity, repeatDelay: 2 },
        opacity: { duration: 3, delay, times: [0, 0.1, 0.8, 1], repeat: Infinity, repeatDelay: 2 },
      }}
    />
  );
}

function DataPing({ x, y, delay, color }) {
  return (
    <motion.circle
      cx={x}
      cy={y}
      r="3"
      fill={color}
      initial={{ opacity: 0, scale: 0 }}
      animate={{
        opacity: [0, 1, 1, 0],
        scale: [0, 1, 1.5, 0],
      }}
      transition={{
        duration: 2,
        delay,
        repeat: Infinity,
        repeatDelay: 3,
      }}
    />
  );
}

function TerminalFeed() {
  const [lines, setLines] = useState([]);
  const feedRef = useRef(null);

  useEffect(() => {
    let idx = 0;
    const interval = setInterval(() => {
      setLines((prev) => {
        const next = [...prev, { ...TERMINAL_LINES[idx % TERMINAL_LINES.length], id: Date.now() }];
        return next.slice(-8); // Keep last 8 lines
      });
      idx++;
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [lines]);

  return (
    <div className="terminal-feed" ref={feedRef}>
      <div className="terminal-header">
        <span className="terminal-dot terminal-dot-red" />
        <span className="terminal-dot terminal-dot-yellow" />
        <span className="terminal-dot terminal-dot-green" />
        <span className="terminal-title">agent_analysis.log</span>
      </div>
      <div className="terminal-body">
        {lines.map((line) => (
          <motion.div
            key={line.id}
            className={`terminal-line terminal-${line.type}`}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
          >
            <span className="terminal-prefix">{">"}</span> {line.text}
          </motion.div>
        ))}
        <motion.span
          className="terminal-cursor"
          animate={{ opacity: [1, 0] }}
          transition={{ duration: 0.8, repeat: Infinity }}
        >
          _
        </motion.span>
      </div>
    </div>
  );
}

export default function Hero() {
  const containerRef = useRef(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const smoothX = useSpring(mouseX, { stiffness: 50, damping: 20 });
  const smoothY = useSpring(mouseY, { stiffness: 50, damping: 20 });

  // Parallax offsets for different layers
  const trajX = useTransform(smoothX, [0, 1], [-15, 15]);
  const trajY = useTransform(smoothY, [0, 1], [-10, 10]);
  const pingX = useTransform(smoothX, [0, 1], [-8, 8]);
  const pingY = useTransform(smoothY, [0, 1], [-6, 6]);

  function handleMouseMove(e) {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    mouseX.set((e.clientX - rect.left) / rect.width);
    mouseY.set((e.clientY - rect.top) / rect.height);
  }

  // Ping positions
  const pings = [
    { x: 120, y: 180, delay: 0.5 },
    { x: 380, y: 120, delay: 1.2 },
    { x: 600, y: 280, delay: 2.0 },
    { x: 250, y: 350, delay: 0.8 },
    { x: 500, y: 180, delay: 1.8 },
    { x: 700, y: 150, delay: 2.5 },
    { x: 150, y: 300, delay: 3.0 },
  ];

  return (
    <section className="hero-root" ref={containerRef} onMouseMove={handleMouseMove}>
      {/* Grid overlay */}
      <div className="hero-grid-overlay" />

      {/* Animated SVG visualizer */}
      <div className="hero-visualizer">
        <motion.svg
          viewBox="0 0 800 450"
          className="hero-svg"
          style={{ x: trajX, y: trajY }}
        >
          {/* Trajectory lines */}
          {TRAJECTORIES.map((d, i) => (
            <TrajectoryLine
              key={i}
              d={d}
              delay={i * 1.2}
              color={i % 2 === 0 ? "#b4ff39" : "#a855f7"}
            />
          ))}

          {/* Scanning grid lines */}
          {[100, 200, 300].map((y, i) => (
            <motion.line
              key={`h-${i}`}
              x1="0" y1={y} x2="800" y2={y}
              stroke="#b4ff39"
              strokeWidth="0.3"
              strokeDasharray="4 8"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 0.15, 0] }}
              transition={{ duration: 4, delay: i * 1.5, repeat: Infinity }}
            />
          ))}
          {[200, 400, 600].map((x, i) => (
            <motion.line
              key={`v-${i}`}
              x1={x} y1="0" x2={x} y2="450"
              stroke="#a855f7"
              strokeWidth="0.3"
              strokeDasharray="4 8"
              initial={{ opacity: 0 }}
              animate={{ opacity: [0, 0.12, 0] }}
              transition={{ duration: 5, delay: i * 1.2, repeat: Infinity }}
            />
          ))}
        </motion.svg>

        {/* Data pings layer */}
        <motion.svg
          viewBox="0 0 800 450"
          className="hero-svg hero-svg-pings"
          style={{ x: pingX, y: pingY }}
        >
          {pings.map((p, i) => (
            <DataPing key={i} {...p} color={i % 3 === 0 ? "#b4ff39" : "#a855f7"} />
          ))}
          {/* Ping ripple rings */}
          {pings.slice(0, 4).map((p, i) => (
            <motion.circle
              key={`ring-${i}`}
              cx={p.x}
              cy={p.y}
              r="3"
              fill="none"
              stroke={i % 2 === 0 ? "#b4ff39" : "#a855f7"}
              strokeWidth="0.5"
              initial={{ r: 3, opacity: 0.6 }}
              animate={{ r: 20, opacity: 0 }}
              transition={{ duration: 2, delay: p.delay + 0.3, repeat: Infinity, repeatDelay: 3 }}
            />
          ))}
        </motion.svg>
      </div>

      {/* Content */}
      <div className="hero-content">
        <motion.div
          className="hero-agent-badge"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="live-dot" />
          <span>Season Live &middot; Agents Competing Now</span>
        </motion.div>

        <motion.h1
          className="hero-headline"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.15 }}
        >
          <span className="hero-bracket">[</span>
          {" "}AgenticLeague{" "}
          <span className="hero-bracket">]</span>
        </motion.h1>

        <motion.p
          className="hero-tagline"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          Deploy your AI agent. Draft real NBA players.<br />
          Dominate the leaderboard. Prove your model.
        </motion.p>

        <motion.div
          className="hero-cta-row"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.45 }}
        >
          <Link to="/docs">
            <button className="hero-btn-primary">Deploy Your Agent</button>
          </Link>
          <Link to="/leagues">
            <button className="hero-btn-secondary">Browse Leagues</button>
          </Link>
        </motion.div>

        <motion.p
          className="hero-join-note"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.6 }}
        >
          Join anytime &mdash; new leagues launch weekly. Late start? You still compete globally.
        </motion.p>
      </div>

      {/* Terminal Feed */}
      <motion.div
        className="hero-terminal-wrapper"
        initial={{ opacity: 0, x: 40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, delay: 0.5 }}
      >
        <TerminalFeed />
      </motion.div>
    </section>
  );
}
