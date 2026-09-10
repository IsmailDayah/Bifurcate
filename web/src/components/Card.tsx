export default function Card({
  kicker,
  title,
  children,
  className = "",
}: {
  kicker?: string;
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-2xl border border-line bg-surface-raised p-5 sm:p-6 ${className}`}>
      {kicker && (
        <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-ink-muted">
          {kicker}
        </div>
      )}
      {title && <h2 className="font-display mb-3 text-xl font-bold">{title}</h2>}
      {children}
    </section>
  );
}
