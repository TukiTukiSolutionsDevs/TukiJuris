"use client";

import { useState, useRef, useEffect, type ReactNode } from "react";
import { ArrowRight, CheckCircle2, ChevronDown } from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { PublicLayout } from "@/components/public/PublicLayout";
import { cn } from "@/lib/utils";

/* ═══════════════════════════════════════════════
   HOOKS & HELPERS
═══════════════════════════════════════════════ */

function useReveal<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add("visible");
          observer.unobserve(el);
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return ref;
}

function Reveal({ children, className, delay }: { children: ReactNode; className?: string; delay?: number }) {
  const ref = useReveal<HTMLDivElement>();
  return (
    <div ref={ref} className={cn("reveal", className)} style={delay ? { transitionDelay: `${delay}ms` } : undefined}>
      {children}
    </div>
  );
}

/* ═══════════════════════════════════════════════
   DATA
═══════════════════════════════════════════════ */

const FREE_FEATURES = [
  "10 consultas por semana", "Chat legal con 11 áreas", "Búsqueda normativa",
  "Gemini Flash, Groq, DeepSeek incluidos", "2 consultas premium/semana",
];

const BASE_FEATURES = [
  "Todo lo de Gratuito", "30 consultas por día", "Todos los modelos incluidos",
  "3 consultas premium/día", "BYOK: sin límite con tu key", "Exportar PDF",
  "Analytics avanzado", "Carpetas, Etiquetas, Marcadores", "Historial ilimitado", "Soporte prioritario",
];

const ENTERPRISE_FEATURES = [
  "Todo lo de Profesional", "100 consultas por día", "15 premium/día + 3 ultra/día",
  "Multi-organización (5 usuarios)", "Integraciones API", "SDKs y webhooks",
  "Soporte dedicado", "SSO empresarial",
];

const FAQ_ITEMS = [
  { q: "¿TukiJuris reemplaza a un abogado?", a: "No. TukiJuris es una herramienta de consulta que potencia al profesional legal. Proporciona orientación basada en normativa peruana con citas verificables, pero no constituye asesoría legal formal." },
  { q: "¿Qué es BYOK (Bring Your Own Key)?", a: "Podés conectar tu propia API key de OpenAI, Google o Anthropic para usar modelos como GPT-4, Gemini Pro o Claude. Así controlás tus costos directamente con el proveedor de IA." },
  { q: "¿Qué áreas del derecho cubre?", a: "Cubrimos 11 áreas: Civil, Penal, Constitucional, Laboral, Administrativo, Tributario, Comercial, Ambiental, Familia, Procesal e Internacional. Cada área tiene un agente especializado." },
  { q: "¿Cómo se verifican las respuestas?", a: "Cada respuesta incluye citas directas a artículos de ley, códigos y jurisprudencia peruana. Las fuentes provienen de nuestra base de conocimiento indexada con documentos oficiales." },
  { q: "¿Puedo usar TukiJuris gratis?", a: "Sí. El plan gratuito incluye 10 consultas por semana con modelos incluidos (Gemini Flash, Groq, DeepSeek). No requiere tarjeta de crédito." },
  { q: "¿Puedo cambiar de plan en cualquier momento?", a: "Sí. Podés actualizar o cambiar tu plan cuando quieras. Los cambios se aplican inmediatamente y se prorratea el cobro." },
  { q: "¿Qué métodos de pago aceptan?", a: "Aceptamos tarjetas de crédito/débito (Visa, Mastercard, American Express) a través de Stripe. También transferencia bancaria para planes Enterprise." },
];

/* ═══════════════════════════════════════════════
   FAQ ACCORDION
═══════════════════════════════════════════════ */

function FaqItem({ q, a, idx }: { q: string; a: string; idx: number }) {
  const [open, setOpen] = useState(false);
  return (
    <Reveal delay={idx * 80}>
      <div className="border-b border-ghost-border">
        <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between py-5 text-left gap-4 group">
          <span className="font-headline text-base sm:text-lg font-semibold text-on-surface group-hover:text-primary transition-colors">{q}</span>
          <ChevronDown className={cn("w-5 h-5 text-on-surface-variant shrink-0 transition-transform duration-300", open && "rotate-180 text-primary")} />
        </button>
        <div className={cn("overflow-hidden transition-all duration-300 ease-in-out", open ? "max-h-48 opacity-100 pb-5" : "max-h-0 opacity-0")}>
          <p className="text-sm text-on-surface-variant leading-relaxed pr-8">{a}</p>
        </div>
      </div>
    </Reveal>
  );
}

/* ═══════════════════════════════════════════════
   PAGE
═══════════════════════════════════════════════ */

export default function PreciosPage() {
  return (
    <PublicLayout>
      {/* Hero */}
      <section className="py-16 sm:py-24 px-4 lg:px-8">
        <div className="max-w-5xl mx-auto text-center">
          <Reveal>
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-medium uppercase tracking-wider mb-6">
              Planes
            </span>
            <h1 className="font-headline text-3xl sm:text-5xl font-bold text-on-surface mb-4">
              Planes simples, <span className="text-primary">sin sorpresas</span>
            </h1>
            <p className="text-on-surface-variant text-base sm:text-lg max-w-2xl mx-auto">
              Todos los planes funcionan con:{" "}
              <span className="text-primary font-medium">tu propia clave de IA (BYOK)</span>.
              Comenzá gratis y escalá cuando lo necesites.
            </p>
          </Reveal>
        </div>
      </section>

      {/* Pricing cards */}
      <section className="pb-16 sm:pb-24 px-4 lg:px-8">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6 items-start">
          {/* FREE */}
          <Reveal delay={0}>
            <div className="bg-surface-container-low hover:bg-surface-container rounded-xl p-6 sm:p-8 flex flex-col gap-5 border border-ghost-border card-lift gradient-border">
              <div>
                <span className="text-on-surface/60 bg-on-surface/10 rounded-lg text-xs px-2 py-0.5 font-medium uppercase tracking-widest">BETA</span>
                <h3 className="font-headline text-xl sm:text-2xl font-bold text-on-surface mt-3 mb-1">Gratuito</h3>
                <div className="flex items-baseline gap-1">
                  <span className="font-headline text-3xl sm:text-4xl font-bold text-on-surface">S/ 0</span>
                  <span className="text-on-surface/60 text-sm">/mes</span>
                </div>
              </div>
              <ul className="flex flex-col gap-2.5 flex-1">
                {FREE_FEATURES.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-on-surface-variant">
                    <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
              <Link href="/auth/register" className="inline-flex items-center justify-center rounded-xl h-11 px-6 transition-all text-sm font-medium w-full text-on-surface hover:text-primary border border-ghost-border hover:border-primary/30 bg-surface-container-high/20 hover:bg-surface-container-high/40 hover:scale-[1.01]">
                Comenzar Beta
              </Link>
            </div>
          </Reveal>

          {/* PROFESIONAL */}
          <Reveal delay={150}>
            <div className="bg-surface-container-low hover:bg-surface-container rounded-xl p-6 sm:p-8 flex flex-col gap-5 relative md:scale-[1.03] border-2 border-primary shadow-xl shadow-primary/10 card-lift">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="text-on-primary text-xs font-bold px-3 py-1 rounded-lg uppercase tracking-widest whitespace-nowrap gold-gradient shadow-lg shadow-primary/20">MÁS POPULAR</span>
              </div>
              <div>
                <span className="text-primary bg-primary/10 rounded-lg text-xs px-2 py-0.5 font-medium uppercase tracking-widest">POPULAR</span>
                <h3 className="font-headline text-xl sm:text-2xl font-bold text-on-surface mt-3 mb-1">Profesional</h3>
                <div className="flex items-baseline gap-1">
                  <span className="font-headline text-3xl sm:text-4xl font-bold text-on-surface">S/ 70</span>
                  <span className="text-on-surface/60 text-sm">/mes</span>
                </div>
              </div>
              <ul className="flex flex-col gap-2.5 flex-1">
                {BASE_FEATURES.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-on-surface-variant">
                    <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
              <Link href="/auth/register" className="inline-flex items-center justify-center rounded-xl h-11 px-6 transition-all hover:opacity-90 text-sm font-bold w-full text-on-primary gold-gradient hover:shadow-xl hover:shadow-primary/20 hover:scale-[1.02]">
                Actualizar a Profesional
              </Link>
            </div>
          </Reveal>

          {/* ENTERPRISE */}
          <Reveal delay={300}>
            <div className="bg-surface-container-low hover:bg-surface-container rounded-xl p-6 sm:p-8 flex flex-col gap-5 border border-ghost-border card-lift gradient-border">
              <div>
                <span className="text-on-surface-variant bg-on-surface-variant/10 rounded-lg text-xs px-2 py-0.5 font-medium uppercase tracking-widest">ESTUDIO</span>
                <h3 className="font-headline text-xl sm:text-2xl font-bold text-on-surface mt-3 mb-1">Estudio</h3>
                <div className="flex items-baseline gap-1">
                  <span className="font-headline text-3xl sm:text-4xl font-bold text-on-surface">Contactar</span>
                </div>
              </div>
              <ul className="flex flex-col gap-2.5 flex-1">
                {ENTERPRISE_FEATURES.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-on-surface-variant">
                    <CheckCircle2 className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />{f}
                  </li>
                ))}
              </ul>
              <a href="mailto:ventas@tukijuris.net.pe?subject=Plan%20Estudio%20TukiJuris" className="inline-flex items-center justify-center rounded-xl h-11 px-6 transition-all text-sm font-medium w-full text-on-surface hover:text-primary border border-ghost-border hover:border-primary/30 bg-surface-container-high/20 hover:bg-surface-container-high/40 hover:scale-[1.01]">
                Contactar ventas
              </a>
            </div>
          </Reveal>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 sm:py-24 px-4 lg:px-8 bg-surface-container-low/30">
        <div className="max-w-3xl mx-auto">
          <Reveal>
            <div className="text-center mb-10 sm:mb-14">
              <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-medium uppercase tracking-wider mb-6">
                FAQ
              </span>
              <h2 className="font-headline text-2xl sm:text-4xl font-bold text-on-surface">¿Tienes dudas?</h2>
            </div>
          </Reveal>
          <div className="border-t border-ghost-border">
            {FAQ_ITEMS.map((item, i) => (
              <FaqItem key={item.q} q={item.q} a={item.a} idx={i} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 sm:py-24 px-4 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <Reveal>
            <div className="relative rounded-2xl p-10 sm:p-16 overflow-hidden border border-ghost-border bg-gradient-to-br from-surface-container-low via-surface-container to-surface-container-low">
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <div className="w-96 h-32 rounded-full bg-primary/8 blur-[80px] animate-pulse-glow" />
              </div>
              <div className="relative flex flex-col lg:flex-row items-center gap-8 lg:gap-12">
                <div className="w-48 sm:w-56 lg:w-64 shrink-0">
                  <Image src="/landing/cta-hero.png" alt="TukiJuris" width={256} height={256} className="w-full h-auto drop-shadow-xl" />
                </div>
                <div className="flex flex-col items-center lg:items-start text-center lg:text-left">
                  <h2 className="font-headline text-2xl sm:text-3xl font-bold text-on-surface mb-4">
                    Comenzá <span className="text-primary">gratis</span> hoy
                  </h2>
                  <p className="text-on-surface-variant text-base mb-8 max-w-xl">
                    Sin tarjeta de crédito. 10 consultas por semana con modelos de IA incluidos.
                  </p>
                  <Link
                    href="/auth/register"
                    className="inline-flex items-center gap-2 font-bold rounded-xl h-12 px-8 transition-all hover:opacity-90 text-on-primary gold-gradient hover:shadow-xl hover:shadow-primary/25 hover:scale-[1.02]"
                  >
                    Comenzar Gratis <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>
    </PublicLayout>
  );
}
