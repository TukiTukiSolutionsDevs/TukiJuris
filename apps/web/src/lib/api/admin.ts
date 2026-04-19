/**
 * Admin API client — thin wrappers around authFetch for admin-saas-panel endpoints.
 *
 * Pattern: mirrors the existing admin/page.tsx approach — plain fetch wrappers
 * that accept authFetch from useAuth(). No external state management library.
 */

export interface RevenueBreakdownItem {
  plan: string;
  display_name: string;
  org_count: number;
  revenue_cents: number;
}

export interface RevenueData {
  source: string;
  mrr_cents: number;
  arr_cents: number;
  breakdown: RevenueBreakdownItem[];
}

export interface BYOKItem {
  user_id: string;
  user_email: string;
  provider: string;
  is_active: boolean;
  api_key_hint: string;
  last_rotation_at: string | null;
}

export interface BYOKPage {
  items: BYOKItem[];
  total: number;
  page: number;
  per_page: number;
}

export interface UserRow {
  id: string;
  email: string;
  full_name?: string;
  plan: string;
  org_name?: string;
  queries_this_month: number;
  created_at: string;
  is_admin?: boolean;
  last_active: string | null;   // NEW
  byok_count: number;           // NEW
}

export interface UsersPage {
  users: UserRow[];
  total: number;
  page: number;
  per_page: number;
}

type AuthFetch = (input: RequestInfo, init?: RequestInit) => Promise<Response>;

export async function fetchRevenue(authFetch: AuthFetch): Promise<RevenueData> {
  const res = await authFetch("/api/admin/revenue");
  if (!res.ok) {
    const err = new Error(`fetchRevenue failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<RevenueData>;
}

export async function fetchBYOK(
  authFetch: AuthFetch,
  page = 1,
  perPage = 20,
  provider?: string,
): Promise<BYOKPage> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });
  if (provider) params.set("provider", provider);

  const res = await authFetch(`/api/admin/byok?${params}`);
  if (!res.ok) {
    const err = new Error(`fetchBYOK failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<BYOKPage>;
}

export async function fetchUsers(
  authFetch: AuthFetch,
  page = 1,
  perPage = 20,
  q?: string,
): Promise<UsersPage> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });
  if (q) params.set("search", q);

  const res = await authFetch(`/api/admin/users?${params}`);
  if (!res.ok) {
    const err = new Error(`fetchUsers failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<UsersPage>;
}
