"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Database,
  ExternalLink,
  Filter,
  Loader2,
  Scale,
  Search as SearchIcon,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { LEGAL_AREAS } from "@/app/chat/constants";
import { AppLayout } from "@/components/AppLayout";
import { PublicLayout } from "@/components/public/PublicLayout";
import { InternalPageHeader } from "@/components/shell/InternalPageHeader";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";
import { useAuth } from "@/lib/auth/AuthContext";

// ---------------------------------------------------------------------------
// Types — mirror the SearchResult schema from documents.py
// ---------------------------------------------------------------------------

interface SearchResult {
  article_number: string | null;
  content: string;
  legal_area: string;
  section_path: string | null;
  document_title: string;
  document_number: string | null;
  score: number;
}

interface KBStats {
  // Matches `/api/documents/stats` response shape. Keep in sync with
  // apps/api/app/api/routes/documents.py:KBStats.
  total_documents: number;
  total_chunks: number;
  chunks_by_area: Record<string, number>;
  // Other fields (embeddings counts, hierarchy breakdown, etc.) ignored here.
}

// ---------------------------------------------------------------------------
// Public corpus browser — no AI, no auth. Free feature.
//
// Lets anyone search and filter the indexed Peruvian legal corpus
// (~2000 chunks across 29 áreas) using full-text search (BM25 on Postgres
// FTS). Backend endpoint `/api/documents/search` already public.
// ---------------------------------------------------------------------------

function BuscarContent() {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [selectedArea, setSelectedArea] = useState<string | "">("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [stats, setStats] = useState<KBStats | null>(null);

  // Load corpus stats once
  useEffect(() => {
    fetch(`/api/documents/stats`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => data && setStats(data))
      .catch(() => {});
  }, []);

  // Debounce query input
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query.trim()), 350);
    return () => clearTimeout(t);
  }, [query]);

  const runSearch = useCallback(async () => {
    if (debouncedQuery.length < 2) {
      setResults([]);
      setSearched(false);
      return;
    }
    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: debouncedQuery,
        limit: "20",
      });
      if (selectedArea) params.set("area", selectedArea);
      const res = await fetch(`/api/documents/search?${params}`);
      if (!res.ok) {
        toast.error("No se pudo realizar la búsqueda.");
        return;
      }
      const data = (await res.json()) as SearchResult[];
      setResults(data);
      setSearched(true);
    } catch (err) {
      console.error(err);
      toast.error("Error de conexión.");
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, selectedArea]);

  useEffect(() => {
    if (debouncedQuery.length >= 2) {
      runSearch();
    } else {
      setResults([]);
      setSearched(false);
    }
  }, [debouncedQuery, selectedArea, runSearch]);

  const topAreas = useMemo(() => {
    if (!stats?.chunks_by_area) return [];
    return Object.entries(stats.chunks_by_area)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 12);
  }, [stats]);

  return (
    <div className="max-w-5xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12">
      {/* Hero */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-[11px] uppercase tracking-wider mb-4">
          <Database className="w-3.5 h-3.5" />
          Buscador público · sin IA
        </div>
        <h1 className="font-['Newsreader'] text-4xl sm:text-5xl font-bold text-on-surface mb-2">
          Corpus jurídico del Perú
        </h1>
        <p className="text-sm sm:text-base text-on-surface/60 max-w-2xl mx-auto">
          Buscá leyes, decretos, jurisprudencia y normativa peruana indexada.
          {stats && (
            <>
              {" "}Hoy hay <strong className="text-on-surface">{stats.total_documents.toLocaleString()}</strong>
              {" "}documentos · <strong className="text-on-surface">{stats.total_chunks.toLocaleString()}</strong>
              {" "}fragmentos en 29 áreas.
            </>
          )}
        </p>
      </div>

      {/* Search box */}
      <div className="relative mb-4">
        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-on-surface/40" />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ej. despido nulo, prescripción tributaria, prisión preventiva, divorcio convencional…"
          className="w-full pl-12 pr-12 py-4 bg-surface border border-outline-variant hover:border-primary/40 focus:border-primary/60 rounded-lg text-on-surface placeholder-on-surface/30 focus:outline-none text-base transition-colors"
          autoFocus
        />
        {query && (
          <button
            onClick={() => setQuery("")}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-on-surface/40 hover:text-on-surface/70"
            aria-label="Limpiar"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Area filter chips */}
      <div className="flex flex-wrap items-center gap-2 mb-6">
        <span className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-on-surface/40">
          <Filter className="w-3 h-3" />
          Filtrar por área
        </span>
        <button
          onClick={() => setSelectedArea("")}
          className={`px-3 py-1 rounded-full text-[11px] border transition-colors ${
            selectedArea === ""
              ? "bg-primary/10 border-primary/40 text-primary"
              : "bg-surface border-outline-variant text-on-surface/60 hover:border-primary/30"
          }`}
        >
          Todas
        </button>
        {LEGAL_AREAS.map((a) => {
          const count = stats?.chunks_by_area?.[a.id] ?? null;
          const active = selectedArea === a.id;
          return (
            <button
              key={a.id}
              onClick={() => setSelectedArea(active ? "" : a.id)}
              className={`px-3 py-1 rounded-full text-[11px] border transition-colors ${
                active
                  ? "bg-primary/10 border-primary/40 text-primary"
                  : "bg-surface border-outline-variant text-on-surface/60 hover:border-primary/30"
              }`}
              title={a.description}
            >
              {a.name}
              {count != null && (
                <span className="ml-1 text-on-surface/30">· {count}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Results */}
      {loading && (
        <div className="flex items-center justify-center py-12 text-on-surface/50 text-sm">
          <Loader2 className="w-4 h-4 animate-spin mr-2" />
          Buscando…
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="w-8 h-8 text-on-surface/30 mx-auto mb-3" />
          <p className="text-sm text-on-surface/50">
            Sin resultados para "{debouncedQuery}"{selectedArea && " en esta área"}.
          </p>
          <p className="text-xs text-on-surface/30 mt-1">
            Probá con otros términos o quitá el filtro de área.
          </p>
        </div>
      )}

      {!loading && !searched && (
        <div className="bg-surface-container-low border border-outline-variant rounded-lg p-6">
          <p className="text-[10px] uppercase tracking-wider text-on-surface/40 mb-3">
            Áreas con más contenido
          </p>
          <div className="flex flex-wrap gap-2">
            {topAreas.map(([area, count]) => {
              const meta = LEGAL_AREAS.find((a) => a.id === area);
              return (
                <button
                  key={area}
                  onClick={() => setSelectedArea(area)}
                  className="flex items-center gap-2 px-3 py-2 rounded-md bg-surface border border-outline-variant hover:border-primary/30 transition-colors"
                >
                  {meta?.icon && <meta.icon className={`w-3.5 h-3.5 ${meta.color}`} />}
                  <span className="text-xs text-on-surface">
                    {meta?.label ?? area}
                  </span>
                  <span className="text-[10px] text-on-surface/40">{count}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs text-on-surface/50 px-1">
            {results.length} resultado{results.length === 1 ? "" : "s"} para "
            <strong className="text-on-surface">{debouncedQuery}</strong>"
            {selectedArea && (
              <> en <strong className="text-on-surface">{LEGAL_AREAS.find((a) => a.id === selectedArea)?.label}</strong></>
            )}
          </p>
          {results.map((r, i) => {
            const areaMeta = LEGAL_AREAS.find((a) => a.id === r.legal_area);
            return (
              <article
                key={`${r.document_number}-${i}`}
                className="bg-surface-container-low border border-outline-variant rounded-lg p-4 hover:border-primary/30 transition-colors"
              >
                <header className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-on-surface truncate">
                      {r.document_title}
                    </h3>
                    {r.section_path && (
                      <p className="text-[11px] text-on-surface/40 truncate">
                        {r.section_path}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {areaMeta && (
                      <span className={`flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-surface border border-outline-variant ${areaMeta.color}`}>
                        {areaMeta.name}
                      </span>
                    )}
                    {r.article_number && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface border border-outline-variant text-on-surface/60">
                        Art. {r.article_number}
                      </span>
                    )}
                  </div>
                </header>
                <p className="text-sm text-on-surface/70 leading-relaxed whitespace-pre-line line-clamp-6">
                  {r.content}
                </p>
                {r.document_number && (
                  <footer className="mt-3 pt-3 border-t border-outline-variant/60 flex items-center justify-between text-[10px] text-on-surface/40">
                    <span>{r.document_number}</span>
                    <span className="font-mono">score: {r.score.toFixed(2)}</span>
                  </footer>
                )}
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function BuscarPage() {
  const { user, isLoading } = useAuth();
  // Dynamically pick the layout. Authenticated users see the workspace shell
  // (sidebar + topbar) so /buscar feels like another feature of the app.
  // Anonymous visitors see the public marketing shell (header + footer).
  // Either path works because /api/documents/search is public.
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-on-surface">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
      </div>
    );
  }
  const Layout = user ? AppLayout : PublicLayout;
  return (
    <Layout>
      <div className="flex min-h-full flex-col">
        {user && (
          <InternalPageHeader
            icon={<SearchIcon className="h-5 w-5" strokeWidth={1.7} />}
            eyebrow="Conocimiento"
            title="Buscar corpus"
            description="Explorá los fragmentos del corpus público — sin IA, sin gating. Filtrá por área del derecho."
            utilitySlot={<div className="hidden md:flex"><ShellUtilityActions /></div>}
          />
        )}
        <BuscarContent />
      </div>
    </Layout>
  );
}
