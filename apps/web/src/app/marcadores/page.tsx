"use client";

import { useEffect, useState } from "react";
import {
  Bookmark,
  Bot,
  BookOpen,
  Shield,
  Briefcase,
  Landmark,
  Gavel,
  Building2,
  Loader2,
  ScrollText,
  FileCheck,
  Globe,
  Lock,
  BadgeCheck,
  Search,
  Scale,
} from "lucide-react";
import { getToken } from "@/lib/auth";
import { AppLayout } from "@/components/AppLayout";
import { renderMarkdown } from "@/lib/markdown";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface BookmarkedMessage {
  id: string;
  role: string;
  content: string;
  agent_used: string | null;
  is_bookmarked: boolean;
  created_at: string;
  conversation_id: string;
  conversation_title: string | null;
  legal_area: string | null;
}

const AREA_META: Record<string, { label: string; icon: React.ElementType; color: string }> = {
  civil: { label: "Civil", icon: BookOpen, color: "text-blue-400" },
  penal: { label: "Penal", icon: Shield, color: "text-red-400" },
  laboral: { label: "Laboral", icon: Briefcase, color: "text-green-400" },
  tributario: { label: "Tributario", icon: Landmark, color: "text-yellow-400" },
  constitucional: { label: "Constitucional", icon: Gavel, color: "text-purple-400" },
  administrativo: { label: "Administrativo", icon: Building2, color: "text-orange-400" },
  corporativo: { label: "Corporativo", icon: ScrollText, color: "text-cyan-400" },
  registral: { label: "Registral", icon: FileCheck, color: "text-pink-400" },
  comercio_exterior: { label: "Comercio Ext.", icon: Globe, color: "text-teal-400" },
  compliance: { label: "Compliance", icon: Lock, color: "text-indigo-400" },
  competencia: { label: "Competencia/PI", icon: BadgeCheck, color: "text-amber-400" },
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-PE", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function truncate(text: string, max = 300): string {
  if (text.length <= max) return text;
  return text.slice(0, max) + "…";
}

const ITEMS_PER_PAGE = 10;

export default function MarcadoresPage() {
  const [bookmarks, setBookmarks] = useState<BookmarkedMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchFilter, setSearchFilter] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setError("Debes iniciar sesion para ver tus marcadores.");
      setIsLoading(false);
      return;
    }

    fetch(`${API_URL}/api/bookmarks/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Error al cargar marcadores");
        return res.json();
      })
      .then((data: BookmarkedMessage[]) => setBookmarks(data))
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoading(false));
  }, []);

  const handleRemove = async (id: string) => {
    const token = getToken();
    if (!token) return;

    setRemovingId(id);
    try {
      const res = await fetch(`${API_URL}/api/bookmarks/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setBookmarks((prev) => prev.filter((b) => b.id !== id));
      }
    } finally {
      setRemovingId(null);
    }
  };

  // Filter bookmarks by search term
  const filteredBookmarks = searchFilter
    ? bookmarks.filter((bm) =>
        bm.content.toLowerCase().includes(searchFilter.toLowerCase()) ||
        (bm.conversation_title &&
          bm.conversation_title.toLowerCase().includes(searchFilter.toLowerCase()))
      )
    : bookmarks;

  // Group filtered bookmarks by legal area
  const grouped = filteredBookmarks.reduce<Record<string, BookmarkedMessage[]>>(
    (acc, bm) => {
      const key = bm.legal_area || "general";
      if (!acc[key]) acc[key] = [];
      acc[key].push(bm);
      return acc;
    },
    {}
  );

  const groupKeys = Object.keys(grouped).sort();

  // Pagination over the flat list (all filtered bookmarks)
  const allFiltered = Object.values(grouped).flat();
  const totalPages = Math.ceil(allFiltered.length / ITEMS_PER_PAGE);
  const paginatedIds = new Set(
    allFiltered
      .slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
      .map((bm) => bm.id)
  );

  return (
    <AppLayout>
      <div className="min-h-full text-[#F5F5F5]">
        {/* Page title */}
        <div className="border-b border-[#1E1E2A] px-6 py-4 flex items-center gap-2">
          <Bookmark className="w-5 h-5 text-[#EAB308]" fill="currentColor" />
          <h1 className="font-semibold text-base">Marcadores</h1>
        </div>

        {/* Content */}
        <main className="max-w-4xl mx-auto px-6 py-8">
          {isLoading && (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-6 h-6 text-[#EAB308] animate-spin mr-2" />
              <span className="text-[#9CA3AF] text-sm">Cargando marcadores...</span>
            </div>
          )}

          {error && (
            <div className="bg-red-950/30 border border-red-800/50 rounded-xl p-6 text-center">
              <p className="text-red-400 text-sm">{error}</p>
              <a
                href="/auth/login"
                className="mt-3 inline-block text-[#EAB308] hover:text-[#D4A00A] text-sm underline"
              >
                Iniciar sesion
              </a>
            </div>
          )}

          {!isLoading && !error && bookmarks.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <img
                src="/brand/logo-full.png"
                className="w-24 mx-auto mb-4 opacity-40"
                alt="Agente Derecho"
              />
              <h2 className="text-lg font-semibold text-[#F5F5F5] mb-2">
                No hay marcadores guardados
              </h2>
              <p className="text-[#6B7280] text-sm max-w-sm">
                Guarda las respuestas mas utiles haciendo clic en el icono de marcador en cualquier mensaje del asistente.
              </p>
              <a
                href="/"
                className="mt-6 inline-flex items-center gap-2 bg-[#EAB308] hover:bg-[#D4A00A] text-black text-sm font-medium px-4 py-2 rounded-xl transition-colors"
              >
                <Scale className="w-4 h-4" />
                Ir al chat
              </a>
            </div>
          )}

          {!isLoading && !error && bookmarks.length > 0 && (
            <div className="space-y-6">
              {/* Header + search */}
              <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                <h1 className="text-lg font-bold flex-1">
                  Mis marcadores
                  <span className="ml-2 text-sm font-normal text-[#6B7280]">
                    ({bookmarks.length} {bookmarks.length === 1 ? "guardado" : "guardados"})
                  </span>
                </h1>
                <div className="relative w-full sm:w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6B7280]" />
                  <input
                    value={searchFilter}
                    onChange={(e) => {
                      setSearchFilter(e.target.value);
                      setCurrentPage(1);
                    }}
                    placeholder="Filtrar marcadores..."
                    className="w-full pl-9 pr-3 h-12 bg-[#111116] border border-[#2A2A35] rounded-xl text-sm text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308]/50 transition-colors"
                  />
                </div>
              </div>

              {filteredBookmarks.length === 0 && searchFilter && (
                <p className="text-sm text-[#6B7280] py-4">
                  No se encontraron marcadores para &ldquo;{searchFilter}&rdquo;
                </p>
              )}

              {groupKeys.map((areaKey) => {
                const meta = AREA_META[areaKey];
                const Icon = meta?.icon ?? BookOpen;
                // Only show items that fall within the current page slice
                const items = grouped[areaKey].filter((bm) => paginatedIds.has(bm.id));
                if (items.length === 0) return null;

                return (
                  <section key={areaKey}>
                    {/* Area header */}
                    <div className="flex items-center gap-2 mb-3">
                      <Icon className={`w-4 h-4 ${meta?.color ?? "text-[#9CA3AF]"}`} />
                      <h2 className="text-sm font-semibold uppercase tracking-wider text-[#9CA3AF]">
                        {meta?.label ?? areaKey}
                      </h2>
                      <span className="text-xs text-[#6B7280]">
                        ({grouped[areaKey].length})
                      </span>
                    </div>

                    {/* Bookmark cards */}
                    <div className="space-y-3">
                      {items.map((bm) => (
                        <article
                          key={bm.id}
                          className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-5 hover:border-[#2A2A35] transition-colors"
                        >
                          {/* Card header */}
                          <div className="flex items-start justify-between gap-3 mb-2">
                            <div className="flex items-center gap-2">
                              <div className="w-6 h-6 rounded-md bg-[#EAB308]/10 flex items-center justify-center shrink-0">
                                <Bot className="w-3.5 h-3.5 text-[#EAB308]" />
                              </div>
                              <div>
                                <p className="text-xs text-[#6B7280]">
                                  {bm.agent_used ?? "TukiJuris"}
                                </p>
                                {bm.conversation_title && (
                                  <p className="text-xs text-[#9CA3AF] line-clamp-1">
                                    {bm.conversation_title}
                                  </p>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              {bm.legal_area && (
                                <span className="bg-[#2C3E50]/30 text-[#9CA3AF] rounded-full text-xs px-2 py-0.5">
                                  {AREA_META[bm.legal_area]?.label ?? bm.legal_area}
                                </span>
                              )}
                              <span className="text-[10px] text-[#6B7280]">
                                {formatDate(bm.created_at)}
                              </span>
                              <button
                                onClick={() => handleRemove(bm.id)}
                                disabled={removingId === bm.id}
                                className="p-1 rounded text-[#6B7280] hover:text-[#F87171] hover:bg-[#1A1A22] transition-colors"
                                title="Quitar marcador"
                              >
                                {removingId === bm.id ? (
                                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                ) : (
                                  <Bookmark
                                    className="w-3.5 h-3.5"
                                    fill="currentColor"
                                  />
                                )}
                              </button>
                            </div>
                          </div>

                          {/* Content preview */}
                          <div
                            className="text-sm text-[#F5F5F5] leading-relaxed prose prose-invert max-w-none"
                            dangerouslySetInnerHTML={{ __html: renderMarkdown(truncate(bm.content)) }}
                          />

                          {/* Footer link */}
                          <div className="mt-3 pt-2 border-t border-[#1E1E2A]/50">
                            <a
                              href={`/?conversation=${bm.conversation_id}`}
                              className="text-xs text-[#EAB308] hover:text-[#D4A00A] transition-colors"
                            >
                              Ver conversacion completa
                            </a>
                          </div>
                        </article>
                      ))}
                    </div>
                  </section>
                );
              })}

              {/* Pagination controls */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-6">
                  <button
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1.5 text-sm rounded-xl bg-[#111116] border border-[#2A2A35] text-[#9CA3AF] hover:bg-[#1A1A22] disabled:opacity-30 transition-colors"
                  >
                    Anterior
                  </button>
                  <span className="text-sm text-[#6B7280]">
                    {currentPage} de {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1.5 text-sm rounded-xl bg-[#111116] border border-[#2A2A35] text-[#9CA3AF] hover:bg-[#1A1A22] disabled:opacity-30 transition-colors"
                  >
                    Siguiente
                  </button>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </AppLayout>
  );
}
