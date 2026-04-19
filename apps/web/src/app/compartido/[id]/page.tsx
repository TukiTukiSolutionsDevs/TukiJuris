import { Metadata } from "next";
import { Scale, Bot, User, ArrowRight, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { renderMarkdown } from "@/lib/markdown";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "https://tukijuris.net.pe";

interface SharedMessage {
  role: "user" | "assistant";
  content: string;
  agent_used: string | null;
  created_at: string;
}

interface SharedConversation {
  title: string | null;
  legal_area: string | null;
  messages: SharedMessage[];
}

const AREA_LABELS: Record<string, string> = {
  civil: "Derecho Civil",
  penal: "Derecho Penal",
  laboral: "Derecho Laboral",
  tributario: "Derecho Tributario",
  constitucional: "Derecho Constitucional",
  administrativo: "Derecho Administrativo",
  corporativo: "Derecho Corporativo",
  registral: "Derecho Registral",
  competencia: "Competencia y PI",
  compliance: "Compliance",
  comercio_exterior: "Comercio Exterior",
};

async function fetchSharedConversation(
  shareId: string
): Promise<SharedConversation | null> {
  try {
    const res = await fetch(`${API_URL}/api/shared/${shareId}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const conv = await fetchSharedConversation(id);
  const title = conv?.title
    ? `${conv.title} — TukiJuris`
    : "Consulta legal compartida — TukiJuris";
  const description =
    conv?.messages?.[0]?.content?.slice(0, 160) ??
    "Consulta legal especializada en derecho peruano, generada con TukiJuris.";

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      url: `${APP_URL}/compartido/${id}`,
      siteName: "TukiJuris",
      type: "article",
    },
    twitter: {
      card: "summary",
      title,
      description,
    },
  };
}

export default async function CompartidoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const conv = await fetchSharedConversation(id);

  if (!conv) {
    return (
      <div className="min-h-screen bg-background text-on-surface flex flex-col items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          {/* Logo wordmark */}
          <div className="flex justify-center mb-8">
            <span className="font-['Newsreader'] text-2xl font-bold text-primary-container">
              TukiJuris
            </span>
          </div>
          <div className="w-14 h-14 bg-red-500/10 border border-[rgba(79,70,51,0.15)] rounded-lg flex items-center justify-center mx-auto mb-6">
            <AlertTriangle className="w-7 h-7 text-red-400" />
          </div>
          <h1 className="font-['Newsreader'] text-3xl text-on-surface mb-3">
            Consulta no encontrada
          </h1>
          <p className="text-on-surface-variant text-sm mb-8">
            Este enlace no existe o ya no está disponible.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold px-6 py-3 rounded-lg transition-opacity hover:opacity-90"
          >
            <Scale className="w-4 h-4" />
            Ir a TukiJuris
          </Link>
        </div>
      </div>
    );
  }

  const areaLabel = conv.legal_area
    ? AREA_LABELS[conv.legal_area] ?? conv.legal_area
    : null;

  return (
    <div className="min-h-screen bg-background text-on-surface flex flex-col">
      {/* Top bar — public, no sidebar */}
      <header className="border-b border-[rgba(79,70,51,0.15)] bg-[#111116]/90 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
          {/* Logo */}
          <div className="flex items-center gap-3 min-w-0">
            <span className="font-['Newsreader'] text-2xl font-bold text-primary-container shrink-0">
              TukiJuris
            </span>
            {conv.title && (
              <>
                <span className="text-[rgba(79,70,51,0.40)] text-lg select-none shrink-0">
                  |
                </span>
                <p className="text-sm text-on-surface truncate">{conv.title}</p>
              </>
            )}
          </div>
          <Link
            href="/"
            className="shrink-0 text-xs text-primary-container hover:text-primary transition-colors font-medium"
          >
            Iniciar sesión
          </Link>
        </div>
      </header>

      {/* Area badge + read-only notice */}
      <div className="bg-primary-container/5 border-b border-[rgba(79,70,51,0.15)]">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-2 flex items-center justify-between gap-3">
          <span className="text-xs text-primary-container/70">
            Vista de solo lectura · consulta compartida
          </span>
          {areaLabel && (
            <span className="shrink-0 bg-secondary-container text-secondary text-[10px] uppercase tracking-widest rounded px-2 py-0.5">
              {areaLabel}
            </span>
          )}
        </div>
      </div>

      {/* Messages */}
      <main className="flex-1 max-w-3xl w-full mx-auto px-4 sm:px-6 py-6 space-y-5">
        {conv.messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
          >
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-lg bg-primary-container/10 flex items-center justify-center shrink-0 mt-1">
                <Bot className="w-4 h-4 text-primary-container" />
              </div>
            )}

            <div
              className={`max-w-[85%] sm:max-w-[80%] rounded-lg ${
                msg.role === "user"
                  ? "bg-surface-container-low text-on-surface rounded-tr-sm px-4 py-3"
                  : "bg-surface rounded-tl-sm px-4 py-3"
              }`}
            >
              {msg.role === "assistant" ? (
                <div
                  className="text-sm text-on-surface leading-relaxed prose prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                />
              ) : (
                <p className="text-sm whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </p>
              )}

              {msg.role === "assistant" && msg.agent_used && (
                <p className="mt-2 pt-2 border-t border-[rgba(79,70,51,0.15)] text-xs text-[#6B7280] flex items-center gap-1.5">
                  <span className="inline-flex items-center gap-1.5 bg-secondary-container text-secondary rounded px-2 py-0.5 text-[10px] uppercase tracking-widest">
                    <Bot className="w-3 h-3" />
                    {msg.agent_used}
                  </span>
                </p>
              )}
            </div>

            {msg.role === "user" && (
              <div className="w-8 h-8 rounded-lg bg-surface-container-low flex items-center justify-center shrink-0 mt-1">
                <User className="w-4 h-4 text-[#6B7280]" />
              </div>
            )}
          </div>
        ))}
      </main>

      {/* Footer — Generado por TukiJuris + CTA */}
      <footer className="border-t border-[rgba(79,70,51,0.15)] bg-[#111116]/80">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-on-surface">
              Haz tus propias consultas legales
            </p>
            <p className="text-xs text-[#6B7280] mt-0.5">
              Generado por TukiJuris · Plataforma jurídica especializada en derecho peruano
            </p>
          </div>
          <Link
            href="/"
            className="shrink-0 inline-flex items-center gap-2 bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold px-5 py-2.5 rounded-lg transition-opacity hover:opacity-90 text-sm"
          >
            Probar TukiJuris
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </footer>
    </div>
  );
}
