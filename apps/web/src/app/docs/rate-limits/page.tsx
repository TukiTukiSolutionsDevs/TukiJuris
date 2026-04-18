"use client";

import { Gauge, TrendingUp, Zap, Crown } from "lucide-react";
import { PageHero, SectionHeader, CodeBlock, Callout, PageNav } from "../_components";
import { RATE_LIMITS } from "../_data/constants";

const PLAN_ICONS: Record<string, typeof Gauge> = {
  Anonymous: Gauge,
  Free: Zap,
  Pro: TrendingUp,
  Enterprise: Crown,
};

const PLAN_COLORS: Record<string, string> = {
  Anonymous: "text-on-surface/40",
  Free: "text-blue-400",
  Pro: "text-primary",
  Enterprise: "text-purple-400",
};

export default function RateLimitsPage() {
  return (
    <>
      <PageHero
        title="Rate Limits y"
        highlight="Planes"
        subtitle="La API aplica rate limiting para garantizar estabilidad. Los límites varían según tu plan — desde acceso anónimo hasta Enterprise con límites personalizados."
        illustration="/docs/illustrations/rate-limits.png"
      />

      {/* Visual plan cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-12">
        {RATE_LIMITS.map((plan) => {
          const Icon = PLAN_ICONS[plan.plan] ?? Gauge;
          const color = PLAN_COLORS[plan.plan] ?? "text-on-surface/40";
          return (
            <div
              key={plan.plan}
              className="flex flex-col items-center p-5 rounded-xl bg-surface-container-low text-center"
              style={{ border: "1px solid rgba(79,70,51,0.1)" }}
            >
              <Icon className={`w-6 h-6 ${color} mb-3`} />
              <span className="text-2xl font-bold text-on-surface font-mono">{plan.rpm}</span>
              <span className="text-[10px] text-on-surface/30 uppercase tracking-wider mt-0.5">req/min</span>
              <span className={`text-xs font-medium mt-2 ${color}`}>{plan.plan}</span>
            </div>
          );
        })}
      </div>

      <SectionHeader
        title="Detalle por plan"
        subtitle="Comparación completa de límites y características."
      />

      <div
        className="overflow-x-auto rounded-lg mb-8"
        style={{ border: "1px solid rgba(79,70,51,0.15)" }}
      >
        <table className="w-full min-w-[500px] text-sm">
          <thead>
            <tr
              className="bg-surface-container-low"
              style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
            >
              <th className="text-left px-4 py-3 text-on-surface/40 font-medium">Plan</th>
              <th className="text-left px-4 py-3 text-on-surface/40 font-medium">Requests/min</th>
              <th className="text-left px-4 py-3 text-on-surface/40 font-medium">Autenticación</th>
              <th className="text-left px-4 py-3 text-on-surface/40 font-medium">Notas</th>
            </tr>
          </thead>
          <tbody>
            {RATE_LIMITS.map((row, idx) => (
              <tr
                key={row.plan}
                className={`hover:bg-surface-container-low transition-colors ${
                  idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                }`}
              >
                <td className="px-4 py-3">
                  <span className={`font-medium ${PLAN_COLORS[row.plan] ?? "text-on-surface"}`}>
                    {row.plan}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="font-mono text-primary font-bold text-lg">{row.rpm}</span>
                </td>
                <td className="px-4 py-3 text-on-surface/50 text-xs">{row.notes}</td>
                <td className="px-4 py-3 text-on-surface/40 text-xs">
                  {row.plan === "Enterprise" && "Contactanos para límites custom"}
                  {row.plan === "Pro" && "Ideal para producción"}
                  {row.plan === "Free" && "Perfecto para desarrollo"}
                  {row.plan === "Anonymous" && "Solo para testing rápido"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* How it works */}
      <SectionHeader
        title="¿Cómo funciona el rate limiting?"
        subtitle="Sliding window de 60 segundos. Headers de respuesta indican el estado."
      />

      <div className="space-y-4 mb-8">
        <Callout variant="info" title="Headers de rate limit">
          <p>Cada respuesta incluye estos headers:</p>
          <div className="mt-2 space-y-1">
            <code className="text-xs block text-on-surface/60">
              <span className="text-blue-400">X-RateLimit-Limit:</span> 120
            </code>
            <code className="text-xs block text-on-surface/60">
              <span className="text-blue-400">X-RateLimit-Remaining:</span> 117
            </code>
            <code className="text-xs block text-on-surface/60">
              <span className="text-blue-400">X-RateLimit-Window:</span> 60
            </code>
          </div>
        </Callout>

        <Callout variant="warning" title="Cuando te excedés del límite">
          La API devuelve <code className="text-[#EF4444] bg-[#EF4444]/10 px-1 rounded">429 Too Many Requests</code>.
          Esperá a que se reinicie la ventana de 60 segundos. Implementá exponential backoff en tu cliente para manejar esto automáticamente.
        </Callout>
      </div>

      <CodeBlock
        lang="json"
        code={`// Respuesta cuando superás el rate limit
{
  "detail": "Rate limit exceeded. Maximum 30 requests per minute for Free plan."
}

// Headers de la respuesta 429:
// X-RateLimit-Limit: 30
// X-RateLimit-Window: 60
// Retry-After: 23`}
      />

      {/* Best practices */}
      <div className="mt-12">
        <SectionHeader title="Optimizá tu consumo" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { title: "Cacheá respuestas", desc: "Queries legales sobre legislación vigente no cambian seguido. Cacheá resultados por al menos 1 hora." },
            { title: "Usá search antes de query", desc: "Si solo necesitás encontrar artículos, /search es más rápido y consume menos tokens que /query." },
            { title: "Batch inteligente", desc: "Agrupá queries similares. Una consulta bien formulada puede reemplazar 5 queries genéricas." },
            { title: "Implementá retry con backoff", desc: "En caso de 429, esperá con exponential backoff. No reintentes inmediatamente." },
          ].map((tip) => (
            <div
              key={tip.title}
              className="p-4 rounded-lg bg-surface-container-low"
              style={{ border: "1px solid rgba(79,70,51,0.1)" }}
            >
              <p className="text-sm font-medium text-on-surface mb-1">{tip.title}</p>
              <p className="text-xs text-on-surface/40 leading-relaxed">{tip.desc}</p>
            </div>
          ))}
        </div>
      </div>

      <PageNav currentId="rate-limits" />
    </>
  );
}
