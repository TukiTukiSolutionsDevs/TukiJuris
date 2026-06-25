"use client";

import type { LucideIcon } from "lucide-react";
import { Hammer } from "lucide-react";

interface ComingSoonTabProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
}

export function ComingSoonTab({ title, description, icon: Icon = Hammer }: ComingSoonTabProps) {
  return (
    <div className="w-full px-4 py-6 sm:py-8 lg:px-6 xl:px-8">
      <div className="bg-surface-container-low rounded-2xl p-8 sm:p-12 flex flex-col items-center text-center" style={{ border: "1px solid rgba(79,70,51,0.15)" }}>
        <div className="w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-5">
          <Icon className="w-8 h-8 text-primary" />
        </div>
        <h2 className="font-['Newsreader'] text-2xl sm:text-3xl font-bold text-primary mb-2">
          {title}
        </h2>
        <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.2em] text-primary/70 bg-primary/5 border border-primary/15 rounded-full px-3 py-1 mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          En construcción
        </span>
        {description && (
          <p className="text-sm text-on-surface/60 max-w-xl">{description}</p>
        )}
        <p className="mt-6 text-xs text-on-surface/40">
          Esta sección está mapeada y tiene endpoints en el backend. La UI se está implementando como parte del plan de producción.
        </p>
      </div>
    </div>
  );
}
