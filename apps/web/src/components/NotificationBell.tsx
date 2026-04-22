"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { authFetch } from "@/lib/auth/authClient";
import {
  AlertTriangle,
  Bell,
  CheckCheck,
  CreditCard,
  Info,
  Loader2,
  UserPlus,
  X,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const POLL_INTERVAL_MS = 30_000;
const DROPDOWN_MAX = 10;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Notification {
  id: string;
  type: "usage_alert" | "invite" | "system" | "billing" | "welcome";
  title: string;
  message: string;
  is_read: boolean;
  action_url: string | null;
  extra_data: Record<string, unknown> | null;
  created_at: string;
}

interface NotificationListResponse {
  notifications: Notification[];
  unread_count: number;
  total: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function timeAgo(isoString: string): string {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  if (diffMin < 1) return "ahora";
  if (diffMin < 60) return `${diffMin}m`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d`;
}

function typeIcon(type: Notification["type"]) {
  switch (type) {
    case "usage_alert":
      return <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />;
    case "invite":
      return <UserPlus className="w-4 h-4 text-blue-400 shrink-0" />;
    case "billing":
      return <CreditCard className="w-4 h-4 text-green-400 shrink-0" />;
    case "welcome":
      return <Bell className="w-4 h-4 text-amber-400 shrink-0" />;
          default:
      return <Info className="w-4 h-4 text-[#9CA3AF] shrink-0" />;
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface NotificationBellProps {
  /** JWT Bearer token for authenticated API calls. */
  token: string | null;
}

export default function NotificationBell({ token }: NotificationBellProps) {
  const [open, setOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // ------------------------------------------------------------------
  // Fetch helpers
  // ------------------------------------------------------------------

  const fetchUnreadCount = useCallback(async () => {
    if (!token) return;
    try {
      const res = await authFetch(`${API_URL}/api/notifications/unread-count`);
      if (!res.ok) return;
      const data: { count: number } = await res.json();
      setUnreadCount(data.count);
    } catch {
      setUnreadCount(0);
    }
  }, [token]);

  const fetchNotifications = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await authFetch(
        `${API_URL}/api/notifications/?per_page=${DROPDOWN_MAX}`
      );
      if (!res.ok) return;
      const data: NotificationListResponse = await res.json();
      setNotifications(data.notifications);
      setUnreadCount(data.unread_count);
    } catch {
      // non-blocking
    } finally {
      setLoading(false);
    }
  }, [token]);

  // ------------------------------------------------------------------
  // Polling (every 30 s — no WebSocket needed for MVP)
  // ------------------------------------------------------------------

  useEffect(() => {
    fetchUnreadCount();
    const id = setInterval(fetchUnreadCount, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchUnreadCount]);

  // ------------------------------------------------------------------
  // Open / close dropdown
  // ------------------------------------------------------------------

  const handleToggle = () => {
    if (!open) {
      fetchNotifications();
    }
    setOpen((prev) => !prev);
  };

  // Close when clicking outside
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // ------------------------------------------------------------------
  // Actions
  // ------------------------------------------------------------------

  const markRead = async (id: string) => {
    if (!token) return;
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    );
    setUnreadCount((c) => Math.max(0, c - 1));
    try {
      await authFetch(`${API_URL}/api/notifications/${id}/read`, {
        method: "PUT",
      });
    } catch {
      // silently ignore — optimistic update already applied
    }
  };

  const markAllRead = async () => {
    if (!token) return;
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
    try {
      await authFetch(`${API_URL}/api/notifications/read-all`, {
        method: "PUT",
      });
    } catch {
      // silently ignore
    }
  };

  const handleNotificationClick = (n: Notification) => {
    if (!n.is_read) markRead(n.id);
    if (n.action_url) {
      window.location.href = n.action_url;
    }
    setOpen(false);
  };

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------

  if (!token) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell button */}
      <button
        onClick={handleToggle}
        className="control-surface relative rounded-xl p-2 text-[#9CA3AF] hover:text-white"
        aria-label="Notificaciones"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1 leading-none">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown panel */}
      {open && (
        <div className="panel-raised absolute right-0 top-full mt-2 w-80 rounded-2xl z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#1A1A22]">
            <span className="text-sm font-semibold text-gray-100">
              Notificaciones
            </span>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllRead}
                  className="flex items-center gap-1 text-xs text-amber-400 hover:text-amber-300 transition-colors"
                  title="Marcar todo como leido"
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                  Marcar todo como leido
                </button>
              )}
              <button
                onClick={() => setOpen(false)}
                className="p-0.5 text-gray-500 hover:text-gray-300 transition-colors"
                aria-label="Cerrar"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Notification list */}
          <div className="max-h-96 overflow-y-auto">
            {loading && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-5 h-5 text-amber-500 animate-spin" />
              </div>
            )}

            {!loading && notifications.length === 0 && (
              <div className="py-8 text-center text-sm text-[#6B7280]">
                Sin notificaciones
              </div>
            )}

            {!loading &&
              notifications.map((n) => (
                <button
                  key={n.id}
                  onClick={() => handleNotificationClick(n)}
                  className={`w-full text-left flex gap-3 px-4 py-3 border-b border-[#1A1A22] hover:bg-[#1A1A22] transition-colors ${
                    !n.is_read ? "bg-[#1A1A22]" : ""
                  }`}
                >
                  <div className="mt-0.5">{typeIcon(n.type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p
                        className={`text-xs font-medium truncate ${
                          !n.is_read ? "text-gray-100" : "text-gray-300"
                        }`}
                      >
                        {n.title}
                      </p>
                      <span className="text-[10px] text-[#6B7280] shrink-0">
                        {timeAgo(n.created_at)}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#9CA3AF] line-clamp-2 mt-0.5">
                      {n.message}
                    </p>
                  </div>
                  {!n.is_read && (
                    <div className="w-2 h-2 rounded-full bg-amber-500 shrink-0 mt-1.5" />
                  )}
                </button>
              ))}
          </div>

          {/* Footer */}
          <div className="px-4 py-2.5 border-t border-[#1A1A22] text-center">
            <p className="text-[10px] text-gray-600">
              {notifications.length > 0 ? `${notifications.length} notificaciones` : "Sin notificaciones pendientes"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
