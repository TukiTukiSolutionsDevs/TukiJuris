"use client";

import { useState, useRef, useEffect } from "react";
import { HelpCircle, Keyboard, BookOpen, Activity, X } from "lucide-react";
import Link from "next/link";

interface HelpPopoverProps {
  onShowShortcuts?: () => void;
}

export default function HelpPopover({ onShowShortcuts }: HelpPopoverProps) {
  const [open, setOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open]);

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => setOpen((prev) => !prev)}
        aria-label="Abrir ayuda"
        aria-expanded={open}
        aria-haspopup="true"
        className="flex items-center justify-center w-7 h-7 rounded-lg border border-[#2A2A35] text-[#6B7280] hover:text-gray-300 hover:border-[#3A3A48] transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500/50 text-xs font-bold"
      >
        ?
      </button>

      {open && (
        <div
          ref={popoverRef}
          role="menu"
          aria-label="Menu de ayuda"
          className="absolute bottom-full right-0 mb-2 w-56 bg-[#111116] border border-[#2A2A35] rounded-xl shadow-xl overflow-hidden z-20"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2.5 border-b border-[#1A1A22]">
            <span className="text-xs font-medium text-gray-300">Ayuda</span>
            <button
              onClick={() => setOpen(false)}
              aria-label="Cerrar menu de ayuda"
              className="p-0.5 rounded text-[#6B7280] hover:text-gray-300 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500/50"
            >
              <X className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>

          <div className="py-1">
            {/* Keyboard shortcuts */}
            <button
              role="menuitem"
              onClick={() => {
                setOpen(false);
                onShowShortcuts?.();
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-sm text-[#9CA3AF] hover:bg-[#1A1A22] hover:text-gray-200 transition-colors text-left focus:outline-none focus:bg-[#1A1A22]"
            >
              <Keyboard className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span>Atajos de teclado</span>
                <kbd className="ml-auto text-xs bg-[#1A1A22] border border-[#3A3A48] rounded px-1 font-mono text-[#6B7280]">
                Ctrl+/
              </kbd>
            </button>

            {/* Guide link */}
            <Link
              href="/guia"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-3 py-2 text-sm text-[#9CA3AF] hover:bg-[#1A1A22] hover:text-gray-200 transition-colors focus:outline-none focus:bg-[#1A1A22]"
            >
              <BookOpen className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span>Guia de uso</span>
            </Link>

            {/* Status link */}
            <Link
              href="/status"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 px-3 py-2 text-sm text-[#9CA3AF] hover:bg-[#1A1A22] hover:text-gray-200 transition-colors focus:outline-none focus:bg-[#1A1A22]"
            >
              <Activity className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span>Estado del servicio</span>
            </Link>
          </div>

          {/* Version */}
          <div className="px-3 py-2 border-t border-[#1A1A22]">
            <p className="text-[10px] text-[#6B7280]">
              TukiJuris{" "}
              <span className="text-gray-500">v0.3.0</span>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
