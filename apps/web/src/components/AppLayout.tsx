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

  // While the boot refresh is in progress or the user is unauthenticated,
  // render nothing. AuthContext fires redirectToPublic() automatically when
  // the refresh fails, so no manual redirect is needed here.
  if (isLoading || !user) return null;

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
