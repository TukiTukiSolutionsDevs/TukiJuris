"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { AppSidebar } from "./AppSidebar";
import { useAuth } from "@/lib/auth/AuthContext";
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
  const { theme } = useTheme();
  const logoSrc = theme === "dark" ? "/brand/logo-full.png" : "/brand/logo-negro.png";

  const { user, isLoading } = useAuth();

  // IMPORTANT: never return null here.
  //
  // Next.js App Router caches the RSC payload of a mounted page and replays
  // it when the user hits the back button. If AppLayout returned null while
  // the boot refresh was in-flight, Next cached an empty tree — pressing
  // back later served that empty cache and the page rendered blank. Only a
  // hard reload recovered.
  //
  // Instead render a lightweight loading shell while `isLoading` or `!user`.
  // The shell is valid DOM, so Next's router cache always has something
  // meaningful to restore. When AuthContext finishes the boot refresh and
  // `user` populates, this component re-renders into the real WorkspaceShell.
  if (isLoading || !user) {
    return (
      <div
        role="status"
        aria-live="polite"
        aria-label="Cargando"
        className="flex h-screen items-center justify-center bg-background"
      >
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-container border-t-transparent" />
      </div>
    );
  }

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
