"use client";

import { useState } from "react";
import {
  Scale,
  Key,
  Zap,
  BookOpen,
  Shield,
  Briefcase,
  Landmark,
  Building2,
  ScrollText,
  FileCheck,
  Globe,
  Lock,
  BadgeCheck,
  Gavel,
  ExternalLink,
  Copy,
  Check,
  ChevronRight,
  ChevronDown,
  Terminal,
  AlertCircle,
  Code2,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { AppLayout } from "@/components/AppLayout";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface NavItem {
  id: string;
  label: string;
}

interface EndpointDoc {
  method: "GET" | "POST" | "PUT" | "DELETE";
  path: string;
  scope?: string;
  description: string;
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const NAV_ITEMS: NavItem[] = [
  { id: "getting-started", label: "Getting Started" },
  { id: "authentication", label: "Authentication" },
  { id: "endpoints", label: "Endpoints" },
  { id: "rate-limits", label: "Rate Limits" },
  { id: "legal-areas", label: "Legal Areas" },
  { id: "error-codes", label: "Error Codes" },
  { id: "sdks", label: "SDKs" },
];

const LEGAL_AREAS = [
  { id: "civil", name: "Derecho Civil", icon: BookOpen, color: "text-blue-400", desc: "Código Civil, CPC, Familia, Sucesiones, Contratos, Obligaciones" },
  { id: "penal", name: "Derecho Penal", icon: Shield, color: "text-red-400", desc: "Código Penal, NCPP, Ejecución Penal" },
  { id: "laboral", name: "Derecho Laboral", icon: Briefcase, color: "text-green-400", desc: "LPCL, Seguridad y Salud, Relaciones Colectivas, CTS, Vacaciones" },
  { id: "tributario", name: "Derecho Tributario", icon: Landmark, color: "text-yellow-400", desc: "Código Tributario, IR, IGV, SUNAT, Procedimientos" },
  { id: "administrativo", name: "Derecho Administrativo", icon: Building2, color: "text-orange-400", desc: "LPAG, Contrataciones del Estado, Procedimientos Sancionadores" },
  { id: "corporativo", name: "Derecho Corporativo", icon: ScrollText, color: "text-cyan-400", desc: "LGS, Mercado de Valores, MYPE, Fusiones y Adquisiciones" },
  { id: "constitucional", name: "Derecho Constitucional", icon: Gavel, color: "text-purple-400", desc: "Constitución 1993, Procesos Constitucionales, TC" },
  { id: "registral", name: "Derecho Registral", icon: FileCheck, color: "text-pink-400", desc: "SUNARP, Registros Públicos, Inscripciones" },
  { id: "competencia", name: "Competencia y PI", icon: BadgeCheck, color: "text-amber-400", desc: "INDECOPI, Marcas, Patentes, Consumidor, Libre Competencia" },
  { id: "compliance", name: "Compliance", icon: Lock, color: "text-indigo-400", desc: "Datos Personales, Anticorrupción, Lavado de Activos, LAFT" },
  { id: "comercio_exterior", name: "Comercio Exterior", icon: Globe, color: "text-teal-400", desc: "Aduanas, TLC, MINCETUR, Regímenes Aduaneros" },
];

const ENDPOINTS: { group: string; items: EndpointDoc[] }[] = [
  {
    group: "Queries & Analysis",
    items: [
      {
        method: "POST",
        path: "/api/v1/query",
        scope: "query",
        description: "Submit a legal question. Returns an AI-generated answer with citations to source documents.",
      },
      {
        method: "POST",
        path: "/api/v1/search",
        scope: "search",
        description: "Hybrid BM25 + semantic search over the knowledge base. Returns ranked document chunks.",
      },
      {
        method: "POST",
        path: "/api/v1/analyze",
        scope: "analyze",
        description: "Deep case analysis. Identifies all applicable areas of law and produces a structured legal assessment.",
      },
    ],
  },
  {
    group: "Knowledge Base",
    items: [
      {
        method: "GET",
        path: "/api/v1/areas",
        description: "List the 11 available areas of Peruvian law.",
      },
      {
        method: "GET",
        path: "/api/v1/documents",
        scope: "documents",
        description: "Browse indexed legal documents. Supports filtering by area and pagination.",
      },
    ],
  },
  {
    group: "Account & Usage",
    items: [
      {
        method: "GET",
        path: "/api/v1/usage",
        description: "API key usage stats: queries today, this month, and rate limit.",
      },
    ],
  },
  {
    group: "Authentication",
    items: [
      {
        method: "POST",
        path: "/api/auth/register",
        description: "Create a new account. Returns a JWT token.",
      },
      {
        method: "POST",
        path: "/api/auth/login",
        description: "Login with email and password. Returns a JWT token.",
      },
    ],
  },
  {
    group: "API Keys",
    items: [
      {
        method: "POST",
        path: "/api/keys/",
        description: "Create a new API key with custom name and scopes.",
      },
      {
        method: "GET",
        path: "/api/keys/",
        description: "List all API keys for the authenticated user.",
      },
      {
        method: "DELETE",
        path: "/api/keys/{key_id}",
        description: "Revoke an API key.",
      },
    ],
  },
];

const RATE_LIMITS = [
  { plan: "Anonymous", rpm: "10", notes: "IP-based, no auth required" },
  { plan: "Free", rpm: "30", notes: "JWT or API key" },
  { plan: "Pro", rpm: "120", notes: "JWT or API key" },
  { plan: "Enterprise", rpm: "600", notes: "Custom limits available" },
];

const ERROR_CODES = [
  { code: "400", title: "Bad Request", desc: "Malformed request body or invalid parameters." },
  { code: "401", title: "Unauthorized", desc: "No valid JWT or API key was provided." },
  { code: "403", title: "Forbidden", desc: "Authenticated, but API key lacks the required scope." },
  { code: "404", title: "Not Found", desc: "The requested resource does not exist." },
  { code: "409", title: "Conflict", desc: "Email already registered (during registration)." },
  { code: "422", title: "Unprocessable Entity", desc: "Validation error — check the `detail` field in the response body." },
  { code: "429", title: "Too Many Requests", desc: "Rate limit exceeded. See X-RateLimit-Limit header." },
  { code: "502", title: "Bad Gateway", desc: "Upstream AI error — LLM or vector database unavailable." },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MethodBadge({ method }: { method: EndpointDoc["method"] }) {
  const colors: Record<EndpointDoc["method"], string> = {
    GET: "bg-[#60A5FA]/20 text-[#60A5FA] border-[#60A5FA]/30",
    POST: "bg-[#34D399]/20 text-[#34D399] border-[#34D399]/30",
    PUT: "bg-[#EAB308]/20 text-[#EAB308] border-[#EAB308]/30",
    DELETE: "bg-[#F87171]/20 text-[#F87171] border-[#F87171]/30",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-bold border ${colors[method]}`}>
      {method}
    </span>
  );
}

function ScopeBadge({ scope }: { scope: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-violet-500/10 text-violet-400 border border-violet-500/20">
      <Key className="w-2.5 h-2.5" />
      {scope}
    </span>
  );
}

function CodeBlock({ lang, code }: { lang: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative rounded-xl border border-[#2A2A35] bg-[#0A0A0F] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[#2A2A35] bg-[#0A0A0F]/80">
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-[#6B7280]" />
          <span className="text-xs text-[#6B7280] font-mono">{lang}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-[#6B7280] hover:text-[#F5F5F5] transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-green-400" />
              <span className="text-green-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 text-sm font-mono leading-relaxed overflow-x-auto text-[#F5F5F5] whitespace-pre">
        <code>{code}</code>
      </pre>
    </div>
  );
}

function SectionHeader({ id, title, subtitle }: { id: string; title: string; subtitle?: string }) {
  return (
    <div id={id} className="scroll-mt-24 mb-6">
      <h2 className="text-2xl font-bold text-white mb-1">{title}</h2>
      {subtitle && <p className="text-[#9CA3AF] text-sm">{subtitle}</p>}
      <div className="mt-3 h-px bg-gradient-to-r from-[#EAB308]/40 to-transparent" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Code Examples
// ---------------------------------------------------------------------------

const PYTHON_EXAMPLE = `import httpx

API_KEY = "ak_your_key_here"
BASE_URL = "https://api.tukijuris.net.pe"

# Make a legal query
response = httpx.post(
    f"{BASE_URL}/api/v1/query",
    headers={"X-API-Key": API_KEY},
    json={"query": "Requisitos para un despido justificado en Peru"},
)
data = response.json()
print(data["answer"])

# Citations from the legal corpus
for citation in data["citations"]:
    print(f"[{citation['document']}] {citation['content'][:100]}...")`;

const JS_EXAMPLE = `const API_KEY = "ak_your_key_here";
const BASE_URL = "https://api.tukijuris.net.pe";

// Make a legal query
const response = await fetch(\`\${BASE_URL}/api/v1/query\`, {
  method: "POST",
  headers: {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    query: "Requisitos para un despido justificado en Peru",
  }),
});

const data = await response.json();
console.log(data.answer);

// Citations from the legal corpus
data.citations.forEach((c) => {
  console.log(\`[\${c.document}]\`, c.content.slice(0, 100));
});`;

const CURL_EXAMPLE = `# Register and get a JWT token
curl -X POST https://api.tukijuris.net.pe/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email": "you@lawfirm.com", "password": "your-password"}'

# Use the JWT token to make a legal query
curl -X POST https://api.tukijuris.net.pe/api/v1/query \\
  -H "Authorization: Bearer eyJ..." \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Plazos de prescripcion en derecho penal peruano"}'

# Or use an API key directly
curl -X POST https://api.tukijuris.net.pe/api/v1/query \\
  -H "X-API-Key: ak_your_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Como se calcula la CTS en Peru"}'`;

const SEARCH_EXAMPLE = `import httpx

API_KEY = "ak_your_key_here"
BASE_URL = "https://api.tukijuris.net.pe"

# Search the legal knowledge base directly
response = httpx.post(
    f"{BASE_URL}/api/v1/search",
    headers={"X-API-Key": API_KEY},
    json={
        "query": "despido arbitrario indemnizacion",
        "area": "laboral",
        "limit": 5,
    },
)
results = response.json()["results"]
for r in results:
    print(f"[score={r['score']:.3f}] [{r['document']}] {r['content'][:120]}...")`;

const ANALYZE_EXAMPLE = `import httpx

API_KEY = "ak_your_key_here"
BASE_URL = "https://api.tukijuris.net.pe"

case = """
Un trabajador fue despedido verbalmente despues de 3 años en la empresa.
No recibio carta de despido ni pago de beneficios sociales.
Desea saber que acciones legales puede tomar.
"""

response = httpx.post(
    f"{BASE_URL}/api/v1/analyze",
    headers={"X-API-Key": API_KEY},
    json={"case_description": case},
)
result = response.json()
print("Areas detectadas:", result["areas_detected"])
print("\\nAnalisis:")
print(result["analysis"])`;

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function DocsPage() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [activeSection, setActiveSection] = useState("getting-started");
  const [tocOpen, setTocOpen] = useState(false);

  const scrollTo = (id: string) => {
    setActiveSection(id);
    setTocOpen(false);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

   return (
    <AppLayout>
      <div className="min-h-full text-[#F5F5F5]">
        {/* Top bar */}
        <div className="sticky top-0 z-50 border-b border-[#1E1E2A] bg-[#0A0A0F]/95 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Image
                src="/brand/logo-full.png"
                alt="TukiJuris"
                width={120}
                height={32}
                className="h-7 w-auto"
              />
              <span className="text-[#2A2A35] text-lg select-none">/</span>
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4 text-[#EAB308]" />
                <span className="font-bold text-sm">API Docs</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <a
                href={`${API_URL}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="hidden sm:flex items-center gap-1.5 text-xs text-[#9CA3AF] hover:text-[#EAB308] transition-colors border border-[#1E1E2A] hover:border-[#EAB308]/50 rounded-lg px-3 py-1.5"
              >
                <Terminal className="w-3.5 h-3.5" />
                Swagger UI
                <ExternalLink className="w-3 h-3" />
              </a>
              <a
                href={`${API_URL}/redoc`}
                target="_blank"
                rel="noopener noreferrer"
                className="hidden sm:flex items-center gap-1.5 text-xs text-[#9CA3AF] hover:text-[#EAB308] transition-colors border border-[#1E1E2A] hover:border-[#EAB308]/50 rounded-lg px-3 py-1.5"
              >
                <Code2 className="w-3.5 h-3.5" />
                ReDoc
                <ExternalLink className="w-3 h-3" />
              </a>
              {/* Mobile TOC toggle */}
              <button
                className="lg:hidden flex items-center gap-1.5 text-xs text-[#9CA3AF] hover:text-white border border-[#1E1E2A] rounded-lg px-3 py-1.5 transition-colors"
                onClick={() => setTocOpen(!tocOpen)}
              >
                Contenidos
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${tocOpen ? "rotate-180" : ""}`} />
              </button>
            </div>
          </div>
          {/* Mobile TOC dropdown */}
          {tocOpen && (
            <div className="lg:hidden border-t border-[#1E1E2A] bg-[#0A0A0F]/98 px-4 py-3">
              <nav className="flex flex-wrap gap-1">
                {NAV_ITEMS.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => scrollTo(item.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
                      activeSection === item.id
                        ? "bg-[#EAB308]/10 text-[#EAB308] font-medium"
                        : "text-[#9CA3AF] hover:text-[#F5F5F5] hover:bg-[#1A1A22]"
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </nav>
            </div>
          )}
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex gap-0 lg:gap-10">
        {/* Sidebar TOC — sticky on desktop */}
        <aside className="hidden lg:block w-56 shrink-0">
          <div className="sticky top-[3.6rem] pt-10 pb-20">
            <p className="text-xs uppercase tracking-widest text-[#6B7280] mb-4 font-medium">Contents</p>
            <nav className="space-y-0.5">
              {NAV_ITEMS.map((item) => (
                <button
                  key={item.id}
                  onClick={() => scrollTo(item.id)}
                  className={`w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                    activeSection === item.id
                      ? "bg-[#EAB308]/10 text-[#EAB308] font-medium"
                      : "text-[#6B7280] hover:text-[#F5F5F5] hover:bg-[#1A1A22]"
                  }`}
                >
                  {activeSection === item.id && (
                    <ChevronRight className="w-3 h-3 text-[#EAB308] shrink-0" />
                  )}
                  <span className={activeSection === item.id ? "" : "ml-5"}>{item.label}</span>
                </button>
              ))}
            </nav>

            <div className="mt-8 p-3 rounded-xl border border-[#EAB308]/20 bg-[#EAB308]/5">
              <p className="text-xs text-[#EAB308] font-medium mb-1">Interactive testing</p>
              <p className="text-xs text-[#6B7280] mb-3">Try all endpoints directly in your browser.</p>
              <a
                href={`${API_URL}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-xs text-[#EAB308] hover:text-[#EAB308]/80 transition-colors"
              >
                Open Swagger UI
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 min-w-0 py-8 sm:py-10 space-y-16 sm:space-y-20">

          {/* Hero */}
          <section className="pt-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#EAB308]/10 border border-[#EAB308]/20 text-[#EAB308] text-xs font-medium mb-6">
              <Zap className="w-3 h-3" />
              API v0.4 — Public Beta
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
              TukiJuris{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#EAB308] to-orange-500">
                API
              </span>
            </h1>
            <p className="text-base sm:text-lg text-[#9CA3AF] max-w-2xl leading-relaxed mb-6 sm:mb-8">
              Integrate Peruvian legal intelligence into your application. Query 11 specialized AI
              agents, search indexed legislation and regulations, and analyze legal cases — all
              through a simple REST API.
            </p>
            <div className="flex flex-wrap gap-3">
              <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#111116] border border-[#1E1E2A] text-sm">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[#F5F5F5]">Base URL:</span>
                <code className="font-mono text-[#EAB308]">https://api.tukijuris.net.pe</code>
              </div>
              <a
                href={`${API_URL}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#EAB308] hover:bg-[#EAB308]/90 text-[#0A0A0F] text-sm font-medium transition-colors"
              >
                <Terminal className="w-4 h-4" />
                Try in Swagger UI
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </section>

          {/* Getting Started */}
          <section>
            <SectionHeader
              id="getting-started"
              title="Getting Started"
              subtitle="Integrate the API in under 5 minutes."
            />

            <div className="p-5 rounded-xl bg-[#2C3E50]/20 border border-[#2C3E50]/30 mb-8">
              <p className="text-sm text-[#9CA3AF]">
                <span className="text-[#EAB308] font-medium">Quick start:</span>{" "}
                Register → Create API key → Make your first query. That&apos;s it.
              </p>
            </div>

            <div className="space-y-10">
              {/* Step 1 */}
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-7 h-7 rounded-full bg-[#EAB308]/15 border border-[#EAB308]/30 flex items-center justify-center text-[#EAB308] text-sm font-bold shrink-0">1</div>
                  <h3 className="text-base font-semibold text-white">Create an account</h3>
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
              </div>

              {/* Step 2 */}
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-7 h-7 rounded-full bg-[#EAB308]/15 border border-[#EAB308]/30 flex items-center justify-center text-[#EAB308] text-sm font-bold shrink-0">2</div>
                  <h3 className="text-base font-semibold text-white">Create an API key</h3>
                </div>
                <p className="text-sm text-[#9CA3AF] mb-3">
                  API keys support granular scopes: <code className="text-violet-400 bg-violet-500/10 px-1 rounded">query</code>{" "}
                  <code className="text-violet-400 bg-violet-500/10 px-1 rounded">search</code>{" "}
                  <code className="text-violet-400 bg-violet-500/10 px-1 rounded">analyze</code>{" "}
                  <code className="text-violet-400 bg-violet-500/10 px-1 rounded">documents</code>.
                  The full key is returned <strong className="text-white">only once</strong> — save it securely.
                </p>
                <CodeBlock
                  lang="bash"
                  code={`curl -X POST https://api.tukijuris.net.pe/api/keys/ \\
  -H "Authorization: Bearer eyJ..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Production Key",
    "scopes": ["query", "search", "analyze"]
  }'

# Response includes full_key — save it, it won't be shown again:
# {"full_key": "ak_abc123...", "key_prefix": "ak_abc1", ...}`}
                />
              </div>

              {/* Step 3 */}
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-7 h-7 rounded-full bg-[#EAB308]/15 border border-[#EAB308]/30 flex items-center justify-center text-[#EAB308] text-sm font-bold shrink-0">3</div>
                  <h3 className="text-base font-semibold text-white">Make your first query</h3>
                </div>
                <div className="grid grid-cols-1 xl:grid-cols-3 gap-3 mb-3">
                  {(["Python", "JavaScript", "cURL"] as const).map((l) => (
                    <div key={l} className="text-xs text-center py-1.5 rounded-lg bg-[#111116] border border-[#1E1E2A] text-[#9CA3AF] cursor-pointer">
                      {l}
                    </div>
                  ))}
                </div>
                <div className="space-y-4">
                  <CodeBlock lang="python" code={PYTHON_EXAMPLE} />
                  <CodeBlock lang="javascript" code={JS_EXAMPLE} />
                  <CodeBlock lang="bash (cURL)" code={CURL_EXAMPLE} />
                </div>
              </div>
            </div>
          </section>

          {/* Authentication */}
          <section>
            <SectionHeader
              id="authentication"
              title="Authentication"
              subtitle="Two methods supported: JWT Bearer tokens and API keys."
            />

            {/* Comparison table */}
            <div className="overflow-x-auto rounded-xl border border-[#1E1E2A] mb-8">
              <table className="w-full min-w-[500px] text-sm">
                <thead>
                  <tr className="border-b border-[#1E1E2A] bg-[#111116]">
                    <th className="text-left px-4 py-3 text-[#9CA3AF] font-medium">Feature</th>
                    <th className="text-left px-4 py-3 text-[#9CA3AF] font-medium">JWT Bearer</th>
                    <th className="text-left px-4 py-3 text-[#9CA3AF] font-medium">API Key</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E1E2A]/50">
                  {[
                    ["How to get", "POST /api/auth/login", "POST /api/keys/"],
                    ["Header", "Authorization: Bearer eyJ...", "X-API-Key: ak_..."],
                    ["Expiry", "60 minutos", "Optional expiry date"],
                    ["Scopes", "Full access", "query, search, analyze, documents"],
                    ["Best for", "User sessions, web apps", "Server-to-server integrations"],
                    ["Revokable", "No (wait for expiry)", "Yes, instantly"],
                  ].map(([feature, jwt, apikey]) => (
                    <tr key={feature} className="hover:bg-[#1A1A22] transition-colors">
                      <td className="px-4 py-3 text-[#9CA3AF] font-medium">{feature}</td>
                      <td className="px-4 py-3 font-mono text-xs text-blue-300">{jwt}</td>
                      <td className="px-4 py-3 font-mono text-xs text-violet-300">{apikey}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-start gap-3 p-4 rounded-xl bg-[#EAB308]/5 border border-[#EAB308]/20">
              <AlertCircle className="w-4 h-4 text-[#EAB308] shrink-0 mt-0.5" />
              <p className="text-sm text-[#9CA3AF]">
                <strong className="text-[#EAB308]">SSO:</strong> Google and Microsoft OAuth2 are also
                supported. Start the flow with{" "}
                <code className="text-[#EAB308] bg-[#EAB308]/10 px-1 rounded">GET /api/auth/oauth/google/authorize</code>{" "}
                or{" "}
                <code className="text-[#EAB308] bg-[#EAB308]/10 px-1 rounded">GET /api/auth/oauth/microsoft/authorize</code>.
                Both return a JWT token on callback.
              </p>
            </div>
          </section>

          {/* Endpoints */}
          <section>
            <SectionHeader
              id="endpoints"
              title="Endpoints Reference"
              subtitle="Grouped by functionality. All v1 endpoints require authentication."
            />

            <div className="space-y-10">
              {ENDPOINTS.map((group) => (
                <div key={group.group}>
                  <h3 className="text-sm font-semibold text-[#F5F5F5] uppercase tracking-widest mb-4">
                    {group.group}
                  </h3>
                  <div className="space-y-3">
                    {group.items.map((ep) => (
                      <div
                        key={ep.path}
                        className="flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-xl bg-[#111116] border border-[#1E1E2A] hover:border-[#2A2A35] transition-colors"
                      >
                        <div className="flex items-center gap-3 shrink-0">
                          <MethodBadge method={ep.method} />
                          <code className="text-sm font-mono text-[#EAB308]">{ep.path}</code>
                        </div>
                        <div className="flex-1 flex flex-col sm:flex-row sm:items-center gap-2">
                          <p className="text-sm text-[#9CA3AF] flex-1">{ep.description}</p>
                          {ep.scope && <ScopeBadge scope={ep.scope} />}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Code examples for search and analyze */}
            <div className="mt-12 space-y-8">
              <h3 className="text-lg font-semibold text-white">More Examples</h3>
              <div>
                <p className="text-sm text-[#9CA3AF] mb-3 font-medium">Search the knowledge base directly</p>
                <CodeBlock lang="python" code={SEARCH_EXAMPLE} />
              </div>
              <div>
                <p className="text-sm text-[#9CA3AF] mb-3 font-medium">Analyze a legal case</p>
                <CodeBlock lang="python" code={ANALYZE_EXAMPLE} />
              </div>
            </div>
          </section>

          {/* Rate Limits */}
          <section>
            <SectionHeader
              id="rate-limits"
              title="Rate Limits"
              subtitle="Applied per IP (anonymous) or per user/key (authenticated)."
            />

            <div className="overflow-x-auto rounded-xl border border-[#1E1E2A] mb-6">
              <table className="w-full min-w-[400px] text-sm">
                <thead>
                  <tr className="border-b border-[#1E1E2A] bg-[#111116]">
                    <th className="text-left px-4 py-3 text-[#9CA3AF] font-medium">Plan</th>
                    <th className="text-left px-4 py-3 text-[#9CA3AF] font-medium">Requests / min</th>
                    <th className="text-left px-4 py-3 text-[#9CA3AF] font-medium">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E1E2A]/50">
                  {RATE_LIMITS.map((row) => (
                    <tr key={row.plan} className="hover:bg-[#1A1A22] transition-colors">
                      <td className="px-4 py-3 font-medium text-white">{row.plan}</td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-[#EAB308] font-bold">{row.rpm}</span>
                        <span className="text-[#6B7280] text-xs ml-1">req/min</span>
                      </td>
                      <td className="px-4 py-3 text-[#9CA3AF] text-xs">{row.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex items-start gap-3 p-4 rounded-xl bg-[#111116] border border-[#1E1E2A]">
              <AlertCircle className="w-4 h-4 text-[#6B7280] shrink-0 mt-0.5" />
              <p className="text-sm text-[#9CA3AF]">
                When rate-limited, the API returns <code className="text-[#F87171] bg-[#F87171]/10 px-1 rounded">429</code>.
                The <code className="text-[#F5F5F5] bg-[#1A1A22] px-1 rounded">X-RateLimit-Limit</code> and{" "}
                <code className="text-[#F5F5F5] bg-[#1A1A22] px-1 rounded">X-RateLimit-Window</code> response headers
                indicate the limit and the time window.
              </p>
            </div>
          </section>

          {/* Legal Areas */}
          <section>
            <SectionHeader
              id="legal-areas"
              title="Legal Areas"
              subtitle="11 specialized areas of Peruvian law. Pass the id as the legal_area parameter."
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {LEGAL_AREAS.map((area) => {
                const Icon = area.icon;
                return (
                  <div
                    key={area.id}
                    className="flex items-start gap-3 p-4 rounded-xl bg-[#111116] border border-[#1E1E2A] hover:border-[#2A2A35] transition-colors"
                  >
                    <div className="shrink-0 mt-0.5">
                      <Icon className={`w-4 h-4 ${area.color}`} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-sm font-medium text-white">{area.name}</span>
                        <code className="text-xs font-mono text-[#6B7280] bg-[#1A1A22] px-1.5 py-0.5 rounded">
                          {area.id}
                        </code>
                      </div>
                      <p className="text-xs text-[#6B7280] leading-relaxed">{area.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Error Codes */}
          <section>
            <SectionHeader
              id="error-codes"
              title="Error Codes"
              subtitle="All errors return JSON with a detail field describing the problem."
            />

            <div className="overflow-x-auto rounded-xl border border-[#1E1E2A] mb-6">
              <table className="w-full min-w-[480px] text-sm">
                <thead>
                  <tr className="border-b border-[#1E1E2A] bg-[#111116]">
                    <th className="text-left px-4 py-3 text-[#9CA3AF] font-medium">Status</th>
                    <th className="text-left px-4 py-3 text-[#9CA3AF] font-medium">Title</th>
                    <th className="text-left px-4 py-3 text-[#9CA3AF] font-medium">Meaning</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E1E2A]/50">
                  {ERROR_CODES.map((err) => (
                    <tr key={err.code} className="hover:bg-[#1A1A22] transition-colors">
                      <td className="px-4 py-3">
                        <span
                          className={`font-mono text-xs font-bold px-2 py-0.5 rounded ${
                            err.code.startsWith("2")
                              ? "bg-emerald-500/10 text-emerald-400"
                              : err.code.startsWith("4")
                              ? "bg-[#EAB308]/10 text-[#EAB308]"
                              : "bg-[#F87171]/10 text-[#F87171]"
                          }`}
                        >
                          {err.code}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium text-white">{err.title}</td>
                      <td className="px-4 py-3 text-[#9CA3AF]">{err.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div>
              <p className="text-sm text-[#9CA3AF] mb-3">Error response format:</p>
              <CodeBlock
                lang="json"
                code={`{
  "detail": "API key does not have the 'analyze' scope"
}`}
              />
            </div>
          </section>

          {/* SDKs */}
          <section>
            <SectionHeader
              id="sdks"
              title="SDKs"
              subtitle="Official client libraries — install and start querying in seconds."
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
              {[
                {
                  lang: "Python",
                  pkg: "tukijuris",
                  color: "from-blue-500/10 to-blue-600/5",
                  border: "border-blue-500/20",
                  badge: "bg-emerald-500/15 text-emerald-400",
                  badgeLabel: "Disponible",
                  snippet: "pip install tukijuris",
                },
                {
                  lang: "JavaScript / TypeScript",
                  pkg: "@tukijuris/sdk",
                  color: "from-yellow-500/10 to-yellow-600/5",
                  border: "border-yellow-500/20",
                  badge: "bg-emerald-500/15 text-emerald-400",
                  badgeLabel: "Disponible",
                  snippet: "npm install @tukijuris/sdk",
                },
              ].map((sdk) => (
                <div
                  key={sdk.lang}
                  className={`p-5 rounded-xl bg-gradient-to-br ${sdk.color} border ${sdk.border}`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-medium text-white text-sm">{sdk.lang}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${sdk.badge}`}>
                      {sdk.badgeLabel}
                    </span>
                  </div>
                  <code className="text-xs font-mono text-[#9CA3AF] block mb-3">{sdk.pkg}</code>
                  <div className="rounded-lg bg-[#0A0A0F]/60 border border-[#2A2A35] px-3 py-2">
                    <code className="text-xs font-mono text-[#EAB308]">{sdk.snippet}</code>
                  </div>
                </div>
              ))}
            </div>

            {/* Python usage example */}
            <div className="mb-6">
              <p className="text-sm text-[#9CA3AF] mb-3 font-medium">Python — uso básico</p>
              <CodeBlock
                lang="python"
                code={`from tukijuris import TukiJuris

client = TukiJuris(api_key="ak_...")

# Consulta legal
result = client.query("¿Qué dice el Art. 1351 del Código Civil?")
print(result.answer)

# Búsqueda directa en normativa
results = client.search("despido arbitrario indemnizacion", area="laboral")
for r in results:
    print(f"[{r.document}] {r.content[:120]}")`}
              />
            </div>

            {/* JavaScript usage example */}
            <div className="mb-6">
              <p className="text-sm text-[#9CA3AF] mb-3 font-medium">JavaScript / TypeScript — uso básico</p>
              <CodeBlock
                lang="typescript"
                code={`import { TukiJuris } from "@tukijuris/sdk";

const client = new TukiJuris({ apiKey: "ak_..." });

// Consulta legal
const result = await client.query("¿Qué dice el Art. 1351 del Código Civil?");
console.log(result.answer);

// Búsqueda directa en normativa
const results = await client.search("despido arbitrario", { area: "laboral" });
results.forEach((r) => console.log(\`[\${r.document}]\`, r.content.slice(0, 120)));`}
              />
            </div>

            <div className="mt-8 p-5 rounded-xl bg-[#111116] border border-[#1E1E2A]">
              <p className="text-sm text-[#9CA3AF]">
                <strong className="text-white">Need help?</strong>{" "}
                Open an issue or contact us at{" "}
                  <a href="mailto:api@tukijuris.net.pe" className="text-[#EAB308] hover:text-[#EAB308]/80 transition-colors">
                    api@tukijuris.net.pe
                  </a>
                . For interactive exploration, use the{" "}
                <a href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer" className="text-[#EAB308] hover:text-[#EAB308]/80 transition-colors inline-flex items-center gap-1">
                  Swagger UI <ExternalLink className="w-3 h-3" />
                </a>.
              </p>
            </div>
          </section>

        </main>
        </div>
      </div>
    </AppLayout>
  );
}
