"use client";

import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Bell,
  CheckCheck,
  CreditCard,
  Info,
  Loader2,
  Trash2,
  UserPlus,
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { AppLayout } from "@/components/AppLayout";
import {
  deleteNotification,
  getUnreadCount,
  listNotifications,
  markAllAsRead,
  markAsRead,
  type NotificationOut,
  type NotificationType,
} from "@/lib/api/notifications";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const POLL_INTERVAL_MS = 30_000;
const PER_PAGE_DEFAULT = 20;
const PER_PAGE_CHIPS = 100; // DR-8: larger page when type chips active

const TYPE_CHIPS: { type: NotificationType; label: string }[] = [
  { type: "usage_alert", label: "Uso" },
  { type: "invite", label: "Invitaciones" },
  { type: "system", label: "Sistema" },
  { type: "billing", label: "Facturación" },
  { type: "welcome", label: "Bienvenida" },
];

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

function typeIcon(type: NotificationType) {
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

export default function NotificacionesPage() {
  const { authFetch } = useAuth();

  const [notifications, setNotifications] = useState<NotificationOut[]>([]);
  const [page, setPage] = useState(1);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [activeChips, setActiveChips] = useState<Set<NotificationType>>(new Set());
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toastError, setToastError] = useState<string | null>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Derived
  const effectivePerPage = activeChips.size > 0 ? PER_PAGE_CHIPS : PER_PAGE_DEFAULT;
  const totalPages = Math.max(1, Math.ceil(total / effectivePerPage));
  const filteredList =
    activeChips.size === 0
      ? notifications
      : notifications.filter((n) => activeChips.has(n.type));

  const isAllEmpty = total === 0 && !unreadOnly && activeChips.size === 0;
  const isFilterEmpty = !isAllEmpty && filteredList.length === 0;

  // ---------------------------------------------------------------------------
  // Toast helper
  // ---------------------------------------------------------------------------

  const showToast = useCallback((msg: string) => {
    setToastError(msg);
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(() => setToastError(null), 4000);
  }, []);

  // ---------------------------------------------------------------------------
  // Fetch
  // ---------------------------------------------------------------------------

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listNotifications(authFetch, {
        page,
        per_page: effectivePerPage,
        unread_only: unreadOnly,
      });
      setNotifications(data.notifications);
      setTotal(data.total);
    } catch {
      setError("No se pudieron cargar las notificaciones.");
    } finally {
      setLoading(false);
    }
  }, [authFetch, page, effectivePerPage, unreadOnly]);

  const refreshUnreadCount = useCallback(async () => {
    try {
      await getUnreadCount(authFetch);
    } catch {
      // non-blocking
    }
  }, [authFetch]);

  // ---------------------------------------------------------------------------
  // Effects
  // ---------------------------------------------------------------------------

  // Initial load + re-fetch when deps change
  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  // 30s polling (NF-9)
  useEffect(() => {
    const id = setInterval(() => void fetchData(), POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchData]);

  // Cleanup toast timer on unmount
  useEffect(() => {
    return () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Filter handlers
  // ---------------------------------------------------------------------------

  const handleUnreadToggle = () => {
    setUnreadOnly((prev) => !prev);
    setPage(1);
  };

  const handleChipToggle = (type: NotificationType) => {
    setActiveChips((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
    setPage(1);
  };

  const handleClearFilters = () => {
    setUnreadOnly(false);
    setActiveChips(new Set());
    setPage(1);
  };

  // ---------------------------------------------------------------------------
  // Mutations
  // ---------------------------------------------------------------------------

  const handleMarkRead = async (id: string) => {
    // Optimistic update (NF-13)
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
    );
    try {
      await markAsRead(authFetch, id);
      void refreshUnreadCount();
    } catch {
      // silently ignore — optimistic update stays
    }
  };

  const handleMarkAllRead = async () => {
    // Optimistic update (NF-14)
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    try {
      await markAllAsRead(authFetch);
      void refreshUnreadCount();
    } catch {
      // silently ignore
    }
  };

  const handleDelete = async (id: string) => {
    // Snapshot for rollback (NF-15)
    const snapshot = [...notifications];
    setNotifications((prev) => prev.filter((n) => n.id !== id));
    try {
      await deleteNotification(authFetch, id);
      void refreshUnreadCount();
    } catch {
      // Rollback + toast
      setNotifications(snapshot);
      showToast("No se pudo eliminar la notificación.");
    }
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <AppLayout>
      <div className="flex flex-col h-full">
        {/* Toast error */}
        {toastError && (
          <div
            role="alert"
            className="fixed top-4 right-4 z-50 bg-red-600 text-white text-sm px-4 py-2.5 rounded-xl shadow-lg"
          >
            {toastError}
          </div>
        )}

        {/* Page header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-[rgba(79,70,51,0.12)]">
          <h1 className="text-xl font-semibold text-on-surface">Notificaciones</h1>
          <button
            onClick={() => void handleMarkAllRead()}
            className="flex items-center gap-1.5 text-sm text-amber-400 hover:text-amber-300 transition-colors"
            aria-label="Marcar todas como leídas"
          >
            <CheckCheck className="w-4 h-4" />
            Marcar todas como leídas
          </button>
        </div>

        {/* Filters row */}
        <div className="flex flex-wrap items-center gap-2 px-6 py-3 border-b border-[rgba(79,70,51,0.08)]">
          {/* Unread toggle */}
          <button
            onClick={handleUnreadToggle}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              unreadOnly
                ? "bg-amber-500/20 border-amber-500/40 text-amber-300"
                : "border-[rgba(79,70,51,0.2)] text-on-surface/60 hover:text-on-surface hover:border-on-surface/30"
            }`}
            aria-pressed={unreadOnly}
          >
            Sin leer
          </button>

          {/* Type chips (DR-8: client-side filtering) */}
          {TYPE_CHIPS.map(({ type, label }) => (
            <button
              key={type}
              onClick={() => handleChipToggle(type)}
              title="Filtros aplicados a las notificaciones cargadas."
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                activeChips.has(type)
                  ? "bg-primary/20 border-primary/40 text-primary"
                  : "border-[rgba(79,70,51,0.2)] text-on-surface/60 hover:text-on-surface hover:border-on-surface/30"
              }`}
              aria-pressed={activeChips.has(type)}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Content area */}
        <div className="flex-1 overflow-y-auto">
          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 text-amber-500 animate-spin" />
            </div>
          )}

          {/* Error */}
          {!loading && error && (
            <div className="px-6 py-8 text-center text-sm text-red-400">{error}</div>
          )}

          {/* All-empty state (NF-17) */}
          {!loading && !error && isAllEmpty && (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <Image
                src="/brand/logo-full.png"
                alt="TukiJuris"
                width={160}
                height={48}
                className="opacity-20"
              />
              <p className="text-sm text-on-surface/40">No tenés notificaciones todavía.</p>
            </div>
          )}

          {/* Filter-empty state (NF-18) */}
          {!loading && !error && isFilterEmpty && (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <p className="text-sm text-on-surface/50">
                No hay notificaciones que coincidan con el filtro.
              </p>
              <button
                onClick={handleClearFilters}
                className="text-xs text-primary hover:text-primary/80 underline underline-offset-2"
              >
                Limpiar filtros
              </button>
            </div>
          )}

          {/* Notification list */}
          {!loading && !error && !isAllEmpty && filteredList.length > 0 && (
            <ul>
              {filteredList.map((n) => (
                <li
                  key={n.id}
                  className={`flex gap-3 px-6 py-4 border-b border-[rgba(79,70,51,0.08)] transition-colors hover:bg-surface-container-low/40 ${
                    !n.is_read ? "bg-surface-container-low/20" : ""
                  }`}
                >
                  {/* Icon */}
                  <div className="mt-0.5 shrink-0">{typeIcon(n.type)}</div>

                  {/* Body */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p
                          className={`text-sm font-medium truncate ${
                            !n.is_read ? "text-on-surface" : "text-on-surface/70"
                          }`}
                        >
                          {n.action_url ? (
                            <a
                              href={n.action_url}
                              className="hover:underline"
                              onClick={() => { if (!n.is_read) void handleMarkRead(n.id); }}
                            >
                              {n.title}
                            </a>
                          ) : (
                            n.title
                          )}
                        </p>
                        <p className="text-xs text-on-surface/50 line-clamp-2 mt-0.5">
                          {n.message}
                        </p>
                      </div>

                      {/* Meta: time + unread dot */}
                      <div className="flex items-center gap-1.5 shrink-0">
                        <span className="text-[10px] text-on-surface/40">
                          {timeAgo(n.created_at)}
                        </span>
                        {!n.is_read && (
                          <span
                            aria-label="No leída"
                            className="w-2 h-2 rounded-full bg-amber-500 shrink-0"
                          />
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-3 mt-2">
                      {!n.is_read && (
                        <button
                          onClick={() => void handleMarkRead(n.id)}
                          className="text-[11px] text-amber-400 hover:text-amber-300 transition-colors"
                          aria-label="Marcar leída"
                        >
                          Marcar leída
                        </button>
                      )}
                      <button
                        onClick={() => void handleDelete(n.id)}
                        className="text-[11px] text-on-surface/30 hover:text-red-400 transition-colors flex items-center gap-0.5"
                        aria-label="Eliminar notificación"
                      >
                        <Trash2 className="w-3 h-3" />
                        Eliminar
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Pagination (NF-8) */}
        {!loading && !isAllEmpty && (
          <div className="flex items-center justify-center gap-4 px-6 py-4 border-t border-[rgba(79,70,51,0.12)]">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="text-sm px-3 py-1.5 rounded-lg border border-[rgba(79,70,51,0.2)] text-on-surface/60 hover:text-on-surface hover:border-on-surface/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              aria-label="Página anterior"
            >
              Anterior
            </button>

            <span className="text-sm text-on-surface/60">
              Página {page} de {totalPages}
            </span>

            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="text-sm px-3 py-1.5 rounded-lg border border-[rgba(79,70,51,0.2)] text-on-surface/60 hover:text-on-surface hover:border-on-surface/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              aria-label="Página siguiente"
            >
              Siguiente
            </button>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
