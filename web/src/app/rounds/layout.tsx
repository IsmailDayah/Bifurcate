import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Round Visualizer",
  description: "Follow 16 bytes across all 12 Feistel rounds, one half at a time, with every round key and rotation shown.",
  alternates: { canonical: "/rounds" },
  openGraph: { title: "Round Visualizer — Bifurcate", description: "Follow 16 bytes across all 12 Feistel rounds, one half at a time, with every round key and rotation shown.", url: "/rounds",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "Bifurcate — a chaos-seeded cipher you can watch" }] },
  twitter: { card: "summary_large_image", title: "Round Visualizer — Bifurcate", description: "Follow 16 bytes across all 12 Feistel rounds, one half at a time, with every round key and rotation shown.",
    images: ["/opengraph-image"] },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
