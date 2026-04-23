"use client";

import Image from "next/image";
import Link from "next/link";
import { useState, useEffect } from "react";
import {
  MessageSquare,
  Search,
  History,
  Bookmark,
  BarChart3,
  Building2,
  CreditCard,
  Settings,
  HelpCircle,
  FileCode,
  Activity,
  Shield,
  LogOut,
  PanelLeftClose,
  PanelLeftOpen,
  Bell,
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { ThemeToggle } from "./ThemeToggle";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  adminOnly?: boolean;
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
// Nav structure
// ---------------------------------------------------------------------------

const NAV_PRINCIPAL: NavItem[] = [
  { label: "Chat", href: "/", icon: MessageSquare },
  { label: "Buscar", href: "/buscar", icon: Search },
];

const NAV_ORGANIZACION: NavItem[] = [
  { label: "Historial", href: "/historial", icon: History },
  { label: "Marcadores", href: "/marcadores", icon: Bookmark },
];

const NAV_GESTION: NavItem[] = [
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Organización", href: "/organizacion", icon: Building2 },
  { label: "Facturación", href: "/billing", icon: CreditCard },
];

const NAV_EXTRA: NavItem[] = [
  { label: "Configuración", href: "/configuracion", icon: Settings },
  { label: "Guía", href: "/guia", icon: HelpCircle },
  { label: "API Docs", href: "/docs", icon: FileCode },
  { label: "Estado", href: "/status", icon: Activity },
];

const NAV_ADMIN: NavItem[] = [
  { label: "Panel Admin", href: "/admin", icon: Shield, adminOnly: true },
];

// ---------------------------------------------------------------------------
// NavLink helper
// ---------------------------------------------------------------------------

function NavLink({
  item,
  currentPath,
  expanded,
  onClick,
}: {
  item: NavItem;
  currentPath: string;
  expanded: boolean;
  onClick?: () => void;
}) {
  const Icon = item.icon;
  const isActive = currentPath === item.href;

  if (!expanded) {
    return (
      <a
        href={item.href}
        onClick={onClick}
        title={item.label}
        className={`flex items-center justify-center py-2.5 mx-2 rounded-lg transition-all duration-200 ${
          isActive
            ? "bg-surface-container-low text-primary"
            : "text-on-surface/80 hover:text-primary hover:bg-surface-container-low"
        }`}
      >
        <Icon className="w-[18px] h-[18px] flex-shrink-0" aria-hidden="true" />
      </a>
    );
  }

  return (
    <a
      href={item.href}
      onClick={onClick}
      className={`flex items-center gap-3 px-5 py-2.5 mx-2 rounded-lg text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary/30 ${
        isActive
          ? "bg-surface-container-low text-primary font-medium"
          : "text-on-surface/80 hover:text-primary hover:bg-surface-container-low"
      }`}
    >
      <Icon className="w-[18px] h-[18px] flex-shrink-0" aria-hidden="true" />
      <span>{item.label}</span>
    </a>
  );
}

// ---------------------------------------------------------------------------
// SectionLabel helper
// ---------------------------------------------------------------------------

function SectionLabel({ label }: { label: string }) {
  return (
    <p className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 px-5 pt-4 pb-2 font-bold">
      {label}
    </p>
  );
}

// ---------------------------------------------------------------------------
// Plan badge helpers
// ---------------------------------------------------------------------------

function getPlanBadgeClasses(plan?: string | null): string {
  if (plan === "studio")
    return "text-[10px] uppercase tracking-widest font-bold bg-[#A78BFA]/20 text-[#A78BFA] px-2 py-0.5 rounded-lg";
  if (plan === "pro")
    return "text-[10px] uppercase tracking-widest font-bold bg-primary/20 text-primary px-2 py-0.5 rounded-lg";
  return "text-[10px] uppercase tracking-widest font-bold bg-surface-container-high text-on-surface/60 px-2 py-0.5 rounded-lg";
}

const PLAN_DISPLAY: Record<string, string> = {
  free: "Gratuito",
  pro: "Profesional",
  studio: "Estudio",
};

function getPlanLabel(plan?: string | null): string {
  if (!plan) return "";
  return PLAN_DISPLAY[plan] ?? plan;
}

// ---------------------------------------------------------------------------
// AppSidebar
// ---------------------------------------------------------------------------

export function AppSidebar({
  currentPath,
  children,
  mode = "desktop",
  onNavigate,
}: AppSidebarProps) {
  const [expanded, setExpanded] = useState(true);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const isMobile = mode === "mobile";

  const { user: authUser, logout, authFetch } = useAuth();

  // Fetch full profile (name, plan) and unread count on mount
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

  const toggleCollapse = () => setExpanded((v) => !v);

  // ---------------------------------------------------------------------------
  // Sidebar core content (reused for desktop + mobile)
  // ---------------------------------------------------------------------------

  return (
    <aside
      role="navigation"
      aria-label="Menu principal"
      className={`panel-base bg-surface flex flex-col h-full border-r border-[rgba(79,70,51,0.12)] transition-all duration-300 ease-in-out ${
        isMobile ? "w-72 max-w-[88vw]" : expanded ? "w-64" : "w-20"
      }`}
    >
      {/* ------------------------------------------------------------------- */}
      {/* Logo area                                                            */}
      {/* ------------------------------------------------------------------- */}
      {expanded || isMobile ? (
        <div className="px-4 pt-4 pb-5">
          <Link
            href="/"
            className="group panel-base flex items-center gap-2.5 rounded-2xl px-4 py-3 transition-all duration-200 hover:border-primary/30 hover:bg-surface-container"
          >
            <Image
              src="/brand/logo-icon.png"
              alt="TukiJuris"
              className="h-13 w-13 shrink-0 object-contain transition-transform duration-200 group-hover:scale-[1.03]"
              width={52}
              height={52}
            />
            <div className="min-w-0">
              <p className="font-['Newsreader'] text-[1.15rem] font-bold tracking-[-0.03em] text-on-surface">TukiJuris</p>
              <p className="section-eyebrow mt-1 text-on-surface/35">Abogados</p>
            </div>
          </Link>
        </div>
      ) : (
        <div className="px-3 py-4 flex justify-center">
          <Link
            href="/"
            title="TukiJuris"
            className="flex h-14 w-14 items-center justify-center rounded-2xl bg-surface shadow-[0_10px_24px_rgba(0,0,0,0.08)] ring-1 ring-[rgba(79,70,51,0.08)] transition-all duration-200 hover:scale-[1.02]"
          >
            <Image src="/brand/logo-icon.png" alt="TukiJuris" className="h-10 w-10 object-contain" width={40} height={40} />
          </Link>
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* Scrollable nav                                                       */}
      {/* ------------------------------------------------------------------- */}
      <div className="flex-1 overflow-y-auto py-3">
        {/* PRINCIPAL */}
        <div className="pb-3">
          {(expanded || isMobile) && <SectionLabel label="Principal" />}
          {NAV_PRINCIPAL.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              currentPath={currentPath}
              expanded={expanded || isMobile}
              onClick={isMobile ? onNavigate : undefined}
            />
          ))}
        </div>

        {/* ORGANIZACIÓN — subtle bg shift instead of border */}
        <div className="bg-surface-container-low py-3">
          {(expanded || isMobile) && <SectionLabel label="Organización" />}
          {NAV_ORGANIZACION.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              currentPath={currentPath}
              expanded={expanded || isMobile}
              onClick={isMobile ? onNavigate : undefined}
            />
          ))}
        </div>

        {/* GESTIÓN */}
        <div className="pb-3">
          {(expanded || isMobile) && <SectionLabel label="Gestión" />}
          {NAV_GESTION.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              currentPath={currentPath}
              expanded={expanded || isMobile}
              onClick={isMobile ? onNavigate : undefined}
            />
          ))}
        </div>

        {/* CONFIGURACIÓN — subtle bg shift */}
        <div className="bg-surface-container-low py-3">
          {(expanded || isMobile) && <SectionLabel label="Configuración" />}
          {NAV_EXTRA.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              currentPath={currentPath}
              expanded={expanded || isMobile}
              onClick={isMobile ? onNavigate : undefined}
            />
          ))}
        </div>

        {/* ADMIN — only if authenticated user has admin claim */}
        {authUser?.isAdmin && (
          <div className="pt-1">
            {(expanded || isMobile) && <SectionLabel label="Admin" />}
            {NAV_ADMIN.map((item) => (
              <NavLink
                key={item.href}
                item={item}
                currentPath={currentPath}
                expanded={expanded || isMobile}
                onClick={isMobile ? onNavigate : undefined}
              />
            ))}
          </div>
        )}

        {/* Page-specific children (chat history, etc.) */}
        {children && (expanded || isMobile) && (
          <div className="mt-3 rounded-2xl bg-surface-container-low/75 pt-2">
            {children}
          </div>
        )}
      </div>

      <div className="mt-auto border-t border-[rgba(79,70,51,0.12)] bg-surface-container-low/80 px-4 py-4">
        {expanded || isMobile ? (
          <>
            {/* User info row */}
            <div className="flex items-center gap-3">
              {/* Avatar */}
              <div className="w-9 h-9 rounded-lg bg-secondary-container flex items-center justify-center text-sm font-medium text-secondary shrink-0">
                {user?.name?.[0]?.toUpperCase() ||
                  user?.email?.[0]?.toUpperCase() ||
                  "U"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-on-surface truncate">
                  {user?.name || user?.email || "Usuario"}
                </p>
                {user?.name && (
                  <p className="text-xs text-on-surface/40 truncate">{user.email}</p>
                )}
              </div>
              {/* Plan badge */}
              {user?.plan && (
                <span className={getPlanBadgeClasses(user.plan)}>
                  {getPlanLabel(user.plan)}
                </span>
              )}
            </div>

            {/* Action buttons row */}
            <div className="flex items-center gap-1 mt-3">
              {/* Collapse toggle */}
              {!isMobile && (
                <button
                  onClick={toggleCollapse}
                  title="Colapsar sidebar"
                  className="p-2 rounded-lg text-on-surface/40 hover:text-on-surface hover:bg-surface-container-high transition"
                >
                  <PanelLeftClose className="w-4 h-4" />
                </button>
              )}

              {/* Theme toggle */}
              <ThemeToggle />

              <div className="flex-1" />

              {/* Notification bell */}
              <a
                href="/notificaciones"
                title="Notificaciones"
                className="relative p-2 rounded-lg text-on-surface/60 hover:text-primary hover:bg-surface-container-high transition"
              >
                <Bell className="w-4 h-4" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-3.5 h-3.5 bg-primary-container text-[8px] font-bold text-black rounded-full flex items-center justify-center">
                    {unreadCount > 9 ? "9+" : unreadCount}
                  </span>
                )}
              </a>

              {/* Logout */}
              <button
                onClick={logout}
                title="Cerrar sesión"
                className="p-2 rounded-lg text-on-surface/40 hover:text-[#F87171] hover:bg-[#F87171]/10 transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center gap-3">
            {/* Avatar */}
            <div className="w-9 h-9 rounded-lg bg-secondary-container flex items-center justify-center text-sm font-medium text-secondary">
              {user?.name?.[0]?.toUpperCase() ||
                user?.email?.[0]?.toUpperCase() ||
                "U"}
            </div>

            {/* Notification bell */}
            <a
              href="/notificaciones"
              title="Notificaciones"
              className="relative p-2 rounded-lg text-on-surface/60 hover:text-primary hover:bg-surface-container-high transition"
            >
              <Bell className="w-4 h-4" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-3.5 h-3.5 bg-primary-container text-[8px] font-bold text-black rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </a>

            {/* Theme toggle */}
            <ThemeToggle />

            {/* Expand toggle */}
            <button
              onClick={toggleCollapse}
              title="Expandir sidebar"
              className="p-2 rounded-lg text-on-surface/40 hover:text-on-surface hover:bg-surface-container-high transition"
            >
              <PanelLeftOpen className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
