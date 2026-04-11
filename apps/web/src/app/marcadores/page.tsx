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
      <div className="flex min-h-full flex-col text-on-surface">
        {/* Header */}
        <div className="border-b border-[rgba(79,70,51,0.15)] px-4 sm:px-6 py-5 flex items-center gap-3 sticky top-0 z-10 bg-[#0e0e14]">
          <Bookmark className="w-4 h-4 text-primary" fill="currentColor" />
          <span className="text-primary text-xs uppercase tracking-[0.2em] font-bold">Guardados</span>
          <span className="text-on-surface/20 mx-1">·</span>
          <h1 className="font-['Newsreader'] text-xl font-bold text-on-surface">Marcadores</h1>
        </div>

        <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
          {isLoading && (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-6 h-6 text-primary animate-spin mr-2" />
              <span className="text-on-surface/40 text-sm">Cargando marcadores...</span>
            </div>
          )}

          {error && (
            <div className="bg-[#93000a]/20 border border-[#ffb4ab]/30 rounded-lg p-6 text-center">
              <p className="text-[#ffb4ab] text-sm">{error}</p>
              <a
                href="/auth/login"
                className="mt-3 inline-block text-primary hover:text-primary-container text-sm transition-colors"
              >
                Iniciar sesion
              </a>
            </div>
          )}

          {!isLoading && !error && bookmarks.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <img
                src="/brand/logo-full.png"
                className="w-24 mx-auto mb-4 opacity-20"
                alt="Agente Derecho"
              />
              <h2 className="font-['Newsreader'] text-2xl font-bold text-on-surface mb-2">
                No hay marcadores guardados
              </h2>
              <p className="text-on-surface/40 text-sm max-w-sm">
                Guarda las respuestas mas utiles haciendo clic en el icono de marcador en cualquier mensaje del asistente.
              </p>
              <a
                href="/"
                className="mt-6 inline-flex items-center gap-2 bg-gradient-to-br from-primary to-primary-container text-on-primary text-sm font-bold px-5 py-2.5 rounded-lg transition-opacity"
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
                <div className="flex-1">
                  <p className="text-primary text-xs uppercase tracking-[0.2em] font-bold mb-1">Guardados</p>
                  <h1 className="font-['Newsreader'] text-3xl font-bold text-on-surface">
                    Mis marcadores
                    <span className="ml-3 text-base font-normal text-on-surface/40">
                      {bookmarks.length} {bookmarks.length === 1 ? "guardado" : "guardados"}
                    </span>
                  </h1>
                </div>
                <div className="relative w-full sm:w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-on-surface/30" />
                  <input
                    value={searchFilter}
                    onChange={(e) => {
                      setSearchFilter(e.target.value);
                      setCurrentPage(1);
                    }}
                    placeholder="Filtrar marcadores..."
                    className="w-full pl-9 pr-3 h-11 bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg text-sm text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors"
                  />
                </div>
              </div>

              {filteredBookmarks.length === 0 && searchFilter && (
                <p className="text-sm text-on-surface/40 py-4">
                  No se encontraron marcadores para &ldquo;{searchFilter}&rdquo;
                </p>
              )}

              {groupKeys.map((areaKey) => {
                const meta = AREA_META[areaKey];
                const Icon = meta?.icon ?? BookOpen;
                const items = grouped[areaKey].filter((bm) => paginatedIds.has(bm.id));
                if (items.length === 0) return null;

                return (
                  <section key={areaKey}>
                    {/* Area header */}
                    <div className="flex items-center gap-2 mb-4">
                      <Icon className={`w-4 h-4 ${meta?.color ?? "text-on-surface/40"}`} />
                      <h2 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                        {meta?.label ?? areaKey}
                      </h2>
                      <span className="text-xs text-on-surface/30">
                        ({grouped[areaKey].length})
                      </span>
                    </div>

                    {/* Bookmark cards */}
                    <div className="space-y-0">
                      {items.map((bm, idx) => (
                        <article
                          key={bm.id}
                          className={`p-5 transition-colors ${
                            idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                          } hover:bg-surface-container`}
                        >
                          {/* Card header */}
                          <div className="flex items-start justify-between gap-3 mb-3">
                            <div className="flex items-center gap-2">
                              <div className="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                                <Bot className="w-3.5 h-3.5 text-primary" />
                              </div>
                              <div>
                                <p className="text-xs text-on-surface/30">
                                  {bm.agent_used ?? "TukiJuris"}
                                </p>
                                {bm.conversation_title && (
                                  <p className="text-xs text-on-surface/50 line-clamp-1">
                                    {bm.conversation_title}
                                  </p>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              {bm.legal_area && (
                                <span className="bg-secondary-container text-secondary text-[10px] uppercase tracking-widest rounded px-2 py-0.5">
                                  {AREA_META[bm.legal_area]?.label ?? bm.legal_area}
                                </span>
                              )}
                              <span className="text-[10px] text-on-surface/30">
                                {formatDate(bm.created_at)}
                              </span>
                              <button
                                onClick={() => handleRemove(bm.id)}
                                disabled={removingId === bm.id}
                                className="p-1 rounded text-on-surface/30 hover:text-[#ffb4ab] hover:bg-[#93000a]/20 transition-colors"
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
                            className="text-sm text-on-surface leading-relaxed prose prose-invert max-w-none"
                            dangerouslySetInnerHTML={{ __html: renderMarkdown(truncate(bm.content)) }}
                          />

                          {/* Footer link */}
                          <div className="mt-3 pt-2 border-t border-[rgba(79,70,51,0.08)]">
                            <a
                              href={`/?conversation=${bm.conversation_id}`}
                              className="text-xs text-primary hover:text-primary-container transition-colors"
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
                    className="px-4 py-2 text-sm rounded-lg bg-surface-container-low border border-[rgba(79,70,51,0.15)] text-on-surface/60 hover:bg-surface-container hover:text-on-surface disabled:opacity-30 transition-colors"
                  >
                    Anterior
                  </button>
                  <span className="text-sm text-on-surface/40">
                    {currentPage} de {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 text-sm rounded-lg bg-surface-container-low border border-[rgba(79,70,51,0.15)] text-on-surface/60 hover:bg-surface-container hover:text-on-surface disabled:opacity-30 transition-colors"
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
