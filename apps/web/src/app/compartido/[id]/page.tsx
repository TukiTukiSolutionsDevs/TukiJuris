import { Metadata } from "next";
import { Scale, Bot, User, ArrowRight, AlertTriangle } from "lucide-react";
import Image from "next/image";
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
      <div className="min-h-screen bg-[#0A0A0F] text-[#F5F5F5] flex flex-col items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          {/* Logo */}
          <div className="flex justify-center mb-8">
            <Image
              src="/brand/logo-full.png"
              alt="TukiJuris"
              width={160}
              height={40}
              className="h-9 w-auto"
            />
          </div>
          <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <AlertTriangle className="w-8 h-8 text-red-400" />
          </div>
          <h1 className="text-2xl font-bold mb-3">Consulta no encontrada</h1>
          <p className="text-[#9CA3AF] mb-8">
            Este enlace no existe o ya no esta disponible.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 bg-[#EAB308] hover:bg-[#EAB308]/90 text-[#0A0A0F] px-6 py-3 rounded-xl transition-colors font-medium"
          >
            <Scale className="w-4 h-4" />
            Ir a TukiJuris
          </Link>
        </div>
      </div>
    );
  }

  const areaLabel = conv.legal_area ? AREA_LABELS[conv.legal_area] ?? conv.legal_area : null;

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-[#F5F5F5] flex flex-col">
      {/* Header */}
      <header className="border-b border-[#1E1E2A] bg-[#111116]/80 sticky top-0 z-10 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <Image
              src="/brand/logo-full.png"
              alt="TukiJuris"
              width={120}
              height={32}
              className="h-7 w-auto shrink-0"
            />
            <span className="text-[#2A2A35] text-lg select-none shrink-0">|</span>
            <p className="text-sm font-semibold truncate text-[#F5F5F5]">
              {conv.title ?? "Consulta legal"}
            </p>
          </div>
          {areaLabel && (
            <span className="shrink-0 text-xs px-2.5 py-1 rounded-full bg-[#EAB308]/10 text-[#EAB308] border border-[#EAB308]/20">
              {areaLabel}
            </span>
          )}
        </div>
      </header>

      {/* Read-only notice */}
      <div className="bg-[#EAB308]/5 border-b border-[#EAB308]/10">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-2 flex items-center gap-2">
          <span className="text-xs text-[#EAB308]/80">
            Vista de solo lectura — consulta compartida desde TukiJuris
          </span>
        </div>
      </div>

      {/* Messages */}
      <main className="flex-1 max-w-3xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {conv.messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
          >
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-lg bg-[#EAB308]/10 flex items-center justify-center shrink-0 mt-1">
                <Bot className="w-4 h-4 text-[#EAB308]" />
              </div>
            )}
            <div
              className={`max-w-[85%] sm:max-w-[80%] rounded-xl ${
                msg.role === "user"
                  ? "bg-[#1A1A22] text-[#F5F5F5] rounded-tr-sm px-4 py-3"
                  : "bg-[#111116] rounded-tl-sm px-4 py-3"
              }`}
            >
              {msg.role === "assistant" ? (
                <div
                  className="text-sm text-[#F5F5F5] leading-relaxed prose prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                />
              ) : (
                <p className="text-sm whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </p>
              )}
              {msg.role === "assistant" && msg.agent_used && (
                <p className="mt-2 pt-2 border-t border-[#2A2A35]/50 text-xs text-[#6B7280] flex items-center gap-1.5">
                  <span className="inline-flex items-center gap-1.5 bg-[#2C3E50]/30 text-[#9CA3AF] rounded-full px-2 py-0.5">
                    <Bot className="w-3 h-3" />
                    {msg.agent_used}
                  </span>
                </p>
              )}
            </div>
            {msg.role === "user" && (
              <div className="w-8 h-8 rounded-lg bg-[#1A1A22] flex items-center justify-center shrink-0 mt-1">
                <User className="w-4 h-4 text-[#9CA3AF]" />
              </div>
            )}
          </div>
        ))}
      </main>

      {/* CTA */}
      <footer className="border-t border-[#1E1E2A] bg-[#111116]/80">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <p className="font-semibold text-sm text-[#F5F5F5]">Haz tus propias consultas legales</p>
            <p className="text-xs text-[#9CA3AF] mt-0.5">
              TukiJuris — Plataforma juridica especializada en derecho peruano
            </p>
          </div>
          <Link
            href="/"
            className="shrink-0 inline-flex items-center gap-2 bg-[#EAB308] hover:bg-[#EAB308]/90 text-[#0A0A0F] px-5 py-2.5 rounded-xl transition-colors text-sm font-medium font-semibold"
          >
            Probar TukiJuris
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </footer>
    </div>
  );
}
