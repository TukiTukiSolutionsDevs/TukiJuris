"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import {
  Scale,
  LayoutDashboard,
  Users,
  Building2,
  CreditCard,
  Activity,
  BarChart3,
  Bell,
  ArrowLeft,
  LogOut,
  ShieldCheck,
} from "lucide-react";
import { getToken, logout } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

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
// Nav structure
// ---------------------------------------------------------------------------

const NAV_DASHBOARD: NavItem[] = [
  { label: "Resumen", href: "/admin", icon: LayoutDashboard },
  { label: "Usuarios", href: "/admin?section=users", icon: Users },
  { label: "Organizaciones", href: "/admin?section=orgs", icon: Building2 },
  { label: "Suscripciones", href: "/admin?section=subscriptions", icon: CreditCard },
];

const NAV_SISTEMA: NavItem[] = [
  { label: "Estado", href: "/status", icon: Activity },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Notificaciones", href: "/configuracion", icon: Bell },
];

// ---------------------------------------------------------------------------
// NavLink helper
// ---------------------------------------------------------------------------

function NavLink({
  item,
  currentPath,
  onClick,
}: {
  item: NavItem;
  currentPath: string;
  onClick?: () => void;
}) {
  const Icon = item.icon;
  const isActive =
    item.href === "/admin"
      ? currentPath === "/admin"
      : currentPath === item.href || currentPath.startsWith(item.href.split("?")[0]);

  return (
    <a
      href={item.href}
      onClick={onClick}
      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors focus:outline-none ${
        isActive
          ? "bg-surface-container-low text-primary"
          : "text-on-surface/60 hover:text-on-surface hover:bg-surface-container-low/60"
      }`}
    >
      <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />
      <span>{item.label}</span>
    </a>
  );
}

// ---------------------------------------------------------------------------
// Section header helper
// ---------------------------------------------------------------------------

function SectionHeader({ label }: { label: string }) {
  return (
    <p className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-1 mt-3 px-1 first:mt-0">
      {label}
    </p>
  );
}

// ---------------------------------------------------------------------------
// AdminSidebar
// ---------------------------------------------------------------------------

export function AdminSidebar({
  currentPath,
  mode = "desktop",
  onNavigate,
}: AdminSidebarProps) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const isMobile = mode === "mobile";

  // Fetch user info on mount
  useEffect(() => {
    const token = getToken();
    if (!token) return;

    fetch(`${API_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setUser(data);
      })
      .catch(() => null);
  }, []);

  return (
    <aside
      role="navigation"
      aria-label="Menu de administración"
      className={`bg-surface border-r border-[rgba(79,70,51,0.15)] flex flex-col h-full ${
        isMobile ? "w-72 max-w-[88vw]" : "w-72"
      }`}
    >
      {/* Logo + Admin badge */}
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

        {/* Dashboard section */}
        <SectionHeader label="Dashboard" />
        {NAV_DASHBOARD.map((item) => (
          <NavLink
            key={item.href}
            item={item}
            currentPath={currentPath}
            onClick={isMobile ? onNavigate : undefined}
          />
        ))}
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-0.5">
        {/* Sistema */}
        <SectionHeader label="Sistema" />
        {NAV_SISTEMA.map((item) => (
          <NavLink
            key={item.href}
            item={item}
            currentPath={currentPath}
            onClick={isMobile ? onNavigate : undefined}
          />
        ))}

        {/* Separator + Volver al App */}
        <div className="border-t border-[rgba(79,70,51,0.15)] my-2" />
        <Link
          href="/"
          onClick={isMobile ? onNavigate : undefined}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-primary hover:text-primary/80 hover:bg-surface-container-low transition-colors"
        >
          <ArrowLeft className="w-4 h-4 shrink-0" aria-hidden="true" />
          <span>Volver al App</span>
        </Link>
      </div>

      {/* Footer: user info + logout */}
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
