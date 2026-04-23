/**
 * Notifications API client — thin wrappers around authFetch.
 *
 * Pattern: mirrors apps/web/src/lib/api/admin.ts — plain fetch wrappers
 * that accept authFetch from useAuth(). No external state management.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type NotificationType =
  | "usage_alert"
  | "invite"
  | "system"
  | "billing"
  | "welcome";

export interface NotificationOut {
  id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  action_url: string | null;
  extra_data: Record<string, unknown> | null;
  created_at: string;
}

export interface NotificationListResponse {
  notifications: NotificationOut[];
  /** Global unread count (not affected by filters). */
  unread_count: number;
  /** Total filtered count (used for pagination). */
  total: number;
}

type AuthFetch = (input: string, init?: RequestInit) => Promise<Response>;

// ---------------------------------------------------------------------------
// NF-1: listNotifications
// ---------------------------------------------------------------------------

export async function listNotifications(
  authFetch: AuthFetch,
  {
    page = 1,
    per_page = 20,
    unread_only = false,
  }: { page?: number; per_page?: number; unread_only?: boolean } = {},
): Promise<NotificationListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(per_page),
    unread_only: String(unread_only),
  });
  const res = await authFetch(`/api/notifications/?${params}`);
  if (!res.ok) {
    const err = new Error(`listNotifications failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<NotificationListResponse>;
}

// ---------------------------------------------------------------------------
// NF-2: getUnreadCount
// ---------------------------------------------------------------------------

export async function getUnreadCount(
  authFetch: AuthFetch,
): Promise<{ count: number }> {
  const res = await authFetch("/api/notifications/unread-count");
  if (!res.ok) {
    const err = new Error(`getUnreadCount failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<{ count: number }>;
}

// ---------------------------------------------------------------------------
// NF-3: markAsRead (PUT)
// ---------------------------------------------------------------------------

export async function markAsRead(
  authFetch: AuthFetch,
  id: string,
): Promise<{ status: string }> {
  const res = await authFetch(`/api/notifications/${id}/read`, {
    method: "PUT",
  });
  if (!res.ok) {
    const err = new Error(`markAsRead failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<{ status: string }>;
}

// ---------------------------------------------------------------------------
// NF-4: markAllAsRead (PUT)
// ---------------------------------------------------------------------------

export async function markAllAsRead(
  authFetch: AuthFetch,
): Promise<{ status: string; updated: number }> {
  const res = await authFetch("/api/notifications/read-all", {
    method: "PUT",
  });
  if (!res.ok) {
    const err = new Error(`markAllAsRead failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<{ status: string; updated: number }>;
}

// ---------------------------------------------------------------------------
// NF-5: deleteNotification (DELETE) — throws on 404
// ---------------------------------------------------------------------------

export async function deleteNotification(
  authFetch: AuthFetch,
  id: string,
): Promise<{ status: string }> {
  const res = await authFetch(`/api/notifications/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = new Error(`deleteNotification failed: ${res.status}`);
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return res.json() as Promise<{ status: string }>;
}
