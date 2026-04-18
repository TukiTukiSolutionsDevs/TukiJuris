"use client";

import Image from "next/image";
import { Check, ChevronRight, ChevronLeft } from "lucide-react";
import { ROLES, LEGAL_AREAS } from "../_constants";
import type { StepProps } from "../_types";

export function StepPerfil({ state, onChange, onNext, onBack }: StepProps) {
  const toggleArea = (id: string) => {
    const current = state.areas;
    const next = current.includes(id)
      ? current.filter((a) => a !== id)
      : [...current, id];
    onChange({ areas: next });
  };

  return (
    <div className="max-w-lg mx-auto">
      {/* Header — compact */}
      <h2 className="font-['Newsreader'] text-2xl sm:text-3xl text-on-surface mb-1 leading-tight">
        Tu Perfil
      </h2>
      <p className="text-on-surface-variant text-sm mb-6">
        Contanos sobre vos para personalizar tu experiencia
      </p>

      {/* Nombre */}
      <div className="mb-5">
        <label className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
          Nombre completo
        </label>
        <input
          type="text"
          value={state.name}
          onChange={(e) => onChange({ name: e.target.value })}
          placeholder="Juan Perez"
          className="w-full h-11 rounded-lg px-4 text-sm text-on-surface placeholder-on-surface-variant/40 bg-surface-container border-2 border-outline-variant/30 focus:outline-none focus:border-primary transition-colors"
        />
      </div>

      {/* Rol */}
      <div className="mb-5">
        <label className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-2">
          Rol profesional
        </label>
        <div className="flex flex-wrap gap-2">
          {ROLES.map((role) => (
            <button
              key={role.id}
              onClick={() => onChange({ role: role.id })}
              className={`h-9 px-4 rounded-full text-xs font-medium border-2 transition-all duration-150 ${
                state.role === role.id
                  ? "border-primary bg-primary text-on-primary shadow-sm"
                  : "border-outline-variant/30 bg-surface-container text-on-surface hover:border-outline-variant/60"
              }`}
            >
              {state.role === role.id && (
                <Check className="w-3 h-3 inline mr-1 -mt-0.5" />
              )}
              {role.label}
            </button>
          ))}
        </div>
      </div>

      {/* Areas */}
      <div className="mb-6">
        <label className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1">
          Areas de interes
        </label>
        <p className="text-xs text-on-surface-variant/60 mb-2">
          Selecciona las que uses habitualmente
        </p>
        <div className="grid grid-cols-2 gap-2">
          {LEGAL_AREAS.map((area) => {
            const Icon = area.icon;
            const selected = state.areas.includes(area.id);
            return (
              <button
                key={area.id}
                onClick={() => toggleArea(area.id)}
                className={`flex items-center gap-2 h-10 px-3 rounded-lg text-xs font-medium border-2 transition-all duration-150 ${
                  selected
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-outline-variant/30 bg-surface-container text-on-surface-variant hover:border-outline-variant/60 hover:text-on-surface"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 shrink-0 ${selected ? "text-primary" : "text-on-surface-variant/50"}`} />
                <span className="truncate flex-1 text-left">{area.name}</span>
                {selected && <Check className="w-3.5 h-3.5 shrink-0 text-primary" />}
              </button>
            );
          })}
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
