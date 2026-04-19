"use client";

import { PageHero, SectionHeader, CodeBlock, Callout, PageNav } from "../_components";
import { LEGAL_AREAS } from "../_data/legal-areas";

const AREA_EXAMPLES: Record<string, string> = {
  civil: "¿Cuáles son los requisitos para la validez de un contrato según el Art. 1351?",
  penal: "¿Qué establece el NCPP sobre la prisión preventiva?",
  laboral: "¿Cómo se calcula la indemnización por despido arbitrario?",
  tributario: "¿Cuál es el plazo de prescripción de la deuda tributaria ante SUNAT?",
  administrativo: "¿Qué recursos administrativos puedo interponer según la LPAG?",
  corporativo: "¿Cuál es el capital mínimo para constituir una SAC?",
  constitucional: "¿Cuáles son los presupuestos para interponer un habeas corpus?",
  registral: "¿Qué documentos necesito para inscribir una compraventa en SUNARP?",
  competencia: "¿Qué protección otorga INDECOPI contra la competencia desleal?",
  compliance: "¿Qué obligaciones impone la Ley de Protección de Datos Personales?",
  comercio_exterior: "¿Cuáles son los regímenes aduaneros disponibles en Perú?",
};

export default function LegalAreasPage() {
  return (
    <>
      <PageHero
        title="11 áreas del"
        highlight="Derecho Peruano"
        subtitle="TukiJuris cubre las principales ramas del ordenamiento jurídico peruano. Cada área tiene su propio agente AI especializado, entrenado con legislación, jurisprudencia y doctrina específica."
        illustration="/docs/illustrations/legal-areas.png"
      />

      <Callout variant="tip" title="Uso en la API">
        Pasá el <code className="text-primary bg-primary/10 px-1 rounded">id</code> del área como parámetro{" "}
        <code className="text-primary bg-primary/10 px-1 rounded">legal_area</code> en los endpoints de search y analyze
        para filtrar resultados por especialidad.
      </Callout>

      <SectionHeader
        title="Áreas disponibles"
        subtitle="Cada área incluye legislación vigente, jurisprudencia relevante y doctrina actualizada."
      />

      <div className="grid grid-cols-1 gap-4 mb-12">
        {LEGAL_AREAS.map((area) => {
          const Icon = area.icon;
          const example = AREA_EXAMPLES[area.id];
          return (
            <div
              key={area.id}
              className="group p-5 rounded-xl bg-surface-container-low hover:bg-surface-container-low/80 transition-all"
              style={{ border: "1px solid rgba(79,70,51,0.12)" }}
            >
              <div className="flex items-start gap-4">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
                  style={{ background: "rgba(79,70,51,0.08)" }}
                >
                  <Icon className={`w-5 h-5 ${area.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <h3 className="text-sm font-semibold text-on-surface">{area.name}</h3>
                    <code className="text-[10px] font-mono text-on-surface/30 bg-surface px-2 py-0.5 rounded-lg">
                      {area.id}
                    </code>
                  </div>
                  <p className="text-xs text-on-surface/40 leading-relaxed mb-3">{area.desc}</p>
                  {example && (
                    <div
                      className="flex items-start gap-2 px-3 py-2 rounded-lg bg-surface/50 text-xs"
                      style={{ border: "1px solid rgba(79,70,51,0.08)" }}
                    >
                      <span className="text-primary shrink-0 mt-px">Q:</span>
                      <span className="text-on-surface/50 italic">{example}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Usage example */}
      <SectionHeader
        title="Ejemplo: filtrar por área"
        subtitle="Usá el parámetro area para enfocar la búsqueda en una especialidad."
      />

      <CodeBlock
        lang="python"
        code={`import httpx

API_KEY = "ak_your_key_here"

# Buscar solo en derecho laboral
response = httpx.post(
    "https://api.tukijuris.net.pe/api/v1/search",
    headers={"X-API-Key": API_KEY},
    json={
        "query": "despido arbitrario indemnización",
        "area": "laboral",  # <-- Filtra por área específica
        "limit": 5,
    },
)

# Sin el filtro, busca en las 11 áreas simultáneamente
response_all = httpx.post(
    "https://api.tukijuris.net.pe/api/v1/search",
    headers={"X-API-Key": API_KEY},
    json={
        "query": "prescripción de acciones",
        # Sin "area" → busca en todo el corpus
        "limit": 10,
    },
)`}
      />

      <div className="mt-8">
        <Callout variant="info" title="Detección automática de áreas">
          El endpoint <code className="text-primary bg-primary/10 px-1 rounded">/api/v1/analyze</code> detecta
          automáticamente las áreas relevantes del caso y puede identificar intersecciones entre múltiples ramas
          del derecho (e.g., un despido que involucra derecho laboral + constitucional).
        </Callout>
      </div>

      <PageNav currentId="legal-areas" />
    </>
  );
}
