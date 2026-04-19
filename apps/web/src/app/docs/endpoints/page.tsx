"use client";

import { PageHero, SectionHeader, CodeBlock, MethodBadge, ScopeBadge, Callout, TabGroup, PageNav } from "../_components";
import { ENDPOINTS } from "../_data/endpoints";
import { SEARCH_EXAMPLE, ANALYZE_EXAMPLE } from "../_data/examples";

export default function EndpointsPage() {
  return (
    <>
      <PageHero
        title="Referencia de"
        highlight="Endpoints"
        subtitle="Todos los endpoints de la API organizados por funcionalidad. Cada endpoint incluye método, ruta, scopes requeridos y descripción completa."
        illustration="/docs/illustrations/endpoints.png"
      />

      <Callout variant="info" title="Autenticación requerida">
        Todos los endpoints bajo <code className="text-primary bg-primary/10 px-1 rounded">/api/v1/</code> requieren autenticación via JWT o API Key.
        Los endpoints de <code className="text-primary bg-primary/10 px-1 rounded">/api/auth/</code> son públicos.
      </Callout>

      <div className="space-y-12 mt-10">
        {ENDPOINTS.map((group) => (
          <div key={group.group}>
            <h3 className="text-xs font-semibold text-on-surface/40 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
              <span className="w-6 h-px bg-primary/30" />
              {group.group}
            </h3>
            <div className="space-y-3">
              {group.items.map((ep) => (
                <div
                  key={`${ep.method}-${ep.path}`}
                  className="group flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-lg bg-surface-container-low hover:bg-surface-container-low/80 transition-all"
                  style={{ border: "1px solid rgba(79,70,51,0.15)" }}
                >
                  <div className="flex items-center gap-3 shrink-0">
                    <MethodBadge method={ep.method} />
                    <code className="text-sm font-mono text-primary group-hover:text-primary/80 transition-colors">{ep.path}</code>
                  </div>
                  <div className="flex-1 flex flex-col sm:flex-row sm:items-center gap-2">
                    <p className="text-sm text-on-surface/50 flex-1">{ep.description}</p>
                    {ep.scope && <ScopeBadge scope={ep.scope} />}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Response format */}
      <div className="mt-16">
        <SectionHeader
          title="Formato de respuesta"
          subtitle="Todas las respuestas son JSON. Los endpoints de query incluyen citas verificables."
        />

        <TabGroup
          tabs={[
            {
              label: "Query response",
              content: (
                <CodeBlock
                  lang="json"
                  code={`{
  "answer": "Según el artículo 1351 del Código Civil, el contrato es...",
  "citations": [
    {
      "document": "Código Civil - Libro VII",
      "article": "Art. 1351",
      "content": "El contrato es el acuerdo de dos o más partes...",
      "relevance_score": 0.97
    }
  ],
  "areas_detected": ["civil"],
  "confidence": 0.94,
  "tokens_used": 623,
  "processing_time_ms": 1847
}`}
                />
              ),
            },
            {
              label: "Search response",
              content: (
                <CodeBlock
                  lang="json"
                  code={`{
  "results": [
    {
      "document": "TUO D.Leg. 728 - LPCL",
      "content": "Si el despido es arbitrario por no haberse expresado...",
      "score": 0.923,
      "area": "laboral",
      "chunk_id": "lpcl_art34_p2"
    },
    {
      "document": "Cas. Lab. 7095-2014-Lima",
      "content": "La indemnización por despido arbitrario equivale...",
      "score": 0.891,
      "area": "laboral",
      "chunk_id": "cas_7095_2014_sum"
    }
  ],
  "total_results": 47,
  "processing_time_ms": 234
}`}
                />
              ),
            },
            {
              label: "Analyze response",
              content: (
                <CodeBlock
                  lang="json"
                  code={`{
  "areas_detected": ["laboral", "civil"],
  "primary_area": "laboral",
  "analysis": "El caso presenta elementos de despido arbitrario según...",
  "applicable_norms": [
    "TUO D.Leg. 728 (LPCL) - Arts. 22-34",
    "D.S. 003-97-TR - Reglamento",
    "Ley 29497 - Nueva Ley Procesal del Trabajo"
  ],
  "recommended_actions": [
    "Demandar indemnización por despido arbitrario",
    "Solicitar pago de beneficios sociales pendientes",
    "Evaluar demanda de reposición si aplica"
  ],
  "confidence": 0.91,
  "tokens_used": 2341
}`}
                />
              ),
            },
          ]}
        />
      </div>

      {/* Code examples */}
      <div className="mt-16">
        <SectionHeader
          title="Ejemplos de integración"
          subtitle="Copiá y pegá estos ejemplos para arrancar rápido."
        />

        <div className="space-y-8">
          <div>
            <h4 className="text-sm text-on-surface/50 mb-3 font-medium">Búsqueda directa en el corpus legal</h4>
            <CodeBlock lang="python" code={SEARCH_EXAMPLE} />
          </div>
          <div>
            <h4 className="text-sm text-on-surface/50 mb-3 font-medium">Análisis completo de un caso</h4>
            <CodeBlock lang="python" code={ANALYZE_EXAMPLE} />
          </div>
        </div>
      </div>

      <Callout variant="tip" title="Probá en vivo">
        Todos estos endpoints están disponibles en el Swagger UI para pruebas interactivas.
        No necesitás escribir código para explorar la API.
      </Callout>

      <PageNav currentId="endpoints" />
    </>
  );
}
