import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";

export const metadata: Metadata = {
  title: "TukiJuris | Plataforma Juridica Inteligente",
  description:
    "Plataforma juridica inteligente especializada en derecho peruano. Consulta normativa, jurisprudencia y orientacion legal con agentes de IA especializados.",
  metadataBase: new URL("https://tukijuris.net.pe"),
  icons: {
    icon: "/brand/logo-full.png",
    shortcut: "/brand/logo-full.png",
    apple: "/brand/logo-full.png",
  },
  openGraph: {
    title: "TukiJuris — Asistente Legal IA para Derecho Peruano",
    description:
      "Consulta normativa, jurisprudencia y recibe orientacion legal con 11 agentes especializados.",
    url: "https://tukijuris.net.pe",
    siteName: "TukiJuris",
    locale: "es_PE",
    type: "website",
    images: [{ url: "/brand/logo-full.png", width: 512, height: 512, alt: "TukiJuris Abogados" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "TukiJuris — Asistente Legal IA",
    description: "Plataforma juridica inteligente para derecho peruano",
    images: ["/brand/logo-full.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

/**
 * Inline script to resolve theme BEFORE React hydrates.
 * Prevents the flash of wrong theme (FOUC).
 */
const themeScript = `
(function() {
  try {
    var stored = localStorage.getItem('tukijuris-theme');
    var theme = stored === 'light' || stored === 'dark'
      ? stored
      : (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
    document.documentElement.classList.add(theme);
  } catch (e) {
    document.documentElement.classList.add('dark');
  }
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <meta name="theme-color" content="#0C0E14" />
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-full flex flex-col">
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
