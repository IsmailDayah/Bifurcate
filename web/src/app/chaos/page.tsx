"use client";

import { useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, CartesianGrid } from "recharts";
import Card from "@/components/Card";
import Bifurcation from "@/viz/Bifurcation";
import Cobweb from "@/viz/Cobweb";

const PRESETS = [
  { r: 2.8, label: "Calm", note: "one value" },
  { r: 3.2, label: "Splits in two", note: "period-2" },
  { r: 3.5, label: "Splits again", note: "period-4" },
  { r: 3.5699, label: "Chaos onset", note: "≈ 3.57" },
  { r: 3.99, label: "Our cipher", note: "r = 3.99" },
];

/** Settle, then classify the long-term behavior of x → r·x·(1−x). */
function regime(r: number, x0: number): { period: number; label: string; tone: string } {
  let x = Math.min(0.999, Math.max(0.001, x0));
  for (let i = 0; i < 2000; i++) x = r * x * (1 - x);
  const tail: number[] = [];
  for (let i = 0; i < 200; i++) { x = r * x * (1 - x); tail.push(x); }
  const n = tail.length;
  for (let p = 1; p <= 8; p++) {
    let ok = true;
    for (let k = 0; k < 12; k++) {
      if (Math.abs(tail[n - 1 - k]! - tail[n - 1 - k - p]!) > 1e-4) { ok = false; break; }
    }
    if (ok) {
      if (p === 1) return { period: 1, label: "Settles to one value", tone: "text-royal" };
      return { period: p, label: `Repeats every ${p} steps (period-${p})`, tone: "text-royal" };
    }
  }
  return { period: 0, label: "Never repeats — chaotic", tone: "text-trail" };
}

export default function ChaosPage() {
  const [r, setR] = useState(3.99);
  const [x0, setX0] = useState(0.5);
  const [n, setN] = useState(80);

  const orbit = useMemo(() => {
    const pts: { n: number; x: number }[] = [];
    let x = Math.min(0.999, Math.max(0.001, x0));
    pts.push({ n: 0, x });
    for (let i = 1; i <= n; i++) { x = r * x * (1 - x); pts.push({ n: i, x }); }
    return pts;
  }, [r, x0, n]);

  const reg = useMemo(() => regime(r, x0), [r, x0]);

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="font-display text-3xl font-bold">The Chaos Engine, live</h1>
      <p className="mt-2 max-w-2xl text-[15px] text-ink-muted">
        Everything in Bifurcate is seeded by one tiny equation. Turn the dial <b className="text-ink">r</b> and
        watch a single calm value <b className="text-ink">split into two</b>, then four, then collapse into
        chaos. That collapse is a <b className="text-ink">bifurcation</b> — and it is where the cipher gets its
        randomness.
      </p>

      {/* formula */}
      <Card kicker="The equation" title="The logistic map" className="mt-8">
        <div className="flex flex-col items-center gap-2 rounded-xl border border-line bg-surface-overlay py-6">
          <div className="font-display text-2xl sm:text-3xl">
            x<sub className="text-base">n+1</sub>&nbsp;=&nbsp;
            <span className="text-trail">r</span>&nbsp;·&nbsp;x<sub className="text-base">n</sub>&nbsp;·&nbsp;(1&nbsp;−&nbsp;x<sub className="text-base">n</sub>)
          </div>
          <div className="max-w-xl px-4 text-center text-sm text-ink-muted">
            Take a number <b className="text-ink">x</b> between 0 and 1, multiply it by the growth dial{" "}
            <b className="text-trail">r</b> and by how far it is from 1 — that gives the next number. Feed it
            back in and repeat. Nothing here is random; the same start always gives the same path.
          </div>
        </div>
      </Card>

      {/* controls */}
      <Card kicker="Your turn" title="Choose the numbers" className="mt-6">
        <div className="flex flex-wrap gap-2">
          {PRESETS.map((p) => (
            <button
              key={p.r}
              onClick={() => setR(p.r)}
              className={`ui-t rounded-full border px-3 py-1.5 text-xs font-semibold ${
                Math.abs(r - p.r) < 1e-6
                  ? "border-trail bg-trail/15 text-trail"
                  : "border-line bg-surface-raised text-ink-muted hover:border-ink-muted hover:text-ink"
              }`}
            >
              {p.label} <span className="tnum opacity-85">· {p.note}</span>
            </button>
          ))}
        </div>

        <div className="mt-6 grid gap-6 sm:grid-cols-3">
          <label className="block">
            <div className="mb-1 flex items-baseline justify-between text-sm">
              <span className="font-semibold">Growth dial <span className="text-trail">r</span></span>
              <span className="tnum text-ink-muted">{r.toFixed(3)}</span>
            </div>
            <input type="range" min={2.5} max={4} step={0.001} value={r}
              onChange={(e) => setR(parseFloat(e.target.value))}
              className="w-full accent-trail" />
            <div className="mt-1 flex justify-between text-[11px] text-ink-muted"><span>2.5</span><span>4.0</span></div>
          </label>

          <label className="block">
            <div className="mb-1 flex items-baseline justify-between text-sm">
              <span className="font-semibold">Seed x<sub>0</sub></span>
              <span className="tnum text-ink-muted">{x0.toFixed(3)}</span>
            </div>
            <input type="range" min={0.01} max={0.99} step={0.001} value={x0}
              onChange={(e) => setX0(parseFloat(e.target.value))}
              className="w-full accent-trail" />
            <div className="mt-1 flex justify-between text-[11px] text-ink-muted"><span>0.01</span><span>0.99</span></div>
          </label>

          <label className="block">
            <div className="mb-1 flex items-baseline justify-between text-sm">
              <span className="font-semibold">Iterations</span>
              <span className="tnum text-ink-muted">{n}</span>
            </div>
            <input type="range" min={20} max={200} step={1} value={n}
              onChange={(e) => setN(parseInt(e.target.value))}
              className="w-full accent-trail" />
            <div className="mt-1 flex justify-between text-[11px] text-ink-muted"><span>20</span><span>200</span></div>
          </label>
        </div>

        <div className="mt-5 flex items-center gap-2 rounded-xl border border-line bg-surface-overlay px-4 py-3 text-sm">
          <span className="text-ink-muted">Long-term behavior at r = {r.toFixed(3)}:</span>
          <span className={`font-semibold ${reg.tone}`}>{reg.label}</span>
        </div>
      </Card>

      {/* orbit + cobweb */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card kicker="The orbit" title="Each step, in order">
          <p className="mb-3 text-sm text-ink-muted">
            The value after every iteration. Flat = calm; a zig-zag = it alternates; a jagged mess = chaos.
          </p>
          <div className="rounded-xl border border-line bg-surface-overlay p-2">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={orbit} margin={{ top: 8, right: 14, bottom: 6, left: -12 }}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                <XAxis dataKey="n" stroke="#94a3b8" fontSize={12}
                  label={{ value: "iteration n", position: "insideBottom", offset: -2, fill: "#94a3b8", fontSize: 12 }} />
                <YAxis domain={[0, 1]} stroke="#94a3b8" fontSize={12} width={44} />
                <Line type="monotone" dataKey="x" stroke="#f59e0b" strokeWidth={2}
                  dot={n <= 60 ? { r: 2, fill: "#f59e0b" } : false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card kicker="The cobweb" title="Bouncing off the curve">
          <p className="mb-3 text-sm text-ink-muted">
            The blue arch is the equation; the orbit climbs to it and slides to the diagonal, over and over.
            A point that spirals inward is stable; a shape that fills the box is chaos.
          </p>
          <Cobweb r={r} x0={x0} steps={Math.min(n, 90)} height={260} />
        </Card>
      </div>

      {/* bifurcation with live marker */}
      <Card kicker="The whole picture" title="Where your r lives on the map" className="mt-6">
        <p className="mb-4 text-sm text-ink-muted">
          Every vertical slice shows the long-term values for one r. Left: one line. Move right and it forks —
          <b className="text-ink"> bifurcates</b> — into 2, 4, 8, then a chaotic haze. The green line is{" "}
          <b className="text-ink">your</b> r. Drag the dial above and watch it travel.
        </p>
        <Bifurcation height={360} marker={r} markerLabel={`r = ${r.toFixed(3)}`} />
        <p className="mt-3 text-xs text-ink-muted">
          Chaos begins near r ≈ 3.57. The cipher runs at the far right, <b className="text-ink">r = 3.99</b>,
          deep in the chaotic band — where the values never settle and never repeat.
        </p>
      </Card>

      {/* connect to the cipher */}
      <Card kicker="Why it matters" title="From this equation to your keys" className="mt-6">
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="text-sm leading-relaxed text-ink-muted">
            <p>
              At <b className="text-ink">r = 3.99</b> the orbit you see above never repeats, and a one-character
              change to your passphrase starts it at a completely different seed — sending it down a totally
              different path. That sensitivity is exactly what a cipher wants.
            </p>
            <p className="mt-3">
              Bifurcate harvests this stream, <b className="text-ink">whitens it with SHA-256</b>, and uses the
              result to shuffle the S-box and grow all 12 round keys. Your password, through this equation,
              literally builds the lock.
            </p>
          </div>
          <div className="min-w-0 rounded-xl border border-line bg-surface-overlay p-4">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink-muted">
              What the cipher actually runs
            </div>
            <pre
              role="region"
              aria-label="The integer logistic map the cipher runs"
              tabIndex={0}
              className="tnum overflow-x-auto text-[12.5px] leading-relaxed text-ink focus:outline-none focus-visible:ring-1 focus-visible:ring-trail"
            >
{`// integer, fixed-point — identical on
// every machine (no float drift)
R_FIXED = round(3.99 · 2^20)
SCALE   = 2^32
step(x) = R_FIXED·x·(SCALE − x) / (SCALE·2^20)`}
            </pre>
            <p className="mt-3 text-xs text-ink-muted">
              Same equation as the slider — but in whole numbers, so the Python reference and this website
              produce byte-for-byte identical keystreams.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
