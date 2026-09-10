import { ShieldCheck, ShieldAlert, TriangleAlert } from "lucide-react";

type Kind = "ok" | "warn" | "fail";
const style: Record<Kind, string> = {
  ok: "border-verified/45 bg-verified/12 text-verified-soft",
  warn: "border-trail/45 bg-trail/10 text-trail-soft",
  fail: "border-tamper/50 bg-tamper/14 text-tamper-soft",
};
const Icon = { ok: ShieldCheck, warn: TriangleAlert, fail: ShieldAlert };

export default function Banner({ kind, children }: { kind: Kind; children: React.ReactNode }) {
  const I = Icon[kind];
  return (
    <div className={`flex items-center gap-2.5 rounded-xl border px-4 py-3 text-sm font-medium ${style[kind]}`}>
      <I className="h-4.5 w-4.5 shrink-0" />
      <span>{children}</span>
    </div>
  );
}
