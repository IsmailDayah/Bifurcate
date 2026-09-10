"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Unlock, Upload, Download } from "lucide-react";
import Card from "@/components/Card";
import Banner from "@/components/Banner";
import HexBlock from "@/components/HexBlock";
import { decrypt, parse, downloadBytes, IntegrityError, type Parsed } from "@/crypto";
import { sniffImageMime, sniffExtension, loadImage } from "@/lib/img";

export default function DecryptPage() {
  const [blob, setBlob] = useState<Uint8Array | null>(null);
  const [header, setHeader] = useState<Parsed | null>(null);
  const [pass, setPass] = useState("");
  const [busy, setBusy] = useState(false);
  const [verdict, setVerdict] = useState<null | "ok" | "fail">(null);
  const [msg, setMsg] = useState("");
  const [text, setText] = useState<string | null>(null);
  const [img, setImg] = useState<string | null>(null);
  const [rawOut, setRawOut] = useState<Uint8Array | null>(null);
  const [ext, setExt] = useState("bin");

  async function onFile(f: File) {
    const bytes = new Uint8Array(await f.arrayBuffer());
    setBlob(bytes); setVerdict(null); setText(null); setImg(null); setRawOut(null);
    try { setHeader(parse(bytes)); } catch { setHeader(null); setMsg("Not a valid .bfc container"); setVerdict("fail"); }
  }

  async function run() {
    if (!blob) return;
    setBusy(true); setVerdict(null); setText(null); setImg(null);
    await new Promise((r) => setTimeout(r, 30));
    try {
      const data = await decrypt(blob, { passphrase: pass });
      setVerdict("ok");
      setMsg(`VERIFIED — HMAC valid · ${data.length.toLocaleString()} bytes recovered`);
      setRawOut(data);
      setExt(sniffExtension(data));
      const mime = sniffImageMime(data);
      if (mime) {
        const image = await loadImage(data, mime);
        const c = document.createElement("canvas");
        c.width = image.naturalWidth; c.height = image.naturalHeight;
        c.getContext("2d")!.drawImage(image, 0, 0);
        setImg(c.toDataURL("image/png"));
      } else {
        try { setText(new TextDecoder("utf-8", { fatal: true }).decode(data)); setExt("txt"); }
        catch { setText(null); }
      }
    } catch (e) {
      if (e instanceof IntegrityError) { setVerdict("fail"); setMsg(e.message); }
      else { setVerdict("fail"); setMsg(String((e as Error).message)); }
    }
    setBusy(false);
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="font-display text-3xl font-bold">Decrypt</h1>
      <p className="mt-2 text-[15px] text-ink-muted">
        The tag is verified <span className="text-ink">before</span> a single byte is decrypted.
        Bifurcate never returns garbage — a failure is always explicit.
      </p>

      <Card kicker="Container" className="mt-6">
        <label className="flex cursor-pointer flex-col items-center gap-2 rounded-xl border border-dashed border-line bg-surface px-4 py-6 text-center text-sm text-ink-muted hover:border-ink-muted">
          <input type="file" accept=".bfc" className="hidden" onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])} />
          <Upload className="h-5 w-5" />
          {blob ? `${blob.length.toLocaleString()} bytes loaded` : "Choose a .bfc file"}
        </label>

        {header && (
          <div className="mt-4 grid grid-cols-4 gap-2 text-center text-xs">
            {[["version", header.version], ["mode", header.modeName], ["hybrid", header.isHybrid ? "yes" : "no"], ["ciphertext", `${header.ciphertext.length} B`]].map(([k, v]) => (
              <div key={k as string} className="rounded-lg border border-line bg-surface p-2">
                <div className="text-ink-muted">{k}</div>
                <div className="tnum mt-0.5 font-bold text-ink">{v}</div>
              </div>
            ))}
          </div>
        )}

        {header && (
          <div className="mt-4 space-y-3">
            <input
              type="password"
              aria-label="Passphrase"
              placeholder="Passphrase"
              value={pass}
              onChange={(e) => setPass(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && run()}
              className="w-full rounded-xl border border-line bg-surface px-3.5 py-2 text-sm text-ink outline-none focus:border-trail"
            />
            <button
              onClick={run}
              disabled={busy || !pass}
              className="ui-t flex w-full items-center justify-center gap-2 rounded-xl bg-trail px-5 py-2.5 text-sm font-semibold text-surface hover:bg-trail-soft disabled:opacity-60"
            >
              <Unlock className="h-4 w-4" /> {busy ? "Verifying…" : "Verify & decrypt"}
            </button>
          </div>
        )}
      </Card>

      {/* the verdict comes first — the one moment of theatre */}
      {verdict === "fail" && (
        <motion.div
          initial={{ x: 0 }}
          animate={{ x: [0, -8, 8, -6, 6, 0] }}
          transition={{ duration: 0.4 }}
          className="mt-5"
        >
          <Banner kind="fail">{msg}</Banner>
          <p className="mt-2 text-sm text-ink-muted">
            The passphrase is wrong, or the file was altered after it was sealed. No plaintext is produced.
          </p>
        </motion.div>
      )}

      {verdict === "ok" && (
        <div className="mt-5 space-y-4">
          <Banner kind="ok">{msg}</Banner>
          {img && <img src={img} alt="recovered" className="mx-auto max-h-96 rounded-xl border border-line" />}
          {text !== null && (
            <Card kicker="Recovered text"><pre className="tnum whitespace-pre-wrap text-sm text-ink">{text}</pre></Card>
          )}
          {rawOut && !img && text === null && (
            <Card kicker="Recovered bytes"><HexBlock data={rawOut} /></Card>
          )}
          {rawOut && (
            <button
              onClick={() => downloadBytes(rawOut, `recovered.${ext}`)}
              className="ui-t flex w-full items-center justify-center gap-2 rounded-xl border border-line bg-surface px-4 py-2 text-sm font-semibold hover:border-ink-muted"
            >
              <Download className="h-4 w-4" /> Download recovered file
              <span className="tnum text-ink-muted">(.{ext})</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}
