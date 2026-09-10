import type { Metadata } from "next";
import Card from "@/components/Card";

export const metadata: Metadata = {
  title: "How it works",
  description: "Six diagrams, in order — from passphrase to key schedule, S-box, round function and full envelope.",
  alternates: { canonical: "/how-it-works" },
  openGraph: { title: "How it works — Bifurcate", description: "Six diagrams, in order — from passphrase to key schedule, S-box, round function and full envelope.", url: "/how-it-works",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "Bifurcate — a chaos-seeded cipher you can watch" }] },
  twitter: { card: "summary_large_image", title: "How it works — Bifurcate", description: "Six diagrams, in order — from passphrase to key schedule, S-box, round function and full envelope.",
    images: ["/opengraph-image"] },
};

const FIGS = [
  ["fig1_master", "The complete system", "Key hierarchy → chaotic engine → cipher → authenticated container."],
  ["fig2_chaos", "The chaotic engine", "An integer logistic map, whitened by SHA-256 — deterministic on every machine."],
  ["fig3_sbox", "Key-derived S-box", "Fisher–Yates shuffle driven by the keystream: your key defines your substitution table."],
  ["fig4_encrypt", "Feistel encryption", "12 rounds; only the right half is transformed each round."],
  ["fig5_decrypt", "Feistel decryption", "The same structure — only the round-key order is reversed."],
  ["fig6_roundf", "The round function F", "XOR key → substitute (confusion) → rotate + permute (diffusion)."],
];

export default function HowItWorks() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-10">
      <h1 className="font-display text-3xl font-bold">How it works</h1>
      <p className="mt-2 max-w-2xl text-[15px] text-ink-muted">
        Six diagrams, in order. Every box has a stated purpose.
      </p>
      <div className="mt-8 space-y-6">
        {FIGS.map(([file, title, desc], i) => (
          <Card key={file} kicker={`Figure ${i + 1}`} title={title}>
            <p className="mb-4 text-sm text-ink-muted">{desc}</p>
            <div
              role="region"
              aria-label={`${title} diagram`}
              tabIndex={0}
              className="overflow-x-auto rounded-xl border border-line bg-white p-2 focus:outline-none focus-visible:ring-1 focus-visible:ring-trail"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`/figures/${file}.svg`}
                alt={title as string}
                loading="lazy"
                decoding="async"
                className="mx-auto w-full max-w-3xl"
              />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
