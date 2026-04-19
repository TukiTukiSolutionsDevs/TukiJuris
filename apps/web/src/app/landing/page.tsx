"use client";

import { useState, useEffect, useRef, type ReactNode } from "react";
import {
  Scale,
  Shield,
  ArrowRight,
  MessageSquare,
  BookOpen,
  Zap,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { PublicLayout } from "@/components/public/PublicLayout";
import { cn } from "@/lib/utils";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ═══════════════════════════════════════════════
   HOOKS
═══════════════════════════════════════════════ */

/** Intersection Observer — triggers "visible" class for scroll animations */
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

/** Animated counter */
function useCounter(end: number, duration = 1800) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const started = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          const start = performance.now();
          const step = (now: number) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            setCount(Math.round(eased * end));
            if (progress < 1) requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
          observer.unobserve(el);
        }
      },
      { threshold: 0.5 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [end, duration]);

  return { count, ref };
}

/* ═══════════════════════════════════════════════
   REVEAL WRAPPER
═══════════════════════════════════════════════ */

function Reveal({ children, className, delay }: { children: ReactNode; className?: string; delay?: number }) {
  const ref = useReveal<HTMLDivElement>();
  return (
    <div
      ref={ref}
      className={cn("reveal", className)}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}

/* ═══════════════════════════════════════════════
   DECORATIVE SVG COMPONENTS
═══════════════════════════════════════════════ */

function ScalesSvg({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="60" cy="60" r="58" stroke="currentColor" strokeWidth="0.5" opacity="0.15" />
      <circle cx="60" cy="60" r="42" stroke="currentColor" strokeWidth="0.5" opacity="0.1" />
      <line x1="60" y1="20" x2="60" y2="55" stroke="currentColor" strokeWidth="1.5" opacity="0.25" />
      <line x1="30" y1="55" x2="90" y2="55" stroke="currentColor" strokeWidth="1.5" opacity="0.25" />
      <path d="M30 55 L22 75 L38 75 Z" stroke="currentColor" strokeWidth="1" fill="currentColor" fillOpacity="0.08" opacity="0.3" />
      <path d="M90 55 L82 75 L98 75 Z" stroke="currentColor" strokeWidth="1" fill="currentColor" fillOpacity="0.08" opacity="0.3" />
      <circle cx="60" cy="18" r="4" fill="currentColor" fillOpacity="0.2" />
    </svg>
  );
}

function GavelSvg({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="15" y="50" width="50" height="6" rx="3" fill="currentColor" fillOpacity="0.12" />
      <rect x="35" y="15" width="28" height="10" rx="4" transform="rotate(35 35 15)" fill="currentColor" fillOpacity="0.15" />
      <rect x="25" y="30" width="6" height="24" rx="3" transform="rotate(-15 25 30)" fill="currentColor" fillOpacity="0.1" />
    </svg>
  );
}

function ParagraphSvg({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
      <text x="12" y="48" fontSize="48" fontFamily="serif" fill="currentColor" fillOpacity="0.07" fontWeight="bold">§</text>
    </svg>
  );
}

/* ═══════════════════════════════════════════════
   DATA
═══════════════════════════════════════════════ */



const HOW_IT_WORKS = [
  { step: 1, icon: BookOpen, title: "Registrate gratis", desc: "Crea tu cuenta en 30 segundos. Sin tarjeta de crédito requerida.", image: "/landing/screenshot-chat.png" },
  { step: 2, icon: Zap, title: "Conectá tu modelo de IA", desc: "Usá los modelos incluidos o conectá tu propia API key para más opciones.", image: "/landing/screenshot-analytics.png" },
  { step: 3, icon: MessageSquare, title: "Recibí respuestas citadas", desc: "Hacé cualquier pregunta legal y recibí respuestas con fuentes oficiales verificables.", image: "/landing/screenshot-search-results.png" },
];





/* ═══════════════════════════════════════════════
   LANDING PAGE
═══════════════════════════════════════════════ */

export default function LandingPage() {
  const [stats, setStats] = useState({ chunks: 138, documents: 21, areas: 11 });
  const chunksCounter = useCounter(stats.chunks);
  const areasCounter = useCounter(stats.areas, 1200);

  useEffect(() => {
    fetch(`${API_URL}/api/health/knowledge`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) {
          setStats({
            chunks: data.total_chunks || 138,
            documents: data.total_documents || 21,
            areas: data.chunks_by_area ? Object.keys(data.chunks_by_area).length : 11,
          });
        }
      })
      .catch(() => {});
  }, []);

  return (
    <PublicLayout>
      {/* ═══════════════════════════════════════════════
          HERO
      ═══════════════════════════════════════════════ */}
      <section className="relative min-h-[90vh] flex items-center px-4 lg:px-8 overflow-hidden">
        {/* Ambient glow orbs — animated */}
        <div className="pointer-events-none absolute -top-32 -left-32 w-[500px] h-[500px] rounded-full bg-primary/5 blur-[120px] animate-pulse-glow" />
        <div className="pointer-events-none absolute top-1/4 right-0 w-[400px] h-[400px] rounded-full bg-secondary-container/10 blur-[100px] animate-pulse-glow delay-500" />

        {/* Decorative floating SVGs */}
        <ScalesSvg className="pointer-events-none absolute top-20 right-[10%] w-32 h-32 text-primary animate-float-slow opacity-40 hidden lg:block" />
        <ParagraphSvg className="pointer-events-none absolute bottom-24 left-[8%] w-20 h-20 text-primary animate-float opacity-30 hidden lg:block" />
        <GavelSvg className="pointer-events-none absolute top-1/3 left-[5%] w-16 h-16 text-on-surface-variant animate-float delay-300 opacity-20 hidden xl:block" />

        {/* Dot pattern background */}
        <div className="pointer-events-none absolute inset-0 dot-grid opacity-30" />

        <div className="relative max-w-7xl mx-auto w-full py-12 sm:py-20 grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
          {/* Left — text */}
          <div className="flex flex-col gap-5 sm:gap-6">
            {/* Badge */}
            <div className="animate-fade-in-up">
              <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-medium uppercase tracking-wider">
                <Sparkles className="w-3.5 h-3.5" />
                IA Jurídica para el Perú
              </span>
            </div>

            {/* H1 with shimmer */}
            <h1 className="animate-fade-in-up delay-100 font-headline text-3xl sm:text-5xl lg:text-6xl font-bold text-on-surface leading-[1.1]">
              Tu Asistente Jurídico{" "}
              <span className="shimmer-text">Inteligente</span>
            </h1>

            {/* Description */}
            <p className="animate-fade-in-up delay-200 text-base sm:text-lg text-on-surface-variant leading-relaxed max-w-lg">
              Consulta legislación, jurisprudencia y doctrina peruana con
              respuestas citadas directamente desde fuentes oficiales.
            </p>

            {/* CTAs */}
            <div className="animate-fade-in-up delay-300 flex flex-col sm:flex-row gap-3">
              <Link
                href="/auth/register"
                className="inline-flex items-center justify-center gap-2 font-bold rounded-xl h-12 px-6 transition-all hover:opacity-90 text-on-primary gold-gradient animate-pulse-glow hover:shadow-xl hover:shadow-primary/25 hover:scale-[1.02]"
              >
                Comenzar Gratis <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/docs"
                className="inline-flex items-center justify-center gap-2 rounded-xl h-12 px-6 transition-all text-on-surface hover:text-primary border border-ghost-border hover:border-primary/30 bg-surface-container-high/20 hover:bg-surface-container-high/40 hover:scale-[1.01]"
              >
                Ver Documentación
              </Link>
            </div>

            {/* Animated stats */}
            <div className="animate-fade-in-up delay-400 flex flex-wrap gap-6 sm:gap-8 pt-4">
              <div className="flex flex-col">
                <span ref={chunksCounter.ref} className="font-headline text-2xl sm:text-3xl font-bold text-primary tabular-nums">
                  {chunksCounter.count.toLocaleString()}+
                </span>
                <span className="text-xs text-on-surface/50 uppercase tracking-widest">fragmentos legales</span>
              </div>
              <div className="w-px self-stretch bg-ghost-border" />
              <div className="flex flex-col">
                <span ref={areasCounter.ref} className="font-headline text-2xl sm:text-3xl font-bold text-primary tabular-nums">
                  {areasCounter.count}
                </span>
                <span className="text-xs text-on-surface/50 uppercase tracking-widest">áreas del derecho</span>
              </div>
              <div className="w-px self-stretch bg-ghost-border" />
              <div className="flex flex-col">
                <span className="font-headline text-2xl sm:text-3xl font-bold text-primary">100%</span>
                <span className="text-xs text-on-surface/50 uppercase tracking-widest">respuestas citadas</span>
              </div>
            </div>
          </div>

          {/* Right — mascot with floating decoration */}
          <div className="relative flex items-center justify-center lg:justify-end animate-fade-in-right delay-200">
            <div className="relative">
              {/* Animated glow behind mascot */}
              <div className="absolute inset-0 rounded-full bg-primary/10 blur-[80px] scale-90 animate-pulse-glow" />

              {/* Rotating ring decoration */}
              <div className="absolute inset-[-20px] animate-spin-slow opacity-20">
                <svg viewBox="0 0 460 460" fill="none" className="w-full h-full">
                  <circle cx="230" cy="230" r="220" stroke="currentColor" strokeWidth="0.5" strokeDasharray="8 12" className="text-primary" />
                  <circle cx="230" cy="230" r="200" stroke="currentColor" strokeWidth="0.3" strokeDasharray="4 16" className="text-on-surface-variant" />
                </svg>
              </div>

              {/* Floating mini badges */}
              <div className="absolute -top-4 -right-2 sm:right-4 z-10 animate-float delay-200">
                <div className="bg-surface/90 backdrop-blur-md border border-ghost-border rounded-lg px-3 py-2 shadow-lg">
                  <div className="flex items-center gap-2">
                    <Scale className="w-3.5 h-3.5 text-primary" />
                    <span className="text-[11px] font-medium text-on-surface">11 Áreas</span>
                  </div>
                </div>
              </div>

              <div className="absolute -bottom-2 -left-2 sm:left-4 z-10 animate-float delay-500">
                <div className="bg-surface/90 backdrop-blur-md border border-ghost-border rounded-lg px-3 py-2 shadow-lg">
                  <div className="flex items-center gap-2">
                    <Shield className="w-3.5 h-3.5 text-primary" />
                    <span className="text-[11px] font-medium text-on-surface">Citas verificables</span>
                  </div>
                </div>
              </div>

              {/* Mascot */}
              <Image
                src="/brand/tukan.png"
                alt="TukiJuris — Asistente Legal IA"
                className="relative w-56 sm:w-72 lg:w-[380px] h-auto drop-shadow-[0_20px_50px_rgba(0,0,0,0.20)] animate-float-slow"
                width={380}
                height={380}
                priority
              />
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          TRUST BAR — Animated slide
      ═══════════════════════════════════════════════ */}
      <section className="py-6 sm:py-8 px-4 lg:px-8 border-y border-ghost-border bg-surface-container-low/20 overflow-hidden">
        <div className="max-w-6xl mx-auto">
          <Reveal>
            <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-8">
              {["Derecho Civil", "Derecho Penal", "Derecho Laboral", "Derecho Tributario", "Derecho Constitucional"].map((area, i) => (
                <span key={area} className="flex items-center gap-2 text-xs uppercase tracking-[0.15em] text-on-surface/30 font-medium" style={{ animationDelay: `${i * 100}ms` }}>
                  <span className="w-1.5 h-1.5 rounded-full bg-primary/30" />
                  {area}
                </span>
              ))}
              <span className="flex items-center gap-2 text-xs uppercase tracking-[0.15em] text-primary/50 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-primary/50" />
                +6 áreas más
              </span>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          FEATURES TEASER — links to /caracteristicas
      ═══════════════════════════════════════════════ */}
      <section className="py-16 sm:py-24 px-4 lg:px-8 relative">
        <div className="pointer-events-none absolute top-0 right-0 w-[300px] h-[300px] rounded-full bg-primary/3 blur-[100px]" />
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="text-center mb-12 sm:mb-16">
              <span className="section-eyebrow text-primary mb-4 block">Capacidades</span>
              <h2 className="font-headline text-2xl sm:text-4xl font-bold text-on-surface mb-3">
                ¿Por qué <span className="text-primary">TukiJuris</span>?
              </h2>
              <p className="text-on-surface-variant text-sm sm:text-base max-w-2xl mx-auto">
                Herramientas diseñadas para profesionales del derecho peruano
              </p>
            </div>
          </Reveal>

          {/* Preview — first showcase feature only */}
          <Reveal>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center mb-12">
              <div className="relative rounded-2xl overflow-hidden shadow-xl shadow-primary/5">
                <Image src="/landing/feature-areas.png" alt="11 Áreas del Derecho" width={800} height={450} className="w-full h-auto" />
                <div className="absolute inset-0 rounded-2xl ring-1 ring-inset ring-ghost-border" />
              </div>
              <div className="flex flex-col gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center icon-glow">
                  <Scale className="w-5 h-5 text-primary" />
                </div>
                <h3 className="font-headline font-bold text-on-surface text-xl sm:text-2xl">11 Áreas del Derecho Peruano</h3>
                <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed">
                  Agentes especializados en Civil, Penal, Laboral, Tributario, Constitucional y 6 áreas más. Cada uno entrenado con legislación, jurisprudencia y doctrina de su área.
                </p>
                <Link
                  href="/caracteristicas"
                  className="inline-flex items-center gap-2 text-primary font-medium text-sm hover:gap-3 transition-all mt-2"
                >
                  Ver todas las características <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          HOW IT WORKS — with animated step icons
      ═══════════════════════════════════════════════ */}
      <section className="py-16 sm:py-24 px-4 lg:px-8 bg-surface-container-low/30 relative overflow-hidden">
        {/* Background deco */}
        <ParagraphSvg className="pointer-events-none absolute top-10 right-10 w-40 h-40 text-primary opacity-10" />

        <div className="max-w-4xl mx-auto">
          <Reveal>
            <div className="text-center mb-12 sm:mb-16">
              <span className="section-eyebrow text-primary mb-4 block">Proceso</span>
              <h2 className="font-headline text-2xl sm:text-4xl font-bold text-on-surface mb-3">¿Cómo funciona?</h2>
            </div>
          </Reveal>

          <div className="space-y-12 sm:space-y-16">
            {HOW_IT_WORKS.map((item, i) => {
              const StepIcon = item.icon;
              const isEven = i % 2 === 1;
              return (
                <Reveal key={item.step} delay={i * 100}>
                  <div className={cn("grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center", isEven && "lg:direction-rtl")}>
                    {/* Screenshot */}
                    <div className={cn("relative rounded-2xl overflow-hidden shadow-xl shadow-primary/5", isEven && "lg:order-2")}>
                      <Image
                        src={item.image}
                        alt={item.title}
                        width={800}
                        height={450}
                        className="w-full h-auto"
                      />
                      <div className="absolute inset-0 rounded-2xl ring-1 ring-inset ring-ghost-border" />
                    </div>

                    {/* Text */}
                    <div className={cn("flex flex-col gap-4", isEven && "lg:order-1")}>
                      <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-on-primary gold-gradient shadow-lg shadow-primary/20">
                          <StepIcon className="w-6 h-6" />
                        </div>
                        <div>
                          <span className="text-xs text-primary font-medium uppercase tracking-widest">Paso {item.step}</span>
                          <h3 className="font-headline font-bold text-on-surface text-lg sm:text-xl">{item.title}</h3>
                        </div>
                      </div>
                      <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                </Reveal>
              );
            })}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          PRICING TEASER — links to /precios
      ═══════════════════════════════════════════════ */}
      <section className="py-16 sm:py-24 px-4 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <Reveal>
            <div className="text-center mb-10">
              <span className="section-eyebrow text-primary mb-4 block">Planes</span>
              <h2 className="font-headline text-2xl sm:text-4xl font-bold text-on-surface mb-3">
                Desde <span className="text-primary">S/ 0</span> al mes
              </h2>
              <p className="text-on-surface-variant text-sm sm:text-base max-w-xl mx-auto mb-8">
                Comenzá gratis con 10 consultas semanales. Escalá a Profesional para uso intensivo o Estudio para equipos completos.
              </p>
            </div>
          </Reveal>

          <Reveal>
            <div className="grid grid-cols-3 gap-4 mb-8">
              {[
                { name: "Gratuito", price: "S/ 0", highlight: false },
                { name: "Profesional", price: "S/ 70", highlight: true },
                { name: "Estudio", price: "Contactar", highlight: false },
              ].map((plan) => (
                <div
                  key={plan.name}
                  className={cn(
                    "rounded-xl p-5 text-center border",
                    plan.highlight
                      ? "border-primary bg-primary/5 shadow-lg shadow-primary/10"
                      : "border-ghost-border bg-surface-container-low"
                  )}
                >
                  <span className="text-xs text-on-surface-variant uppercase tracking-widest">{plan.name}</span>
                  <p className={cn("font-headline text-2xl font-bold mt-1", plan.highlight ? "text-primary" : "text-on-surface")}>
                    {plan.price}
                  </p>
                </div>
              ))}
            </div>
          </Reveal>

          <Reveal>
            <div className="text-center">
              <Link
                href="/precios"
                className="inline-flex items-center gap-2 text-primary font-medium text-sm hover:gap-3 transition-all"
              >
                Ver planes completos y FAQ <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          FINAL CTA — with animated gradient border
      ═══════════════════════════════════════════════ */}
      <section className="py-16 sm:py-24 px-4 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <Reveal>
            <div className="relative rounded-2xl p-10 sm:p-16 text-center overflow-hidden border border-ghost-border bg-gradient-to-br from-surface-container-low via-surface-container to-surface-container-low">
              {/* Animated glow */}
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <div className="w-96 h-32 rounded-full bg-primary/8 blur-[80px] animate-pulse-glow" />
              </div>

              {/* Floating scales */}
              <ScalesSvg className="pointer-events-none absolute top-6 right-8 w-16 h-16 text-primary opacity-15 animate-float" />
              <GavelSvg className="pointer-events-none absolute bottom-6 left-8 w-14 h-14 text-primary opacity-10 animate-float delay-300" />

              <div className="relative flex flex-col lg:flex-row items-center gap-8 lg:gap-12">
                {/* CTA Image */}
                <div className="w-48 sm:w-56 lg:w-64 shrink-0">
                  <Image
                    src="/landing/cta-hero.png"
                    alt="TukiJuris"
                    width={256}
                    height={256}
                    className="w-full h-auto drop-shadow-xl"
                  />
                </div>

                {/* CTA Text */}
                <div className="flex flex-col items-center lg:items-start text-center lg:text-left">
                  <span className="section-eyebrow text-primary mb-4 block">Acceso Anticipado</span>
                  <h2 className="font-headline text-2xl sm:text-4xl font-bold text-on-surface mb-4">
                    ¿Listo para transformar tu <span className="shimmer-text">práctica legal</span>?
                  </h2>
                  <p className="text-on-surface-variant text-base sm:text-lg mb-8 max-w-xl">
                    Comienza gratis y descubre el poder de la IA jurídica especializada en derecho peruano
                  </p>
                  <Link
                    href="/auth/register"
                    className="inline-flex items-center gap-2 font-bold rounded-xl h-12 px-8 transition-all hover:opacity-90 text-on-primary gold-gradient animate-pulse-glow hover:shadow-xl hover:shadow-primary/25 hover:scale-[1.02]"
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
