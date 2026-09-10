import type { MetadataRoute } from "next";

const ROUTES = ["", "/encrypt", "/decrypt", "/rounds", "/chaos", "/analysis", "/how-it-works", "/about"];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return ROUTES.map((path) => ({
    url: `https://bifurcate.vercel.app${path}`,
    lastModified: now,
    changeFrequency: "monthly" as const,
    priority: path === "" ? 1 : 0.8,
  }));
}
