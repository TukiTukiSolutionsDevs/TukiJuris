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

export interface InvoiceRow {
  id: string;
  org_id: string;
  provider: string;
  provider_charge_id: string;
  status: string;
  currency: string;
  base_amount: string;
  seats_count: number;
  seat_amount: string;
  subtotal_amount: string;
  tax_amount: string;
  total_amount: string;
  plan: string;
  paid_at: string | null;
  failed_at: string | null;
  refunded_at: string | null;
  voided_at: string | null;
  refund_reason: string | null;
  void_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvoicesPage {
  items: InvoiceRow[];
  total: number;
  page: number;
  per_page: number;
}

export interface TrialAdminRow {
  id: string;
  org_id: string;
  status: string;
  trial_ends_at: string;
  charge_amount: string;
  currency: string;
  provider: string | null;
  charge_id: string | null;
  charged_at: string | null;
  created_at: string;
}

export interface TrialsAdminPage {
  items: TrialAdminRow[];
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

export async function fetchAdminInvoices(
  authFetch: AuthFetch,
  page = 1,
  perPage = 20,
  invoiceStatus?: string,
  orgId?: string,
): Promise<InvoicesPage> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });
  if (invoiceStatus) params.set("status", invoiceStatus);
  if (orgId) params.set("org_id", orgId);

  const res = await authFetch(`/api/admin/invoices?${params}`);
  if (!res.ok) {
    const err = new Error(`fetchAdminInvoices failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<InvoicesPage>;
}

export async function fetchAdminTrials(
  authFetch: AuthFetch,
  page = 1,
  perPage = 20,
  status?: string,
): Promise<TrialsAdminPage> {
  const params = new URLSearchParams({ page: String(page), per_page: String(perPage) });
  if (status) params.set("status", status);
  const res = await authFetch(`/api/admin/trials?${params}`);
  if (!res.ok) {
    const err = new Error(`fetchAdminTrials failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<TrialsAdminPage>;
}

export async function patchAdminTrial(
  authFetch: AuthFetch,
  id: string,
  body: { status: string },
): Promise<TrialAdminRow> {
  const res = await authFetch(`/api/admin/trials/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = new Error(`patchAdminTrial failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<TrialAdminRow>;
}
