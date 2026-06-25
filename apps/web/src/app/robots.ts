import type { MetadataRoute } from "next";

const BASE_URL =
  process.env.NEXT_PUBLIC_APP_URL?.replace(/\/$/, "") || "https://tukijuris.com.pe";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        // Public surface area: landing, marketing, legal, docs, public help.
        allow: [
          "/landing",
          "/precios",
          "/caracteristicas",
          "/guia",
          "/status",
          "/docs",
          "/privacy",
          "/terms",
          "/contacto",
          "/libro-reclamaciones",
        ],
        // App shell and authenticated areas must not be indexed.
        disallow: [
          "/",
          "/auth/",
          "/chat",
          "/analizar",
          "/billing",
          "/configuracion",
          "/organizacion",
          "/historial",
          "/buscar",
          "/marcadores",
          "/notificaciones",
          "/admin",
          "/analytics",
          "/onboarding",
          "/compartido/",
          "/documento/",
          "/api/",
        ],
      },
    ],
    sitemap: `${BASE_URL}/sitemap.xml`,
    host: BASE_URL,
  };
}
