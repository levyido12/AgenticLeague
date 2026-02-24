import { useEffect, useRef } from "react";

const CHARS = ["+", "-", "=", "/", ":", "*", "#", "."];

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

    const isMobile = window.innerWidth < 768;
    const cellSize = isMobile ? 28 : 18;

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      ctx.scale(dpr, dpr);
    }

    resize();

    const ro = new ResizeObserver(resize);
    ro.observe(document.body);

    // Density field functions — sport-themed shapes
    function basketballArc(x, y, cx, cy, r, t) {
      const dx = x - cx;
      const dy = y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const angle = Math.atan2(dy, dx) + t * 0.3;
      const arcDist = Math.abs(dist - r);
      return Math.max(0, 1 - arcDist / 60) * (0.5 + 0.5 * Math.sin(angle * 3));
    }

    function spiralField(x, y, cx, cy, t) {
      const dx = x - cx;
      const dy = y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const angle = Math.atan2(dy, dx);
      return Math.max(0, 1 - dist / 200) * (0.5 + 0.5 * Math.sin(angle * 4 + dist * 0.03 - t * 0.5));
    }

    function stitchCurve(x, y, cx, cy, t) {
      const dx = x - cx;
      const dy = y - cy;
      const wave = Math.sin(dx * 0.02 + t * 0.4) * 40;
      const dist = Math.abs(dy - wave);
      return Math.max(0, 1 - dist / 50) * 0.7;
    }

    function circleField(x, y, cx, cy, r, t) {
      const dx = x - cx;
      const dy = y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const ringDist = Math.abs(dist - r);
      return Math.max(0, 1 - ringDist / 30) * (0.5 + 0.5 * Math.sin(t * 0.6));
    }

    function draw(t) {
      const w = window.innerWidth;
      const h = window.innerHeight;

      ctx.clearRect(0, 0, w, h);
      ctx.font = `${cellSize - 4}px monospace`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      const cols = Math.ceil(w / cellSize);
      const rows = Math.ceil(h / cellSize);

      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = col * cellSize + cellSize / 2;
          const y = row * cellSize + cellSize / 2;

          // Combine density fields from different sport shapes
          let density = 0;
          density += basketballArc(x, y, w * 0.25, h * 0.3, 120, t) * 0.5;
          density += spiralField(x, y, w * 0.75, h * 0.25, t) * 0.4;
          density += stitchCurve(x, y, w * 0.5, h * 0.65, t) * 0.3;
          density += circleField(x, y, w * 0.7, h * 0.7, 80, t) * 0.4;

          // Add subtle noise
          density += Math.sin(x * 0.01 + t * 0.2) * Math.cos(y * 0.01 - t * 0.15) * 0.15;

          if (density < 0.08) continue;

          const alpha = Math.min(0.15, density * 0.15);
          const charIndex = Math.floor((density * 7 + x * 0.1 + y * 0.1) % CHARS.length);

          // Slight green tint for variety on some chars
          const useGreen = (col + row) % 7 === 0;
          if (useGreen) {
            ctx.fillStyle = `rgba(34, 197, 94, ${alpha * 0.6})`;
          } else {
            ctx.fillStyle = `rgba(99, 102, 241, ${alpha})`;
          }

          ctx.fillText(CHARS[charIndex], x, y);
        }
      }
    }

    if (prefersReducedMotion) {
      draw(0);
    } else {
      function animate() {
        timeRef.current += 0.008;
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
