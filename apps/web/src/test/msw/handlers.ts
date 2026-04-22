import { http, HttpResponse } from "msw";

// ---------------------------------------------------------------------------
// Default access token payload (non-admin user)
// ---------------------------------------------------------------------------
const ACCESS_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." +
  btoa(JSON.stringify({ sub: "user-1", email: "user@test.com", is_admin: false, exp: 9999999999 }))
    .replace(/=/g, "") +
  ".sig";

const ADMIN_ACCESS_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." +
  btoa(JSON.stringify({ sub: "admin-1", email: "admin@test.com", is_admin: true, exp: 9999999999 }))
    .replace(/=/g, "") +
  ".sig";

export const handlers = [
  // POST /api/auth/login
  http.post("/api/auth/login", () =>
    HttpResponse.json({ access_token: ACCESS_TOKEN, token_type: "bearer", expires_in: 900 })
  ),

  // POST /api/auth/register
  http.post("/api/auth/register", () =>
    HttpResponse.json({ access_token: ACCESS_TOKEN, token_type: "bearer", expires_in: 900 })
  ),

  // POST /api/auth/refresh — success by default
  http.post("/api/auth/refresh", () =>
    HttpResponse.json({ access_token: ACCESS_TOKEN, token_type: "bearer", expires_in: 900 })
  ),

  // POST /api/auth/logout
  http.post("/api/auth/logout", () => new HttpResponse(null, { status: 204 })),

  // GET /api/auth/me
  http.get("/api/auth/me", () =>
    HttpResponse.json({
      id: "user-1",
      email: "user@test.com",
      is_admin: false,
      onboarding_completed: false,
      plan: "free",
      entitlements: ["chat"],
    })
  ),

  // GET /api/auth/me/permissions
  http.get("/api/auth/me/permissions", () =>
    HttpResponse.json({ permissions: [] })
  ),

  // POST /api/auth/me/onboarding
  http.post("/api/auth/me/onboarding", () => new HttpResponse(null, { status: 204 })),

  // POST /api/auth/logout-all
  http.post("/api/auth/logout-all", () => new HttpResponse(null, { status: 204 })),

  // POST /api/auth/change-password — FCB-14: default 204 success
  http.post("/api/auth/change-password", () => new HttpResponse(null, { status: 204 })),
];

// ---------------------------------------------------------------------------
// Named override factories — use in individual tests via server.use(...)
// ---------------------------------------------------------------------------
export const authHandlers = {
  refreshFailure: () =>
    http.post("/api/auth/refresh", () =>
      new HttpResponse(null, { status: 401 })
    ),

  loginFailure: () =>
    http.post("/api/auth/login", () =>
      HttpResponse.json({ detail: "Credenciales inválidas" }, { status: 401 })
    ),

  adminLogin: () =>
    http.post("/api/auth/login", () =>
      HttpResponse.json({ access_token: ADMIN_ACCESS_TOKEN, token_type: "bearer", expires_in: 900 })
    ),

  adminRefresh: () =>
    http.post("/api/auth/refresh", () =>
      HttpResponse.json({ access_token: ADMIN_ACCESS_TOKEN, token_type: "bearer", expires_in: 900 })
    ),

  // FCB-15: per-test error override for POST /api/auth/change-password
  changePasswordError: (
    detail: string | { code?: string; auth_provider?: string } | null,
    status = 400,
  ) =>
    http.post("/api/auth/change-password", () =>
      HttpResponse.json({ detail }, { status })
    ),
};

export { ACCESS_TOKEN, ADMIN_ACCESS_TOKEN };
