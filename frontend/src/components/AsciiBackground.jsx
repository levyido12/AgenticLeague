import { useEffect, useRef } from "react";

// Characters ordered by visual density (light → heavy)
const DENSITY_CHARS = " .·:+*#@";

// Simple 2D noise implementation (value noise with smoothing)
function hash(x, y) {
  let h = x * 374761393 + y * 668265263;
  h = (h ^ (h >> 13)) * 1274126177;
  return ((h ^ (h >> 16)) & 0x7fffffff) / 0x7fffffff;
}

function smoothNoise(x, y) {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const fx = x - ix;
  const fy = y - iy;

  // Smoothstep
  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);

  const n00 = hash(ix, iy);
  const n10 = hash(ix + 1, iy);
  const n01 = hash(ix, iy + 1);
  const n11 = hash(ix + 1, iy + 1);

  return (
    n00 * (1 - sx) * (1 - sy) +
    n10 * sx * (1 - sy) +
    n01 * (1 - sx) * sy +
    n11 * sx * sy
  );
}

function fractalNoise(x, y, octaves = 4) {
  let val = 0;
  let amp = 1;
  let freq = 1;
  let maxAmp = 0;
  for (let i = 0; i < octaves; i++) {
    val += smoothNoise(x * freq, y * freq) * amp;
    maxAmp += amp;
    amp *= 0.5;
    freq *= 2;
  }
  return val / maxAmp;
}

export default function AsciiBackground() {
  const canvasRef = useRef(null);
  const animRef = useRef(null);
  const timeRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    let isMobile = window.innerWidth < 768;
    let cellSize = isMobile ? 20 : 14;
    let w, h, cols, rows;

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
      cellSize = isMobile ? 20 : 14;
      cols = Math.ceil(w / cellSize);
      rows = Math.ceil(h / cellSize);
    }

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(document.body);

    // Sport-shaped density modifiers
    function sportShapes(x, y, t, maxW, maxH) {
      let bonus = 0;

      // Basketball arc (top-left region)
      const bx = x - maxW * 0.2;
      const by = y - maxH * 0.25;
      const bDist = Math.sqrt(bx * bx + by * by);
      const arcR = 140 + Math.sin(t * 0.3) * 20;
      bonus += Math.max(0, 1 - Math.abs(bDist - arcR) / 35) * 0.5;

      // Football spiral (right region)
      const fx = x - maxW * 0.78;
      const fy = y - maxH * 0.35;
      const fDist = Math.sqrt(fx * fx + fy * fy);
      const fAngle = Math.atan2(fy, fx);
      bonus += Math.max(0, 1 - fDist / 160) * Math.abs(Math.sin(fAngle * 3 + fDist * 0.04 - t * 0.5)) * 0.4;

      // Baseball stitch wave (center-bottom)
      const stitchY = maxH * 0.7 + Math.sin(x * 0.015 + t * 0.4) * 50;
      bonus += Math.max(0, 1 - Math.abs(y - stitchY) / 40) * 0.35;

      // Soccer circle (bottom-left)
      const sx = x - maxW * 0.3;
      const sy = y - maxH * 0.75;
      const sDist = Math.sqrt(sx * sx + sy * sy);
      const sR = 70 + Math.sin(t * 0.5) * 10;
      bonus += Math.max(0, 1 - Math.abs(sDist - sR) / 25) * 0.4;

      return bonus;
    }

    function draw(t) {
      ctx.clearRect(0, 0, w, h);
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      const noiseScale = 0.04;
      const timeScale = t * 0.15;

      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = col * cellSize + cellSize / 2;
          const y = row * cellSize + cellSize / 2;

          // Multi-octave noise for topographic feel
          const nx = col * noiseScale + timeScale;
          const ny = row * noiseScale + timeScale * 0.7;
          let density = fractalNoise(nx, ny, 4);

          // Add sport shape contours
          density += sportShapes(x, y, t, w, h);

          // Create contour lines (topographic effect)
          const contourFreq = 8;
          const contourVal = (density * contourFreq) % 1;
          const contourEdge = Math.min(contourVal, 1 - contourVal) * 2;
          const isContourLine = contourEdge < 0.15;

          // Boost density on contour lines
          if (isContourLine) {
            density = Math.min(1, density + 0.3);
          }

          // Map density to character
          const charIdx = Math.min(
            DENSITY_CHARS.length - 1,
            Math.floor(density * DENSITY_CHARS.length)
          );
          const ch = DENSITY_CHARS[charIdx];
          if (ch === " ") continue;

          // Opacity: higher density = more visible
          const alpha = 0.03 + density * 0.12;

          // Color: neon green for contour lines, purple for fill
          const useGreen = isContourLine || (col + row * 7) % 11 === 0;
          const fontSize = cellSize - (isMobile ? 6 : 4);

          ctx.font = `${fontSize}px monospace`;

          if (useGreen) {
            ctx.fillStyle = `rgba(180, 255, 57, ${alpha * 1.2})`;
          } else {
            ctx.fillStyle = `rgba(168, 85, 247, ${alpha * 0.8})`;
          }

          ctx.fillText(ch, x, y);
        }
      }
    }

    if (prefersReducedMotion) {
      draw(0);
    } else {
      function animate() {
        timeRef.current += 0.012;
        draw(timeRef.current);
        animRef.current = requestAnimationFrame(animate);
      }
      animate();
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
