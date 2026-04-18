"use client";

import { Package, ExternalLink, CheckCircle2 } from "lucide-react";
import { PageHero, SectionHeader, CodeBlock, Callout, TabGroup, PageNav } from "../_components";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PYTHON_FEATURES = [
  "Typed responses con dataclasses",
  "Async support (httpx)",
  "Auto-retry con exponential backoff",
  "Rate limit handling automático",
  "Streaming para respuestas largas",
];

const TS_FEATURES = [
  "Full TypeScript types",
  "Fetch-based (zero dependencies)",
  "ESM + CJS support",
  "Auto-retry con configurable backoff",
  "Compatible con Node.js, Deno, Bun",
];

export default function SdksPage() {
  return (
    <>
      <PageHero
        title="SDKs"
        highlight="oficiales"
        subtitle="Librerías cliente listas para producción. Instalá, configurá tu API key, y empezá a consultar en segundos. Typed, con retry automático y manejo de errores incluido."
        illustration="/docs/illustrations/sdks.png"
      />

      {/* SDK Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-12">
        {/* Python */}
        <div
          className="p-6 rounded-xl bg-blue-500/5"
          style={{ border: "1px solid rgba(59,130,246,0.2)" }}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-blue-400" />
              <span className="font-semibold text-on-surface">Python</span>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-lg font-medium bg-[#10B981]/10 text-[#10B981]">
              Disponible
            </span>
          </div>
          <code className="text-xs font-mono text-on-surface/40 block mb-4">tukijuris</code>
          <div
            className="rounded-lg bg-surface-container-lowest px-4 py-2.5 mb-4"
            style={{ border: "1px solid rgba(79,70,51,0.15)" }}
          >
            <code className="text-sm font-mono text-primary">pip install tukijuris</code>
          </div>
          <div className="space-y-1.5">
            {PYTHON_FEATURES.map((f) => (
              <div key={f} className="flex items-center gap-2 text-xs text-on-surface/40">
                <CheckCircle2 className="w-3 h-3 text-blue-400 shrink-0" />
                {f}
              </div>
            ))}
          </div>
        </div>

        {/* TypeScript */}
        <div
          className="p-6 rounded-xl bg-primary/5"
          style={{ border: "1px solid rgba(255,209,101,0.2)" }}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-primary" />
              <span className="font-semibold text-on-surface">JavaScript / TypeScript</span>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-lg font-medium bg-[#10B981]/10 text-[#10B981]">
              Disponible
            </span>
          </div>
          <code className="text-xs font-mono text-on-surface/40 block mb-4">@tukijuris/sdk</code>
          <div
            className="rounded-lg bg-surface-container-lowest px-4 py-2.5 mb-4"
            style={{ border: "1px solid rgba(79,70,51,0.15)" }}
          >
            <code className="text-sm font-mono text-primary">npm install @tukijuris/sdk</code>
          </div>
          <div className="space-y-1.5">
            {TS_FEATURES.map((f) => (
              <div key={f} className="flex items-center gap-2 text-xs text-on-surface/40">
                <CheckCircle2 className="w-3 h-3 text-primary shrink-0" />
                {f}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick start */}
      <SectionHeader
        title="Quick Start"
        subtitle="De la instalación a tu primera consulta en 30 segundos."
      />

      <TabGroup
        tabs={[
          {
            label: "Python",
            content: (
              <CodeBlock
                lang="python"
                code={`from tukijuris import TukiJuris

client = TukiJuris(api_key="ak_...")

# Consulta legal con citas
result = client.query("¿Qué dice el Art. 1351 del Código Civil?")
print(result.answer)
for cite in result.citations:
    print(f"  [{cite.document}] {cite.content[:80]}...")

# Búsqueda directa en normativa
results = client.search("despido arbitrario indemnizacion", area="laboral")
for r in results:
    print(f"[score={r.score:.2f}] [{r.document}] {r.content[:100]}")

# Análisis completo de un caso
analysis = client.analyze("""
Un trabajador fue despedido verbalmente después de 3 años.
No recibió carta de despido ni pago de beneficios sociales.
""")
print("Áreas:", analysis.areas_detected)
print("Análisis:", analysis.analysis)`}
              />
            ),
          },
          {
            label: "TypeScript",
            content: (
              <CodeBlock
                lang="typescript"
                code={`import { TukiJuris } from "@tukijuris/sdk";

const client = new TukiJuris({ apiKey: "ak_..." });

// Consulta legal con citas
const result = await client.query("¿Qué dice el Art. 1351 del Código Civil?");
console.log(result.answer);
result.citations.forEach((cite) => {
  console.log(\`  [\${cite.document}] \${cite.content.slice(0, 80)}...\`);
});

// Búsqueda directa
const results = await client.search("despido arbitrario", { area: "laboral" });
results.forEach((r) => {
  console.log(\`[score=\${r.score.toFixed(2)}] [\${r.document}]\`, r.content.slice(0, 100));
});

// Análisis completo
const analysis = await client.analyze(\`
Un trabajador fue despedido verbalmente después de 3 años.
No recibió carta de despido ni pago de beneficios sociales.
\`);
console.log("Áreas:", analysis.areasDetected);
console.log("Análisis:", analysis.analysis);`}
              />
            ),
          },
        ]}
      />

      {/* Error handling */}
      <div className="mt-12">
        <SectionHeader
          title="Manejo de errores"
          subtitle="Los SDKs incluyen excepciones tipadas para cada tipo de error."
        />

        <TabGroup
          tabs={[
            {
              label: "Python",
              content: (
                <CodeBlock
                  lang="python"
                  code={`from tukijuris import TukiJuris, TukiError, RateLimitError

client = TukiJuris(api_key="ak_...")

try:
    result = client.query("¿Plazo de prescripción penal?")
except RateLimitError as e:
    print(f"Rate limit: reintentar en {e.retry_after}s")
except TukiError as e:
    print(f"Error {e.status_code}: {e.detail}")`}
                />
              ),
            },
            {
              label: "TypeScript",
              content: (
                <CodeBlock
                  lang="typescript"
                  code={`import { TukiJuris, TukiError, RateLimitError } from "@tukijuris/sdk";

const client = new TukiJuris({ apiKey: "ak_..." });

try {
  const result = await client.query("¿Plazo de prescripción penal?");
} catch (e) {
  if (e instanceof RateLimitError) {
    console.log(\`Rate limit: reintentar en \${e.retryAfter}s\`);
  } else if (e instanceof TukiError) {
    console.log(\`Error \${e.statusCode}: \${e.detail}\`);
  }
}`}
                />
              ),
            },
          ]}
        />
      </div>

      {/* Configuration */}
      <div className="mt-12">
        <SectionHeader
          title="Configuración avanzada"
          subtitle="Timeouts, retries y base URL customizable."
        />
        <CodeBlock
          lang="python"
          code={`client = TukiJuris(
    api_key="ak_...",
    base_url="https://api.tukijuris.net.pe",  # default
    timeout=30,        # segundos (default: 30)
    max_retries=3,     # reintentos automáticos (default: 3)
    retry_delay=1.0,   # delay inicial entre retries (default: 1.0)
)`}
        />
      </div>

      {/* CTA */}
      <div
        className="mt-12 p-6 rounded-xl bg-surface-container-low flex flex-col sm:flex-row items-center gap-4"
        style={{ border: "1px solid rgba(79,70,51,0.15)" }}
      >
        <div className="flex-1">
          <p className="text-sm font-medium text-on-surface mb-1">¿Necesitás ayuda?</p>
          <p className="text-xs text-on-surface/40">
            Abrí un issue en GitHub o escribinos. Para testing interactivo, usá el Swagger UI.
          </p>
        </div>
        <div className="flex gap-2">
          <a
            href="mailto:api@tukijuris.net.pe"
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-surface-container-low hover:bg-surface text-xs text-on-surface/60 font-medium transition-colors"
            style={{ border: "1px solid rgba(79,70,51,0.15)" }}
          >
            api@tukijuris.net.pe
          </a>
          <a
            href={`${API_URL}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-background text-xs font-medium transition-colors"
          >
            Swagger UI
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      <PageNav currentId="sdks" />
    </>
  );
}
