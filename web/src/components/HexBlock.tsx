export default function HexBlock({ data, limit = 512 }: { data: Uint8Array; limit?: number }) {
  const shown = data.slice(0, limit);
  let text = Array.from(shown, (b) => b.toString(16).padStart(2, "0").toUpperCase()).join(" ");
  if (data.length > limit) text += `  … (+${data.length - limit} bytes)`;
  return (
    <div className="tnum max-h-56 overflow-auto rounded-xl border border-line bg-surface-overlay p-3.5 text-[13px] leading-relaxed tracking-wide text-trail-soft break-all">
      {text || <span className="text-ink-muted">(empty)</span>}
    </div>
  );
}
