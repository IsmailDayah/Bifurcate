"use client";

import { useEffect, useRef } from "react";

/**
 * The bifurcation diagram of the logistic map x -> r*x*(1-x), drawn on canvas.
 * Amber points on slate; a green marker breathes at r = 3.99 (our operating
 * point). This is DECORATION-GRADE float math — deliberately separate from the
 * cipher's integer engine (see /how-it-works).
 */
export default function Bifurcation({
  height = 420,
  rMin = 2.6,
  rMax = 4.0,
  marker = 3.99,
  markerLabel = "r = 3.99 — our operating point",
}: {
  height?: number;
  rMin?: number;
  rMax?: number;
  marker?: number;
  markerLabel?: string;
}) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    let raf = 0;
    let t = 0;

    const draw = () => {
      const parent = canvas.parentElement!;
      const w = parent.clientWidth;
      const h = height;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;
      const ctx = canvas.getContext("2d")!;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);

      // scatter
      const cols = Math.floor(w);
      ctx.fillStyle = "rgba(245, 158, 11, 0.34)";
      for (let px = 0; px < cols; px++) {
        const r = rMin + ((rMax - rMin) * px) / cols;
        let x = 0.5;
        for (let i = 0; i < 110; i++) x = r * x * (1 - x); // settle
        for (let i = 0; i < 90; i++) {
          x = r * x * (1 - x);
          const py = h - x * h;
          ctx.fillRect(px, py, 1, 1);
        }
      }

      // operating-point marker (breathing)
      const mx = ((marker - rMin) / (rMax - rMin)) * w;
      const pulse = 0.5 + 0.5 * Math.sin(t / 30);
      ctx.strokeStyle = `rgba(22, 163, 74, ${0.5 + 0.4 * pulse})`;
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 5]);
      ctx.beginPath();
      ctx.moveTo(mx, 0);
      ctx.lineTo(mx, h);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#4ade80";
      ctx.font = "600 12px Inter, sans-serif";
      ctx.fillText(markerLabel, Math.min(mx + 8, w - 210), 20);
    };

    const loop = () => {
      t += 1;
      draw();
      raf = requestAnimationFrame(loop);
    };
    loop();
    const onResize = () => draw();
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
    };
  }, [height, rMin, rMax, marker, markerLabel]);

  return (
    <div className="relative w-full overflow-hidden rounded-2xl border border-line bg-surface-overlay">
      <canvas ref={ref} className="block w-full" />
      <div className="pointer-events-none absolute bottom-2 left-3 text-[11px] text-ink-muted">
        logistic map · chaos onset ≈ 3.57
      </div>
    </div>
  );
}
