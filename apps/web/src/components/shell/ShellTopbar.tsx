"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Menu, Plus, Scale } from "lucide-react";

interface ShellTopbarProps {
  title: string;
  logoHref?: string;
  logoSrc?: string;
  onOpenMenu?: () => void;
  endSlot?: React.ReactNode;
}

// Route → human label for breadcrumb. Single source of truth; keep in sync with
// AppSidebar nav items.
const ROUTE_LABELS: Record<string, string> = {
  "/analizar": "Analizar caso",
  "/buscar": "Buscar corpus",
  "/historial": "Historial",
  "/marcadores": "Marcadores",
  "/notificaciones": "Notificaciones",
  "/analytics": "Analytics",
  "/organizacion": "Organización",
  "/billing": "Facturación",
  "/configuracion": "Configuración",
  "/guia": "Guía",
  "/docs": "API Docs",
  "/onboarding": "Bienvenido",
  "/admin": "Panel Admin",
};

function deriveLabel(pathname: string): string {
  if (ROUTE_LABELS[pathname]) return ROUTE_LABELS[pathname];
  // /historial/123 → fall back to /historial label
  for (const route of Object.keys(ROUTE_LABELS)) {
    if (pathname.startsWith(route + "/")) return ROUTE_LABELS[route];
  }
  return "Inicio";
}

export function ShellTopbar({
  title,
  logoHref = "/",
  logoSrc,
  onOpenMenu,
  endSlot,
}: ShellTopbarProps) {
  const pathname = usePathname() ?? "/";
  const pageLabel = deriveLabel(pathname);

  return (
    <>
      {/* ── Desktop topbar ─────────────────────────────────────── */}
      <header className="hidden h-14 shrink-0 items-center gap-3 border-b border-outline-variant bg-background px-[22px] md:flex">
        <div className="flex items-center gap-2 text-[13px] text-on-surface-subtle">
          <Scale className="h-3.5 w-3.5 text-primary" />
          <span className="text-on-surface-subtle">TukiJuris</span>
          <ChevronRight className="h-3 w-3 text-on-surface-faint" strokeWidth={2} />
          <span className="font-semibold text-on-surface-strong">{pageLabel}</span>
        </div>

        <div className="flex-1" />

        <div className="flex items-center gap-1.5">{endSlot}</div>

        <div className="mx-1 h-[22px] w-px bg-outline-variant" />

        <Link
          href="/analizar"
          className="gold-gradient inline-flex h-[34px] items-center gap-1.5 rounded-lg px-3.5 text-[12.5px] font-bold text-on-primary transition-opacity hover:opacity-95"
        >
          <Plus className="h-3.5 w-3.5" strokeWidth={2.2} />
          Nuevo
        </Link>
      </header>

      {/* ── Mobile topbar (drawer trigger) ──────────────────────── */}
      <header className="sticky top-0 z-40 border-b border-outline-variant bg-surface/95 backdrop-blur md:hidden">
        <div className="flex h-14 items-center gap-3 px-3">
          <button
            type="button"
            onClick={onOpenMenu}
            aria-label="Abrir menú"
            className="control-surface inline-flex h-9 w-9 items-center justify-center rounded-xl text-on-surface/70 hover:text-on-surface"
          >
            <Menu className="h-4 w-4" />
          </button>

          <Link
            href={logoHref}
            className="flex min-w-0 items-center gap-2 rounded-xl px-1.5 py-1 transition hover:bg-surface-container-low/60"
          >
            {logoSrc ? (
              <Image
                src={logoSrc}
                alt={title}
                className="h-7 w-auto object-contain"
                width={120}
                height={28}
              />
            ) : null}
            <span className="truncate text-sm font-semibold text-on-surface">
              {title}
            </span>
          </Link>

          <div className="ml-auto flex items-center gap-2">{endSlot}</div>
        </div>
      </header>
    </>
  );
}
