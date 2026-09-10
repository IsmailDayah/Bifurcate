"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";

const LINKS = [
  { href: "/encrypt", label: "Encrypt" },
  { href: "/decrypt", label: "Decrypt" },
  { href: "/rounds", label: "Rounds" },
  { href: "/chaos", label: "Chaos" },
  { href: "/analysis", label: "Analysis" },
  { href: "/how-it-works", label: "How it works" },
  { href: "/about", label: "About" },
];

export default function SiteNav() {
  const path = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-surface/85 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center gap-1 px-4 py-3">
        <Link href="/" className="mr-4 flex items-center gap-2 shrink-0">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-trail text-[15px] font-bold text-surface">
            ⎇
          </span>
          <span className="font-display text-lg font-bold tracking-tight">Bifurcate</span>
        </Link>
        <div className="hidden flex-1 items-center gap-0.5 md:flex">
          {LINKS.map((l) => {
            const active = path === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`ui-t rounded-lg px-3 py-1.5 text-sm ${
                  active
                    ? "bg-surface-raised font-semibold text-ink"
                    : "text-ink-muted hover:bg-surface-raised hover:text-ink"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </div>
        <Link
          href="/encrypt"
          className="ui-t ml-auto rounded-lg bg-trail px-3.5 py-1.5 text-sm font-semibold text-surface hover:bg-trail-soft"
        >
          Try it →
        </Link>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="site-menu"
          className="ui-t ml-1 rounded-lg border border-line p-1.5 text-ink-muted hover:text-ink md:hidden"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      <div
        id="site-menu"
        hidden={!open}
        className="border-t border-line bg-surface md:hidden"
      >
        <div className="mx-auto flex max-w-6xl flex-col px-4 py-2">
          {LINKS.map((l) => {
            const active = path === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className={`ui-t rounded-lg px-3 py-2.5 text-sm ${
                  active
                    ? "bg-surface-raised font-semibold text-ink"
                    : "text-ink-muted hover:bg-surface-raised hover:text-ink"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </div>
      </div>
    </header>
  );
}
