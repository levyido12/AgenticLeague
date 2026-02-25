import { useEffect, useRef } from "react";

// Characters ordered by visual density (light → heavy)
const CHARS = " .·:+*#@";

// ─── Sport Scene Definitions ───
// Each scene is a list of shape primitives that get rasterized to a density field.
// Types: circle, arc, line, rect, bezier

const SCENES = [
  // 0 — Basketball: hoop + backboard + ball trajectory
  {
    name: "basketball",
    shapes: [
      // Backboard
      { type: "rect", cx: 0.72, cy: 0.22, w: 0.02, h: 0.18, density: 0.9 },
      // Rim (half-circle opening down)
      { type: "arc", cx: 0.65, cy: 0.32, r: 0.06, startAngle: 0, endAngle: Math.PI, density: 1.0 },
      // Net lines
      { type: "line", x1: 0.59, y1: 0.32, x2: 0.62, y2: 0.48, density: 0.5 },
      { type: "line", x1: 0.65, y1: 0.32, x2: 0.65, y2: 0.50, density: 0.5 },
      { type: "line", x1: 0.71, y1: 0.32, x2: 0.68, y2: 0.48, density: 0.5 },
      // Ball arc trajectory
      { type: "bezier", x1: 0.15, y1: 0.7, cx1: 0.3, cy1: 0.05, cx2: 0.5, cy2: 0.05, x2: 0.65, y2: 0.28, density: 0.8 },
      // Ball
      { type: "circle", cx: 0.15, cy: 0.7, r: 0.035, density: 1.0 },
      // Court line
      { type: "line", x1: 0.05, y1: 0.85, x2: 0.95, y2: 0.85, density: 0.3 },
      // Three-point arc
      { type: "arc", cx: 0.72, cy: 0.85, r: 0.28, startAngle: Math.PI, endAngle: Math.PI * 1.75, density: 0.25 },
    ],
  },
  // 1 — Football: quarterback throwing a spiral
  {
    name: "football",
    shapes: [
      // Player body (stick figure)
      { type: "circle", cx: 0.25, cy: 0.35, r: 0.03, density: 0.9 }, // head
      { type: "line", x1: 0.25, y1: 0.38, x2: 0.25, y2: 0.58, density: 0.8 }, // torso
      { type: "line", x1: 0.25, y1: 0.42, x2: 0.32, y2: 0.35, density: 0.7 }, // throwing arm
      { type: "line", x1: 0.25, y1: 0.42, x2: 0.18, y2: 0.48, density: 0.6 }, // other arm
      { type: "line", x1: 0.25, y1: 0.58, x2: 0.20, y2: 0.72, density: 0.6 }, // leg
      { type: "line", x1: 0.25, y1: 0.58, x2: 0.30, y2: 0.72, density: 0.6 }, // leg
      // Football (ellipse-ish with spiral lines)
      { type: "circle", cx: 0.34, cy: 0.33, r: 0.025, density: 1.0 },
      // Spiral trajectory
      { type: "bezier", x1: 0.34, y1: 0.33, cx1: 0.5, cy1: 0.1, cx2: 0.65, cy2: 0.15, x2: 0.82, y2: 0.45, density: 0.6 },
      // Spiral rotation marks along path
      { type: "circle", cx: 0.45, cy: 0.18, r: 0.008, density: 0.4 },
      { type: "circle", cx: 0.55, cy: 0.15, r: 0.008, density: 0.4 },
      { type: "circle", cx: 0.65, cy: 0.18, r: 0.008, density: 0.4 },
      { type: "circle", cx: 0.75, cy: 0.30, r: 0.008, density: 0.4 },
      // Goal posts
      { type: "line", x1: 0.85, y1: 0.2, x2: 0.85, y2: 0.75, density: 0.4 },
      { type: "line", x1: 0.80, y1: 0.2, x2: 0.85, y2: 0.2, density: 0.5 },
      { type: "line", x1: 0.90, y1: 0.2, x2: 0.85, y2: 0.2, density: 0.5 },
      // Field lines
      { type: "line", x1: 0.05, y1: 0.75, x2: 0.95, y2: 0.75, density: 0.2 },
      { type: "line", x1: 0.4, y1: 0.72, x2: 0.4, y2: 0.78, density: 0.15 },
      { type: "line", x1: 0.6, y1: 0.72, x2: 0.6, y2: 0.78, density: 0.15 },
    ],
  },
  // 2 — Baseball: batter hitting a home run
  {
    name: "baseball",
    shapes: [
      // Batter (stick figure in swing pose)
      { type: "circle", cx: 0.3, cy: 0.45, r: 0.03, density: 0.9 }, // head
      { type: "line", x1: 0.3, y1: 0.48, x2: 0.3, y2: 0.65, density: 0.8 }, // torso
      { type: "line", x1: 0.3, y1: 0.52, x2: 0.38, y2: 0.46, density: 0.7 }, // bat arm
      { type: "line", x1: 0.38, y1: 0.46, x2: 0.48, y2: 0.40, density: 0.9 }, // bat
      { type: "line", x1: 0.3, y1: 0.65, x2: 0.26, y2: 0.78, density: 0.6 }, // leg
      { type: "line", x1: 0.3, y1: 0.65, x2: 0.34, y2: 0.78, density: 0.6 }, // leg
      // Ball trajectory (home run arc)
      { type: "bezier", x1: 0.48, y1: 0.40, cx1: 0.55, cy1: 0.15, cx2: 0.7, cy2: 0.08, x2: 0.88, y2: 0.2, density: 0.7 },
      // Ball
      { type: "circle", cx: 0.88, cy: 0.2, r: 0.02, density: 1.0 },
      // Impact burst
      { type: "circle", cx: 0.48, cy: 0.40, r: 0.015, density: 0.6 },
      // Diamond
      { type: "line", x1: 0.3, y1: 0.82, x2: 0.50, y2: 0.72, density: 0.3 }, // 1st
      { type: "line", x1: 0.50, y1: 0.72, x2: 0.3, y2: 0.62, density: 0.3 }, // 2nd
      { type: "line", x1: 0.3, y1: 0.62, x2: 0.10, y2: 0.72, density: 0.3 }, // 3rd
      { type: "line", x1: 0.10, y1: 0.72, x2: 0.3, y2: 0.82, density: 0.3 }, // home
      // Bases
      { type: "circle", cx: 0.3, cy: 0.82, r: 0.012, density: 0.5 },
      { type: "circle", cx: 0.50, cy: 0.72, r: 0.012, density: 0.5 },
      { type: "circle", cx: 0.3, cy: 0.62, r: 0.012, density: 0.5 },
      { type: "circle", cx: 0.10, cy: 0.72, r: 0.012, density: 0.5 },
    ],
  },
  // 3 — Soccer: goal kick
  {
    name: "soccer",
    shapes: [
      // Kicker
      { type: "circle", cx: 0.35, cy: 0.5, r: 0.03, density: 0.9 }, // head
      { type: "line", x1: 0.35, y1: 0.53, x2: 0.35, y2: 0.68, density: 0.8 }, // torso
      { type: "line", x1: 0.35, y1: 0.56, x2: 0.28, y2: 0.60, density: 0.6 }, // arm
      { type: "line", x1: 0.35, y1: 0.56, x2: 0.42, y2: 0.60, density: 0.6 }, // arm
      { type: "line", x1: 0.35, y1: 0.68, x2: 0.30, y2: 0.82, density: 0.6 }, // standing leg
      { type: "line", x1: 0.35, y1: 0.68, x2: 0.42, y2: 0.72, density: 0.8 }, // kicking leg
      // Ball
      { type: "circle", cx: 0.44, cy: 0.72, r: 0.025, density: 1.0 },
      // Ball trajectory into goal
      { type: "bezier", x1: 0.44, y1: 0.72, cx1: 0.55, cy1: 0.35, cx2: 0.7, cy2: 0.30, x2: 0.82, y2: 0.45, density: 0.6 },
      // Goal frame
      { type: "line", x1: 0.75, y1: 0.3, x2: 0.75, y2: 0.7, density: 0.7 }, // left post
      { type: "line", x1: 0.92, y1: 0.3, x2: 0.92, y2: 0.7, density: 0.7 }, // right post
      { type: "line", x1: 0.75, y1: 0.3, x2: 0.92, y2: 0.3, density: 0.7 }, // crossbar
      // Net grid
      { type: "line", x1: 0.80, y1: 0.3, x2: 0.80, y2: 0.7, density: 0.2 },
      { type: "line", x1: 0.85, y1: 0.3, x2: 0.85, y2: 0.7, density: 0.2 },
      { type: "line", x1: 0.75, y1: 0.43, x2: 0.92, y2: 0.43, density: 0.2 },
      { type: "line", x1: 0.75, y1: 0.57, x2: 0.92, y2: 0.57, density: 0.2 },
      // Field
      { type: "line", x1: 0.05, y1: 0.82, x2: 0.95, y2: 0.82, density: 0.2 },
    ],
  },
];

// ─── Rasterize shape to density at point ───
function sampleShape(shape, nx, ny) {
  switch (shape.type) {
    case "circle": {
      const dx = nx - shape.cx;
      const dy = ny - shape.cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < shape.r) {
        return shape.density * (1 - dist / shape.r);
      }
      // Slight glow outside
      if (dist < shape.r * 1.8) {
        return shape.density * 0.2 * (1 - (dist - shape.r) / (shape.r * 0.8));
      }
      return 0;
    }
    case "arc": {
      const dx = nx - shape.cx;
      const dy = ny - shape.cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const angle = Math.atan2(dy, dx);
      const normAngle = angle < 0 ? angle + Math.PI * 2 : angle;
      const inAngle = normAngle >= shape.startAngle && normAngle <= shape.endAngle;
      if (inAngle && Math.abs(dist - shape.r) < 0.015) {
        return shape.density * (1 - Math.abs(dist - shape.r) / 0.015);
      }
      return 0;
    }
    case "line": {
      const lx = shape.x2 - shape.x1;
      const ly = shape.y2 - shape.y1;
      const len2 = lx * lx + ly * ly;
      if (len2 === 0) return 0;
      const t = Math.max(0, Math.min(1, ((nx - shape.x1) * lx + (ny - shape.y1) * ly) / len2));
      const px = shape.x1 + t * lx;
      const py = shape.y1 + t * ly;
      const dist = Math.sqrt((nx - px) ** 2 + (ny - py) ** 2);
      const thickness = 0.012;
      if (dist < thickness) {
        return shape.density * (1 - dist / thickness);
      }
      return 0;
    }
    case "rect": {
      const hw = shape.w / 2;
      const hh = shape.h / 2;
      const dx = Math.abs(nx - shape.cx);
      const dy = Math.abs(ny - shape.cy);
      if (dx < hw && dy < hh) {
        const edgeDist = Math.min(hw - dx, hh - dy);
        return shape.density * Math.min(1, edgeDist * 30);
      }
      return 0;
    }
    case "bezier": {
      // Sample cubic bezier at many points and find closest
      let minDist = 1;
      for (let t = 0; t <= 1; t += 0.02) {
        const it = 1 - t;
        const bx =
          it * it * it * shape.x1 +
          3 * it * it * t * shape.cx1 +
          3 * it * t * t * shape.cx2 +
          t * t * t * shape.x2;
        const by =
          it * it * it * shape.y1 +
          3 * it * it * t * shape.cy1 +
          3 * it * t * t * shape.cy2 +
          t * t * t * shape.y2;
        const dist = Math.sqrt((nx - bx) ** 2 + (ny - by) ** 2);
        if (dist < minDist) minDist = dist;
      }
      const thickness = 0.015;
      if (minDist < thickness) {
        return shape.density * (1 - minDist / thickness);
      }
      return 0;
    }
    default:
      return 0;
  }
}

function sampleScene(scene, nx, ny) {
  let maxD = 0;
  for (const shape of scene.shapes) {
    const d = sampleShape(shape, nx, ny);
    if (d > maxD) maxD = d;
  }
  return maxD;
}

// ─── Precompute scene grids for performance ───
function precomputeSceneGrid(scene, cols, rows) {
  const grid = new Float32Array(cols * rows);
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const nx = col / cols;
      const ny = row / rows;
      grid[row * cols + col] = sampleScene(scene, nx, ny);
    }
  }
  return grid;
}

export default function AsciiBackground() {
  const canvasRef = useRef(null);
  const animRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    let isMobile = window.innerWidth < 768;
    let cellSize = isMobile ? 18 : 14;
    let w, h, cols, rows;
    let sceneGrids = [];
    const SCENE_DURATION = 5; // seconds per scene
    const MORPH_DURATION = 1.5; // seconds for crossfade

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      isMobile = w < 768;
      cellSize = isMobile ? 18 : 14;
      cols = Math.ceil(w / cellSize);
      rows = Math.ceil(h / cellSize);

      // Precompute all scene grids at new resolution
      sceneGrids = SCENES.map((scene) => precomputeSceneGrid(scene, cols, rows));
    }

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(document.body);

    function draw(t) {
      ctx.clearRect(0, 0, w, h);
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      const totalCycle = SCENE_DURATION + MORPH_DURATION;
      const totalTime = SCENES.length * totalCycle;
      const cycleT = t % totalTime;
      const sceneIdx = Math.floor(cycleT / totalCycle) % SCENES.length;
      const withinScene = cycleT - sceneIdx * totalCycle;

      let alpha1 = 1;
      let alpha2 = 0;
      let nextIdx = (sceneIdx + 1) % SCENES.length;

      if (withinScene > SCENE_DURATION) {
        // In morph transition
        const morphProgress = (withinScene - SCENE_DURATION) / MORPH_DURATION;
        alpha1 = 1 - morphProgress;
        alpha2 = morphProgress;
      }

      const grid1 = sceneGrids[sceneIdx];
      const grid2 = sceneGrids[nextIdx];
      if (!grid1 || !grid2) return;

      const fontSize = cellSize - (isMobile ? 6 : 4);
      ctx.font = `${fontSize}px monospace`;

      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const idx = row * cols + col;
          const density = grid1[idx] * alpha1 + grid2[idx] * alpha2;

          if (density < 0.02) continue;

          const x = col * cellSize + cellSize / 2;
          const y = row * cellSize + cellSize / 2;

          const charIdx = Math.min(
            CHARS.length - 1,
            Math.floor(density * CHARS.length)
          );
          const ch = CHARS[charIdx];
          if (ch === " ") continue;

          const opacity = 0.06 + density * 0.35;

          // Green for high density (main shapes), purple for lower density (ambient)
          if (density > 0.5) {
            ctx.fillStyle = `rgba(180, 255, 57, ${opacity})`;
          } else if (density > 0.25) {
            ctx.fillStyle = `rgba(180, 255, 57, ${opacity * 0.7})`;
          } else {
            ctx.fillStyle = `rgba(168, 85, 247, ${opacity * 0.6})`;
          }

          ctx.fillText(ch, x, y);
        }
      }
    }

    if (prefersReducedMotion) {
      draw(0);
    } else {
      let startTime = null;
      function animate(ts) {
        if (!startTime) startTime = ts;
        const elapsed = (ts - startTime) / 1000;
        draw(elapsed);
        animRef.current = requestAnimationFrame(animate);
      }
      animRef.current = requestAnimationFrame(animate);
    }

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      ro.disconnect();
    };
  }, []);

  return (
    <div className="ascii-bg-wrapper">
      <canvas ref={canvasRef} />
    </div>
  );
}
