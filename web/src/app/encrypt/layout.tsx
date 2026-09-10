import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Encrypt",
  description: "Turn text or a file into authenticated noise, entirely in your browser. Nothing is uploaded.",
  alternates: { canonical: "/encrypt" },
  openGraph: { title: "Encrypt — Bifurcate", description: "Turn text or a file into authenticated noise, entirely in your browser. Nothing is uploaded.", url: "/encrypt",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "Bifurcate — a chaos-seeded cipher you can watch" }] },
  twitter: { card: "summary_large_image", title: "Encrypt — Bifurcate", description: "Turn text or a file into authenticated noise, entirely in your browser. Nothing is uploaded.",
    images: ["/opengraph-image"] },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
