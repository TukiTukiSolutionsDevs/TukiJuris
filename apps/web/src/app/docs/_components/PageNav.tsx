"use client";

import Link from "next/link";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { NAV_ITEMS } from "../_data/navigation";

interface PageNavProps {
  currentId: string;
}

export function PageNav({ currentId }: PageNavProps) {
  const idx = NAV_ITEMS.findIndex((n) => n.id === currentId);
  const prev = idx > 0 ? NAV_ITEMS[idx - 1] : null;
  const next = idx < NAV_ITEMS.length - 1 ? NAV_ITEMS[idx + 1] : null;

  return (
    <nav className="flex items-center justify-between mt-16 pt-8" style={{ borderTop: "1px solid rgba(79,70,51,0.15)" }}>
      {prev ? (
        <Link
          href={prev.href}
          className="group flex items-center gap-2 text-sm text-on-surface/40 hover:text-primary transition-colors"
        >
          <ChevronLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
          <div>
            <span className="text-[10px] uppercase tracking-wider text-on-surface/30 block">Previous</span>
            <span className="font-medium">{prev.label}</span>
          </div>
        </Link>
      ) : (
        <div />
      )}
      {next ? (
        <Link
          href={next.href}
          className="group flex items-center gap-2 text-sm text-on-surface/40 hover:text-primary transition-colors text-right"
        >
          <div>
            <span className="text-[10px] uppercase tracking-wider text-on-surface/30 block">Next</span>
            <span className="font-medium">{next.label}</span>
          </div>
          <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      ) : (
        <div />
      )}
    </nav>
  );
}
