"use client";

const STATUS_CONFIG: Record<string, { label: string; cls: string }> = {
  active: { label: "Activa", cls: "text-green-700 bg-green-50" },
  charged: { label: "Cobrada", cls: "text-purple-700 bg-purple-50" },
  charge_failed: { label: "Cobro fallido", cls: "text-orange-700 bg-orange-50" },
  downgraded: { label: "Vencida", cls: "text-red-700 bg-red-50" },
  canceled_pending: { label: "Cancelando", cls: "text-yellow-700 bg-yellow-50" },
  canceled: { label: "Cancelada", cls: "text-gray-500 bg-gray-100" },
};

export function TrialStatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, cls: "text-gray-500 bg-gray-100" };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium uppercase tracking-wide ${cfg.cls}`}
      data-testid="trial-status-badge"
    >
      {cfg.label}
    </span>
  );
}
