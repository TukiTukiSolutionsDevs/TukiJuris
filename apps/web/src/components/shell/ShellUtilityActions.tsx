"use client";

import Link from "next/link";
import { HelpCircle, Settings2 } from "lucide-react";
import { usePathname } from "next/navigation";
import NotificationBell from "@/components/NotificationBell";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/lib/auth/AuthContext";

interface ShellUtilityActionsProps {
  showSettingsLink?: boolean;
  compact?: boolean;
  showHelp?: boolean;
}

/**
 * Canonical topbar utility actions used on every workspace page.
 * Layout: [Help] [Bell] [Theme] [optional Settings]
 *
 * Buttons are 34×34 rounded-lg with outline-variant border to match the
 * Lex Aurum v3 page-header pattern.
 */
export function ShellUtilityActions({
  showSettingsLink = false,
  compact = false,
  showHelp = true,
}: ShellUtilityActionsProps) {
  const pathname = usePathname();
  const { accessToken: token } = useAuth();
  const hideSettingsLink = !showSettingsLink || pathname === "/configuracion";

  const buttonSize = compact ? "h-[34px] w-[34px]" : "h-9 w-9";
  const iconSize = "h-4 w-4";
  const buttonBase = `inline-flex ${buttonSize} items-center justify-center rounded-lg border border-outline-variant bg-transparent text-on-surface-variant transition-colors hover:border-outline hover:text-on-surface-strong`;

  return (
    <div className="flex items-center gap-1.5">
      {showHelp ? (
        <Link href="/guia" aria-label="Ayuda" title="Ayuda" className={buttonBase}>
          <HelpCircle className={iconSize} strokeWidth={1.8} />
        </Link>
      ) : null}

      <NotificationBell token={token} buttonClassName={buttonBase} />

      <ThemeToggle className={buttonBase} />

      {!hideSettingsLink ? (
        <Link
          href="/configuracion"
          aria-label="Ir a configuración"
          title="Configuración"
          className={buttonBase}
        >
          <Settings2 className={iconSize} strokeWidth={1.8} />
        </Link>
      ) : null}
    </div>
  );
}
