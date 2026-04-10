"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { getToken, authHeaders as getAuthHeaders } from "@/lib/auth";
import { AppLayout } from "@/components/AppLayout";
import {
  Search,
  Filter,
  X,
  ChevronDown,
  Bookmark,
  BookmarkCheck,
  Clock,
  SlidersHorizontal,
  FileText,
  Calendar,
  BookOpen,
  Shield,
  Briefcase,
  Landmark,
  Gavel,
  Building2,
  ScrollText,
  FileCheck,
  Globe,
  Lock,
  BadgeCheck,
  RotateCcw,
  Scale,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const LEGAL_AREAS = [
  { id: "civil", name: "Civil", icon: BookOpen, color: "text-blue-400" },
  { id: "penal", name: "Penal", icon: Shield, color: "text-red-400" },
  { id: "laboral", name: "Laboral", icon: Briefcase, color: "text-green-400" },
  { id: "tributario", name: "Tributario", icon: Landmark, color: "text-yellow-400" },
  { id: "constitucional", name: "Constitucional", icon: Gavel, color: "text-purple-400" },
  { id: "administrativo", name: "Administrativo", icon: Building2, color: "text-orange-400" },
  { id: "corporativo", name: "Corporativo", icon: ScrollText, color: "text-cyan-400" },
  { id: "registral", name: "Registral", icon: FileCheck, color: "text-pink-400" },
  { id: "comercio_exterior", name: "Comercio Ext.", icon: Globe, color: "text-teal-400" },
  { id: "compliance", name: "Compliance", icon: Lock, color: "text-indigo-400" },
  { id: "competencia", name: "Competencia/PI", icon: BadgeCheck, color: "text-amber-400" },
];

const AREA_MAP = Object.fromEntries(LEGAL_AREAS.map((a) => [a.id, a]));

const DOCUMENT_TYPES = [
  { id: "", name: "Todos los tipos" },
  { id: "ley", name: "Ley" },
  { id: "decreto_supremo", name: "Decreto Supremo" },
  { id: "decreto_legislativo", name: "Decreto Legislativo" },
  { id: "resolucion", name: "Resolución" },
  { id: "resolucion_ministerial", name: "Resolución Ministerial" },
  { id: "sentencia", name: "Sentencia" },
  { id: "casacion", name: "Casación" },
  { id: "constitucion", name: "Constitución" },
  { id: "reglamento", name: "Reglamento" },
];

const HIERARCHY_OPTIONS = [
  { id: "", name: "Todas las jerarquías" },
  { id: "constitucional", name: "Constitucional" },
  { id: "legal", name: "Legal" },
  { id: "reglamentario", name: "Reglamentario" },
];

const SORT_OPTIONS = [
  { id: "relevance", name: "Relevancia" },
  { id: "date_desc", name: "Fecha (más reciente)" },
  { id: "date_asc", name: "Fecha (más antigua)" },
];

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface SearchResult {
  id: string;
  document_id: string;
  title: string;
  document_type: string;
  document_number: string | null;
  legal_area: string;
  hierarchy: string | null;
  source: string;
  publication_date: string | null;
  snippet: string;
  score: number;
}

interface SearchFilters {
  areas: string[];
  document_type: string;
  date_from: string;
  date_to: string;
  hierarchy: string;
}

interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: Record<string, unknown> | null;
  created_at: string;
}

interface HistoryItem {
  id: string;
  query: string;
  filters: Record<string, unknown> | null;
  results_count: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function authHeaders(): HeadersInit {
  return { "Content-Type": "application/json", ...getAuthHeaders() };
}

function highlightTerms(text: string, query: string): string {
  if (!query.trim()) return text;
  const terms = query
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  if (!terms.length) return text;
  const regex = new RegExp(`(${terms.join("|")})`, "gi");
  return text.replace(regex, "__MARK__$1__/MARK__");
}

function HighlightedText({ text, query }: { text: string; query: string }) {
  const highlighted = highlightTerms(text, query);
  const parts = highlighted.split(/__MARK__|__\/MARK__/);
  return (
    <span>
      {parts.map((part, i) => {
        const isHighlighted = i % 2 === 1;
        return isHighlighted ? (
          <mark key={i} className="bg-primary/20 text-primary rounded px-0.5 not-italic font-semibold">
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        );
      })}
    </span>
  );
}

// Skeleton card
function SkeletonCard() {
  return (
    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-5 animate-pulse">
      <div className="flex justify-between gap-4 mb-3">
        <div className="flex-1">
          <div className="h-4 bg-[#35343a] rounded w-3/4 mb-2" />
          <div className="h-3 bg-surface rounded w-1/3" />
        </div>
        <div className="h-5 bg-[#35343a] rounded w-20 shrink-0" />
      </div>
      <div className="space-y-1.5">
        <div className="h-3 bg-surface rounded w-full" />
        <div className="h-3 bg-surface rounded w-5/6" />
        <div className="h-3 bg-surface rounded w-4/6" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function BuscarPageWrapper() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" /></div>}>
      <BuscarPage />
    </Suspense>
  );
}

function BuscarPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // --- State ---
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [filters, setFilters] = useState<SearchFilters>({
    areas: searchParams.getAll("area"),
    document_type: searchParams.get("tipo") || "",
    date_from: searchParams.get("desde") || "",
    date_to: searchParams.get("hasta") || "",
    hierarchy: searchParams.get("jerarquia") || "",
  });
  const [sort, setSort] = useState(searchParams.get("orden") || "relevance");
  const [page, setPage] = useState(Number(searchParams.get("pagina")) || 1);

  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  // All documents for browse mode (shown when no search query)
  const [allDocs, setAllDocs] = useState<Array<{id: string; title: string; document_type: string; document_number: string | null; legal_area: string; hierarchy: string | null; source: string}>>([]);
  const [docsLoading, setDocsLoading] = useState(true);

  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const suggestTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const [showFilters, setShowFilters] = useState(false);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [saving, setSaving] = useState(false);

  const searchInputRef = useRef<HTMLInputElement>(null);

  // ---------------------------------------------------------------------------
  // Auth + sidebar data
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const token = getToken();
    setIsLoggedIn(!!token);
    if (token) {
      fetchSavedSearches();
      fetchHistory();
    }
    // Load all documents for browse mode
    fetch(`${API_URL}/api/documents/`)
      .then((r) => (r.ok ? r.json() : []))
      .then((docs) => setAllDocs(docs))
      .catch(() => {})
      .finally(() => setDocsLoading(false));
  }, []);

  const fetchSavedSearches = async () => {
    try {
      const res = await fetch(`${API_URL}/api/search/saved`, { headers: authHeaders() });
      if (res.ok) setSavedSearches(await res.json());
    } catch {
      // non-blocking
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/api/search/history`, { headers: authHeaders() });
      if (res.ok) setHistory(await res.json());
    } catch {
      // non-blocking
    }
  };

  // ---------------------------------------------------------------------------
  // Run search on mount if URL has params
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (searchParams.get("q")) {
      runSearch(
        searchParams.get("q") || "",
        {
          areas: searchParams.getAll("area"),
          document_type: searchParams.get("tipo") || "",
          date_from: searchParams.get("desde") || "",
          date_to: searchParams.get("hasta") || "",
          hierarchy: searchParams.get("jerarquia") || "",
        },
        searchParams.get("orden") || "relevance",
        Number(searchParams.get("pagina")) || 1,
      );
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Core search
  // ---------------------------------------------------------------------------

  const runSearch = useCallback(
    async (q: string, f: SearchFilters, s: string, p: number) => {
      if (!q.trim()) return;
      setLoading(true);
      setSearched(true);

      const params = new URLSearchParams();
      params.set("q", q);
      if (f.areas.length) f.areas.forEach((a) => params.append("area", a));
      if (f.document_type) params.set("tipo", f.document_type);
      if (f.date_from) params.set("desde", f.date_from);
      if (f.date_to) params.set("hasta", f.date_to);
      if (f.hierarchy) params.set("jerarquia", f.hierarchy);
      if (s !== "relevance") params.set("orden", s);
      if (p > 1) params.set("pagina", String(p));
      router.replace(`/buscar?${params.toString()}`, { scroll: false });

      try {
        const body = {
          query: q,
          filters: {
            areas: f.areas.length ? f.areas : undefined,
            document_types: f.document_type ? [f.document_type] : undefined,
            date_from: f.date_from || undefined,
            date_to: f.date_to || undefined,
            hierarchy: f.hierarchy || undefined,
          },
          sort: s,
          page: p,
          per_page: 20,
        };

        const res = await fetch(`${API_URL}/api/search/advanced`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify(body),
        });

        if (!res.ok) {
          setResults([]);
          setTotal(0);
          setTotalPages(0);
          return;
        }

        const data = await res.json();
        setResults(data.results);
        setTotal(data.total);
        setTotalPages(data.total_pages);
      } catch {
        setResults([]);
        setTotal(0);
        setTotalPages(0);
      } finally {
        setLoading(false);
        if (isLoggedIn) fetchHistory();
      }
    },
    [router, isLoggedIn],
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setShowSuggestions(false);
    runSearch(query, filters, sort, 1);
  };

  // ---------------------------------------------------------------------------
  // Auto-suggest (debounced 300ms)
  // ---------------------------------------------------------------------------

  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 2) {
      setSuggestions([]);
      return;
    }
    try {
      const res = await fetch(
        `${API_URL}/api/search/suggestions?q=${encodeURIComponent(q)}&limit=6`,
        { headers: authHeaders() },
      );
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.suggestions || []);
      }
    } catch {
      setSuggestions([]);
    }
  }, []);

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    setShowSuggestions(true);
    if (suggestTimeout.current) clearTimeout(suggestTimeout.current);
    suggestTimeout.current = setTimeout(() => fetchSuggestions(val), 300);
  };

  const pickSuggestion = (s: string) => {
    setQuery(s);
    setShowSuggestions(false);
    setPage(1);
    runSearch(s, filters, sort, 1);
  };

  // ---------------------------------------------------------------------------
  // Filters
  // ---------------------------------------------------------------------------

  const toggleArea = (area: string) => {
    setFilters((prev) => ({
      ...prev,
      areas: prev.areas.includes(area)
        ? prev.areas.filter((a) => a !== area)
        : [...prev.areas, area],
    }));
  };

  const clearFilters = () => {
    setFilters({ areas: [], document_type: "", date_from: "", date_to: "", hierarchy: "" });
  };

  const hasActiveFilters =
    filters.areas.length > 0 ||
    !!filters.document_type ||
    !!filters.date_from ||
    !!filters.date_to ||
    !!filters.hierarchy;

  // ---------------------------------------------------------------------------
  // Sort / Pagination
  // ---------------------------------------------------------------------------

  const handleSortChange = (newSort: string) => {
    setSort(newSort);
    setPage(1);
    runSearch(query, filters, newSort, 1);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    runSearch(query, filters, sort, newPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // ---------------------------------------------------------------------------
  // Saved searches
  // ---------------------------------------------------------------------------

  const handleSaveSearch = async () => {
    if (!saveName.trim() || !query.trim()) return;
    setSaving(true);
    try {
      const body = {
        name: saveName.trim(),
        query,
        filters: hasActiveFilters
          ? {
              areas: filters.areas.length ? filters.areas : undefined,
              document_types: filters.document_type ? [filters.document_type] : undefined,
              date_from: filters.date_from || undefined,
              date_to: filters.date_to || undefined,
              hierarchy: filters.hierarchy || undefined,
            }
          : undefined,
      };
      const res = await fetch(`${API_URL}/api/search/saved`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(body),
      });
      if (res.ok) {
        setSaveModalOpen(false);
        setSaveName("");
        fetchSavedSearches();
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteSaved = async (id: string) => {
    await fetch(`${API_URL}/api/search/saved/${id}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    setSavedSearches((prev) => prev.filter((s) => s.id !== id));
  };

  const applySaved = (saved: SavedSearch) => {
    const f = saved.filters as Record<string, unknown> | null;
    const newFilters: SearchFilters = {
      areas: Array.isArray(f?.areas) ? (f.areas as string[]) : [],
      document_type: Array.isArray(f?.document_types) ? ((f.document_types as string[])[0] ?? "") : "",
      date_from: typeof f?.date_from === "string" ? f.date_from : "",
      date_to: typeof f?.date_to === "string" ? f.date_to : "",
      hierarchy: typeof f?.hierarchy === "string" ? f.hierarchy : "",
    };
    setQuery(saved.query);
    setFilters(newFilters);
    setPage(1);
    runSearch(saved.query, newFilters, sort, 1);
  };

  const applyHistory = (item: HistoryItem) => {
    const f = item.filters as Record<string, unknown> | null;
    const newFilters: SearchFilters = {
      areas: Array.isArray(f?.areas) ? (f.areas as string[]) : [],
      document_type: Array.isArray(f?.document_types) ? ((f.document_types as string[])[0] ?? "") : "",
      date_from: typeof f?.date_from === "string" ? f.date_from : "",
      date_to: typeof f?.date_to === "string" ? f.date_to : "",
      hierarchy: typeof f?.hierarchy === "string" ? f.hierarchy : "",
    };
    setQuery(item.query);
    setFilters(newFilters);
    setPage(1);
    runSearch(item.query, newFilters, sort, 1);
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <AppLayout>
      <div className="min-h-full text-on-surface">
        {/* Page header */}
        <div className="border-b border-[rgba(79,70,51,0.15)] px-4 sm:px-6 py-5 flex items-center justify-between sticky top-0 bg-[#0e0e14] z-30">
          <div className="flex items-center gap-3">
            <Search className="w-4 h-4 text-primary" />
            <span className="text-primary text-xs uppercase tracking-[0.2em] font-bold">Normativa</span>
            <span className="text-on-surface/20 mx-1">·</span>
            <h1 className="font-['Newsreader'] text-xl font-bold text-on-surface">Buscador Avanzado</h1>
          </div>
          {/* Mobile: toggle filters button */}
          <button
            onClick={() => setShowFilters((v) => !v)}
            className="sm:hidden flex items-center gap-1.5 text-sm text-on-surface/60 hover:text-on-surface transition-colors bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg px-3 py-1.5"
          >
            <SlidersHorizontal className="w-4 h-4" />
            Filtros
            {hasActiveFilters && (
              <span className="w-1.5 h-1.5 rounded-full bg-primary ml-0.5" />
            )}
          </button>
        </div>

        <div className="max-w-screen-xl mx-auto px-4 sm:px-6 py-6">
          {/* Search bar */}
          <div className="relative mb-5">
            <form onSubmit={handleSubmit}>
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-on-surface/30 pointer-events-none" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={query}
                  onChange={handleQueryChange}
                  onFocus={() => suggestions.length && setShowSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                  placeholder="Buscar en la normativa peruana... (ej: despido arbitrario, alimentos, IGV)"
                  className="w-full bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg pl-12 pr-40 h-14 text-base text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors"
                  autoComplete="off"
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                  {query && (
                    <button
                      type="button"
                      onClick={() => { setQuery(""); setSuggestions([]); }}
                      className="text-on-surface/30 hover:text-on-surface transition-colors p-1"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    type="submit"
                    disabled={loading || !query.trim()}
                    className="bg-gradient-to-br from-primary to-primary-container disabled:opacity-40 text-on-primary rounded-lg px-5 h-11 text-sm font-bold transition-opacity"
                  >
                    {loading ? "Buscando..." : "Buscar"}
                  </button>
                </div>
              </div>
            </form>

            {/* Auto-suggest dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg shadow-2xl z-50 overflow-hidden">
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    onMouseDown={() => pickSuggestion(s)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-on-surface hover:bg-surface-container hover:text-white transition-colors text-left"
                  >
                    <Search className="w-3.5 h-3.5 text-on-surface/30 shrink-0" />
                    <span>{s}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Layout: filters + results + sidebar */}
          <div className="flex gap-5">
            {/* LEFT: Filter panel */}
            <aside
              className={`
                ${showFilters ? "block" : "hidden"} sm:block
                w-full sm:w-60 lg:w-64 shrink-0
                ${showFilters ? "fixed inset-0 z-50 sm:relative sm:inset-auto sm:z-auto" : ""}
              `}
            >
              {showFilters && (
                <div
                  className="fixed inset-0 bg-black/70 sm:hidden z-40"
                  onClick={() => setShowFilters(false)}
                />
              )}

              <div className={`
                ${showFilters ? "fixed right-0 top-0 bottom-0 w-80 z-50 overflow-y-auto sm:relative sm:inset-auto sm:w-auto sm:overflow-visible" : ""}
                bg-surface-container-low sm:bg-transparent border border-[rgba(79,70,51,0.15)] sm:border-0 rounded-lg sm:rounded-none p-4
              `}>
                {/* Mobile header */}
                <div className="flex items-center justify-between mb-4 sm:hidden">
                  <span className="font-medium text-sm text-on-surface">Filtros</span>
                  <button onClick={() => setShowFilters(false)} className="text-on-surface/40 hover:text-on-surface transition-colors">
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="space-y-5">
                  {/* Areas */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-3">
                      Area del derecho
                    </h3>
                    <div className="space-y-1">
                      {LEGAL_AREAS.map((area) => {
                        const Icon = area.icon;
                        const checked = filters.areas.includes(area.id);
                        return (
                          <label
                            key={area.id}
                            className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg cursor-pointer transition-colors text-sm ${
                              checked
                                ? "bg-surface-container text-on-surface"
                                : "text-on-surface/60 hover:text-on-surface hover:bg-surface-container"
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggleArea(area.id)}
                              className="rounded border-[rgba(79,70,51,0.15)] bg-[#35343a] text-primary focus:ring-primary/50 focus:ring-1 w-3.5 h-3.5"
                            />
                            <Icon className={`w-3.5 h-3.5 ${area.color}`} />
                            {area.name}
                          </label>
                        );
                      })}
                    </div>
                  </div>

                  {/* Document type */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-2">
                      Tipo de documento
                    </h3>
                    <div className="relative">
                      <select
                        value={filters.document_type}
                        onChange={(e) => setFilters((p) => ({ ...p, document_type: e.target.value }))}
                        className="w-full bg-[#35343a] border border-transparent rounded-lg px-3 py-2.5 text-sm text-on-surface focus:outline-none focus:border-primary appearance-none pr-8 transition-colors"
                      >
                        {DOCUMENT_TYPES.map((t) => (
                          <option key={t.id} value={t.id}>{t.name}</option>
                        ))}
                      </select>
                      <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-on-surface/30 pointer-events-none" />
                    </div>
                  </div>

                  {/* Hierarchy */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-2">
                      Jerarquia normativa
                    </h3>
                    <div className="relative">
                      <select
                        value={filters.hierarchy}
                        onChange={(e) => setFilters((p) => ({ ...p, hierarchy: e.target.value }))}
                        className="w-full bg-[#35343a] border border-transparent rounded-lg px-3 py-2.5 text-sm text-on-surface focus:outline-none focus:border-primary appearance-none pr-8 transition-colors"
                      >
                        {HIERARCHY_OPTIONS.map((h) => (
                          <option key={h.id} value={h.id}>{h.name}</option>
                        ))}
                      </select>
                      <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-on-surface/30 pointer-events-none" />
                    </div>
                  </div>

                  {/* Date range */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-2">
                      Rango de fecha
                    </h3>
                    <div className="space-y-2">
                      <div className="relative">
                        <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-on-surface/30" />
                        <input
                          type="date"
                          value={filters.date_from}
                          onChange={(e) => setFilters((p) => ({ ...p, date_from: e.target.value }))}
                          className="w-full bg-[#35343a] border border-transparent rounded-lg pl-8 pr-3 py-2.5 text-sm text-on-surface focus:outline-none focus:border-primary transition-colors"
                        />
                      </div>
                      <div className="relative">
                        <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-on-surface/30" />
                        <input
                          type="date"
                          value={filters.date_to}
                          onChange={(e) => setFilters((p) => ({ ...p, date_to: e.target.value }))}
                          className="w-full bg-[#35343a] border border-transparent rounded-lg pl-8 pr-3 py-2.5 text-sm text-on-surface focus:outline-none focus:border-primary transition-colors"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Clear filters */}
                  {hasActiveFilters && (
                    <button
                      onClick={clearFilters}
                      className="w-full flex items-center justify-center gap-2 text-sm text-on-surface/60 hover:text-on-surface border border-[rgba(79,70,51,0.15)] hover:border-primary/30 rounded-lg py-2.5 transition-colors"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      Limpiar filtros
                    </button>
                  )}

                  {/* Apply filters button (mobile) */}
                  <button
                    onClick={() => { setShowFilters(false); setPage(1); runSearch(query, filters, sort, 1); }}
                    className="sm:hidden w-full bg-gradient-to-br from-primary to-primary-container text-on-primary rounded-lg py-2.5 h-11 text-sm font-bold transition-opacity"
                  >
                    Aplicar filtros
                  </button>
                </div>
              </div>
            </aside>

            {/* CENTER: Results */}
            <main className="flex-1 min-w-0">
              {/* Toolbar: count + sort */}
              {(searched || loading) && (
                <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
                  <p className="text-sm text-on-surface/40">
                    {loading ? (
                      <span className="inline-block w-32 h-4 bg-surface-container-low rounded animate-pulse" />
                    ) : (
                      <>
                        <span className="text-on-surface font-medium">{total.toLocaleString()}</span>{" "}
                        resultado{total !== 1 ? "s" : ""} para{" "}
                        <span className="text-primary">&ldquo;{query}&rdquo;</span>
                      </>
                    )}
                  </p>
                  <div className="relative">
                    <select
                      value={sort}
                      onChange={(e) => handleSortChange(e.target.value)}
                      className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg pl-3 pr-8 py-1.5 text-sm text-on-surface focus:outline-none focus:border-primary appearance-none transition-colors"
                    >
                      {SORT_OPTIONS.map((s) => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-on-surface/30 pointer-events-none" />
                  </div>
                </div>
              )}

              {/* Loading skeletons */}
              {loading && (
                <div className="space-y-3">
                  {[...Array(5)].map((_, i) => <SkeletonCard key={i} />)}
                </div>
              )}

              {/* Empty state — post-search no results */}
              {searched && !loading && results.length === 0 && (
                <div className="text-center py-20">
                  <img src="/brand/logo-full.png" className="w-24 mx-auto mb-4 opacity-20" alt="Agente Derecho" />
                  <p className="text-base text-on-surface/60 font-medium mb-1">
                    No se encontraron resultados
                  </p>
                  <p className="text-sm text-on-surface/30">
                    Intenta con otros terminos{hasActiveFilters ? " o limpia los filtros" : ""}
                  </p>
                  {hasActiveFilters && (
                    <button
                      onClick={clearFilters}
                      className="mt-4 text-sm text-primary hover:text-primary-container transition-colors"
                    >
                      Limpiar todos los filtros
                    </button>
                  )}
                </div>
              )}

              {/* Browse mode — show all documents when no search query */}
              {!searched && !loading && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <p className="text-sm text-on-surface/60">
                      <span className="text-on-surface font-medium">{
                        (filters.areas.length > 0
                          ? allDocs.filter((d) => filters.areas.includes(d.legal_area))
                          : allDocs
                        ).length
                      }</span>{" "}
                      documentos en la base de conocimiento
                    </p>
                  </div>
                  {docsLoading ? (
                    <div className="space-y-3">
                      {[...Array(5)].map((_, i) => <SkeletonCard key={i} />)}
                    </div>
                  ) : allDocs.length === 0 ? (
                    <div className="text-center py-20">
                      <p className="text-sm text-on-surface/40">No hay documentos cargados en la base de conocimiento</p>
                    </div>
                  ) : (
                    <div className="space-y-0">
                      {(filters.areas.length > 0
                        ? allDocs.filter((d) => filters.areas.includes(d.legal_area))
                        : allDocs
                      ).map((doc, idx) => {
                        const areaInfo = AREA_MAP[doc.legal_area];
                        return (
                          <Link
                            key={doc.id}
                            href={`/documento/${doc.id}`}
                            className={`block p-5 transition-colors group ${
                              idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                            } hover:bg-surface-container`}
                          >
                            <div className="flex items-start justify-between gap-3 mb-2">
                              <div className="flex-1 min-w-0">
                                <h3 className="font-medium text-sm text-on-surface group-hover:text-primary transition-colors leading-snug">
                                  {doc.title}
                                  {doc.document_number && (
                                    <span className="text-on-surface/30 font-normal ml-2 text-xs">
                                      ({doc.document_number})
                                    </span>
                                  )}
                                </h3>
                              </div>
                              <div className="flex items-center gap-1.5 shrink-0">
                                {areaInfo && (
                                  <span className="bg-secondary-container text-secondary text-[10px] uppercase tracking-widest rounded px-2 py-0.5">
                                    {areaInfo.name}
                                  </span>
                                )}
                                <span className="text-[10px] px-2 py-0.5 rounded bg-[#35343a] text-on-surface/40">
                                  {doc.document_type.replace("_", " ")}
                                </span>
                              </div>
                            </div>
                            <p className="text-xs text-on-surface/30">
                              Fuente: {doc.source} {doc.hierarchy && `· ${doc.hierarchy}`}
                            </p>
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* Result cards */}
              {!loading && results.length > 0 && (
                <div className="space-y-0">
                  {results.map((result, idx) => {
                    const areaInfo = AREA_MAP[result.legal_area];
                    return (
                      <Link
                        key={result.id}
                        href={`/documento/${result.document_id}`}
                        className={`block p-5 transition-colors group ${
                          idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                        } hover:bg-surface-container`}
                      >
                        {/* Title row */}
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-sm text-on-surface group-hover:text-primary transition-colors leading-snug">
                              <HighlightedText text={result.title} query={query} />
                              {result.document_number && (
                                <span className="text-on-surface/30 font-normal ml-2 text-xs">
                                  ({result.document_number})
                                </span>
                              )}
                            </h3>
                          </div>
                          <div className="flex items-center gap-1.5 shrink-0">
                            {areaInfo && (
                              <span className="bg-secondary-container text-secondary text-[10px] uppercase tracking-widest rounded px-2 py-0.5">
                                {areaInfo.name}
                              </span>
                            )}
                            <span className="text-[10px] px-2 py-0.5 rounded bg-[#35343a] text-on-surface/40">
                              {result.document_type.replace("_", " ")}
                            </span>
                          </div>
                        </div>

                        {/* Score bar */}
                        {result.score > 0 && (
                          <div className="mb-2">
                            <div className="h-0.5 bg-surface-container-low rounded-full overflow-hidden w-24">
                              <div
                                className="h-full bg-gradient-to-r from-primary to-primary-container rounded-full"
                                style={{ width: `${Math.min(100, result.score * 100)}%` }}
                              />
                            </div>
                          </div>
                        )}

                        {/* Snippet */}
                        <p className="text-sm text-on-surface/60 leading-relaxed line-clamp-3">
                          <HighlightedText text={result.snippet} query={query} />
                        </p>

                        {/* Meta row */}
                        <div className="flex items-center gap-3 mt-2 text-xs text-on-surface/30">
                          {result.source && <span>{result.source}</span>}
                          {result.publication_date && (
                            <>
                              <span>·</span>
                              <span>{new Date(result.publication_date).getFullYear()}</span>
                            </>
                          )}
                          {result.hierarchy && (
                            <>
                              <span>·</span>
                              <span className="capitalize">{result.hierarchy}</span>
                            </>
                          )}
                        </div>
                      </Link>
                    );
                  })}
                </div>
              )}

              {/* Pagination */}
              {!loading && totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-8">
                  <button
                    onClick={() => handlePageChange(page - 1)}
                    disabled={page <= 1}
                    className="px-3 py-1.5 text-sm border border-[rgba(79,70,51,0.15)] rounded-lg text-on-surface/60 hover:text-on-surface hover:border-primary/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    Anterior
                  </button>

                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum: number;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (page <= 3) {
                      pageNum = i + 1;
                    } else if (page >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = page - 2 + i;
                    }
                    return (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`w-9 h-9 text-sm rounded-lg transition-colors ${
                          pageNum === page
                            ? "bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold"
                            : "border border-[rgba(79,70,51,0.15)] text-on-surface/60 hover:text-on-surface hover:border-primary/30"
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}

                  <button
                    onClick={() => handlePageChange(page + 1)}
                    disabled={page >= totalPages}
                    className="px-3 py-1.5 text-sm border border-[rgba(79,70,51,0.15)] rounded-lg text-on-surface/60 hover:text-on-surface hover:border-primary/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    Siguiente
                  </button>
                </div>
              )}
            </main>

            {/* RIGHT SIDEBAR: Saved searches + History (desktop only) */}
            <aside className="hidden lg:block w-60 shrink-0 space-y-4">
              {/* Save current search */}
              {isLoggedIn && query.trim() && searched && (
                <button
                  onClick={() => setSaveModalOpen(true)}
                  className="w-full flex items-center justify-center gap-2 text-sm border border-dashed border-[rgba(79,70,51,0.15)] hover:border-primary/40 text-on-surface/40 hover:text-primary rounded-lg py-2.5 transition-colors"
                >
                  <Bookmark className="w-4 h-4" />
                  Guardar esta busqueda
                </button>
              )}

              {/* Saved searches */}
              {isLoggedIn && savedSearches.length > 0 && (
                <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <BookmarkCheck className="w-3.5 h-3.5 text-primary" />
                    <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                      Busquedas guardadas
                    </h3>
                  </div>
                  <div className="space-y-0.5">
                    {savedSearches.slice(0, 8).map((s) => (
                      <div key={s.id} className="flex items-center gap-1 group">
                        <button
                          onClick={() => applySaved(s)}
                          className="flex-1 text-left text-sm text-on-surface hover:text-white truncate py-1 px-2 rounded-lg hover:bg-surface-container transition-colors"
                          title={s.query}
                        >
                          {s.name}
                        </button>
                        <button
                          onClick={() => handleDeleteSaved(s.id)}
                          className="opacity-0 group-hover:opacity-100 p-1 text-on-surface/30 hover:text-[#ffb4ab] transition-all"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Search history */}
              {isLoggedIn && history.length > 0 && (
                <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Clock className="w-3.5 h-3.5 text-on-surface/30" />
                    <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                      Busquedas recientes
                    </h3>
                  </div>
                  <div className="space-y-0.5">
                    {history.slice(0, 10).map((h) => (
                      <button
                        key={h.id}
                        onClick={() => applyHistory(h)}
                        className="w-full text-left text-sm text-on-surface/60 hover:text-on-surface py-1.5 px-2 rounded-lg hover:bg-surface-container transition-colors truncate flex items-center gap-2"
                        title={h.query}
                      >
                        <Search className="w-3 h-3 shrink-0 text-on-surface/30" />
                        <span className="truncate">{h.query}</span>
                        {h.results_count > 0 && (
                          <span className="text-xs text-on-surface/30 shrink-0 ml-auto">
                            {h.results_count}
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Not logged in hint */}
              {!isLoggedIn && (
                <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-4 text-center">
                  <Filter className="w-8 h-8 mx-auto mb-2 text-on-surface/10" />
                  <p className="text-xs text-on-surface/30 mb-3">
                    Inicia sesion para guardar busquedas y ver tu historial
                  </p>
                  <Link
                    href="/auth/login"
                    className="text-xs text-primary hover:text-primary-container transition-colors"
                  >
                    Iniciar sesion
                  </Link>
                </div>
              )}
            </aside>
          </div>
        </div>

        {/* Save search modal */}
        {saveModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
            <div
              className="absolute inset-0 bg-black/70"
              onClick={() => setSaveModalOpen(false)}
            />
            <div className="relative bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6 w-full max-w-sm shadow-2xl">
              <h2 className="font-['Newsreader'] text-xl font-bold text-on-surface mb-1">Guardar busqueda</h2>
              <p className="text-sm text-on-surface/40 mb-4 truncate">
                &ldquo;{query}&rdquo;
              </p>
              <input
                type="text"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSaveSearch()}
                placeholder="Nombre para esta busqueda..."
                className="w-full bg-[#35343a] border border-transparent rounded-lg px-3 py-3 text-sm placeholder-on-surface/30 text-on-surface focus:outline-none focus:border-primary mb-4 transition-colors"
                autoFocus
              />
              <div className="flex gap-3">
                <button
                  onClick={() => setSaveModalOpen(false)}
                  className="flex-1 border border-[rgba(79,70,51,0.15)] rounded-lg py-2.5 text-sm text-on-surface/60 hover:text-on-surface transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSaveSearch}
                  disabled={saving || !saveName.trim()}
                  className="flex-1 bg-gradient-to-br from-primary to-primary-container disabled:opacity-40 text-on-primary rounded-lg py-2.5 text-sm font-bold transition-opacity"
                >
                  {saving ? "Guardando..." : "Guardar"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
