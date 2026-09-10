export default function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
}) {
  return (
    <div className="rounded-2xl border border-line bg-surface-raised px-5 py-4">
      <div className="text-xs font-semibold uppercase tracking-wider text-ink-muted">{label}</div>
      <div className="tnum mt-1.5 text-2xl font-bold text-ink">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-ink-muted">{sub}</div>}
    </div>
  );
}
