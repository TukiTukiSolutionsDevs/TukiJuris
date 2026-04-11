"use client";

import { useState, useEffect } from "react";
import {
  Scale,
  Search,
  Key,
  Shield,
  BarChart3,
  Users,
  ArrowRight,
  CheckCircle2,
  Sun,
  Moon,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { useTheme } from "@/components/ThemeProvider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const FEATURES = [
  {
    icon: Scale,
    title: "11 Áreas del Derecho",
    desc: "Especialización en Civil, Penal, Constitucional, Laboral, Administrativo, Tributario, Comercial, Ambiental, Familia, Procesal e Internacional.",
  },
  {
    icon: Search,
    title: "Búsqueda Normativa Inteligente",
    desc: "Encuentra leyes, decretos y resoluciones con filtros avanzados. Miles de documentos indexados con búsqueda semántica.",
  },
  {
    icon: Key,
    title: "Tu Propia Clave de IA (BYOK)",
    desc: "Conecta tu API key de OpenAI, Google o Anthropic. Control total de costos. Usa GPT-4, Gemini o Claude.",
  },
  {
    icon: Shield,
    title: "Respuestas con Citas",
    desc: "Cada respuesta incluye referencias directas a artículos, leyes y jurisprudencia. Verificable y confiable.",
  },
  {
    icon: BarChart3,
    title: "Analytics Avanzado",
    desc: "Monitorea el uso, costos y áreas más consultadas. Exporta reportes en CSV y PDF.",
  },
  {
    icon: Users,
    title: "Equipos y Organizaciones",
    desc: "Crea organizaciones, invita miembros, gestiona roles. Ideal para estudios de abogados.",
  },
];

const HOW_IT_WORKS = [
  {
    step: 1,
    title: "Registrate gratis",
    desc: "Crea tu cuenta en 30 segundos. Sin tarjeta de crédito.",
  },
  {
    step: 2,
    title: "Configura tu clave IA",
    desc: "Agrega tu API key de OpenAI, Google o Anthropic.",
  },
  {
    step: 3,
    title: "Consulta",
    desc: "Hacé cualquier pregunta legal y recibí respuestas citadas.",
  },
];

const FREE_FEATURES = [
  "10 consultas por día",
  "Chat legal con 11 áreas",
  "Búsqueda normativa",
  "Trae tu propia clave de IA (BYOK)",
  "Modelos free incluidos próximamente",
];

const BASE_FEATURES = [
  "Todo lo de Gratuito",
  "100 consultas por día",
  "Trae tu propia IA (BYOK)",
  "Exportar PDF",
  "Analytics avanzado",
  "Carpetas y Etiquetas",
  "Historial ilimitado",
  "Marcadores",
  "Soporte prioritario",
];

const ENTERPRISE_FEATURES = [
  "Todo lo de Profesional",
  "Consultas ilimitadas",
  "Multi-organización",
  "Integraciones API",
  "SDKs y webhooks",
  "Soporte dedicado",
  "SSO empresarial",
  "Members ilimitados",
];

export default function LandingPage() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  const heroMascotSrc = "/brand/tukan.png";

  const [stats, setStats] = useState({
    chunks: 138,
    documents: 21,
    areas: 11,
  });

  useEffect(() => {
    fetch(`${API_URL}/api/health/knowledge`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) {
          setStats({
            chunks: data.total_chunks || 138,
            documents: data.total_documents || 21,
            areas: data.chunks_by_area
              ? Object.keys(data.chunks_by_area).length
              : 11,
          });
        }
      })
      .catch(() => {}); // Silently fail — show defaults
  }, []);

  return (
    <div className="min-h-screen bg-background text-on-surface font-['Manrope']">

      {/* ═══════════════════════════════════════════════
          HEADER
      ═══════════════════════════════════════════════ */}
      <header
        className="fixed top-0 left-0 right-0 z-50 bg-surface/80 backdrop-blur-md"
        style={{ borderBottom: "1px solid var(--ghost-border)" }}
      >
        <div className="max-w-7xl mx-auto px-4 lg:px-8 h-20 flex items-center justify-between">
          {/* Logo — tucán icon + text */}
          <Link href="/" className="flex items-center gap-3.5 rounded-2xl px-2 py-1 transition-transform duration-200 hover:scale-[1.01]">
            <Image
              src="/brand/logo-icon.png"
              alt="TukiJuris"
              className="h-14 w-14 object-contain drop-shadow-[0_8px_20px_rgba(0,0,0,0.12)]"
              width={56}
              height={56}
            />
            <span className="font-['Newsreader'] text-[2.2rem] leading-none font-bold text-primary tracking-[-0.03em] hidden sm:inline">
              TukiJuris
            </span>
          </Link>

          {/* Nav links — hidden on mobile */}
          <nav className="hidden md:flex items-center gap-8">
            <a
              href="#caracteristicas"
              className="text-sm font-['Newsreader'] text-on-surface-variant hover:text-primary transition-colors"
            >
              Características
            </a>
            <a
              href="#precios"
              className="text-sm font-['Newsreader'] text-on-surface-variant hover:text-primary transition-colors"
            >
              Precios
            </a>
            <Link
              href="/docs"
              className="text-sm font-['Newsreader'] text-on-surface-variant hover:text-primary transition-colors"
            >
              Documentación
            </Link>

          </nav>

          {/* Auth actions */}
          <div className="flex items-center gap-3">
            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              title={isDark ? "Modo claro" : "Modo oscuro"}
              className="p-2 rounded-lg text-on-surface-variant hover:text-primary transition-colors"
            >
              {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <Link
              href="/auth/login"
              className="text-sm text-on-surface/60 hover:text-on-surface transition-colors px-3 py-2"
            >
              Iniciar Sesión
            </Link>
            <Link
              href="/auth/register"
              className="text-sm font-bold rounded-lg h-11 px-6 flex items-center transition-opacity hover:opacity-90 whitespace-nowrap text-on-primary"
              style={{
                background: "linear-gradient(135deg, var(--gold-gradient-from) 0%, var(--gold-gradient-to) 100%)",
              }}
            >
              Comenzar Gratis
            </Link>
          </div>
        </div>
      </header>

      {/* ═══════════════════════════════════════════════
          HERO
      ═══════════════════════════════════════════════ */}
      <section className="relative min-h-[80vh] flex items-center pt-16 px-4 lg:px-8 overflow-hidden">
        {/* Ambient glow orbs */}
        <div className="pointer-events-none absolute -top-32 -left-32 w-[600px] h-[600px] rounded-full bg-primary-container/5 blur-[120px]" />
        <div className="pointer-events-none absolute top-1/4 right-0 w-[500px] h-[500px] rounded-full bg-secondary-container/10 blur-[100px]" />

        <div className="relative max-w-7xl mx-auto w-full py-20 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left — text */}
          <div className="flex flex-col gap-6">
            {/* Category label */}
            <span className="w-fit text-primary text-xs uppercase tracking-[0.2em] font-bold">
              Plataforma de IA Jurídica para el Perú
            </span>

            {/* H1 */}
            <h1 className="font-['Newsreader'] text-4xl sm:text-5xl lg:text-6xl font-bold text-on-surface leading-tight">
              Tu Asistente Jurídico{" "}
              <span className="text-primary">Inteligente</span>
            </h1>

            {/* Description */}
            <p className="text-lg text-on-surface-variant leading-relaxed max-w-lg">
              Consulta legislación, jurisprudencia y doctrina peruana con
              respuestas citadas directamente desde fuentes oficiales.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                href="/auth/register"
                className="inline-flex items-center justify-center gap-2 font-bold rounded-lg h-11 px-6 transition-opacity hover:opacity-90 text-on-primary"
                style={{
                  background:
                    "linear-gradient(135deg, var(--gold-gradient-from) 0%, var(--gold-gradient-to) 100%)",
                }}
              >
                Comenzar Gratis <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/docs"
                className="inline-flex items-center justify-center gap-2 rounded-lg h-11 px-6 transition-colors text-on-surface hover:text-primary bg-surface-container-high/40 hover:bg-surface-container-high/60"
                style={{ border: "1px solid var(--ghost-border)" }}
              >
                Ver Documentación
              </Link>
            </div>

            {/* Stats row */}
            <div className="flex flex-wrap gap-6 pt-2">
              <div className="flex flex-col">
                <span className="font-['Newsreader'] text-2xl font-bold text-primary">
                  {stats.documents.toLocaleString()}+
                </span>
                <span className="text-xs text-on-surface/60 uppercase tracking-widest">
                  documentos indexados
                </span>
              </div>
              <div
                className="w-px self-stretch"
                style={{ background: "var(--ghost-border)" }}
              />
              <div className="flex flex-col">
                <span className="font-['Newsreader'] text-2xl font-bold text-primary">
                  {stats.areas}
                </span>
                <span className="text-xs text-on-surface/60 uppercase tracking-widest">
                  áreas del derecho
                </span>
              </div>
              <div
                className="w-px self-stretch"
                style={{ background: "var(--ghost-border)" }}
              />
              <div className="flex flex-col">
                <span className="font-['Newsreader'] text-2xl font-bold text-primary">
                  100%
                </span>
                <span className="text-xs text-on-surface/60 uppercase tracking-widest">
                  respuestas citadas
                </span>
              </div>
            </div>
          </div>

          {/* Right — mascot logo */}
          <div className="relative flex items-center justify-center">
            <div
              className="absolute inset-6 rounded-[2.5rem] blur-3xl"
              style={{
                background: isDark
                  ? "radial-gradient(circle at center, rgba(234,179,8,0.22) 0%, rgba(15,23,42,0.00) 72%)"
                  : "radial-gradient(circle at center, rgba(15,23,42,0.10) 0%, rgba(15,23,42,0.00) 72%)",
              }}
            />
            <div
              className="relative overflow-hidden rounded-[2rem] px-6 py-5 shadow-[0_28px_80px_rgba(15,23,42,0.12)]"
              style={{
                background: isDark
                  ? "linear-gradient(180deg, rgba(17,24,39,0.96) 0%, rgba(8,15,28,0.92) 100%)"
                  : "linear-gradient(180deg, rgba(248,250,252,0.98) 0%, rgba(241,245,249,0.96) 100%)",
                border: isDark
                  ? "1px solid rgba(234,179,8,0.14)"
                  : "1px solid rgba(15,23,42,0.06)",
              }}
            >
              <div
                className="pointer-events-none absolute inset-0 opacity-70"
                style={{
                  background: isDark
                    ? "radial-gradient(circle at 50% 18%, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.00) 58%)"
                    : "radial-gradient(circle at 50% 15%, rgba(255,255,255,0.72) 0%, rgba(255,255,255,0.00) 55%)",
                }}
              />
              <div className="relative flex flex-col items-center">
                <Image
                  src={heroMascotSrc}
                  alt="Mascota de TukiJuris"
                  className="relative w-[28rem] max-w-[88vw] h-auto drop-shadow-[0_24px_60px_rgba(0,0,0,0.24)] lg:scale-[1.08]"
                  width={448}
                  height={448}
                  priority
                />
                <div className="mt-2 text-center">
                  <div
                    className="font-['Newsreader'] text-[4.2rem] leading-[0.95] font-bold tracking-[-0.06em]"
                    style={{
                      color: isDark ? "#F8FAFC" : "#0F172A",
                      textShadow: isDark
                        ? "0 10px 34px rgba(234,179,8,0.10)"
                        : "0 10px 24px rgba(15,23,42,0.08)",
                    }}
                  >
                    TUKIJURIS
                  </div>
                  <div
                    className="mt-1 text-[1.1rem] font-semibold tracking-[0.45em]"
                    style={{ color: isDark ? "#FACC15" : "#A16207" }}
                  >
                    ABOGADOS
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          FEATURES
      ═══════════════════════════════════════════════ */}
      <section
        id="caracteristicas"
        className="py-20 px-4 lg:px-8 scroll-mt-16"
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <span className="block text-primary text-xs uppercase tracking-[0.2em] font-bold mb-4">
              Capacidades
            </span>
            <h2 className="font-['Newsreader'] text-3xl sm:text-4xl font-bold text-on-surface mb-4">
              ¿Por qué TukiJuris?
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.title}
                  className="group bg-surface-container-low hover:bg-surface-container rounded-lg p-8 transition-colors"
                  style={{ border: "1px solid var(--ghost-border)" }}
                >
                  <div className="w-12 h-12 rounded-lg bg-primary-container/10 flex items-center justify-center mb-5 transition-transform group-hover:scale-110">
                    <Icon className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="font-['Newsreader'] font-semibold text-on-surface text-lg mb-2">
                    {f.title}
                  </h3>
                  <p className="text-sm text-on-surface-variant leading-relaxed">
                    {f.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          HOW IT WORKS
      ═══════════════════════════════════════════════ */}
      <section className="py-20 px-4 lg:px-8 bg-surface-container-low/30">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <span className="block text-primary text-xs uppercase tracking-[0.2em] font-bold mb-4">
              Proceso
            </span>
            <h2 className="font-['Newsreader'] text-3xl sm:text-4xl font-bold text-on-surface mb-4">
              ¿Cómo funciona?
            </h2>
          </div>

          {/* Steps */}
          <div className="relative grid grid-cols-1 sm:grid-cols-3 gap-8">
            {/* Connector line (hidden on mobile) */}
            <div
              className="hidden sm:block absolute top-8 left-[calc(16.66%+1rem)] right-[calc(16.66%+1rem)] h-px"
              style={{ background: "var(--ghost-border)" }}
            />

            {HOW_IT_WORKS.map((item) => (
              <div
                key={item.step}
                className="flex flex-col items-center text-center gap-4 relative"
              >
                {/* Number circle */}
                <div
                  className="w-16 h-16 rounded-lg font-['Newsreader'] font-bold text-2xl flex items-center justify-center flex-shrink-0 z-10 text-on-primary"
                  style={{
                    background:
                      "linear-gradient(135deg, var(--gold-gradient-from) 0%, var(--gold-gradient-to) 100%)",
                  }}
                >
                  {item.step}
                </div>
                <div>
                  <h3 className="font-['Newsreader'] font-semibold text-on-surface text-lg mb-2">
                    {item.title}
                  </h3>
                  <p className="text-sm text-on-surface-variant leading-relaxed">
                    {item.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          PRICING
      ═══════════════════════════════════════════════ */}
      <section id="precios" className="py-20 px-4 lg:px-8 scroll-mt-16">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-4">
            <span className="block text-primary text-xs uppercase tracking-[0.2em] font-bold mb-4">
              Planes
            </span>
            <h2 className="font-['Newsreader'] text-3xl sm:text-4xl font-bold text-on-surface mb-4">
              Planes simples, sin sorpresas
            </h2>
            <p className="text-on-surface-variant text-base">
              Todos los planes funcionan con:{" "}
              <span className="text-primary font-medium">
                tu propia clave de IA (BYOK)
              </span>
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-12 items-start">

            {/* FREE */}
            <div
              className="bg-surface-container-low hover:bg-surface-container rounded-lg p-8 flex flex-col gap-6 transition-colors"
              style={{ border: "1px solid var(--ghost-border)" }}
            >
              <div>
                <span className="text-on-surface/60 bg-on-surface/10 rounded-lg text-xs px-2 py-0.5 font-medium uppercase tracking-widest">
                  BETA
                </span>
                <h3 className="font-['Newsreader'] text-2xl font-bold text-on-surface mt-3 mb-1">
                  Gratuito
                </h3>
                <div className="flex items-baseline gap-1">
                  <span className="font-['Newsreader'] text-4xl font-bold text-on-surface">
                    S/ 0
                  </span>
                  <span className="text-on-surface/60 text-sm">/mes</span>
                </div>
              </div>

              <ul className="flex flex-col gap-3 flex-1">
                {FREE_FEATURES.map((f) => (
                  <li
                    key={f}
                    className="flex items-start gap-2 text-sm text-on-surface-variant"
                  >
                    <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>

              <Link
                href="/auth/register"
                className="inline-flex items-center justify-center rounded-lg h-11 px-6 transition-colors text-sm font-medium w-full text-on-surface hover:text-primary bg-surface-container-high/40 hover:bg-surface-container-high/60"
                style={{ border: "1px solid var(--ghost-border)" }}
              >
                Comenzar Beta
              </Link>
            </div>

            {/* PROFESIONAL — highlighted */}
            <div
              className="bg-surface-container-low hover:bg-surface-container rounded-lg p-8 flex flex-col gap-6 relative md:scale-105 transition-colors"
              style={{ border: "2px solid var(--primary)" }}
            >
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span
                  className="text-on-primary text-xs font-bold px-3 py-1 rounded-lg uppercase tracking-widest whitespace-nowrap"
                  style={{
                    background:
                      "linear-gradient(135deg, var(--gold-gradient-from) 0%, var(--gold-gradient-to) 100%)",
                  }}
                >
                  MÁS POPULAR
                </span>
              </div>

              <div>
                <span className="text-primary bg-primary/10 rounded-lg text-xs px-2 py-0.5 font-medium uppercase tracking-widest">
                  POPULAR
                </span>
                <h3 className="font-['Newsreader'] text-2xl font-bold text-on-surface mt-3 mb-1">
                  Profesional
                </h3>
                <div className="flex items-baseline gap-1">
                  <span className="font-['Newsreader'] text-4xl font-bold text-on-surface">
                    S/ 70
                  </span>
                  <span className="text-on-surface/60 text-sm">/mes</span>
                </div>
              </div>

              <ul className="flex flex-col gap-3 flex-1">
                {BASE_FEATURES.map((f) => (
                  <li
                    key={f}
                    className="flex items-start gap-2 text-sm text-on-surface-variant"
                  >
                    <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>

              <Link
                href="/auth/register"
                className="inline-flex items-center justify-center rounded-lg h-11 px-6 transition-opacity hover:opacity-90 text-sm font-bold w-full text-on-primary"
                style={{
                  background:
                    "linear-gradient(135deg, var(--gold-gradient-from) 0%, var(--gold-gradient-to) 100%)",
                }}
              >
                Actualizar a Profesional
              </Link>
            </div>

            {/* ENTERPRISE */}
            <div
              className="bg-surface-container-low hover:bg-surface-container rounded-lg p-8 flex flex-col gap-6 transition-colors"
              style={{ border: "1px solid var(--ghost-border)" }}
            >
              <div>
                <span className="text-on-surface-variant bg-on-surface-variant/10 rounded-lg text-xs px-2 py-0.5 font-medium uppercase tracking-widest">
                  ESTUDIO
                </span>
                <h3 className="font-['Newsreader'] text-2xl font-bold text-on-surface mt-3 mb-1">
                  Estudio
                </h3>
                <div className="flex items-baseline gap-1">
                  <span className="font-['Newsreader'] text-4xl font-bold text-on-surface">
                    Contactar
                  </span>
                </div>
              </div>

              <ul className="flex flex-col gap-3 flex-1">
                {ENTERPRISE_FEATURES.map((f) => (
                  <li
                    key={f}
                    className="flex items-start gap-2 text-sm text-on-surface-variant"
                  >
                    <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>

              <a
                href="mailto:ventas@tukijuris.net.pe?subject=Plan%20Estudio%20TukiJuris"
                className="inline-flex items-center justify-center rounded-lg h-11 px-6 transition-colors text-sm font-medium w-full text-on-surface hover:text-primary bg-surface-container-high/40 hover:bg-surface-container-high/60"
                style={{ border: "1px solid var(--ghost-border)" }}
              >
                Contactar ventas
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          FINAL CTA
      ═══════════════════════════════════════════════ */}
      <section className="py-20 px-4 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div
            className="relative rounded-lg p-16 text-center overflow-hidden"
            style={{
              background:
                "linear-gradient(135deg, var(--surface-container-low) 0%, var(--surface-container) 50%, var(--surface-container-low) 100%)",
              border: "1px solid var(--ghost-border)",
            }}
          >
            {/* Ambient glow inside CTA */}
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div className="w-96 h-32 rounded-full bg-primary-container/5 blur-[80px]" />
            </div>

            <span className="relative block text-primary text-xs uppercase tracking-[0.2em] font-bold mb-6">
              Acceso Anticipado
            </span>
            <h2 className="relative font-['Newsreader'] text-3xl sm:text-4xl font-bold text-on-surface mb-4">
              ¿Listo para transformar tu práctica legal?
            </h2>
            <p className="relative text-on-surface-variant text-lg mb-8">
              Comienza gratis y descubre el poder de la IA jurídica
            </p>
            <Link
              href="/auth/register"
              className="relative inline-flex items-center gap-2 font-bold rounded-lg h-11 px-8 transition-opacity hover:opacity-90 text-on-primary"
              style={{
                background: "linear-gradient(135deg, var(--gold-gradient-from) 0%, var(--gold-gradient-to) 100%)",
              }}
            >
              Comenzar Gratis <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          FOOTER
      ═══════════════════════════════════════════════ */}
      <footer
        className="bg-background py-12 px-4 lg:px-8"
        style={{ borderTop: "1px solid var(--ghost-border)" }}
      >
        <div className="max-w-7xl mx-auto">
          {/* Top row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 mb-8">
            {/* Brand */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2.5">
                <Image
                  src="/brand/logo-icon.png"
                  alt="TukiJuris"
                  className="h-12 w-12 object-contain"
                  width={48}
                  height={48}
                />
                <span className="font-['Newsreader'] text-xl font-bold text-primary tracking-tight">
                  TukiJuris
                </span>
              </div>
              <p className="text-sm text-on-surface/60 max-w-xs">
                Plataforma Jurídica Inteligente para el Derecho Peruano
              </p>
            </div>

            {/* Links */}
            <div className="flex flex-col sm:items-center gap-3">
              <nav className="flex flex-wrap gap-4 text-xs uppercase tracking-widest text-on-surface-variant">
                <Link
                  href="/terms"
                  className="hover:text-primary transition-colors"
                >
                  Términos
                </Link>
                <Link
                  href="/privacy"
                  className="hover:text-primary transition-colors"
                >
                  Privacidad
                </Link>
                <Link
                  href="/docs"
                  className="hover:text-primary transition-colors"
                >
                  Documentación
                </Link>
                <Link
                  href="/status"
                  className="hover:text-primary transition-colors"
                >
                  Estado
                </Link>
              </nav>
            </div>

            {/* Contact */}
            <div className="flex flex-col sm:items-end gap-2">
              <a
                href="mailto:soporte@tukijuris.net.pe"
                className="text-sm text-on-surface-variant hover:text-primary transition-colors"
              >
                soporte@tukijuris.net.pe
              </a>
            </div>
          </div>

          {/* Bottom */}
          <div
            className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-on-surface/60 uppercase tracking-widest"
            style={{ borderTop: "1px solid var(--ghost-border)" }}
          >
            <span>
              © 2026 TukiJuris Abogados. Todos los derechos reservados.
            </span>
            <span>Esta plataforma no constituye asesoría legal.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
