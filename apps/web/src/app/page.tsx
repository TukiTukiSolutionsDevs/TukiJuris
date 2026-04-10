"use client";

import { useState, useRef, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Scale,
  Send,
  Bot,
  User,
  Loader2,
  BookOpen,
  Shield,
  Briefcase,
  Landmark,
  Gavel,
  Building2,
  Plus,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  ScrollText,
  FileCheck,
  Globe,
  Lock,
  BadgeCheck,
  Download,
  Bookmark,
  Bold,
  Italic,
  List,
  Code,
  ChevronDown,
  ChevronUp,
  Pin,
  Archive,
  Share2,
  Trash2,
  History,
  Pencil,
  Check,
  Paperclip,
  FileText,
  X,
  Brain,
  CheckCircle2,
  PanelRightClose,
  Calculator,
  Store,
  TreePine,
  Heart,
} from "lucide-react";
import NotificationBell from "@/components/NotificationBell";
import KeyboardShortcuts from "@/components/KeyboardShortcuts";
import HelpPopover from "@/components/HelpPopover";
import { AppLayout } from "@/components/AppLayout";
import { getToken } from "@/lib/auth";
import { t } from "@/lib/i18n";
import { renderMarkdown } from "@/lib/markdown";
import { MODEL_CATALOG, availableModelsForProviders, modelSupportsThinking } from "@/lib/models";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Query templates
// ---------------------------------------------------------------------------
const QUERY_TEMPLATES: Record<string, { label: string; query: string }[]> = {
  laboral: [
    { label: "Despido justificado", query: "Cuales son los requisitos legales para un despido justificado segun el DS 003-97-TR?" },
    { label: "Calculo CTS", query: "Como se calcula la Compensacion por Tiempo de Servicios en Peru?" },
    { label: "Vacaciones", query: "Cuales son los derechos de vacaciones segun el DL 713?" },
    { label: "Horas extras", query: "Como se calcula el pago de horas extras en Peru?" },
  ],
  penal: [
    { label: "Prescripcion", query: "Cuales son los plazos de prescripcion en materia penal?" },
    { label: "Legitima defensa", query: "Requisitos de la legitima defensa en el Codigo Penal peruano" },
    { label: "Medidas cautelares", query: "Cuando procede la detencion preventiva segun el CPP peruano?" },
    { label: "Principio de legalidad", query: "Como se aplica el principio de legalidad en el derecho penal peruano?" },
  ],
  civil: [
    { label: "Responsabilidad civil", query: "Que establece el Art. 1969 del Codigo Civil sobre responsabilidad extracontractual?" },
    { label: "Contratos", query: "Requisitos de validez de un contrato segun el Codigo Civil peruano" },
    { label: "Prescripcion civil", query: "Cuales son los plazos de prescripcion en materia civil?" },
    { label: "Daños y perjuicios", query: "Como se determina la indemnizacion por danos y perjuicios en Peru?" },
  ],
  tributario: [
    { label: "Impuesto a la Renta", query: "Cuales son las categorias del Impuesto a la Renta en Peru?" },
    { label: "IGV", query: "Que operaciones estan gravadas con el IGV?" },
    { label: "Infracciones SUNAT", query: "Cuales son las principales infracciones tributarias y sus multas?" },
    { label: "Regimenes tributarios", query: "Que regimenes tributarios existen para empresas en Peru?" },
  ],
  constitucional: [
    { label: "Habeas corpus", query: "Cuando procede el habeas corpus segun el Tribunal Constitucional?" },
    { label: "Derechos fundamentales", query: "Cuales son los derechos fundamentales en la Constitucion peruana?" },
    { label: "Amparo", query: "Que es la accion de amparo y cuando procede en Peru?" },
    { label: "Bloque constitucional", query: "Que comprende el bloque de constitucionalidad en Peru?" },
  ],
  administrativo: [
    { label: "Silencio administrativo", query: "Que es el silencio administrativo positivo y negativo en Peru?" },
    { label: "Recursos administrativos", query: "Cuales son los recursos administrativos en la LPAG?" },
    { label: "Acto administrativo", query: "Cuales son los requisitos de validez de un acto administrativo?" },
    { label: "Contrataciones Estado", query: "Cuales son las modalidades de contratacion del Estado peruano?" },
  ],
  general: [
    { label: "Despido justificado", query: "Cuales son los requisitos para un despido justificado?" },
    { label: "CTS", query: "Como se calcula la CTS en Peru?" },
    { label: "Art. 1351 CC", query: "Que dice el Art. 1351 del Codigo Civil?" },
    { label: "Prescripcion penal", query: "Plazos de prescripcion en derecho penal" },
  ],
};

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface Citation {
  type: string;
  text: string;
  reference: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent_used?: string;
  legal_area?: string;
  latency_ms?: number;
  citations?: Citation[];
  model_used?: string;
  is_bookmarked?: boolean;
  feedback?: "thumbs_up" | "thumbs_down";
  is_multi_area?: boolean; // True when multiple specialists were consulted
}

const LEGAL_AREAS = [
  { id: "civil", name: "Civil", label: "Derecho Civil", icon: BookOpen, color: "text-blue-400" },
  { id: "penal", name: "Penal", label: "Derecho Penal", icon: Shield, color: "text-red-400" },
  { id: "laboral", name: "Laboral", label: "Derecho Laboral", icon: Briefcase, color: "text-green-400" },
  { id: "tributario", name: "Tributario", label: "Derecho Tributario", icon: Calculator, color: "text-yellow-400" },
  { id: "constitucional", name: "Constitucional", label: "Derecho Constitucional", icon: Landmark, color: "text-purple-400" },
  { id: "administrativo", name: "Administrativo", label: "Derecho Administrativo", icon: Building2, color: "text-orange-400" },
  { id: "corporativo", name: "Corporativo", label: "Derecho Comercial", icon: Store, color: "text-cyan-400" },
  { id: "registral", name: "Registral", label: "Derecho Registral", icon: FileCheck, color: "text-pink-400" },
  { id: "comercio_exterior", name: "Comercio Ext.", label: "Comercio Exterior", icon: Globe, color: "text-teal-400" },
  { id: "compliance", name: "Compliance", label: "Compliance / Ambiental", icon: TreePine, color: "text-indigo-400" },
  { id: "competencia", name: "Competencia/PI", label: "Competencia / Propiedad Intelectual", icon: Heart, color: "text-amber-400" },
];

interface ChatHistory {
  id: string;
  title: string | null;
  legal_area: string | null;
  date: string;
  is_pinned: boolean;
  is_shared: boolean;
}

interface ContextMenu {
  convId: string;
  convTitle: string | null;
  x: number;
  y: number;
}

// ---------------------------------------------------------------------------
// Formatting toolbar helpers
// ---------------------------------------------------------------------------
function insertMarkdownSyntax(
  textarea: HTMLTextAreaElement,
  prefix: string,
  suffix: string,
  placeholder: string,
  setter: (v: string) => void
) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selected = textarea.value.slice(start, end) || placeholder;
  const before = textarea.value.slice(0, start);
  const after = textarea.value.slice(end);
  const newValue = `${before}${prefix}${selected}${suffix}${after}`;
  setter(newValue);

  // Restore focus and selection after React re-render
  requestAnimationFrame(() => {
    textarea.focus();
    const newStart = start + prefix.length;
    const newEnd = newStart + selected.length;
    textarea.setSelectionRange(newStart, newEnd);
  });
}

// ---------------------------------------------------------------------------
// Main component (inner — uses useSearchParams, must be wrapped in Suspense)
// ---------------------------------------------------------------------------
function ChatPage() {
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedArea, setSelectedArea] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState(MODEL_CATALOG[0].id);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [reasoningEffort, setReasoningEffort] = useState<string | null>(null); // "low" | "medium" | "high" | null (auto)

  // Hydration-safe: load user's preferred model from localStorage after mount
  useEffect(() => {
    const saved = localStorage.getItem("pref_default_model");
    if (saved && saved !== selectedModel) {
      setSelectedModel(saved);
      // Reset reasoning if saved model doesn't support it
      if (!modelSupportsThinking(saved)) {
        setReasoningEffort(null);
      }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [showAreas, setShowAreas] = useState(true);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [showAllTemplates, setShowAllTemplates] = useState(false);
  const [contextMenu, setContextMenu] = useState<ContextMenu | null>(null);
  const [contextActionLoading, setContextActionLoading] = useState<string | null>(null);
  const [copiedShareId, setCopiedShareId] = useState<string | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [conversationTitle, setConversationTitle] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showShortcutsModal, setShowShortcutsModal] = useState(false);
  const [attachedFile, setAttachedFile] = useState<{
    id: string;
    name: string;
    type: string;
    preview: string;
  } | null>(null);
  const [uploading, setUploading] = useState(false);
  const [orchestratorStatus, setOrchestratorStatus] = useState<string | null>(null);

  // Orchestration panel state
  const [showOrchPanel, setShowOrchPanel] = useState(true);
  const [orchState, setOrchState] = useState<{
    phase: 'idle' | 'classifying' | 'retrieving' | 'thinking' | 'evaluating' | 'enriching' | 'synthesizing' | 'done';
    activeAgents: string[];
    primaryArea: string | null;
    secondaryAreas: string[];
    confidence: number;
    statusText: string;
    steps: { icon: string; text: string; ts: number; done: boolean }[];
    evaluationReason: string;
    latencyMs: number;
    citationCount: number;
    modelUsed: string;
    reasoningLevel: string | null;
    startTime: number;
  }>({
    phase: 'idle',
    activeAgents: [],
    primaryArea: null,
    secondaryAreas: [],
    confidence: 0,
    statusText: '',
    steps: [],
    evaluationReason: '',
    latencyMs: 0,
    citationCount: 0,
    modelUsed: '',
    reasoningLevel: null,
    startTime: 0,
  });

  // Load auth token on mount (client-side only — localStorage not available on server)
  useEffect(() => {
    setAuthToken(getToken());
  }, []);

  // Beta BYOK-only: fetch available models strictly from the user's own keys.
  useEffect(() => {
    const token = getToken();
    if (!token) return;

    fetch(`${API_URL}/api/keys/llm-keys`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : []))
      .then((keys: { provider: string }[]) => {
        const providers = keys.map((k) => k.provider);
        const byokModels = [...new Set(availableModelsForProviders(providers))];

        setAvailableModels(byokModels);
        // Update selected model if current selection is no longer available
        if (byokModels.length > 0 && !byokModels.includes(selectedModel)) {
          setSelectedModel(byokModels[0]);
        }
      })
      .catch(() => {
        setAvailableModels([]);
      });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Sync model selection across tabs (e.g. when changed in Configuración)
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === "pref_default_model" && e.newValue) {
        setSelectedModel(e.newValue);
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  // Load a conversation by ID from API
  const loadConversation = useCallback(async (id: string) => {
    const token = getToken();
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/conversations/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setCurrentConversationId(id);
      setMessages(
        data.messages.map((m: { role: string; content: string; agent_used?: string; citations?: string[]; latency_ms?: number; id?: string }) => ({
          id: m.id ?? crypto.randomUUID(),
          role: m.role,
          content: m.content,
          agent_used: m.agent_used,
          citations: m.citations,
          latency_ms: m.latency_ms,
        }))
      );
      if (data.title) setConversationTitle(data.title);
      if (data.legal_area) setSelectedArea(data.legal_area);
    } catch (e) {
      console.error("Error loading conversation:", e);
    }
  }, []);

  // Process URL search params on mount / param change
  useEffect(() => {
    const conversationId =
      searchParams.get("conversation") || searchParams.get("conv");
    if (conversationId) {
      loadConversation(conversationId);
    }

    const initialQuery = searchParams.get("q");
    if (initialQuery) {
      setInput(decodeURIComponent(initialQuery));
    }
  }, [searchParams, loadConversation]);

  // Feedback handler — sends thumbs up/down to API
  const handleFeedback = useCallback(
    async (messageId: string, rating: "thumbs_up" | "thumbs_down") => {
      const token = getToken();
      if (!token) return;
      try {
        await fetch(`${API_URL}/api/feedback/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ message_id: messageId, feedback: rating }),
        });
        // Optimistic visual update — highlight selected rating
        setMessages((prev) =>
          prev.map((m) =>
            m.id === messageId ? { ...m, feedback: rating } : m
          )
        );
      } catch (e) {
        console.error("Feedback error:", e);
      }
    },
    []
  );

  // Close context menu on outside click
  useEffect(() => {
    if (!contextMenu) return;
    const handler = () => setContextMenu(null);
    window.addEventListener("click", handler);
    window.addEventListener("keydown", (e) => e.key === "Escape" && setContextMenu(null));
    return () => window.removeEventListener("click", handler);
  }, [contextMenu]);

  // Fetch conversation history from API (requires auth)
  const fetchHistory = useCallback(async (token: string) => {
    try {
      const res = await fetch(`${API_URL}/api/conversations/?status=active&limit=30`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      const entries: ChatHistory[] = data.map((c: {
        id: string;
        title: string | null;
        legal_area: string | null;
        updated_at: string;
        is_pinned: boolean;
        is_shared: boolean;
      }) => ({
        id: c.id,
        title: c.title,
        legal_area: c.legal_area,
        date: new Date(c.updated_at).toLocaleDateString("es-PE"),
        is_pinned: c.is_pinned,
        is_shared: c.is_shared,
      }));
      // Pinned first
      entries.sort((a, b) => Number(b.is_pinned) - Number(a.is_pinned));
      setChatHistory(entries);
    } catch {
      // Silently fail — history is a convenience feature
    }
  }, []);

  useEffect(() => {
    if (authToken) fetchHistory(authToken);
  }, [authToken, fetchHistory]);

  // Context menu action helper
  const contextAction = useCallback(async (
    convId: string,
    endpoint: string,
    method = "PUT"
  ) => {
    if (!authToken) return;
    setContextActionLoading(endpoint);
    try {
      const res = await fetch(`${API_URL}/api/conversations/${convId}/${endpoint}`, {
        method,
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (!res.ok) return;
      await fetchHistory(authToken);
    } finally {
      setContextActionLoading(null);
      setContextMenu(null);
    }
  }, [authToken, fetchHistory]);

  const contextShare = useCallback(async (convId: string) => {
    if (!authToken) return;
    setContextActionLoading("share");
    try {
      const res = await fetch(`${API_URL}/api/conversations/${convId}/share`, {
        method: "POST",
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      const appBase = process.env.NEXT_PUBLIC_APP_URL || "https://tukijuris.net.pe";
      const url = data.url ?? `${appBase}/compartido/${data.share_id}`;
      await navigator.clipboard.writeText(url);
      setCopiedShareId(convId);
      setTimeout(() => setCopiedShareId(null), 2500);
      await fetchHistory(authToken);
    } finally {
      setContextActionLoading(null);
      setContextMenu(null);
    }
  }, [authToken, fetchHistory]);

  const startNewChat = useCallback(() => {
    setMessages([]);
    setSelectedArea(null);
    setShowAllTemplates(false);
    setCurrentConversationId(null);
    setConversationTitle(null);
    setAttachedFile(null);
  }, []);

  const handleFileUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const token = getToken();
      if (!token) {
        // setError not available here — log and return
        console.error("Inicia sesión para subir archivos");
        return;
      }

      setUploading(true);
      try {
        const formData = new FormData();
        formData.append("file", file);
        if (currentConversationId) {
          formData.append("conversation_id", currentConversationId);
        }

        const res = await fetch(`${API_URL}/api/upload/`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Error al subir" }));
          throw new Error(err.detail || "Error al subir archivo");
        }

        const data = await res.json();
        setAttachedFile({
          id: data.id,
          name: data.filename,
          type: data.file_type,
          preview: data.text_preview || "",
        });
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Error al subir archivo";
        console.error(message);
      } finally {
        setUploading(false);
        // Reset input so the same file can be re-uploaded if needed
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    },
    [currentConversationId]
  );

  const handleDownloadPDF = async (assistantMsg: Message) => {
    const msgIndex = messages.findIndex((m) => m.id === assistantMsg.id);
    const precedingUser = messages
      .slice(0, msgIndex)
      .reverse()
      .find((m) => m.role === "user");

    const query = precedingUser?.content ?? "Consulta legal";
    const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, "");

    try {
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`;
      }

      const res = await fetch(`${API_URL}/api/export/consultation/pdf`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          query,
          answer: assistantMsg.content,
          citations: [],
          area: assistantMsg.legal_area ?? selectedArea ?? "general",
          agent_used: assistantMsg.agent_used ?? "TukiJuris",
          model: selectedModel,
          timestamp: new Date().toISOString(),
        }),
      });

      if (!res.ok) throw new Error("Error al generar PDF");

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `consulta-tukijuris-${dateStr}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch {
      // Silent fail — the button is a convenience feature
    }
  };

  const handleToggleBookmark = async (msg: Message) => {
    // Optimistic update
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msg.id ? { ...m, is_bookmarked: !m.is_bookmarked } : m
      )
    );

    if (!authToken) return; // bookmarks require auth

    try {
      await fetch(`${API_URL}/api/bookmarks/${msg.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
      });
    } catch {
      // Revert optimistic update on failure
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msg.id ? { ...m, is_bookmarked: msg.is_bookmarked } : m
        )
      );
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    if (availableModels.length === 0) return;

    // Build the query — prepend file context if an attachment is present
    let queryToSend = input;
    if (attachedFile && attachedFile.preview) {
      queryToSend = `[Documento adjunto: ${attachedFile.name}]\n\n${attachedFile.preview}\n\n---\n\nConsulta del usuario: ${input}`;
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: input,
    };
    setMessages((prev) => [...prev, userMessage]);
    const query = queryToSend;
    setInput("");
    setAttachedFile(null);
    setIsLoading(true);

    // Reset orchestration panel for new query
    const reasoningLabels: Record<string, string> = { low: 'Rápida', medium: 'Moderada', high: 'Profunda' };
    setOrchState({
      phase: 'classifying',
      activeAgents: [],
      primaryArea: null,
      secondaryAreas: [],
      confidence: 0,
      statusText: 'Analizando consulta...',
      steps: [{ icon: '📝', text: 'Consulta recibida', ts: Date.now(), done: true }],
      evaluationReason: '',
      latencyMs: 0,
      citationCount: 0,
      modelUsed: selectedModel,
      reasoningLevel: reasoningEffort ? (reasoningLabels[reasoningEffort] || reasoningEffort) : 'Auto',
      startTime: Date.now(),
    });

    // Create placeholder assistant message for streaming
    const assistantId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      { id: assistantId, role: "assistant", content: "", is_bookmarked: false },
    ]);

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      const token = getToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(`${API_URL}/api/chat/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          message: query,
          conversation_id: currentConversationId || undefined,
          legal_area: selectedArea || undefined,
          model: selectedModel,
          reasoning_effort: reasoningEffort || undefined,
        }),
      });

      if (!res.ok) {
        // Read error detail from API (e.g., 429 daily limit exceeded)
        const errData = await res.json().catch(() => null);
        const detail = errData?.detail ?? "Error en la consulta";
        throw new Error(detail);
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let agentUsed = "";
      let latencyMs = 0;

      if (reader) {
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === "final_stream_start") {
                // The backend finished ALL internal processing.
                // Now tokens will arrive via "final_token" events.
                agentUsed = data.agent_used || agentUsed;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? {
                          ...m,
                          agent_used: data.agent_used || m.agent_used,
                          legal_area: data.legal_area || m.legal_area,
                          is_multi_area: data.is_multi_area || false,
                        }
                      : m
                  )
                );
                setOrchState(prev => ({
                  ...prev,
                  phase: 'done',
                  statusText: 'Respuesta lista',
                  steps: [
                    ...prev.steps.map(s => ({ ...s, done: true })),
                    { icon: '✨', text: 'Respuesta lista', ts: Date.now(), done: true },
                  ],
                }));

              } else if (data.type === "final_token") {
                // The ONLY token type — final verified response
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, content: m.content + data.content }
                      : m
                  )
                );

              } else if (data.type === "token") {
                // Legacy fallback — should not occur with v2 pipeline
                // but kept for safety during rollout
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, content: m.content + data.content }
                      : m
                  )
                );
              } else if (data.type === "classification") {
                setOrchState(prev => ({
                  ...prev,
                  phase: 'retrieving',
                  primaryArea: data.legal_area,
                  activeAgents: [data.legal_area],
                  confidence: data.confidence || 0,
                  statusText: `Área detectada: ${data.legal_area} (${Math.round((data.confidence || 0) * 100)}%)`,
                  steps: [...prev.steps, { icon: '🎯', text: `Clasificado: ${data.legal_area}`, ts: Date.now(), done: true }],
                }));

              } else if (data.type === "agent") {
                agentUsed = data.agent_used;
                // Don't set message content yet — wait for final_stream_start
                setOrchState(prev => ({
                  ...prev,
                  phase: 'thinking',
                  activeAgents: data.legal_area ? [data.legal_area] : prev.activeAgents,
                  statusText: `${data.agent_used} trabajando...`,
                }));

              } else if (data.type === "status") {
                // Update the orchestrator status bar (NOT in message content)
                setOrchestratorStatus(data.content);
                const msg = data.content || "";
                const step = data.step || "";

                // Map backend step names to orchestrator phases and timeline entries
                const stepMap: Record<string, { phase: typeof orchState.phase; icon: string; text: string }> = {
                  classify:          { phase: 'classifying',  icon: '🧠', text: 'Analizando consulta...' },
                  classify_done:     { phase: 'classifying',  icon: '🎯', text: msg },
                  rag:               { phase: 'retrieving',   icon: '📚', text: 'Buscando normativa peruana...' },
                  rag_done:          { phase: 'retrieving',   icon: '📖', text: msg },
                  primary_working:   { phase: 'thinking',     icon: '⚖️', text: msg },
                  primary_done:      { phase: 'thinking',     icon: '✅', text: msg },
                  evaluating:        { phase: 'evaluating',   icon: '🔍', text: 'Verificando cobertura de la respuesta...' },
                  eval_pass:         { phase: 'evaluating',   icon: '✅', text: msg },
                  secondary_working: { phase: 'enriching',    icon: '👨‍⚖️', text: msg },
                  secondary_done:    { phase: 'enriching',    icon: '✅', text: msg },
                  synthesizing:      { phase: 'synthesizing', icon: '🔄', text: 'Integrando análisis multi-agente...' },
                  synthesis_done:    { phase: 'synthesizing', icon: '✅', text: 'Síntesis completada' },
                  streaming:         { phase: 'done',         icon: '✨', text: 'Mostrando respuesta...' },
                };

                const mapped = step ? stepMap[step] : null;
                if (mapped) {
                  setOrchState(prev => ({
                    ...prev,
                    phase: mapped.phase,
                    statusText: msg,
                    steps: [...prev.steps, {
                      icon: mapped.icon,
                      text: mapped.text.length > 85 ? mapped.text.slice(0, 82) + '...' : mapped.text,
                      ts: Date.now(),
                      done: step.endsWith('_done') || step === 'eval_pass' || step === 'streaming',
                    }],
                  }));
                } else {
                  // Generic status fallback (no step field)
                  setOrchState(prev => ({
                    ...prev,
                    statusText: msg,
                  }));
                }

              } else if (data.type === "orchestrator_thinking") {
                // Show the "meeting convened" in the orchestrator panel only.
                // Mark secondary agents as active so they appear highlighted.
                const secAreas: string[] = data.secondary_areas || [];
                setOrchState(prev => ({
                  ...prev,
                  phase: 'enriching',
                  statusText: data.content || 'Reunión de especialistas convocada...',
                  evaluationReason: data.reason || prev.evaluationReason,
                  secondaryAreas: secAreas.length > 0 ? secAreas : prev.secondaryAreas,
                  activeAgents: [...new Set([...prev.activeAgents, ...secAreas])],
                  steps: [...prev.steps, {
                    icon: '📋',
                    text: data.content
                      ? (data.content.length > 85 ? data.content.slice(0, 82) + '...' : data.content)
                      : 'Reunión de especialistas convocada',
                    ts: Date.now(),
                    done: false,
                  }],
                }));

              } else if (data.type === "done") {
                latencyMs = data.latency_ms;
                setOrchestratorStatus(null); // clear status bar
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? {
                          ...m,
                          agent_used: agentUsed,
                          latency_ms: latencyMs,
                          citations: data.citations || m.citations,
                          model_used: data.model_used || undefined,
                        }
                      : m
                  )
                );
                // Update orchState with final stats
                setOrchState(prev => ({
                  ...prev,
                  latencyMs: data.latency_ms || 0,
                  citationCount: data.citations?.length || 0,
                  modelUsed: data.model_used || prev.modelUsed,
                }));

                // Capture conversation_id from backend
                if (data.conversation_id) {
                  setCurrentConversationId(data.conversation_id);
                }

                // Refresh sidebar history
                const doneToken = getToken();
                if (doneToken) {
                  fetchHistory(doneToken);
                }

              } else if (data.type === "error") {
                // Backend error (classify failure, agent failure, API key issues)
                const errMsg = data.message || "Error del servidor";
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, content: m.content || errMsg }
                      : m
                  )
                );
                setOrchState(prev => ({
                  ...prev,
                  statusText: `⚠️ ${errMsg.slice(0, 100)}`,
                  steps: [...prev.steps, { icon: '❌', text: errMsg.slice(0, 80), ts: Date.now(), done: true }],
                }));
              }
            } catch {
              // skip malformed SSE
            }
          }
        }
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : null;
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? {
                ...m,
                content: errorMsg
                  ? errorMsg
                  : "Lo siento, hubo un error al procesar tu consulta. Verifica que el servidor API este corriendo en http://localhost:8000",
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      setOrchestratorStatus(null); // always clear status on completion or error
    }
  };

  // ---------------------------------------------------------------------------
  // Template helpers
  // ---------------------------------------------------------------------------
  const activeTemplates =
    selectedArea && QUERY_TEMPLATES[selectedArea]
      ? QUERY_TEMPLATES[selectedArea]
      : QUERY_TEMPLATES.general;

  const visibleTemplates = showAllTemplates
    ? activeTemplates
    : activeTemplates.slice(0, 4);

  // ---------------------------------------------------------------------------
  // Context usage calculation
  // ---------------------------------------------------------------------------
  const MAX_CONTEXT_MESSAGES = 20; // last N messages sent to LLM
  const MAX_CONTEXT_TOKENS = 128000; // approximate max for most models
  const estimatedTokens = messages.reduce((acc, m) => acc + Math.ceil(m.content.length / 3.5), 0);
  const contextMessagesPercent = Math.min(100, Math.round((messages.length / MAX_CONTEXT_MESSAGES) * 100));
  const contextTokensPercent = Math.min(100, Math.round((estimatedTokens / MAX_CONTEXT_TOKENS) * 100));
  const contextPercent = Math.max(contextMessagesPercent, contextTokensPercent);
  const contextColor =
    contextPercent >= 80 ? "bg-red-500" : contextPercent >= 50 ? "bg-amber-500" : "bg-primary";
  const contextTextColor =
    contextPercent >= 80 ? "text-red-400" : contextPercent >= 50 ? "text-amber-400" : "text-primary/70";

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <AppLayout>
      {/* Skip to main content — visible on focus for keyboard/screen reader users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:bg-primary-container focus:text-background focus:px-4 focus:py-2 focus:rounded-lg focus:text-sm focus:font-medium"
      >
        {t("skip.content")}
      </a>

      {/* Global keyboard shortcuts handler */}
      <KeyboardShortcuts
        onNewChat={startNewChat}
        onToggleSidebar={() => {}}
        onFocusSearch={() => inputRef.current?.focus()}
        onSendMessage={() => {
          if (!isLoading && input.trim()) {
            const form = inputRef.current?.closest("form");
            form?.requestSubmit();
          }
        }}
      />

      {/* Outer flex row: [Chat Area] [Orchestration Panel] */}
      <div className="flex h-full overflow-hidden">

      {/* Main Chat Area */}
      <div id="main-content" className="flex flex-col flex-1 min-w-0 overflow-hidden bg-surface-container-lowest">
        {/* Header */}
        <header className="h-14 flex items-center justify-between px-4 lg:px-6 bg-surface shrink-0">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary-container" aria-hidden="true" />
            <span className="text-sm font-medium text-on-surface">
              {conversationTitle
                ? conversationTitle
                : selectedArea
                ? `Consulta dirigida: ${LEGAL_AREAS.find((a) => a.id === selectedArea)?.name}`
                : "Consulta general — el orquestador determinara el area"}
            </span>
            {currentConversationId && (
              <span className="hidden text-[10px] text-on-surface/20" aria-hidden="true">
                #{currentConversationId.slice(0, 8)}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <NotificationBell token={authToken} />
            <label htmlFor="model-select" className="sr-only">{t("model.select")}</label>
            {availableModels.length === 0 ? (
              <a
                href="/configuracion"
                className="text-xs text-primary/70 hover:text-primary border border-primary/20 rounded-lg px-2 py-1 transition-colors"
                title="Configurar clave de IA"
              >
                Cargando modelos...
              </a>
            ) : (
              <select
                id="model-select"
                value={selectedModel}
                onChange={(e) => {
                  const newModel = e.target.value;
                  setSelectedModel(newModel);
                  localStorage.setItem("pref_default_model", newModel);
                  // Reset reasoning if new model doesn't support it
                  if (!modelSupportsThinking(newModel) && reasoningEffort !== null) {
                    setReasoningEffort(null);
                  }
                }}
                aria-label={t("model.select")}
                className="bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg px-2 py-1 text-xs text-on-surface/60 focus:outline-none focus:border-primary/50"
              >
                {MODEL_CATALOG
                  .filter((model) => availableModels.includes(model.id))
                  .map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.name}
                    </option>
                  ))}
              </select>
            )}

            {/* Thinking depth selector — how deep the AI analyzes */}
            {(() => {
              const hasThinking = modelSupportsThinking(selectedModel);
              return (
                <div
                  className="flex items-center gap-0.5 bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg p-0.5"
                  title={hasThinking
                    ? "Controla qué tan profundo analiza la IA tu consulta"
                    : "Este modelo no soporta modos de razonamiento — usa velocidad estándar"
                  }
                >
                  {[
                    { value: null, label: "Auto", tooltip: "La IA decide el nivel de análisis según tu consulta" },
                    { value: "low", label: "Rápida", tooltip: "Respuesta directa y veloz — ideal para preguntas simples" },
                    { value: "medium", label: "Moderada", tooltip: "Análisis balanceado — buen nivel sin demoras largas" },
                    { value: "high", label: "Profunda", tooltip: "Análisis exhaustivo — ideal para casos complejos con múltiples áreas" },
                  ].map((opt) => {
                    const isDisabled = !hasThinking && opt.value !== null;
                    return (
                      <button
                        key={opt.label}
                        onClick={() => !isDisabled && setReasoningEffort(opt.value)}
                        title={isDisabled
                          ? `${MODEL_CATALOG.find(m => m.id === selectedModel)?.name || selectedModel} no soporta modo "${opt.label}"`
                          : opt.tooltip
                        }
                        disabled={isDisabled}
                        className={`px-2 py-0.5 rounded text-[10px] font-medium transition-all ${
                          isDisabled
                            ? "text-surface-container-high cursor-not-allowed"
                            : reasoningEffort === opt.value
                              ? "bg-secondary-container text-secondary"
                              : "bg-surface-container-low text-on-surface/60 hover:text-on-surface hover:bg-surface-container-high"
                        }`}
                      >
                        {opt.label}
                      </button>
                    );
                  })}
                </div>
              );
            })()}
          </div>
        </header>

        {/* Context usage bar — shows how loaded the conversation context is */}
        {messages.length > 0 && (
          <div className="px-4 lg:px-6 py-1.5 bg-surface-container-lowest flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <svg className="w-3 h-3 text-on-surface/20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2Zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8Z" opacity="0.3"/>
                <path d="M12 6v6l4 2"/>
              </svg>
              <span className="text-[10px] text-on-surface/30 uppercase tracking-wider">Contexto</span>
            </div>
            <div className="flex-1 max-w-xs">
              <div className="w-full bg-surface-container-low rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full transition-all duration-500 ${contextColor}`}
                  style={{ width: `${Math.max(2, contextPercent)}%` }}
                />
              </div>
            </div>
            <span className={`text-[10px] font-mono ${contextTextColor}`}>
              {messages.length} msgs · ~{estimatedTokens.toLocaleString()} tokens
            </span>
            {contextPercent >= 80 && (
              <span className="text-[10px] text-red-400/70 animate-pulse">
                Contexto casi lleno
              </span>
            )}
          </div>
        )}

        {/* Orchestrator status bar — shows during deliberative loop */}
        {orchestratorStatus && isLoading && (
          <div className="px-4 lg:px-6 py-2 bg-primary-container/5 flex items-center gap-2">
            <Loader2 className="w-3.5 h-3.5 text-primary-container animate-spin" aria-hidden="true" />
            <span className="text-xs text-primary-container/80">{orchestratorStatus}</span>
          </div>
        )}

        {/* No models at all — something is wrong */}
        {availableModels.length === 0 && authToken && (
          <div className="mx-4 mt-3 mb-0 p-4 bg-surface-container border border-[rgba(79,70,51,0.15)] rounded-lg shrink-0 flex items-center gap-3">
            <Lock className="w-4 h-4 text-primary-container shrink-0" />
            <p className="text-sm text-on-surface/60">
              Esta beta funciona con API key propia por usuario. Configurá tu clave para habilitar el chat en{" "}
              <a href="/configuracion" className="text-primary hover:text-primary/80 font-medium">
                Configuración → API Keys
              </a>
            </p>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 bg-surface-container-lowest" aria-live="polite" aria-label="Mensajes de la consulta">
          {messages.length === 0 ? (
            // Empty state with logo
            <div className="h-full flex flex-col items-center justify-center text-center">
              <img src="/brand/logo-full.png" className="w-32 mx-auto mb-6 opacity-40" alt="TukiJuris" />
              <h2 className="font-['Newsreader'] text-2xl font-bold mb-2 text-on-surface tracking-tight">¿En qué puedo ayudarte?</h2>
              <p className="text-on-surface/50 max-w-md mb-8 text-sm leading-relaxed">
                Plataforma jurídica inteligente especializada en derecho
                peruano. Consulta normativa, jurisprudencia y recibí
                orientación legal con agentes de IA especializados.
              </p>

              {/* Template section */}
              <div className="w-full max-w-lg">
                {selectedArea && QUERY_TEMPLATES[selectedArea] && (
                  <p className="text-[10px] text-on-surface/30 mb-3 uppercase tracking-[0.2em]">
                    {LEGAL_AREAS.find((a) => a.id === selectedArea)?.name} — consultas frecuentes
                  </p>
                )}
                <div className="grid grid-cols-2 gap-3">
                  {visibleTemplates.map((tpl) => (
                    <button
                      key={tpl.label}
                      onClick={() => setInput(tpl.query)}
                      className="text-left text-sm p-3 rounded-lg border border-[rgba(79,70,51,0.15)] bg-surface-container text-on-surface/60 hover:border-primary/30 hover:text-on-surface hover:bg-surface-container-high transition-all duration-200"
                    >
                      <span className="font-medium text-on-surface block mb-0.5 text-xs">
                        {tpl.label}
                      </span>
                      <span className="text-xs text-on-surface/40 line-clamp-2">
                        {tpl.query}
                      </span>
                    </button>
                  ))}
                </div>

                {activeTemplates.length > 4 && (
                  <button
                    onClick={() => setShowAllTemplates((v) => !v)}
                    className="mt-3 flex items-center gap-1.5 text-xs text-on-surface/40 hover:text-on-surface/70 transition-colors mx-auto"
                  >
                    {showAllTemplates ? (
                      <>
                        <ChevronUp className="w-3.5 h-3.5" />
                        Ver menos
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-3.5 h-3.5" />
                        Ver mas ({activeTemplates.length - 4} adicionales)
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
                >
                  {msg.role === "assistant" && (
                    <div className="w-8 h-8 rounded-lg bg-primary-container/10 flex items-center justify-center shrink-0 mt-1">
                      <Bot className="w-4 h-4 text-primary-container" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] ${
                      msg.role === "user"
                        ? "bg-surface-container-low text-on-surface rounded-lg rounded-tr-sm px-4 py-3"
                        : "bg-surface border border-[rgba(79,70,51,0.15)] rounded-lg rounded-tl-sm px-4 py-3"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <>
                        {/* Render markdown for assistant messages */}
                        <div
                          className="text-sm text-on-surface leading-relaxed"
                          dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                        />
                      </>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    )}

                    {/* Citations section — collapsible list of legal references */}
                    {msg.citations && msg.citations.length > 0 && (
                      <details className="mt-2 pt-2">
                        <summary className="text-[10px] text-on-surface/40 cursor-pointer hover:text-on-surface/70 transition-colors select-none">
                          📜 {msg.citations.length} referencia{msg.citations.length > 1 ? 's' : ''} normativa{msg.citations.length > 1 ? 's' : ''}
                        </summary>
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          {msg.citations.slice(0, 20).map((cit, i) => (
                            <span
                              key={i}
                              className="text-[9px] bg-surface-container-low text-on-surface/60 rounded-lg px-1.5 py-0.5"
                              title={cit.text}
                            >
                              {cit.text.length > 40 ? cit.text.slice(0, 37) + '...' : cit.text}
                            </span>
                          ))}
                        </div>
                      </details>
                    )}

                    {msg.agent_used && (
                      <div className="mt-2 pt-2 flex items-center justify-between text-xs text-on-surface/40">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[10px] uppercase bg-surface-container-high text-on-surface/60 rounded-lg px-2 py-0.5">{msg.agent_used}</span>
                          {msg.model_used && (
                            <span className="text-[10px] text-on-surface/30">{msg.model_used.split('/').pop()}</span>
                          )}
                          {msg.latency_ms && <span className="text-on-surface/30">{(msg.latency_ms / 1000).toFixed(1)}s</span>}
                          {msg.is_multi_area && (
                            <span className="text-[10px] bg-primary/10 text-primary border border-primary/20 rounded-lg px-1.5 py-0.5">
                              Multi-área
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleFeedback(msg.id, "thumbs_up")}
                            aria-label={t("chat.feedback.good")}
                            className={`p-1 rounded-lg hover:bg-surface-container-low transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 ${
                              msg.feedback === "thumbs_up"
                                ? "text-green-400"
                                : "text-on-surface/30 hover:text-primary"
                            }`}
                          >
                            <ThumbsUp className="w-3.5 h-3.5" aria-hidden="true" />
                          </button>
                          <button
                            onClick={() => handleFeedback(msg.id, "thumbs_down")}
                            aria-label={t("chat.feedback.bad")}
                            className={`p-1 rounded-lg hover:bg-surface-container-low transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 ${
                              msg.feedback === "thumbs_down"
                                ? "text-red-400"
                                : "text-on-surface/30 hover:text-[#F87171]"
                            }`}
                          >
                            <ThumbsDown className="w-3.5 h-3.5" aria-hidden="true" />
                          </button>
                          <button
                            onClick={() => handleToggleBookmark(msg)}
                            className={`p-1 rounded-lg hover:bg-surface-container-low transition-colors ${
                              msg.is_bookmarked
                                ? "text-primary hover:text-primary/80"
                                : "text-on-surface/30 hover:text-primary"
                            }`}
                            aria-label={msg.is_bookmarked ? "Quitar marcador" : "Guardar como marcador"}
                          >
                            <Bookmark
                              className="w-3.5 h-3.5"
                              fill={msg.is_bookmarked ? "currentColor" : "none"}
                            />
                          </button>
                          <button
                            onClick={() => handleDownloadPDF(msg)}
                            aria-label={t("chat.download.pdf")}
                            className="p-1 rounded-lg hover:bg-surface-container-low text-on-surface/30 hover:text-on-surface transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30"
                          >
                            <Download className="w-3.5 h-3.5" aria-hidden="true" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-lg bg-surface-container-high flex items-center justify-center shrink-0 mt-1">
                      <User className="w-4 h-4 text-on-surface/60" />
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-3" role="status" aria-label={t("chat.analyzing")}>
                  <div className="w-8 h-8 rounded-lg bg-primary-container/10 flex items-center justify-center shrink-0" aria-hidden="true">
                    <Loader2 className="w-4 h-4 text-primary-container animate-spin" />
                  </div>
                  <div className="bg-surface border border-[rgba(79,70,51,0.15)] rounded-lg rounded-tl-sm px-4 py-3">
                    <p className="text-sm text-on-surface/50 animate-pulse">{t("chat.analyzing")}</p>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* TODO: Sprint 33 — Daily usage indicator when /api/billing/daily-usage endpoint is ready */}

        {/* Formatting toolbar + Input */}
        <div className="p-4 bg-surface shrink-0">
          <div className="max-w-3xl mx-auto">
            {/* Formatting toolbar */}
            <div className="flex items-center gap-1 mb-2 px-1">
              <span className="text-[10px] text-on-surface/30 mr-1 uppercase tracking-[0.2em]">Formato:</span>
              {[
                { icon: Bold, label: "Negrita", prefix: "**", suffix: "**", placeholder: "texto" },
                { icon: Italic, label: "Cursiva", prefix: "*", suffix: "*", placeholder: "texto" },
                { icon: List, label: "Lista", prefix: "\n- ", suffix: "", placeholder: "elemento" },
                { icon: Code, label: "Codigo", prefix: "`", suffix: "`", placeholder: "codigo" },
              ].map(({ icon: Icon, label, prefix, suffix, placeholder }) => (
                <button
                  key={label}
                  type="button"
                  title={label}
                  onClick={() => {
                    if (inputRef.current) {
                      insertMarkdownSyntax(inputRef.current, prefix, suffix, placeholder, setInput);
                    }
                  }}
                  aria-label={label}
                  className="p-1.5 rounded-lg text-on-surface/30 hover:text-on-surface/70 hover:bg-surface-container-low transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30"
                >
                  <Icon className="w-3.5 h-3.5" aria-hidden="true" />
                </button>
              ))}

              {/* File attachment */}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,.webp,.txt"
                onChange={handleFileUpload}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                className="p-1.5 rounded-lg text-on-surface/40 hover:text-primary hover:bg-surface-container-low transition-colors disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-primary/30 ml-1"
                title="Adjuntar archivo"
                aria-label="Adjuntar archivo"
              >
                {uploading ? (
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Paperclip className="w-4 h-4" aria-hidden="true" />
                )}
              </button>
            </div>

            {/* Attached file preview */}
            {attachedFile && (
              <div className="mb-2 flex items-center gap-2 px-3 py-2 bg-surface-container-low border border-[rgba(79,70,51,0.15)] rounded-lg">
                <FileText className="w-4 h-4 text-primary flex-shrink-0" aria-hidden="true" />
                <span className="text-xs text-on-surface/60 truncate flex-1">{attachedFile.name}</span>
                <button
                  type="button"
                  onClick={() => setAttachedFile(null)}
                  className="text-on-surface/40 hover:text-on-surface/70 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 rounded-lg"
                  aria-label="Quitar archivo adjunto"
                >
                  <X className="w-3 h-3" aria-hidden="true" />
                </button>
              </div>
            )}

            {/* Input form */}
            <form onSubmit={handleSubmit} aria-busy={isLoading} aria-label="Formulario de consulta legal" className="flex gap-3">
              <label htmlFor="chat-input" className="sr-only">{t("chat.placeholder")}</label>
              <textarea
                id="chat-input"
                ref={inputRef}
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e as unknown as React.FormEvent);
                  }
                }}
                aria-label={t("chat.placeholder")}
                className="flex-1 bg-surface-container border border-[rgba(79,70,51,0.15)] rounded-lg px-4 py-3 text-sm placeholder-on-surface/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 resize-none min-h-[52px] max-h-32 overflow-y-auto text-on-surface transition-colors"
                disabled={isLoading || availableModels.length === 0}
                placeholder={availableModels.length === 0 ? "Configurá tu API key para usar el chat en esta beta" : t("chat.placeholder")}
                style={{ height: "auto" }}
                onInput={(e) => {
                  const el = e.currentTarget;
                  el.style.height = "auto";
                  el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
                }}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim() || availableModels.length === 0}
                aria-label={t("chat.send")}
                className="bg-gradient-to-tr from-primary to-primary-container hover:from-primary/90 hover:to-primary-container/90 disabled:from-surface-container-low disabled:to-surface-container-low disabled:text-on-surface/20 text-on-primary rounded-lg px-4 py-3 transition-all self-end focus:outline-none focus:ring-2 focus:ring-primary/40"
              >
                <Send className="w-5 h-5" aria-hidden="true" />
              </button>
              <HelpPopover onShowShortcuts={() => setShowShortcutsModal(true)} />
            </form>
            <p className="text-[10px] text-on-surface/25 mt-1.5 px-1">
              Enter para enviar, Shift+Enter para nueva linea
            </p>
          </div>
        </div>
      </div>{/* end #main-content */}

      {/* ------------------------------------------------------------------ */}
      {/* Orchestration Panel — Right side (lg+ only)                         */}
      {/* ------------------------------------------------------------------ */}
      {showOrchPanel && (
        <aside className="hidden lg:flex w-72 bg-surface flex-col overflow-hidden flex-shrink-0">
          {/* Header */}
          <div className="px-4 py-3 bg-surface-container-low flex items-center justify-between shrink-0">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-on-surface/40">Orquestador</span>
              {/* Model + Reasoning badge */}
              {orchState.modelUsed && orchState.phase !== 'idle' && (
                <div className="flex items-center gap-1.5 mt-1">
                  <span className="text-[9px] bg-surface-container-high text-on-surface/60 rounded-lg px-1.5 py-0.5">
                    {orchState.modelUsed.split('/').pop()}
                  </span>
                  {orchState.reasoningLevel && (
                    <span className={`text-[9px] rounded-lg px-1.5 py-0.5 ${
                      orchState.reasoningLevel === 'Profunda' ? 'bg-[#EF4444]/10 text-[#EF4444]' :
                      orchState.reasoningLevel === 'Moderada' ? 'bg-[#F59E0B]/10 text-[#F59E0B]' :
                      orchState.reasoningLevel === 'Rápida'   ? 'bg-[#34D399]/10 text-[#34D399]' :
                      'bg-surface-container-high text-on-surface/40'
                    }`}>
                      {orchState.reasoningLevel}
                    </span>
                  )}
                </div>
              )}
            </div>
            <button
              onClick={() => setShowOrchPanel(false)}
              className="text-on-surface/40 hover:text-on-surface/70 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 rounded-lg"
              aria-label="Cerrar panel de orquestación"
            >
              <PanelRightClose className="w-4 h-4" />
            </button>
          </div>

          {/* Brain / Orchestrator node */}
          <div className="px-4 py-5 flex flex-col items-center bg-surface shrink-0">
            <div className={`w-14 h-14 rounded-lg flex items-center justify-center transition-all duration-500 ${
              orchState.phase === 'idle'       ? 'bg-surface-container-low text-on-surface/30' :
              orchState.phase === 'evaluating' ? 'bg-[#A78BFA]/20 text-[#A78BFA] animate-pulse shadow-lg shadow-[#A78BFA]/20' :
              orchState.phase === 'done'       ? 'bg-[#34D399]/20 text-[#34D399]' :
              'bg-primary/20 text-primary animate-pulse shadow-lg shadow-primary/20'
            }`}>
              {orchState.phase === 'done'
                ? <CheckCircle2 className="w-7 h-7" />
                : <Brain className="w-7 h-7" />
              }
            </div>
            <p className="mt-2 text-[11px] text-on-surface/60 text-center leading-snug max-w-[220px]">
              {orchState.statusText || 'Esperando consulta...'}
            </p>
            {/* Stats row: confidence + latency + citations */}
            {(orchState.confidence > 0 || orchState.latencyMs > 0) && (
              <div className="flex items-center gap-3 mt-2">
                {orchState.confidence > 0 && (
                  <span className="text-[10px] text-on-surface/40">
                    🎯 {Math.round(orchState.confidence * 100)}%
                  </span>
                )}
                {orchState.latencyMs > 0 && (
                  <span className="text-[10px] text-on-surface/40">
                    ⏱ {(orchState.latencyMs / 1000).toFixed(1)}s
                  </span>
                )}
                {orchState.citationCount > 0 && (
                  <span className="text-[10px] text-on-surface/40">
                    📜 {orchState.citationCount}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Evaluation reason — why extra agents were called */}
          {orchState.evaluationReason && orchState.phase === 'done' && (
            <div className="px-4 py-2.5 bg-surface-container-low shrink-0">
              <p className="text-[10px] uppercase tracking-[0.2em] text-[#A78BFA]/70 mb-1">Motivo de convocatoria</p>
              <p className="text-[10px] text-on-surface/60 leading-relaxed">{orchState.evaluationReason}</p>
            </div>
          )}

          {/* Agent Grid */}
          <div className="flex-1 overflow-y-auto px-3 py-3">
            <p className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 px-1 mb-2">
              Agentes Especializados
            </p>
            <div className="space-y-1">
              {LEGAL_AREAS.map(area => {
                const isActive    = orchState.activeAgents.includes(area.id);
                const isPrimary   = orchState.primaryArea === area.id;
                const isSecondary = orchState.secondaryAreas.includes(area.id);
                const AreaIcon    = area.icon;
                return (
                  <div
                    key={area.id}
                    className={`flex items-center gap-2.5 px-3 py-1.5 rounded-lg transition-all duration-500 ${
                      isPrimary   ? 'bg-primary/10 border border-primary/20' :
                      isSecondary ? 'bg-[#A78BFA]/10 border border-[#A78BFA]/20' :
                      isActive    ? 'bg-surface-container-high border border-transparent' :
                      'border border-transparent'
                    }`}
                  >
                    {/* Status dot */}
                    <div className={`w-2 h-2 rounded-full flex-shrink-0 transition-all duration-500 ${
                      isPrimary   ? 'bg-primary shadow-sm shadow-primary/50' :
                      isSecondary ? 'bg-[#A78BFA] shadow-sm shadow-[#A78BFA]/50' :
                      isActive    ? 'bg-[#34D399]' :
                      'bg-surface-container-high'
                    } ${isActive && orchState.phase !== 'done' ? 'animate-pulse' : ''}`} />

                    {/* Agent icon */}
                    <AreaIcon className={`w-3.5 h-3.5 flex-shrink-0 transition-all duration-500 ${
                      isPrimary   ? 'text-primary' :
                      isSecondary ? 'text-[#A78BFA]' :
                      isActive    ? 'text-on-surface' :
                      'text-on-surface/20'
                    }`} />

                    {/* Agent name + role tag */}
                    <span className={`text-[11px] truncate flex-1 transition-all duration-500 ${
                      isActive || isSecondary ? 'text-on-surface' : 'text-on-surface/25'
                    }`}>
                      {area.label}
                      {isPrimary && orchState.phase === 'done' && (
                        <span className="ml-1.5 text-[9px] text-primary/70">Principal</span>
                      )}
                      {isSecondary && orchState.phase === 'done' && (
                        <span className="ml-1.5 text-[9px] text-[#A78BFA]/70">Complementó</span>
                      )}
                    </span>

                    {/* Typing indicator while active */}
                    {isActive && orchState.phase !== 'done' && (
                      <div className="ml-auto flex gap-0.5">
                        <div className="w-1 h-1 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-1 h-1 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-1 h-1 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    )}

                    {/* Completed check */}
                    {(isActive || isSecondary) && orchState.phase === 'done' && (
                      <CheckCircle2 className={`ml-auto w-3.5 h-3.5 flex-shrink-0 ${
                        isPrimary ? 'text-primary' :
                        isSecondary ? 'text-[#A78BFA]' :
                        'text-[#34D399]'
                      }`} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Steps timeline with relative timestamps */}
          {orchState.steps.length > 0 && (
            <div className="bg-surface-container-low px-4 py-3 max-h-48 overflow-y-auto shrink-0">
              <p className="text-[10px] uppercase tracking-[0.2em] text-on-surface/40 mb-2">Timeline</p>
              <div className="space-y-1">
                {orchState.steps.map((step, i) => {
                  const elapsed = orchState.startTime > 0 ? ((step.ts - orchState.startTime) / 1000).toFixed(1) : null;
                  return (
                    <div key={i} className="flex items-center gap-2 text-[11px]">
                      <span className="w-4 text-center">{step.icon}</span>
                      <span className={`flex-1 truncate ${step.done ? 'text-on-surface/50' : 'text-primary'}`}>
                        {step.text}
                      </span>
                      {elapsed && (
                        <span className="text-[9px] text-on-surface/25 tabular-nums flex-shrink-0">{elapsed}s</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </aside>
      )}

      {/* Toggle button when panel is hidden — desktop */}
      {!showOrchPanel && (
        <button
          onClick={() => setShowOrchPanel(true)}
          className="fixed right-0 top-1/2 -translate-y-1/2 z-30 bg-surface border border-[rgba(79,70,51,0.15)] rounded-l-lg p-2 hover:bg-surface-container-low transition hidden lg:flex items-center"
          title="Mostrar Orquestador"
          aria-label="Mostrar panel del orquestador"
        >
          <Brain className="w-5 h-5 text-on-surface/40" />
        </button>
      )}

      {/* Mobile orchestrator — floating status pill (visible during processing on small screens) */}
      {orchState.phase !== 'idle' && (
        <div className="lg:hidden fixed bottom-20 left-1/2 -translate-x-1/2 z-30">
          <button
            onClick={() => setShowOrchPanel(p => !p)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border shadow-lg transition-all ${
              orchState.phase === 'done'
                ? 'bg-surface border-[#34D399]/20 text-[#34D399]'
                : 'bg-surface border-primary/20 text-primary animate-pulse'
            }`}
          >
            {orchState.phase === 'done' ? <CheckCircle2 className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
            <span className="text-[11px] max-w-[200px] truncate">
              {orchState.phase === 'done'
                ? `✅ ${orchState.activeAgents.length} agentes · ${(orchState.latencyMs / 1000).toFixed(1)}s`
                : orchState.statusText.slice(0, 40)
              }
            </span>
          </button>
        </div>
      )}

      {/* Mobile orchestrator drawer — slides up from bottom */}
      {showOrchPanel && (
        <div className="lg:hidden fixed inset-0 z-40" onClick={() => setShowOrchPanel(false)}>
          <div className="absolute inset-0 bg-black/50" />
          <div
            className="absolute bottom-0 left-0 right-0 bg-surface rounded-t-lg max-h-[70vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}
          >
            {/* Drag handle */}
            <div className="flex justify-center py-2">
              <div className="w-10 h-1 rounded-full bg-surface-container-high" />
            </div>
            {/* Compact mobile content */}
            <div className="px-4 pb-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-on-surface/40">Orquestador</span>
                <div className="flex items-center gap-2">
                  {orchState.modelUsed && (
                    <span className="text-[9px] bg-surface-container-high text-on-surface/60 rounded-lg px-1.5 py-0.5">
                      {orchState.modelUsed.split('/').pop()}
                    </span>
                  )}
                  {orchState.reasoningLevel && (
                    <span className="text-[9px] bg-surface-container-high text-on-surface/40 rounded-lg px-1.5 py-0.5">
                      {orchState.reasoningLevel}
                    </span>
                  )}
                </div>
              </div>
              {/* Stats row */}
              <div className="flex items-center gap-4 mb-3">
                {orchState.confidence > 0 && <span className="text-[10px] text-on-surface/40">🎯 {Math.round(orchState.confidence * 100)}%</span>}
                {orchState.latencyMs > 0 && <span className="text-[10px] text-on-surface/40">⏱ {(orchState.latencyMs / 1000).toFixed(1)}s</span>}
                {orchState.citationCount > 0 && <span className="text-[10px] text-on-surface/40">📜 {orchState.citationCount} refs</span>}
                <span className="text-[10px] text-on-surface/40">👥 {orchState.activeAgents.length} agentes</span>
              </div>
              {/* Active agents only */}
              <div className="flex flex-wrap gap-1.5 mb-3">
                {LEGAL_AREAS.filter(a => orchState.activeAgents.includes(a.id) || orchState.secondaryAreas.includes(a.id)).map(area => {
                  const isPrimary = orchState.primaryArea === area.id;
                  const isSecondary = orchState.secondaryAreas.includes(area.id);
                  return (
                    <span key={area.id} className={`text-[10px] rounded-lg px-2 py-0.5 border ${
                      isPrimary ? 'bg-primary/10 border-primary/20 text-primary' :
                      isSecondary ? 'bg-[#A78BFA]/10 border-[#A78BFA]/20 text-[#A78BFA]' :
                      'bg-surface-container-low border-transparent text-on-surface/60'
                    }`}>
                      {area.name} {isPrimary ? '★' : ''}
                    </span>
                  );
                })}
              </div>
              {/* Evaluation reason */}
              {orchState.evaluationReason && (
                <p className="text-[10px] text-on-surface/60 leading-relaxed mb-3 border-l-2 border-[#A78BFA]/30 pl-2">
                  {orchState.evaluationReason}
                </p>
              )}
              {/* Timeline compact */}
              {orchState.steps.length > 0 && (
                <div className="space-y-1">
                  {orchState.steps.slice(-6).map((step, i) => {
                    const elapsed = orchState.startTime > 0 ? ((step.ts - orchState.startTime) / 1000).toFixed(1) : null;
                    return (
                      <div key={i} className="flex items-center gap-2 text-[10px]">
                        <span>{step.icon}</span>
                        <span className={`flex-1 truncate ${step.done ? 'text-on-surface/50' : 'text-primary'}`}>{step.text}</span>
                        {elapsed && <span className="text-[9px] text-on-surface/25">{elapsed}s</span>}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      </div>{/* end outer flex row */}

      {/* Context menu — right-click on conversation */}
      {contextMenu && (
        <div
          className="fixed z-50 bg-surface-container border border-[rgba(79,70,51,0.15)] rounded-lg shadow-lg shadow-black/40 py-1 min-w-[180px]"
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          <p className="px-4 py-1.5 text-[10px] text-on-surface/40 truncate max-w-[180px] uppercase tracking-[0.2em]">
            {contextMenu.convTitle ?? "Consulta"}
          </p>
          <div className="h-px bg-surface-container-high mt-1" />
          <ContextMenuItem
            icon={<Pencil className="w-3.5 h-3.5" />}
            label="Renombrar"
            loading={contextActionLoading === "rename"}
            onClick={() => {
              const newTitle = prompt("Nuevo nombre:", contextMenu.convTitle ?? "");
              if (!newTitle || !authToken) { setContextMenu(null); return; }
              setContextActionLoading("rename");
              fetch(`${API_URL}/api/conversations/${contextMenu.convId}/rename`, {
                method: "PUT",
                headers: { Authorization: `Bearer ${authToken}`, "Content-Type": "application/json" },
                body: JSON.stringify({ title: newTitle }),
              }).then(() => fetchHistory(authToken!)).finally(() => {
                setContextActionLoading(null);
                setContextMenu(null);
              });
            }}
          />
          <ContextMenuItem
            icon={<Pin className="w-3.5 h-3.5" />}
            label={chatHistory.find((c) => c.id === contextMenu.convId)?.is_pinned ? "Desfijar" : "Fijar"}
            loading={contextActionLoading === "pin"}
            onClick={() => contextAction(contextMenu.convId, "pin")}
          />
          <ContextMenuItem
            icon={<Archive className="w-3.5 h-3.5" />}
            label="Archivar"
            loading={contextActionLoading === "archive"}
            onClick={() => contextAction(contextMenu.convId, "archive")}
          />
          <ContextMenuItem
            icon={copiedShareId === contextMenu.convId ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Share2 className="w-3.5 h-3.5" />}
            label={copiedShareId === contextMenu.convId ? "Enlace copiado" : "Compartir"}
            loading={contextActionLoading === "share"}
            onClick={() => contextShare(contextMenu.convId)}
          />
          <div className="h-px bg-surface-container-high my-1" />
          <ContextMenuItem
            icon={<Trash2 className="w-3.5 h-3.5" />}
            label="Eliminar"
            loading={contextActionLoading === "delete"}
            danger
            onClick={() => {
              if (!confirm("Eliminar esta conversacion?")) { setContextMenu(null); return; }
              contextAction(contextMenu.convId, "", "DELETE");
            }}
          />
        </div>
      )}
    </AppLayout>
  );
}

// ---------------------------------------------------------------------------
// Root export — wraps ChatPage in Suspense (required for useSearchParams)
// ---------------------------------------------------------------------------
export default function Home() {
  return (
    <Suspense fallback={null}>
      <ChatPage />
    </Suspense>
  );
}

// ---------------------------------------------------------------------------
// Context menu item helper
// ---------------------------------------------------------------------------
function ContextMenuItem({
  icon,
  label,
  loading,
  onClick,
  danger,
}: {
  icon: React.ReactNode;
  label: string;
  loading: boolean;
  onClick: () => void;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-xs transition-colors disabled:opacity-50 ${
        danger
          ? "text-[#F87171] hover:bg-[#F87171]/10"
          : "text-on-surface hover:bg-surface-container-high"
      }`}
    >
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : icon}
      {label}
    </button>
  );
}
