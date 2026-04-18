export type EndpointMethod = "GET" | "POST" | "PUT" | "DELETE";

export interface EndpointDoc {
  method: EndpointMethod;
  path: string;
  scope?: string;
  description: string;
}

export const ENDPOINTS: { group: string; items: EndpointDoc[] }[] = [
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
