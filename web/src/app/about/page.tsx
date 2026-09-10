import type { Metadata } from "next";
import Card from "@/components/Card";
import Banner from "@/components/Banner";

export const metadata: Metadata = {
  title: "About",
  description: "What Bifurcate is, how it is built, and the honest limits of a chaos-seeded cipher.",
  alternates: { canonical: "/about" },
  openGraph: { title: "About — Bifurcate", description: "What Bifurcate is, how it is built, and the honest limits of a chaos-seeded cipher.", url: "/about",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "Bifurcate — a chaos-seeded cipher you can watch" }] },
  twitter: { card: "summary_large_image", title: "About — Bifurcate", description: "What Bifurcate is, how it is built, and the honest limits of a chaos-seeded cipher.",
    images: ["/opengraph-image"] },
};

export default function About() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold">About Bifurcate</h1>
        <p className="mt-2 text-[15px] text-ink-muted">
          A key-dependent 12-round Feistel cipher whose S-box and round keys are grown from a
          deterministic integer logistic map, wrapped in an RSA hybrid envelope and authenticated
          end-to-end.
        </p>
      </div>

      <Card kicker="The name">
        <p className="text-sm leading-relaxed text-ink-muted">
          <b className="text-ink">Bifurcation</b> is what the logistic map does as it collapses into
          chaos near r ≈ 3.57 — and it is exactly what a <b className="text-ink">Feistel network</b>{" "}
          does to a block: it splits it in two and feeds the halves through each other. One word,
          both the entropy source and the structure.
        </p>
      </Card>

      <Card kicker="Two implementations, one cipher">
        <p className="text-sm leading-relaxed text-ink-muted">
          The algorithm is written in <b className="text-ink">Python</b> (the reference implementation) and
          re-implemented in <b className="text-ink">TypeScript</b> for this site. Both pass the same{" "}
          <b className="text-trail">36 known-answer vectors</b>, cross-validated automatically —
          independent agreement being our primary evidence of correctness.
        </p>
      </Card>

      <div>
        <h2 className="font-display mb-3 text-xl font-bold">Limitations — stated deliberately</h2>
        <Banner kind="warn">Bifurcate is a study project. It is not a replacement for AES.</Banner>
        <ul className="mt-3 space-y-2 text-sm text-ink-muted">
          <li>• <b className="text-ink">No formal cryptanalysis.</b> We report empirical avalanche and entropy — necessary but not sufficient.</li>
          <li>• <b className="text-ink">Not constant-time;</b> no side-channel analysis.</li>
          <li>• <b className="text-ink">No public review.</b> AES has 25 years of it; Bifurcate has none.</li>
          <li>• <b className="text-ink">Chaos is not the security argument.</b> Raw states are whitened through SHA-256 (Alvarez &amp; Li, 2006). Chaos supplies key-dependent structure; SHA-256 supplies statistical quality.</li>
        </ul>
      </div>

      <Card kicker="References">
        <ol className="list-decimal space-y-1 pl-5 text-sm text-ink-muted">
          <li>C. E. Shannon, &quot;Communication Theory of Secrecy Systems,&quot; 1949.</li>
          <li>NIST, FIPS 46-3 (DES), 1999; FIPS 197 (AES), 2001.</li>
          <li>G. Alvarez &amp; S. Li, &quot;Basic cryptographic requirements for chaos-based cryptosystems,&quot; 2006.</li>
          <li>M. Bellare &amp; C. Namprempre, &quot;Authenticated Encryption,&quot; 2000.</li>
          <li>IETF RFC 8017 (RSA-OAEP), RFC 5869 (HKDF).</li>
          <li>R. M. May, &quot;Simple mathematical models with very complicated dynamics,&quot; Nature, 1976.</li>
        </ol>
      </Card>
    </div>
  );
}
