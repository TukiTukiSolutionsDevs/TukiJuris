"use client";

import Link from "next/link";
import { Settings2 } from "lucide-react";
import { usePathname } from "next/navigation";
import { useMemo } from "react";
import NotificationBell from "@/components/NotificationBell";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getToken } from "@/lib/auth";

interface ShellUtilityActionsProps {
  showSettingsLink?: boolean;
  compact?: boolean;
}

export function ShellUtilityActions({
  showSettingsLink = true,
  compact = false,
}: ShellUtilityActionsProps) {
  const pathname = usePathname();
  const token = useMemo(() => getToken(), []);
  const hideSettingsLink = !showSettingsLink || pathname === "/configuracion";

  return (
    <div className="flex items-center gap-1.5">
      <NotificationBell token={token} />
      <ThemeToggle className="control-surface bg-surface" />
      {!hideSettingsLink ? (
        <Link
          href="/configuracion"
          aria-label="Ir a configuración"
          className={`control-surface inline-flex items-center justify-center rounded-xl bg-surface text-on-surface/70 hover:text-on-surface ${
            compact ? "h-9 w-9" : "h-10 w-10"
          }`}
        >
          <Settings2 className="h-4 w-4" />
        </Link>
      ) : null}
    </div>
  );
}
