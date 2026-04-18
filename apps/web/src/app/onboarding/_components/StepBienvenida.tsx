"use client";

import { ChevronRight, Sparkles } from "lucide-react";

export function StepBienvenida({ onNext }: { onNext: () => void }) {
  return (
    <div className="text-center max-w-lg mx-auto py-4 sm:py-8">
      {/* Logo */}
      <div className="mb-6">
        <img
          src="/brand/logo-full.png"
          alt="TukiJuris"
          className="h-16 sm:h-20 mx-auto"
          onError={(e) => {
            const target = e.currentTarget;
            target.style.display = "none";
            const fallback = document.createElement("div");
            fallback.className =
              "w-16 h-16 rounded-lg flex items-center justify-center mx-auto bg-primary/10 border-2 border-primary/20";
            fallback.innerHTML =
              '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="text-primary"><path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/></svg>';
            target.parentNode?.insertBefore(fallback, target);
          }}
        />
      </div>

      {/* Badge */}
      <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary/10 border-2 border-primary/20 mb-6">
        <Sparkles className="w-3 h-3 text-primary" />
        <span className="text-[11px] sm:text-xs uppercase tracking-wider font-semibold text-primary">
          Asistente Juridico IA
        </span>
      </div>

      <h1 className="font-['Newsreader'] text-3xl sm:text-4xl text-on-surface mb-3 leading-[1.15]">
        Bienvenido a{" "}
        <span className="text-primary font-semibold">TukiJuris</span>
      </h1>

      <p className="text-on-surface-variant text-sm sm:text-base mb-2 leading-relaxed max-w-md mx-auto">
        Tu asistente inteligente para el derecho peruano.
        Analiza, busca y consulta legislacion en segundos.
      </p>

      <p className="text-on-surface-variant/50 text-xs sm:text-sm mb-10">
        Configuremos tu cuenta en solo{" "}
        <span className="text-on-surface-variant font-medium">4 pasos</span>
      </p>

      {/* CTA */}
      <button
        onClick={onNext}
        className="group inline-flex items-center gap-3 h-12 sm:h-14 px-8 sm:px-10 bg-gradient-to-br from-primary to-primary-container text-on-primary font-bold rounded-lg uppercase tracking-wider text-sm transition-all duration-200 hover:shadow-[0_8px_24px_rgba(234,179,8,0.3)] active:scale-[0.97]"
      >
        Comenzar
        <ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
      </button>

      {/* Feature hints */}
      <div className="mt-12 flex justify-center gap-8 sm:gap-12">
        {[
          { label: "Legislacion", sub: "actualizada" },
          { label: "Analisis", sub: "con IA" },
          { label: "Busqueda", sub: "semantica" },
        ].map((item) => (
          <div key={item.label} className="text-center">
            <p className="text-xs font-semibold text-on-surface-variant">{item.label}</p>
            <p className="text-[10px] text-on-surface-variant/40 mt-0.5">{item.sub}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
