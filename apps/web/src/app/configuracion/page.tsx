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
  BookOpen,
  Shield,
  Briefcase,
  Landmark,
  Gavel,
  ScrollText,
  FileCheck,
  Globe,
  BadgeCheck,
  Brain,
  Trash2,
  ToggleLeft,
  ToggleRight,
  Plus,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { getToken, logout } from "@/lib/auth";
import { AppLayout } from "@/components/AppLayout";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UserProfile {
  id: string;
  email: string;
  name?: string;
  is_admin?: boolean;
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

const MODELS = [
  // --- Gratis / Ultra económicos ---
  { id: "gemini/gemini-2.0-flash", name: "⚡ Gemini 2.0 Flash (gratis)", group: "Gratis" },
  { id: "deepseek/deepseek-chat", name: "⚡ DeepSeek V3 (ultra barato)", group: "Gratis" },
  { id: "groq/llama-3.1-8b-instant", name: "⚡ Llama 3.1 8B — Groq (gratis)", group: "Gratis" },
  { id: "groq/llama-3.3-70b-versatile", name: "⚡ Llama 3.3 70B — Groq (rápido)", group: "Gratis" },
  // --- Estándar ---
  { id: "gpt-4o-mini", name: "GPT-4o Mini (rápido)", group: "Estándar" },
  { id: "claude-3-5-haiku-20241022", name: "Claude 3.5 Haiku (rápido)", group: "Estándar" },
  { id: "deepseek/deepseek-reasoner", name: "DeepSeek Reasoner (análisis)", group: "Estándar" },
  { id: "groq/qwen-qwq-32b", name: "Qwen QwQ 32B — Groq (potente)", group: "Estándar" },
  // --- Avanzados ---
  { id: "gpt-4o", name: "GPT-4o (avanzado)", group: "Avanzado" },
  { id: "claude-sonnet-4-20250514", name: "Claude Sonnet 4 (avanzado)", group: "Avanzado" },
  { id: "gemini/gemini-2.5-pro", name: "Gemini 2.5 Pro (contexto largo)", group: "Avanzado" },
  { id: "groq/moonshotai/kimi-k2-instruct", name: "Kimi K2 — Groq (avanzado)", group: "Avanzado" },
];

type ActiveTab = "perfil" | "organizacion" | "preferencias" | "apikeys" | "memoria";

const TABS: { id: ActiveTab; label: string; icon: React.ElementType }[] = [
  { id: "perfil", label: "Perfil", icon: User },
  { id: "organizacion", label: "Organizacion", icon: Building2 },
  { id: "preferencias", label: "Preferencias", icon: Sliders },
  { id: "memoria", label: "Memoria", icon: Brain },
  { id: "apikeys", label: "API Keys", icon: Key },
];

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
  profession: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  interests: "bg-green-500/10 text-green-400 border-green-500/20",
  cases: "bg-[#EAB308]/10 text-[#EAB308] border-[#EAB308]/20",
  preferences: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  context: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
};

// LLM Key types
interface LLMKey {
  id: string;
  provider: string;
  label?: string;
  hint: string; // e.g. "sk-...3kF2"
  created_at?: string;
}

interface LLMProvider {
  id: string;
  name: string;
  accent: string;
  accentBg: string;
  accentBorder: string;
  docsUrl: string;
  docsLabel: string;
  models: string[];
}

const LLM_PROVIDERS: LLMProvider[] = [
  {
    id: "google",
    name: "Google AI (Gemini)",
    accent: "text-blue-400",
    accentBg: "bg-blue-500/10",
    accentBorder: "border-blue-500/30",
    docsUrl: "https://aistudio.google.com/apikey",
    docsLabel: "aistudio.google.com/apikey",
    models: ["gemini-2.0-flash (gratis)", "gemini-2.5-pro"],
  },
  {
    id: "groq",
    name: "Groq (Ultra Rápido)",
    accent: "text-orange-400",
    accentBg: "bg-orange-500/10",
    accentBorder: "border-orange-500/30",
    docsUrl: "https://console.groq.com/keys",
    docsLabel: "console.groq.com/keys",
    models: ["Llama 3.1/3.3", "Qwen QwQ", "Kimi K2"],
  },
  {
    id: "deepseek",
    name: "DeepSeek",
    accent: "text-cyan-400",
    accentBg: "bg-cyan-500/10",
    accentBorder: "border-cyan-500/30",
    docsUrl: "https://platform.deepseek.com/api_keys",
    docsLabel: "platform.deepseek.com",
    models: ["deepseek-chat", "deepseek-reasoner"],
  },
  {
    id: "openai",
    name: "OpenAI",
    accent: "text-green-400",
    accentBg: "bg-green-500/10",
    accentBorder: "border-green-500/30",
    docsUrl: "https://platform.openai.com/api-keys",
    docsLabel: "platform.openai.com/api-keys",
    models: ["GPT-4o", "GPT-4o-mini"],
  },
  {
    id: "anthropic",
    name: "Anthropic (Claude)",
    accent: "text-amber-400",
    accentBg: "bg-amber-500/10",
    accentBorder: "border-amber-500/30",
    docsUrl: "https://console.anthropic.com/settings/keys",
    docsLabel: "console.anthropic.com",
    models: ["Claude Sonnet 4", "Claude 3.5 Haiku"],
  },
  {
    id: "moonshot",
    name: "Moonshot AI (Kimi)",
    accent: "text-violet-400",
    accentBg: "bg-violet-500/10",
    accentBorder: "border-violet-500/30",
    docsUrl: "https://platform.moonshot.cn/console/api-keys",
    docsLabel: "platform.moonshot.cn",
    models: ["moonshot-v1-8k", "moonshot-v1-32k"],
  },
  {
    id: "qwen",
    name: "Qwen (Alibaba)",
    accent: "text-indigo-400",
    accentBg: "bg-indigo-500/10",
    accentBorder: "border-indigo-500/30",
    docsUrl: "https://dashscope.console.aliyun.com/apiKey",
    docsLabel: "dashscope.aliyun.com",
    models: ["qwen-turbo", "qwen-plus", "qwen-max"],
  },
  {
    id: "zhipu",
    name: "Zhipu AI (GLM)",
    accent: "text-rose-400",
    accentBg: "bg-rose-500/10",
    accentBorder: "border-rose-500/30",
    docsUrl: "https://open.bigmodel.cn/usercenter/apikeys",
    docsLabel: "open.bigmodel.cn",
    models: ["GLM-4 Plus", "GLM-4 Flash"],
  },
];

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

  // Org fields
  const [orgName, setOrgName] = useState("");
  const [savingOrg, setSavingOrg] = useState(false);

  // Memory fields
  const [memoriesData, setMemoriesData] = useState<MemoriesData | null>(null);
  const [loadingMemories, setLoadingMemories] = useState(false);
  const [clearingMemories, setClearingMemories] = useState(false);
  const [memoryEnabled, setMemoryEnabled] = useState(true);

  // Preferences (stored in localStorage)
  const [defaultModel, setDefaultModel] = useState(MODELS[0].id);
  const [defaultArea, setDefaultArea] = useState("");

  // LLM Keys state
  const [llmKeys, setLlmKeys] = useState<LLMKey[]>([]);
  const [loadingLlmKeys, setLoadingLlmKeys] = useState(false);
  const [addingProvider, setAddingProvider] = useState<string | null>(null);
  const [newApiKey, setNewApiKey] = useState("");
  const [newApiLabel, setNewApiLabel] = useState("");
  const [savingKey, setSavingKey] = useState(false);
  const [deletingKeyId, setDeletingKeyId] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);

  const authHeaders = () => ({
    "Content-Type": "application/json",
    Authorization: "Bearer " + getToken(),
  });

  const showSuccess = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(""), 3000);
  };

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [meRes, orgRes] = await Promise.allSettled([
        fetch(`${API_URL}/api/auth/me`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/organizations/`, { headers: authHeaders() }),
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

      // Load preferences from localStorage
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // NOTE: tab-specific data loading moved after loadMemories/loadLlmKeys declarations (see below)

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    setSavingProfile(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/auth/me`, {
        method: "PUT",
        headers: authHeaders(),
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
      setError("Las contrasenas no coinciden");
      return;
    }
    if (newPassword.length < 8) {
      setError("La contrasena debe tener al menos 8 caracteres");
      return;
    }
    setSavingPassword(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/auth/change-password`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || "No se pudo cambiar la contrasena");
      }
      showSuccess("Contrasena actualizada correctamente");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cambiar contrasena");
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
      const res = await fetch(`${API_URL}/api/organizations/${org.id}`, {
        method: "PUT",
        headers: authHeaders(),
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
      const res = await fetch(`${API_URL}/api/memory/`, { headers: authHeaders() });
      if (res.ok) {
        const data: MemoriesData = await res.json();
        setMemoriesData(data);
      }
    } catch {
      // fail silently — memory is non-critical
    } finally {
      setLoadingMemories(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleToggleMemory = async (memoryId: string, isActive: boolean) => {
    try {
      const res = await fetch(`${API_URL}/api/memory/${memoryId}/toggle`, {
        method: "PUT",
        headers: authHeaders(),
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
      const res = await fetch(`${API_URL}/api/memory/${memoryId}`, {
        method: "DELETE",
        headers: authHeaders(),
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
      const res = await fetch(`${API_URL}/api/keys/llm-keys`, { headers: authHeaders() });
      if (res.ok) {
        const data = await res.json();
        setLlmKeys(Array.isArray(data) ? data : data.keys || []);
      }
    } catch {
      // fail silently
    } finally {
      setLoadingLlmKeys(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load tab-specific data (MUST be after loadMemories and loadLlmKeys declarations)
  useEffect(() => {
    if (activeTab === "memoria") {
      loadMemories();
    }
    if (activeTab === "apikeys") {
      loadLlmKeys();
    }
  }, [activeTab, loadMemories, loadLlmKeys]);

  const handleAddKey = async (providerId: string) => {
    if (!newApiKey.trim()) return;
    setSavingKey(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/keys/llm-keys`, {
        method: "POST",
        headers: authHeaders(),
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
      const res = await fetch(`${API_URL}/api/keys/llm-keys/${keyId}`, {
        method: "DELETE",
        headers: authHeaders(),
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

  const handleClearAllMemories = async () => {
    if (!confirm("Borrar TODA la memoria de contexto? Esta accion es irreversible.")) return;
    setClearingMemories(true);
    try {
      const res = await fetch(`${API_URL}/api/memory/`, {
        method: "DELETE",
        headers: authHeaders(),
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
    logout();
  };

  return (
    <AppLayout>
      <div className="min-h-full text-[#F5F5F5]">
        <div className="border-b border-[#1E1E2A] px-4 lg:px-6 py-4 flex items-center gap-3">
          <Settings className="w-5 h-5 text-[#EAB308]" />
          <h1 className="font-bold text-base">Configuración</h1>
        </div>

        <div className="max-w-5xl mx-auto px-4 lg:px-6 py-6 sm:py-8">
        {/* Alerts */}
        {error && (
          <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl px-4 py-3 mb-6 text-sm">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {successMsg && (
          <div className="flex items-center gap-3 bg-[#34D399]/10 border border-[#34D399]/30 text-[#34D399] rounded-xl px-4 py-3 mb-6 text-sm">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-3">
            <Loader2 className="w-8 h-8 text-[#EAB308] animate-spin" />
            <p className="text-sm text-[#6B7280]">Cargando configuracion...</p>
          </div>
        ) : (
          <div className="flex flex-col lg:flex-row gap-4 sm:gap-6">
            {/* Tabs — horizontal scrollable on mobile, vertical sidebar on desktop */}
            <aside className="lg:w-52 shrink-0">
              {/* Mobile: horizontal scroll tabs */}
              <div className="lg:hidden overflow-x-auto">
                <div className="flex gap-1 bg-[#111116] border border-[#1E1E2A] rounded-xl p-1 min-w-max">
                  {TABS.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => {
                          setActiveTab(tab.id);
                          setError("");
                        }}
                        className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors whitespace-nowrap ${
                          activeTab === tab.id
                            ? "bg-[#EAB308]/10 text-[#EAB308]"
                            : "text-[#9CA3AF] hover:bg-[#1A1A22] hover:text-[#F5F5F5]"
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                        {tab.label}
                      </button>
                    );
                  })}
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm text-red-400/70 hover:text-red-400 transition-colors whitespace-nowrap"
                  >
                    <LogOut className="w-4 h-4" />
                    Salir
                  </button>
                </div>
              </div>

              {/* Desktop: vertical sidebar */}
              <nav className="hidden lg:block bg-[#111116] border border-[#1E1E2A] rounded-xl overflow-hidden">
                {TABS.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => {
                        setActiveTab(tab.id);
                        setError("");
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors border-b border-[#1E1E2A] last:border-0 ${
                        activeTab === tab.id
                          ? "bg-[#EAB308]/10 text-[#EAB308]"
                          : "text-[#9CA3AF] hover:bg-[#1A1A22] hover:text-[#F5F5F5]"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      {tab.label}
                    </button>
                  );
                })}

                {/* Logout */}
                <div className="border-t border-[#1E1E2A]">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-400/70 hover:text-red-400 hover:bg-red-400/10 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Cerrar sesion
                  </button>
                </div>
              </nav>
            </aside>

            {/* Tab Content */}
            <div className="flex-1 min-w-0">
              {/* --- PERFIL TAB --- */}
              {activeTab === "perfil" && (
                <div className="space-y-5">
                  {/* Profile info */}
                  <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-6">
                    <h2 className="font-semibold text-sm mb-5 flex items-center gap-2">
                      <User className="w-4 h-4 text-[#EAB308]" />
                      Informacion del perfil
                    </h2>
                    <form onSubmit={handleSaveProfile} className="space-y-4">
                      <div>
                        <label className="block text-xs font-medium text-[#9CA3AF] mb-1.5">
                          Correo electronico
                        </label>
                        <input
                          type="email"
                          value={profile?.email || ""}
                          readOnly
                          className="w-full bg-[#1A1A22]/50 border border-[#2A2A35] rounded-xl px-3 py-2.5 text-sm text-[#6B7280] cursor-not-allowed"
                        />
                        <p className="text-[10px] text-[#6B7280] mt-1">El email no puede ser modificado</p>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-[#9CA3AF] mb-1.5">
                          Nombre
                        </label>
                        <input
                          type="text"
                          value={profileName}
                          onChange={(e) => setProfileName(e.target.value)}
                          placeholder="Tu nombre completo"
                          className="w-full bg-[#111116] border border-[#2A2A35] rounded-xl px-3 py-2.5 text-sm text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-1 focus:ring-[#EAB308]/25"
                        />
                      </div>
                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={savingProfile}
                          className="bg-[#EAB308] hover:bg-[#ca9a07] disabled:bg-[#2A2A35] disabled:text-[#6B7280] text-[#0A0A0F] rounded-xl px-4 py-2 text-sm font-medium flex items-center gap-2 transition-colors"
                        >
                          {savingProfile ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                          Guardar cambios
                        </button>
                      </div>
                    </form>
                  </div>

                  {/* Change Password */}
                  <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-6">
                    <h2 className="font-semibold text-sm mb-5 flex items-center gap-2">
                      <Lock className="w-4 h-4 text-[#EAB308]" />
                      Cambiar contrasena
                    </h2>
                    <form onSubmit={handleChangePassword} className="space-y-4">
                      <div>
                        <label className="block text-xs font-medium text-[#9CA3AF] mb-1.5">
                          Contrasena actual
                        </label>
                        <div className="relative">
                          <input
                            type={showCurrentPw ? "text" : "password"}
                            value={currentPassword}
                            onChange={(e) => setCurrentPassword(e.target.value)}
                            placeholder="••••••••"
                            className="w-full bg-[#111116] border border-[#2A2A35] rounded-xl px-3 py-2.5 pr-10 text-sm text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-1 focus:ring-[#EAB308]/25"
                            required
                          />
                          <button
                            type="button"
                            onClick={() => setShowCurrentPw(!showCurrentPw)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B7280] hover:text-[#F5F5F5]"
                          >
                            {showCurrentPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-[#9CA3AF] mb-1.5">
                          Nueva contrasena
                        </label>
                        <div className="relative">
                          <input
                            type={showNewPw ? "text" : "password"}
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            placeholder="Minimo 8 caracteres"
                            className="w-full bg-[#111116] border border-[#2A2A35] rounded-xl px-3 py-2.5 pr-10 text-sm text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-1 focus:ring-[#EAB308]/25"
                            required
                            minLength={8}
                          />
                          <button
                            type="button"
                            onClick={() => setShowNewPw(!showNewPw)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B7280] hover:text-[#F5F5F5]"
                          >
                            {showNewPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-[#9CA3AF] mb-1.5">
                          Confirmar nueva contrasena
                        </label>
                        <input
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          placeholder="Repite la nueva contrasena"
                          className="w-full bg-[#111116] border border-[#2A2A35] rounded-xl px-3 py-2.5 text-sm text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-1 focus:ring-[#EAB308]/25"
                          required
                        />
                      </div>
                      <div className="flex justify-end">
                        <button
                          type="submit"
                          disabled={savingPassword || !currentPassword || !newPassword || !confirmPassword}
                          className="bg-[#EAB308] hover:bg-[#ca9a07] disabled:bg-[#2A2A35] disabled:text-[#6B7280] text-[#0A0A0F] rounded-xl px-4 py-2 text-sm font-medium flex items-center gap-2 transition-colors"
                        >
                          {savingPassword ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Lock className="w-3.5 h-3.5" />}
                          Actualizar contrasena
                        </button>
                      </div>
                    </form>
                  </div>
                </div>
              )}

              {/* --- ORGANIZACION TAB --- */}
              {activeTab === "organizacion" && (
                <div className="space-y-5">
                  {org ? (
                    <>
                      {/* Org Settings */}
                      <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-6">
                        <h2 className="font-semibold text-sm mb-5 flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-[#EAB308]" />
                          Datos de la organizacion
                        </h2>
                        <form onSubmit={handleSaveOrg} className="space-y-4">
                          <div>
                            <label className="block text-xs font-medium text-[#9CA3AF] mb-1.5">
                              Nombre de la organizacion
                            </label>
                            <input
                              type="text"
                              value={orgName}
                              onChange={(e) => setOrgName(e.target.value)}
                              placeholder="Nombre de tu organizacion"
                              className="w-full bg-[#111116] border border-[#2A2A35] rounded-xl px-3 py-2.5 text-sm text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-1 focus:ring-[#EAB308]/25"
                              required
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-[#9CA3AF] mb-1.5">
                              Identificador (slug)
                            </label>
                            <input
                              type="text"
                              value={org.slug}
                              readOnly
                              className="w-full bg-[#1A1A22]/50 border border-[#2A2A35] rounded-xl px-3 py-2.5 text-sm text-[#6B7280] cursor-not-allowed"
                            />
                            <p className="text-[10px] text-[#6B7280] mt-1">El slug no puede ser modificado</p>
                          </div>
                          <div>
                            <label className="block text-xs font-medium text-[#9CA3AF] mb-1.5">Plan</label>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-[#F5F5F5] capitalize">{org.plan}</span>
                              <Link href="/billing" className="text-xs text-[#EAB308] hover:text-[#ca9a07]">
                                Cambiar plan
                              </Link>
                            </div>
                          </div>
                          <div className="flex justify-end">
                            <button
                              type="submit"
                              disabled={savingOrg || !orgName.trim()}
                              className="bg-[#EAB308] hover:bg-[#ca9a07] disabled:bg-[#2A2A35] disabled:text-[#6B7280] text-[#0A0A0F] rounded-xl px-4 py-2 text-sm font-medium flex items-center gap-2 transition-colors"
                            >
                              {savingOrg ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                              Guardar cambios
                            </button>
                          </div>
                        </form>
                      </div>

                      {/* Danger Zone */}
                      <div className="bg-[#F87171]/5 border border-[#F87171]/20 rounded-xl p-6">
                        <h2 className="font-semibold text-sm mb-2 flex items-center gap-2 text-red-400">
                          <AlertTriangle className="w-4 h-4" />
                          Zona de peligro
                        </h2>
                        <p className="text-xs text-[#6B7280] mb-4">
                          Estas acciones son irreversibles. Procede con cuidado.
                        </p>
                        <button
                          onClick={async () => {
                            if (!org || !profile) return;
                            if (!confirm("¿Estás seguro que querés abandonar esta organización? Esta acción no se puede deshacer.")) return;
                            try {
                              const res = await fetch(
                                `${API_URL}/api/organizations/${org.id}/members/${profile.id}`,
                                { method: "DELETE", headers: authHeaders() }
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
                          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-red-500/30 text-red-400 hover:bg-red-500/10 text-sm transition-colors"
                        >
                          <LogOut className="w-3.5 h-3.5" />
                          Abandonar organizacion
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-8 text-center">
                      <Building2 className="w-10 h-10 text-[#2A2A35] mx-auto mb-3" />
                      <p className="text-sm text-[#9CA3AF] mb-4">No perteneces a ninguna organizacion</p>
                      <Link
                        href="/organizacion"
                        className="inline-flex items-center gap-2 bg-[#EAB308] hover:bg-[#ca9a07] text-[#0A0A0F] rounded-xl px-4 py-2 text-sm font-medium transition-colors"
                      >
                        <Building2 className="w-4 h-4" />
                        Crear organizacion
                      </Link>
                    </div>
                  )}
                </div>
              )}

              {/* --- PREFERENCIAS TAB --- */}
              {activeTab === "preferencias" && (
                <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-6">
                  <h2 className="font-semibold text-sm mb-5 flex items-center gap-2">
                    <Sliders className="w-4 h-4 text-[#EAB308]" />
                    Preferencias de uso
                  </h2>
                  <form onSubmit={handleSavePreferences} className="space-y-5">
                    <div>
                      <label className="block text-xs font-medium text-[#9CA3AF] mb-1.5">
                        Modelo de IA predeterminado
                      </label>
                      <select
                        value={defaultModel}
                        onChange={(e) => setDefaultModel(e.target.value)}
                        className="w-full bg-[#111116] border border-[#2A2A35] rounded-xl px-3 py-2.5 text-sm text-[#F5F5F5] focus:outline-none focus:border-[#EAB308]"
                      >
                        {["Gratis", "Estándar", "Avanzado"].map((group) => (
                          <optgroup key={group} label={group}>
                            {MODELS.filter((m) => m.group === group).map((m) => (
                              <option key={m.id} value={m.id}>{m.name}</option>
                            ))}
                          </optgroup>
                        ))}
                      </select>
                      <p className="text-[10px] text-[#6B7280] mt-1">
                        El modelo se usara por defecto al iniciar una consulta
                      </p>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-[#9CA3AF] mb-1.5">
                        Area legal predeterminada
                      </label>
                      <select
                        value={defaultArea}
                        onChange={(e) => setDefaultArea(e.target.value)}
                        className="w-full bg-[#111116] border border-[#2A2A35] rounded-xl px-3 py-2.5 text-sm text-[#F5F5F5] focus:outline-none focus:border-[#EAB308]"
                      >
                        {LEGAL_AREAS.map((a) => (
                          <option key={a.id} value={a.id}>{a.name}</option>
                        ))}
                      </select>
                      <p className="text-[10px] text-[#6B7280] mt-1">
                        Las consultas se dirigiran a esta area por defecto
                      </p>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-[#9CA3AF] mb-1.5">
                        Tema de la interfaz
                      </label>
                      <div className="flex items-center gap-3 py-2.5 px-3 bg-[#111116] border border-[#2A2A35] rounded-xl">
                        <div className="w-4 h-4 rounded-full bg-[#0A0A0F] border border-[#2A2A35]" />
                        <span className="text-sm text-[#F5F5F5]">Modo oscuro</span>
                        <span className="ml-auto text-[10px] text-[#6B7280]">Siempre activo</span>
                      </div>
                    </div>

                    <div className="flex justify-end pt-2">
                      <button
                        type="submit"
                        className="bg-[#EAB308] hover:bg-[#ca9a07] text-[#0A0A0F] rounded-xl px-4 py-2 text-sm font-medium flex items-center gap-2 transition-colors"
                      >
                        <Save className="w-3.5 h-3.5" />
                        Guardar preferencias
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* --- MEMORIA TAB --- */}
              {activeTab === "memoria" && (
                <div className="space-y-5">
                  {/* Toggle + description */}
                  <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h2 className="font-semibold text-sm flex items-center gap-2 mb-1">
                          <Brain className="w-4 h-4 text-[#EAB308]" />
                          Memoria de Contexto
                        </h2>
                        <p className="text-xs text-[#9CA3AF] max-w-md">
                          TukiJuris recordara informacion relevante sobre vos entre conversaciones
                          para dar respuestas mas personalizadas.
                        </p>
                      </div>
                      <button
                        onClick={() => setMemoryEnabled(!memoryEnabled)}
                        className={`shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium transition-colors ${
                          memoryEnabled
                            ? "bg-[#EAB308]/10 text-[#EAB308] hover:bg-[#EAB308]/20"
                            : "bg-[#1A1A22] text-[#6B7280] hover:bg-[#2A2A35]"
                        }`}
                      >
                        {memoryEnabled ? (
                          <ToggleRight className="w-4 h-4" />
                        ) : (
                          <ToggleLeft className="w-4 h-4" />
                        )}
                        {memoryEnabled ? "Activa" : "Inactiva"}
                      </button>
                    </div>

                    {/* Stats */}
                    {memoriesData && (
                      <div className="mt-4 flex items-center gap-4 text-xs text-[#6B7280]">
                        <span>{memoriesData.active_count} memorias activas</span>
                        <span className="text-[#2A2A35]">•</span>
                        <span>{memoriesData.total} memorias en total</span>
                      </div>
                    )}
                  </div>

                  {/* Memory list */}
                  <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-6">
                    <h3 className="font-semibold text-sm mb-4 text-[#F5F5F5]">
                      Lo que TukiJuris sabe sobre vos
                    </h3>

                    {loadingMemories ? (
                      <div className="flex items-center justify-center py-10 gap-2">
                        <Loader2 className="w-5 h-5 text-[#EAB308] animate-spin" />
                        <span className="text-sm text-[#6B7280]">Cargando memorias...</span>
                      </div>
                    ) : !memoriesData || memoriesData.total === 0 ? (
                      <div className="flex flex-col items-center justify-center py-10 text-center border border-dashed border-[#2A2A35] rounded-xl">
                        <Brain className="w-10 h-10 text-[#2A2A35] mb-3" />
                        <p className="text-sm font-medium text-[#9CA3AF] mb-1">
                          Sin memorias todavia
                        </p>
                        <p className="text-xs text-[#6B7280] max-w-xs">
                          TukiJuris aprendera sobre vos a medida que uses la plataforma.
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-5">
                        {memoriesData.groups.map((group) => (
                          <div key={group.category}>
                            <div className="flex items-center gap-2 mb-2">
                              <span
                                className={`text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded border ${
                                  CATEGORY_COLORS[group.category] ||
                                  "bg-[#2A2A35] text-[#9CA3AF] border-[#2A2A35]"
                                }`}
                              >
                                {group.label}
                              </span>
                            </div>
                            <div className="space-y-1.5">
                              {group.memories.map((memory) => (
                                <div
                                  key={memory.id}
                                  className={`flex items-center gap-3 px-3 py-2 rounded-xl border transition-colors ${
                                    memory.is_active
                                      ? "bg-[#1A1A22] border-[#2A2A35]"
                                      : "bg-[#1A1A22]/30 border-[#1E1E2A] opacity-50"
                                  }`}
                                >
                                  <span className="flex-1 text-sm text-[#F5F5F5] truncate">
                                    {memory.content}
                                  </span>
                                  <div className="flex items-center gap-1 shrink-0">
                                    <button
                                      onClick={() =>
                                        handleToggleMemory(memory.id, !memory.is_active)
                                      }
                                      title={memory.is_active ? "Desactivar" : "Activar"}
                                      className="p-1.5 rounded-md text-[#6B7280] hover:text-[#F5F5F5] hover:bg-[#2A2A35] transition-colors"
                                    >
                                      <Eye className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                      onClick={() => handleDeleteMemory(memory.id)}
                                      title="Eliminar"
                                      className="p-1.5 rounded-md text-[#6B7280] hover:text-red-400 hover:bg-red-400/10 transition-colors"
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
                  </div>

                  {/* Danger zone — clear all */}
                  {memoriesData && memoriesData.total > 0 && (
                    <div className="bg-[#F87171]/5 border border-[#F87171]/20 rounded-xl p-6">
                      <h3 className="font-semibold text-sm mb-2 flex items-center gap-2 text-red-400">
                        <AlertTriangle className="w-4 h-4" />
                        Zona de peligro
                      </h3>
                      <p className="text-xs text-[#6B7280] mb-4">
                        Borrar toda la memoria eliminara permanentemente todos los datos que
                        TukiJuris aprendio sobre vos.
                      </p>
                      <button
                        onClick={handleClearAllMemories}
                        disabled={clearingMemories}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl border border-red-500/30 text-red-400 hover:bg-red-500/10 disabled:opacity-50 text-sm transition-colors"
                      >
                        {clearingMemories ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="w-3.5 h-3.5" />
                        )}
                        Borrar toda la memoria
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* --- API KEYS TAB --- */}
              {activeTab === "apikeys" && (
                <div className="space-y-5">
                  {/* Header card */}
                  <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-6">
                    <h2 className="font-semibold text-sm mb-2 flex items-center gap-2">
                      <Key className="w-4 h-4 text-[#EAB308]" />
                      Tus Claves de Proveedor de IA
                    </h2>
                    <p className="text-xs text-[#9CA3AF] leading-relaxed">
                      TukiJuris no incluye modelos de IA. Conectá tu propia clave API del proveedor que prefieras.
                      Tu consumo se cobra directamente por el proveedor, no por TukiJuris.
                    </p>
                  </div>

                  {/* Provider cards */}
                  {loadingLlmKeys ? (
                    <div className="flex items-center justify-center py-10 gap-2">
                      <Loader2 className="w-5 h-5 text-[#EAB308] animate-spin" />
                      <span className="text-sm text-[#6B7280]">Cargando claves...</span>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {LLM_PROVIDERS.map((provider) => {
                        const providerKeys = llmKeys.filter((k) => k.provider === provider.id);
                        const isAdding = addingProvider === provider.id;

                        return (
                          <div
                            key={provider.id}
                            className="bg-[#111116] border border-[#1E1E2A] rounded-xl overflow-hidden"
                          >
                            {/* Provider header */}
                            <div className="px-5 py-3 border-b border-[#1E1E2A] flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className={`w-2 h-2 rounded-full ${providerKeys.length > 0 ? "bg-green-500" : "bg-[#2A2A35]"}`} />
                                <span className={`text-sm font-semibold ${providerKeys.length > 0 ? provider.accent : "text-[#F5F5F5]"}`}>
                                  {provider.name}
                                </span>
                              </div>
                              <span className="text-[10px] text-[#6B7280]">
                                {provider.models.join(" · ")}
                              </span>
                            </div>

                            {/* Existing keys */}
                            {providerKeys.length > 0 && (
                              <div className="divide-y divide-[#1E1E2A]/50">
                                {providerKeys.map((key) => (
                                  <div key={key.id} className="flex items-center gap-3 px-5 py-3">
                                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 shrink-0" />
                                    <span className="text-xs font-mono text-[#F5F5F5] flex-1">
                                      {key.hint}
                                    </span>
                                    {key.label && (
                                      <span className="text-xs text-[#6B7280] truncate max-w-[120px]">
                                        &ldquo;{key.label}&rdquo;
                                      </span>
                                    )}
                                    <button
                                      onClick={() => handleDeleteKey(key.id)}
                                      disabled={deletingKeyId === key.id}
                                      className="flex items-center gap-1 text-xs text-red-400/70 hover:text-red-400 hover:bg-red-400/10 px-2 py-1 rounded transition-colors disabled:opacity-50"
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
                              </div>
                            )}

                            {/* No key state / Add button */}
                            {!isAdding && (
                              <div className="px-5 py-3 flex items-center justify-between">
                                {providerKeys.length === 0 && (
                                  <span className="text-xs text-[#6B7280]">Sin clave configurada</span>
                                )}
                                <button
                                  onClick={() => {
                                    setAddingProvider(provider.id);
                                    setNewApiKey("");
                                    setNewApiLabel("");
                                    setShowApiKey(false);
                                  }}
                                  className={`ml-auto flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-xl border transition-colors ${provider.accentBorder} ${provider.accentBg} ${provider.accent}`}
                                >
                                  <Plus className="w-3 h-3" />
                                  Agregar clave
                                </button>
                              </div>
                            )}

                            {/* Inline add form */}
                            {isAdding && (
                              <div className="px-5 py-4 space-y-3 border-t border-[#1E1E2A]">
                                <div>
                                  <label className="block text-xs text-[#9CA3AF] mb-1.5">
                                    API Key <span className="text-red-400">*</span>
                                  </label>
                                  <div className="relative">
                                    <input
                                      type={showApiKey ? "text" : "password"}
                                      value={newApiKey}
                                      onChange={(e) => setNewApiKey(e.target.value)}
                                      placeholder="sk-... / sk-ant-... / AIza..."
                                      autoFocus
                                      className="w-full bg-[#111116] border border-[#2A2A35] rounded-xl px-3 py-2.5 pr-10 text-sm font-mono text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-1 focus:ring-[#EAB308]/25"
                                    />
                                    <button
                                      type="button"
                                      onClick={() => setShowApiKey(!showApiKey)}
                                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B7280] hover:text-[#F5F5F5]"
                                    >
                                      {showApiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                                    </button>
                                  </div>
                                </div>
                                <div>
                                  <label className="block text-xs text-[#9CA3AF] mb-1.5">
                                    Etiqueta <span className="text-[#6B7280]">(opcional)</span>
                                  </label>
                                  <input
                                    type="text"
                                    value={newApiLabel}
                                    onChange={(e) => setNewApiLabel(e.target.value)}
                                    placeholder={`Mi cuenta ${provider.name}`}
                                    className="w-full bg-[#111116] border border-[#2A2A35] rounded-xl px-3 py-2.5 text-sm text-[#F5F5F5] placeholder-[#6B7280] focus:outline-none focus:border-[#EAB308] focus:ring-1 focus:ring-[#EAB308]/25"
                                  />
                                </div>
                                <div className="flex items-center gap-2 justify-end pt-1">
                                  <button
                                    onClick={() => {
                                      setAddingProvider(null);
                                      setNewApiKey("");
                                      setNewApiLabel("");
                                    }}
                                    className="px-3 py-1.5 text-xs text-[#9CA3AF] hover:text-[#F5F5F5] border border-[#2A2A35] rounded-xl transition-colors"
                                  >
                                    Cancelar
                                  </button>
                                  <button
                                    onClick={() => handleAddKey(provider.id)}
                                    disabled={savingKey || !newApiKey.trim()}
                                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-[#EAB308] hover:bg-[#ca9a07] disabled:bg-[#2A2A35] disabled:text-[#6B7280] text-[#0A0A0F] rounded-xl transition-colors"
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

                  {/* Info footer */}
                  <div className="bg-[#111116] border border-[#1E1E2A] rounded-xl p-5 space-y-4">
                    <div className="flex items-start gap-2">
                      <span className="text-base">ℹ️</span>
                      <p className="text-xs text-[#9CA3AF] leading-relaxed">
                        Cada proveedor tiene sus propios modelos y precios. Tu consumo se cobra directamente
                        por el proveedor, no por TukiJuris. Las claves se almacenan cifradas y nunca se muestran
                        completas.
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-[#6B7280] mb-2 flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-[#EAB308]" />
                        Guías para obtener claves:
                      </p>
                      <div className="space-y-1.5">
                        {LLM_PROVIDERS.map((p) => (
                          <a
                            key={p.id}
                            href={p.docsUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`flex items-center gap-2 text-xs transition-colors ${p.accent} hover:underline`}
                          >
                            <ExternalLink className="w-3 h-3" />
                            <span className="font-medium">{p.name}:</span>
                            <span className="text-[#6B7280]">{p.docsLabel}</span>
                          </a>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        </div>
      </div>
    </AppLayout>
  );
}
