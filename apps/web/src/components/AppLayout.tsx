"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { AppSidebar } from "./AppSidebar";
import { buildReturnTo, redirectToPublic, validateSession } from "@/lib/auth";
import { WorkspaceShell } from "./shell/WorkspaceShell";
import { ShellTopbar } from "./shell/ShellTopbar";
import { ShellMobileDrawer } from "./shell/ShellMobileDrawer";
import { useTheme } from "./ThemeProvider";
import { ShellUtilityActions } from "./shell/ShellUtilityActions";

interface AppLayoutProps {
  children: React.ReactNode;
  sidebarContent?: React.ReactNode;
  contentClassName?: string;
  rightRail?: React.ReactNode;
}

export function AppLayout({ children, sidebarContent, contentClassName, rightRail }: AppLayoutProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sessionReady, setSessionReady] = useState(false);
  const { theme } = useTheme();
  const logoSrc = theme === "dark" ? "/brand/logo-full.png" : "/brand/logo-negro.png";

  useEffect(() => {
    let cancelled = false;

    const verify = async () => {
      const status = await validateSession();
      if (cancelled) return;

      if (status === "valid") {
        setSessionReady(true);
        return;
      }

      const returnTo = buildReturnTo(window.location.pathname, window.location.search);
      redirectToPublic(status === "offline" ? "offline" : "missing", returnTo);
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
      sidebar={
        <AppSidebar currentPath={pathname ?? "/"}>
          {sidebarContent}
        </AppSidebar>
      }
      topbar={
        <ShellTopbar
          title="TukiJuris"
          logoHref="/"
          logoSrc={logoSrc}
          onOpenMenu={() => setMobileOpen(true)}
          endSlot={<ShellUtilityActions compact />}
        />
      }
      mobileDrawer={
        <ShellMobileDrawer key={pathname ?? "/"} open={mobileOpen} onClose={() => setMobileOpen(false)}>
          <AppSidebar currentPath={pathname ?? "/"} mode="mobile" onNavigate={() => setMobileOpen(false)}>
            {sidebarContent}
          </AppSidebar>
        </ShellMobileDrawer>
      }
    >
      {children}
    </WorkspaceShell>
  );
}
