"use client";

import { useEffect, useState } from "react";
import { Check, Copy, ShieldAlert, X } from "lucide-react";

interface CopyOnceModalProps {
  /** Whether the modal is visible */
  open: boolean;
  /** The secret value to display exactly once */
  secret: string;
  /** Called only when the user explicitly clicks the close button */
  onClose: () => void;
}

/**
 * CopyOnceModal — displays a secret exactly once.
 *
 * Security UX (non-negotiable):
 *  - Click-outside DOES NOT close the modal.
 *  - Escape key DOES NOT close the modal.
 *  - Only the explicit "Entendido, cerrar" button triggers onClose.
 */
export function CopyOnceModal({ open, secret, onClose }: CopyOnceModalProps) {
  const [copied, setCopied] = useState(false);

  // Reset copied state every time the modal opens with a new secret.
  // Adjust during render (not in an effect) to avoid cascading renders.
  const [prevOpen, setPrevOpen] = useState(open);
  if (prevOpen !== open) {
    setPrevOpen(open);
    if (open) setCopied(false);
  }

  // Block Escape in capture phase — no listener downstream can dismiss this modal
  useEffect(() => {
    if (!open) return;
    const block = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    document.addEventListener("keydown", block, true);
    return () => document.removeEventListener("keydown", block, true);
  }, [open]);

  if (!open) return null;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard unavailable — user can still select-all and copy manually
    }
  };

  return (
    // Intentionally NO onClick on the backdrop — click-outside must NOT close this modal
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      data-testid="copy-once-backdrop"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="copy-once-title"
        className="relative mx-4 w-full max-w-md rounded-xl border border-[rgba(79,70,51,0.3)] bg-[#0e0e12] p-6 shadow-2xl"
      >
        <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-amber-500/10">
          <ShieldAlert className="h-5 w-5 text-amber-400" />
        </div>

        <h2
          id="copy-once-title"
          className="mb-1 font-['Newsreader'] text-xl font-bold text-on-surface"
        >
          Guardá tu clave ahora
        </h2>
        <p className="mb-5 text-sm leading-6 text-on-surface/55">
          Esta es la <strong className="text-on-surface">única vez</strong>{" "}
          que se muestra la clave completa. Copiala y guardala en un lugar
          seguro — no podrás volver a verla.
        </p>

        <div
          className="mb-4 select-all break-all rounded-lg border border-[rgba(79,70,51,0.2)] bg-surface px-3 py-3 font-mono text-xs text-on-surface"
          data-testid="copy-once-secret"
        >
          {secret}
        </div>

        <button
          type="button"
          onClick={() => void handleCopy()}
          className="mb-3 flex w-full items-center justify-center gap-2 rounded-lg border border-[rgba(79,70,51,0.2)] py-2.5 text-sm font-medium text-on-surface/80 transition-colors hover:border-primary/30 hover:text-on-surface"
          data-testid="copy-once-copy-btn"
        >
          {copied ? (
            <>
              <Check className="h-4 w-4 text-[#6ee7b7]" />
              <span className="text-[#6ee7b7]">Copiado</span>
            </>
          ) : (
            <>
              <Copy className="h-4 w-4" />
              Copiar clave
            </>
          )}
        </button>

        <button
          type="button"
          onClick={onClose}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-br from-primary to-primary-container py-2.5 text-sm font-bold text-on-primary transition-opacity hover:opacity-90"
          data-testid="copy-once-close-btn"
        >
          <X className="h-4 w-4" />
          Entendido, cerrar
        </button>
      </div>
    </div>
  );
}
