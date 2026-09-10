"use client";

import { useMemo, useState } from "react";
import { Dice5 } from "lucide-react";
import Card from "@/components/Card";
import { expand, F, rootKeyFromPassphrase, deriveSubkeys } from "@/crypto";

const toHex = (b: Uint8Array) => Array.from(b, (x) => x.toString(16).padStart(2, "0").toUpperCase());
const SALT = new Uint8Array(16);

export default function RoundsPage() {
  const [pass, setPass] = useState("correct horse battery staple");
  const [blockHex, setBlockHex] = useState("00112233445566778899AABBCCDDEEFF");

  const { states, keys, rots, cipher, error } = useMemo(() => {
    const clean = blockHex.replace(/[^0-9a-fA-F]/g, "");
    if (clean.length !== 32) return { states: [], keys: [], rots: [], cipher: "", error: "Enter 32 hex digits (16 bytes)." };
    const block = new Uint8Array(16);
    for (let i = 0; i < 16; i++) block[i] = parseInt(clean.slice(i * 2, i * 2 + 2), 16);
    const rk = expand(deriveSubkeys(rootKeyFromPassphrase(pass, SALT)).encSeed);
    const states: { l: Uint8Array; r: Uint8Array }[] = [{ l: block.slice(0, 8), r: block.slice(8) }];
    let left = block.slice(0, 8), right = block.slice(8);
    for (let i = 0; i < 12; i++) {
      const f = F(right, rk.keys[i]!, rk.rots[i]!, rk.sbox);
      const nr = new Uint8Array(8);
      for (let j = 0; j < 8; j++) nr[j] = left[j]! ^ f[j]!;
      left = right; right = nr;
      states.push({ l: left, r: right });
    }
    const last = states[states.length - 1]!;
    const cipherBytes = new Uint8Array(16); cipherBytes.set(last.r); cipherBytes.set(last.l, 8);
    return { states, keys: rk.keys, rots: rk.rots, cipher: toHex(cipherBytes).join(""), error: "" };
  }, [pass, blockHex]);

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="font-display text-3xl font-bold">Round Visualizer</h1>
      <p className="mt-2 max-w-2xl text-[15px] text-ink-muted">
        Twelve Feistel rounds. Amber = the half <b className="text-ink">computed</b> this round;
        dashed = the half <b className="text-ink">copied</b> verbatim. Read down the dashed column:
        every L is the previous round&apos;s R, untouched — the Feistel guarantee that makes
        decryption work no matter what F does.
      </p>

      <div className="mt-6 grid gap-3 sm:grid-cols-[1fr_auto]">
        <input
          value={pass}
          onChange={(e) => setPass(e.target.value)}
          className="rounded-xl border border-line bg-surface px-3.5 py-2 text-sm outline-none focus:border-trail"
          placeholder="Passphrase"
        />
        <button
          onClick={() => setBlockHex(toHex(crypto.getRandomValues(new Uint8Array(16))).join(""))}
          className="ui-t inline-flex items-center justify-center gap-2 rounded-xl border border-line bg-surface-raised px-4 py-2 text-sm font-semibold hover:border-ink-muted"
        >
          <Dice5 className="h-4 w-4" /> Random block
        </button>
      </div>
      <input
        value={blockHex}
        onChange={(e) => setBlockHex(e.target.value)}
        className="tnum mt-3 w-full rounded-xl border border-line bg-surface px-3.5 py-2 text-sm outline-none focus:border-trail"
        placeholder="16-byte block, hex"
      />

      {error ? (
        <p className="mt-6 text-sm text-trail-soft">{error}</p>
      ) : (
        <Card className="mt-6">
          <div className="mb-3 flex gap-5 text-xs text-ink-muted">
            <span className="flex items-center gap-1.5"><span className="inline-block h-3 w-3 rounded-sm bg-trail" /> computed this round</span>
            <span className="flex items-center gap-1.5"><span className="inline-block h-3 w-3 rounded-sm border border-dashed border-line" /> copied verbatim</span>
          </div>
          <div
            role="region"
            aria-label="Feistel rounds table"
            tabIndex={0}
            className="overflow-x-auto focus:outline-none focus-visible:ring-1 focus-visible:ring-trail"
          >
          <table className="tnum w-full border-separate border-spacing-1 text-[12px]">
            <thead>
              <tr className="text-ink-muted">
                <th className="text-right pr-2">round</th>
                <th colSpan={8} className="text-left">L (left half)</th>
                <th />
                <th colSpan={8} className="text-left">R (right half)</th>
                <th className="text-left pl-2">round key ↺rot</th>
              </tr>
            </thead>
            <tbody>
              {states.map((s, i) => (
                <tr key={i}>
                  <td className="pr-2 text-right text-ink-muted">{i === 0 ? "in" : i}</td>
                  {toHex(s.l).map((h, j) => (
                    <td key={j} className={`rounded px-1.5 py-1 text-center ${i === 0 ? "bg-royal/25" : "border border-dashed border-line text-ink-muted"}`}>{h}</td>
                  ))}
                  <td className="text-line">│</td>
                  {toHex(s.r).map((h, j) => (
                    <td key={j} className={`rounded px-1.5 py-1 text-center font-semibold ${i === 0 ? "bg-royal/25" : "bg-trail text-surface"}`}>{h}</td>
                  ))}
                  <td className="pl-2 text-[11px] text-ink-muted">
                    {i > 0 && `${toHex(keys[i - 1]!).join("")} ↺${rots[i - 1]}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
          <p className="mt-4 text-sm text-ink-muted">
            Ciphertext block = <span className="tnum font-bold text-trail">{cipher}</span> (final swap: R ‖ L)
          </p>
        </Card>
      )}
    </div>
  );
}
