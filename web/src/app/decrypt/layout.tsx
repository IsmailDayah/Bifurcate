import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Decrypt",
  description: "The authentication tag is verified before a single byte is decrypted — a failure is always explicit, never garbage output.",
  alternates: { canonical: "/decrypt" },
  openGraph: { title: "Decrypt — Bifurcate", description: "The authentication tag is verified before a single byte is decrypted — a failure is always explicit, never garbage output.", url: "/decrypt",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "Bifurcate — a chaos-seeded cipher you can watch" }] },
  twitter: { card: "summary_large_image", title: "Decrypt — Bifurcate", description: "The authentication tag is verified before a single byte is decrypted — a failure is always explicit, never garbage output.",
    images: ["/opengraph-image"] },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
