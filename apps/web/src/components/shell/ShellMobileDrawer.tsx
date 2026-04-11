"use client";

import { X } from "lucide-react";

interface ShellMobileDrawerProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

export function ShellMobileDrawer({ open, onClose, children }: ShellMobileDrawerProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />

      <div className="relative flex h-full max-w-[88vw]">
        {children}
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar menu"
          className="absolute left-full top-4 ml-3 inline-flex h-9 w-9 items-center justify-center rounded-xl border border-white/15 bg-black/25 text-white transition hover:bg-black/40"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
