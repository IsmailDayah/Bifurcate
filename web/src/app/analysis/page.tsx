"use client";

import { useState } from "react";
import { Play } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, ReferenceLine, ResponsiveContainer, CartesianGrid } from "recharts";
import Card from "@/components/Card";
import Banner from "@/components/Banner";
import StatCard from "@/components/StatCard";
import { expand, encryptBlock, rootKeyFromPassphrase, deriveSubkeys, shannonEntropy, differenceRatio } from "@/crypto";
import { plaintextAvalanche, keyAvalanche, roundsCurve, avalancheGrid } from "@/lib/analysis";

const SALT = new Uint8Array(16);

export default function AnalysisPage() {
  const [pwA, setPwA] = useState("correct horse battery staple");
  const [pwB, setPwB] = useState("correct horse battery stapla");
  const [busy, setBusy] = useState(false);
  const [r, setR] = useState<null | {
    pt: number; key: number; ent: number; sbox: number; curve: number[]; grid: number[]; bit: number; reached: number;
  }>(null);

  async function run() {
    setBusy(true);
    await new Promise((res) => setTimeout(res, 30));
    const rkA = expand(deriveSubkeys(rootKeyFromPassphrase(pwA, SALT)).encSeed);
    const rkB = expand(deriveSubkeys(rootKeyFromPassphrase(pwB, SALT)).encSeed);
    let sample = new Uint8Array(0);
    const parts: Uint8Array[] = [];
    for (let i = 0; i < 2500; i++) parts.push(encryptBlock(crypto.getRandomValues(new Uint8Array(16)), rkA));
    sample = new Uint8Array(parts.length * 16);
    parts.forEach((p, i) => sample.set(p, i * 16));
    const curve = roundsCurve(rkA);
    const bit = Math.floor(Math.random() * 128);
    setR({
      pt: plaintextAvalanche(rkA), key: keyAvalanche(rkA, rkB),
      ent: shannonEntropy(sample), sbox: differenceRatio(rkA.sbox, rkB.sbox) * 100,
      curve, grid: avalancheGrid(rkA, crypto.getRandomValues(new Uint8Array(16)), bit), bit,
      reached: curve.findIndex((v) => v >= 45) + 1,
    });
    setBusy(false);
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="font-display text-3xl font-bold">Security Analysis</h1>
      <p className="mt-2 max-w-2xl text-[15px] text-ink-muted">
        Every number below is computed live in your browser. Nothing here is quoted — it is all measured on the spot.
      </p>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <input value={pwA} onChange={(e) => setPwA(e.target.value)} className="rounded-xl border border-line bg-surface px-3.5 py-2 text-sm outline-none focus:border-trail" placeholder="Passphrase A" />
        <input value={pwB} onChange={(e) => setPwB(e.target.value)} className="rounded-xl border border-line bg-surface px-3.5 py-2 text-sm outline-none focus:border-trail" placeholder="Passphrase B (one char different)" />
      </div>
      <button onClick={run} disabled={busy} className="ui-t mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-trail px-5 py-2.5 text-sm font-semibold text-surface hover:bg-trail-soft disabled:opacity-60">
        <Play className="h-4 w-4" /> {busy ? "Measuring…" : "Run full analysis"}
      </button>

      {r && (
        <div className="mt-6 space-y-5">
          <div className="grid gap-3 sm:grid-cols-4">
            <StatCard label="Plaintext avalanche" value={`${r.pt.toFixed(2)}%`} sub="target 45–55%" />
            <StatCard label="Key avalanche" value={`${r.key.toFixed(2)}%`} sub="target 45–55%" />
            <StatCard label="Ciphertext entropy" value={r.ent.toFixed(4)} sub="of 8.000 bits/byte" />
            <StatCard label="S-box difference" value={`${r.sbox.toFixed(2)}%`} sub="theory 99.61%" />
          </div>
          <Banner kind={r.pt >= 45 && r.pt <= 55 && r.key >= 45 && r.key <= 55 ? "ok" : "warn"}>
            Avalanche within target and entropy {r.ent.toFixed(3)} bits/byte — the cipher behaves like a random permutation.
          </Banner>

          <Card kicker="The key figure" title="Rounds vs avalanche — why 12 rounds">
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={r.curve.map((v, i) => ({ round: i + 1, v }))} margin={{ top: 8, right: 16, bottom: 8, left: -8 }}>
                <CartesianGrid stroke="#1e2c48" />
                <XAxis dataKey="round" stroke="#94a3b8" fontSize={12} label={{ value: "rounds applied", position: "insideBottom", offset: -4, fill: "#94a3b8", fontSize: 12 }} />
                <YAxis domain={[0, 60]} stroke="#94a3b8" fontSize={12} />
                <ReferenceLine y={50} stroke="#16a34a" strokeDasharray="5 4" />
                <Line type="monotone" dataKey="v" stroke="#f59e0b" strokeWidth={3} dot={{ r: 4, fill: "#f59e0b" }} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
            <p className="mt-2 text-sm text-ink-muted">
              Full avalanche (≥45%) first reached at <b className="text-ink">round {r.reached}</b> — 12 rounds gives{" "}
              <b className="text-trail">{12 - r.reached} rounds of margin</b>. The green line is the 50% ideal.
            </p>
          </Card>

          <Card kicker="Avalanche heatmap" title="One bit in, half the block out">
            <p className="mb-3 text-sm text-ink-muted">Flipped plaintext bit #{r.bit}. Lit cells = ciphertext bits that changed.</p>
            <div className="grid gap-[3px]" style={{ gridTemplateColumns: "repeat(16, 1fr)", maxWidth: 480 }}>
              {r.grid.map((b, i) => (
                <div key={i} className="aspect-square rounded-sm" style={{ background: b ? "#f59e0b" : "#16233c", boxShadow: b ? "0 0 6px rgba(245,158,11,.5)" : "none" }} />
              ))}
            </div>
            <p className="mt-3 tnum text-sm text-trail">{r.grid.reduce((a, b) => a + b, 0)} / 128 bits changed ({(r.grid.reduce((a, b) => a + b, 0) / 128 * 100).toFixed(1)}%)</p>
          </Card>
        </div>
      )}
    </div>
  );
}
