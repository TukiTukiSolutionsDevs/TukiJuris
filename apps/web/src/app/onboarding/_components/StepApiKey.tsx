"use client";

import { useState } from "react";
import {
  Check, ChevronRight, ChevronLeft, Key, Eye, EyeOff, Loader2,
  AlertTriangle, Zap, Sparkles, HelpCircle, ExternalLink,
} from "lucide-react";
import { AI_PROVIDERS } from "../_constants";
import type { StepProps } from "../_types";
import { useAuth } from "@/lib/auth/AuthContext";

type Mode = "undecided" | "free" | "byok";

export function StepApiKey({ state, onChange, onNext, onBack }: StepProps) {
  const { authFetch } = useAuth();
  const [mode, setMode] = useState<Mode>(
    state.apiKeySaved ? "byok" : state.apiProvider ? "byok" : "undecided"
  );
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [showHelp, setShowHelp] = useState(false);
  const selectedProvider = AI_PROVIDERS.find((p) => p.id === state.apiProvider);

  const handleSaveKey = async () => {
    if (!state.apiKey.trim() || !state.apiProvider) return;
    setSaving(true);
    setSaveError("");
    try {
      const res = await authFetch("/api/keys/llm-keys", {
        method: "POST",
        body: JSON.stringify({ provider: state.apiProvider, api_key: state.apiKey.trim(), label: state.apiKeyLabel.trim() || undefined }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "Error al guardar la clave");
      }
      onChange({ apiKeySaved: true });
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const toggleProvider = (id: string) => {
    if (state.apiProvider === id) {
      onChange({ apiProvider: "", apiKeySaved: false, apiKey: "", apiKeyLabel: "" });
    } else {
      onChange({ apiProvider: id, apiKeySaved: false, apiKey: "", apiKeyLabel: "" });
    }
  };

  return (
    <div className="max-w-lg mx-auto">
      <h2 className="font-['Newsreader'] text-2xl sm:text-3xl text-on-surface mb-1 leading-tight">
        Motor de Inteligencia Artificial
      </h2>
      <p className="text-on-surface-variant text-sm mb-6">
        Elegi como queres que funcione el asistente
      </p>

      {/* Help toggle */}
      <button
        onClick={() => setShowHelp(!showHelp)}
        className="flex items-center gap-1.5 text-xs text-primary hover:underline mb-4"
      >
        <HelpCircle className="w-3.5 h-3.5" />
        {showHelp ? "Ocultar explicacion" : "Que es esto? Como funciona?"}
      </button>

      {showHelp && (
        <div className="mb-6 p-4 rounded-lg bg-primary/5 border-2 border-primary/15 text-sm text-on-surface-variant space-y-2">
          <p>
            <strong className="text-on-surface">TukiJuris</strong> usa inteligencia artificial para analizar leyes y responder tus consultas juridicas.
          </p>
          <p>
            Tenes dos opciones:
          </p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li><strong>Modo gratuito:</strong> Usas Gemini Flash de Google, sin costo y sin configurar nada. Ideal para empezar.</li>
            <li><strong>Tu propia clave:</strong> Si ya tenes una cuenta en OpenAI, Anthropic, Google AI o DeepSeek, podes traer tu API key para usar modelos premium como GPT-4 o Claude.</li>
          </ul>
          <p className="text-xs text-on-surface-variant/60">
            Siempre podes cambiar esto despues en Configuracion.
          </p>
        </div>
      )}

      {/* Main choice — Free vs BYOK */}
      {!state.apiKeySaved && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          {/* Free option */}
          <button
            onClick={() => {
              setMode("free");
              onChange({ apiProvider: "", apiKey: "", apiKeyLabel: "", apiKeySaved: false });
            }}
            className={`flex flex-col items-center gap-3 p-5 rounded-lg border-2 text-center transition-all duration-150 ${
              mode === "free"
                ? "border-primary bg-primary/10"
                : "border-outline-variant/30 bg-surface-container hover:border-outline-variant/60"
            }`}
          >
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              mode === "free" ? "bg-primary text-on-primary" : "bg-surface-container-low text-on-surface-variant"
            }`}>
              <Zap className="w-6 h-6" />
            </div>
            <div>
              <p className={`text-sm font-bold ${mode === "free" ? "text-primary" : "text-on-surface"}`}>
                Modo Gratuito
              </p>
              <p className="text-[11px] text-on-surface-variant/60 mt-1 leading-snug">
                Gemini Flash incluido.<br />Sin configurar nada.
              </p>
            </div>
            {mode === "free" && <Check className="w-4 h-4 text-primary" />}
          </button>

          {/* BYOK option */}
          <button
            onClick={() => setMode("byok")}
            className={`flex flex-col items-center gap-3 p-5 rounded-lg border-2 text-center transition-all duration-150 ${
              mode === "byok"
                ? "border-primary bg-primary/10"
                : "border-outline-variant/30 bg-surface-container hover:border-outline-variant/60"
            }`}
          >
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              mode === "byok" ? "bg-primary text-on-primary" : "bg-surface-container-low text-on-surface-variant"
            }`}>
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <p className={`text-sm font-bold ${mode === "byok" ? "text-primary" : "text-on-surface"}`}>
                Tengo mi Clave
              </p>
              <p className="text-[11px] text-on-surface-variant/60 mt-1 leading-snug">
                Usa GPT-4, Claude u otros<br />modelos premium.
              </p>
            </div>
            {mode === "byok" && <Check className="w-4 h-4 text-primary" />}
          </button>
        </div>
      )}

      {/* Free mode selected — confirmation */}
      {mode === "free" && !state.apiKeySaved && (
        <div className="flex items-center gap-3 p-4 bg-primary/8 border-2 border-primary/20 rounded-lg mb-5">
          <Zap className="w-5 h-5 text-primary shrink-0" />
          <div>
            <p className="text-sm font-semibold text-on-surface">Listo para usar</p>
            <p className="text-xs text-on-surface-variant mt-0.5">
              Vas a usar Gemini Flash (gratis). Podes agregar tu clave despues en Configuracion.
            </p>
          </div>
        </div>
      )}

      {/* BYOK mode — Provider selector */}
      {mode === "byok" && !state.apiKeySaved && (
        <>
          <div className="mb-4">
            <label className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-2">
              Elegi tu proveedor
            </label>
            <div className="grid grid-cols-2 gap-2">
              {AI_PROVIDERS.map((provider) => (
                <button
                  key={provider.id}
                  onClick={() => toggleProvider(provider.id)}
                  className={`p-3 rounded-lg border-2 text-left transition-all duration-150 ${
                    state.apiProvider === provider.id
                      ? "border-primary bg-primary/10"
                      : "border-outline-variant/30 bg-surface-container hover:border-outline-variant/60"
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    {state.apiProvider === provider.id && <Check className="w-3 h-3 text-primary shrink-0" />}
                    <span className={`text-sm font-semibold ${state.apiProvider === provider.id ? "text-primary" : "text-on-surface"}`}>
                      {provider.name}
                    </span>
                  </div>
                  <p className="text-[10px] text-on-surface-variant/50 mt-0.5">{provider.models.join(", ")}</p>
                </button>
              ))}
            </div>
          </div>

          {/* API Key form — only when provider selected */}
          {state.apiProvider && selectedProvider && (
            <div className="space-y-3 mb-5 p-4 rounded-lg bg-surface-container-low border-2 border-outline-variant/20">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
                  Tu clave de {selectedProvider.name}
                </label>
                <div className="relative">
                  <input
                    type={showKey ? "text" : "password"}
                    value={state.apiKey}
                    onChange={(e) => onChange({ apiKey: e.target.value })}
                    placeholder={selectedProvider.placeholder}
                    className="w-full h-11 rounded-lg px-4 pr-11 text-sm font-mono text-on-surface placeholder-on-surface-variant/40 bg-surface-container border-2 border-outline-variant/30 focus:outline-none focus:border-primary transition-colors"
                  />
                  <button type="button" onClick={() => setShowKey(!showKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant/40 hover:text-on-surface-variant transition-colors">
                    {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-1.5">
                  Etiqueta <span className="font-normal normal-case tracking-normal text-on-surface-variant/40">(opcional)</span>
                </label>
                <input
                  type="text"
                  value={state.apiKeyLabel}
                  onChange={(e) => onChange({ apiKeyLabel: e.target.value })}
                  placeholder="Ej: Mi clave principal"
                  className="w-full h-11 rounded-lg px-4 text-sm text-on-surface placeholder-on-surface-variant/40 bg-surface-container border-2 border-outline-variant/30 focus:outline-none focus:border-primary transition-colors"
                />
              </div>

              {saveError && (
                <div className="flex items-center gap-2 text-xs text-error bg-error/10 border border-error/20 rounded-lg px-3 py-2.5">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0" />{saveError}
                </div>
              )}

              <button
                onClick={handleSaveKey}
                disabled={saving || !state.apiKey.trim()}
                className="w-full flex items-center justify-center gap-2 h-11 bg-gradient-to-br from-primary to-primary-container disabled:opacity-40 text-on-primary font-bold rounded-lg text-sm transition-all duration-200 hover:shadow-[0_4px_12px_rgba(234,179,8,0.3)] disabled:cursor-not-allowed disabled:shadow-none"
              >
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
                Guardar Clave
              </button>

              <div className="flex items-center justify-center gap-1.5 text-xs text-on-surface-variant/50">
                <ExternalLink className="w-3 h-3" />
                <a href={selectedProvider.dashboardUrl} target="_blank" rel="noopener noreferrer"
                  className="text-primary hover:underline">
                  Obtene tu clave de {selectedProvider.name}
                </a>
              </div>
            </div>
          )}
        </>
      )}

      {/* Key saved confirmation */}
      {state.apiKeySaved && (
        <>
          <div className="flex items-center gap-3 p-4 bg-primary/10 border-2 border-primary/30 rounded-lg mb-5">
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
              <Check className="w-4 h-4 text-on-primary" />
            </div>
            <div>
              <p className="text-sm font-semibold text-primary">Clave guardada correctamente</p>
              <p className="text-xs text-on-surface-variant mt-0.5">{selectedProvider?.name} — {selectedProvider?.models.join(", ")}</p>
            </div>
          </div>

          {/* Model selector */}
          {selectedProvider && (
            <div className="mb-5">
              <label className="block text-xs font-semibold uppercase tracking-wider text-on-surface-variant mb-2">
                Modelo predeterminado
              </label>
              <div className="space-y-2">
                {selectedProvider.models.map((modelId) => (
                  <button
                    key={modelId}
                    onClick={() => onChange({ model: modelId })}
                    className={`w-full flex items-center gap-3 h-11 px-4 rounded-lg border-2 text-left transition-all duration-150 ${
                      state.model === modelId
                        ? "border-primary bg-primary/10"
                        : "border-outline-variant/30 bg-surface-container hover:border-outline-variant/60"
                    }`}
                  >
                    <span className={`text-sm font-mono ${state.model === modelId ? "text-primary font-semibold" : "text-on-surface-variant"}`}>
                      {modelId}
                    </span>
                    {state.model === modelId && (
                      <div className="ml-auto w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                        <Check className="w-3 h-3 text-on-primary" />
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
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
          disabled={mode === "undecided"}
          className="group flex items-center gap-2 h-10 px-6 bg-gradient-to-br from-primary to-primary-container disabled:opacity-40 text-on-primary font-bold rounded-lg text-sm transition-all duration-200 hover:shadow-[0_4px_12px_rgba(234,179,8,0.3)] active:scale-[0.98] disabled:cursor-not-allowed disabled:shadow-none"
        >
          Continuar
          <ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
        </button>
      </div>
    </div>
  );
}
