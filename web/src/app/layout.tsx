import type { Metadata } from "next";
import { Inter, Fraunces } from "next/font/google";
import "./globals.css";
import SiteNav from "@/components/SiteNav";
import SiteFooter from "@/components/SiteFooter";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
  weight: ["600", "700"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://bifurcate.vercel.app"),
  alternates: { canonical: "/" },
  title: {
    default: "Bifurcate — a chaos-seeded cipher you can watch",
    template: "%s — Bifurcate",
  },
  description:
    "A key-dependent Feistel cipher whose S-box and round keys are grown from a chaotic map. Encrypt in your browser, watch a block cross 12 rounds, dissolve an image into noise, and see tampering caught in real time.",
  openGraph: {
    title: "Bifurcate — a chaos-seeded cipher you can watch",
    description:
      "Encrypt in your browser, watch a block cross 12 Feistel rounds, and see tampering caught live.",
    type: "website",
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable} h-full`}>
      <body className="min-h-full flex flex-col bg-surface text-ink">
        <SiteNav />
        <main className="flex-1">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
