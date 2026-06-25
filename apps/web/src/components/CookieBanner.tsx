"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Cookie } from "lucide-react";

const STORAGE_KEY = "tk_cookies_ack";

/**
 * Lightweight cookie notice.
 *
 * TukiJuris only sets strictly-essential cookies (refresh_token, tk_session,
 * tk_admin). No analytics, no marketing, no third-party trackers — so this
 * is an informational notice, not a granular consent manager.
 *
 * The user can dismiss it; the choice persists in localStorage until cleared.
 * No cookie is set by this banner itself.
 */
export function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const acked = window.localStorage.getItem(STORAGE_KEY);
      if (!acked) setVisible(true);
    } catch {
      setVisible(true);
    }
  }, []);

  const accept = () => {
    try {
      window.localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      /* localStorage may be disabled — fail silently */
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-label="Aviso de cookies"
      className="fixed bottom-4 inset-x-4 sm:inset-x-auto sm:right-4 sm:max-w-md z-[100] rounded-xl bg-surface-container border border-ghost-border shadow-2xl p-4 sm:p-5 text-sm text-on-surface-variant"
    >
      <div className="flex items-start gap-3">
        <Cookie className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" aria-hidden />
        <div className="flex-1">
          <p className="font-medium text-on-surface mb-1">Solo cookies esenciales</p>
          <p>
            Usamos cookies estrictamente necesarias para mantener tu sesión. No usamos cookies de
            publicidad ni rastreo. Lee más en{" "}
            <Link href="/privacy" className="text-primary underline">
              nuestra política de privacidad
            </Link>
            .
          </p>
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={accept}
              className="px-3 py-1.5 rounded-lg bg-primary text-on-primary text-xs font-bold hover:opacity-90 transition-opacity"
            >
              Entendido
            </button>
            <Link
              href="/privacy"
              className="px-3 py-1.5 rounded-lg border border-ghost-border text-xs hover:text-primary hover:border-primary/30 transition-colors"
            >
              Más información
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
