export default function SiteFooter() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto flex max-w-6xl flex-col gap-1 px-4 py-6 text-xs text-ink-muted sm:flex-row sm:items-center sm:justify-between">
        <p>
          <span className="font-display font-bold text-ink">Bifurcate</span> · a chaos-seeded
          Feistel cipher
        </p>
        <p>
          Runs entirely in your browser · Python reference + TypeScript port, cross-validated ·{" "}
          <span className="text-trail">research project, not for production</span>
        </p>
      </div>
    </footer>
  );
}
