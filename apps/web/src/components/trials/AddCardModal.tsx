"use client";

import { useState } from "react";
import { Loader2, X, CreditCard } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { addCardToTrial } from "@/lib/api/trial";

interface Props {
  /**
   * Trial id is kept in the public API for callers but is NOT sent to the
   * backend — `/api/trials/add-card` resolves the trial from the JWT subject.
   * It stays here so the modal can be opened in a trial-scoped UI flow.
   */
  trialId: string;
  onClose: (success?: boolean) => void;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function AddCardModal({ trialId: _trialId, onClose }: Props) {
  const { authFetch, user } = useAuth();
  const [cardToken, setCardToken] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  // Prefill with the session email when available; the field stays editable so
  // restored sessions without an email claim can still complete the flow.
  const [email, setEmail] = useState(user?.email ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit =
    cardToken.trim().length >= 4 &&
    firstName.trim().length > 0 &&
    lastName.trim().length > 0 &&
    EMAIL_RE.test(email.trim());

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      await addCardToTrial(authFetch, {
        provider: "culqi",
        token_id: cardToken.trim(),
        customer_info: {
          email: email.trim(),
          first_name: firstName.trim(),
          last_name: lastName.trim(),
        },
      });
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
            <label htmlFor="card-token" className="block text-xs text-on-surface/60 mb-1">
              Token de tarjeta
            </label>
            <input
              id="card-token"
              type="text"
              value={cardToken}
              onChange={(e) => setCardToken(e.target.value)}
              placeholder="tkn_..."
              className="w-full rounded-lg border border-on-surface/20 bg-surface px-3 py-2 text-sm text-on-surface focus:outline-none focus:border-primary"
              data-testid="card-token-input"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="card-first-name" className="block text-xs text-on-surface/60 mb-1">
                Nombre
              </label>
              <input
                id="card-first-name"
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="Juan"
                className="w-full rounded-lg border border-on-surface/20 bg-surface px-3 py-2 text-sm text-on-surface focus:outline-none focus:border-primary"
                data-testid="first-name-input"
              />
            </div>
            <div>
              <label htmlFor="card-last-name" className="block text-xs text-on-surface/60 mb-1">
                Apellido
              </label>
              <input
                id="card-last-name"
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Pérez"
                className="w-full rounded-lg border border-on-surface/20 bg-surface px-3 py-2 text-sm text-on-surface focus:outline-none focus:border-primary"
                data-testid="last-name-input"
              />
            </div>
          </div>

          <div>
            <label htmlFor="card-email" className="block text-xs text-on-surface/60 mb-1">
              Email
            </label>
            <input
              id="card-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tu@correo.pe"
              className="w-full rounded-lg border border-on-surface/20 bg-surface px-3 py-2 text-sm text-on-surface focus:outline-none focus:border-primary"
              data-testid="card-email-input"
              autoComplete="email"
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
              disabled={submitting || !canSubmit}
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
