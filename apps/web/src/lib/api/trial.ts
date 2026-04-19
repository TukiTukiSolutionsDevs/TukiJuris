/**
 * Trial API client — user-facing trial endpoints.
 */

export type TrialStatus = "active" | "expired" | "converted" | "cancelled" | "charged";

export interface TrialRead {
  id: string;
  org_id: string;
  status: TrialStatus;
  trial_ends_at: string;
  charge_amount: string;
  currency: string;
  provider: string | null;
  created_at: string;
}

type AuthFetch = (input: RequestInfo, init?: RequestInit) => Promise<Response>;

export async function fetchCurrentTrial(authFetch: AuthFetch): Promise<TrialRead | null> {
  const res = await authFetch("/api/trials/current");
  if (res.status === 404) return null;
  if (!res.ok) {
    const err = new Error(`fetchCurrentTrial failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<TrialRead>;
}

export async function startTrial(authFetch: AuthFetch): Promise<TrialRead> {
  const res = await authFetch("/api/trials", { method: "POST" });
  if (!res.ok) {
    const err = new Error(`startTrial failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<TrialRead>;
}

export async function cancelTrial(authFetch: AuthFetch, id: string): Promise<void> {
  const res = await authFetch(`/api/trials/${id}`, { method: "DELETE" });
  if (!res.ok) {
    const err = new Error(`cancelTrial failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
}

export async function addCardToTrial(
  authFetch: AuthFetch,
  id: string,
  cardToken: string,
): Promise<TrialRead> {
  const res = await authFetch(`/api/trials/${id}/add-card`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ card_token: cardToken }),
  });
  if (!res.ok) {
    const err = new Error(`addCardToTrial failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<TrialRead>;
}
