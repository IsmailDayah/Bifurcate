import Link from "next/link";
import { ArrowRight, ShieldCheck, Eye, KeyRound, GitCompareArrows } from "lucide-react";
import Bifurcation from "@/viz/Bifurcation";
import StatCard from "@/components/StatCard";

export default function Home() {
  return (
    <div className="mx-auto max-w-6xl px-4">
      {/* hero */}
      <section className="grid gap-8 py-12 lg:grid-cols-[1.05fr_1.35fr] lg:items-center lg:py-16">
        <div>
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-line bg-surface-raised px-3 py-1 text-xs text-ink-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-verified" />
            Python reference + TypeScript port · same 36 known-answer vectors
          </div>
          <h1 className="font-display text-4xl font-bold leading-[1.05] sm:text-5xl">
            A chaos-seeded cipher <span className="text-trail">you can watch.</span>
          </h1>
          <p className="mt-4 max-w-lg text-[15px] leading-relaxed text-ink-muted">
            Bifurcate is a 12-round Feistel cipher whose substitution table and every round key
            are <span className="text-ink">grown from your passphrase</span> by a deterministic
            logistic map. Two passphrases are effectively two different ciphers — and the whole
            thing runs, privately, in your browser.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/encrypt"
              className="ui-t inline-flex items-center gap-2 rounded-xl bg-trail px-5 py-2.5 text-sm font-semibold text-surface hover:bg-trail-soft"
            >
              Encrypt something <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/how-it-works"
              className="ui-t inline-flex items-center gap-2 rounded-xl border border-line bg-surface-raised px-5 py-2.5 text-sm font-semibold text-ink hover:border-ink-muted"
            >
              How it works
            </Link>
          </div>
        </div>
        <Bifurcation height={420} />
      </section>

      {/* stats + the name's double meaning */}
      <section className="border-t border-line py-10">
        <div className="grid gap-4 sm:grid-cols-4">
          <StatCard label="Block size" value="128 bits" />
          <StatCard label="Key size" value="256 bits" sub="keyspace 2²⁵⁶" />
          <StatCard label="Rounds" value="12" sub="full avalanche by 7" />
          <StatCard label="Runs on" value="your device" sub="nothing sent to a server" />
        </div>
        <p className="mt-6 max-w-3xl text-[15px] leading-relaxed text-ink-muted">
          <span className="font-display text-ink">Bifurcation</span> is what the logistic map does
          as it collapses into chaos near <span className="tnum text-ink">r ≈ 3.57</span> — and it is
          exactly what a <span className="text-ink">Feistel network</span> does to a block: it{" "}
          <span className="text-trail">splits it in two</span> and feeds the halves through each
          other. One word, both the entropy source and the structure.
        </p>
      </section>

      {/* what you can do */}
      <section className="grid gap-4 border-t border-line py-10 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { icon: Eye, title: "Watch a block", body: "Follow 16 bytes across all 12 Feistel rounds — only the half being computed glows.", href: "/rounds" },
          { icon: ShieldCheck, title: "Dissolve an image", body: "See a photo become noise while its histogram flattens and entropy hits 8.", href: "/encrypt" },
          { icon: GitCompareArrows, title: "Measure it", body: "Live avalanche, entropy and the rounds curve that justifies 12 rounds.", href: "/analysis" },
          { icon: KeyRound, title: "Break it (on purpose)", body: "Change one character of the passphrase and watch integrity fail — in red.", href: "/decrypt" },
        ].map((c) => (
          <Link
            key={c.title}
            href={c.href}
            className="ui-t group rounded-2xl border border-line bg-surface-raised p-5 hover:border-ink-muted"
          >
            <c.icon className="h-5 w-5 text-trail" />
            <h3 className="mt-3 font-semibold text-ink">{c.title}</h3>
            <p className="mt-1 text-sm leading-relaxed text-ink-muted">{c.body}</p>
            <span className="ui-t mt-3 inline-flex items-center gap-1 text-xs font-semibold text-trail opacity-0 group-hover:opacity-100">
              open <ArrowRight className="h-3 w-3" />
            </span>
          </Link>
        ))}
      </section>
    </div>
  );
}
