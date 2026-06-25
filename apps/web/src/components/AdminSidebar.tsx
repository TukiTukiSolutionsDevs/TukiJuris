"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Scale, LogOut, ShieldCheck } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { ADMIN_SECTIONS, type AdminTab } from "@/app/admin/_lib/admin-nav";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AdminSidebarProps {
  currentPath: string;
  mode?: "desktop" | "mobile";
  onNavigate?: () => void;
}

interface UserInfo {
  id: string;
  email: string;
  name?: string | null;
  is_admin?: boolean;
}

// ---------------------------------------------------------------------------
// NavLink helper
// ---------------------------------------------------------------------------

function NavLink({
  tab,
  activeTab,
  onClick,
}: {
  tab: AdminTab;
  activeTab: string;
  onClick?: () => void;
}) {
  const Icon = tab.icon;
  const isActive = tab.key === activeTab;
  const href = `/admin?tab=${tab.key}`;

  return (
    <a
      href={href}
      onClick={onClick}
      aria-current={isActive ? "page" : undefined}
      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors focus:outline-none ${
        isActive
          ? "bg-surface-container-low text-primary"
          : "text-on-surface/60 hover:text-on-surface hover:bg-surface-container-low/60"
      }`}
    >
      <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
      <span className="flex-1 truncate">{tab.label}</span>
      {tab.comingSoon && (
        <span className="text-[9px] uppercase tracking-[0.15em] text-on-surface/30">
          Soon
        </span>
      )}
    </a>
  );
}

function SectionHeader({ label }: { label: string }) {
  return (
    <p className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-1 mt-4 px-1 first:mt-0">
      {label}
    </p>
  );
}

// ---------------------------------------------------------------------------
// AdminSidebar
// ---------------------------------------------------------------------------
//
// Design contract:
//
// 1. Sidebar must NEVER link to client-panel routes (`/`, `/historial`, etc.).
//    Admin users are gated OUT of the client panel by middleware.
//
// 2. Tab keys MUST match the values consumed by /admin/page.tsx
//    (`searchParams.get("tab")`). The source of truth is admin-nav.ts.
//
// 3. Items with `requiresPermission` are filtered against `hasPermission()`.
//    The backend RBAC is the source of truth — this is a UX affordance.
//
// 4. Sections that end up empty after filtering are dropped.

export function AdminSidebar({
  currentPath: _currentPath,
  mode = "desktop",
  onNavigate,
}: AdminSidebarProps) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const isMobile = mode === "mobile";

  const { logout, authFetch, hasPermission } = useAuth();
  const searchParams = useSearchParams();
  const activeTab = searchParams?.get("tab") ?? "resumen";

  useEffect(() => {
    void authFetch("/api/auth/me", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: UserInfo | null) => {
        if (data) setUser(data);
      })
      .catch(() => null);
  }, [authFetch]);

  const visibleSections = ADMIN_SECTIONS.map((section) => ({
    ...section,
    tabs: section.tabs.filter(
      (t) => !t.requiresPermission || hasPermission(t.requiresPermission)
    ),
  })).filter((s) => s.tabs.length > 0);

  return (
    <aside
      role="navigation"
      aria-label="Menu de administración"
      className={`bg-surface border-r border-[rgba(79,70,51,0.15)] flex flex-col h-full ${
        isMobile ? "w-72 max-w-[88vw]" : "w-72"
      }`}
    >
      <div className="p-4 border-b border-[rgba(79,70,51,0.15)]">
        <a href="/admin" className="flex items-center gap-2.5 mb-1">
          <div className="w-9 h-9 bg-primary/10 border border-primary/20 rounded-lg flex items-center justify-center shrink-0">
            <Scale className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="font-['Newsreader'] font-bold text-base text-on-surface">TukiJuris</h1>
            <p className="text-[10px] text-on-surface/40">Panel de Administración</p>
          </div>
          <span className="ml-auto text-[9px] font-bold tracking-widest uppercase px-1.5 py-0.5 rounded-lg bg-primary/10 text-primary border border-primary/20">
            ADMIN
          </span>
        </a>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-0.5">
        {visibleSections.map((section) => (
          <div key={section.label}>
            <SectionHeader label={section.label} />
            {section.tabs.map((tab) => (
              <NavLink
                key={tab.key}
                tab={tab}
                activeTab={activeTab}
                onClick={isMobile ? onNavigate : undefined}
              />
            ))}
          </div>
        ))}
      </div>

      <div className="p-3 border-t border-[rgba(79,70,51,0.15)] space-y-1">
        {user && (
          <div className="flex items-center gap-2 px-3 py-2">
            <div className="w-7 h-7 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-3.5 h-3.5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-on-surface truncate">
                {user.name || user.email}
              </p>
              {user.name && (
                <p className="text-[10px] text-on-surface/40 truncate">{user.email}</p>
              )}
            </div>
            <button
              onClick={logout}
              title="Cerrar sesión"
              className="p-1.5 rounded-lg text-on-surface/30 hover:text-red-400 hover:bg-red-400/10 transition-colors shrink-0"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
