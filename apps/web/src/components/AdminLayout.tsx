"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { AdminSidebar } from "./AdminSidebar";
import { buildReturnTo, getToken, redirectToPublic, validateSession } from "@/lib/auth";
import { WorkspaceShell } from "./shell/WorkspaceShell";
import { ShellTopbar } from "./shell/ShellTopbar";
import { ShellMobileDrawer } from "./shell/ShellMobileDrawer";
import { Shield } from "lucide-react";
import { ShellUtilityActions } from "./shell/ShellUtilityActions";

interface AdminLayoutProps {
  children: React.ReactNode;
  contentClassName?: string;
  rightRail?: React.ReactNode;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function AdminLayout({ children, contentClassName, rightRail }: AdminLayoutProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sessionReady, setSessionReady] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const verify = async () => {
      const status = await validateSession();
      if (cancelled) return;

      if (status !== "valid") {
        const returnTo = buildReturnTo(window.location.pathname, window.location.search);
        redirectToPublic(status === "offline" ? "offline" : "missing", returnTo);
        return;
      }

      const token = getToken();
      if (!token) {
        const returnTo = buildReturnTo(window.location.pathname, window.location.search);
        redirectToPublic("missing", returnTo);
        return;
      }

      const res = await fetch(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      }).catch(() => null);

      if (cancelled) return;

      if (!res) {
        const returnTo = buildReturnTo(window.location.pathname, window.location.search);
        redirectToPublic("offline", returnTo);
        return;
      }

      const data = res.ok ? await res.json().catch(() => null) : null;
      if (!data?.is_admin) {
        window.location.href = "/";
        return;
      }

      setSessionReady(true);
    };

    verify();

    const handleFocus = () => { void verify(); };
    const handleOnline = () => { void verify(); };
    window.addEventListener("focus", handleFocus);
    window.addEventListener("online", handleOnline);
    const interval = window.setInterval(() => { void verify(); }, 30000);

    return () => {
      cancelled = true;
      window.removeEventListener("focus", handleFocus);
      window.removeEventListener("online", handleOnline);
      window.clearInterval(interval);
    };
  }, []);

  if (!sessionReady) return null;

  return (
    <WorkspaceShell
      contentClassName={contentClassName}
      rightRail={rightRail}
      sidebar={<AdminSidebar currentPath={pathname ?? "/admin"} />}
      topbar={
        <ShellTopbar
          title="TukiJuris Admin"
          logoHref="/admin"
          onOpenMenu={() => setMobileOpen(true)}
          endSlot={
            <div className="flex items-center gap-2">
              <span className="inline-flex h-9 min-w-9 items-center justify-center rounded-xl border border-primary/20 bg-primary/10 px-2 text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
                <Shield className="mr-1 h-3.5 w-3.5" />
                Admin
              </span>
              <ShellUtilityActions compact />
            </div>
          }
        />
      }
      mobileDrawer={
        <ShellMobileDrawer key={pathname ?? "/admin"} open={mobileOpen} onClose={() => setMobileOpen(false)}>
          <AdminSidebar
            currentPath={pathname ?? "/admin"}
            mode="mobile"
            onNavigate={() => setMobileOpen(false)}
          />
        </ShellMobileDrawer>
      }
    >
      {children}
    </WorkspaceShell>
  );
}
