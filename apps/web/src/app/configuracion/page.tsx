"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Settings,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  User,
  Building2,
  Sliders,
  Key,
  Lock,
  Eye,
  EyeOff,
  Save,
  LogOut,
  Shield,
  BadgeCheck,
  Brain,
  Trash2,
  Plus,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/AuthContext";
import { FeatureGate } from "@/components/FeatureGate";
import { AppLayout } from "@/components/AppLayout";
import { InternalPageHeader } from "@/components/shell/InternalPageHeader";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";
import { MODEL_CATALOG } from "@/lib/models";

interface UserProfile {
  id: string;
  email: string;
  name?: string;
  is_admin?: boolean;
  auth_provider?: string;
}

interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  role?: string;
}

const LEGAL_AREAS = [
  { id: "", name: "Sin preferencia" },
  { id: "civil", name: "Civil" },
  { id: "penal", name: "Penal" },
  { id: "laboral", name: "Laboral" },
  { id: "tributario", name: "Tributario" },
  { id: "constitucional", name: "Constitucional" },
  { id: "administrativo", name: "Administrativo" },
  { id: "corporativo", name: "Corporativo" },
  { id: "registral", name: "Registral" },
  { id: "comercio_exterior", name: "Comercio Exterior" },
  { id: "compliance", name: "Compliance" },
  { id: "competencia", name: "Competencia/PI" },
];

const PROVIDER_ORDER = ["google", "groq", "deepseek", "openai", "anthropic", "xai"] as const;

const PROVIDER_LABELS: Record<string, { name: string; color: string; tone: string }> = {
  google: { name: "Google (Gemini)", color: "text-blue-400", tone: "from-blue-500/12 to-blue-500/5 border-blue-500/20" },
  groq: { name: "Groq", color: "text-orange-400", tone: "from-orange-500/12 to-orange-500/5 border-orange-500/20" },
  deepseek: { name: "DeepSeek", color: "text-cyan-400", tone: "from-cyan-500/12 to-cyan-500/5 border-cyan-500/20" },
  openai: { name: "OpenAI", color: "text-green-400", tone: "from-green-500/12 to-green-500/5 border-green-500/20" },
  anthropic: { name: "Anthropic", color: "text-amber-400", tone: "from-amber-500/12 to-amber-500/5 border-amber-500/20" },
  xai: { name: "xAI (Grok)", color: "text-purple-400", tone: "from-purple-500/12 to-purple-500/5 border-purple-500/20" },
};

const tierBadgeStyles: Record<string, string> = {
  free: "bg-[#1a3a2a] text-[#6ee7b7]",
  standard: "bg-secondary-container text-secondary",
  pro: "bg-[#2d1f4a] text-[#c4b5fd]",
};

const tierBadgeLabels: Record<string, string> = {
  free: "Gratis",
  standard: "Estándar",
  pro: "Avanzado",
};

type ActiveTab = "perfil" | "organizacion" | "preferencias" | "apikeys" | "memoria";

const TABS: { id: ActiveTab; label: string; icon: React.ElementType }[] = [
  { id: "perfil", label: "Perfil", icon: User },
  { id: "organizacion", label: "Organizacion", icon: Building2 },
  { id: "preferencias", label: "Preferencias", icon: Sliders },
  { id: "memoria", label: "Memoria", icon: Brain },
  { id: "apikeys", label: "API Keys", icon: Key },
];

const TAB_DETAILS: Record<ActiveTab, { title: string; description: string }> = {
  perfil: {
    title: "Perfil y seguridad",
    description: "Actualizá tus datos personales y protegé el acceso a tu cuenta con una contraseña fuerte.",
  },
  organizacion: {
    title: "Organización",
    description: "Administrá la identidad del equipo, el plan activo y las acciones sensibles sobre la organización.",
  },
  preferencias: {
    title: "Preferencias operativas",
    description: "Elegí el modelo y el área legal que TukiJuris debe priorizar cuando iniciás una consulta.",
  },
  memoria: {
    title: "Memoria contextual",
    description: "Controlá qué recuerda el sistema sobre vos para personalizar mejor las respuestas futuras.",
  },
  apikeys: {
    title: "Conexiones de IA",
    description: "Vinculá tus proveedores, probá claves y mantené el control del consumo desde un solo lugar.",
  },
};

function SectionCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`panel-base rounded-[1.35rem] p-5 sm:p-6 ${className}`}>{children}</section>;
}

function SectionHeader({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description?: string;
}) {
  return (
    <div className="mb-5 flex items-start gap-3">
      <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
        {icon}
      </div>
      <div className="min-w-0">
        <h2 className="font-['Newsreader'] text-[1.35rem] font-bold leading-none tracking-[-0.02em] text-on-surface">{title}</h2>
        {description && <p className="mt-1.5 text-sm leading-6 text-on-surface/55">{description}</p>}
      </div>
    </div>
  );
}

function DisclosureCard({
  title,
  description,
  icon,
  open,
  onToggle,
  children,
  tone = "default",
}: {
  title: string;
  description?: string;
  icon: React.ReactNode;
  open: boolean;
  onToggle: () => void;
  children?: React.ReactNode;
  tone?: "default" | "danger";
}) {
  const cardTone =
    tone === "danger"
      ? "border border-[#ffb4ab]/20 bg-[#93000a]/10"
      : "";

  return (
    <SectionCard className={`overflow-hidden ${cardTone}`}>
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-start justify-between gap-4 text-left"
        aria-expanded={open}
      >
        <SectionHeader icon={icon} title={title} description={description} />
        <div className="mb-5 shrink-0 rounded-xl border border-[rgba(79,70,51,0.15)] bg-surface px-3 py-2 text-on-surface/55">
          {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>

      {open ? (
        children
      ) : (
        <div className="-mt-1 rounded-2xl border border-dashed border-[rgba(79,70,51,0.15)] bg-surface/60 px-4 py-3 text-sm text-on-surface/45">
          Oculto para reducir ruido visual. Abrilo solo cuando lo necesites.
        </div>
      )}
    </SectionCard>
  );
}

// Memory types
interface MemoryItem {
  id: string;
  category: string;
  content: string;
  confidence: number;
  is_active: boolean;
  created_at: string;
}

interface MemoryGroup {
  category: string;
  label: string;
  memories: MemoryItem[];
}

interface MemoriesData {
  groups: MemoryGroup[];
  total: number;
  active_count: number;
}

const CATEGORY_COLORS: Record<string, string> = {
  profession: "bg-secondary-container text-secondary",
  interests: "bg-[#1a3a2a] text-[#6ee7b7]",
  cases: "bg-[#4f3700]/40 text-primary",
  preferences: "bg-[#2d1f4a] text-[#c4b5fd]",
  context: "bg-[#0f2d35] text-[#67e8f9]",
};

// LLM Key types
interface LLMKey {
  id: string;
  provider: string;
  label?: string;
  hint: string;
  is_active?: boolean;
  created_at?: string;
}

interface LLMProvider {
  id: string;
  name: string;
  description: string;
  accent: string;
  accentBg: string;
  accentBorder: string;
  docsUrl: string;
  docsLabel: string;
  models: string[];
  recommended?: boolean;
  note?: string;
}

const LLM_PROVIDERS: LLMProvider[] = [
  {
    id: "google",
    name: "Google AI (Gemini)",
    description: "Gemini Flash es gratuito. Gemini 3.1 Pro es el flagship con Deep Think y 1M contexto.",
    accent: "text-blue-400",
    accentBg: "bg-blue-500/10",
    accentBorder: "border-blue-500/30",
    docsUrl: "https://aistudio.google.com/apikey",
    docsLabel: "aistudio.google.com/apikey",
    models: ["Gemini 2.5 Flash (gratis)", "Gemini 2.5 Pro", "Gemini 3.1 Flash-Lite", "Gemini 3.1 Pro"],
    recommended: true,
  },
  {
    id: "groq",
    name: "Groq (Ultra Rápido)",
    description: "Inferencia hasta 1000 t/s. Ideal para respuestas instantáneas con modelos open-source.",
    accent: "text-orange-400",
    accentBg: "bg-orange-500/10",
    accentBorder: "border-orange-500/30",
    docsUrl: "https://console.groq.com/keys",
    docsLabel: "console.groq.com/keys",
    models: ["Llama 3.1 8B", "Llama 3.3 70B", "Qwen3 32B", "GPT-OSS 120B"],
    recommended: true,
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    description: "V3.2 con 128K contexto. Reasoner usa thinking mode para análisis legal profundo.",
    accent: "text-cyan-400",
    accentBg: "bg-cyan-500/10",
    accentBorder: "border-cyan-500/30",
    docsUrl: "https://platform.deepseek.com/api_keys",
    docsLabel: "platform.deepseek.com",
    models: ["DeepSeek V3.2 ($0.28/M)", "DeepSeek Reasoner"],
  },
  {
    id: "openai",
    name: "OpenAI",
    description: "GPT-5.4 con 1M contexto y 128K output. Flagship de OpenAI para análisis legal.",
    accent: "text-green-400",
    accentBg: "bg-green-500/10",
    accentBorder: "border-green-500/30",
    docsUrl: "https://platform.openai.com/api-keys",
    docsLabel: "platform.openai.com/api-keys",
    models: ["GPT-5.4 Nano ($0.20/M)", "GPT-5.4 Mini ($0.75/M)", "GPT-5.4 ($2.50/M)"],
  },
  {
    id: "anthropic",
    name: "Anthropic (Claude)",
    description: "Claude 4.6 — el más inteligente del mercado. 1M contexto, excelente razonamiento legal.",
    accent: "text-amber-400",
    accentBg: "bg-amber-500/10",
    accentBorder: "border-amber-500/30",
    docsUrl: "https://console.anthropic.com/settings/keys",
    docsLabel: "console.anthropic.com",
    models: ["Haiku 4.5 ($1/M)", "Sonnet 4.6 ($3/M)", "Opus 4.6 ($5/M)"],
  },
  {
    id: "xai",
    name: "xAI (Grok)",
    description: "Grok 4.20 — menor alucinación del mercado. 2M contexto, reasoning + tool-calling.",
    accent: "text-purple-400",
    accentBg: "bg-purple-500/10",
    accentBorder: "border-purple-500/30",
    docsUrl: "https://console.x.ai",
    docsLabel: "console.x.ai",
    models: ["Grok 3 Mini Fast ($0.30/M)", "Grok 4.1 Fast ($0.20/M)", "Grok 4 ($3/M)", "Grok 4.20 ($2/M)"],
  },
];

// ---------------------------------------------------------------------------
// Change-password error mapper (pure, module-level — FCB-1..FCB-6)
// ---------------------------------------------------------------------------
type ChangePwdDetail =
  | string
  | { code?: string; auth_provider?: string }
  | null
  | undefined;

/**
 * Maps POST /api/auth/change-password error responses to user-friendly Spanish messages.
 * FCB-1: 401 invalid_credentials → wrong current password (no logout)
 * FCB-2: 400 oauth_password_unsupported → OAuth user, interpolate provider
 * FCB-3: 400 new_password_same_as_current → same password
 * FCB-4: 422 → verbatim validator message
 * FCB-5: 429 → rate-limit copy
 * FCB-6: 401 session-expiry handled in caller before reaching this function
 */
function mapChangePasswordError(status: number, detail: ChangePwdDetail): string {
  if (status === 401) {
    // FCB-1: invalid credentials (session-expiry 401 never reaches here)
    return "La contraseña actual es incorrecta.";
  }
  if (status === 400) {
    if (
      typeof detail === "object" &&
      detail !== null &&
      detail.code === "oauth_password_unsupported"
    ) {
      // FCB-2
      const provider = detail.auth_provider ?? "social";
      return `Tu cuenta usa inicio de sesión social (${provider}). No se puede cambiar contraseña aquí.`;
    }
    if (detail === "new_password_same_as_current") {
      // FCB-3
      return "La nueva contraseña debe ser distinta a la actual.";
    }
  }
  if (status === 422) {
    // FCB-4: verbatim validator message
    return typeof detail === "string" && detail
      ? detail
      : "La nueva contraseña no cumple los requisitos.";
  }
  if (status === 429) {
    // FCB-5
    return "Demasiados intentos. Esperá un momento e intentá de nuevo.";
  }
  return "No se pudo cambiar la contraseña. Intentá de nuevo.";
}

export default function ConfiguracionPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("perfil");
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [org, setOrg] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Perfil fields
  const [profileName, setProfileName] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);

  // Password fields
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPw, setShowCurrentPw] = useState(false);
  const [showNewPw, setShowNewPw] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [isPasswordPanelOpen, setIsPasswordPanelOpen] = useState(false);

  // Org fields
  const [orgName, setOrgName] = useState("");
  const [savingOrg, setSavingOrg] = useState(false);

  // Memory fields
  const [memoriesData, setMemoriesData] = useState<MemoriesData | null>(null);
  const [loadingMemories, setLoadingMemories] = useState(false);
  const [clearingMemories, setClearingMemories] = useState(false);
  const [memoryEnabled, setMemoryEnabled] = useState(true);
  const [isProfileInfoOpen, setIsProfileInfoOpen] = useState(true);
  const [isOrgInfoOpen, setIsOrgInfoOpen] = useState(true);
  const [isOrgDangerOpen, setIsOrgDangerOpen] = useState(false);
  const [isMemoryListOpen, setIsMemoryListOpen] = useState(true);
  const [isMemoryDangerOpen, setIsMemoryDangerOpen] = useState(false);
  const [isApiOverviewOpen, setIsApiOverviewOpen] = useState(true);
  const [expandedProviderId, setExpandedProviderId] = useState<string | null>(null);

  // Preferences (stored in localStorage)
  const [defaultModel, setDefaultModel] = useState(MODEL_CATALOG[0].id);
  const [defaultArea, setDefaultArea] = useState("");
  const [selectedProvider, setSelectedProvider] = useState<string>(MODEL_CATALOG[0]?.provider || "google");

  // LLM Keys state
  const [llmKeys, setLlmKeys] = useState<LLMKey[]>([]);
  const [loadingLlmKeys, setLoadingLlmKeys] = useState(false);
  const [addingProvider, setAddingProvider] = useState<string | null>(null);
  const [newApiKey, setNewApiKey] = useState("");
  const [newApiLabel, setNewApiLabel] = useState("");
  const [savingKey, setSavingKey] = useState(false);
  const [deletingKeyId, setDeletingKeyId] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { ok: boolean; latency_ms?: number; error?: string }>>({});

  const inputClassName = "control-surface w-full rounded-xl px-3 py-3 text-sm text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors";
  const readonlyClassName = "w-full rounded-xl border border-transparent bg-surface px-3 py-3 text-sm text-on-surface/40 cursor-not-allowed";
  const labelClassName = "mb-1.5 block text-[11px] font-medium uppercase tracking-[0.18em] text-on-surface/42";

  const activeTabMeta = TAB_DETAILS[activeTab];
  const configuredProviders = new Set(llmKeys.map((key) => key.provider));
  const selectedModelMeta = MODEL_CATALOG.find((model) => model.id === defaultModel) || MODEL_CATALOG[0];
  const visibleProvider = PROVIDER_LABELS[selectedProvider] ? selectedProvider : selectedModelMeta?.provider || "google";
  const visibleModels = MODEL_CATALOG.filter((model) => model.provider === visibleProvider);

  useEffect(() => {
    if (selectedModelMeta?.provider && selectedModelMeta.provider !== selectedProvider) {
      setSelectedProvider(selectedModelMeta.provider);
    }
  }, [selectedModelMeta, selectedProvider]);

  const { authFetch, logout, logoutAll } = useAuth();
  const router = useRouter();

  const showSuccess = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 3000);
  };

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [meRes, orgRes] = await Promise.allSettled([
        authFetch(`/api/auth/me`, {}),
        authFetch(`/api/organizations/`, {}),
      ]);

      if (meRes.status === "fulfilled" && meRes.value.ok) {
        const me: UserProfile = await meRes.value.json();
        setProfile(me);
        setProfileName(me.name || "");
      }

      if (orgRes.status === "fulfilled" && orgRes.value.ok) {
        const orgData = await orgRes.value.json();
        const orgs = Array.isArray(orgData) ? orgData : orgData.organizations || [];
        if (orgs.length > 0) {
          setOrg(orgs[0]);
          setOrgName(orgs[0].name || "");
        }
      }

      if (typeof window !== "undefined") {
        const savedModel = localStorage.getItem("pref_default_model");
        const savedArea = localStorage.getItem("pref_default_area");
        if (savedModel) setDefaultModel(savedModel);
        if (savedArea) setDefaultArea(savedArea);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    setSavingProfile(true);
    setError("");
    try {
      const res = await authFetch(`/api/auth/me`, {
        method: "PUT",
        body: JSON.stringify({ name: profileName }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "No se pudo actualizar el perfil");
      }
      showSuccess("Perfil actualizado correctamente");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }
    if (newPassword.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres");
      return;
    }
    setSavingPassword(true);
    setError("");
    try {
      const res = await authFetch(`/api/auth/change-password`, {
        method: "POST",
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        // FCB-6: 401 that is NOT invalid_credentials → session expiry → force logout + redirect
        if (res.status === 401 && data?.detail !== "invalid_credentials") {
          setError("Tu sesión expiró. Iniciá sesión de nuevo.");
          setTimeout(async () => {
            try {
              await logout();
            } finally {
              router.push("/login");
            }
          }, 1500);
          return;
        }
        setError(mapChangePasswordError(res.status, data?.detail ?? data));
        return;
      }
      // FCB-7: success toast
      showSuccess("Contraseña actualizada. Por seguridad, iniciá sesión de nuevo.");
      // FCB-9: clear form fields immediately (cosmetic — user is leaving)
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      // FCB-8: after 1500 ms logout and always redirect, even if logout throws
      setTimeout(async () => {
        try {
          await logout();
        } finally {
          router.push("/login");
        }
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo cambiar la contraseña. Intentá de nuevo.");
    } finally {
      setSavingPassword(false);
    }
  };

  const handleSaveOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    setSavingOrg(true);
    setError("");
    try {
      const res = await authFetch(`/api/organizations/${org.id}`, {
        method: "PUT",
        body: JSON.stringify({ name: orgName }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "No se pudo actualizar la organizacion");
      }
      showSuccess("Organizacion actualizada correctamente");
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSavingOrg(false);
    }
  };

  const handleSavePreferences = (e: React.FormEvent) => {
    e.preventDefault();
    if (typeof window !== "undefined") {
      localStorage.setItem("pref_default_model", defaultModel);
      localStorage.setItem("pref_default_area", defaultArea);
    }
    showSuccess("Preferencias guardadas");
  };

  const loadMemories = useCallback(async () => {
    setLoadingMemories(true);
    try {
      const res = await authFetch(`/api/memory/`, {});
      if (res.ok) {
        const data: MemoriesData = await res.json();
        setMemoriesData(data);
      }
    } catch {
      // fail silently — memory is non-critical
    } finally {
      setLoadingMemories(false);
    }
  }, [authFetch]);

  const handleToggleMemory = async (memoryId: string, isActive: boolean) => {
    try {
      const res = await authFetch(`/api/memory/${memoryId}/toggle`, {
        method: "PUT",
        body: JSON.stringify({ is_active: isActive }),
      });
      if (res.ok) {
        await loadMemories();
      }
    } catch {
      setError("No se pudo actualizar la memoria");
    }
  };

  const handleDeleteMemory = async (memoryId: string) => {
    if (!confirm("Eliminar esta memoria? Esta accion es irreversible.")) return;
    try {
      const res = await authFetch(`/api/memory/${memoryId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        await loadMemories();
        showSuccess("Memoria eliminada");
      }
    } catch {
      setError("No se pudo eliminar la memoria");
    }
  };

  const loadLlmKeys = useCallback(async () => {
    setLoadingLlmKeys(true);
    try {
      const res = await authFetch(`/api/keys/llm-keys`, {});
      if (res.ok) {
        const data = await res.json();
        setLlmKeys(Array.isArray(data) ? data : data.keys || []);
      }
    } catch {
      // fail silently
    } finally {
      setLoadingLlmKeys(false);
    }
  }, [authFetch]);

  useEffect(() => {
    if (activeTab === "memoria") {
      loadMemories();
    }
    if (activeTab === "apikeys" || activeTab === "preferencias") {
      loadLlmKeys();
    }
  }, [activeTab, loadMemories, loadLlmKeys]);

  const handleAddKey = async (providerId: string) => {
    if (!newApiKey.trim()) return;
    setSavingKey(true);
    setError("");
    try {
      const res = await authFetch(`/api/keys/llm-keys`, {
        method: "POST",
        body: JSON.stringify({ provider: providerId, api_key: newApiKey.trim(), label: newApiLabel.trim() || undefined }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "No se pudo guardar la clave");
      }
      showSuccess("Clave API guardada correctamente");
      setAddingProvider(null);
      setNewApiKey("");
      setNewApiLabel("");
      setShowApiKey(false);
      await loadLlmKeys();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar la clave");
    } finally {
      setSavingKey(false);
    }
  };

  const handleDeleteKey = async (keyId: string) => {
    if (!confirm("Eliminar esta clave API? Esta accion es irreversible.")) return;
    setDeletingKeyId(keyId);
    try {
      const res = await authFetch(`/api/keys/llm-keys/${keyId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        showSuccess("Clave eliminada");
        await loadLlmKeys();
      }
    } catch {
      setError("No se pudo eliminar la clave");
    } finally {
      setDeletingKeyId(null);
    }
  };

  const handleTestKey = async (providerId: string) => {
    setTestingProvider(providerId);
    setTestResults((prev) => {
      const next = { ...prev };
      delete next[providerId];
      return next;
    });
    try {
      const res = await authFetch(`/api/keys/llm-keys/test`, {
        method: "POST",
        body: JSON.stringify({ provider: providerId }),
      });
      const data = await res.json();
      setTestResults((prev) => ({ ...prev, [providerId]: data }));
    } catch {
      setTestResults((prev) => ({
        ...prev,
        [providerId]: { ok: false, error: "No se pudo conectar al servidor" },
      }));
    } finally {
      setTestingProvider(null);
    }
  };

  const handleClearAllMemories = async () => {
    if (!confirm("Borrar TODA la memoria de contexto? Esta accion es irreversible.")) return;
    setClearingMemories(true);
    try {
      const res = await authFetch(`/api/memory/`, {
        method: "DELETE",
      });
      if (res.ok) {
        await loadMemories();
        showSuccess("Toda la memoria fue eliminada");
      }
    } catch {
      setError("No se pudo borrar la memoria");
    } finally {
      setClearingMemories(false);
    }
  };

  const handleLogout = () => {
    void logout();
  };

  const handleLogoutAll = () => {
    void logoutAll();
  };

  return (
    <AppLayout>
      <div className="flex min-h-full flex-col text-on-surface">
        <InternalPageHeader
          icon={<Settings className="w-5 h-5 text-primary" />}
          eyebrow="Cuenta"
          title="Configuración"
          description="Administrá perfil, seguridad, claves y preferencias desde una estructura consistente con el resto del producto."
          utilitySlot={<div className="hidden md:flex"><ShellUtilityActions showSettingsLink={false} /></div>}
          compact
        />

        <div className="w-full px-4 py-6 sm:py-8 lg:px-6 xl:px-8">
          {/* Alerts */}
          {error && (
            <div className="flex items-center gap-3 bg-[#93000a]/20 border border-[#ffb4ab]/30 text-[#ffb4ab] rounded-lg px-4 py-3 mb-6 text-sm">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {successMsg && (
            <div className="flex items-center gap-3 bg-[#1a3a2a]/60 border border-[#6ee7b7]/20 text-[#6ee7b7] rounded-lg px-4 py-3 mb-6 text-sm">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-24 gap-3">
              <Loader2 className="w-8 h-8 text-primary animate-spin" />
              <p className="text-sm text-on-surface/40">Cargando configuracion...</p>
            </div>
          ) : (
            <div className="flex flex-col gap-4 lg:flex-row xl:gap-6">
              {/* Sidebar */}
              <aside className="shrink-0 lg:sticky lg:top-20 lg:w-60 xl:w-64 lg:self-start">
                {/* Mobile: horizontal scroll tabs */}
                <div className="lg:hidden overflow-x-auto">
                  <div className="panel-base flex gap-1 rounded-xl p-1 min-w-max">
                    {TABS.map((tab) => {
                      const Icon = tab.icon;
                      return (
                        <button
                          key={tab.id}
                          onClick={() => { setActiveTab(tab.id); setError(""); }}
                          className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors whitespace-nowrap ${
                            activeTab === tab.id
                              ? "bg-primary/10 text-primary"
                              : "text-on-surface/60 hover:text-on-surface hover:bg-surface-container"
                          }`}
                        >
                          <Icon className="w-4 h-4" />
                          {tab.label}
                        </button>
                      );
                    })}
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm text-[#ffb4ab]/70 hover:text-[#ffb4ab] transition-colors whitespace-nowrap"
                    >
                      <LogOut className="w-4 h-4" />
                      Salir
                    </button>
                  </div>
                </div>

                {/* Desktop: vertical sidebar */}
                <nav className="panel-base hidden overflow-hidden rounded-[1.35rem] lg:block">
                  {TABS.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => { setActiveTab(tab.id); setError(""); }}
                        className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors border-b border-[rgba(79,70,51,0.15)] last:border-0 ${
                          activeTab === tab.id
                            ? "bg-primary/10 text-primary"
                            : "text-on-surface/60 hover:text-on-surface hover:bg-surface-container"
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                        {tab.label}
                      </button>
                    );
                  })}
                  <div className="border-t border-[rgba(79,70,51,0.15)]">
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-4 py-3 text-sm text-[#ffb4ab]/70 hover:text-[#ffb4ab] hover:bg-[#93000a]/20 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      Cerrar sesion
                    </button>
                  </div>
                </nav>
              </aside>

              {/* Tab Content */}
              <div className="flex-1 min-w-0">
                <div className="mb-3 flex flex-col gap-2 sm:mb-4 xl:flex-row xl:items-center xl:justify-between">
                  <div className="min-w-0 flex-1">
                    <p className="section-eyebrow text-primary/80">{TABS.find((tab) => tab.id === activeTab)?.label}</p>
                    <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1.5">
                      <h2 className="font-['Newsreader'] text-[1.35rem] font-bold leading-none tracking-[-0.04em] text-on-surface sm:text-[1.55rem]">
                        {activeTabMeta.title}
                      </h2>
                      <p className="max-w-2xl text-[13px] leading-5 text-on-surface/50">{activeTabMeta.description}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 xl:justify-end">
                    <div className="rounded-xl border border-[rgba(79,70,51,0.15)] bg-surface px-3 py-1.5">
                      <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/38">Cuenta</p>
                      <p className="mt-1 max-w-[18rem] truncate text-xs font-medium text-on-surface">{profile?.email || "Sin email"}</p>
                    </div>
                    <div className="rounded-xl border border-[rgba(79,70,51,0.15)] bg-surface px-3 py-1.5">
                      <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/38">Organización</p>
                      <p className="mt-1 max-w-[12rem] truncate text-xs font-medium text-on-surface">{org?.name || "Sin organización"}</p>
                    </div>
                    {activeTab === "perfil" && (
                      <button
                        type="button"
                        onClick={() => setIsPasswordPanelOpen((prev) => !prev)}
                        className="inline-flex items-center gap-2 rounded-xl border border-[rgba(79,70,51,0.15)] bg-surface px-3 py-2 text-xs font-medium text-on-surface/65 transition-colors hover:border-primary/30 hover:text-on-surface"
                      >
                        <Lock className="h-3.5 w-3.5 text-primary" />
                        {isPasswordPanelOpen ? "Ocultar clave" : "Cambiar clave"}
                        {isPasswordPanelOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                      </button>
                    )}
                  </div>
                </div>

                {/* --- PERFIL TAB --- */}
                {activeTab === "perfil" && (
                  <div className="space-y-4">
                    <DisclosureCard
                      icon={<User className="w-4 h-4" />}
                      title="Información del perfil"
                      description="Editá tu identidad visible dentro del sistema."
                      open={isProfileInfoOpen}
                      onToggle={() => setIsProfileInfoOpen((prev) => !prev)}
                    >
                      <form onSubmit={handleSaveProfile} className="space-y-4">
                        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
                          <div>
                            <label className={labelClassName}>
                              Correo electronico
                            </label>
                            <input
                              type="email"
                              value={profile?.email || ""}
                              readOnly
                              className={readonlyClassName}
                            />
                            <p className="mt-1 text-[10px] text-on-surface/30">El email no puede ser modificado</p>
                          </div>
                          <div>
                            <label className={labelClassName}>
                              Nombre
                            </label>
                            <input
                              type="text"
                              value={profileName}
                              onChange={(e) => setProfileName(e.target.value)}
                              placeholder="Tu nombre completo"
                              className={inputClassName}
                            />
                          </div>
                        </div>
                        <div className="flex justify-end">
                          <button
                            type="submit"
                            disabled={savingProfile}
                            className="gold-gradient disabled:opacity-40 text-on-primary rounded-xl px-5 py-2.5 text-sm font-bold flex items-center gap-2 shadow-[0_12px_24px_rgba(0,0,0,0.14)] transition-opacity"
                          >
                            {savingProfile ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                            Guardar cambios
                          </button>
                        </div>
                      </form>
                    </DisclosureCard>

                    {/* FCB-10/FCB-11: hide form for OAuth users, show info card instead */}
                    {profile?.auth_provider && profile.auth_provider !== "email" ? (
                      <SectionCard>
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                            <Lock className="w-4 h-4" />
                          </div>
                          <div>
                            <h2 className="font-['Newsreader'] text-[1.35rem] font-bold leading-none tracking-[-0.02em] text-on-surface">
                              Contraseña gestionada externamente
                            </h2>
                            <p className="mt-1.5 text-sm leading-6 text-on-surface/55">
                              Tu cuenta usa inicio de sesión con{" "}
                              <span className="font-medium text-on-surface">{profile.auth_provider}</span>
                              . La contraseña es gestionada en {profile.auth_provider}.
                            </p>
                          </div>
                        </div>
                      </SectionCard>
                    ) : (
                      <DisclosureCard
                        icon={<Lock className="w-4 h-4" />}
                        title="Cambiar contraseña"
                        description="Abrilo solo cuando realmente necesites actualizar tu clave."
                        open={isPasswordPanelOpen}
                        onToggle={() => setIsPasswordPanelOpen((prev) => !prev)}
                      >
                          <form onSubmit={handleChangePassword} className="space-y-4">
                            <div className="grid gap-4 lg:grid-cols-2">
                              <div>
                                <label className={labelClassName}>
                                  Contrasena actual
                                </label>
                                <div className="relative">
                                  <input
                                    type={showCurrentPw ? "text" : "password"}
                                    value={currentPassword}
                                    onChange={(e) => setCurrentPassword(e.target.value)}
                                    placeholder="••••••••"
                                    className={`${inputClassName} pr-10`}
                                    required
                                  />
                                  <button
                                    type="button"
                                    onClick={() => setShowCurrentPw(!showCurrentPw)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface/40 hover:text-on-surface transition-colors"
                                  >
                                    {showCurrentPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                  </button>
                                </div>
                              </div>
                              <div>
                                <label className={labelClassName}>
                                  Nueva contrasena
                                </label>
                                <div className="relative">
                                  <input
                                    type={showNewPw ? "text" : "password"}
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    placeholder="Minimo 8 caracteres"
                                    className={`${inputClassName} pr-10`}
                                    required
                                    minLength={8}
                                  />
                                  <button
                                    type="button"
                                    onClick={() => setShowNewPw(!showNewPw)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface/40 hover:text-on-surface transition-colors"
                                  >
                                    {showNewPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                  </button>
                                </div>
                              </div>
                            </div>
                            <div>
                              <label className={labelClassName}>
                                Confirmar nueva contrasena
                              </label>
                              <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="Repite la nueva contrasena"
                                className={inputClassName}
                                required
                              />
                            </div>
                            <div className="flex justify-end gap-2">
                              <button
                                type="button"
                                onClick={() => setIsPasswordPanelOpen(false)}
                                className="rounded-xl border border-[rgba(79,70,51,0.15)] px-4 py-2.5 text-sm text-on-surface/55 transition-colors hover:text-on-surface"
                              >
                                Cancelar
                              </button>
                              <button
                                type="submit"
                                disabled={savingPassword || !currentPassword || !newPassword || !confirmPassword}
                                className="bg-gradient-to-br from-primary to-primary-container disabled:opacity-40 text-on-primary rounded-lg px-5 py-2.5 text-sm font-bold flex items-center gap-2 transition-opacity"
                              >
                                {savingPassword ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Lock className="w-3.5 h-3.5" />}
                                Actualizar contrasena
                              </button>
                            </div>
                          </form>
                      </DisclosureCard>
                    )}

                    {/* Logout all devices */}
                    <div className="flex items-center justify-between rounded-xl border border-[rgba(79,70,51,0.15)] bg-surface-container px-4 py-3.5">
                      <div>
                        <p className="text-sm font-medium text-on-surface">Cerrar sesion en todos los dispositivos</p>
                        <p className="mt-0.5 text-xs text-on-surface/50">Revoca todos los tokens activos e invalida todas las sesiones abiertas.</p>
                      </div>
                      <button
                        type="button"
                        onClick={handleLogoutAll}
                        data-testid="logout-all-btn"
                        className="flex items-center gap-2 rounded-lg border border-[#ffb4ab]/30 px-4 py-2 text-sm text-[#ffb4ab] transition-colors hover:bg-[#93000a]/20"
                      >
                        <LogOut className="w-3.5 h-3.5" />
                        Cerrar todas las sesiones
                      </button>
                    </div>
                  </div>
                )}

                {/* --- ORGANIZACION TAB --- */}
                {activeTab === "organizacion" && (
                  <div className="space-y-4">
                    {org ? (
                      <>
                        <DisclosureCard
                          icon={<Building2 className="w-4 h-4" />}
                          title="Datos de la organización"
                          description="Nombre, slug y plan activo del equipo."
                          open={isOrgInfoOpen}
                          onToggle={() => setIsOrgInfoOpen((prev) => !prev)}
                        >
                          <form onSubmit={handleSaveOrg} className="space-y-4">
                            <div>
                              <label className={labelClassName}>
                                Nombre de la organizacion
                              </label>
                              <input
                                type="text"
                                value={orgName}
                                onChange={(e) => setOrgName(e.target.value)}
                                placeholder="Nombre de tu organizacion"
                                className={inputClassName}
                                required
                              />
                            </div>
                            <div>
                              <label className={labelClassName}>
                                Identificador (slug)
                              </label>
                              <input
                                type="text"
                                value={org.slug}
                                readOnly
                                className={readonlyClassName}
                              />
                              <p className="text-[10px] text-on-surface/30 mt-1">El slug no puede ser modificado</p>
                            </div>
                            <div>
                              <label className={labelClassName}>Plan</label>
                              <div className="flex items-center gap-2 rounded-xl border border-[rgba(79,70,51,0.15)] bg-surface px-3 py-3">
                                <span className="text-sm text-on-surface capitalize">{org.plan}</span>
                                <Link href="/billing" className="text-xs text-primary hover:text-primary-container transition-colors">
                                  Cambiar plan
                                </Link>
                              </div>
                            </div>
                            <div className="flex justify-end">
                              <button
                                type="submit"
                                disabled={savingOrg || !orgName.trim()}
                                className="bg-gradient-to-br from-primary to-primary-container disabled:opacity-40 text-on-primary rounded-lg px-5 py-2.5 text-sm font-bold flex items-center gap-2 transition-opacity"
                              >
                                {savingOrg ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                                Guardar cambios
                              </button>
                            </div>
                          </form>
                        </DisclosureCard>

                        <DisclosureCard
                          icon={<AlertTriangle className="w-4 h-4 text-[#ffb4ab]" />}
                          title="Zona de peligro"
                          description="Acciones sensibles e irreversibles sobre tu organización."
                          open={isOrgDangerOpen}
                          onToggle={() => setIsOrgDangerOpen((prev) => !prev)}
                          tone="danger"
                        >
                          <button
                            onClick={async () => {
                              if (!org || !profile) return;
                              if (!confirm("¿Estás seguro que querés abandonar esta organización? Esta acción no se puede deshacer.")) return;
                              try {
                                const res = await authFetch(
                                  `/api/organizations/${org.id}/members/${profile.id}`,
                                  { method: "DELETE" }
                                );
                                if (!res.ok) {
                                  const data = await res.json().catch(() => null);
                                  throw new Error(data?.detail || "Error al abandonar la organización");
                                }
                                window.location.reload();
                              } catch (err: unknown) {
                                setError(err instanceof Error ? err.message : "Error al abandonar la organización");
                              }
                            }}
                            className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-[#ffb4ab]/30 text-[#ffb4ab] hover:bg-[#93000a]/20 text-sm transition-colors"
                          >
                            <LogOut className="w-3.5 h-3.5" />
                            Abandonar organizacion
                          </button>
                        </DisclosureCard>
                      </>
                    ) : (
                      <SectionCard className="py-8 text-center">
                        <Building2 className="w-10 h-10 text-on-surface/10 mx-auto mb-3" />
                        <p className="text-sm text-on-surface/40 mb-4">No perteneces a ninguna organizacion</p>
                        <Link
                          href="/organizacion"
                          className="inline-flex items-center gap-2 bg-gradient-to-br from-primary to-primary-container text-on-primary rounded-lg px-4 py-2.5 text-sm font-bold transition-opacity"
                        >
                          <Building2 className="w-4 h-4" />
                          Crear organizacion
                        </Link>
                      </SectionCard>
                    )}
                  </div>
                )}

                {/* --- PREFERENCIAS TAB --- */}
                {activeTab === "preferencias" && (
                  <div className="grid gap-4 xl:grid-cols-[minmax(0,1.65fr)_23rem] xl:items-stretch">
                    <SectionCard className="h-full">
                      <SectionHeader
                        icon={<Sliders className="w-4 h-4" />}
                        title="Studio de preferencias"
                        description="Elegí un proveedor primero y después seleccioná el modelo que querés priorizar. Mostramos una sola escena a la vez para que no tengas que scrollear." 
                      />

                      <div className="mb-4 flex flex-wrap gap-2">
                        {PROVIDER_ORDER.map((providerId) => {
                          const info = PROVIDER_LABELS[providerId];
                          const hasModels = MODEL_CATALOG.some((model) => model.provider === providerId);
                          if (!info || !hasModels) return null;
                          const isActive = visibleProvider === providerId;
                          const hasKey = configuredProviders.has(providerId);

                          return (
                            <button
                              key={providerId}
                              type="button"
                              onClick={() => setSelectedProvider(providerId)}
                              className={`rounded-xl border px-3 py-2 text-left transition-all ${
                                isActive
                                  ? `bg-gradient-to-br ${info.tone} ${info.color}`
                                  : "border-[rgba(79,70,51,0.15)] bg-surface text-on-surface/55 hover:text-on-surface"
                              }`}
                            >
                              <div className="flex items-center gap-2">
                                <span className={`h-2 w-2 rounded-full ${hasKey ? "bg-[#6ee7b7]" : "bg-on-surface/20"}`} />
                                <span className="text-[11px] font-semibold uppercase tracking-[0.18em]">{info.name}</span>
                              </div>
                              <p className="mt-1 text-[10px] text-on-surface/40">{hasKey ? "Configurado" : "Sin API key"}</p>
                            </button>
                          );
                        })}
                      </div>

                      <div className="grid gap-3 lg:grid-cols-2">
                        {visibleModels.map((model) => {
                          const isSelected = defaultModel === model.id;
                          const providerInfo = PROVIDER_LABELS[visibleProvider];
                          const hasKey = configuredProviders.has(visibleProvider);

                          return (
                            <label
                              key={model.id}
                              className={`group flex min-h-[10.5rem] cursor-pointer flex-col rounded-[1.25rem] border p-4 transition-all ${
                                isSelected
                                  ? "border-primary/30 bg-primary/10 shadow-[0_10px_30px_rgba(201,169,97,0.08)]"
                                  : "border-[rgba(79,70,51,0.15)] bg-surface hover:border-primary/20 hover:bg-surface-container"
                              } ${!hasKey ? "opacity-35 cursor-not-allowed" : ""}`}
                            >
                              <input
                                type="radio"
                                name="defaultModel"
                                value={model.id}
                                checked={isSelected}
                                disabled={!hasKey}
                                onChange={(e) => setDefaultModel(e.target.value)}
                                className="sr-only"
                              />
                              <div className="flex items-start justify-between gap-3">
                                <div>
                                  <p className={`text-[10px] font-semibold uppercase tracking-[0.18em] ${providerInfo?.color || "text-primary"}`}>{providerInfo?.name}</p>
                                  <h3 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-on-surface">{model.name}</h3>
                                </div>
                                <div className={`flex h-5 w-5 items-center justify-center rounded-full border-2 ${isSelected ? "border-primary" : "border-on-surface/20"}`}>
                                  {isSelected && <div className="h-2 w-2 rounded-full bg-primary" />}
                                </div>
                              </div>
                              <p className="mt-3 line-clamp-2 text-sm leading-6 text-on-surface/55">{model.description}</p>
                              <div className="mt-auto flex items-center justify-between gap-3 pt-4">
                                <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.16em] ${tierBadgeStyles[model.tier] || "bg-surface-container text-on-surface/55"}`}>
                                  {tierBadgeLabels[model.tier] || model.tier}
                                </span>
                                <span className="text-[11px] text-on-surface/38">{hasKey ? "Listo para usar" : "Conectá una API key"}</span>
                              </div>
                            </label>
                          );
                        })}
                      </div>
                    </SectionCard>

                    <SectionCard className="flex h-full flex-col bg-[radial-gradient(circle_at_top,rgba(201,169,97,0.10),transparent_38%),linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0))]">
                      <SectionHeader
                        icon={<Brain className="w-4 h-4" />}
                        title="Tu configuración actual"
                        description="Un resumen corto para que tomes la decisión y guardes sin salir de la escena." 
                      />

                      <form onSubmit={handleSavePreferences} className="flex h-full flex-col gap-4">
                        <div className="rounded-2xl border border-[rgba(79,70,51,0.15)] bg-surface px-4 py-4">
                          <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/40">Modelo elegido</p>
                          <p className="mt-2 text-lg font-semibold text-on-surface">{selectedModelMeta?.name || "Sin selección"}</p>
                          <p className="mt-1 text-sm text-on-surface/50">{PROVIDER_LABELS[selectedModelMeta?.provider || visibleProvider]?.name || "Proveedor"}</p>
                        </div>

                        <div>
                          <label className={labelClassName}>Área legal predeterminada</label>
                          <select
                            value={defaultArea}
                            onChange={(e) => setDefaultArea(e.target.value)}
                            className={inputClassName}
                          >
                            {LEGAL_AREAS.map((a) => (
                              <option key={a.id} value={a.id}>{a.name}</option>
                            ))}
                          </select>
                          <p className="mt-1 text-[10px] text-on-surface/30">Las consultas nuevas se abrirán con esta orientación por defecto.</p>
                        </div>

                        <div className="rounded-xl border border-[rgba(79,70,51,0.15)] bg-surface px-3 py-3">
                          <div className="flex items-center gap-3">
                            <div className="h-4 w-4 rounded-full border border-[rgba(79,70,51,0.15)] bg-[#0e0e14]" />
                            <div>
                              <p className="text-sm font-medium text-on-surface">Tema activo</p>
                              <p className="text-[11px] text-on-surface/40">Modo oscuro permanente</p>
                            </div>
                          </div>
                        </div>

                        <div className="rounded-xl border border-dashed border-[rgba(79,70,51,0.15)] px-3 py-3 text-sm leading-6 text-on-surface/50">
                          {configuredProviders.has(visibleProvider)
                            ? "Tu proveedor seleccionado ya tiene credenciales activas. Solo te falta confirmar la combinación que querés usar por defecto."
                            : "Este proveedor todavía no tiene API key conectada. Podés configurarla desde la pestaña API Keys."}
                        </div>

                        <div className="mt-auto flex items-center justify-between gap-3 pt-2">
                          <div className="text-xs text-on-surface/35">Se guarda en tu sesión y futuras consultas.</div>
                          <button
                            type="submit"
                            className="bg-gradient-to-br from-primary to-primary-container text-on-primary rounded-lg px-5 py-2.5 text-sm font-bold flex items-center gap-2 transition-opacity"
                          >
                            <Save className="w-3.5 h-3.5" />
                            Guardar preferencias
                          </button>
                        </div>
                      </form>
                    </SectionCard>
                  </div>
                )}

                {/* --- MEMORIA TAB --- */}
                {activeTab === "memoria" && (
                  <div className="space-y-4">
                    <SectionCard className="py-4 sm:py-5">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <h2 className="font-['Newsreader'] text-lg font-bold text-on-surface flex items-center gap-2 mb-1">
                            <Brain className="w-4 h-4 text-primary" />
                            Memoria de Contexto
                          </h2>
                          <p className="text-xs text-on-surface/40 max-w-md">
                            TukiJuris recordara informacion relevante sobre vos entre conversaciones
                            para dar respuestas mas personalizadas.
                          </p>
                        </div>
                        <button
                          onClick={() => setMemoryEnabled(!memoryEnabled)}
                          className={`shrink-0 w-10 h-6 rounded-full transition-colors relative ${
                            memoryEnabled ? "bg-primary-container" : "bg-[#35343a]"
                          }`}
                        >
                          <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform shadow ${
                            memoryEnabled ? "translate-x-4" : "translate-x-0.5"
                          }`} />
                        </button>
                      </div>

                      {memoriesData && (
                        <div className="mt-4 flex items-center gap-4 text-xs text-on-surface/40">
                          <span>{memoriesData.active_count} memorias activas</span>
                          <span className="text-on-surface/10">•</span>
                          <span>{memoriesData.total} memorias en total</span>
                        </div>
                      )}
                    </SectionCard>

                    <DisclosureCard
                      icon={<Brain className="w-4 h-4" />}
                      title="Memorias guardadas"
                      description="Abrí este bloque para revisar y depurar lo que el sistema recuerda."
                      open={isMemoryListOpen}
                      onToggle={() => setIsMemoryListOpen((prev) => !prev)}
                    >

                      {loadingMemories ? (
                        <div className="flex items-center justify-center py-10 gap-2">
                          <Loader2 className="w-5 h-5 text-primary animate-spin" />
                          <span className="text-sm text-on-surface/40">Cargando memorias...</span>
                        </div>
                      ) : !memoriesData || memoriesData.total === 0 ? (
                        <div className="flex flex-col items-center justify-center py-10 text-center border border-dashed border-[rgba(79,70,51,0.15)] rounded-lg">
                          <Brain className="w-10 h-10 text-on-surface/10 mb-3" />
                          <p className="text-sm font-medium text-on-surface/40 mb-1">
                            Sin memorias todavia
                          </p>
                          <p className="text-xs text-on-surface/25 max-w-xs">
                            TukiJuris aprendera sobre vos a medida que uses la plataforma.
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-5">
                          {memoriesData.groups.map((group) => (
                            <div key={group.category}>
                              <div className="flex items-center gap-2 mb-2">
                                <span
                                  className={`text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded ${
                                    CATEGORY_COLORS[group.category] || "bg-[#35343a] text-on-surface/60"
                                  }`}
                                >
                                  {group.label}
                                </span>
                              </div>
                              <div className="space-y-px">
                                {group.memories.map((memory, idx) => (
                                  <div
                                    key={memory.id}
                                    className={`flex items-center gap-3 px-3 py-2.5 transition-colors ${
                                      idx % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                                    } ${!memory.is_active ? "opacity-40" : ""}`}
                                  >
                                    <span className="flex-1 text-sm text-on-surface truncate">
                                      {memory.content}
                                    </span>
                                    <div className="flex items-center gap-1 shrink-0">
                                      <button
                                        onClick={() => handleToggleMemory(memory.id, !memory.is_active)}
                                        title={memory.is_active ? "Desactivar" : "Activar"}
                                        className="p-1.5 rounded-lg text-on-surface/30 hover:text-on-surface hover:bg-[#35343a] transition-colors"
                                      >
                                        <Eye className="w-3.5 h-3.5" />
                                      </button>
                                      <button
                                        onClick={() => handleDeleteMemory(memory.id)}
                                        title="Eliminar"
                                        className="p-1.5 rounded-lg text-on-surface/30 hover:text-[#ffb4ab] hover:bg-[#93000a]/20 transition-colors"
                                      >
                                        <Trash2 className="w-3.5 h-3.5" />
                                      </button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </DisclosureCard>

                    {memoriesData && memoriesData.total > 0 && (
                      <DisclosureCard
                        icon={<AlertTriangle className="w-4 h-4 text-[#ffb4ab]" />}
                        title="Zona de peligro"
                        description="Borrado total de memoria personal almacenada."
                        open={isMemoryDangerOpen}
                        onToggle={() => setIsMemoryDangerOpen((prev) => !prev)}
                        tone="danger"
                      >
                        <button
                          onClick={handleClearAllMemories}
                          disabled={clearingMemories}
                          className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-[#ffb4ab]/30 text-[#ffb4ab] hover:bg-[#93000a]/20 disabled:opacity-50 text-sm transition-colors"
                        >
                          {clearingMemories ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="w-3.5 h-3.5" />
                          )}
                          Borrar toda la memoria
                        </button>
                      </DisclosureCard>
                    )}
                  </div>
                )}

                {/* --- API KEYS TAB --- */}
                {activeTab === "apikeys" && (
                  <FeatureGate
                    feature="byok_enabled"
                    fallback={
                      <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
                        <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10">
                          <Lock className="w-6 h-6 text-primary" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold text-on-surface mb-1">
                            BYOK disponible en planes de pago
                          </p>
                          <p className="text-xs text-[#7c7885] max-w-xs">
                            Conectá tu propia API key con el plan Profesional o Estudio.
                          </p>
                        </div>
                        <a
                          href="/billing"
                          className="mt-2 px-4 py-2 rounded-lg bg-primary/10 text-primary text-xs font-bold hover:bg-primary/20 transition-colors"
                        >
                          Ver planes
                        </a>
                      </div>
                    }
                  >
                  <div className="space-y-4">
                    <DisclosureCard
                      icon={<Key className="w-4 h-4" />}
                      title="Conecta tu Inteligencia Artificial"
                      description="Resumen de proveedores y estado actual de tus claves."
                      open={isApiOverviewOpen}
                      onToggle={() => setIsApiOverviewOpen((prev) => !prev)}
                    >
                      <p className="text-xs text-on-surface/40 leading-relaxed -mt-2">
                        TukiJuris te permite elegir y conectar tu propio proveedor de IA. Solo necesitas
                        una clave API de al menos un proveedor para empezar a consultar. El consumo de tokens
                        se cobra directamente por el proveedor que elijas, no por TukiJuris.
                      </p>
                      <div className="flex items-center gap-3 pt-1">
                        {(() => {
                          const activeCount = llmKeys.length;
                          const providerCount = new Set(llmKeys.map(k => k.provider)).size;
                          if (activeCount === 0) return (
                            <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                              <span>No tienes claves configuradas. Agrega al menos una para usar la plataforma.</span>
                            </div>
                          );
                          return (
                            <div className="flex items-center gap-2 text-xs text-[#6ee7b7] bg-[#1a3a2a]/60 border border-[#6ee7b7]/20 rounded-lg px-3 py-2">
                              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                              <span>{activeCount} {activeCount === 1 ? "clave activa" : "claves activas"} en {providerCount} {providerCount === 1 ? "proveedor" : "proveedores"}</span>
                            </div>
                          );
                        })()}
                      </div>
                    </DisclosureCard>

                    {loadingLlmKeys ? (
                      <div className="flex items-center justify-center py-10 gap-2">
                        <Loader2 className="w-5 h-5 text-primary animate-spin" />
                        <span className="text-sm text-on-surface/40">Cargando claves...</span>
                      </div>
                    ) : (
                       <div className="space-y-3">
                         {LLM_PROVIDERS.map((provider) => {
                           const providerKeys = llmKeys.filter((k) => k.provider === provider.id);
                           const isAdding = addingProvider === provider.id;
                           const isActive = providerKeys.length > 0;
                           const isExpanded = expandedProviderId === provider.id;

                           return (
                             <div
                              key={provider.id}
                              className={`panel-base border rounded-[1.35rem] overflow-hidden transition-colors ${
                                isActive ? `${provider.accentBorder}` : "border-[rgba(79,70,51,0.15)]"
                              }`}
                            >
                               <div className="flex items-start justify-between gap-3 px-5 py-4">
                                <button
                                  type="button"
                                  onClick={() => setExpandedProviderId((prev) => (prev === provider.id ? null : provider.id))}
                                  className="flex flex-1 items-start gap-3 text-left"
                                  aria-expanded={isExpanded}
                                >
                                  <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className={`w-2 h-2 rounded-full shrink-0 ${isActive ? "bg-[#6ee7b7]" : "bg-[#35343a]"}`} />
                                    <span className={`text-sm font-bold ${isActive ? provider.accent : "text-on-surface"}`}>
                                      {provider.name}
                                    </span>
                                    {provider.recommended && (
                                      <span className="text-[9px] uppercase tracking-widest font-bold bg-primary/15 text-primary px-1.5 py-0.5 rounded">
                                        Recomendado
                                      </span>
                                    )}
                                    {isActive && (
                                      <span className="text-[9px] uppercase tracking-widest font-bold bg-[#1a3a2a] text-[#6ee7b7] px-1.5 py-0.5 rounded">
                                        Activo
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-[11px] text-on-surface/40 leading-relaxed">{provider.description}</p>
                                  <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                                    {provider.models.map((m) => (
                                      <span key={m} className="text-[10px] text-on-surface/40 bg-surface px-2 py-0.5 rounded">{m}</span>
                                    ))}
                                  </div>
                                </div>
                                </button>
                                  <a
                                     href={provider.docsUrl}
                                     target="_blank"
                                     rel="noopener noreferrer"
                                     className="text-[10px] text-on-surface/30 hover:text-on-surface flex items-center gap-1 shrink-0 transition-colors"
                                  >
                                     <ExternalLink className="w-3 h-3" />
                                     Obtener clave
                                  </a>
                               </div>

                               {isExpanded && provider.note && (
                                 <div className="mx-5 mb-3 flex items-start gap-2 text-[11px] text-blue-300/80 bg-blue-500/5 border border-blue-500/10 rounded-lg px-3 py-2">
                                    <Shield className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                                    <span>{provider.note}</span>
                                 </div>
                               )}

                               {isExpanded && providerKeys.length > 0 && (
                                 <div className="border-t border-[rgba(79,70,51,0.15)]">
                                  {providerKeys.map((key) => (
                                    <div key={key.id} className="flex items-center gap-3 px-5 py-3 border-b border-[rgba(79,70,51,0.08)] last:border-0">
                                      <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                                        testResults[provider.id]?.ok === true ? "bg-[#6ee7b7]" :
                                        testResults[provider.id]?.ok === false ? "bg-[#ffb4ab]" :
                                        "bg-[#6ee7b7]"
                                      }`} />
                                      <div className="flex-1 min-w-0">
                                        <span className="text-xs font-mono text-on-surface">{key.hint}</span>
                                        {key.label && (
                                          <span className="text-xs text-on-surface/30 ml-2">&mdash; {key.label}</span>
                                        )}
                                      </div>
                                      <button
                                        onClick={() => handleTestKey(provider.id)}
                                        disabled={testingProvider === provider.id}
                                        className="flex items-center gap-1 text-xs text-blue-400/70 hover:text-blue-400 hover:bg-blue-400/10 px-2 py-1 rounded-lg transition-colors disabled:opacity-50"
                                      >
                                        {testingProvider === provider.id ? (
                                          <Loader2 className="w-3 h-3 animate-spin" />
                                        ) : (
                                          <BadgeCheck className="w-3 h-3" />
                                        )}
                                        Probar
                                      </button>
                                      <button
                                        onClick={() => handleDeleteKey(key.id)}
                                        disabled={deletingKeyId === key.id}
                                        className="flex items-center gap-1 text-xs text-[#ffb4ab]/60 hover:text-[#ffb4ab] hover:bg-[#93000a]/20 px-2 py-1 rounded-lg transition-colors disabled:opacity-50"
                                      >
                                        {deletingKeyId === key.id ? (
                                          <Loader2 className="w-3 h-3 animate-spin" />
                                        ) : (
                                          <Trash2 className="w-3 h-3" />
                                        )}
                                        Eliminar
                                      </button>
                                    </div>
                                  ))}
                                  {testResults[provider.id] && (
                                    <div className={`px-5 py-2 text-xs flex items-center gap-2 ${
                                      testResults[provider.id].ok
                                        ? "bg-[#1a3a2a]/60 text-[#6ee7b7]"
                                        : "bg-[#93000a]/20 text-[#ffb4ab]"
                                    }`}>
                                      {testResults[provider.id].ok ? (
                                        <>
                                          <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                                          <span>Conexión exitosa — {testResults[provider.id].latency_ms}ms</span>
                                        </>
                                      ) : (
                                        <>
                                          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                                          <span className="truncate">{testResults[provider.id].error}</span>
                                        </>
                                      )}
                                    </div>
                                  )}
                                </div>
                               )}

                               {isExpanded && !isAdding && (
                                 <div className={`px-5 py-3 flex items-center justify-between ${providerKeys.length > 0 ? "border-t border-[rgba(79,70,51,0.15)]" : ""}`}>
                                  {providerKeys.length === 0 && (
                                    <span className="text-xs text-on-surface/20">Sin clave configurada</span>
                                  )}
                                  <button
                                    onClick={() => {
                                      setAddingProvider(provider.id);
                                      setNewApiKey("");
                                      setNewApiLabel("");
                                      setShowApiKey(false);
                                    }}
                                    className={`ml-auto flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors ${provider.accentBorder} ${provider.accentBg} ${provider.accent}`}
                                  >
                                    <Plus className="w-3 h-3" />
                                    {providerKeys.length > 0 ? "Agregar otra clave" : "Agregar clave"}
                                  </button>
                                </div>
                               )}

                               {isExpanded && isAdding && (
                                 <div className="px-5 py-4 space-y-3 border-t border-[rgba(79,70,51,0.15)]">
                                  <div>
                                    <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">
                                      API Key <span className="text-[#ffb4ab]">*</span>
                                    </label>
                                    <div className="relative">
                                      <input
                                        type={showApiKey ? "text" : "password"}
                                        value={newApiKey}
                                        onChange={(e) => setNewApiKey(e.target.value)}
                                        placeholder="sk-... / sk-ant-... / AIza..."
                                        autoFocus
                                        className={`${inputClassName} pr-10 font-mono placeholder-on-surface/20`}
                                      />
                                      <button
                                        type="button"
                                        onClick={() => setShowApiKey(!showApiKey)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface/30 hover:text-on-surface transition-colors"
                                      >
                                        {showApiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                                      </button>
                                    </div>
                                  </div>
                                  <div>
                                    <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">
                                      Etiqueta <span className="text-on-surface/20">(opcional)</span>
                                    </label>
                                    <input
                                      type="text"
                                      value={newApiLabel}
                                      onChange={(e) => setNewApiLabel(e.target.value)}
                                      placeholder="Ej: Cuenta personal, Estudio jurídico..."
                                        className={`${inputClassName} placeholder-on-surface/20`}
                                      />
                                  </div>
                                  <div className="flex items-center gap-2 justify-end pt-1">
                                    <button
                                      onClick={() => {
                                        setAddingProvider(null);
                                        setNewApiKey("");
                                        setNewApiLabel("");
                                      }}
                                      className="px-3 py-1.5 text-xs text-on-surface/60 hover:text-on-surface border border-[rgba(79,70,51,0.15)] rounded-lg transition-colors"
                                    >
                                      Cancelar
                                    </button>
                                    <button
                                      onClick={() => handleAddKey(provider.id)}
                                      disabled={savingKey || !newApiKey.trim()}
                                      className="flex items-center gap-1.5 px-4 py-1.5 text-xs bg-gradient-to-br from-primary to-primary-container disabled:opacity-40 text-on-primary font-bold rounded-lg transition-opacity"
                                    >
                                      {savingKey ? (
                                        <Loader2 className="w-3 h-3 animate-spin" />
                                      ) : (
                                        <Save className="w-3 h-3" />
                                      )}
                                      Guardar clave
                                    </button>
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}

                    <SectionCard className="space-y-4">
                      <div className="flex items-start gap-2.5">
                        <Lock className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                        <div className="space-y-1">
                          <p className="text-xs text-on-surface font-bold">Seguridad de tus claves</p>
                          <p className="text-[11px] text-on-surface/40 leading-relaxed">
                            Todas las claves se almacenan cifradas con encriptacion AES-256. Nunca se muestran completas
                            despues de guardarlas. Solo vos podes usarlas a traves de TukiJuris.
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5">
                        <Shield className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                        <div className="space-y-1">
                          <p className="text-xs text-on-surface font-bold">Tu consumo, tu control</p>
                          <p className="text-[11px] text-on-surface/40 leading-relaxed">
                            Cada proveedor cobra directamente a tu cuenta por los tokens usados. TukiJuris no tiene
                            acceso a tu facturacion ni agrega recargos sobre el consumo de IA.
                          </p>
                        </div>
                      </div>
                    </SectionCard>
                  </div>
                  </FeatureGate>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
