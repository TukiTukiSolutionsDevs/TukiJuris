/**
 * Trial API client — user-facing trial endpoints.
 */

export type TrialStatus =
  | "active"
  | "charged"
  | "charge_failed"
  | "downgraded"
  | "canceled_pending"
  | "canceled";

export interface Trial {
  id: string;
  user_id: string;
  plan_code: string;
  status: TrialStatus;
  started_at: string;
  ends_at: string;
  days_remaining: number;
  card_added_at: string | null;
  provider: string | null;
  charged_at: string | null;
  charge_failed_at: string | null;
  charge_failure_reason: string | null;
  retry_count: number;
  canceled_at: string | null;
  canceled_by_user: boolean;
  downgraded_at: string | null;
  subscription_id: string | null;
}

type AuthFetch = (input: RequestInfo, init?: RequestInit) => Promise<Response>;

export async function fetchCurrentTrial(authFetch: AuthFetch): Promise<Trial | null> {
  const res = await authFetch("/api/trials/me");
  if (res.status === 404) return null;
  if (!res.ok) {
    const err = new Error(`fetchCurrentTrial failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  const data = await res.json();
  if (data === null) return null;
  return data as Trial;
}

export async function startTrial(
  authFetch: AuthFetch,
  plan_code = "pro",
): Promise<Trial> {
  const res = await authFetch("/api/trials/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ plan_code }),
  });
  if (!res.ok) {
    const err = new Error(`startTrial failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<Trial>;
}

export async function cancelTrial(authFetch: AuthFetch, id: string): Promise<Trial> {
  const res = await authFetch(`/api/trials/${id}/cancel`, { method: "POST" });
  if (!res.ok) {
    const err = new Error(`cancelTrial failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<Trial>;
}

export interface AddCardBody {
  provider: string;
  token_id: string;
  customer_info: {
    email: string;
    first_name: string;
    last_name: string;
  };
}

export async function addCardToTrial(
  authFetch: AuthFetch,
  body: AddCardBody,
): Promise<Trial> {
  const res = await authFetch("/api/trials/add-card", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = new Error(`addCardToTrial failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<Trial>;
}
