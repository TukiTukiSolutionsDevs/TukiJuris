"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Scale,
  BookOpen,
  Shield,
  Briefcase,
  Landmark,
  Gavel,
  Building2,
  ScrollText,
  FileCheck,
  Globe,
  Lock,
  BadgeCheck,
  ChevronRight,
  ChevronLeft,
  Check,
  Building,
  Key,
  Eye,
  EyeOff,
  Loader2,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import Link from "next/link";
import { getToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ————————————————————————————————————————————————
// CONSTANTS
// ————————————————————————————————————————————————

const TOTAL_STEPS = 5;

const STEP_LABELS = [
  "Bienvenida",
  "Perfil",
  "Organización",
  "API Key",
  "Listo",
];

const ROLES = [
  { id: "abogado", label: "Abogado" },
  { id: "paralegal", label: "Paralegal" },
  { id: "estudiante", label: "Estudiante de Derecho" },
  { id: "corporativo", label: "Equipo Legal Corporativo" },
  { id: "otro", label: "Otro" },
];

const LEGAL_AREAS = [
  { id: "civil", name: "Civil", icon: BookOpen },
  { id: "penal", name: "Penal", icon: Shield },
  { id: "laboral", name: "Laboral", icon: Briefcase },
  { id: "tributario", name: "Tributario", icon: Landmark },
  { id: "constitucional", name: "Constitucional", icon: Gavel },
  { id: "administrativo", name: "Administrativo", icon: Building2 },
  { id: "corporativo", name: "Corporativo", icon: ScrollText },
  { id: "registral", name: "Registral", icon: FileCheck },
  { id: "comercio_exterior", name: "Comercio Exterior", icon: Globe },
  { id: "compliance", name: "Compliance", icon: Lock },
  { id: "competencia", name: "Competencia / PI", icon: BadgeCheck },
];

interface AIProvider {
  id: string;
  name: string;
  models: string[];
  placeholder: string;
  dashboardUrl: string;
}

const AI_PROVIDERS: AIProvider[] = [
  {
    id: "openai",
    name: "OpenAI",
    models: ["gpt-4o", "gpt-4o-mini"],
    placeholder: "sk-...",
    dashboardUrl: "https://platform.openai.com/api-keys",
  },
  {
    id: "anthropic",
    name: "Anthropic",
    models: ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"],
    placeholder: "sk-ant-...",
    dashboardUrl: "https://console.anthropic.com/settings/keys",
  },
  {
    id: "google",
    name: "Google AI",
    models: ["gemini-2.0-flash", "gemini-2.5-pro"],
    placeholder: "AIza...",
    dashboardUrl: "https://aistudio.google.com/app/apikey",
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    models: ["deepseek-chat", "deepseek-reasoner"],
    placeholder: "sk-...",
    dashboardUrl: "https://platform.deepseek.com/api_keys",
  },
];

const SUGGESTED_QUERIES_BY_AREA: Record<string, string> = {
  civil: "Que dice el Art. 1969 del Codigo Civil sobre responsabilidad civil?",
  penal: "Cuales son los elementos del delito de estafa en Peru?",
  laboral: "Como se calcula la CTS para un trabajador a tiempo completo?",
  tributario: "Cuales son los regimenes tributarios disponibles para una MYPE?",
  constitucional: "Cuando procede interponer un recurso de habeas corpus?",
  administrativo: "Que es el silencio administrativo positivo y negativo?",
  corporativo: "Cuales son los requisitos para constituir una SAC en Peru?",
  registral: "Como se inscribe una hipoteca en Registros Publicos?",
  comercio_exterior: "En que consiste el regimen de drawback en aduanas?",
  compliance: "Que empresas estan obligadas a tener un sistema SPLAFT?",
  competencia: "Como se registra una marca ante INDECOPI?",
};

// ————————————————————————————————————————————————
// INTERFACES
// ————————————————————————————————————————————————

interface OnboardingState {
  name: string;
  role: string;
  areas: string[];
  hasOrg: boolean;
  orgName: string;
  orgSlug: string;
  model: string;
  apiProvider: string;
  apiKey: string;
  apiKeyLabel: string;
  apiKeySaved: boolean;
}

// ————————————————————————————————————————————————
// HELPERS
// ————————————————————————————————————————————————

function slugify(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

// ————————————————————————————————————————————————
// PROGRESS BAR
// ————————————————————————————————————————————————

function ProgressBar({ current }: { current: number }) {
  return (
    <div className="w-full max-w-2xl mb-8">
      <div className="flex items-center justify-between">
        {STEP_LABELS.map((label, i) => (
          <div key={i} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all duration-300 ${
                  i + 1 < current
                    ? "bg-[#EAB308] text-[#0A0A0F]"
                    : i + 1 === current
                    ? "bg-[#EAB308]/20 text-[#EAB308] border-2 border-[#EAB308]"
                    : "bg-[#1A1A22] text-[#6B7280] border border-[#2A2A35]"
                }`}
              >
                {i + 1 < current ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : (
                  i + 1
                )}
              </div>
              <span
                className={`text-[10px] font-medium hidden sm:block ${
                  i + 1 === current
                    ? "text-[#EAB308]"
                    : i + 1 < current
                    ? "text-[#9CA3AF]"
                    : "text-[#6B7280]"
                }`}
              >
                {label}
              </span>
            </div>
            {i < STEP_LABELS.length - 1 && (
              <div
                className={`w-8 sm:w-16 h-0.5 mx-1 sm:mx-2 transition-all duration-300 ${
                  i + 1 < current ? "bg-[#EAB308]" : "bg-[#2A2A35]"
                }`}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ————————————————————————————————————————————————
// STEP COMPONENTS
// ————————————————————————————————————————————————

function StepBienvenido({ onNext }: { onNext: () => void }) {
  return (
    <div className="text-center">
      {/* Logo */}
      <img
        src="/brand/logo-full.png"
        alt="TukiJuris"
        className="w-48 mx-auto mb-8"
        onError={(e) => {
          const target = e.currentTarget;
          target.style.display = "none";
          const fallback = document.createElement("div");
          fallback.className =
            "w-20 h-20 bg-gradient-to-br from-[#EAB308]/20 to-[#EAB308]/5 rounded-2xl flex items-center justify-center mx-auto mb-8 border border-[#EAB308]/20";
          fallback.innerHTML =
            '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#EAB308" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/></svg>';
          target.parentNode?.insertBefore(fallback, target);
        }}
      />

      <h1 className="text-3xl font-bold text-[#F5F5F5] mb-3">
        ¡Bienvenido a TukiJuris!
      </h1>
      <p className="text-[#9CA3AF] text-lg mb-4 max-w-md mx-auto leading-relaxed">
        Tu asistente jurídico inteligente para el derecho peruano
      </p>
      <p className="text-[#6B7280] text-sm mb-10">
        Configuremos tu cuenta en 4 simples pasos
      </p>

      <button
        onClick={onNext}
        className="inline-flex items-center gap-2 h-12 px-8 bg-[#EAB308] hover:bg-[#D4A017] text-[#0A0A0F] font-semibold rounded-xl transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
      >
        Comenzar
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}

function StepPerfil({
  state,
  onChange,
  onNext,
  onBack,
}: {
  state: OnboardingState;
  onChange: (updates: Partial<OnboardingState>) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  const toggleArea = (id: string) => {
    const current = state.areas;
    const next = current.includes(id)
      ? current.filter((a) => a !== id)
      : [...current, id];
    onChange({ areas: next });
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-[#F5F5F5] mb-2">Tu Perfil</h2>
      <p className="text-[#9CA3AF] mb-8">
        Cuéntanos sobre ti para personalizar tu experiencia
      </p>

      <div className="space-y-6">
        {/* Nombre completo */}
        <div>
          <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
            Nombre completo
          </label>
          <input
            type="text"
            value={state.name}
            onChange={(e) => onChange({ name: e.target.value })}
            placeholder="Juan Pérez"
            className="w-full h-12 bg-[#111116] border border-[#2A2A35] rounded-xl px-4 text-[#F5F5F5] placeholder-[#4B5563] focus:outline-none focus:border-[#EAB308] transition-colors text-sm"
          />
        </div>

        {/* Rol profesional */}
        <div>
          <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
            Rol profesional
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {ROLES.map((role) => (
              <button
                key={role.id}
                onClick={() => onChange({ role: role.id })}
                className={`px-3 py-2.5 rounded-xl text-sm border transition-all duration-200 text-left ${
                  state.role === role.id
                    ? "border-[#EAB308] bg-[#EAB308]/10 text-[#EAB308]"
                    : "border-[#2A2A35] text-[#9CA3AF] hover:border-[#3A3A45] bg-[#1A1A22]"
                }`}
              >
                {state.role === role.id && (
                  <Check className="w-3 h-3 inline mr-1.5 text-[#EAB308]" />
                )}
                {role.label}
              </button>
            ))}
          </div>
        </div>

        {/* Áreas de interés */}
        <div>
          <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
            Áreas de interés{" "}
            <span className="text-[#6B7280] font-normal">
              (seleccioná las que uses)
            </span>
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {LEGAL_AREAS.map((area) => {
              const Icon = area.icon;
              const selected = state.areas.includes(area.id);
              return (
                <button
                  key={area.id}
                  onClick={() => toggleArea(area.id)}
                  className={`flex items-center gap-2 px-3 py-3 rounded-lg text-xs border transition-all duration-200 cursor-pointer ${
                    selected
                      ? "border-[#EAB308] bg-[#EAB308]/10 text-[#EAB308]"
                      : "border-[#2A2A35] bg-[#1A1A22] text-[#9CA3AF] hover:border-[#3A3A45]"
                  }`}
                >
                  <Icon
                    className={`w-3.5 h-3.5 shrink-0 ${
                      selected ? "text-[#EAB308]" : "text-[#6B7280]"
                    }`}
                  />
                  <span className="truncate">{area.name}</span>
                  {selected && (
                    <Check className="w-3 h-3 ml-auto shrink-0 text-[#EAB308]" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between mt-8">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-[#6B7280] hover:text-[#9CA3AF] transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Atrás
        </button>
        <button
          onClick={onNext}
          className="flex items-center gap-2 h-12 px-6 bg-[#EAB308] hover:bg-[#D4A017] text-[#0A0A0F] font-semibold rounded-xl transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
        >
          Continuar
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function StepOrganizacion({
  state,
  onChange,
  onNext,
  onBack,
}: {
  state: OnboardingState;
  onChange: (updates: Partial<OnboardingState>) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-[#F5F5F5] mb-2">
        Tu Organización
      </h2>
      <p className="text-[#9CA3AF] mb-8">
        Crea o únete a una organización para compartir configuraciones con tu equipo
      </p>

      <div className="space-y-4">
        {/* Tipo de uso */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button
            onClick={() => onChange({ hasOrg: false })}
            className={`p-4 rounded-xl border text-left transition-all duration-200 ${
              !state.hasOrg
                ? "border-[#EAB308] bg-[#EAB308]/10"
                : "border-[#2A2A35] bg-[#1A1A22] hover:border-[#3A3A45]"
            }`}
          >
            <p
              className={`text-sm font-medium mb-1 ${
                !state.hasOrg ? "text-[#EAB308]" : "text-[#F5F5F5]"
              }`}
            >
              {!state.hasOrg && <Check className="w-3 h-3 inline mr-1.5" />}
              Trabajo solo
            </p>
            <p className="text-xs text-[#6B7280]">Uso personal o independiente</p>
          </button>

          <button
            onClick={() => onChange({ hasOrg: true })}
            className={`p-4 rounded-xl border text-left transition-all duration-200 ${
              state.hasOrg
                ? "border-[#EAB308] bg-[#EAB308]/10"
                : "border-[#2A2A35] bg-[#1A1A22] hover:border-[#3A3A45]"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <Building
                className={`w-4 h-4 ${
                  state.hasOrg ? "text-[#EAB308]" : "text-[#9CA3AF]"
                }`}
              />
              <p
                className={`text-sm font-medium ${
                  state.hasOrg ? "text-[#EAB308]" : "text-[#F5F5F5]"
                }`}
              >
                Tengo un equipo
              </p>
            </div>
            <p className="text-xs text-[#6B7280]">Estudio jurídico o equipo legal</p>
          </button>
        </div>

        {/* Formulario de organización */}
        {state.hasOrg && (
          <div className="space-y-4 p-5 rounded-xl bg-[#0A0A0F] border border-[#1E1E2A]">
            <div>
              <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                Nombre de la organización
              </label>
              <input
                type="text"
                value={state.orgName}
                onChange={(e) => {
                  const name = e.target.value;
                  onChange({ orgName: name, orgSlug: slugify(name) });
                }}
                placeholder="Estudio Jurídico Pérez & Asociados"
                className="w-full h-12 bg-[#111116] border border-[#2A2A35] rounded-xl px-4 text-[#F5F5F5] placeholder-[#4B5563] focus:outline-none focus:border-[#EAB308] transition-colors text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
                Identificador (slug)
              </label>
              <input
                type="text"
                value={state.orgSlug}
                readOnly
                placeholder="estudio-juridico-perez-asociados"
                className="w-full h-12 bg-[#0A0A0F] border border-[#1E1E2A] rounded-xl px-4 text-[#6B7280] text-sm cursor-default"
              />
              {state.orgSlug && (
                <p className="text-xs text-[#6B7280] mt-1.5">
                  URL:{" "}
                  <span className="text-[#9CA3AF]">
                    tukijuris.net.pe/org/{state.orgSlug}
                  </span>
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between mt-8">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-[#6B7280] hover:text-[#9CA3AF] transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Atrás
        </button>
        <button
          onClick={onNext}
          className="flex items-center gap-2 h-12 px-6 bg-[#EAB308] hover:bg-[#D4A017] text-[#0A0A0F] font-semibold rounded-xl transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
        >
          {state.hasOrg && state.orgName ? "Crear Organización" : "Continuar"}
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function StepConectaIA({
  state,
  onChange,
  onNext,
  onBack,
}: {
  state: OnboardingState;
  onChange: (updates: Partial<OnboardingState>) => void;
  onNext: () => void;
  onBack: () => void;
}) {
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  const selectedProvider = AI_PROVIDERS.find((p) => p.id === state.apiProvider);

  const handleSaveKey = async () => {
    if (!state.apiKey.trim() || !state.apiProvider) return;
    setSaving(true);
    setSaveError("");
    try {
      const token = getToken();
      if (!token) throw new Error("No autenticado");
      const res = await fetch(`${API_URL}/api/keys/llm-keys`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          provider: state.apiProvider,
          api_key: state.apiKey.trim(),
          label: state.apiKeyLabel.trim() || undefined,
        }),
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

  return (
    <div>
      <h2 className="text-2xl font-bold text-[#F5F5F5] mb-2">
        Configura tu Clave de IA
      </h2>
      <p className="text-[#9CA3AF] mb-8">
        TukiJuris usa el modelo BYOK: trae tu propia API key de cualquier proveedor
      </p>

      {/* Provider selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-[#9CA3AF] mb-3">
          Proveedor
        </label>
        <div className="grid grid-cols-2 gap-2">
          {AI_PROVIDERS.map((provider) => (
            <button
              key={provider.id}
              onClick={() =>
                onChange({
                  apiProvider: provider.id,
                  apiKeySaved: false,
                  apiKey: "",
                  apiKeyLabel: "",
                })
              }
              className={`p-3 rounded-xl border text-left transition-all duration-200 ${
                state.apiProvider === provider.id
                  ? "border-[#EAB308] bg-[#EAB308]/10"
                  : "border-[#2A2A35] bg-[#1A1A22] hover:border-[#3A3A45]"
              }`}
            >
              <div
                className={`text-sm font-medium ${
                  state.apiProvider === provider.id
                    ? "text-[#EAB308]"
                    : "text-[#F5F5F5]"
                }`}
              >
                {state.apiProvider === provider.id && (
                  <Check className="w-3 h-3 inline mr-1.5" />
                )}
                {provider.name}
              </div>
              <p className="text-[10px] text-[#6B7280] mt-0.5">
                {provider.models.join(", ")}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* API Key input */}
      {state.apiProvider && !state.apiKeySaved && (
        <div className="space-y-4 mb-5">
          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
              API Key{" "}
              <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <input
                type={showKey ? "text" : "password"}
                value={state.apiKey}
                onChange={(e) => onChange({ apiKey: e.target.value })}
                placeholder={selectedProvider?.placeholder}
                className="w-full h-12 bg-[#111116] border border-[#2A2A35] rounded-xl px-4 pr-11 text-[#F5F5F5] font-mono placeholder-[#4B5563] focus:outline-none focus:border-[#EAB308] transition-colors text-sm"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B7280] hover:text-[#9CA3AF] transition-colors"
              >
                {showKey ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
              Etiqueta{" "}
              <span className="text-[#6B7280] font-normal">(opcional)</span>
            </label>
            <input
              type="text"
              value={state.apiKeyLabel}
              onChange={(e) => onChange({ apiKeyLabel: e.target.value })}
              placeholder="Mi clave principal"
              className="w-full h-12 bg-[#111116] border border-[#2A2A35] rounded-xl px-4 text-[#F5F5F5] placeholder-[#4B5563] focus:outline-none focus:border-[#EAB308] transition-colors text-sm"
            />
          </div>

          {saveError && (
            <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              {saveError}
            </div>
          )}

          <button
            onClick={handleSaveKey}
            disabled={saving || !state.apiKey.trim()}
            className="w-full flex items-center justify-center gap-2 h-12 bg-[#EAB308] hover:bg-[#D4A017] disabled:bg-[#2A2A35] disabled:text-[#6B7280] text-[#0A0A0F] font-semibold rounded-xl transition-all duration-200 disabled:cursor-not-allowed"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Key className="w-4 h-4" />
            )}
            Guardar y Continuar
          </button>
        </div>
      )}

      {/* Clave guardada */}
      {state.apiKeySaved && (
        <div className="flex items-center gap-3 p-4 bg-[#34D399]/10 border border-[#34D399]/20 rounded-xl mb-5">
          <CheckCircle2 className="w-5 h-5 text-[#34D399] shrink-0" />
          <div>
            <p className="text-sm font-medium text-[#34D399]">
              Clave guardada correctamente
            </p>
            <p className="text-xs text-[#6B7280] mt-0.5">
              {selectedProvider?.name} — modelos: {selectedProvider?.models.join(", ")}
            </p>
          </div>
        </div>
      )}

      {/* Model selector after key saved */}
      {state.apiKeySaved && selectedProvider && (
        <div className="mb-5">
          <label className="block text-sm font-medium text-[#9CA3AF] mb-2">
            Modelo predeterminado
          </label>
          <div className="space-y-2">
            {selectedProvider.models.map((modelId) => (
              <button
                key={modelId}
                onClick={() => onChange({ model: modelId })}
                className={`w-full flex items-center gap-3 h-11 px-4 rounded-xl border text-left transition-all duration-200 ${
                  state.model === modelId
                    ? "border-[#EAB308] bg-[#EAB308]/10"
                    : "border-[#2A2A35] bg-[#1A1A22] hover:border-[#3A3A45]"
                }`}
              >
                <span
                  className={`text-sm font-mono ${
                    state.model === modelId
                      ? "text-[#EAB308]"
                      : "text-[#9CA3AF]"
                  }`}
                >
                  {modelId}
                </span>
                {state.model === modelId && (
                  <div className="ml-auto w-4 h-4 rounded-full bg-[#EAB308] flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 text-[#0A0A0F]" />
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Info box — dónde conseguir API key */}
      {state.apiProvider && !state.apiKeySaved && selectedProvider && (
        <div className="bg-[#2C3E50]/20 border border-[#2C3E50]/30 rounded-xl p-4 mb-5">
          <p className="text-xs text-[#9CA3AF] mb-2">
            ¿No tenés una API key? Podés obtener una gratis en:
          </p>
          <a
            href={selectedProvider.dashboardUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-[#EAB308] hover:text-[#D4A017] underline transition-colors"
          >
            {selectedProvider.dashboardUrl}
          </a>
        </div>
      )}

      {/* Advertencia si no hay clave */}
      {!state.apiKeySaved && !state.apiProvider && (
        <div className="text-xs text-[#EAB308]/70 bg-[#EAB308]/5 border border-[#EAB308]/10 rounded-lg px-3 py-2 mb-5">
          ⚠️ Si omitís este paso, no podrás usar el chat hasta configurar una clave API en Configuración → API Keys.
        </div>
      )}

      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-[#6B7280] hover:text-[#9CA3AF] transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Atrás
        </button>
        <div className="flex items-center gap-3">
          {!state.apiKeySaved && (
            <button
              onClick={onNext}
              className="text-sm text-[#6B7280] hover:text-[#9CA3AF] transition-colors px-3 py-2"
            >
              Omitir por ahora
            </button>
          )}
          {state.apiKeySaved && (
            <button
              onClick={onNext}
              className="flex items-center gap-2 h-12 px-6 bg-[#EAB308] hover:bg-[#D4A017] text-[#0A0A0F] font-semibold rounded-xl transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
            >
              Continuar
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function StepListo({
  state,
  onFinish,
}: {
  state: OnboardingState;
  onFinish: () => void;
}) {
  const suggestions = state.areas
    .slice(0, 3)
    .map((a) => SUGGESTED_QUERIES_BY_AREA[a])
    .filter(Boolean);

  const defaultSuggestions = [
    "¿Cuáles son los requisitos para un despido justificado?",
    "¿Cómo se calcula la CTS en Perú?",
    "¿Qué dice el Art. 1351 del Código Civil sobre contratos?",
  ];

  const displaySuggestions = suggestions.length > 0 ? suggestions : defaultSuggestions;

  return (
    <div className="text-center">
      <CheckCircle2 className="w-16 h-16 text-[#34D399] mx-auto mb-6" />

      <h2 className="text-3xl font-bold text-[#F5F5F5] mb-3">¡Todo listo!</h2>
      <p className="text-[#9CA3AF] mb-8 max-w-md mx-auto">
        Tu cuenta está configurada. Aquí hay algunas consultas para empezar:
      </p>

      {!state.apiKeySaved && (
        <div className="flex items-center gap-2 mb-8 px-4 py-3 bg-[#EAB308]/10 border border-[#EAB308]/20 rounded-xl text-sm text-[#EAB308]">
          ⚠️ Recordá configurar tu clave API en{" "}
          <a href="/configuracion" className="underline font-medium">
            Configuración → API Keys
          </a>{" "}
          para poder usar el chat.
        </div>
      )}

      {/* Suggestion cards */}
      <div className="mb-8 text-left space-y-2">
        {displaySuggestions.map((s) => (
          <Link
            key={s}
            href={`/?q=${encodeURIComponent(s)}`}
            className="block bg-[#1A1A22] border border-[#2A2A35] rounded-xl p-4 text-sm text-[#9CA3AF] hover:border-[#EAB308]/50 hover:text-[#F5F5F5] transition-all duration-200 cursor-pointer"
          >
            {s}
          </Link>
        ))}
      </div>

      <button
        onClick={onFinish}
        className="inline-flex items-center gap-2 h-12 px-8 bg-[#EAB308] hover:bg-[#D4A017] text-[#0A0A0F] font-semibold rounded-xl transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
      >
        Ir al Chat
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}

// ————————————————————————————————————————————————
// PAGE
// ————————————————————————————————————————————————

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [animating, setAnimating] = useState(false);
  const [state, setState] = useState<OnboardingState>({
    name: "",
    role: "",
    areas: [],
    hasOrg: false,
    orgName: "",
    orgSlug: "",
    model: "",
    apiProvider: "",
    apiKey: "",
    apiKeyLabel: "",
    apiKeySaved: false,
  });

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

    // Step 2 → 3: Save profile to backend
    if (step === 2) {
      const token = getToken();
      if (token && state.name) {
        try {
          await fetch(`${API_URL}/api/auth/me`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ full_name: state.name }),
          });
        } catch {
          // Graceful degradation — localStorage already has the value
        }
      }
    }

    // Step 3 → 4: Create organization if user chose to have one
    if (step === 3 && state.hasOrg && state.orgName) {
      const token = getToken();
      if (token) {
        try {
          await fetch(`${API_URL}/api/organizations/`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ name: state.orgName, slug: state.orgSlug }),
          });
        } catch {
          // Graceful degradation — org creation failure doesn't block onboarding
        }
      }
    }

    setAnimating(true);
    setTimeout(() => {
      setStep((s) => s + 1);
      setAnimating(false);
    }, 150);
  };

  const goBack = () => {
    if (step <= 1) return;
    setAnimating(true);
    setTimeout(() => {
      setStep((s) => s - 1);
      setAnimating(false);
    }, 150);
  };

  const finish = () => {
    try {
      localStorage.setItem("tukijuris_onboarding_done", "true");
      // Save full prefs (role, areas, name, model) — used by various parts of the app
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
    router.push("/");
  };

  const skipAll = () => {
    try {
      localStorage.setItem("tukijuris_onboarding_done", "true");
    } catch {
      // ignore
    }
    router.push("/");
  };

  return (
    <div className="bg-[#0A0A0F] min-h-screen flex flex-col items-center justify-center px-4 py-12">
      {/* Progress bar */}
      <ProgressBar current={step} />

      {/* Step content card */}
      <div
        className={`w-full max-w-2xl bg-[#111116] border border-[#1E1E2A] rounded-2xl p-8 sm:p-10 transition-opacity duration-150 ${
          animating ? "opacity-0" : "opacity-100"
        }`}
      >
        {step === 1 && <StepBienvenido onNext={goNext} />}
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
          <StepConectaIA
            state={state}
            onChange={updateState}
            onNext={goNext}
            onBack={goBack}
          />
        )}
        {step === 5 && <StepListo state={state} onFinish={finish} />}
      </div>

      {/* Skip link below card */}
      {step < TOTAL_STEPS && (
        <button
          onClick={skipAll}
          className="mt-6 text-sm text-[#6B7280] hover:text-[#9CA3AF] transition-colors"
        >
          Omitir configuración
        </button>
      )}
    </div>
  );
}
