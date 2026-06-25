/**
 * admin-nav.ts — single source of truth for the admin panel navigation.
 *
 * Both AdminSidebar and admin/page.tsx import from here. Each tab's `key`
 * is the value used in the `?tab=` query param.
 */

import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  ScrollText,
  Receipt,
  KeyRound,
  Users,
  Building2,
  ShieldCheck,
  Clock,
  BookOpen,
  Tag,
  CreditCard,
  Cpu,
  KeyRound as KeySquare,
  ToggleLeft,
  Gauge,
  Plug,
  Bell,
  Heart,
  BarChart3,
  Banknote,
  Lock,
  Eye,
} from "lucide-react";

export interface AdminTab {
  key: string;
  label: string;
  icon: LucideIcon;
  requiresPermission?: string;
  /** If true, the page renders a ComingSoon placeholder. */
  comingSoon?: boolean;
  description?: string;
}

export interface AdminSection {
  label: string;
  tabs: AdminTab[];
}

export const ADMIN_SECTIONS: AdminSection[] = [
  {
    label: "Dashboard",
    tabs: [
      { key: "resumen", label: "Resumen", icon: LayoutDashboard },
    ],
  },
  {
    label: "Usuarios",
    tabs: [
      { key: "usuarios", label: "Usuarios", icon: Users, requiresPermission: "users:read" },
      { key: "organizaciones", label: "Organizaciones", icon: Building2 },
      { key: "roles", label: "Roles & Permisos", icon: ShieldCheck, requiresPermission: "roles:read" },
      { key: "trials", label: "Trials", icon: Clock },
    ],
  },
  {
    label: "Contenido",
    tabs: [
      { key: "conocimiento", label: "Conocimiento", icon: BookOpen },
    ],
  },
  {
    label: "Monetización",
    tabs: [
      { key: "planes", label: "Planes", icon: Tag },
      { key: "facturas", label: "Facturas", icon: Receipt, requiresPermission: "billing:update" },
      { key: "suscripciones", label: "Suscripciones", icon: CreditCard },
    ],
  },
  {
    label: "Modelos & IA",
    tabs: [
      { key: "modelos", label: "Modelos LLM", icon: Cpu },
      { key: "claves", label: "Claves plataforma", icon: KeyRound, requiresPermission: "platform_keys:write" },
      { key: "byok", label: "BYOK", icon: KeySquare },
    ],
  },
  {
    label: "Sistema",
    tabs: [
      { key: "funcionalidades", label: "Funcionalidades", icon: ToggleLeft },
      { key: "limites", label: "Límites", icon: Gauge },
      { key: "oauth", label: "OAuth", icon: Plug },
      { key: "notificaciones", label: "Notificaciones", icon: Bell },
    ],
  },
  {
    label: "Observabilidad",
    tabs: [
      { key: "auditoria", label: "Auditoría", icon: ScrollText },
      { key: "salud", label: "Salud", icon: Heart },
      { key: "analytics", label: "Analytics", icon: BarChart3 },
    ],
  },
  {
    label: "Configuración avanzada",
    tabs: [
      { key: "pagos", label: "Pagos", icon: Banknote },
      { key: "seguridad", label: "Seguridad", icon: Lock },
      { key: "observabilidad", label: "Observabilidad", icon: Eye },
    ],
  },
];

export const ALL_TAB_KEYS: string[] = ADMIN_SECTIONS.flatMap((s) =>
  s.tabs.map((t) => t.key)
);

export function findTab(key: string): AdminTab | undefined {
  for (const section of ADMIN_SECTIONS) {
    const found = section.tabs.find((t) => t.key === key);
    if (found) return found;
  }
  return undefined;
}
