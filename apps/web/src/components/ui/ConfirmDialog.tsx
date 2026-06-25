"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, X } from "lucide-react";

export type ConfirmVariant = "default" | "danger" | "warning";

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: ConfirmVariant;
  /**
   * When provided, the user must type this exact string to enable the confirm
   * button. Used for destructive actions like "ELIMINAR MI CUENTA".
   */
  requireTyping?: string;
  /** Disable both buttons + show spinner on confirm */
  loading?: boolean;
  onConfirm: () => void | Promise<void>;
}

const VARIANT_BUTTON: Record<ConfirmVariant, string> = {
  default:
    "gold-gradient text-on-primary hover:opacity-95 disabled:opacity-50",
  danger:
    "bg-[rgba(224,107,92,0.12)] text-status-danger border border-[rgba(224,107,92,0.3)] hover:bg-[rgba(224,107,92,0.18)] disabled:opacity-50",
  warning:
    "bg-[rgba(232,179,14,0.12)] text-status-warning border border-[rgba(232,179,14,0.3)] hover:bg-[rgba(232,179,14,0.18)] disabled:opacity-50",
};

/**
 * Canonical confirm dialog — replaces native confirm() across the workspace.
 * Respects dark/light theme, supports requireTyping for destructive actions.
 *
 * Usage:
 *   const [open, setOpen] = useState(false);
 *   <ConfirmDialog
 *     open={open}
 *     onOpenChange={setOpen}
 *     title="Eliminar conversación"
 *     description="Esta acción es irreversible..."
 *     variant="danger"
 *     onConfirm={handleDelete}
 *   />
 */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  variant = "default",
  requireTyping,
  loading = false,
  onConfirm,
}: ConfirmDialogProps) {
  const [typedText, setTypedText] = useState("");
  const confirmRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const close = useCallback(() => {
    if (loading) return;
    setTypedText("");
    onOpenChange(false);
  }, [loading, onOpenChange]);

  // Focus management + Escape
  useEffect(() => {
    if (!open) return;
    const target = requireTyping ? inputRef.current : confirmRef.current;
    target?.focus();

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
      if (e.key === "Enter" && !requireTyping) {
        e.preventDefault();
        void onConfirm();
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, requireTyping, close, onConfirm]);

  if (!open) return null;

  const typingMatches = !requireTyping || typedText === requireTyping;
  const confirmDisabled = loading || !typingMatches;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
      className="fixed inset-0 z-[100] flex items-center justify-center px-4"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={close}
        aria-hidden="true"
      />

      {/* Panel */}
      <div className="card-canon relative z-10 w-full max-w-[480px] p-6 shadow-[0_24px_48px_rgba(0,0,0,0.65)]">
        <button
          type="button"
          onClick={close}
          aria-label="Cerrar"
          disabled={loading}
          className="absolute right-4 top-4 inline-flex h-8 w-8 items-center justify-center rounded-lg text-on-surface-subtle transition-colors hover:bg-surface-container hover:text-on-surface-strong disabled:opacity-50"
        >
          <X className="h-4 w-4" strokeWidth={1.8} />
        </button>

        <h2
          id="confirm-title"
          className="font-['Newsreader'] text-[21px] font-bold leading-tight tracking-[-0.01em] text-on-surface-strong"
        >
          {title}
        </h2>

        {description ? (
          <div className="mt-3 text-[13.5px] leading-6 text-on-surface-variant">
            {description}
          </div>
        ) : null}

        {requireTyping ? (
          <div className="mt-5">
            <label className="label-input">
              Escribí{" "}
              <span className="text-on-surface-strong">{requireTyping}</span> para
              confirmar
            </label>
            <input
              ref={inputRef}
              type="text"
              value={typedText}
              onChange={(e) => setTypedText(e.target.value)}
              disabled={loading}
              className="control-surface h-10 w-full rounded-lg px-3 text-[13px] text-on-surface placeholder-on-surface/30 focus:border-primary focus:outline-none"
              placeholder={requireTyping}
              autoComplete="off"
              spellCheck={false}
            />
          </div>
        ) : null}

        <div className="mt-6 flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={close}
            disabled={loading}
            className="h-10 rounded-lg border border-outline-variant bg-transparent px-4 text-[12.5px] font-semibold text-on-surface-variant transition-colors hover:border-outline hover:text-on-surface-strong disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            ref={confirmRef}
            type="button"
            onClick={() => void onConfirm()}
            disabled={confirmDisabled}
            className={`inline-flex h-10 items-center justify-center gap-2 rounded-lg px-5 text-[12.5px] font-bold transition-opacity ${VARIANT_BUTTON[variant]}`}
          >
            {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
