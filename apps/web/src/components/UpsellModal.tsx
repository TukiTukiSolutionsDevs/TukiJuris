"use client";

/**
 * UpsellModal — shown when a user clicks a locked feature.
 *
 * Explains the feature requires a paid plan and CTAs to /billing.
 * Uses planDisplayName() for consistent localised copy.
 */

import { X, Zap } from "lucide-react";
import { planDisplayName } from "@/lib/plans";

const FEATURE_LABELS: Record<string, string> = {
  pdf_export: "exportar conversaciones en PDF",
  file_upload: "adjuntar archivos al chat",
  byok_enabled: "conectar tu propia API key (BYOK)",
  team_seats: "gestión de equipo multi-usuario",
  priority_support: "soporte prioritario",
};

interface UpsellModalProps {
  feature: string;
  onClose: () => void;
}

export function UpsellModal({ feature, onClose }: UpsellModalProps) {
  const featureLabel = FEATURE_LABELS[feature] ?? feature;
  const proName = planDisplayName("pro");

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-sm mx-4 bg-[#0e0e12] border border-[rgba(79,70,51,0.3)] rounded-xl p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#7c7885] hover:text-on-surface transition-colors"
          aria-label="Cerrar"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Icon */}
        <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10 mb-4">
          <Zap className="w-5 h-5 text-primary" />
        </div>

        {/* Content */}
        <h2 className="font-['Newsreader'] text-xl font-bold text-on-surface mb-2">
          Función exclusiva
        </h2>
        <p className="text-sm text-[#a09ba8] mb-5">
          Para {featureLabel} necesitás el plan{" "}
          <span className="text-primary font-semibold">{proName}</span> o superior.
        </p>

        {/* CTA */}
        <a
          href="/billing"
          className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg bg-gradient-to-br from-primary to-primary-container text-on-primary text-sm font-bold hover:opacity-90 transition-opacity"
        >
          <Zap className="w-4 h-4" />
          Actualizar a {proName}
        </a>

        <button
          onClick={onClose}
          className="mt-3 w-full py-2 text-xs text-[#7c7885] hover:text-on-surface transition-colors"
        >
          Ahora no
        </button>
      </div>
    </div>
  );
}
