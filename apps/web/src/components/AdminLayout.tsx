"use client";

/**
 * AdminLayout — pure visual shell for the admin section.
 *
 * Auth (session check + role guard) is handled upstream by
 * apps/web/src/app/admin/layout.tsx. This component only renders
 * the workspace shell, sidebar, topbar, and mobile drawer.
 */

import { useState } from "react";
import { usePathname } from "next/navigation";
import { AdminSidebar } from "./AdminSidebar";
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

export function AdminLayout({ children, contentClassName, rightRail }: AdminLayoutProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

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
        <ShellMobileDrawer
          key={pathname ?? "/admin"}
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
        >
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
