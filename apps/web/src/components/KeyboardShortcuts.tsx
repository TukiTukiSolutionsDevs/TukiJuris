"use client";

import { useEffect, useState, useCallback } from "react";
import { X, Keyboard } from "lucide-react";

interface ShortcutDef {
  action: string;
  description: string;
}

const SHORTCUTS: Record<string, ShortcutDef> = {
  "Ctrl+K": { action: "focus-search", description: "Enfocar busqueda" },
  "Ctrl+N": { action: "new-chat", description: "Nueva consulta" },
  "Ctrl+/": { action: "show-shortcuts", description: "Mostrar atajos" },
  Escape: { action: "close-modal", description: "Cerrar modal/menu" },
  "Ctrl+Shift+S": { action: "toggle-sidebar", description: "Mostrar/ocultar sidebar" },
  "Ctrl+Enter": { action: "send-message", description: "Enviar mensaje" },
  "Ctrl+B": { action: "bookmarks", description: "Ir a marcadores" },
  "Ctrl+H": { action: "history", description: "Ir a historial" },
};

interface KeyboardShortcutsProps {
  onNewChat?: () => void;
  onToggleSidebar?: () => void;
  onFocusSearch?: () => void;
  onSendMessage?: () => void;
}

export default function KeyboardShortcuts({
  onNewChat,
  onToggleSidebar,
  onFocusSearch,
  onSendMessage,
}: KeyboardShortcutsProps) {
  const [showModal, setShowModal] = useState(false);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const ctrl = e.ctrlKey || e.metaKey;
      const shift = e.shiftKey;
      const key = e.key;

      // Ctrl+/ — show shortcuts modal
      if (ctrl && key === "/") {
        e.preventDefault();
        setShowModal((prev) => !prev);
        return;
      }

      // Escape — close modal (or delegate to other handlers)
      if (key === "Escape") {
        if (showModal) {
          e.preventDefault();
          setShowModal(false);
          return;
        }
        // Let other Escape handlers run (don't preventDefault)
        return;
      }

      // Don't intercept when typing in inputs/textareas
      const target = e.target as HTMLElement;
      const isEditable =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      // Ctrl+Enter — send message (works inside input)
      if (ctrl && key === "Enter" && isEditable) {
        e.preventDefault();
        onSendMessage?.();
        return;
      }

      // All remaining shortcuts below should NOT fire from inside editable fields
      if (isEditable) return;

      // Ctrl+K — focus search
      if (ctrl && key === "k") {
        e.preventDefault();
        onFocusSearch?.();
        return;
      }

      // Ctrl+N — new chat
      if (ctrl && key === "n") {
        e.preventDefault();
        onNewChat?.();
        return;
      }

      // Ctrl+Shift+S — toggle sidebar
      if (ctrl && shift && key === "S") {
        e.preventDefault();
        onToggleSidebar?.();
        return;
      }

      // Ctrl+B — bookmarks
      if (ctrl && key === "b") {
        e.preventDefault();
        window.location.href = "/marcadores";
        return;
      }

      // Ctrl+H — history (skip if browser would normally handle it)
      if (ctrl && key === "h") {
        e.preventDefault();
        window.location.href = "/historial";
        return;
      }
    },
    [showModal, onNewChat, onToggleSidebar, onFocusSearch, onSendMessage]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  if (!showModal) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={() => setShowModal(false)}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative w-full max-w-lg bg-[#111116] border border-[#2A2A35] rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1A1A22]">
          <div className="flex items-center gap-2.5">
            <Keyboard className="w-5 h-5 text-amber-500" aria-hidden="true" />
            <h2 id="shortcuts-title" className="font-semibold text-white">
              Atajos de Teclado
            </h2>
          </div>
          <button
            onClick={() => setShowModal(false)}
            aria-label="Cerrar modal de atajos"
            className="p-1.5 rounded-lg text-[#9CA3AF] hover:text-white hover:bg-[#1A1A22] transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500/50"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        {/* Shortcuts grid */}
        <div className="p-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {Object.entries(SHORTCUTS).map(([keys, { description }]) => (
            <div
              key={keys}
              className="flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg bg-[#1A1A22]"
            >
              <span className="text-sm text-gray-300">{description}</span>
              <div className="flex items-center gap-1 shrink-0">
                {keys.split("+").map((k, i, arr) => (
                  <span key={k} className="flex items-center gap-1">
                    <kbd className="inline-flex items-center justify-center min-w-[1.75rem] h-7 px-1.5 rounded bg-[#2A2A35] border border-[#3A3A48] text-xs font-mono text-gray-200 shadow-sm">
                      {k}
                    </kbd>
                    {i < arr.length - 1 && (
                      <span className="text-[#6B7280] text-xs">+</span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer hint */}
        <div className="px-6 pb-5">
          <p className="text-xs text-[#6B7280] text-center">
            Presiona{" "}
            <kbd className="inline-flex items-center justify-center h-5 px-1.5 rounded bg-[#2A2A35] border border-[#3A3A48] text-xs font-mono text-[#9CA3AF]">
              Escape
            </kbd>{" "}
            para cerrar
          </p>
        </div>
      </div>
    </div>
  );
}
