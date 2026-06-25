import type { MetadataRoute } from "next";

const BASE_URL =
  process.env.NEXT_PUBLIC_APP_URL?.replace(/\/$/, "") || "https://tukijuris.com.pe";

// Public, indexable URLs only. Authenticated app routes never appear here.
const PUBLIC_ROUTES: Array<{
  path: string;
  changeFrequency: MetadataRoute.Sitemap[number]["changeFrequency"];
  priority: number;
}> = [
  { path: "/landing", changeFrequency: "weekly", priority: 1.0 },
  { path: "/precios", changeFrequency: "monthly", priority: 0.9 },
  { path: "/caracteristicas", changeFrequency: "monthly", priority: 0.8 },
  { path: "/guia", changeFrequency: "monthly", priority: 0.6 },
  { path: "/docs", changeFrequency: "weekly", priority: 0.6 },
  { path: "/status", changeFrequency: "daily", priority: 0.3 },
  { path: "/privacy", changeFrequency: "yearly", priority: 0.4 },
  { path: "/terms", changeFrequency: "yearly", priority: 0.4 },
  { path: "/contacto", changeFrequency: "yearly", priority: 0.4 },
  { path: "/libro-reclamaciones", changeFrequency: "yearly", priority: 0.3 },
];

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date();
  return PUBLIC_ROUTES.map((r) => ({
    url: `${BASE_URL}${r.path}`,
    lastModified,
    changeFrequency: r.changeFrequency,
    priority: r.priority,
  }));
}
