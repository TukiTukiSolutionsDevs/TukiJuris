// Canonical legal areas, projected into the shape that `docs/legal-areas/page.tsx`
// expects (uses `desc` instead of `description`).
//
// Single source of truth: `apps/web/src/app/chat/constants.ts`. Add new areas there.

import type { LucideIcon } from "lucide-react";
import { LEGAL_AREAS as CANONICAL_AREAS } from "@/app/chat/constants";

export interface LegalArea {
  id: string;
  name: string;
  icon: LucideIcon;
  color: string;
  desc: string;
}

export const LEGAL_AREAS: LegalArea[] = CANONICAL_AREAS.map((a) => ({
  id: a.id,
  name: a.label,
  icon: a.icon as LucideIcon,
  color: a.color,
  desc: a.description,
}));
