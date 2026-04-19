"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthContext";
import { TOTAL_STEPS } from "./_constants";
import { INITIAL_STATE, type OnboardingState } from "./_types";
import { ProgressBar } from "./_components/ProgressBar";
import { StepBienvenida } from "./_components/StepBienvenida";
import { StepPerfil } from "./_components/StepPerfil";
import { StepOrganizacion } from "./_components/StepOrganizacion";
import { StepApiKey } from "./_components/StepApiKey";
import { StepListo } from "./_components/StepListo";

export default function OnboardingPage() {
  const router = useRouter();
  const { authFetch, completeOnboarding } = useAuth();
  const [step, setStep] = useState(1);
  const [animating, setAnimating] = useState(false);
  const [state, setState] = useState<OnboardingState>(INITIAL_STATE);

  // Load saved state from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("tukijuris_onboarding");
      if (saved) {
        const parsed = JSON.parse(saved) as Partial<OnboardingState>;
        setState((prev) => ({ ...prev, ...parsed }));
      }
    } catch {
      // ignore parse errors
    }
  }, []);

  const updateState = (updates: Partial<OnboardingState>) => {
    setState((prev) => {
      const next = { ...prev, ...updates };
      try {
        localStorage.setItem("tukijuris_onboarding", JSON.stringify(next));
      } catch {
        // ignore storage errors
      }
      return next;
    });
  };

  const goNext = async () => {
    if (step >= TOTAL_STEPS) return;

    // Step 2 -> 3: Save profile to backend
    if (step === 2 && state.name) {
      try {
        await authFetch("/api/auth/me", {
          method: "PUT",
          body: JSON.stringify({ full_name: state.name }),
        });
      } catch {
        // Graceful degradation
      }
    }

    // Step 3 -> 4: Create organization if user chose to have one
    if (step === 3 && state.hasOrg && state.orgName) {
      try {
        await authFetch("/api/organizations/", {
          method: "POST",
          body: JSON.stringify({ name: state.orgName, slug: state.orgSlug }),
        });
      } catch {
        // Graceful degradation
      }
    }

    setAnimating(true);
    setTimeout(() => {
      setStep((s) => s + 1);
      setAnimating(false);
    }, 250);
  };

  const goBack = () => {
    if (step <= 1) return;
    setAnimating(true);
    setTimeout(() => {
      setStep((s) => s - 1);
      setAnimating(false);
    }, 250);
  };

  const finish = async () => {
    try {
      localStorage.setItem("tukijuris_onboarding_done", "true");
      const selectedModel = state.model || "";
      localStorage.setItem(
        "tukijuris_prefs",
        JSON.stringify({
          role: state.role,
          areas: state.areas,
          model: selectedModel,
          name: state.name,
        })
      );
      if (selectedModel) {
        localStorage.setItem("pref_default_model", selectedModel);
      }
    } catch {
      // ignore storage errors
    }
    await completeOnboarding();
    router.push("/chat");
  };

  const skipAll = async () => {
    try {
      localStorage.setItem("tukijuris_onboarding_done", "true");
    } catch {
      // ignore
    }
    await completeOnboarding();
    router.push("/chat");
  };

  return (
    <div className="relative min-h-[calc(100vh-5rem)]">
      {/* Subtle radial gradient background for premium feel */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(234,179,8,0.04)_0%,transparent_60%)] pointer-events-none" />

      <div className="relative flex flex-col items-center justify-center min-h-[calc(100vh-5rem)] px-4 py-8 sm:py-12">
        {/* Progress bar */}
        <ProgressBar current={step} />

        {/* Step content — no card on mobile, card on desktop */}
        <div
          className={`w-full max-w-4xl transition-all duration-250 ${
            animating
              ? "opacity-0 translate-y-3 scale-[0.99]"
              : "opacity-100 translate-y-0 scale-100"
          } sm:bg-surface-container sm:border sm:border-[rgba(79,70,51,0.08)] sm:rounded-lg sm:p-8 lg:p-10 sm:shadow-[0_24px_48px_-12px_rgba(0,0,0,0.4)]`}
        >
          {step === 1 && <StepBienvenida onNext={goNext} />}
          {step === 2 && (
            <StepPerfil
              state={state}
              onChange={updateState}
              onNext={goNext}
              onBack={goBack}
            />
          )}
          {step === 3 && (
            <StepOrganizacion
              state={state}
              onChange={updateState}
              onNext={goNext}
              onBack={goBack}
            />
          )}
          {step === 4 && (
            <StepApiKey
              state={state}
              onChange={updateState}
              onNext={goNext}
              onBack={goBack}
            />
          )}
          {step === 5 && <StepListo state={state} onFinish={finish} />}
        </div>

        {/* Skip link */}
        {step < TOTAL_STEPS && (
          <button
            onClick={skipAll}
            className="mt-6 text-[10px] sm:text-xs uppercase tracking-[0.2em] text-[#4a4850] hover:text-primary/60 transition-colors duration-300"
          >
            Omitir configuracion
          </button>
        )}
      </div>
    </div>
  );
}
