"use client";

import { useState, useEffect, useRef, useCallback } from "react";
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
  { id: "civil", name: "Civil", icon: BookOpen, color: "text-blue-400", badge: "bg-blue-500/10 text-blue-400 border-blue-500/30" },
  { id: "penal", name: "Penal", icon: Shield, color: "text-red-400", badge: "bg-red-500/10 text-red-400 border-red-500/30" },
  { id: "laboral", name: "Laboral", icon: Briefcase, color: "text-green-400", badge: "bg-green-500/10 text-green-400 border-green-500/30" },
  { id: "tributario", name: "Tributario", icon: Landmark, color: "text-yellow-400", badge: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30" },
  { id: "constitucional", name: "Constitucional", icon: Gavel, color: "text-purple-400", badge: "bg-purple-500/10 text-purple-400 border-purple-500/30" },
  { id: "administrativo", name: "Administrativo", icon: Building2, color: "text-orange-400", badge: "bg-orange-500/10 text-orange-400 border-orange-500/30" },
  { id: "corporativo", name: "Corporativo", icon: ScrollText, color: "text-cyan-400", badge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30" },
  { id: "registral", name: "Registral", icon: FileCheck, color: "text-pink-400", badge: "bg-pink-500/10 text-pink-400 border-pink-500/30" },
  { id: "comercio_exterior", name: "Comercio Ext.", icon: Globe, color: "text-teal-400", badge: "bg-teal-500/10 text-teal-400 border-teal-500/30" },
  { id: "compliance", name: "Compliance", icon: Lock, color: "text-indigo-400", badge: "bg-indigo-500/10 text-indigo-400 border-indigo-500/30" },
  { id: "competencia", name: "Competencia/PI", icon: BadgeCheck, color: "text-amber-400", badge: "bg-amber-500/10 text-amber-400 border-amber-500/30" },
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
          <mark key={i} className="bg-amber-500/25 text-amber-300 rounded px-0.5 not-italic font-semibold">
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        );
      })}
    </span>
  );
}

// Skeleton card — premium tokens
function SkeletonCard() {
  return (
    <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-5 animate-pulse">
      <div className="flex justify-between gap-4 mb-3">
        <div className="flex-1">
          <div className="h-4 bg-[#2A2A35] rounded w-3/4 mb-2" />
          <div className="h-3 bg-[#1A1A22] rounded w-1/3" />
        </div>
        <div className="h-5 bg-[#2A2A35] rounded-full w-20 shrink-0" />
      </div>
      <div className="space-y-1.5">
        <div className="h-3 bg-[#1A1A22] rounded w-full" />
        <div className="h-3 bg-[#1A1A22] rounded w-5/6" />
        <div className="h-3 bg-[#1A1A22] rounded w-4/6" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function BuscarPage() {
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

      // Sync URL state
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
        // Refresh sidebar history after search
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
      <div className="min-h-full text-[#F5F5F5]">
        {/* Page header */}
        <div className="border-b border-[#1E1E2A] px-4 sm:px-6 py-3 flex items-center justify-between sticky top-0 bg-[#0A0A0F] z-30">
          <div className="flex items-center gap-2">
            <Search className="w-5 h-5 text-[#EAB308]" />
            <h1 className="font-bold text-base">Buscador Avanzado</h1>
          </div>
          {/* Mobile: toggle filters button */}
          <button
            onClick={() => setShowFilters((v) => !v)}
            className="sm:hidden flex items-center gap-1.5 text-sm text-[#9CA3AF] hover:text-[#F5F5F5] transition-colors bg-[#1A1A22] border border-[#2A2A35] rounded-xl px-3 py-1.5"
          >
            <SlidersHorizontal className="w-4 h-4" />
            Filtros
            {hasActiveFilters && (
              <span className="w-1.5 h-1.5 rounded-full bg-[#EAB308] ml-0.5" />
            )}
          </button>
        </div>

        <div className="max-w-screen-xl mx-auto px-4 sm:px-6 py-6">
        {/* ------------------------------------------------------------------ */}
        {/* Search bar                                                           */}
        {/* ------------------------------------------------------------------ */}
        <div className="relative mb-4">
          <form onSubmit={handleSubmit}>
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#6B7280] pointer-events-none" />
              <input
                ref={searchInputRef}
                type="text"
                value={query}
                onChange={handleQueryChange}
                onFocus={() => suggestions.length && setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                placeholder="Buscar en la normativa peruana... (ej: despido arbitrario, alimentos, IGV)"
                className="w-full bg-[#111116] border border-[#2A2A35] rounded-2xl pl-12 pr-40 h-14 text-lg placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-1 focus:ring-[#EAB308]/25 transition-colors"
                autoComplete="off"
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
                {query && (
                  <button
                    type="button"
                    onClick={() => { setQuery(""); setSuggestions([]); }}
                    className="text-[#6B7280] hover:text-[#F5F5F5] transition-colors p-1"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="bg-[#EAB308] hover:bg-[#CA9E00] disabled:bg-[#2A2A35] disabled:text-[#6B7280] text-[#0A0A0F] rounded-xl px-5 h-11 text-sm font-semibold transition-colors"
                >
                  {loading ? "Buscando..." : "Buscar"}
                </button>
              </div>
            </div>
          </form>

          {/* Auto-suggest dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-[#111116] border border-[#2A2A35] rounded-xl shadow-2xl z-50 overflow-hidden">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onMouseDown={() => pickSuggestion(s)}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-[#F5F5F5] hover:bg-[#1A1A22] hover:text-white transition-colors text-left"
                >
                  <Search className="w-3.5 h-3.5 text-[#6B7280] shrink-0" />
                  <span>{s}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* ------------------------------------------------------------------ */}
        {/* Layout: filters + results + sidebar                                 */}
        {/* ------------------------------------------------------------------ */}
        <div className="flex gap-6">
          {/* ================================================================ */}
          {/* LEFT: Filter panel                                                */}
          {/* Desktop: always visible. Mobile: slide-out via showFilters.       */}
          {/* ================================================================ */}
          <aside
            className={`
              ${showFilters ? "block" : "hidden"} sm:block
              w-full sm:w-64 lg:w-72 shrink-0
              ${showFilters ? "fixed inset-0 z-50 sm:relative sm:inset-auto sm:z-auto" : ""}
            `}
          >
            {/* Mobile overlay backdrop */}
            {showFilters && (
              <div
                className="fixed inset-0 bg-black/60 sm:hidden z-40"
                onClick={() => setShowFilters(false)}
              />
            )}

            <div className={`
              ${showFilters ? "fixed right-0 top-0 bottom-0 w-80 z-50 overflow-y-auto sm:relative sm:inset-auto sm:w-auto sm:overflow-visible" : ""}
              bg-[#111116] sm:bg-transparent border border-[#1E1E2A] sm:border-0 rounded-xl sm:rounded-none p-4
            `}>
              {/* Mobile header */}
              <div className="flex items-center justify-between mb-4 sm:hidden">
                <span className="font-medium text-sm">Filtros</span>
                <button onClick={() => setShowFilters(false)} className="text-[#9CA3AF] hover:text-[#F5F5F5]">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-5">
                {/* Areas */}
                <div>
                  <h3 className="text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider mb-3">
                    Area del derecho
                  </h3>
                  <div className="space-y-1.5">
                    {LEGAL_AREAS.map((area) => {
                      const Icon = area.icon;
                      const checked = filters.areas.includes(area.id);
                      return (
                        <label
                          key={area.id}
                          className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded-xl cursor-pointer transition-colors text-sm ${
                            checked
                              ? "bg-[#1A1A22] text-[#F5F5F5]"
                              : "text-[#9CA3AF] hover:text-[#F5F5F5] hover:bg-[#1A1A22]/50"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleArea(area.id)}
                            className="rounded border-[#2A2A35] bg-[#1A1A22] text-[#EAB308] focus:ring-[#EAB308]/50 focus:ring-1 w-3.5 h-3.5"
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
                  <h3 className="text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider mb-2">
                    Tipo de documento
                  </h3>
                  <div className="relative">
                    <select
                      value={filters.document_type}
                      onChange={(e) => setFilters((p) => ({ ...p, document_type: e.target.value }))}
                      className="w-full bg-[#1A1A22] border border-[#2A2A35] rounded-xl px-3 py-2 text-sm text-[#F5F5F5] focus:outline-none focus:border-[#EAB308] appearance-none pr-8"
                    >
                      {DOCUMENT_TYPES.map((t) => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6B7280] pointer-events-none" />
                  </div>
                </div>

                {/* Hierarchy */}
                <div>
                  <h3 className="text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider mb-2">
                    Jerarquia normativa
                  </h3>
                  <div className="relative">
                    <select
                      value={filters.hierarchy}
                      onChange={(e) => setFilters((p) => ({ ...p, hierarchy: e.target.value }))}
                      className="w-full bg-[#1A1A22] border border-[#2A2A35] rounded-xl px-3 py-2 text-sm text-[#F5F5F5] focus:outline-none focus:border-[#EAB308] appearance-none pr-8"
                    >
                      {HIERARCHY_OPTIONS.map((h) => (
                        <option key={h.id} value={h.id}>{h.name}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6B7280] pointer-events-none" />
                  </div>
                </div>

                {/* Date range */}
                <div>
                  <h3 className="text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider mb-2">
                    Rango de fecha
                  </h3>
                  <div className="space-y-2">
                    <div className="relative">
                      <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6B7280]" />
                      <input
                        type="date"
                        value={filters.date_from}
                        onChange={(e) => setFilters((p) => ({ ...p, date_from: e.target.value }))}
                        className="w-full bg-[#1A1A22] border border-[#2A2A35] rounded-xl pl-8 pr-3 py-2 text-sm text-[#F5F5F5] focus:outline-none focus:border-[#EAB308]"
                      />
                    </div>
                    <div className="relative">
                      <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6B7280]" />
                      <input
                        type="date"
                        value={filters.date_to}
                        onChange={(e) => setFilters((p) => ({ ...p, date_to: e.target.value }))}
                        className="w-full bg-[#1A1A22] border border-[#2A2A35] rounded-xl pl-8 pr-3 py-2 text-sm text-[#F5F5F5] focus:outline-none focus:border-[#EAB308]"
                      />
                    </div>
                  </div>
                </div>

                {/* Clear filters */}
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="w-full flex items-center justify-center gap-2 text-sm text-[#9CA3AF] hover:text-[#F5F5F5] border border-[#2A2A35] hover:border-[#EAB308]/40 rounded-xl py-2 transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    Limpiar filtros
                  </button>
                )}

                {/* Apply filters button (mobile) */}
                <button
                  onClick={() => { setShowFilters(false); setPage(1); runSearch(query, filters, sort, 1); }}
                  className="sm:hidden w-full bg-[#EAB308] hover:bg-[#CA9E00] text-[#0A0A0F] rounded-xl py-2.5 h-11 text-sm font-semibold transition-colors"
                >
                  Aplicar filtros
                </button>
              </div>
            </div>
          </aside>

          {/* ================================================================ */}
          {/* CENTER: Results                                                   */}
          {/* ================================================================ */}
          <main className="flex-1 min-w-0">
            {/* Toolbar: count + sort */}
            {(searched || loading) && (
              <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
                <p className="text-sm text-[#9CA3AF]">
                  {loading ? (
                    <span className="inline-block w-32 h-4 bg-[#1A1A22] rounded animate-pulse" />
                  ) : (
                    <>
                      <span className="text-[#F5F5F5] font-medium">{total.toLocaleString()}</span>{" "}
                      resultado{total !== 1 ? "s" : ""} para{" "}
                      <span className="text-[#EAB308]">&ldquo;{query}&rdquo;</span>
                    </>
                  )}
                </p>
                <div className="relative">
                  <select
                    value={sort}
                    onChange={(e) => handleSortChange(e.target.value)}
                    className="bg-[#1A1A22] border border-[#2A2A35] rounded-xl pl-3 pr-8 py-1.5 text-sm text-[#F5F5F5] focus:outline-none focus:border-[#EAB308] appearance-none"
                  >
                    {SORT_OPTIONS.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6B7280] pointer-events-none" />
                </div>
              </div>
            )}

            {/* Loading skeletons */}
            {loading && (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => <SkeletonCard key={i} />)}
              </div>
            )}

            {/* Empty state — post-search no results */}
            {searched && !loading && results.length === 0 && (
              <div className="text-center py-20 text-[#6B7280]">
                <img src="/brand/logo-full.png" className="w-24 mx-auto mb-4 opacity-40" alt="Agente Derecho" />
                <p className="text-base text-[#9CA3AF] font-medium mb-1">
                  No se encontraron resultados
                </p>
                <p className="text-sm">
                  Intenta con otros terminos{hasActiveFilters ? " o limpia los filtros" : ""}
                </p>
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="mt-4 text-sm text-[#EAB308] hover:text-[#CA9E00] underline transition-colors"
                  >
                    Limpiar todos los filtros
                  </button>
                )}
              </div>
            )}

            {/* Initial empty state — never searched */}
            {!searched && !loading && (
              <div className="text-center py-20 text-[#6B7280]">
                <img src="/brand/logo-full.png" className="w-24 mx-auto mb-4 opacity-40" alt="Agente Derecho" />
                <p className="text-sm text-[#6B7280]">Ingresa un termino para comenzar la busqueda</p>
              </div>
            )}

            {/* Result cards */}
            {!loading && results.length > 0 && (
              <div className="space-y-4">
                {results.map((result) => {
                  const areaInfo = AREA_MAP[result.legal_area];
                  return (
                    <Link
                      key={result.id}
                      href={`/documento/${result.document_id}`}
                      className="block bg-[#111116] border border-[#1E1E2A] rounded-xl p-5 hover:border-[#2A2A35] hover:bg-[#1A1A22] transition-colors group"
                    >
                      {/* Title row */}
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-sm text-[#F5F5F5] group-hover:text-[#EAB308] transition-colors leading-snug">
                            <HighlightedText text={result.title} query={query} />
                            {result.document_number && (
                              <span className="text-[#6B7280] font-normal ml-2 text-xs">
                                ({result.document_number})
                              </span>
                            )}
                          </h3>
                        </div>
                        <div className="flex items-center gap-1.5 shrink-0">
                          {areaInfo && (
                            <span className={`text-[10px] px-2 py-0.5 rounded-full border ${areaInfo.badge}`}>
                              {areaInfo.name}
                            </span>
                          )}
                          <span className="text-[10px] px-2 py-0.5 rounded-full border bg-[#1A1A22] text-[#9CA3AF] border-[#2A2A35]">
                            {result.document_type.replace("_", " ")}
                          </span>
                        </div>
                      </div>

                      {/* Snippet */}
                      <p className="text-sm text-[#9CA3AF] leading-relaxed line-clamp-3">
                        <HighlightedText text={result.snippet} query={query} />
                      </p>

                      {/* Meta row */}
                      <div className="flex items-center gap-3 mt-3 text-xs text-[#6B7280]">
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
                  className="px-3 py-1.5 text-sm border border-[#2A2A35] rounded-xl text-[#9CA3AF] hover:text-[#F5F5F5] hover:border-[#EAB308]/40 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Anterior
                </button>

                {/* Page numbers — show window of 5 around current */}
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
                      className={`w-9 h-9 text-sm rounded-xl transition-colors ${
                        pageNum === page
                          ? "bg-[#EAB308] text-[#0A0A0F] font-semibold border border-[#EAB308]"
                          : "border border-[#2A2A35] text-[#9CA3AF] hover:text-[#F5F5F5] hover:border-[#EAB308]/40"
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}

                <button
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page >= totalPages}
                  className="px-3 py-1.5 text-sm border border-[#2A2A35] rounded-xl text-[#9CA3AF] hover:text-[#F5F5F5] hover:border-[#EAB308]/40 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  Siguiente
                </button>
              </div>
            )}
          </main>

          {/* ================================================================ */}
          {/* RIGHT SIDEBAR: Saved searches + History (desktop only)           */}
          {/* ================================================================ */}
          <aside className="hidden lg:block w-64 shrink-0 space-y-5">
            {/* Save current search */}
            {isLoggedIn && query.trim() && searched && (
              <button
                onClick={() => setSaveModalOpen(true)}
                className="w-full flex items-center justify-center gap-2 text-sm border border-dashed border-[#2A2A35] hover:border-[#EAB308]/50 text-[#9CA3AF] hover:text-[#EAB308] rounded-xl py-2.5 transition-colors"
              >
                <Bookmark className="w-4 h-4" />
                Guardar esta busqueda
              </button>
            )}

            {/* Saved searches */}
            {isLoggedIn && savedSearches.length > 0 && (
              <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <BookmarkCheck className="w-4 h-4 text-[#EAB308]" />
                  <h3 className="text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">
                    Busquedas guardadas
                  </h3>
                </div>
                <div className="space-y-1">
                  {savedSearches.slice(0, 8).map((s) => (
                    <div key={s.id} className="flex items-center gap-1 group">
                      <button
                        onClick={() => applySaved(s)}
                        className="flex-1 text-left text-sm text-[#F5F5F5] hover:text-white truncate py-1 px-2 rounded-xl hover:bg-[#1A1A22] transition-colors"
                        title={s.query}
                      >
                        {s.name}
                      </button>
                      <button
                        onClick={() => handleDeleteSaved(s.id)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-[#6B7280] hover:text-red-400 transition-all"
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
              <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Clock className="w-4 h-4 text-[#6B7280]" />
                  <h3 className="text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">
                    Busquedas recientes
                  </h3>
                </div>
                <div className="space-y-0.5">
                  {history.slice(0, 10).map((h) => (
                    <button
                      key={h.id}
                      onClick={() => applyHistory(h)}
                      className="w-full text-left text-sm text-[#9CA3AF] hover:text-[#F5F5F5] py-1.5 px-2 rounded-xl hover:bg-[#1A1A22] transition-colors truncate flex items-center gap-2"
                      title={h.query}
                    >
                      <Search className="w-3 h-3 shrink-0 text-[#6B7280]" />
                      <span className="truncate">{h.query}</span>
                      {h.results_count > 0 && (
                        <span className="text-xs text-[#6B7280] shrink-0 ml-auto">
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
              <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-4 text-center">
                <Filter className="w-8 h-8 mx-auto mb-2 text-[#2A2A35]" />
                <p className="text-xs text-[#6B7280] mb-3">
                  Inicia sesion para guardar busquedas y ver tu historial
                </p>
                <Link
                  href="/auth/login"
                  className="text-xs text-[#EAB308] hover:text-[#CA9E00] transition-colors"
                >
                  Iniciar sesion
                </Link>
              </div>
            )}
          </aside>
        </div>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* Save search modal                                                     */}
      {/* -------------------------------------------------------------------- */}
      {saveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <div
            className="absolute inset-0 bg-black/70"
            onClick={() => setSaveModalOpen(false)}
          />
          <div className="relative bg-[#111116] border border-[#2A2A35] rounded-2xl p-6 w-full max-w-sm shadow-2xl">
            <h2 className="font-bold text-base mb-1 text-[#F5F5F5]">Guardar busqueda</h2>
            <p className="text-sm text-[#9CA3AF] mb-4 truncate">
              &ldquo;{query}&rdquo;
            </p>
            <input
              type="text"
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSaveSearch()}
              placeholder="Nombre para esta busqueda..."
              className="w-full bg-[#111116] border border-[#2A2A35] rounded-xl px-3 h-12 text-sm placeholder-[#6B7280] text-[#F5F5F5] focus:outline-none focus:border-[#EAB308] mb-4"
              autoFocus
            />
            <div className="flex gap-3">
              <button
                onClick={() => setSaveModalOpen(false)}
                className="flex-1 border border-[#2A2A35] rounded-xl py-2 text-sm text-[#9CA3AF] hover:text-[#F5F5F5] transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveSearch}
                disabled={saving || !saveName.trim()}
                className="flex-1 bg-[#EAB308] hover:bg-[#CA9E00] disabled:bg-[#2A2A35] disabled:text-[#6B7280] text-[#0A0A0F] rounded-xl py-2 text-sm font-semibold transition-colors"
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
