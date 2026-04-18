"use client";

import { Zap, Terminal, ExternalLink, Clock, Sparkles } from "lucide-react";
import { PageHero, SectionHeader, CodeBlock, Callout, TabGroup, PageNav } from "../_components";
import { PYTHON_EXAMPLE, JS_EXAMPLE, CURL_EXAMPLE } from "../_data/examples";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function GettingStartedPage() {
  return (
    <>
      <PageHero
        title="Tu primer query legal en"
        highlight="2 minutos"
        subtitle="Registrate, creá una API key, y empezá a consultar el corpus legal peruano completo. Sin configuración, sin SDKs obligatorios — solo HTTP."
        illustration="/docs/illustrations/getting-started.png"
      />

      {/* Quick stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-12">
        {[
          { label: "Áreas de derecho", value: "11", icon: Sparkles },
          { label: "Tiempo de setup", value: "~2 min", icon: Clock },
          { label: "Documentos indexados", value: "5,000+", icon: Terminal },
          { label: "Uptime", value: "99.9%", icon: Zap },
        ].map((stat) => (
          <div
            key={stat.label}
            className="flex flex-col items-center p-4 rounded-lg bg-surface-container-low text-center"
            style={{ border: "1px solid rgba(79,70,51,0.1)" }}
          >
            <stat.icon className="w-4 h-4 text-primary mb-2" />
            <span className="text-lg font-bold text-on-surface font-mono">{stat.value}</span>
            <span className="text-[10px] text-on-surface/40 uppercase tracking-wider mt-0.5">{stat.label}</span>
          </div>
        ))}
      </div>

      <SectionHeader
        title="Onboarding en 3 pasos"
        subtitle="De cero a tu primera respuesta legal con citas."
      />

      <Callout variant="tip" title="¿Solo querés probar sin código?">
        Abrí el{" "}
        <a
          href={`${API_URL}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary underline"
        >
          Swagger UI
        </a>{" "}
        y ejecutá queries directamente desde el browser. No necesitás nada instalado.
      </Callout>

      <div className="space-y-10 mt-8">
        {/* Step 1 */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <div
              className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary text-sm font-bold shrink-0"
              style={{ border: "1px solid rgba(255,209,101,0.2)" }}
            >
              1
            </div>
            <div>
              <h3 className="text-base font-semibold text-on-surface">Creá tu cuenta</h3>
              <p className="text-xs text-on-surface/40">Un POST y ya tenés tu JWT token</p>
            </div>
          </div>
          <CodeBlock
            lang="bash"
            code={`curl -X POST https://api.tukijuris.net.pe/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "dev@lawfirm.com",
    "password": "SecurePass123",
    "full_name": "Legal Developer"
  }'

# Response:
# {"access_token": "eyJ...", "token_type": "bearer"}`}
          />
          <Callout variant="info" title="OAuth también disponible">
            También podés registrarte con Google o Microsoft OAuth2.
            Consultá la sección de <strong>Authentication</strong> para más detalles.
          </Callout>
        </div>

        {/* Step 2 */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <div
              className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary text-sm font-bold shrink-0"
              style={{ border: "1px solid rgba(255,209,101,0.2)" }}
            >
              2
            </div>
            <div>
              <h3 className="text-base font-semibold text-on-surface">Generá una API Key</h3>
              <p className="text-xs text-on-surface/40">Permisos granulares por scope — query, search, analyze, documents</p>
            </div>
          </div>
          <CodeBlock
            lang="bash"
            code={`curl -X POST https://api.tukijuris.net.pe/api/keys/ \\
  -H "Authorization: Bearer eyJ..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Production Key",
    "scopes": ["query", "search", "analyze"]
  }'

# La full_key solo se muestra UNA VEZ — guardala bien:
# {"full_key": "ak_abc123...", "key_prefix": "ak_abc1", ...}`}
          />
          <Callout variant="warning" title="Guardá tu key">
            La API key completa solo se muestra al momento de creación. Si la perdés, tenés que crear una nueva y revocar la anterior.
          </Callout>
        </div>

        {/* Step 3 */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <div
              className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary text-sm font-bold shrink-0"
              style={{ border: "1px solid rgba(255,209,101,0.2)" }}
            >
              3
            </div>
            <div>
              <h3 className="text-base font-semibold text-on-surface">Hacé tu primera consulta</h3>
              <p className="text-xs text-on-surface/40">Elegí tu lenguaje preferido</p>
            </div>
          </div>
          <TabGroup
            tabs={[
              { label: "Python", content: <CodeBlock lang="python" code={PYTHON_EXAMPLE} /> },
              { label: "JavaScript", content: <CodeBlock lang="javascript" code={JS_EXAMPLE} /> },
              { label: "cURL", content: <CodeBlock lang="bash" code={CURL_EXAMPLE} /> },
            ]}
          />
        </div>
      </div>

      {/* What you get */}
      <div className="mt-16">
        <SectionHeader
          title="¿Qué obtenés en cada respuesta?"
          subtitle="Cada query devuelve una respuesta estructurada con citas verificables."
        />
        <CodeBlock
          lang="json"
          code={`{
  "answer": "Según el artículo 34 del TUO del D.Leg. 728 (LPCL), el despido...",
  "citations": [
    {
      "document": "TUO D.Leg. 728 - LPCL",
      "article": "Art. 34",
      "content": "Si el despido es arbitrario por no haberse expresado causa..."
    },
    {
      "document": "Cas. Lab. 7095-2014-Lima",
      "content": "La indemnización por despido arbitrario equivale a..."
    }
  ],
  "areas_detected": ["laboral"],
  "confidence": 0.94,
  "tokens_used": 847
}`}
        />
        <Callout variant="tip" title="Respuestas con fuentes reales">
          Cada cita incluye el documento fuente exacto, artículo y fragmento relevante. No es un LLM inventando — es retrieval-augmented generation sobre legislación peruana real.
        </Callout>
      </div>

      {/* CTA */}
      <div
        className="mt-12 p-6 rounded-xl bg-gradient-to-r from-primary/10 to-primary/5 flex flex-col sm:flex-row items-center gap-4"
        style={{ border: "1px solid rgba(255,209,101,0.2)" }}
      >
        <div className="flex-1">
          <p className="text-sm font-medium text-on-surface mb-1">¿Listo para integrar?</p>
          <p className="text-xs text-on-surface/40">
            Probá los endpoints en vivo con el Swagger UI o revisá los SDKs disponibles.
          </p>
        </div>
        <div className="flex gap-2">
          <a
            href={`${API_URL}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-background text-xs font-medium transition-colors"
          >
            <Terminal className="w-3.5 h-3.5" />
            Swagger UI
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      <PageNav currentId="getting-started" />
    </>
  );
}
