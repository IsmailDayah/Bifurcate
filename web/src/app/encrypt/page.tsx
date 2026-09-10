"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lock, Download, FileText, File as FileIcon, Image as ImageIcon } from "lucide-react";
import Card from "@/components/Card";
import Banner from "@/components/Banner";
import HexBlock from "@/components/HexBlock";
import Histogram from "@/components/Histogram";
import { encrypt, parse, downloadBytes, shannonEntropy, histogram, MODE_CBC, MODE_ECB } from "@/crypto";
import { fileToBytes, loadImage, bytesToNoiseCanvas } from "@/lib/img";

type Mode = "text" | "file" | "image";

export default function EncryptPage() {
  const [mode, setMode] = useState<Mode>("text");
  const [text, setText] = useState("Attack at dawn — meet by the old pier.");
  const [payload, setPayload] = useState<Uint8Array | null>(null);
  const [fileName, setFileName] = useState("");
  const [origImg, setOrigImg] = useState<string | null>(null);
  const [dims, setDims] = useState<[number, number] | null>(null);
  const [pass, setPass] = useState("correct horse battery staple");
  const [ecb, setEcb] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<null | {
    blob: Uint8Array; ct: Uint8Array; ms: number; entIn: number; entOut: number; noise: string | null;
  }>(null);

  async function onFile(f: File, asImage: boolean) {
    const bytes = await fileToBytes(f);
    setPayload(bytes);
    setFileName(f.name);
    setResult(null);
    if (asImage) {
      const img = await loadImage(bytes, f.type || "image/png");
      const w = Math.min(img.naturalWidth, 320);
      const h = Math.round((img.naturalHeight / img.naturalWidth) * w) || w;
      setDims([w, h]);
      const c = document.createElement("canvas");
      c.width = w; c.height = h;
      c.getContext("2d")!.drawImage(img, 0, 0, w, h);
      setOrigImg(c.toDataURL("image/png"));
    } else {
      setOrigImg(null); setDims(null);
    }
  }

  async function run() {
    const data = mode === "text" ? new TextEncoder().encode(text) : payload;
    if (!data || data.length === 0 || !pass) return;
    setBusy(true);
    setError(null);
    await new Promise((r) => setTimeout(r, 30)); // let the spinner paint
    try {
      const t0 = performance.now();
      const blob = await encrypt(data, { passphrase: pass, mode: ecb ? MODE_ECB : MODE_CBC });
      const ms = performance.now() - t0;
      const c = parse(blob);
      const noise = mode === "image" && dims ? bytesToNoiseCanvas(c.ciphertext, dims[0], dims[1]) : null;
      setResult({ blob, ct: c.ciphertext, ms, entIn: shannonEntropy(data), entOut: shannonEntropy(c.ciphertext), noise });
    } catch (e) {
      setResult(null);
      setError((e as Error).message || "Encryption failed.");
    } finally {
      setBusy(false);
    }
  }

  const tabs: [Mode, string, typeof FileText][] = [
    ["text", "Text", FileText],
    ["file", "File", FileIcon],
    ["image", "Image", ImageIcon],
  ];

  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="font-display text-3xl font-bold">Encrypt</h1>
      <p className="mt-2 max-w-2xl text-[15px] text-ink-muted">
        Turn anything into authenticated noise — in your browser. Nothing is uploaded.
      </p>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <Card kicker="Input">
          <div className="mb-4 flex gap-1 rounded-xl border border-line bg-surface p-1">
            {tabs.map(([m, label, Icon]) => (
              <button
                key={m}
                onClick={() => { setMode(m); setResult(null); }}
                className={`ui-t flex flex-1 items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium ${
                  mode === m ? "bg-surface-raised text-ink" : "text-ink-muted hover:text-ink"
                }`}
              >
                <Icon className="h-4 w-4" /> {label}
              </button>
            ))}
          </div>

          {mode === "text" && (
            <textarea
              aria-label="Text to encrypt"
              value={text}
              onChange={(e) => { setText(e.target.value); setResult(null); }}
              rows={5}
              className="w-full resize-none rounded-xl border border-line bg-surface px-3.5 py-3 text-sm text-ink outline-none focus:border-trail"
            />
          )}
          {mode !== "text" && (
            <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-line bg-surface px-4 py-8 text-center text-sm text-ink-muted hover:border-ink-muted">
              <input
                type="file"
                accept={mode === "image" ? "image/*" : undefined}
                className="hidden"
                onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0], mode === "image")}
              />
              {fileName ? <span className="text-ink">{fileName}</span> : <span>Click to choose a {mode}</span>}
              {origImg && <img src={origImg} alt="original" className="mt-2 max-h-40 rounded-lg" />}
            </label>
          )}

          <div className="mt-4 space-y-3">
            <div>
              <label htmlFor="encrypt-passphrase" className="text-xs font-semibold text-ink-muted">
                Passphrase
              </label>
              <input
                id="encrypt-passphrase"
                type="password"
                value={pass}
                onChange={(e) => setPass(e.target.value)}
                className="mt-1 w-full rounded-xl border border-line bg-surface px-3.5 py-2 text-sm text-ink outline-none focus:border-trail"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-ink-muted">
              <input type="checkbox" checked={ecb} onChange={(e) => setEcb(e.target.checked)} className="accent-tamper" />
              Use ECB mode <span className="text-tamper-soft">(INSECURE — demo only)</span>
            </label>
            {ecb && <Banner kind="fail">ECB selected — identical blocks encrypt identically. Never use this for real data.</Banner>}
            <button
              onClick={run}
              disabled={busy || !pass || (mode === "text" ? text.length === 0 : !payload)}
              className="ui-t flex w-full items-center justify-center gap-2 rounded-xl bg-trail px-5 py-2.5 text-sm font-semibold text-surface hover:bg-trail-soft disabled:opacity-60"
            >
              <Lock className="h-4 w-4" /> {busy ? "Encrypting…" : "Encrypt"}
            </button>
          </div>
        </Card>

        <Card kicker="Output">
          {error ? (
            <Banner kind="fail">{error}</Banner>
          ) : !result ? (
            <div className="flex h-full min-h-56 items-center justify-center text-sm text-ink-muted">
              Encrypt something to see the ciphertext, entropy and download.
            </div>
          ) : (
            <div className="space-y-4">
              <Banner kind="ok">
                Encrypted {result.blob.length.toLocaleString()} bytes in {result.ms.toFixed(0)} ms · {ecb ? "ECB" : "CBC"}
              </Banner>
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="rounded-xl border border-line bg-surface p-3">
                  <div className="text-xs text-ink-muted">plaintext entropy</div>
                  <div className="tnum text-lg font-bold">{result.entIn.toFixed(3)}</div>
                </div>
                <div className="rounded-xl border border-line bg-surface p-3">
                  <div className="text-xs text-ink-muted">ciphertext entropy</div>
                  <div className="tnum text-lg font-bold text-trail">{result.entOut.toFixed(3)}</div>
                </div>
              </div>
              <button
                onClick={() => downloadBytes(result.blob, "message.bfc")}
                className="ui-t flex w-full items-center justify-center gap-2 rounded-xl border border-line bg-surface px-4 py-2 text-sm font-semibold hover:border-ink-muted"
              >
                <Download className="h-4 w-4" /> Download .bfc
              </button>
              <div>
                <div className="mb-1 text-xs font-semibold text-ink-muted">Ciphertext</div>
                <HexBlock data={result.ct} />
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* image dissolve + histogram */}
      {result?.noise && origImg && (
        <Card kicker="The dissolve" title="Structure becomes noise" className="mt-5">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="flex flex-col items-center gap-2">
              <div className="relative">
                <img src={origImg} alt="original" className="rounded-lg" />
                <AnimatePresence>
                  <motion.img
                    key={result.noise}
                    src={result.noise}
                    alt="encrypted"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
                    className="absolute inset-0 rounded-lg"
                  />
                </AnimatePresence>
              </div>
              <span className="text-xs text-ink-muted">original → ciphertext</span>
            </div>
            <div>
              <div className="mb-1 text-xs font-semibold text-ink-muted">plaintext histogram (peaky)</div>
              <Histogram counts={histogram(payload!)} color="#94a3b8" height={120} />
              <div className="mt-3 mb-1 text-xs font-semibold text-ink-muted">ciphertext histogram (flat)</div>
              <Histogram counts={histogram(result.ct)} color="#f59e0b" uniform={result.ct.length / 256} height={120} />
              <p className="mt-2 text-xs text-ink-muted">
                Green line = uniform expectation. Entropy climbed{" "}
                <span className="tnum text-ink">{result.entIn.toFixed(2)}</span> →{" "}
                <span className="tnum text-trail">{result.entOut.toFixed(3)}</span> bits/byte (8.000 is perfectly flat).
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
