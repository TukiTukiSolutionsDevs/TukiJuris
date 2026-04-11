"use client";

import { useState, useEffect, useCallback } from "react";
import {
  CreditCard,
  Loader2,
  Check,
  AlertTriangle,
  Zap,
  Building2,
  Key,
} from "lucide-react";
import { getToken } from "@/lib/auth";
import { AppLayout } from "@/components/AppLayout";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// UsageStats kept for backward compat with API (not displayed)
interface UsageStats {
  queries_used: number;
  queries_limit: number;
  period: string;
}

interface Subscription {
  plan: string;
  status: string;
  current_period_start?: string;
}

interface BillingConfig {
  payments_enabled: boolean;
  providers: { name: string; enabled: boolean }[];
}

interface Plan {
  id: string;
  name: string;
  price: string;
  period?: string;
  badge?: string;
  features: string[];
  byok_note: string;
  cta: string;
  cta_disabled: boolean;
  highlighted: boolean;
}

const STATIC_PLANS: Plan[] = [
  {
    id: "free",
    name: "Gratuito",
    price: "S/ 0",
    period: "/mes",
    badge: "BETA",
    features: [
      "10 consultas por día",
      "Chat legal con 11 áreas",
      "Búsqueda normativa",
      "Trae tu propia clave de IA (BYOK)",
      "1 organización",
      "Historial 30 días",
      "Modelos free incluidos próximamente",
    ],
    byok_note: "Conectá tu propia API key. Modelos free próximamente.",
    cta: "Tu plan actual",
    cta_disabled: true,
    highlighted: false,
  },
  {
    id: "base",
    name: "Profesional",
    price: "S/ 70",
    period: "/mes",
    features: [
      "Todo lo de Gratuito",
      "100 consultas por día",
      "Analytics avanzado",
      "Exportar PDF",
      "Carpetas y Etiquetas",
      "Historial ilimitado",
      "Marcadores",
      "Soporte prioritario",
    ],
    byok_note: "Conectá tu propia API key",
    cta: "Actualizar a Profesional",
    cta_disabled: false,
    highlighted: true,
  },
  {
    id: "enterprise",
    name: "Estudio",
    price: "Contactar",
    period: "",
    features: [
      "Todo lo de Profesional",
      "Consultas ilimitadas",
      "Soporte dedicado",
      "Integraciones API",
      "Multi-organización",
      "SDKs y webhooks",
      "SSO empresarial",
      "Members ilimitados",
    ],
    byok_note: "Conectá tu propia API key",
    cta: "Contactar ventas",
    cta_disabled: false,
    highlighted: false,
  },
];

const PLAN_COLORS: Record<string, string> = {
  free: "bg-[#25242b] text-[#a09ba8]",
  base: "bg-primary/10 text-primary",
  enterprise: "bg-purple-500/20 text-purple-400",
};

const PLAN_LABELS: Record<string, string> = {
  free: "Gratuito",
  base: "Profesional",
  enterprise: "Estudio",
};

export default function BillingPage() {
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [billingConfig, setBillingConfig] = useState<BillingConfig | null>(null);
  const [orgId, setOrgId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);

  const authHeaders = () => ({
    "Content-Type": "application/json",
    Authorization: "Bearer " + getToken(),
  });

  const loadBillingData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [configRes, orgRes] = await Promise.allSettled([
        fetch(`${API_URL}/api/billing/config`),
        fetch(`${API_URL}/api/organizations/`, { headers: authHeaders() }),
      ]);

      if (configRes.status === "fulfilled" && configRes.value.ok) {
        setBillingConfig(await configRes.value.json());
      }

      if (orgRes.status === "rejected" || !("value" in orgRes) || !orgRes.value.ok) {
        throw new Error("No se pudo cargar la organización");
      }
      const orgData = await orgRes.value.json();
      const orgs = Array.isArray(orgData) ? orgData : orgData.organizations || [];

      if (orgs.length > 0) {
        const oid = orgs[0].id;
        setOrgId(oid);

        const [usageRes, subRes] = await Promise.allSettled([
          fetch(`${API_URL}/api/billing/${oid}/usage`, { headers: authHeaders() }),
          fetch(`${API_URL}/api/billing/${oid}/subscription`, { headers: authHeaders() }),
        ]);

        if (usageRes.status === "fulfilled" && usageRes.value.ok) {
          setUsage(await usageRes.value.json());
        }
        if (subRes.status === "fulfilled" && subRes.value.ok) {
          setSubscription(await subRes.value.json());
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error de red");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBillingData();
  }, [loadBillingData]);

  const handleCheckout = async (planId: string) => {
    if (!orgId) return;

    // Enterprise goes to mailto
    if (planId === "enterprise") {
      window.location.href =
        "mailto:ventas@tukijuris.net.pe?subject=Plan%20Enterprise%20TukiJuris";
      return;
    }

    setCheckoutLoading(planId);
    try {
      const token = getToken();
      const res = await fetch(`${API_URL}/api/billing/${orgId}/checkout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ plan: planId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        alert(err?.detail || "Error al procesar el pago");
        return;
      }
      const { checkout_url } = await res.json();
      window.location.href = checkout_url;
    } catch {
      alert("Error de conexión. Intentá de nuevo.");
    } finally {
      setCheckoutLoading(null);
    }
  };

  const currentPlan = subscription?.plan || "free";
  const paymentsEnabled = billingConfig?.payments_enabled ?? false;
  const hasPaidSubscription = currentPlan !== "free";

  const getPlanCta = (
    plan: Plan
  ): { label: string; disabled: boolean; action?: () => void } => {
    const isCurrentPlan = plan.id === currentPlan;

    if (isCurrentPlan) {
      return { label: "Tu plan actual", disabled: true };
    }

    if (plan.id === "free") {
      return { label: "Disponible en downgrade", disabled: true };
    }

    if (plan.id === "enterprise") {
      return {
        label: "Contactar ventas",
        disabled: false,
        action: () => handleCheckout("enterprise"),
      };
    }

    // Base plan
    return {
      label: checkoutLoading === plan.id ? "Redirigiendo..." : "Actualizar a Profesional",
      disabled: checkoutLoading === plan.id,
      action: () => handleCheckout(plan.id),
    };
  };

  // Suppress unused variable lint warning — usage kept for API compat
  void usage;
  void hasPaidSubscription;

  return (
    <AppLayout>
      <div className="flex min-h-full flex-col text-on-surface">
        {/* Page header */}
        <div className="border-b border-[rgba(79,70,51,0.15)] px-4 lg:px-6 py-4 flex items-center gap-3 sticky top-0 z-10 bg-[#0e0e12]">
          <CreditCard className="w-5 h-5 text-primary" />
          <h1 className="font-['Newsreader'] text-4xl font-bold text-on-surface leading-none">
            Facturación y Planes
          </h1>
          {!loading && (
            <span
              className={`ml-auto text-[10px] px-2 py-1 rounded-lg font-medium ${
                paymentsEnabled
                  ? "bg-green-500/20 text-green-400"
                  : "bg-[#25242b] text-[#a09ba8]"
              }`}
            >
              {paymentsEnabled ? "Pagos activos" : "Modo beta"}
            </span>
          )}
        </div>

        <div className="max-w-5xl mx-auto px-4 lg:px-6 py-6 sm:py-8">
          {/* Beta Banner — only shown when payments not configured */}
          {!paymentsEnabled && (
            <div className="flex items-start sm:items-center gap-3 bg-primary/10 border border-primary/20 rounded-lg px-5 py-4 mb-8">
              <Zap className="w-5 h-5 text-primary shrink-0 mt-0.5 sm:mt-0" />
              <div>
                <p className="text-sm font-semibold text-primary">Beta gratuita</p>
                <p className="text-xs text-primary/70 mt-0.5">
                  Acceso completo sin costo durante la beta. Sin compromiso ni
                  tarjeta de crédito.
                </p>
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg px-4 py-3 mb-6 text-sm">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-24 gap-3">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
              <p className="text-sm text-[#7c7885]">
                Cargando información de facturación...
              </p>
            </div>
          ) : (
            <>
              {/* Current Plan */}
              {orgId && (
                <div className="mb-8 sm:mb-10">
                  <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-5 inline-flex flex-col gap-3 min-w-[200px]">
                    <div className="flex items-center gap-2">
                      <CreditCard className="w-4 h-4 text-primary" />
                      <h2 className="text-sm font-semibold text-on-surface">Plan actual</h2>
                    </div>
                    <div className="flex items-center gap-3">
                      <span
                        className={`text-sm font-bold px-3 py-1 rounded-lg ${
                          PLAN_COLORS[currentPlan] || PLAN_COLORS.free
                        }`}
                      >
                        {PLAN_LABELS[currentPlan] || currentPlan}
                      </span>
                      {subscription?.status && (
                        <span
                          className={`text-xs capitalize ${
                            subscription.status === "past_due"
                              ? "text-red-400"
                              : "text-[#7c7885]"
                          }`}
                        >
                          {subscription.status === "past_due"
                            ? "Pago pendiente"
                            : subscription.status}
                        </span>
                      )}
                    </div>
                    {subscription?.current_period_start && (
                      <p className="text-xs text-[#7c7885]">
                        Activo desde{" "}
                        {new Date(subscription.current_period_start).toLocaleDateString("es-PE")}
                      </p>
                    )}
                    <p className="text-xs text-[#7c7885]">
                      Para cambiar o cancelar tu plan, contacta a{" "}
                      <a
                        href="mailto:soporte@tukijuris.net.pe"
                        className="text-primary hover:text-primary-container transition-colors"
                      >
                        soporte@tukijuris.net.pe
                      </a>
                    </p>
                  </div>
                </div>
              )}

              {/* BYOK note */}
              <div className="flex items-start gap-3 bg-primary/10 border border-primary/20 rounded-lg px-5 py-4 mb-8">
                <Key className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-primary">
                    Traé tu propia clave de IA
                  </p>
                  <p className="text-xs text-primary/70 mt-0.5">
                    TukiJuris no incluye modelos de IA. Conectá tu propia API key en{" "}
                    <a
                      href="/configuracion"
                      className="underline hover:text-primary"
                    >
                      Configuración → API Keys
                    </a>
                    . El costo de uso del modelo lo cobra directamente el proveedor.
                  </p>
                </div>
              </div>

              {/* Plan Comparison */}
              <h2 className="font-['Newsreader'] text-3xl font-bold text-on-surface mb-6">
                Comparar planes
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 md:items-start">
                {STATIC_PLANS.map((plan) => {
                  const isCurrentPlan = plan.id === currentPlan;
                  const cta = getPlanCta(plan);
                  return (
                    <div
                      key={plan.id}
                      className={`relative flex flex-col p-6 rounded-lg ${
                        plan.highlighted
                          ? "bg-surface-container border-2 border-primary-container md:scale-105 shadow-2xl shadow-primary/5"
                          : "bg-surface border border-[rgba(79,70,51,0.15)]"
                      }`}
                    >
                      {/* Popular badge */}
                      {plan.highlighted && (
                        <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                          <span className="bg-primary-container text-on-primary text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-lg">
                            Popular
                          </span>
                        </div>
                      )}

                      {/* Plan Header */}
                      <div className="mb-5">
                        <div className="flex items-center gap-2 mb-3">
                          {plan.id === "free" && (
                            <CreditCard className="w-4 h-4 text-[#a09ba8]" />
                          )}
                          {plan.id === "base" && (
                            <Zap className="w-4 h-4 text-primary" />
                          )}
                          {plan.id === "enterprise" && (
                            <Building2 className="w-4 h-4 text-purple-400" />
                          )}
                          <h3 className="font-['Newsreader'] text-xl font-bold text-on-surface">
                            {plan.name}
                          </h3>
                          {plan.badge && (
                            <span className="ml-auto text-[10px] font-bold uppercase tracking-widest bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-lg">
                              {plan.badge}
                            </span>
                          )}
                          {isCurrentPlan && (
                            <span className="ml-auto text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-lg font-semibold">
                              Activo
                            </span>
                          )}
                        </div>
                        <div className="flex items-end gap-1">
                          <span className="font-['Newsreader'] text-3xl font-bold text-primary">
                            {plan.price}
                          </span>
                          {plan.period && (
                            <span className="text-sm text-[#7c7885] mb-1">{plan.period}</span>
                          )}
                        </div>
                      </div>

                      {/* Features */}
                      <div className="flex-1 space-y-2.5 mb-5">
                        {plan.features.map((feature) => (
                          <div key={feature} className="flex items-start gap-2">
                            <Check className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
                            <span className="text-xs text-[#a09ba8]">{feature}</span>
                          </div>
                        ))}
                      </div>

                      {/* BYOK note per plan */}
                      <div className="flex items-center gap-2 mb-5 px-3 py-2 bg-primary/5 border border-primary/10 rounded-lg">
                        <Key className="w-3 h-3 text-primary/50 shrink-0" />
                        <span className="text-[10px] text-primary/60">{plan.byok_note}</span>
                      </div>

                      {/* CTA Button */}
                      <button
                        onClick={cta.action}
                        disabled={cta.disabled}
                        className={`w-full py-2.5 rounded-lg text-sm font-bold transition-opacity flex items-center justify-center gap-1.5 ${
                          isCurrentPlan
                            ? "bg-primary/10 text-primary border border-primary/20 cursor-default"
                            : cta.action && !cta.disabled
                            ? "bg-gradient-to-br from-primary to-primary-container hover:opacity-90 text-on-primary cursor-pointer"
                            : "border border-[rgba(79,70,51,0.15)] text-on-surface/40 cursor-not-allowed"
                        }`}
                      >
                        {checkoutLoading === plan.id && (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        )}
                        {isCurrentPlan ? "Tu plan actual" : cta.label}
                      </button>
                    </div>
                  );
                })}
              </div>

              {/* Payment methods */}
              <div className="mt-8 text-center">
                <p className="text-xs text-[#7c7885] mb-3">Métodos de pago aceptados</p>
                <div className="flex items-center justify-center gap-3 text-[#a09ba8]">
                  {["Visa", "Mastercard", "Yape", "BCP"].map((method) => (
                    <span
                      key={method}
                      className="text-xs border border-[rgba(79,70,51,0.15)] rounded-lg px-2 py-1 bg-surface-container-low"
                    >
                      {method}
                    </span>
                  ))}
                </div>
              </div>

              {/* Danger zone — contact support */}
              {orgId && currentPlan !== "free" && (
                <div className="mt-10 border border-[#ffb4ab]/20 rounded-lg p-6">
                  <h3 className="text-sm font-semibold text-red-300 mb-1">Zona de peligro</h3>
                  <p className="text-xs text-[#7c7885] mb-4">
                    Para cancelar o modificar tu suscripción contacta a soporte.
                  </p>
                  <a
                    href="mailto:soporte@tukijuris.net.pe?subject=Cancelar%20suscripción"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold text-red-300 border border-[#ffb4ab]/30 hover:bg-[#ffb4ab]/10 transition-colors"
                  >
                    Solicitar cancelación
                  </a>
                </div>
              )}

              {/* Footer note */}
              <p className="text-center text-xs text-[#7c7885] mt-8">
                Los pagos son procesados de forma segura por MercadoPago y Culqi. Para consultas
                sobre planes Enterprise, contactá a{" "}
                <span className="text-[#a09ba8]">ventas@tukijuris.net.pe</span>
              </p>
            </>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
