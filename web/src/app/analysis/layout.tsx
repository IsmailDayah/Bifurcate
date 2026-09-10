import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Security Analysis",
  description: "Avalanche, entropy and key sensitivity measured live in your browser — no quoted figures.",
  alternates: { canonical: "/analysis" },
  openGraph: { title: "Security Analysis — Bifurcate", description: "Avalanche, entropy and key sensitivity measured live in your browser — no quoted figures.", url: "/analysis",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "Bifurcate — a chaos-seeded cipher you can watch" }] },
  twitter: { card: "summary_large_image", title: "Security Analysis — Bifurcate", description: "Avalanche, entropy and key sensitivity measured live in your browser — no quoted figures.",
    images: ["/opengraph-image"] },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
