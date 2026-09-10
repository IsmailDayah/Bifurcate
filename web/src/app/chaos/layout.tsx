import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "The Chaos Engine",
  description: "Turn the dial r and watch one value split into two, then four, then collapse into chaos near r ≈ 3.57 — the map that seeds every key.",
  alternates: { canonical: "/chaos" },
  openGraph: { title: "The Chaos Engine — Bifurcate", description: "Turn the dial r and watch one value split into two, then four, then collapse into chaos near r ≈ 3.57 — the map that seeds every key.", url: "/chaos",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "Bifurcate — a chaos-seeded cipher you can watch" }] },
  twitter: { card: "summary_large_image", title: "The Chaos Engine — Bifurcate", description: "Turn the dial r and watch one value split into two, then four, then collapse into chaos near r ≈ 3.57 — the map that seeds every key.",
    images: ["/opengraph-image"] },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
