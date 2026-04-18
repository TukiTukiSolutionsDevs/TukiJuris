"use client";

import { Shield, Key, Clock, Globe, ArrowRight } from "lucide-react";
import { PageHero, SectionHeader, CodeBlock, Callout, TabGroup, PageNav } from "../_components";

export default function AuthenticationPage() {
  return (
    <>
      <PageHero
        title="Autenticación"
        highlight="segura"
        subtitle="Dos mecanismos para acceder a la API: JWT tokens para sesiones de usuario y API keys para integraciones servidor-a-servidor. Elegí el que mejor se adapte a tu caso."
        illustration="/docs/illustrations/authentication.png"
      />

      {/* Visual flow */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-12">
        <div
          className="p-5 rounded-xl bg-blue-500/5"
          style={{ border: "1px solid rgba(59,130,246,0.2)" }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold text-on-surface text-sm">JWT Bearer Token</h3>
          </div>
          <p className="text-xs text-on-surface/50 mb-4 leading-relaxed">
            Ideal para <strong className="text-on-surface">aplicaciones web</strong> y sesiones de usuario. 
            El token expira en 60 minutos y otorga acceso completo a la cuenta.
          </p>
          <div className="space-y-2">
            {[
              { icon: Clock, text: "Expira en 60 min" },
              { icon: Globe, text: "Acceso completo" },
              { icon: ArrowRight, text: "Login → Token → Request" },
            ].map((item) => (
              <div key={item.text} className="flex items-center gap-2 text-xs text-on-surface/40">
                <item.icon className="w-3 h-3 text-blue-400" />
                {item.text}
              </div>
            ))}
          </div>
        </div>

        <div
          className="p-5 rounded-xl bg-primary/5"
          style={{ border: "1px solid rgba(255,209,101,0.2)" }}
        >
          <div className="flex items-center gap-2 mb-3">
            <Key className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-on-surface text-sm">API Key</h3>
          </div>
          <p className="text-xs text-on-surface/50 mb-4 leading-relaxed">
            Ideal para <strong className="text-on-surface">integraciones backend</strong> y scripts. 
            Soporta scopes granulares y se puede revocar al instante.
          </p>
          <div className="space-y-2">
            {[
              { icon: Clock, text: "Sin expiración (o configurable)" },
              { icon: Key, text: "Scopes: query, search, analyze, documents" },
              { icon: Shield, text: "Revocable instantáneamente" },
            ].map((item) => (
              <div key={item.text} className="flex items-center gap-2 text-xs text-on-surface/40">
                <item.icon className="w-3 h-3 text-primary" />
                {item.text}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Comparison */}
      <SectionHeader
        title="Comparación detallada"
        subtitle="¿Cuándo usar cada método?"
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
              <th className="text-left px-4 py-3 text-on-surface/40 font-medium">Característica</th>
              <th className="text-left px-4 py-3 text-blue-400 font-medium">JWT Bearer</th>
              <th className="text-left px-4 py-3 text-primary font-medium">API Key</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["Cómo obtenerlo", "POST /api/auth/login", "POST /api/keys/"],
              ["Header", "Authorization: Bearer eyJ...", "X-API-Key: ak_..."],
              ["Expiración", "60 minutos", "Configurable o sin expiración"],
              ["Scopes", "Acceso completo a la cuenta", "query, search, analyze, documents"],
              ["Mejor para", "Apps web, sesiones de usuario", "Backends, scripts, CI/CD"],
              ["Revocable", "No (esperar expiración)", "Sí, al instante desde /api/keys/"],
              ["Seguridad", "Más seguro (corta vida)", "Requiere almacenamiento seguro"],
            ].map(([feature, jwt, apikey], idx) => (
              <tr
                key={feature}
                className={`hover:bg-surface-container-low transition-colors ${
                  idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                }`}
              >
                <td className="px-4 py-3 text-on-surface/50 font-medium">{feature}</td>
                <td className="px-4 py-3 font-mono text-xs text-blue-300">{jwt}</td>
                <td className="px-4 py-3 font-mono text-xs text-primary">{apikey}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* JWT Flow */}
      <SectionHeader
        title="Flujo JWT"
        subtitle="Registrate o logueate para obtener un token. Usalo en cada request."
      />

      <TabGroup
        tabs={[
          {
            label: "Login",
            content: (
              <CodeBlock
                lang="bash"
                code={`curl -X POST https://api.tukijuris.net.pe/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email": "dev@lawfirm.com", "password": "SecurePass123"}'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIs...",
#   "token_type": "bearer"
# }`}
              />
            ),
          },
          {
            label: "Usar el token",
            content: (
              <CodeBlock
                lang="bash"
                code={`# Usá el token en el header Authorization
curl -X POST https://api.tukijuris.net.pe/api/v1/query \\
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Plazo de prescripción en derecho penal"}'`}
              />
            ),
          },
        ]}
      />

      {/* API Key Flow */}
      <div className="mt-12">
        <SectionHeader
          title="Flujo API Key"
          subtitle="Creá una key con scopes específicos. Más simple para integración backend."
        />

        <TabGroup
          tabs={[
            {
              label: "Crear key",
              content: (
                <CodeBlock
                  lang="bash"
                  code={`# Necesitás un JWT token para crear la key
curl -X POST https://api.tukijuris.net.pe/api/keys/ \\
  -H "Authorization: Bearer eyJ..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Backend Integration",
    "scopes": ["query", "search"]
  }'

# IMPORTANTE: full_key solo se muestra UNA VEZ
# {"full_key": "ak_7f3b2c...", "key_prefix": "ak_7f3b", ...}`}
                />
              ),
            },
            {
              label: "Usar la key",
              content: (
                <CodeBlock
                  lang="bash"
                  code={`# Enviá la key en el header X-API-Key
curl -X POST https://api.tukijuris.net.pe/api/v1/query \\
  -H "X-API-Key: ak_7f3b2c..." \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Requisitos para constituir una SRL"}'`}
                />
              ),
            },
            {
              label: "Revocar",
              content: (
                <CodeBlock
                  lang="bash"
                  code={`# Listá tus keys activas
curl https://api.tukijuris.net.pe/api/keys/ \\
  -H "Authorization: Bearer eyJ..."

# Revocá una key específica por ID
curl -X DELETE https://api.tukijuris.net.pe/api/keys/key_id_123 \\
  -H "Authorization: Bearer eyJ..."

# La key deja de funcionar inmediatamente`}
                />
              ),
            },
          ]}
        />
      </div>

      {/* OAuth */}
      <div className="mt-12">
        <SectionHeader
          title="OAuth2 (Google & Microsoft)"
          subtitle="Single Sign-On para aplicaciones web."
        />
        <Callout variant="info" title="Flujo OAuth2">
          <p className="mb-2">
            Redirigí al usuario a uno de estos endpoints para iniciar el flujo:
          </p>
          <code className="text-primary bg-primary/10 px-1.5 py-0.5 rounded text-xs block mb-1">
            GET /api/auth/oauth/google/authorize
          </code>
          <code className="text-primary bg-primary/10 px-1.5 py-0.5 rounded text-xs block mb-2">
            GET /api/auth/oauth/microsoft/authorize
          </code>
          <p>
            Después del login, el callback redirige con un JWT token que podés usar normalmente.
          </p>
        </Callout>
      </div>

      {/* Best practices */}
      <div className="mt-12">
        <SectionHeader
          title="Best practices de seguridad"
        />
        <div className="space-y-3">
          {[
            { title: "Nunca expongas tokens en el frontend", desc: "Guardá las API keys en variables de entorno del servidor. Nunca las incluyas en código client-side o repositorios públicos." },
            { title: "Rotá las keys periódicamente", desc: "Creá keys nuevas y revocá las viejas cada 90 días como mínimo. Automatizá esto en tu pipeline de deployment." },
            { title: "Usá scopes mínimos", desc: "Si tu integración solo necesita búsqueda, creá la key solo con scope 'search'. Principio de least privilege." },
            { title: "Monitoreá el uso", desc: "Revisá /api/v1/usage regularmente para detectar consumo anómalo que pueda indicar una key comprometida." },
          ].map((practice) => (
            <div
              key={practice.title}
              className="flex items-start gap-3 p-4 rounded-lg bg-surface-container-low"
              style={{ border: "1px solid rgba(79,70,51,0.1)" }}
            >
              <Shield className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-on-surface mb-0.5">{practice.title}</p>
                <p className="text-xs text-on-surface/40 leading-relaxed">{practice.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <PageNav currentId="authentication" />
    </>
  );
}
