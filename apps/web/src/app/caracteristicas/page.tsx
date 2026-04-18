"use client";

import { useRef, useEffect, type ReactNode } from "react";
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

const FEATURES_SHOWCASE = [
  {
    icon: Scale,
    title: "11 Áreas del Derecho Peruano",
    desc: "Agentes especializados en Civil, Penal, Laboral, Tributario, Constitucional, Administrativo, Corporativo, Registral, Competencia, Compliance y Comercio Exterior. Cada uno entrenado con legislación, jurisprudencia y doctrina de su área.",
    image: "/landing/feature-areas.png",
    badges: ["Civil", "Penal", "Laboral", "Tributario", "+7 más"],
  },
  {
    icon: Search,
    title: "Búsqueda Normativa Inteligente",
    desc: "Búsqueda híbrida BM25 + semántica sobre miles de documentos indexados. Encontrá leyes, decretos, resoluciones y jurisprudencia con precisión milimétrica. Los resultados incluyen score de relevancia y fragmento exacto.",
    image: "/landing/feature-search.png",
    badges: ["Semántica", "BM25", "Ranked results"],
    reverse: true,
  },
  {
    icon: Key,
    title: "Tu Propia Clave de IA (BYOK)",
    desc: "Conectá tu API key de OpenAI, Google o Anthropic. Usá GPT-4o, Gemini Pro o Claude con control total de costos. También incluimos modelos gratuitos como Gemini Flash, Groq y DeepSeek.",
    image: "/landing/feature-byok.png",
    badges: ["OpenAI", "Google", "Anthropic", "Gratuitos incluidos"],
  },
];

const FEATURES_GRID = [
  { icon: Shield, title: "Respuestas con Citas", desc: "Cada respuesta incluye referencias a artículos, leyes y jurisprudencia. Verificable y confiable." },
  { icon: BarChart3, title: "Analytics Avanzado", desc: "Monitorea uso, costos y áreas más consultadas. Exporta reportes en CSV y PDF." },
  { icon: Users, title: "Equipos y Organizaciones", desc: "Crea organizaciones, invita miembros, gestiona roles. Ideal para estudios de abogados." },
];

const EXTRA_FEATURES = [
  "Historial ilimitado de consultas",
  "Exportación PDF de respuestas",
  "Carpetas y etiquetas para organizar",
  "Marcadores para guardar respuestas clave",
  "Modo oscuro y claro",
  "Interfaz responsive — funciona en móvil",
  "Atajos de teclado para power users",
  "SSO con Google y Microsoft",
];

/* ═══════════════════════════════════════════════
   PAGE
═══════════════════════════════════════════════ */

export default function CaracteristicasPage() {
  return (
    <PublicLayout>
      {/* Hero */}
      <section className="py-16 sm:py-24 px-4 lg:px-8 relative overflow-hidden">
        <div className="pointer-events-none absolute -top-32 right-0 w-[400px] h-[400px] rounded-full bg-primary/5 blur-[120px]" />
        <div className="max-w-7xl mx-auto text-center">
          <Reveal>
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-medium uppercase tracking-wider mb-6">
              Capacidades
            </span>
            <h1 className="font-headline text-3xl sm:text-5xl font-bold text-on-surface mb-4">
              Todo lo que necesitás para{" "}
              <span className="text-primary">ejercer mejor</span>
            </h1>
            <p className="text-on-surface-variant text-base sm:text-lg max-w-2xl mx-auto">
              Herramientas de IA jurídica diseñadas para profesionales del derecho peruano.
              Cada feature resuelve un problema real del día a día legal.
            </p>
          </Reveal>
        </div>
      </section>

      {/* Showcase features — alternating image/text */}
      <section className="pb-16 sm:pb-24 px-4 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-16 sm:space-y-24">
          {FEATURES_SHOWCASE.map((f, i) => {
            const Icon = f.icon;
            const isReverse = "reverse" in f && f.reverse;
            return (
              <Reveal key={f.title} delay={i * 100}>
                <div className={cn("grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center", isReverse && "lg:direction-rtl")}>
                  <div className={cn("relative rounded-2xl overflow-hidden shadow-xl shadow-primary/5", isReverse && "lg:order-2")}>
                    <Image src={f.image} alt={f.title} width={800} height={450} className="w-full h-auto" />
                    <div className="absolute inset-0 rounded-2xl ring-1 ring-inset ring-ghost-border" />
                  </div>
                  <div className={cn("flex flex-col gap-4", isReverse && "lg:order-1")}>
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center icon-glow">
                      <Icon className="w-5 h-5 text-primary" />
                    </div>
                    <h2 className="font-headline font-bold text-on-surface text-xl sm:text-2xl">{f.title}</h2>
                    <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed">{f.desc}</p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {f.badges.map((badge) => (
                        <span key={badge} className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-primary/8 text-primary border border-primary/15">
                          {badge}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* Grid features */}
      <section className="py-16 sm:py-24 px-4 lg:px-8 bg-surface-container-low/30">
        <div className="max-w-7xl mx-auto">
          <Reveal>
            <div className="text-center mb-12">
              <h2 className="font-headline text-2xl sm:text-3xl font-bold text-on-surface mb-3">Y mucho más</h2>
              <p className="text-on-surface-variant text-sm sm:text-base">Funcionalidades que potencian tu flujo de trabajo</p>
            </div>
          </Reveal>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mb-12">
            {FEATURES_GRID.map((f, i) => {
              const Icon = f.icon;
              return (
                <Reveal key={f.title} delay={i * 100}>
                  <div className="group bg-surface-container-low hover:bg-surface-container rounded-xl p-6 sm:p-8 border border-ghost-border card-lift gradient-border cursor-default">
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-5 icon-glow transition-all duration-300 group-hover:bg-primary/20 group-hover:scale-110">
                      <Icon className="w-5 h-5 text-primary transition-transform duration-300 group-hover:scale-110" />
                    </div>
                    <h3 className="font-headline font-semibold text-on-surface text-base sm:text-lg mb-2 group-hover:text-primary transition-colors">{f.title}</h3>
                    <p className="text-sm text-on-surface-variant leading-relaxed">{f.desc}</p>
                  </div>
                </Reveal>
              );
            })}
          </div>

          {/* Extra features checklist */}
          <Reveal>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {EXTRA_FEATURES.map((f) => (
                <div key={f} className="flex items-center gap-2 text-sm text-on-surface-variant">
                  <CheckCircle2 className="w-4 h-4 text-primary shrink-0" />
                  {f}
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 sm:py-24 px-4 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <Reveal>
            <h2 className="font-headline text-2xl sm:text-3xl font-bold text-on-surface mb-4">
              ¿Listo para probarlo?
            </h2>
            <p className="text-on-surface-variant text-base mb-8">
              Comenzá gratis, sin tarjeta de crédito. Probá todas las features con modelos de IA incluidos.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-3">
              <Link
                href="/auth/register"
                className="inline-flex items-center justify-center gap-2 font-bold rounded-xl h-12 px-8 transition-all hover:opacity-90 text-on-primary gold-gradient hover:shadow-xl hover:shadow-primary/25 hover:scale-[1.02]"
              >
                Comenzar Gratis <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/precios"
                className="inline-flex items-center justify-center gap-2 rounded-xl h-12 px-8 text-on-surface hover:text-primary border border-ghost-border hover:border-primary/30 transition-all hover:scale-[1.01]"
              >
                Ver Precios
              </Link>
            </div>
          </Reveal>
        </div>
      </section>
    </PublicLayout>
  );
}
