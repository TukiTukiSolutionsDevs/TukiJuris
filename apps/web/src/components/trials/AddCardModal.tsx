"use client";

import { useState } from "react";
import { Loader2, X, CreditCard } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { addCardToTrial } from "@/lib/api/trial";

interface Props {
  trialId: string;
  onClose: (success?: boolean) => void;
}

export function AddCardModal({ trialId, onClose }: Props) {
  const { authFetch } = useAuth();
  const [cardToken, setCardToken] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!cardToken.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await addCardToTrial(authFetch, trialId, cardToken.trim());
      onClose(true);
    } catch {
      setError("No se pudo registrar la tarjeta. Verifica los datos e intenta nuevamente.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      data-testid="add-card-modal"
    >
      <div className="bg-surface-container rounded-xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-primary" />
            <h2 className="font-semibold text-on-surface">Agregar tarjeta</h2>
          </div>
          <button
            onClick={() => onClose()}
            className="p-1 rounded hover:bg-surface-container-high"
            aria-label="Cerrar"
            data-testid="modal-close"
          >
            <X className="w-4 h-4 text-on-surface/60" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-on-surface/60 mb-1">Token de tarjeta</label>
            <input
              type="text"
              value={cardToken}
              onChange={(e) => setCardToken(e.target.value)}
              placeholder="tkn_..."
              className="w-full rounded-lg border border-on-surface/20 bg-surface px-3 py-2 text-sm text-on-surface focus:outline-none focus:border-primary"
              data-testid="card-token-input"
            />
          </div>

          {error && (
            <p className="text-xs text-red-600" data-testid="card-error">
              {error}
            </p>
          )}

          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={() => onClose()}
              className="px-4 py-2 rounded-lg text-sm text-on-surface/60 hover:bg-surface-container-high transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || !cardToken.trim()}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-on-primary text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
              data-testid="submit-card-btn"
            >
              {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
              Guardar tarjeta
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
