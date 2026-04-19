"use client";

import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { PageHero, SectionHeader, CodeBlock, Callout, PageNav } from "../_components";
import { ERROR_CODES } from "../_data/constants";

const TROUBLESHOOTING: Record<string, string> = {
  "400": "Revisá el body del request. ¿El JSON es válido? ¿Incluiste todos los campos requeridos? Usá el Swagger UI para verificar el formato exacto.",
  "401": "Tu token JWT expiró (duran 60 min) o la API key es inválida. Generá un nuevo token con /api/auth/login o verificá que la key esté activa.",
  "403": "Tu API key no tiene el scope necesario. Ejemplo: si usás /api/v1/analyze, la key necesita el scope 'analyze'. Creá una nueva key con los scopes correctos.",
  "404": "El recurso no existe. Si es un documento, verificá el ID. Si es un endpoint, revisá la ruta — ¿incluiste el prefijo /api/v1/?",
  "409": "El email ya está registrado. Usá /api/auth/login para obtener un token, o /api/auth/reset-password si olvidaste la contraseña.",
  "422": "Error de validación. El campo 'detail' en la respuesta te dice exactamente qué parámetro falló y por qué. Revisalo.",
  "429": "Superaste el rate limit. Implementá exponential backoff y cacheá respuestas. Consultá la sección de Rate Limits para ver tu límite actual.",
  "502": "Error upstream — el LLM o la base de datos vectorial está temporalmente no disponible. Reintentá después de unos segundos. Si persiste, revisá /status.",
};

export default function ErrorCodesPage() {
  return (
    <>
      <PageHero
        title="Códigos de error y"
        highlight="Troubleshooting"
        subtitle="Guía completa de errores que puede devolver la API, qué significan y cómo resolverlos. No solo la tabla — también qué hacer cuando los encontrás."
        illustration="/docs/illustrations/error-codes.png"
      />

      {/* Visual summary */}
      <div className="grid grid-cols-3 gap-3 mb-12">
        <div
          className="flex flex-col items-center p-4 rounded-xl bg-[#10B981]/5 text-center"
          style={{ border: "1px solid rgba(16,185,129,0.15)" }}
        >
          <CheckCircle2 className="w-6 h-6 text-[#10B981] mb-2" />
          <span className="text-xs font-medium text-[#10B981]">2xx Success</span>
          <span className="text-[10px] text-on-surface/30 mt-1">Todo bien</span>
        </div>
        <div
          className="flex flex-col items-center p-4 rounded-xl bg-primary/5 text-center"
          style={{ border: "1px solid rgba(255,209,101,0.15)" }}
        >
          <AlertTriangle className="w-6 h-6 text-primary mb-2" />
          <span className="text-xs font-medium text-primary">4xx Client Error</span>
          <span className="text-[10px] text-on-surface/30 mt-1">Error tuyo</span>
        </div>
        <div
          className="flex flex-col items-center p-4 rounded-xl bg-[#EF4444]/5 text-center"
          style={{ border: "1px solid rgba(239,68,68,0.15)" }}
        >
          <XCircle className="w-6 h-6 text-[#EF4444] mb-2" />
          <span className="text-xs font-medium text-[#EF4444]">5xx Server Error</span>
          <span className="text-[10px] text-on-surface/30 mt-1">Error nuestro</span>
        </div>
      </div>

      <SectionHeader
        title="Referencia de errores"
        subtitle="Cada error incluye código, significado y cómo solucionarlo."
      />

      {/* Error cards instead of just a table */}
      <div className="space-y-4 mb-12">
        {ERROR_CODES.map((err) => {
          const colorClass = err.code.startsWith("4")
            ? "text-primary border-primary/20 bg-primary/5"
            : "text-[#EF4444] border-[#EF4444]/20 bg-[#EF4444]/5";

          return (
            <div
              key={err.code}
              className="rounded-xl overflow-hidden"
              style={{ border: "1px solid rgba(79,70,51,0.12)" }}
            >
              <div className="flex items-center gap-3 px-5 py-3 bg-surface-container-low">
                <span className={`font-mono text-sm font-bold px-2.5 py-1 rounded-lg ${colorClass}`}>
                  {err.code}
                </span>
                <span className="font-medium text-on-surface text-sm">{err.title}</span>
              </div>
              <div className="px-5 py-4 space-y-2">
                <p className="text-sm text-on-surface/50">{err.desc}</p>
                {TROUBLESHOOTING[err.code] && (
                  <div className="flex items-start gap-2 mt-2 pt-2" style={{ borderTop: "1px solid rgba(79,70,51,0.08)" }}>
                    <span className="text-[10px] uppercase tracking-wider text-primary font-medium shrink-0 mt-0.5">Fix:</span>
                    <p className="text-xs text-on-surface/40 leading-relaxed">{TROUBLESHOOTING[err.code]}</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <SectionHeader
        title="Formato de error"
        subtitle="Todas las respuestas de error siguen el mismo formato JSON."
      />

      <CodeBlock
        lang="json"
        code={`// Error simple
{
  "detail": "API key does not have the 'analyze' scope"
}

// Error de validación (422) — con detalles por campo
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}`}
      />

      <div className="mt-8">
        <Callout variant="tip" title="Consejo de implementación">
          Siempre parseá el campo <code className="text-primary bg-primary/10 px-1 rounded">detail</code> de la respuesta.
          Para errores 422, <code className="text-primary bg-primary/10 px-1 rounded">detail</code> es un array con la ubicación exacta del error
          (<code className="text-primary bg-primary/10 px-1 rounded">loc</code>) y el mensaje descriptivo.
        </Callout>
      </div>

      <PageNav currentId="error-codes" />
    </>
  );
}
