"use client";

import { Check } from "lucide-react";
import { TOTAL_STEPS, STEP_LABELS } from "../_constants";

export function ProgressBar({ current }: { current: number }) {
  return (
    <div className="w-full max-w-2xl mx-auto mb-8 sm:mb-10 px-6">
      <div className="relative flex items-center justify-between">
        {/* Connecting line behind dots */}
        <div className="absolute top-3.5 left-0 right-0 h-px bg-[rgba(79,70,51,0.15)]" />
        <div
          className="absolute top-3.5 left-0 h-px bg-gradient-to-r from-primary to-primary-container transition-all duration-700 ease-out"
          style={{
            width: `${((current - 1) / (TOTAL_STEPS - 1)) * 100}%`,
          }}
        />

        {STEP_LABELS.map((label, i) => {
          const stepNum = i + 1;
          const isCompleted = stepNum < current;
          const isActive = stepNum === current;

          return (
            <div key={i} className="relative z-10 flex flex-col items-center">
              {/* Dot */}
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold transition-all duration-500 ring-4 ring-background ${
                  isCompleted
                    ? "bg-gradient-to-br from-primary to-primary-container text-on-primary shadow-[0_0_12px_rgba(234,179,8,0.3)]"
                    : isActive
                      ? "bg-gradient-to-br from-primary/80 to-primary-container/80 text-on-primary shadow-[0_0_16px_rgba(234,179,8,0.25)] scale-110"
                      : "bg-surface-container-low text-[#6b6974] border border-[rgba(79,70,51,0.15)]"
                }`}
              >
                {isCompleted ? (
                  <Check className="w-3.5 h-3.5" strokeWidth={3} />
                ) : (
                  stepNum
                )}
              </div>

              {/* Label */}
              <span
                className={`mt-2 text-[9px] sm:text-[10px] uppercase tracking-[0.15em] font-medium transition-all duration-300 whitespace-nowrap ${
                  isActive
                    ? "text-primary"
                    : isCompleted
                      ? "text-on-surface-variant"
                      : "text-[#4a4850]"
                }`}
              >
                {label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
