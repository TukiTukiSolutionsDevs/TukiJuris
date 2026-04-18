"use client";

import { Check, ChevronRight, ChevronLeft, Building, User } from "lucide-react";
import { slugify } from "../_constants";
import type { StepProps } from "../_types";

export function StepOrganizacion({ state, onChange, onNext, onBack }: StepProps) {
  return (
    <div className="max-w-lg mx-auto">
      <h2 className="font-['Newsreader'] text-2xl sm:text-3xl text-on-surface mb-1 leading-tight">
        Tu Organizacion
      </h2>
      <p className="text-on-surface-variant text-sm mb-6">
        Crea o unite a una organizacion para compartir configuraciones
      </p>

      {/* Tipo de uso */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
        <button
          onClick={() => onChange({ hasOrg: false })}
          className={`flex items-center gap-3 p-4 rounded-lg border-2 text-left transition-all duration-150 ${
            !state.hasOrg
              ? "border-primary bg-primary/10"
              : "border-outline-variant/30 bg-surface-container hover:border-outline-variant/60"
          }`}
        >
          <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
            !state.hasOrg ? "bg-primary text-on-primary" : "bg-surface-container-low text-on-surface-variant"
          }`}>
            <User className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className={`text-sm font-semibold ${!state.hasOrg ? "text-primary" : "text-on-surface"}`}>
              Trabajo solo
            </p>
            <p className="text-[11px] text-on-surface-variant/60 mt-0.5">Personal o independiente</p>
          </div>
          {!state.hasOrg && <Check className="w-4 h-4 ml-auto text-primary shrink-0" />}
        </button>

        <button
          onClick={() => onChange({ hasOrg: true })}
          className={`flex items-center gap-3 p-4 rounded-lg border-2 text-left transition-all duration-150 ${
            state.hasOrg
              ? "border-primary bg-primary/10"
              : "border-outline-variant/30 bg-surface-container hover:border-outline-variant/60"
          }`}
        >
          <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
            state.hasOrg ? "bg-primary text-on-primary" : "bg-surface-container-low text-on-surface-variant"
          }`}>
            <Building className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <p className={`text-sm font-semibold ${state.hasOrg ? "text-primary" : "text-on-surface"}`}>
              Tengo un equipo
            </p>
            <p className="text-[11px] text-on-surface-variant/60 mt-0.5">Estudio o equipo legal</p>
          </div>
          {state.hasOrg && <Check className="w-4 h-4 ml-auto text-primary shrink-0" />}
        </button>
      </div>

      {/* Org form */}
      {state.hasOrg && (
        <div className="space-y-4 p-4 rounded-lg bg-surface-container-low border-2 border-outline-variant/20 mb-5">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
              Nombre de la organizacion
            </label>
            <input
              type="text"
              value={state.orgName}
              onChange={(e) => {
                const name = e.target.value;
                onChange({ orgName: name, orgSlug: slugify(name) });
              }}
              placeholder="Estudio Juridico Perez & Asociados"
              className="w-full h-11 rounded-lg px-4 text-sm text-on-surface placeholder-on-surface-variant/40 bg-surface-container border-2 border-outline-variant/30 focus:outline-none focus:border-primary transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
              Identificador (slug)
            </label>
            <input
              type="text"
              value={state.orgSlug}
              readOnly
              className="w-full h-11 rounded-lg px-4 text-sm text-on-surface-variant/50 bg-surface-container-low border-2 border-outline-variant/15 cursor-default"
            />
            {state.orgSlug && (
              <p className="text-[11px] text-on-surface-variant/50 mt-1">
                URL: <span className="font-medium text-on-surface-variant">{state.orgSlug}.tukijuris.net.pe</span>
              </p>
            )}
          </div>
        </div>
      )}

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
          {state.hasOrg && state.orgName ? "Crear Organizacion" : "Continuar"}
          <ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
        </button>
      </div>
    </div>
  );
}
