import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#0A0A0F] text-[#F5F5F5]">
        {children}
      </body>
    </html>
  );
}
