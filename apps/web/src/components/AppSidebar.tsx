"use client";

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
  Menu,
  X,
} from "lucide-react";
import { getToken, logout } from "@/lib/auth";
import { useTheme } from "./ThemeProvider";
import { ThemeToggle } from "./ThemeToggle";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  if (plan === "enterprise")
    return "text-[10px] uppercase tracking-widest font-bold bg-[#A78BFA]/20 text-[#A78BFA] px-2 py-0.5 rounded-lg";
  if (plan === "base")
    return "text-[10px] uppercase tracking-widest font-bold bg-primary/20 text-primary px-2 py-0.5 rounded-lg";
  return "text-[10px] uppercase tracking-widest font-bold bg-surface-container-high text-on-surface/60 px-2 py-0.5 rounded-lg";
}

function getPlanLabel(plan?: string | null): string {
  if (!plan) return "";
  return plan === "free" ? "Beta" : plan;
}

// ---------------------------------------------------------------------------
// AppSidebar
// ---------------------------------------------------------------------------

export function AppSidebar({ currentPath, children }: AppSidebarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expanded, setExpanded] = useState(true);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const { theme } = useTheme();
  const logoSrc = theme === "dark" ? "/brand/logo-full.png" : "/brand/logo-negro.png";

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

    // Fetch unread notification count
    fetch(`${API_URL}/api/notifications/unread-count`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data && typeof data.count === "number") setUnreadCount(data.count);
      })
      .catch(() => null);
  }, []);

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [currentPath]);

  const closeMobile = () => setMobileOpen(false);
  const toggleCollapse = () => setExpanded((v) => !v);

  // ---------------------------------------------------------------------------
  // Sidebar core content (reused for desktop + mobile)
  // ---------------------------------------------------------------------------

  const sidebarCore = (isMobile = false) => (
    <aside
      role="navigation"
      aria-label="Menu principal"
      className={`bg-surface flex flex-col h-full transition-all duration-300 ease-in-out ${
        isMobile ? "w-72" : expanded ? "w-64" : "w-20"
      }`}
    >
      {/* ------------------------------------------------------------------- */}
      {/* Logo area                                                            */}
      {/* ------------------------------------------------------------------- */}
      {expanded || isMobile ? (
        <div className="px-5 py-5">
          <a href="/" className="flex items-center gap-3">
            <img src={logoSrc} alt="TukiJuris" className="h-9 w-9 rounded-lg object-contain flex-shrink-0" />
            <span className="font-['Newsreader'] text-2xl font-bold text-primary tracking-tight">
              TukiJuris
            </span>
          </a>
        </div>
      ) : (
        <div className="px-3 py-5 flex justify-center">
          <a href="/" title="TukiJuris">
            <img src={logoSrc} alt="TukiJuris" className="h-9 w-9 rounded-lg object-contain" />
          </a>
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
              onClick={isMobile ? closeMobile : undefined}
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
              onClick={isMobile ? closeMobile : undefined}
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
              onClick={isMobile ? closeMobile : undefined}
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
              onClick={isMobile ? closeMobile : undefined}
            />
          ))}
        </div>

        {/* ADMIN — only if user.is_admin */}
        {user?.is_admin && (
          <div className="pt-1">
            {(expanded || isMobile) && <SectionLabel label="Admin" />}
            {NAV_ADMIN.map((item) => (
              <NavLink
                key={item.href}
                item={item}
                currentPath={currentPath}
                expanded={expanded || isMobile}
                onClick={isMobile ? closeMobile : undefined}
              />
            ))}
          </div>
        )}

        {/* Page-specific children (chat history, etc.) */}
        {children && (expanded || isMobile) && (
          <div className="bg-surface-container-low mt-2 pt-2">
            {children}
          </div>
        )}
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* User section (bottom)                                                */}
      {/* ------------------------------------------------------------------- */}
      <div className="mt-auto bg-surface-container-low px-4 py-4">
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
                href="/configuracion"
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
          // Collapsed state
          <div className="flex flex-col items-center gap-3">
            {/* Avatar */}
            <div className="w-9 h-9 rounded-lg bg-secondary-container flex items-center justify-center text-sm font-medium text-secondary">
              {user?.name?.[0]?.toUpperCase() ||
                user?.email?.[0]?.toUpperCase() ||
                "U"}
            </div>

            {/* Notification bell */}
            <a
              href="/configuracion"
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

  return (
    <>
      {/* Hamburger button — mobile only */}
      <button
        onClick={() => setMobileOpen(true)}
        aria-label="Abrir menu"
        className="fixed top-3 left-3 z-50 p-2 rounded-lg bg-surface text-on-surface/60 hover:text-on-surface transition-colors md:hidden"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={closeMobile}
            aria-hidden="true"
          />
          {/* Sidebar panel */}
          <div className="relative h-full flex">
            {sidebarCore(true)}
            <button
              onClick={closeMobile}
              aria-label="Cerrar menu"
              className="absolute top-4 right-4 p-1.5 rounded-lg text-on-surface/40 hover:text-on-surface transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Desktop sidebar — always visible */}
      <div className="hidden md:flex h-full">{sidebarCore(false)}</div>
    </>
  );
}
