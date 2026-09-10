"use client";

import { useEffect, useRef } from "react";

/**
 * Cobweb (staircase) plot of the logistic map x -> r*x*(1-x).
 * Draws the parabola f(x), the diagonal y = x, and the orbit that bounces
 * between them from a seed x0. A fixed point spirals to a point; period-2
 * traces a rectangle; chaos fills the box. Pure decoration-grade float math,
 * kept separate from the cipher's integer engine.
 */
export default function Cobweb({
  r,
  x0,
  steps = 60,
  height = 300,
}: {
  r: number;
  x0: number;
  steps?: number;
  height?: number;
}) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

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

      const pad = 34;
      const X = (x: number) => pad + x * (w - pad - 10);
      const Y = (y: number) => h - pad - y * (h - pad - 10);

      // axes
      ctx.strokeStyle = "rgba(148,163,184,0.35)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(X(0), Y(0)); ctx.lineTo(X(1), Y(0));
      ctx.moveTo(X(0), Y(0)); ctx.lineTo(X(0), Y(1));
      ctx.stroke();
      ctx.fillStyle = "rgba(100,116,139,0.9)";
      ctx.font = "11px Inter, sans-serif";
      ctx.fillText("xₙ", X(1) - 14, Y(0) + 16);
      ctx.fillText("xₙ₊₁", X(0) - 2, Y(1) - 6);

      // diagonal y = x
      ctx.strokeStyle = "rgba(100,116,139,0.55)";
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(X(0), Y(0)); ctx.lineTo(X(1), Y(1)); ctx.stroke();
      ctx.setLineDash([]);

      // parabola f(x) = r x (1 - x)
      ctx.strokeStyle = "#2563eb";
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i <= 200; i++) {
        const x = i / 200;
        const y = r * x * (1 - x);
        if (i === 0) ctx.moveTo(X(x), Y(y));
        else ctx.lineTo(X(x), Y(y));
      }
      ctx.stroke();

      // cobweb orbit
      ctx.strokeStyle = "rgba(245,158,11,0.85)";
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      let x = Math.min(0.999, Math.max(0.001, x0));
      ctx.moveTo(X(x), Y(0));
      for (let i = 0; i < steps; i++) {
        const fx = r * x * (1 - x);
        ctx.lineTo(X(x), Y(fx)); // up/down to the curve
        ctx.lineTo(X(fx), Y(fx)); // across to the diagonal
        x = fx;
      }
      ctx.stroke();

      // seed dot
      ctx.fillStyle = "#f59e0b";
      ctx.beginPath();
      ctx.arc(X(Math.min(0.999, Math.max(0.001, x0))), Y(0), 3.2, 0, Math.PI * 2);
      ctx.fill();
    };

    draw();
    const onResize = () => draw();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [r, x0, steps, height]);

  return (
    <div className="relative w-full overflow-hidden rounded-2xl border border-line bg-surface-overlay">
      <canvas ref={ref} className="block w-full" />
      <div className="pointer-events-none absolute right-3 top-2 text-[11px] text-ink-muted">
        <span className="text-royal">parabola f(x)</span> · <span className="text-trail">the orbit</span>
      </div>
    </div>
  );
}
