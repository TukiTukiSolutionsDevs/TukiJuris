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
} from "lucide-react";
import Link from "next/link";

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
  "Acceso completo por 3 meses",
  "Chat legal con 11 áreas",
  "Búsqueda normativa",
  "1 organización",
];

const BASE_FEATURES = [
  "Todo lo de Gratuito",
  "100 consultas por día",
  "Analytics avanzado",
  "Exportar PDF",
  "Carpetas y etiquetas",
  "Soporte prioritario",
];

const ENTERPRISE_FEATURES = [
  "Todo lo de Base",
  "Consultas ilimitadas",
  "Soporte dedicado",
  "API access",
  "Multi-organización",
  "SSO empresarial",
];

export default function LandingPage() {
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
    <div className="min-h-screen bg-[#0A0A0F] text-[#F5F5F5]">

      {/* ═══════════════════════════════════════════════
          HEADER
      ═══════════════════════════════════════════════ */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#0A0A0F]/80 backdrop-blur-lg border-b border-[#1E1E2A]">
        <div className="max-w-7xl mx-auto px-4 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center">
            <img
              src="/brand/logo-full.png"
              alt="TukiJuris"
              className="h-10 w-auto"
            />
          </Link>

          {/* Nav links — hidden on mobile */}
          <nav className="hidden md:flex items-center gap-8">
            <a
              href="#caracteristicas"
              className="text-sm text-[#9CA3AF] hover:text-[#EAB308] transition-colors"
            >
              Características
            </a>
            <a
              href="#precios"
              className="text-sm text-[#9CA3AF] hover:text-[#EAB308] transition-colors"
            >
              Precios
            </a>
            <Link
              href="/docs"
              className="text-sm text-[#9CA3AF] hover:text-[#EAB308] transition-colors"
            >
              Documentación
            </Link>
            <Link
              href="/status"
              className="text-sm text-[#9CA3AF] hover:text-[#EAB308] transition-colors"
            >
              Estado
            </Link>
          </nav>

          {/* Auth actions */}
          <div className="flex items-center gap-3">
            <Link
              href="/auth/login"
              className="text-sm text-[#9CA3AF] hover:text-[#F5F5F5] transition-colors px-3 py-2"
            >
              Iniciar Sesión
            </Link>
            <Link
              href="/auth/register"
              className="text-sm bg-[#EAB308] hover:bg-[#CA9A07] text-[#0A0A0F] font-semibold rounded-lg h-11 px-6 flex items-center transition-colors whitespace-nowrap"
            >
              Comenzar Gratis
            </Link>
          </div>
        </div>
      </header>

      {/* ═══════════════════════════════════════════════
          HERO
      ═══════════════════════════════════════════════ */}
      <section className="min-h-[80vh] flex items-center pt-16 px-4 lg:px-8">
        <div className="max-w-7xl mx-auto w-full py-20 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left — text */}
          <div className="flex flex-col gap-6">
            {/* Badge */}
            <div className="w-fit text-[#EAB308] bg-[#EAB308]/10 rounded-full px-4 py-1 text-sm font-medium">
              Plataforma de IA Jurídica para el Perú
            </div>

            {/* H1 */}
            <h1 className="text-4xl sm:text-5xl font-bold text-white leading-tight">
              Tu Asistente Jurídico{" "}
              <span className="text-[#EAB308]">Inteligente</span>
            </h1>

            {/* Description */}
            <p className="text-lg text-[#9CA3AF] leading-relaxed max-w-lg">
              Consulta legislación, jurisprudencia y doctrina peruana con
              respuestas citadas directamente desde fuentes oficiales.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                href="/auth/register"
                className="inline-flex items-center justify-center gap-2 bg-[#EAB308] hover:bg-[#CA9A07] text-[#0A0A0F] font-semibold rounded-lg h-11 px-6 transition-colors"
              >
                Comenzar Gratis <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/docs"
                className="inline-flex items-center justify-center gap-2 border border-[#2A2A35] text-[#F5F5F5] hover:border-[#EAB308] hover:text-[#EAB308] rounded-lg h-11 px-6 transition-colors"
              >
                Ver Documentación
              </Link>
            </div>

            {/* Stats row */}
            <div className="flex flex-wrap gap-6 pt-2">
              <div className="flex flex-col">
                <span className="text-2xl font-bold text-[#EAB308]">
                  {stats.documents.toLocaleString()}+
                </span>
                <span className="text-xs text-[#6B7280]">
                  documentos indexados
                </span>
              </div>
              <div className="w-px bg-[#1E1E2A] self-stretch" />
              <div className="flex flex-col">
                <span className="text-2xl font-bold text-[#EAB308]">
                  {stats.areas}
                </span>
                <span className="text-xs text-[#6B7280]">
                  áreas del derecho
                </span>
              </div>
              <div className="w-px bg-[#1E1E2A] self-stretch" />
              <div className="flex flex-col">
                <span className="text-2xl font-bold text-[#EAB308]">
                  100%
                </span>
                <span className="text-xs text-[#6B7280]">
                  respuestas citadas
                </span>
              </div>
            </div>
          </div>

          {/* Right — mascot logo */}
          <div className="flex items-center justify-center">
            <img
              src="/brand/logo-full.png"
              alt="TukiJuris Abogados"
              className="w-80 h-auto drop-shadow-2xl"
            />
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
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              ¿Por qué TukiJuris?
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.title}
                  className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-8 hover:border-[#2A2A35] transition-colors"
                >
                  <div className="w-12 h-12 rounded-lg bg-[#EAB308]/10 flex items-center justify-center mb-5">
                    <Icon className="w-6 h-6 text-[#EAB308]" />
                  </div>
                  <h3 className="font-semibold text-[#F5F5F5] text-lg mb-2">
                    {f.title}
                  </h3>
                  <p className="text-sm text-[#9CA3AF] leading-relaxed">
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
      <section className="py-20 px-4 lg:px-8 bg-[#111116]/50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              ¿Cómo funciona?
            </h2>
          </div>

          {/* Steps */}
          <div className="relative grid grid-cols-1 sm:grid-cols-3 gap-8">
            {/* Connector line (hidden on mobile) */}
            <div className="hidden sm:block absolute top-8 left-[calc(16.66%+1rem)] right-[calc(16.66%+1rem)] h-px bg-[#1E1E2A]" />

            {HOW_IT_WORKS.map((item) => (
              <div
                key={item.step}
                className="flex flex-col items-center text-center gap-4 relative"
              >
                {/* Number circle */}
                <div className="w-16 h-16 rounded-full bg-[#EAB308] text-[#0A0A0F] font-bold text-2xl flex items-center justify-center flex-shrink-0 z-10">
                  {item.step}
                </div>
                <div>
                  <h3 className="font-semibold text-[#F5F5F5] text-lg mb-2">
                    {item.title}
                  </h3>
                  <p className="text-sm text-[#9CA3AF] leading-relaxed">
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
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Planes simples, sin sorpresas
            </h2>
            <p className="text-[#9CA3AF] text-base">
              Todos los planes incluyen:{" "}
              <span className="text-[#EAB308] font-medium">
                Trae tu propia clave de IA (BYOK)
              </span>
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-12">

            {/* FREE */}
            <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-8 flex flex-col gap-6">
              <div>
                <span className="text-[#9CA3AF] bg-[#6B7280]/20 rounded-full text-xs px-2 py-0.5 font-medium">
                  BETA
                </span>
                <h3 className="text-2xl font-bold text-[#F5F5F5] mt-3 mb-1">
                  Gratuito
                </h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-white">S/ 0</span>
                  <span className="text-[#6B7280] text-sm">/mes</span>
                </div>
              </div>

              <ul className="flex flex-col gap-3 flex-1">
                {FREE_FEATURES.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-[#9CA3AF]">
                    <CheckCircle2 className="w-4 h-4 text-[#34D399] flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>

              <Link
                href="/auth/register"
                className="inline-flex items-center justify-center border border-[#2A2A35] text-[#F5F5F5] hover:border-[#EAB308] hover:text-[#EAB308] rounded-lg h-11 px-6 transition-colors text-sm font-medium w-full"
              >
                Comenzar Beta
              </Link>
            </div>

            {/* BASE — highlighted */}
            <div className="bg-[#111116] border-2 border-[#EAB308] rounded-xl p-8 flex flex-col gap-6 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="bg-[#EAB308] text-[#0A0A0F] text-xs font-bold px-3 py-1 rounded-full">
                  MÁS POPULAR
                </span>
              </div>

              <div>
                <span className="text-[#EAB308] bg-[#EAB308]/20 rounded-full text-xs px-2 py-0.5 font-medium">
                  POPULAR
                </span>
                <h3 className="text-2xl font-bold text-[#F5F5F5] mt-3 mb-1">
                  Base
                </h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-white">S/ 70</span>
                  <span className="text-[#6B7280] text-sm">/mes</span>
                </div>
              </div>

              <ul className="flex flex-col gap-3 flex-1">
                {BASE_FEATURES.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-[#9CA3AF]">
                    <CheckCircle2 className="w-4 h-4 text-[#34D399] flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>

              <Link
                href="/auth/register"
                className="inline-flex items-center justify-center bg-[#EAB308] hover:bg-[#CA9A07] text-[#0A0A0F] font-semibold rounded-lg h-11 px-6 transition-colors text-sm w-full"
              >
                Actualizar a Base
              </Link>
            </div>

            {/* ENTERPRISE */}
            <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-8 flex flex-col gap-6">
              <div>
                <span className="text-[#A78BFA] bg-[#A78BFA]/20 rounded-full text-xs px-2 py-0.5 font-medium">
                  ENTERPRISE
                </span>
                <h3 className="text-2xl font-bold text-[#F5F5F5] mt-3 mb-1">
                  Enterprise
                </h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-bold text-white">
                    Contactar
                  </span>
                </div>
              </div>

              <ul className="flex flex-col gap-3 flex-1">
                {ENTERPRISE_FEATURES.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-[#9CA3AF]">
                    <CheckCircle2 className="w-4 h-4 text-[#34D399] flex-shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>

              <a
                href="mailto:ventas@tukijuris.net.pe"
                className="inline-flex items-center justify-center border border-[#2A2A35] text-[#F5F5F5] hover:border-[#A78BFA] hover:text-[#A78BFA] rounded-lg h-11 px-6 transition-colors text-sm font-medium w-full"
              >
                Contactar Ventas
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
          <div className="bg-gradient-to-r from-[#2C3E50] to-[#1A1A22] rounded-2xl p-16 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              ¿Listo para transformar tu práctica legal?
            </h2>
            <p className="text-[#9CA3AF] text-lg mb-8">
              Comienza gratis y descubre el poder de la IA jurídica
            </p>
            <Link
              href="/auth/register"
              className="inline-flex items-center gap-2 bg-[#EAB308] hover:bg-[#CA9A07] text-[#0A0A0F] font-semibold rounded-lg h-11 px-8 transition-colors"
            >
              Comenzar Gratis <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          FOOTER
      ═══════════════════════════════════════════════ */}
      <footer className="bg-[#0A0A0F] border-t border-[#1E1E2A] py-12 px-4 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Top row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 mb-8">
            {/* Brand */}
            <div className="flex flex-col gap-3">
              <img
                src="/brand/logo-full.png"
                alt="TukiJuris Abogados"
                className="h-12 w-auto"
              />
              <p className="text-sm text-[#6B7280] max-w-xs">
                Plataforma Jurídica Inteligente para el Derecho Peruano
              </p>
            </div>

            {/* Links */}
            <div className="flex flex-col sm:items-center gap-3">
              <nav className="flex flex-wrap gap-4 text-sm text-[#9CA3AF]">
                <Link href="/terms" className="hover:text-[#EAB308] transition-colors">
                  Términos
                </Link>
                <Link href="/privacy" className="hover:text-[#EAB308] transition-colors">
                  Privacidad
                </Link>
                <Link href="/docs" className="hover:text-[#EAB308] transition-colors">
                  Documentación
                </Link>
                <Link href="/status" className="hover:text-[#EAB308] transition-colors">
                  Estado del Sistema
                </Link>
              </nav>
            </div>

            {/* Contact */}
            <div className="flex flex-col sm:items-end gap-2">
              <a
                href="mailto:soporte@tukijuris.net.pe"
                className="text-sm text-[#9CA3AF] hover:text-[#EAB308] transition-colors"
              >
                soporte@tukijuris.net.pe
              </a>
            </div>
          </div>

          {/* Bottom */}
          <div className="border-t border-[#1E1E2A] pt-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-[#6B7280]">
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
