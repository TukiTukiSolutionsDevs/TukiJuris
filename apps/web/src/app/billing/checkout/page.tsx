"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CreditCard, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { AppLayout } from "@/components/AppLayout";
import { useAuth } from "@/lib/auth/AuthContext";
import { loadCulqi, tokenizeCard, type CardData } from "@/lib/culqi";

/**
 * /billing/checkout — destination after `POST /api/billing/{org}/checkout`.
 *
 * The backend returns a redirect URL to this page with:
 *   - provider=culqi
 *   - order_id (Culqi order)
 *   - plan
 *
 * While Culqi habilita en producción (NEXT_PUBLIC_CULQI_PUBLIC_KEY empty),
 * we render a "pagos en habilitación" notice so the user is not stuck on a 404.
 * The real PCI-safe card form swaps in once the key is set.
 */
function CheckoutInner() {
  const params = useSearchParams();
  const { authFetch } = useAuth();
  const [card, setCard] = useState<CardData>({
    card_number: "",
    cvv: "",
    expiration_month: "",
    expiration_year: "",
    email: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [ready, setReady] = useState<"loading" | "ok" | "unavailable">("loading");

  const provider = params.get("provider") || "culqi";
  const orderId = params.get("order_id") || "";
  const plan = params.get("plan") || "";

  useEffect(() => {
    if (!process.env.NEXT_PUBLIC_CULQI_PUBLIC_KEY) {
      setReady("unavailable");
      return;
    }
    loadCulqi()
      .then(() => setReady("ok"))
      .catch(() => setReady("unavailable"));
  }, []);

  const handlePay = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    try {
      const token = await tokenizeCard(card);
      // Send the token (NOT the PAN/CVV) to the backend to confirm the order.
      const res = await authFetch(`/api/billing/checkout/confirm`, {
        method: "POST",
        body: JSON.stringify({
          provider,
          order_id: orderId,
          token: token.id,
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        toast.error(body?.detail || "El pago fue rechazado");
        return;
      }
      toast.success("¡Pago aprobado! Activando tu plan…");
      window.location.href = "/billing?status=success";
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Error procesando el pago");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-xl mx-auto px-4 lg:px-6 py-12">
        <div className="flex items-center gap-3 mb-6">
          <CreditCard className="w-5 h-5 text-primary" />
          <h1 className="font-['Newsreader'] text-3xl font-bold text-on-surface">
            Confirma tu pago
          </h1>
        </div>

        {plan && (
          <p className="text-sm text-on-surface-variant mb-8">
            Estás suscribiéndote al plan{" "}
            <strong className="text-on-surface uppercase">{plan}</strong>.
          </p>
        )}

        {ready === "unavailable" ? (
          <div className="rounded-xl border border-primary/30 bg-primary/5 p-6 text-sm text-on-surface-variant">
            <p className="font-medium text-on-surface mb-2">
              Estamos habilitando los pagos con Culqi
            </p>
            <p>
              La integración con Culqi se completa durante los primeros días posteriores al
              lanzamiento. Te avisaremos por correo cuando puedas activar tu suscripción.
              Mientras tanto puedes seguir usando el plan Gratuito.
            </p>
            <div className="mt-4">
              <Link
                href="/billing"
                className="inline-flex items-center justify-center rounded-lg h-10 px-4 text-sm font-medium text-on-surface hover:text-primary border border-ghost-border hover:border-primary/30"
              >
                Volver a facturación
              </Link>
            </div>
          </div>
        ) : ready === "loading" ? (
          <div className="flex items-center gap-2 text-sm text-on-surface-variant">
            <Loader2 className="w-4 h-4 animate-spin" /> Cargando pasarela segura…
          </div>
        ) : (
          <form onSubmit={handlePay} className="space-y-4">
            <label className="block">
              <span className="text-xs uppercase tracking-widest text-on-surface-variant">
                Número de tarjeta
              </span>
              <input
                inputMode="numeric"
                autoComplete="cc-number"
                value={card.card_number}
                onChange={(e) => setCard((c) => ({ ...c, card_number: e.target.value }))}
                className="mt-1 w-full rounded-lg bg-surface-container border border-ghost-border px-3 py-2 text-sm"
                placeholder="4111 1111 1111 1111"
                required
              />
            </label>
            <div className="grid grid-cols-3 gap-3">
              <label className="block col-span-1">
                <span className="text-xs uppercase tracking-widest text-on-surface-variant">Mes</span>
                <input
                  inputMode="numeric"
                  autoComplete="cc-exp-month"
                  value={card.expiration_month}
                  onChange={(e) => setCard((c) => ({ ...c, expiration_month: e.target.value }))}
                  className="mt-1 w-full rounded-lg bg-surface-container border border-ghost-border px-3 py-2 text-sm"
                  placeholder="01"
                  required
                />
              </label>
              <label className="block col-span-1">
                <span className="text-xs uppercase tracking-widest text-on-surface-variant">Año</span>
                <input
                  inputMode="numeric"
                  autoComplete="cc-exp-year"
                  value={card.expiration_year}
                  onChange={(e) => setCard((c) => ({ ...c, expiration_year: e.target.value }))}
                  className="mt-1 w-full rounded-lg bg-surface-container border border-ghost-border px-3 py-2 text-sm"
                  placeholder="2030"
                  required
                />
              </label>
              <label className="block col-span-1">
                <span className="text-xs uppercase tracking-widest text-on-surface-variant">CVV</span>
                <input
                  inputMode="numeric"
                  autoComplete="cc-csc"
                  value={card.cvv}
                  onChange={(e) => setCard((c) => ({ ...c, cvv: e.target.value }))}
                  className="mt-1 w-full rounded-lg bg-surface-container border border-ghost-border px-3 py-2 text-sm"
                  placeholder="123"
                  required
                />
              </label>
            </div>
            <label className="block">
              <span className="text-xs uppercase tracking-widest text-on-surface-variant">
                Correo electrónico
              </span>
              <input
                type="email"
                autoComplete="email"
                value={card.email}
                onChange={(e) => setCard((c) => ({ ...c, email: e.target.value }))}
                className="mt-1 w-full rounded-lg bg-surface-container border border-ghost-border px-3 py-2 text-sm"
                required
              />
            </label>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center justify-center gap-2 rounded-xl h-11 px-6 text-sm font-bold text-on-primary gold-gradient disabled:opacity-50"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}
              {submitting ? "Procesando…" : "Pagar suscripción"}
            </button>
            <p className="text-xs text-on-surface/50">
              Pago seguro con Culqi. TukiJuris no almacena tu número de tarjeta ni CVV.
            </p>
          </form>
        )}
      </div>
    </AppLayout>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={null}>
      <CheckoutInner />
    </Suspense>
  );
}
