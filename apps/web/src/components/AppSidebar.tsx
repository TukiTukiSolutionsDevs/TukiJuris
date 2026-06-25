"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  BarChart3,
  BellRing,
  Bookmark,
  Building2,
  CreditCard,
  FileCode,
  FileSearch,
  HelpCircle,
  History,
  LogOut,
  Plus,
  Search,
  Settings,
  Shield,
  X,
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

interface NavItem {
  id: string;
  label: string;
  href: string;
  icon: React.ElementType;
}

interface NavSection {
  label: string;
  admin?: boolean;
  items: NavItem[];
}

interface AppSidebarProps {
  currentPath: string;
  children?: React.ReactNode;
  mode?: "desktop" | "mobile";
  onNavigate?: () => void;
}

interface UserInfo {
  id: string;
  email: string;
  name?: string | null;
  is_admin?: boolean;
  plan?: string | null;
}

// ---------------------------------------------------------------------------
// Nav structure — canonical for v3 workspace
// ---------------------------------------------------------------------------
const NAV_SECTIONS: NavSection[] = [
  {
    label: "Principal",
    items: [
      { id: "analizar", label: "Analizar caso", href: "/analizar", icon: FileSearch },
      { id: "buscar", label: "Buscar corpus", href: "/buscar", icon: Search },
    ],
  },
  {
    label: "Organización",
    items: [
      { id: "historial", label: "Historial", href: "/historial", icon: History },
      { id: "marcadores", label: "Marcadores", href: "/marcadores", icon: Bookmark },
      { id: "notificaciones", label: "Notificaciones", href: "/notificaciones", icon: BellRing },
    ],
  },
  {
    label: "Gestión",
    items: [
      { id: "analytics", label: "Analytics", href: "/analytics", icon: BarChart3 },
      { id: "organizacion", label: "Organización", href: "/organizacion", icon: Building2 },
      { id: "billing", label: "Facturación", href: "/billing", icon: CreditCard },
    ],
  },
  {
    label: "Configuración",
    items: [
      { id: "configuracion", label: "Configuración", href: "/configuracion", icon: Settings },
      { id: "guia", label: "Guía", href: "/guia", icon: HelpCircle },
      { id: "docs", label: "API Docs", href: "/docs", icon: FileCode },
    ],
  },
  {
    label: "Admin",
    admin: true,
    items: [{ id: "admin", label: "Panel Admin", href: "/admin", icon: Shield }],
  },
];

const PLAN_DISPLAY: Record<string, string> = {
  free: "Gratuito",
  pro: "Profesional",
  studio: "Estudio",
};

const PLAN_BADGE_STYLE: Record<string, string> = {
  free: "bg-surface-container text-on-surface-variant border border-outline-variant",
  pro: "bg-[rgba(201,168,76,0.12)] text-primary border border-[rgba(201,168,76,0.25)]",
  studio: "bg-[rgba(179,164,240,0.12)] text-status-info border border-[rgba(179,164,240,0.25)]",
};

function planLabel(plan?: string | null): string {
  if (!plan) return "Gratuito";
  return PLAN_DISPLAY[plan] ?? plan;
}

function planBadgeClass(plan?: string | null): string {
  if (!plan) return PLAN_BADGE_STYLE.free;
  return PLAN_BADGE_STYLE[plan] ?? PLAN_BADGE_STYLE.free;
}

function getInitials(name?: string | null, email?: string | null): string {
  if (name) {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.slice(0, 2).toUpperCase();
  }
  return email?.slice(0, 2).toUpperCase() ?? "U";
}

// ---------------------------------------------------------------------------
// Nav button (single source of truth for hover / active styling)
// ---------------------------------------------------------------------------
function NavLink({
  item,
  active,
  badge,
  onClick,
}: {
  item: NavItem;
  active: boolean;
  badge?: number;
  onClick?: () => void;
}) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      className={`relative flex h-[38px] items-center gap-2.5 rounded-lg px-3 text-[13px] font-semibold transition-colors ${
        active
          ? "bg-surface-container text-on-surface-strong"
          : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface-strong"
      }`}
      style={
        active
          ? { boxShadow: "inset 3px 0 0 var(--primary)" }
          : undefined
      }
    >
      <Icon
        className={`h-[17px] w-[17px] shrink-0 ${active ? "text-primary" : "text-on-surface-subtle"}`}
        strokeWidth={1.7}
      />
      <span className="flex-1 truncate">{item.label}</span>
      {badge && badge > 0 ? (
        <span className="inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-status-danger px-1.5 text-[10px] font-bold text-white">
          {badge > 9 ? "9+" : badge}
        </span>
      ) : null}
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Sidebar
// ---------------------------------------------------------------------------
export function AppSidebar({
  currentPath,
  children,
  mode = "desktop",
  onNavigate,
}: AppSidebarProps) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const isDrawer = mode === "mobile";

  const { user: authUser, logout, authFetch } = useAuth();

  useEffect(() => {
    void authFetch("/api/auth/me", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: UserInfo | null) => {
        if (data) setUser(data);
      })
      .catch(() => null);

    void authFetch("/api/notifications/unread-count", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: { count?: number } | null) => {
        if (data && typeof data.count === "number") setUnreadCount(data.count);
      })
      .catch(() => null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const initials = getInitials(user?.name, user?.email);
  const displayName = user?.name || user?.email || "Usuario";
  const plan = user?.plan ?? "free";
  const isFreePlan = plan === "free";

  // Free tier: 4 consultas + 1 razonamiento por día.
  // TODO(backend): expose /api/billing/usage/today to drive this.
  // For now, default to placeholder consumption so the visual lands.
  const dailyUsed = isFreePlan ? 0 : null;
  const dailyLimit = isFreePlan ? 4 : null;
  const usagePct =
    dailyLimit && dailyUsed != null ? Math.min(100, (dailyUsed / dailyLimit) * 100) : 0;
  const usageColor =
    usagePct >= 80 ? "var(--status-danger)" : usagePct >= 50 ? "var(--status-warning)" : "var(--primary)";

  return (
    <aside
      aria-label="Navegación principal"
      className={`flex h-full flex-col border-r border-outline-variant bg-surface ${
        isDrawer ? "w-[300px] shadow-[0_24px_48px_rgba(0,0,0,0.65)]" : "w-[284px]"
      }`}
    >
      {/* ── Header / Brand ─────────────────────────────────────── */}
      <div className="flex h-[76px] shrink-0 items-center justify-between gap-3 border-b border-outline-variant px-[18px]">
        <Link
          href="/analizar"
          className="flex items-center gap-2.5"
          onClick={isDrawer ? onNavigate : undefined}
        >
          <Image
            src="/brand/logo-tj.png"
            alt="TukiJuris"
            width={34}
            height={34}
            priority
            className="h-[34px] w-[34px] shrink-0 rounded-[9px] object-contain"
          />
          <div className="leading-[1.1]">
            <div className="font-['Newsreader'] text-[19px] font-semibold tracking-[-0.01em] text-on-surface-strong">
              TukiJuris
            </div>
            <div className="mt-px text-[9.5px] font-bold uppercase tracking-[0.22em] text-[#8a7a4a]">
              Abogados
            </div>
          </div>
        </Link>
        {isDrawer ? (
          <button
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface-strong"
            aria-label="Cerrar menú"
            onClick={onNavigate}
          >
            <X className="h-[18px] w-[18px]" strokeWidth={1.6} />
          </button>
        ) : null}
      </div>

      {/* ── Quick actions ──────────────────────────────────────── */}
      <div className="flex shrink-0 flex-col gap-2 px-[14px] py-[14px] pb-2">
        <Link
          href="/analizar"
          onClick={isDrawer ? onNavigate : undefined}
          className="gold-gradient flex h-10 items-center justify-center gap-2 rounded-[9px] text-[13px] font-bold text-on-primary shadow-[0_2px_10px_rgba(201,168,76,0.22)] transition-opacity hover:opacity-95"
        >
          <Plus className="h-4 w-4" strokeWidth={2.2} />
          Nuevo caso
        </Link>
        <Link
          href="/buscar"
          onClick={isDrawer ? onNavigate : undefined}
          className="flex h-9 items-center gap-2.5 rounded-[9px] border border-outline-variant bg-background px-3 text-[12.5px] font-medium text-on-surface-variant transition-colors hover:border-outline hover:text-on-surface"
        >
          <Search className="h-[15px] w-[15px]" strokeWidth={2} />
          <span className="flex-1 text-left">Buscar workspace</span>
          <kbd className="rounded border border-outline-variant bg-surface-container px-1.5 py-px text-[10px] font-semibold text-on-surface-subtle">
            ⌘K
          </kbd>
        </Link>
      </div>

      {/* ── Nav ────────────────────────────────────────────────── */}
      <nav className="flex min-h-0 flex-1 flex-col gap-[3px] overflow-y-auto px-[14px] pb-3 pt-1.5">
        {NAV_SECTIONS.map((section) => {
          if (section.admin && !authUser?.isAdmin) return null;
          return (
            <div key={section.label}>
              <div className="px-3 pb-1.5 pt-3 text-[10px] font-extrabold uppercase tracking-[0.18em] text-on-surface-faint">
                {section.label}
              </div>
              <div className="flex flex-col gap-[3px]">
                {section.items.map((item) => (
                  <NavLink
                    key={item.id}
                    item={item}
                    active={currentPath === item.href}
                    badge={item.id === "notificaciones" ? unreadCount : undefined}
                    onClick={isDrawer ? onNavigate : undefined}
                  />
                ))}
              </div>
            </div>
          );
        })}

        {children ? <div className="mt-3">{children}</div> : null}
      </nav>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <div className="shrink-0 border-t border-outline-variant px-[14px] py-3">
        {/* Usage badge — only on free plan */}
        {isFreePlan && dailyLimit != null && dailyUsed != null ? (
          <div className="mb-2.5">
            <div className="mb-1.5 flex items-center justify-between">
              <span className="text-[10.5px] font-semibold text-on-surface-variant">
                Consultas hoy
              </span>
              <span className="font-mono text-[10.5px] font-semibold text-primary">
                {dailyUsed} / {dailyLimit}
              </span>
            </div>
            <div className="h-[5px] overflow-hidden rounded-[3px] bg-surface-container">
              <div
                className="h-full rounded-[3px] transition-all"
                style={{ width: `${usagePct}%`, background: usageColor }}
              />
            </div>
          </div>
        ) : null}

        {/* User row */}
        <div className="flex items-center gap-2.5 rounded-[9px] border border-outline-variant bg-background p-[7px]">
          <div
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg font-bold text-[12px] text-[#cfd8e3]"
            style={{
              background: "linear-gradient(140deg,#3a4a5e,#2a3340)",
            }}
            aria-label={`Avatar ${displayName}`}
          >
            {initials}
          </div>
          <div className="min-w-0 flex-1 leading-tight">
            <div className="truncate text-[12.5px] font-semibold text-on-surface-strong">
              {displayName}
            </div>
            <div className="truncate text-[10.5px] text-on-surface-subtle">
              {user?.email ?? ""}
            </div>
          </div>
          <span
            className={`shrink-0 rounded-[5px] px-1.5 py-[3px] text-[9px] font-bold uppercase tracking-[0.08em] ${planBadgeClass(
              plan,
            )}`}
          >
            {planLabel(plan)}
          </span>
        </div>

        {/* Logout */}
        <button
          onClick={() => void logout()}
          className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-[11.5px] font-semibold text-on-surface-subtle transition-colors hover:bg-[rgba(224,107,92,0.08)] hover:text-status-danger"
        >
          <LogOut className="h-3.5 w-3.5" strokeWidth={1.8} />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
