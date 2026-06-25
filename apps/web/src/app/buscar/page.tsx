"use client";

import {
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ArrowUpRight,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Copy,
  Database,
  Download,
  ExternalLink,
  Filter,
  Loader2,
  Quote,
  Search as SearchIcon,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { LEGAL_AREAS } from "@/app/chat/constants";
import { AppLayout } from "@/components/AppLayout";
import { PublicLayout } from "@/components/public/PublicLayout";
import { InternalPageHeader } from "@/components/shell/InternalPageHeader";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";
import { UpsellModal } from "@/components/UpsellModal";
import { useAuth, useHasFeature } from "@/lib/auth/AuthContext";
import { downloadBlob } from "@/lib/export/downloadBlob";

// ---------------------------------------------------------------------------
// Types — mirror schemas in apps/api/app/api/routes/search.py and documents.py
// ---------------------------------------------------------------------------

interface SearchResultItem {
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

interface PaginatedSearchResponse {
  results: SearchResultItem[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  query: string;
}

interface KBStats {
  total_documents: number;
  total_chunks: number;
  chunks_by_area: Record<string, number>;
}

interface DocumentDetail {
  id: string;
  title: string;
  document_type: string;
  document_number: string | null;
  legal_area: string;
  hierarchy: string | null;
  source: string;
  source_url: string | null;
  publication_date: string | null;
  is_active: boolean;
}

interface DocumentChunkDetail {
  id: string;
  article_number: string | null;
  section_path: string | null;
  content: string;
}

interface DocumentResponse {
  document: DocumentDetail;
  chunks: DocumentChunkDetail[];
  total_chunks: number;
}

type SortMode = "relevance" | "date_desc" | "date_asc";

const PER_PAGE = 20;

// Example queries shown on the empty state — chosen to cover the most common
// areas a Peruvian lawyer searches for, and to teach the user the kind of
// terminology that returns good hits (article names, legal concepts, leading
// cases). When clicked, the area filter is also pre-selected so the result set
// is narrower and easier to scan.
const EXAMPLE_QUERIES: { query: string; area: string; hint: string }[] = [
  {
    query: "despido arbitrario",
    area: "laboral",
    hint: "Art. 34 y 38 del TUO del DL 728 · indemnización",
  },
  {
    query: "prescripción tributaria",
    area: "tributario",
    hint: "Plazos del Código Tributario · suspensión e interrupción",
  },
  {
    query: "prisión preventiva",
    area: "penal",
    hint: "Presupuestos del CPP · jurisprudencia vinculante",
  },
  {
    query: "responsabilidad extracontractual",
    area: "civil",
    hint: "Art. 1969 y siguientes del Código Civil · daños",
  },
  {
    query: "habeas corpus",
    area: "constitucional",
    hint: "Precedentes del TC · tipos y procedencia",
  },
  {
    query: "silencio administrativo",
    area: "administrativo",
    hint: "LPAG · silencio positivo y negativo",
  },
  {
    query: "protección al consumidor",
    area: "consumidor",
    hint: "Código del Consumidor · INDECOPI",
  },
  {
    query: "datos personales tratamiento",
    area: "datos_personales",
    hint: "Ley 29733 · consentimiento y derechos ARCO",
  },
];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  ley: "Ley",
  decreto_supremo: "Decreto Supremo",
  decreto_legislativo: "Decreto Legislativo",
  resolucion: "Resolución",
  resolucion_ministerial: "Resolución Ministerial",
  sentencia: "Sentencia",
  casacion: "Casación",
  constitucion: "Constitución",
  reglamento: "Reglamento",
};

const HIERARCHY_LABELS: Record<string, string> = {
  constitucional: "Constitucional",
  legal: "Legal",
  reglamentario: "Reglamentario",
};

function prettyDocType(type: string): string {
  return DOCUMENT_TYPE_LABELS[type] ?? type.replace(/_/g, " ");
}

function prettyDate(iso: string | null): string | null {
  if (!iso) return null;
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("es-PE", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return iso;
  }
}

/**
 * Escapes user input for use inside a RegExp without breaking with chars like
 * `()*+?[]\^$|.` — required because the search box is free-text.
 */
function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Splits text into tokens and wraps any matching segment in <mark>.
 * Case- and accent-insensitive within the limits of the browser locale,
 * but RegExp itself is plain — we only do `\b` boundary + i flag.
 */
function HighlightedText({
  text,
  query,
  className,
}: {
  text: string;
  query: string;
  className?: string;
}) {
  const tokens = useMemo(() => {
    const q = query.trim();
    if (q.length < 2) return [{ text, match: false }];
    // Split query into words ≥2 chars, escape each, join as alternation.
    const words = q
      .split(/\s+/)
      .filter((w) => w.length >= 2)
      .map(escapeRegExp);
    if (!words.length) return [{ text, match: false }];
    const re = new RegExp(`(${words.join("|")})`, "ig");
    const parts = text.split(re);
    return parts.map((p) => ({ text: p, match: re.test(p) && p.length > 0 }));
  }, [text, query]);

  return (
    <span className={className}>
      {tokens.map((t, i) =>
        t.match ? (
          <mark
            key={i}
            className="bg-amber-300/30 text-on-surface rounded-sm px-0.5"
          >
            {t.text}
          </mark>
        ) : (
          <span key={i}>{t.text}</span>
        ),
      )}
    </span>
  );
}

// Common Peruvian source codes that should display uppercase (acronyms).
const SOURCE_DISPLAY: Record<string, string> = {
  spij: "SPIJ",
  tc: "Tribunal Constitucional",
  el_peruano: "El Peruano",
  sunat: "SUNAT",
  mef: "MEF",
  cs: "Corte Suprema",
  pj: "Poder Judicial",
  congreso: "Congreso",
  minjus: "MINJUS",
  osce: "OSCE",
  indecopi: "INDECOPI",
};

function prettySource(source: string): string {
  if (!source) return "";
  const key = source.toLowerCase().trim();
  if (SOURCE_DISPLAY[key]) return SOURCE_DISPLAY[key];
  // Short tokens that look like acronyms → uppercase
  if (key.length <= 5 && /^[a-z]+$/.test(key)) return key.toUpperCase();
  return source;
}

/**
 * If a `document_number` already starts with its short-code (DS 003-97-TR for
 * a "decreto_supremo"), surface the number as-is to avoid awkward
 * "Decreto Supremo Nº DS 003-97-TR". Otherwise emit "<Type> Nº <num>".
 */
function buildDocumentHead(
  documentType: string,
  documentNumber: string | null,
): string {
  const type = prettyDocType(documentType);
  const num = documentNumber?.trim();
  if (!num) return type;
  const SHORT_CODES = ["DS", "DL", "DU", "RM", "RJ", "RD", "RA", "RS", "RR", "Ley"];
  const startsWithCode = SHORT_CODES.some((c) =>
    num.toLowerCase().startsWith(c.toLowerCase() + " ") ||
    num.toLowerCase().startsWith(c.toLowerCase() + "-"),
  );
  if (startsWithCode) return num; // number already self-describing
  return `${type} Nº ${num}`;
}

/**
 * Build a Peruvian-style legal citation.
 *
 * Examples:
 *  - "DS 003-97-TR, art. 34 — TUO del DL 728. Fuente: SPIJ."
 *  - "Decreto Legislativo Nº 1075, art. 5 — Régimen común de propiedad industrial.
 *    Publicado el 28 jun 2008. Fuente: El Peruano."
 *  - "Código Civil, art. 924. Fuente: SPIJ."
 */
function buildCitation(
  doc: DocumentDetail,
  chunk: DocumentChunkDetail | null,
): string {
  const head = buildDocumentHead(doc.document_type, doc.document_number);
  const parts: string[] = [head];
  if (chunk?.article_number) parts.push(`art. ${chunk.article_number}`);
  let citation = parts.join(", ");

  // Append the title only when it adds info not already in the head.
  if (
    doc.title &&
    !head.toLowerCase().includes(doc.title.toLowerCase().slice(0, 12)) &&
    !doc.title.toLowerCase().includes(head.toLowerCase())
  ) {
    citation += ` — ${doc.title}`;
  }

  const meta: string[] = [];
  const pub = prettyDate(doc.publication_date);
  if (pub) meta.push(`Publicado el ${pub}`);
  const src = prettySource(doc.source);
  if (src) meta.push(`Fuente: ${src}`);
  if (meta.length) citation += `. ${meta.join(". ")}.`;
  else citation += ".";
  return citation;
}

function buildCitationWithText(
  doc: DocumentDetail,
  chunk: DocumentChunkDetail,
): string {
  const cite = buildCitation(doc, chunk);
  const text = chunk.content.trim();
  return `"${text}"\n\n— ${cite}`;
}

// ---------------------------------------------------------------------------
// Result card
// ---------------------------------------------------------------------------

function ResultCard({
  result,
  query,
  onOpen,
}: {
  result: SearchResultItem;
  query: string;
  onOpen: () => void;
}) {
  const areaMeta = LEGAL_AREAS.find((a) => a.id === result.legal_area);
  return (
    <button
      type="button"
      onClick={onOpen}
      className="w-full text-left bg-surface-container-low border border-outline-variant rounded-lg p-4 hover:border-primary/40 hover:shadow-sm transition-all group"
    >
      <header className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-on-surface line-clamp-2">
            <HighlightedText text={result.title} query={query} />
          </h3>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 mt-1 text-[11px] text-on-surface/50">
            <span>{prettyDocType(result.document_type)}</span>
            {result.document_number && (
              <>
                <span>·</span>
                <span className="font-mono">{result.document_number}</span>
              </>
            )}
            {result.publication_date && (
              <>
                <span>·</span>
                <span>{prettyDate(result.publication_date)}</span>
              </>
            )}
            {result.source && (
              <>
                <span>·</span>
                <span>{result.source}</span>
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {areaMeta && (
            <span
              className={`flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-surface border border-outline-variant ${areaMeta.color}`}
            >
              {areaMeta.name}
            </span>
          )}
          {result.hierarchy && HIERARCHY_LABELS[result.hierarchy] && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface border border-outline-variant text-on-surface/60">
              {HIERARCHY_LABELS[result.hierarchy]}
            </span>
          )}
        </div>
      </header>
      <p className="text-sm text-on-surface/70 leading-relaxed line-clamp-4 whitespace-pre-line">
        <HighlightedText text={result.snippet} query={query} />
      </p>
      <footer className="mt-3 pt-3 border-t border-outline-variant/60 flex items-center justify-between text-[10px] text-on-surface/40">
        <span className="font-mono">score: {result.score.toFixed(3)}</span>
        <span className="flex items-center gap-1 text-primary/80 opacity-0 group-hover:opacity-100 transition-opacity">
          Abrir documento <ArrowUpRight className="w-3 h-3" />
        </span>
      </footer>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Document drawer
// ---------------------------------------------------------------------------

function DocumentDrawer({
  documentId,
  initialChunkId,
  query,
  onClose,
}: {
  documentId: string;
  initialChunkId: string | null;
  query: string;
  onClose: () => void;
}) {
  const [data, setData] = useState<DocumentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeChunkId, setActiveChunkId] = useState<string | null>(initialChunkId);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError(null);
    fetch(`/api/documents/${documentId}/chunks`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = (await res.json()) as DocumentResponse;
        if (alive) {
          setData(json);
          if (!initialChunkId && json.chunks.length) {
            setActiveChunkId(json.chunks[0].id);
          }
        }
      })
      .catch((e) => {
        if (alive) setError(e.message || "Error al cargar documento");
      })
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [documentId, initialChunkId]);

  // Scroll active chunk into view on first load & whenever it changes
  useEffect(() => {
    if (!activeChunkId || !containerRef.current) return;
    const el = containerRef.current.querySelector<HTMLElement>(
      `[data-chunk-id="${activeChunkId}"]`,
    );
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [activeChunkId, data]);

  // ESC closes
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const activeChunk = useMemo(
    () => data?.chunks.find((c) => c.id === activeChunkId) ?? null,
    [data, activeChunkId],
  );

  const navigateChunk = useCallback(
    (delta: 1 | -1) => {
      if (!data || !activeChunkId) return;
      const idx = data.chunks.findIndex((c) => c.id === activeChunkId);
      if (idx < 0) return;
      const next = idx + delta;
      if (next < 0 || next >= data.chunks.length) return;
      setActiveChunkId(data.chunks[next].id);
    },
    [data, activeChunkId],
  );

  const handleCopyCitation = useCallback(
    async (mode: "short" | "with_text") => {
      if (!data || !activeChunk) return;
      const text =
        mode === "short"
          ? buildCitation(data.document, activeChunk)
          : buildCitationWithText(data.document, activeChunk);
      try {
        await navigator.clipboard.writeText(text);
        toast.success(mode === "short" ? "Cita copiada" : "Cita con texto copiada");
      } catch {
        toast.error("No se pudo copiar al portapapeles");
      }
    },
    [data, activeChunk],
  );

  return (
    <div className="fixed inset-0 z-50 flex" role="dialog" aria-modal="true">
      <button
        type="button"
        aria-label="Cerrar"
        onClick={onClose}
        className="flex-1 bg-black/40 backdrop-blur-sm"
      />
      <aside className="w-full max-w-3xl bg-surface border-l border-outline-variant shadow-2xl flex flex-col">
        {/* Sticky header */}
        <header className="shrink-0 border-b border-outline-variant bg-surface-container-low">
          <div className="flex items-start justify-between gap-3 px-5 pt-4 pb-3">
            <div className="flex-1 min-w-0">
              {loading ? (
                <div className="h-5 w-2/3 bg-on-surface/10 rounded animate-pulse" />
              ) : data ? (
                <>
                  <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] uppercase tracking-wider text-on-surface/40 mb-1">
                    <span>{prettyDocType(data.document.document_type)}</span>
                    {data.document.document_number && (
                      <>
                        <span>·</span>
                        <span className="font-mono normal-case">
                          {data.document.document_number}
                        </span>
                      </>
                    )}
                    {data.document.hierarchy &&
                      HIERARCHY_LABELS[data.document.hierarchy] && (
                        <>
                          <span>·</span>
                          <span>{HIERARCHY_LABELS[data.document.hierarchy]}</span>
                        </>
                      )}
                  </div>
                  <h2 className="text-lg font-semibold text-on-surface leading-snug">
                    {data.document.title}
                  </h2>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-[11px] text-on-surface/50">
                    {data.document.publication_date && (
                      <span>Publicado: {prettyDate(data.document.publication_date)}</span>
                    )}
                    {data.document.source && (
                      <span>Fuente: {prettySource(data.document.source)}</span>
                    )}
                    {data.document.is_active === false && (
                      <span className="text-red-500">No vigente</span>
                    )}
                    {data.document.source_url && (
                      <a
                        href={data.document.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-primary hover:underline"
                      >
                        Fuente oficial <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </>
              ) : (
                <p className="text-sm text-red-500">{error}</p>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-md hover:bg-on-surface/5 text-on-surface/60"
              aria-label="Cerrar drawer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Navigation toolbar */}
          {data && data.chunks.length > 0 && (
            <div className="flex items-center justify-between gap-2 px-5 py-2 border-t border-outline-variant/60 bg-surface">
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => navigateChunk(-1)}
                  disabled={
                    !activeChunkId ||
                    data.chunks.findIndex((c) => c.id === activeChunkId) <= 0
                  }
                  className="p-1.5 rounded-md hover:bg-on-surface/5 text-on-surface/60 disabled:opacity-30 disabled:cursor-not-allowed"
                  aria-label="Artículo anterior"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-[11px] text-on-surface/50 px-1">
                  {activeChunk?.article_number
                    ? `Art. ${activeChunk.article_number}`
                    : activeChunkId
                      ? `Sección ${data.chunks.findIndex((c) => c.id === activeChunkId) + 1}`
                      : "—"}
                  <span className="text-on-surface/30">
                    {" "}
                    de {data.chunks.length}
                  </span>
                </span>
                <button
                  type="button"
                  onClick={() => navigateChunk(1)}
                  disabled={
                    !activeChunkId ||
                    data.chunks.findIndex((c) => c.id === activeChunkId) >=
                      data.chunks.length - 1
                  }
                  className="p-1.5 rounded-md hover:bg-on-surface/5 text-on-surface/60 disabled:opacity-30 disabled:cursor-not-allowed"
                  aria-label="Artículo siguiente"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => handleCopyCitation("short")}
                  disabled={!activeChunk}
                  className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-on-surface/70 hover:bg-on-surface/5 hover:text-on-surface disabled:opacity-40"
                  title="Copiar referencia formateada"
                >
                  <Copy className="w-3 h-3" />
                  Copiar cita
                </button>
                <button
                  type="button"
                  onClick={() => handleCopyCitation("with_text")}
                  disabled={!activeChunk}
                  className="flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-on-surface/70 hover:bg-on-surface/5 hover:text-on-surface disabled:opacity-40"
                  title="Copiar texto del artículo + cita"
                >
                  <Quote className="w-3 h-3" />
                  Copiar con texto
                </button>
              </div>
            </div>
          )}
        </header>

        {/* Body */}
        <div ref={containerRef} className="flex-1 overflow-y-auto">
          {loading && (
            <div className="flex items-center justify-center py-20 text-on-surface/50">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              Cargando documento…
            </div>
          )}
          {!loading && data && data.chunks.length === 0 && (
            <div className="py-20 text-center text-on-surface/50 text-sm">
              Este documento aún no tiene artículos indexados.
            </div>
          )}
          {!loading && data && (
            <div className="divide-y divide-outline-variant/40">
              {data.chunks.map((c) => {
                const isActive = c.id === activeChunkId;
                return (
                  <article
                    key={c.id}
                    data-chunk-id={c.id}
                    onClick={() => setActiveChunkId(c.id)}
                    className={`px-5 py-4 cursor-pointer scroll-mt-4 transition-colors ${
                      isActive
                        ? "bg-primary/5 border-l-2 border-l-primary"
                        : "hover:bg-on-surface/[0.02] border-l-2 border-l-transparent"
                    }`}
                  >
                    {(c.article_number || c.section_path) && (
                      <header className="flex items-baseline gap-2 mb-2">
                        {c.article_number && (
                          <span className="text-[11px] font-semibold uppercase tracking-wider text-primary">
                            Art. {c.article_number}
                          </span>
                        )}
                        {c.section_path && (
                          <span className="text-[10px] text-on-surface/40 truncate">
                            {c.section_path}
                          </span>
                        )}
                      </header>
                    )}
                    <p className="text-sm text-on-surface/80 leading-relaxed whitespace-pre-line">
                      <HighlightedText text={c.content} query={query} />
                    </p>
                  </article>
                );
              })}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagination
// ---------------------------------------------------------------------------

function Pagination({
  page,
  totalPages,
  onChange,
}: {
  page: number;
  totalPages: number;
  onChange: (p: number) => void;
}) {
  if (totalPages <= 1) return null;
  const canPrev = page > 1;
  const canNext = page < totalPages;
  return (
    <nav
      className="flex items-center justify-center gap-2 mt-6 text-sm"
      aria-label="Paginación"
    >
      <button
        type="button"
        onClick={() => canPrev && onChange(page - 1)}
        disabled={!canPrev}
        className="flex items-center gap-1 px-3 py-1.5 rounded-md border border-outline-variant text-on-surface/70 hover:border-primary/40 disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <ChevronLeft className="w-4 h-4" /> Anterior
      </button>
      <span className="text-on-surface/60">
        Página <strong className="text-on-surface">{page}</strong> de {totalPages}
      </span>
      <button
        type="button"
        onClick={() => canNext && onChange(page + 1)}
        disabled={!canNext}
        className="flex items-center gap-1 px-3 py-1.5 rounded-md border border-outline-variant text-on-surface/70 hover:border-primary/40 disabled:opacity-30 disabled:cursor-not-allowed"
      >
        Siguiente <ChevronRight className="w-4 h-4" />
      </button>
    </nav>
  );
}

// ---------------------------------------------------------------------------
// Main content
// ---------------------------------------------------------------------------

function BuscarContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, authFetch } = useAuth();
  const hasPdfExport = useHasFeature("pdf_export");

  // URL-backed state — read once on mount and on URL change
  const urlQuery = searchParams.get("q") ?? "";
  const urlArea = searchParams.get("area") ?? "";
  const urlSort = (searchParams.get("sort") as SortMode | null) ?? "relevance";
  const urlPage = Math.max(1, parseInt(searchParams.get("page") ?? "1", 10) || 1);
  const urlDoc = searchParams.get("doc");
  const urlChunk = searchParams.get("chunk");

  const [query, setQuery] = useState(urlQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(urlQuery);
  const [selectedArea, setSelectedArea] = useState<string>(urlArea);
  const [sort, setSort] = useState<SortMode>(urlSort);
  const [page, setPage] = useState(urlPage);

  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const [stats, setStats] = useState<KBStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  const [openDoc, setOpenDoc] = useState<{ docId: string; chunkId: string | null } | null>(
    urlDoc ? { docId: urlDoc, chunkId: urlChunk } : null,
  );
  const [exporting, setExporting] = useState(false);
  const [showUpsell, setShowUpsell] = useState(false);

  const [showFilters, setShowFilters] = useState(false);

  // Sync URL ← state
  const writeUrl = useCallback(
    (next: {
      query?: string;
      area?: string;
      sort?: SortMode;
      page?: number;
      doc?: string | null;
      chunk?: string | null;
    }) => {
      const params = new URLSearchParams();
      const q = next.query ?? debouncedQuery;
      const a = next.area ?? selectedArea;
      const s = next.sort ?? sort;
      const p = next.page ?? page;
      const d = next.doc !== undefined ? next.doc : openDoc?.docId ?? null;
      const c = next.chunk !== undefined ? next.chunk : openDoc?.chunkId ?? null;
      if (q) params.set("q", q);
      if (a) params.set("area", a);
      if (s && s !== "relevance") params.set("sort", s);
      if (p && p > 1) params.set("page", String(p));
      if (d) params.set("doc", d);
      if (c) params.set("chunk", c);
      const qs = params.toString();
      router.replace(qs ? `/buscar?${qs}` : "/buscar", { scroll: false });
    },
    [debouncedQuery, selectedArea, sort, page, openDoc, router],
  );

  // Load stats once (silent failure — strip is hidden if error)
  useEffect(() => {
    let alive = true;
    setStatsLoading(true);
    authFetch("/api/documents/stats")
      .then((r: Response) => (r.ok ? r.json() : null))
      .then((data: KBStats | null) => {
        if (alive && data) setStats(data);
      })
      .catch(() => {})
      .finally(() => alive && setStatsLoading(false));
    return () => {
      alive = false;
    };
  }, [authFetch]);

  // Debounce query input
  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedQuery(query.trim());
      if (query.trim() !== debouncedQuery) setPage(1);
    }, 350);
    return () => clearTimeout(t);
  }, [query, debouncedQuery]);

  // Run search
  const runSearch = useCallback(async () => {
    if (debouncedQuery.length < 2) {
      setResults([]);
      setTotal(0);
      setTotalPages(1);
      setSearched(false);
      return;
    }
    setLoading(true);
    try {
      const body = {
        query: debouncedQuery,
        filters: selectedArea ? { areas: [selectedArea] } : null,
        sort,
        page,
        per_page: PER_PAGE,
      };
      const res = await authFetch("/api/search/advanced", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        toast.error("No se pudo realizar la búsqueda.");
        setResults([]);
        return;
      }
      const data = (await res.json()) as PaginatedSearchResponse;
      setResults(data.results);
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setSearched(true);
    } catch (err) {
      console.error(err);
      toast.error("Error de conexión.");
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, selectedArea, sort, page, authFetch]);

  useEffect(() => {
    runSearch();
  }, [runSearch]);

  // Push URL on relevant state changes (after search runs)
  useEffect(() => {
    writeUrl({});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedQuery, selectedArea, sort, page, openDoc]);

  const handleExport = useCallback(async () => {
    if (!debouncedQuery) return;
    if (!hasPdfExport) {
      setShowUpsell(true);
      return;
    }
    setExporting(true);
    try {
      const params = new URLSearchParams({ q: debouncedQuery });
      if (selectedArea) params.set("area", selectedArea);
      const res = await authFetch(`/api/export/search-results/pdf?${params}`);
      if (!res.ok) {
        toast.error("No se pudo exportar. Intentá nuevamente.");
        return;
      }
      const blob = await res.blob();
      const cd = res.headers.get("content-disposition");
      const slug = debouncedQuery.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40);
      downloadBlob(blob, `busqueda-${slug || "resultados"}.pdf`, cd);
      toast.success("Resultados exportados");
    } catch {
      toast.error("No se pudo exportar. Intentá nuevamente.");
    } finally {
      setExporting(false);
    }
  }, [debouncedQuery, selectedArea, hasPdfExport, authFetch]);

  // ESC closes drawer is handled inside drawer; here we just unmount
  const closeDrawer = useCallback(() => setOpenDoc(null), []);

  const browseMode = !searched && !loading;

  return (
    <div className="max-w-6xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12">
      {/* Hero */}
      <div className="text-center mb-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-[11px] uppercase tracking-wider mb-4">
          <Database className="w-3.5 h-3.5" />
          Buscador público · sin IA
        </div>
        <h1 className="font-['Newsreader'] text-4xl sm:text-5xl font-bold text-on-surface mb-2">
          Corpus jurídico del Perú
        </h1>
        <p className="text-sm sm:text-base text-on-surface/60 max-w-2xl mx-auto">
          Buscá leyes, decretos, jurisprudencia y normativa peruana indexada. Filtrá por
          área del derecho, copiá citas formateadas y compartí enlaces directos a un
          artículo.
        </p>
      </div>

      {/* KB stats strip — kept for telemetry tests */}
      {browseMode && (
        <div className="flex justify-center mb-6">
          {statsLoading ? (
            <div
              data-testid="kb-stats-skeleton"
              className="h-6 w-64 bg-on-surface/5 rounded animate-pulse"
            />
          ) : (
            stats && (
              <div
                data-testid="kb-stats-strip"
                className="text-xs text-on-surface/60 flex items-center gap-3"
              >
                <span>
                  <strong className="text-on-surface">
                    {stats.total_documents.toLocaleString("es-PE")}
                  </strong>{" "}
                  documentos
                </span>
                <span className="text-on-surface/30">·</span>
                <span>
                  <strong className="text-on-surface">
                    {stats.total_chunks.toLocaleString("es-PE")}
                  </strong>{" "}
                  fragmentos
                </span>
                <span className="text-on-surface/30">·</span>
                <span>29 áreas</span>
              </div>
            )
          )}
        </div>
      )}

      {/* Search box */}
      <div className="relative mb-4">
        <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-on-surface/40 pointer-events-none" />
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

      {/* Toolbar — filters toggle + sort + export */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <button
          type="button"
          onClick={() => setShowFilters((v) => !v)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs text-on-surface/70 border border-outline-variant hover:border-primary/40"
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          Filtros {selectedArea && <span className="text-primary">· 1</span>}
        </button>

        <div className="flex items-center gap-3">
          {searched && (
            <p className="text-xs text-on-surface/50">
              <strong className="text-on-surface">{total.toLocaleString("es-PE")}</strong>{" "}
              resultado{total === 1 ? "" : "s"}
            </p>
          )}
          <label className="flex items-center gap-1.5 text-xs text-on-surface/60">
            <span className="text-[10px] uppercase tracking-wider text-on-surface/40">
              Orden
            </span>
            <select
              value={sort}
              onChange={(e) => {
                setSort(e.target.value as SortMode);
                setPage(1);
              }}
              className="bg-surface border border-outline-variant rounded px-2 py-1 text-xs text-on-surface focus:outline-none focus:border-primary/60"
            >
              <option value="relevance">Relevancia</option>
              <option value="date_desc">Más recientes</option>
              <option value="date_asc">Más antiguos</option>
            </select>
          </label>
          {user && searched && results.length > 0 && (
            <button
              type="button"
              onClick={handleExport}
              disabled={exporting}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs text-on-surface/70 border border-outline-variant hover:border-primary/40 disabled:opacity-50"
              aria-label="Exportar resultados a PDF"
            >
              {exporting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5" />
              )}
              Exportar resultados
            </button>
          )}
        </div>
      </div>

      {/* Area chips (collapsible) */}
      {showFilters && (
        <div className="flex flex-wrap items-center gap-2 mb-6 p-3 bg-surface-container-low border border-outline-variant rounded-lg">
          <span className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-on-surface/40 mr-1">
            <Filter className="w-3 h-3" />
            Área del derecho
          </span>
          <button
            onClick={() => {
              setSelectedArea("");
              setPage(1);
            }}
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
                onClick={() => {
                  setSelectedArea(active ? "" : a.id);
                  setPage(1);
                }}
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
      )}

      {/* Results / states */}
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
            Sin resultados para &quot;{debouncedQuery}&quot;
            {selectedArea && " en esta área"}.
          </p>
          <p className="text-xs text-on-surface/30 mt-1">
            Probá con sinónimos o quitá el filtro de área.
          </p>
        </div>
      )}

      {!loading && !searched && (
        <div className="bg-surface-container-low border border-outline-variant rounded-lg p-6">
          <p className="text-[10px] uppercase tracking-wider text-on-surface/40 mb-3 flex items-center gap-1.5">
            <SearchIcon className="w-3 h-3" />
            Búsquedas de ejemplo
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {EXAMPLE_QUERIES.map((ex) => {
              const meta = LEGAL_AREAS.find((a) => a.id === ex.area);
              return (
                <button
                  key={ex.query}
                  onClick={() => {
                    setQuery(ex.query);
                    if (ex.area) setSelectedArea(ex.area);
                    setPage(1);
                  }}
                  className="text-left bg-surface border border-outline-variant hover:border-primary/40 hover:shadow-sm rounded-md p-3 transition-all group"
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <span className="text-sm font-medium text-on-surface group-hover:text-primary transition-colors">
                      {ex.query}
                    </span>
                    {meta && (
                      <span
                        className={`shrink-0 flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full bg-surface-container-low border border-outline-variant ${meta.color}`}
                      >
                        {meta.name}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-on-surface/50 leading-relaxed">
                    {ex.hint}
                  </p>
                </button>
              );
            })}
          </div>
          <p className="text-[11px] text-on-surface/40 mt-4 leading-relaxed">
            Tip: hacé clic en cualquier resultado para abrir el documento completo,
            navegar entre sus artículos y copiar la cita ya formateada en estilo
            peruano. Usá el botón <strong>Filtros</strong> para acotar por área del
            derecho.
          </p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-3">
          {results.map((r) => (
            <ResultCard
              key={r.id}
              result={r}
              query={debouncedQuery}
              onOpen={() => setOpenDoc({ docId: r.document_id, chunkId: r.id })}
            />
          ))}
          <Pagination
            page={page}
            totalPages={totalPages}
            onChange={(p) => {
              setPage(p);
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
          />
        </div>
      )}

      {openDoc && (
        <DocumentDrawer
          documentId={openDoc.docId}
          initialChunkId={openDoc.chunkId}
          query={debouncedQuery}
          onClose={closeDrawer}
        />
      )}

      {showUpsell && (
        <UpsellModal feature="pdf_export" onClose={() => setShowUpsell(false)} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page wrapper — Suspense required because BuscarContent uses useSearchParams
// ---------------------------------------------------------------------------

function BuscarShell() {
  const { user, isLoading } = useAuth();
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
            utilitySlot={
              <div className="hidden md:flex">
                <ShellUtilityActions />
              </div>
            }
          />
        )}
        <BuscarContent />
      </div>
    </Layout>
  );
}

export default function BuscarPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-background text-on-surface">
          <Loader2 className="w-5 h-5 animate-spin text-primary" />
        </div>
      }
    >
      <BuscarShell />
    </Suspense>
  );
}
