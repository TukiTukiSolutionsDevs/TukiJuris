"use client";

const STATUS_CONFIG: Record<string, { label: string; cls: string }> = {
  active: { label: "Activa", cls: "text-green-700 bg-green-50" },
  expired: { label: "Vencida", cls: "text-red-700 bg-red-50" },
  converted: { label: "Convertida", cls: "text-blue-700 bg-blue-50" },
  cancelled: { label: "Cancelada", cls: "text-gray-500 bg-gray-100" },
  charged: { label: "Cobrada", cls: "text-purple-700 bg-purple-50" },
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
