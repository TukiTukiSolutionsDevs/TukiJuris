/**
 * TukiJuris JavaScript/TypeScript SDK — Legal AI API for Peruvian Law.
 *
 * Zero runtime dependencies. Uses the native fetch API (Node.js 18+, browsers, Deno, Bun).
 */

// ---------------------------------------------------------------------------
// Request option types
// ---------------------------------------------------------------------------

export interface QueryOptions {
  /** Optional area hint: "civil", "penal", "laboral", etc. */
  legalArea?: string;
  /** LLM model override. Omit to use the default. */
  model?: string;
}

export interface SearchOptions {
  /** Filter results to a specific legal area. */
  area?: string;
  /** Maximum number of results (1–50). Default 10. */
  limit?: number;
}

export interface DocumentsOptions {
  /** Filter by legal area. */
  area?: string;
  /** Maximum number of results (1–100). Default 20. */
  limit?: number;
  /** Pagination offset. Default 0. */
  offset?: number;
}

// ---------------------------------------------------------------------------
// Response types
// ---------------------------------------------------------------------------

export interface CitationItem {
  document: string;
  article: string | null;
  content: string;
  score: number | null;
}

export interface QueryResult {
  answer: string;
  citations: CitationItem[];
  area_detected: string;
  agent_used: string;
  model_used: string;
  tokens_used: number | null;
  latency_ms: number;
}

export interface SearchResultItem {
  content: string;
  document: string;
  article: string | null;
  score: number;
  legal_area: string;
}

export interface SearchResult {
  results: SearchResultItem[];
  total: number;
  query: string;
}

export interface AnalyzeResult {
  areas_detected: string[];
  analysis: string;
  model_used: string;
  latency_ms: number;
}

export interface AreaInfo {
  id: string;
  name: string;
  chunks: number;
}

export interface DocumentItem {
  id: string;
  title: string;
  document_number: string | null;
  legal_area: string | null;
  chunk_count: number | null;
}

export interface DocumentsResult {
  documents: DocumentItem[];
  total: number;
}

export interface UsageResult {
  queries_today: number;
  queries_month: number;
  limit_per_minute: number;
  key_name: string | null;
}

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export class TukiJurisError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(`TukiJuris API Error (${status}): ${detail}`);
    this.name = "TukiJurisError";
  }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export class TukiJurisClient {
  private readonly baseUrl: string;
  private readonly apiKey: string;

  /**
   * Create a TukiJuris API client.
   *
   * @param apiKey - Your TukiJuris API key (starts with ak_).
   * @param baseUrl - Override the base URL. Useful for local development.
   *
   * @example
   * const client = new TukiJurisClient("ak_your_key");
   * const result = await client.query("Requisitos para despido justificado");
   * console.log(result.answer);
   */
  constructor(apiKey: string, baseUrl?: string) {
    this.apiKey = apiKey;
    this.baseUrl = (baseUrl ?? "https://tukijuris.net.pe/api/v1").replace(/\/$/, "");
  }

  // ------------------------------------------------------------------
  // Internal request helper
  // ------------------------------------------------------------------

  private async request<T>(
    method: "GET" | "POST",
    path: string,
    body?: Record<string, unknown>,
    params?: Record<string, string>,
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`);
    if (params) {
      for (const [key, value] of Object.entries(params)) {
        url.searchParams.set(key, value);
      }
    }

    const res = await fetch(url.toString(), {
      method,
      headers: {
        "X-API-Key": this.apiKey,
        "Content-Type": "application/json",
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      let detail = res.statusText;
      try {
        const err = (await res.json()) as { detail?: string };
        if (err.detail) detail = err.detail;
      } catch {
        // ignore — use statusText as fallback
      }
      throw new TukiJurisError(res.status, detail);
    }

    return res.json() as Promise<T>;
  }

  // ------------------------------------------------------------------
  // Public methods
  // ------------------------------------------------------------------

  /**
   * Submit a legal query.
   *
   * The system classifies the question by area of Peruvian law, retrieves
   * relevant context from the knowledge base, and returns an AI-generated
   * answer with citations.
   *
   * @param query - Legal question (3–2000 characters).
   * @param options - Optional area hint and model override.
   *
   * @example
   * const result = await client.query(
   *   "Cuales son los requisitos para un despido justificado?",
   *   { legalArea: "laboral" }
   * );
   * console.log(result.answer);
   * result.citations.forEach(c => console.log(c.document, c.article));
   */
  async query(query: string, options?: QueryOptions): Promise<QueryResult> {
    const body: Record<string, unknown> = { query };
    if (options?.legalArea) body["legal_area"] = options.legalArea;
    if (options?.model) body["model"] = options.model;
    return this.request<QueryResult>("POST", "/query", body);
  }

  /**
   * Search the legal knowledge base.
   *
   * Performs hybrid BM25 + semantic search and returns ranked document
   * chunks with relevance scores.
   *
   * @param query - Search query (2–500 characters).
   * @param options - Optional area filter and result limit.
   *
   * @example
   * const { results } = await client.search("articulo 34 CTS", { area: "laboral" });
   * results.forEach(r => console.log(`[${r.score.toFixed(2)}] ${r.document}`));
   */
  async search(query: string, options?: SearchOptions): Promise<SearchResult> {
    const body: Record<string, unknown> = {
      query,
      limit: options?.limit ?? 10,
    };
    if (options?.area) body["area"] = options.area;
    return this.request<SearchResult>("POST", "/search", body);
  }

  /**
   * Analyze a legal case description.
   *
   * Returns a structured analysis covering: areas of law, applicable
   * regulations, rights, legal courses of action, deadlines, and
   * a general recommendation.
   *
   * @param caseDescription - Case description (10–5000 characters).
   * @param areas - Limit analysis to specific areas. Omit for auto-detect.
   *
   * @example
   * const result = await client.analyze(
   *   "Un empleado fue despedido verbalmente sin carta ni liquidacion...",
   *   ["laboral"]
   * );
   * console.log(result.analysis);
   */
  async analyze(caseDescription: string, areas?: string[]): Promise<AnalyzeResult> {
    const body: Record<string, unknown> = { case_description: caseDescription };
    if (areas?.length) body["areas"] = areas;
    return this.request<AnalyzeResult>("POST", "/analyze", body);
  }

  /**
   * List all available legal areas.
   *
   * Use the `id` value as `legalArea` in query() and search().
   *
   * @example
   * const areas = await client.areas();
   * areas.forEach(a => console.log(a.id, a.name));
   * // civil   Derecho Civil
   * // penal   Derecho Penal
   */
  async areas(): Promise<AreaInfo[]> {
    const data = await this.request<{ areas: AreaInfo[] }>("GET", "/areas");
    return data.areas;
  }

  /**
   * List documents in the knowledge base.
   *
   * @param options - Optional area filter, limit, and pagination offset.
   *
   * @example
   * const { documents, total } = await client.documents({ area: "tributario" });
   * console.log(`Found ${total} documents`);
   * documents.forEach(d => console.log(d.title));
   */
  async documents(options?: DocumentsOptions): Promise<DocumentsResult> {
    const params: Record<string, string> = {
      limit: String(options?.limit ?? 20),
      offset: String(options?.offset ?? 0),
    };
    if (options?.area) params["area"] = options.area;
    return this.request<DocumentsResult>("GET", "/documents", undefined, params);
  }

  /**
   * Get API key usage statistics.
   *
   * @example
   * const stats = await client.usage();
   * console.log(`Today: ${stats.queries_today} queries`);
   * console.log(`Rate limit: ${stats.limit_per_minute} req/min`);
   */
  async usage(): Promise<UsageResult> {
    return this.request<UsageResult>("GET", "/usage");
  }
}

export default TukiJurisClient;
