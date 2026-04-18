export interface NavItem {
  id: string;
  label: string;
  href: string;
}

export const NAV_ITEMS: NavItem[] = [
  { id: "getting-started", label: "Getting Started", href: "/docs/getting-started" },
  { id: "authentication", label: "Authentication", href: "/docs/authentication" },
  { id: "endpoints", label: "Endpoints", href: "/docs/endpoints" },
  { id: "rate-limits", label: "Rate Limits", href: "/docs/rate-limits" },
  { id: "legal-areas", label: "Legal Areas", href: "/docs/legal-areas" },
  { id: "error-codes", label: "Error Codes", href: "/docs/error-codes" },
  { id: "sdks", label: "SDKs", href: "/docs/sdks" },
];
