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
import { MODEL_CATALOG } from "@/lib/models";

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
  const [defaultModel, setDefaultModel] = useState(MODEL_CATALOG[0].id);
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
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { ok: boolean; latency_ms?: number; error?: string }>>({});

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

  const handleTestKey = async (providerId: string) => {
    setTestingProvider(providerId);
    setTestResults((prev) => ({ ...prev, [providerId]: undefined as any }));
    try {
      const res = await fetch(`${API_URL}/api/keys/llm-keys/test`, {
        method: "POST",
        headers: authHeaders(),
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
      <div className="min-h-full text-on-surface">
        {/* Header */}
        <div className="border-b border-[rgba(79,70,51,0.15)] px-4 lg:px-6 py-5 flex items-center gap-3 sticky top-0 z-10 bg-[#0e0e14]">
          <Settings className="w-4 h-4 text-primary" />
          <span className="text-primary text-xs uppercase tracking-[0.2em] font-bold">Cuenta</span>
          <span className="text-on-surface/20 mx-1">·</span>
          <h1 className="font-['Newsreader'] text-xl font-bold text-on-surface">Configuración</h1>
        </div>

        <div className="max-w-5xl mx-auto px-4 lg:px-6 py-6 sm:py-8">
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
            <div className="flex flex-col lg:flex-row gap-4 sm:gap-6">
              {/* Sidebar */}
              <aside className="lg:w-52 shrink-0 lg:sticky lg:top-20 lg:self-start">
                {/* Mobile: horizontal scroll tabs */}
                <div className="lg:hidden overflow-x-auto">
                  <div className="flex gap-1 bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-1 min-w-max">
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
                <nav className="hidden lg:block bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg overflow-hidden">
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
                {/* --- PERFIL TAB --- */}
                {activeTab === "perfil" && (
                  <div className="space-y-4">
                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6">
                      <h2 className="font-['Newsreader'] text-lg font-bold text-on-surface mb-5 flex items-center gap-2">
                        <User className="w-4 h-4 text-primary" />
                        Informacion del perfil
                      </h2>
                      <form onSubmit={handleSaveProfile} className="space-y-4">
                        <div>
                          <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">
                            Correo electronico
                          </label>
                          <input
                            type="email"
                            value={profile?.email || ""}
                            readOnly
                            className="w-full bg-surface border border-transparent rounded-lg px-3 py-3 text-sm text-on-surface/40 cursor-not-allowed"
                          />
                          <p className="text-[10px] text-on-surface/30 mt-1">El email no puede ser modificado</p>
                        </div>
                        <div>
                          <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">
                            Nombre
                          </label>
                          <input
                            type="text"
                            value={profileName}
                            onChange={(e) => setProfileName(e.target.value)}
                            placeholder="Tu nombre completo"
                            className="w-full bg-[#35343a] border border-transparent rounded-lg px-3 py-3 text-sm text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors"
                          />
                        </div>
                        <div className="flex justify-end">
                          <button
                            type="submit"
                            disabled={savingProfile}
                            className="bg-gradient-to-br from-primary to-primary-container disabled:opacity-40 text-on-primary rounded-lg px-5 py-2.5 text-sm font-bold flex items-center gap-2 transition-opacity"
                          >
                            {savingProfile ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                            Guardar cambios
                          </button>
                        </div>
                      </form>
                    </div>

                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6">
                      <h2 className="font-['Newsreader'] text-lg font-bold text-on-surface mb-5 flex items-center gap-2">
                        <Lock className="w-4 h-4 text-primary" />
                        Cambiar contrasena
                      </h2>
                      <form onSubmit={handleChangePassword} className="space-y-4">
                        <div>
                          <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">
                            Contrasena actual
                          </label>
                          <div className="relative">
                            <input
                              type={showCurrentPw ? "text" : "password"}
                              value={currentPassword}
                              onChange={(e) => setCurrentPassword(e.target.value)}
                              placeholder="••••••••"
                              className="w-full bg-[#35343a] border border-transparent rounded-lg px-3 py-3 pr-10 text-sm text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors"
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
                          <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">
                            Nueva contrasena
                          </label>
                          <div className="relative">
                            <input
                              type={showNewPw ? "text" : "password"}
                              value={newPassword}
                              onChange={(e) => setNewPassword(e.target.value)}
                              placeholder="Minimo 8 caracteres"
                              className="w-full bg-[#35343a] border border-transparent rounded-lg px-3 py-3 pr-10 text-sm text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors"
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
                        <div>
                          <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">
                            Confirmar nueva contrasena
                          </label>
                          <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="Repite la nueva contrasena"
                            className="w-full bg-[#35343a] border border-transparent rounded-lg px-3 py-3 text-sm text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors"
                            required
                          />
                        </div>
                        <div className="flex justify-end">
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
                    </div>
                  </div>
                )}

                {/* --- ORGANIZACION TAB --- */}
                {activeTab === "organizacion" && (
                  <div className="space-y-4">
                    {org ? (
                      <>
                        <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6">
                          <h2 className="font-['Newsreader'] text-lg font-bold text-on-surface mb-5 flex items-center gap-2">
                            <Building2 className="w-4 h-4 text-primary" />
                            Datos de la organizacion
                          </h2>
                          <form onSubmit={handleSaveOrg} className="space-y-4">
                            <div>
                              <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">
                                Nombre de la organizacion
                              </label>
                              <input
                                type="text"
                                value={orgName}
                                onChange={(e) => setOrgName(e.target.value)}
                                placeholder="Nombre de tu organizacion"
                                className="w-full bg-[#35343a] border border-transparent rounded-lg px-3 py-3 text-sm text-on-surface placeholder-on-surface/30 focus:outline-none focus:border-primary transition-colors"
                                required
                              />
                            </div>
                            <div>
                              <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">
                                Identificador (slug)
                              </label>
                              <input
                                type="text"
                                value={org.slug}
                                readOnly
                                className="w-full bg-surface border border-transparent rounded-lg px-3 py-3 text-sm text-on-surface/40 cursor-not-allowed"
                              />
                              <p className="text-[10px] text-on-surface/30 mt-1">El slug no puede ser modificado</p>
                            </div>
                            <div>
                              <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">Plan</label>
                              <div className="flex items-center gap-2">
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
                        </div>

                        <div className="bg-[#93000a]/10 border border-[#ffb4ab]/20 rounded-lg p-6">
                          <h2 className="font-['Newsreader'] text-base font-bold mb-2 flex items-center gap-2 text-[#ffb4ab]">
                            <AlertTriangle className="w-4 h-4" />
                            Zona de peligro
                          </h2>
                          <p className="text-xs text-on-surface/40 mb-4">
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
                            className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-[#ffb4ab]/30 text-[#ffb4ab] hover:bg-[#93000a]/20 text-sm transition-colors"
                          >
                            <LogOut className="w-3.5 h-3.5" />
                            Abandonar organizacion
                          </button>
                        </div>
                      </>
                    ) : (
                      <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-8 text-center">
                        <Building2 className="w-10 h-10 text-on-surface/10 mx-auto mb-3" />
                        <p className="text-sm text-on-surface/40 mb-4">No perteneces a ninguna organizacion</p>
                        <Link
                          href="/organizacion"
                          className="inline-flex items-center gap-2 bg-gradient-to-br from-primary to-primary-container text-on-primary rounded-lg px-4 py-2.5 text-sm font-bold transition-opacity"
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
                  <div className="space-y-4">
                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6">
                      <h2 className="font-['Newsreader'] text-lg font-bold text-on-surface mb-1 flex items-center gap-2">
                        <Sliders className="w-4 h-4 text-primary" />
                        Modelo de IA predeterminado
                      </h2>
                      <p className="text-[11px] text-on-surface/40 mb-5">
                        Selecciona el modelo que se usará por defecto al iniciar una consulta.
                      </p>

                      <div className="space-y-4">
                        {(() => {
                          const providerOrder = ["google", "groq", "deepseek", "openai", "anthropic", "xai"];
                          const providerLabels: Record<string, { name: string; color: string }> = {
                            google: { name: "Google (Gemini)", color: "text-blue-400" },
                            groq: { name: "Groq", color: "text-orange-400" },
                            deepseek: { name: "DeepSeek", color: "text-cyan-400" },
                            openai: { name: "OpenAI", color: "text-green-400" },
                            anthropic: { name: "Anthropic (Claude)", color: "text-amber-400" },
                          };
                          const tierBadge = (tier: string) => {
                            const styles: Record<string, string> = {
                              free: "bg-[#1a3a2a] text-[#6ee7b7]",
                              standard: "bg-secondary-container text-secondary",
                              pro: "bg-[#2d1f4a] text-[#c4b5fd]",
                            };
                            const labels: Record<string, string> = {
                              free: "Gratis",
                              standard: "Estándar",
                              pro: "Avanzado",
                            };
                            return (
                              <span className={`text-[9px] uppercase tracking-widest font-bold px-1.5 py-0.5 rounded ${styles[tier] || ""}`}>
                                {labels[tier] || tier}
                              </span>
                            );
                          };

                          const configuredProviders = new Set(llmKeys.map(k => k.provider));

                          return providerOrder.map((providerId) => {
                            const info = providerLabels[providerId];
                            if (!info) return null;
                            const models = MODEL_CATALOG.filter(m => m.provider === providerId);
                            if (models.length === 0) return null;
                            const hasKey = configuredProviders.has(providerId);

                            return (
                              <div key={providerId}>
                                <div className="flex items-center gap-2 mb-2">
                                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${hasKey ? "bg-[#6ee7b7]" : "bg-[#35343a]"}`} />
                                  <span className={`text-xs font-bold uppercase tracking-widest ${info.color}`}>{info.name}</span>
                                  {!hasKey && (
                                    <span className="text-[9px] text-on-surface/20">— sin API key</span>
                                  )}
                                </div>

                                <div className="space-y-1 pl-3.5">
                                  {models.map((model) => {
                                    const isSelected = defaultModel === model.id;
                                    return (
                                      <label
                                        key={model.id}
                                        className={`flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                                          isSelected
                                            ? "bg-primary/10 border border-primary/20"
                                            : "border border-transparent hover:bg-surface-container"
                                        } ${!hasKey ? "opacity-30 cursor-not-allowed" : ""}`}
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
                                        <div className={`w-3.5 h-3.5 rounded-full border-2 shrink-0 flex items-center justify-center ${
                                          isSelected ? "border-primary" : "border-[#35343a]"
                                        }`}>
                                          {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-primary" />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                          <span className={`text-sm ${isSelected ? "text-on-surface font-medium" : "text-on-surface/60"}`}>
                                            {model.name}
                                          </span>
                                        </div>
                                        <div className="flex items-center gap-2 shrink-0">
                                          {tierBadge(model.tier)}
                                        </div>
                                        <span className="text-[10px] text-on-surface/25 max-w-[140px] truncate hidden sm:block">
                                          {model.description}
                                        </span>
                                      </label>
                                    );
                                  })}
                                </div>
                              </div>
                            );
                          });
                        })()}
                      </div>
                    </div>

                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6">
                      <form onSubmit={handleSavePreferences} className="space-y-5">
                        <div>
                          <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">
                            Área legal predeterminada
                          </label>
                          <select
                            value={defaultArea}
                            onChange={(e) => setDefaultArea(e.target.value)}
                            className="w-full bg-[#35343a] border border-transparent rounded-lg px-3 py-3 text-sm text-on-surface focus:outline-none focus:border-primary transition-colors"
                          >
                            {LEGAL_AREAS.map((a) => (
                              <option key={a.id} value={a.id}>{a.name}</option>
                            ))}
                          </select>
                          <p className="text-[10px] text-on-surface/30 mt-1">
                            Las consultas se dirigirán a esta área por defecto
                          </p>
                        </div>

                        <div>
                          <label className="block text-xs uppercase tracking-widest text-on-surface-variant mb-1.5">
                            Tema de la interfaz
                          </label>
                          <div className="flex items-center gap-3 py-3 px-3 bg-surface border border-transparent rounded-lg">
                            <div className="w-4 h-4 rounded-full bg-[#0e0e14] border border-[rgba(79,70,51,0.15)]" />
                            <span className="text-sm text-on-surface">Modo oscuro</span>
                            <span className="ml-auto text-[10px] text-on-surface/30">Siempre activo</span>
                          </div>
                        </div>

                        <div className="flex justify-end pt-2">
                          <button
                            type="submit"
                            className="bg-gradient-to-br from-primary to-primary-container text-on-primary rounded-lg px-5 py-2.5 text-sm font-bold flex items-center gap-2 transition-opacity"
                          >
                            <Save className="w-3.5 h-3.5" />
                            Guardar preferencias
                          </button>
                        </div>
                      </form>
                    </div>
                  </div>
                )}

                {/* --- MEMORIA TAB --- */}
                {activeTab === "memoria" && (
                  <div className="space-y-4">
                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6">
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
                    </div>

                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6">
                      <h3 className="text-xs uppercase tracking-widest text-on-surface-variant mb-4">
                        Lo que TukiJuris sabe sobre vos
                      </h3>

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
                    </div>

                    {memoriesData && memoriesData.total > 0 && (
                      <div className="bg-[#93000a]/10 border border-[#ffb4ab]/20 rounded-lg p-6">
                        <h3 className="font-['Newsreader'] text-base font-bold mb-2 flex items-center gap-2 text-[#ffb4ab]">
                          <AlertTriangle className="w-4 h-4" />
                          Zona de peligro
                        </h3>
                        <p className="text-xs text-on-surface/40 mb-4">
                          Borrar toda la memoria eliminara permanentemente todos los datos que
                          TukiJuris aprendio sobre vos.
                        </p>
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
                      </div>
                    )}
                  </div>
                )}

                {/* --- API KEYS TAB --- */}
                {activeTab === "apikeys" && (
                  <div className="space-y-4">
                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-6 space-y-4">
                      <h2 className="font-['Newsreader'] text-lg font-bold text-on-surface flex items-center gap-2">
                        <Key className="w-4 h-4 text-primary" />
                        Conecta tu Inteligencia Artificial
                      </h2>
                      <p className="text-xs text-on-surface/40 leading-relaxed">
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
                    </div>

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

                          return (
                            <div
                              key={provider.id}
                              className={`bg-surface-container-low border rounded-lg overflow-hidden transition-colors ${
                                isActive ? `${provider.accentBorder}` : "border-[rgba(79,70,51,0.15)]"
                              }`}
                            >
                              <div className="px-5 py-4 flex items-start justify-between gap-3">
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

                              {provider.note && (
                                <div className="mx-5 mb-3 flex items-start gap-2 text-[11px] text-blue-300/80 bg-blue-500/5 border border-blue-500/10 rounded-lg px-3 py-2">
                                  <Shield className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                                  <span>{provider.note}</span>
                                </div>
                              )}

                              {providerKeys.length > 0 && (
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

                              {!isAdding && (
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

                              {isAdding && (
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
                                        className="w-full bg-surface border border-transparent rounded-lg px-3 py-3 pr-10 text-sm font-mono text-on-surface placeholder-on-surface/20 focus:outline-none focus:border-primary transition-colors"
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
                                      className="w-full bg-surface border border-transparent rounded-lg px-3 py-3 text-sm text-on-surface placeholder-on-surface/20 focus:outline-none focus:border-primary transition-colors"
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

                    <div className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-5 space-y-4">
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
