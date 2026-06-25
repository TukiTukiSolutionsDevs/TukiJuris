"use client";

import { useState } from "react";
import {
  ChevronRight, ChevronLeft, Zap, HelpCircle, Building2, Mail,
} from "lucide-react";
import type { StepProps } from "../_types";

/**
 * Step 4 — "API Key" (renamed to "Motor IA" UX-side).
 *
 * BYOK is NOT self-service for individual clients. It is only available on
 * the Enterprise plan, which requires contacting sales. This step therefore
 * shows only the free-tier option (Gemini Flash) plus an Enterprise CTA.
 */

export function StepApiKey({ onNext, onBack }: StepProps) {
  const [showHelp, setShowHelp] = useState(false);

  return (
    <div className="max-w-lg mx-auto">
      <h2 className="font-['Newsreader'] text-2xl sm:text-3xl text-on-surface mb-1 leading-tight">
        Motor de Inteligencia Artificial
      </h2>
      <p className="text-on-surface-variant text-sm mb-6">
        Tu cuenta arranca con el modelo gratuito incluido.
      </p>

      <button
        onClick={() => setShowHelp(!showHelp)}
        className="flex items-center gap-1.5 text-xs text-primary hover:underline mb-4"
      >
        <HelpCircle className="w-3.5 h-3.5" />
        {showHelp ? "Ocultar explicacion" : "Como funciona el motor de IA?"}
      </button>

      {showHelp && (
        <div className="mb-6 p-4 rounded-lg bg-primary/5 border-2 border-primary/15 text-sm text-on-surface-variant space-y-2">
          <p>
            <strong className="text-on-surface">TukiJuris</strong> usa modelos
            propios de la plataforma para analizar legislación peruana y responder
            tus consultas. No necesitas configurar nada.
          </p>
          <p className="text-xs text-on-surface-variant/70">
            Para usar tu propia clave (GPT-4, Claude, etc.) y modelos premium ilimitados,
            necesitás el <strong>plan Empresarial</strong>. Te asignamos un asesor que coordina
            la configuración con tu equipo legal y TI.
          </p>
        </div>
      )}

      {/* Free tier — selected by default, non-actionable card */}
      <div className="mb-4 p-5 rounded-lg border-2 border-primary bg-primary/10">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-full flex items-center justify-center bg-primary text-on-primary shrink-0">
            <Zap className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-primary">Modelo Gratuito incluido</p>
            <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
              Gemini 2.5 Flash + Llama 3.3 70B (Groq). Razonamiento jurídico
              con citas, sin configurar nada.
            </p>
            <ul className="mt-3 space-y-1 text-[11px] text-on-surface-variant/70">
              <li>• 4 consultas normales por día</li>
              <li>• 1 consulta con razonamiento por día</li>
              <li>• Respuestas con citas del derecho peruano</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Enterprise CTA */}
      <div className="mb-6 p-4 rounded-lg border-2 border-outline-variant/20 bg-surface-container">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-full flex items-center justify-center bg-surface-container-low text-on-surface-variant shrink-0">
            <Building2 className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-on-surface">
              ¿Necesitás más capacidad o tu propia API key?
            </p>
            <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
              El plan Empresarial habilita BYOK (GPT-4, Claude, Gemini Pro,
              DeepSeek), uso ilimitado, asientos de equipo y soporte dedicado.
            </p>
            <a
              href="mailto:ventas@tukijuris.com?subject=Plan%20Empresarial%20-%20BYOK"
              className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"
            >
              <Mail className="w-3.5 h-3.5" />
              Contactar a ventas
            </a>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between pt-4 border-t border-outline-variant/20">
        <button
          onClick={onBack}
          className="flex items-center gap-1 h-10 px-4 text-sm text-on-surface-variant rounded-lg border-2 border-outline-variant/30 hover:border-outline-variant/60 hover:text-on-surface transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Atras
        </button>
        <button
          onClick={onNext}
          className="group flex items-center gap-2 h-10 px-6 bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold rounded-lg text-sm transition-all duration-200 hover:shadow-[0_4px_12px_rgba(234,179,8,0.3)] active:scale-[0.98]"
        >
          Continuar
          <ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
        </button>
      </div>
    </div>
  );
}
