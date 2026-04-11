"use client";

import { useState, useRef, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  Send,
  Bot,
  User,
  Loader2,
  BookOpen,
  Shield,
  Briefcase,
  Landmark,
  Building2,
  ThumbsUp,
  ThumbsDown,
  FileCheck,
  Globe,
  Lock,
  Download,
  Bookmark,
  Type,
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
import KeyboardShortcuts from "@/components/KeyboardShortcuts";
import HelpPopover from "@/components/HelpPopover";
import { AppLayout } from "@/components/AppLayout";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";
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
  { id: "civil", name: "Civil", label: "Derecho Civil", description: "Contratos, daños, bienes y obligaciones", icon: BookOpen, color: "text-blue-400" },
  { id: "penal", name: "Penal", label: "Derecho Penal", description: "Delitos, denuncias y responsabilidad penal", icon: Shield, color: "text-red-400" },
  { id: "laboral", name: "Laboral", label: "Derecho Laboral", description: "Trabajo, despidos e indemnizaciones", icon: Briefcase, color: "text-green-400" },
  { id: "tributario", name: "Tributario", label: "Derecho Tributario", description: "Impuestos y obligaciones fiscales", icon: Calculator, color: "text-yellow-400" },
  { id: "constitucional", name: "Constitucional", label: "Derecho Constitucional", description: "Derechos fundamentales y garantías", icon: Landmark, color: "text-purple-400" },
  { id: "administrativo", name: "Administrativo", label: "Derecho Administrativo", description: "Trámites, sanciones y organismos públicos", icon: Building2, color: "text-orange-400" },
  { id: "corporativo", name: "Corporativo", label: "Derecho Comercial", description: "Empresas, sociedades y actividad comercial", icon: Store, color: "text-cyan-400" },
  { id: "registral", name: "Registral", label: "Derecho Registral", description: "Inscripciones, títulos y registros", icon: FileCheck, color: "text-pink-400" },
  { id: "comercio_exterior", name: "Comercio Ext.", label: "Comercio Exterior", description: "Operaciones internacionales y aduanas", icon: Globe, color: "text-teal-400" },
  { id: "compliance", name: "Compliance", label: "Compliance / Ambiental", description: "Normativas, controles y riesgo regulatorio", icon: TreePine, color: "text-indigo-400" },
  { id: "competencia", name: "Competencia/PI", label: "Competencia / Propiedad Intelectual", description: "Marcas, patentes y competencia desleal", icon: Heart, color: "text-amber-400" },
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
  const [attachedFile, setAttachedFile] = useState<{
    id: string;
    name: string;
    type: string;
    preview: string;
  } | null>(null);
  const [uploading, setUploading] = useState(false);
  const [orchestratorStatus, setOrchestratorStatus] = useState<string | null>(null);
  const [showFormattingTools, setShowFormattingTools] = useState(false);
  const [isAnalysisTimelineOpen, setIsAnalysisTimelineOpen] = useState(false);

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

  const selectedAreaMeta = selectedArea ? LEGAL_AREAS.find((a) => a.id === selectedArea) : null;
  const handleShowShortcuts = useCallback(() => {}, []);

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

  const involvedAreas = LEGAL_AREAS.filter(
    (area) => orchState.activeAgents.includes(area.id) || orchState.secondaryAreas.includes(area.id)
  );
  const highlightedAreas = LEGAL_AREAS.filter(
    (area) => orchState.primaryArea === area.id || orchState.secondaryAreas.includes(area.id)
  );
  const processSteps = [
    { id: "received", label: "Nos contás tu caso", done: orchState.steps.length > 0 },
    { id: "detected", label: "Detectamos áreas relevantes", done: orchState.activeAgents.length > 0 },
    { id: "prepared", label: "Preparamos una orientación más precisa", done: orchState.phase === "done" },
  ];
  const currentAnalysisStep = [...orchState.steps].reverse().find((step) => !step.done) ?? orchState.steps[orchState.steps.length - 1] ?? null;
  const currentStepElapsed =
    currentAnalysisStep && orchState.startTime > 0
      ? ((currentAnalysisStep.ts - orchState.startTime) / 1000).toFixed(1)
      : null;
  const radarAreas = (highlightedAreas.length > 0 ? highlightedAreas : involvedAreas.length > 0 ? involvedAreas : LEGAL_AREAS.slice(0, 3)).slice(0, 3);
  const analysisHeadline =
    orchState.phase === "done"
      ? "Análisis completado"
      : orchState.phase === "evaluating"
        ? "Estamos revisando tu consulta"
        : "Listo para revisar tu consulta";
  const analysisSupportingText =
    orchState.phase === "done"
      ? highlightedAreas.length > 0
        ? `Detectamos ${highlightedAreas.map((area) => area.label).join(", ")} como ${highlightedAreas.length === 1 ? "área relevante" : "áreas relevantes"} para tu caso.`
        : "Terminamos la revisión inicial de tu consulta."
      : orchState.phase === "evaluating"
        ? orchState.statusText || "Estamos identificando los temas legales que podrían intervenir en tu caso."
        : "Cuando nos cuentes tu situación, vamos a identificar qué áreas legales podrían intervenir para orientarte mejor.";

  const getAreaPresentation = (areaId: string) => {
    const isPrimary = orchState.primaryArea === areaId;
    const isSecondary = orchState.secondaryAreas.includes(areaId);
    const isActive = orchState.activeAgents.includes(areaId);

    if (isPrimary) {
      return {
        badge: "Prioritaria",
        containerClass: "border-primary/30 bg-primary/10 shadow-[0_0_0_1px_rgba(201,169,97,0.08)]",
        iconClass: "text-primary bg-primary/15",
        badgeClass: "bg-primary/15 text-primary",
      };
    }

    if (isSecondary) {
      return {
        badge: "Detectada",
        containerClass: "border-[#A78BFA]/30 bg-[#A78BFA]/10",
        iconClass: "text-[#A78BFA] bg-[#A78BFA]/15",
        badgeClass: "bg-[#A78BFA]/15 text-[#C4B5FD]",
      };
    }

    if (isActive) {
      return {
        badge: "En revisión",
        containerClass: "border-emerald-400/20 bg-emerald-400/10",
        iconClass: "text-emerald-300 bg-emerald-400/10",
        badgeClass: "bg-emerald-400/10 text-emerald-300",
      };
    }

    return {
      badge: "Disponible",
      containerClass: "border-[rgba(255,255,255,0.04)] bg-surface-container-low/60",
      iconClass: "text-on-surface/55 bg-surface-container-high/70",
      badgeClass: "bg-surface-container-high/70 text-on-surface/45",
    };
  };

  const orchestratorRail = showOrchPanel ? (
    <aside className="flex h-full w-[22rem] border-l border-[rgba(79,70,51,0.15)] bg-surface flex-col overflow-hidden flex-shrink-0">
      <div className="px-4 py-4 bg-surface-container-low flex items-start justify-between shrink-0 border-b border-[rgba(255,255,255,0.04)]">
        <div className="max-w-[260px]">
          <span className="text-[10px] font-bold uppercase tracking-[0.22em] text-primary/75">Análisis de tu caso</span>
          <p className="mt-2 text-[12px] text-on-surface/72 leading-relaxed">
            Identificamos las áreas legales que podrían intervenir para orientarte mejor.
          </p>
        </div>
        <button
          onClick={() => setShowOrchPanel(false)}
          className="text-on-surface/40 hover:text-on-surface/70 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30 rounded-lg"
          aria-label="Cerrar panel de análisis"
        >
          <PanelRightClose className="w-4 h-4" />
        </button>
      </div>

      <div className="px-4 py-4 bg-surface shrink-0 border-b border-[rgba(255,255,255,0.04)]">
        <div className="overflow-hidden rounded-[1.6rem] border border-[rgba(255,255,255,0.06)] bg-[radial-gradient(circle_at_top,rgba(167,139,250,0.18),transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0))] p-4 shadow-[0_24px_60px_rgba(0,0,0,0.28)]">
          <div className="flex items-start gap-4">
            <div className="relative flex h-24 w-24 shrink-0 items-center justify-center rounded-[1.4rem] border border-white/6 bg-[#111723]">
              <svg viewBox="0 0 120 120" className="h-20 w-20" aria-hidden="true">
                <defs>
                  <linearGradient id="analysis-ring" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#A78BFA" />
                    <stop offset="100%" stopColor="#34D399" />
                  </linearGradient>
                </defs>
                <circle cx="60" cy="60" r="38" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1.5" />
                <circle cx="60" cy="60" r="28" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
                {radarAreas.map((area, index) => {
                  const positions = [
                    { x: 60, y: 18 },
                    { x: 92, y: 76 },
                    { x: 28, y: 78 },
                  ];
                  const point = positions[index];
                  return (
                    <g key={area.id}>
                      <line x1="60" y1="60" x2={point.x} y2={point.y} stroke="url(#analysis-ring)" strokeOpacity="0.45" strokeWidth="1.5" strokeDasharray="4 4">
                        <animate attributeName="stroke-dashoffset" values="0;-16" dur="1.8s" repeatCount="indefinite" />
                      </line>
                      <circle cx={point.x} cy={point.y} r="6" fill={index === 0 && orchState.phase !== "idle" ? "#34D399" : "#A78BFA"}>
                        <animate attributeName="r" values="5.5;7.5;5.5" dur={`${1.8 + index * 0.25}s`} repeatCount="indefinite" />
                        <animate attributeName="opacity" values="0.7;1;0.7" dur={`${1.8 + index * 0.25}s`} repeatCount="indefinite" />
                      </circle>
                    </g>
                  );
                })}
                <circle cx="60" cy="60" r="12" fill={orchState.phase === "done" ? "#34D399" : "#C9A961"} fillOpacity="0.2" stroke="url(#analysis-ring)" strokeWidth="2.5">
                  <animate attributeName="r" values="11;13;11" dur="2.4s" repeatCount="indefinite" />
                </circle>
                {orchState.phase === "done" ? (
                  <path d="M54 60l5 5 9-12" fill="none" stroke="#34D399" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                ) : (
                  <path d="M52 47c-4 2-6 6-6 11 0 8 6 14 14 14 3 0 6-1 8-3m-2-22c4 2 6 6 6 11" fill="none" stroke="#C9A961" strokeWidth="3" strokeLinecap="round" />
                )}
              </svg>
              <div className="pointer-events-none absolute inset-0 rounded-[1.4rem] bg-[radial-gradient(circle,rgba(201,169,97,0.12),transparent_60%)]" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[11px] uppercase tracking-[0.18em] text-on-surface/45">Estado del análisis</p>
              <h3 className="mt-1 text-[1.15rem] font-semibold tracking-[-0.02em] text-on-surface">{analysisHeadline}</h3>
              <p className="mt-1.5 text-[11px] text-on-surface/68 leading-relaxed">{analysisSupportingText}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {radarAreas.map((area, index) => (
                  <span key={area.id} className={`rounded-full px-2.5 py-1 text-[10px] ${index === 0 ? "bg-primary/12 text-primary" : "bg-white/5 text-on-surface/55"}`}>
                    {area.name}
                  </span>
                ))}
              </div>
            </div>
          </div>
          {(orchState.confidence > 0 || orchState.latencyMs > 0 || orchState.citationCount > 0) && (
            <div className="mt-3 flex flex-wrap gap-2">
              {orchState.confidence > 0 && (
                <span className="rounded-full bg-surface-container-high px-2.5 py-1 text-[10px] text-on-surface/60">
                  Confianza {Math.round(orchState.confidence * 100)}%
                </span>
              )}
              {orchState.latencyMs > 0 && (
                <span className="rounded-full bg-surface-container-high px-2.5 py-1 text-[10px] text-on-surface/60">
                  {(orchState.latencyMs / 1000).toFixed(1)}s
                </span>
              )}
              {orchState.citationCount > 0 && (
                <span className="rounded-full bg-surface-container-high px-2.5 py-1 text-[10px] text-on-surface/60">
                  {orchState.citationCount} referencias
                </span>
              )}
            </div>
          )}
          <div className="mt-4 space-y-2 rounded-2xl border border-white/5 bg-black/10 p-3">
            <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/45">Cómo funciona</p>
            {processSteps.map((step) => {
              const done = step.done;
              return (
                <div key={step.id} className="flex items-center gap-2.5 text-[11px]">
                  <span
                    className={`flex h-5 w-5 items-center justify-center rounded-full border text-[10px] ${
                      done
                        ? "border-primary/30 bg-primary/10 text-primary"
                        : "border-[rgba(255,255,255,0.06)] bg-surface text-on-surface/40"
                    }`}
                  >
                    {done ? "✓" : processSteps.findIndex((item) => item.id === step.id) + 1}
                  </span>
                  <span className={done ? "text-on-surface/80" : "text-on-surface/50"}>{step.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {orchState.evaluationReason && orchState.phase === "done" && (
        <div className="px-4 py-3 bg-surface-container-low shrink-0 border-b border-[rgba(255,255,255,0.04)]">
          <p className="text-[10px] uppercase tracking-[0.18em] text-[#A78BFA]/75 mb-1">Por qué estas áreas</p>
          <p className="text-[11px] text-on-surface/65 leading-relaxed">{orchState.evaluationReason}</p>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/45 mb-2">Áreas legales involucradas</p>
          <p className="text-[11px] text-on-surface/55 leading-relaxed mb-3">
            Estas áreas se activan según el contenido de tu consulta. No todas participan siempre.
          </p>
        </div>
        <div className="space-y-2">
          {LEGAL_AREAS.map((area) => {
            const AreaIcon = area.icon;
            const areaPresentation = getAreaPresentation(area.id);
            return (
              <div
                key={area.id}
                className={`rounded-2xl border px-3 py-3 transition-all duration-500 ${areaPresentation.containerClass}`}
              >
                <div className="flex items-start gap-3">
                  <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-all duration-500 ${areaPresentation.iconClass}`}>
                    <AreaIcon className="w-4 h-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-[12px] font-medium text-on-surface">{area.label}</p>
                        <p className="mt-1 text-[10px] leading-relaxed text-on-surface/55">{area.description}</p>
                      </div>
                      <span className={`shrink-0 rounded-full px-2 py-1 text-[9px] font-medium ${areaPresentation.badgeClass}`}>
                        {areaPresentation.badge}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="rounded-2xl border border-[rgba(255,255,255,0.05)] bg-surface-container-low/70 p-4">
          <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/45">Resultado del análisis</p>
          {orchState.phase === "done" && involvedAreas.length > 0 ? (
            <>
              <p className="mt-2 text-sm font-medium text-on-surface">
                Detectamos {involvedAreas.map((area) => area.label).join(", ")}
              </p>
              <p className="mt-1 text-[11px] leading-relaxed text-on-surface/60">
                Estas áreas aparecen porque encontramos elementos de tu consulta que podrían requerir una revisión combinada.
              </p>
            </>
          ) : (
            <>
              <p className="mt-2 text-sm font-medium text-on-surface">Todavía no recibimos una consulta</p>
              <p className="mt-1 text-[11px] leading-relaxed text-on-surface/60">
                Apenas escribas tu caso, te mostraremos qué áreas detectamos y por qué podrían intervenir.
              </p>
            </>
          )}
        </div>
      </div>

      {orchState.steps.length > 0 && currentAnalysisStep && (
        <div className="bg-surface-container-low px-4 py-3 shrink-0 border-t border-[rgba(255,255,255,0.04)]">
          <button
            type="button"
            onClick={() => setIsAnalysisTimelineOpen((prev) => !prev)}
            className="flex w-full items-center gap-3 rounded-2xl border border-white/5 bg-white/[0.02] px-3 py-3 text-left transition hover:bg-white/[0.04]"
            aria-expanded={isAnalysisTimelineOpen}
            aria-label="Mostrar seguimiento del análisis"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <span className="text-sm">{currentAnalysisStep.icon}</span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/42">Seguimiento del análisis</p>
              <p className="mt-1 truncate text-[11px] text-on-surface/72">{currentAnalysisStep.text}</p>
            </div>
            <div className="flex items-center gap-2">
              {currentStepElapsed && <span className="text-[10px] tabular-nums text-on-surface/35">{currentStepElapsed}s</span>}
              {isAnalysisTimelineOpen ? <ChevronUp className="h-4 w-4 text-on-surface/40" /> : <ChevronDown className="h-4 w-4 text-on-surface/40" />}
            </div>
          </button>
          {isAnalysisTimelineOpen && (
            <div className="mt-2 max-h-48 overflow-y-auto rounded-2xl border border-white/5 bg-black/10 p-3">
              <div className="space-y-1.5">
                {orchState.steps.map((step, i) => {
                  const elapsed = orchState.startTime > 0 ? ((step.ts - orchState.startTime) / 1000).toFixed(1) : null;
                  const isCurrent = currentAnalysisStep.ts === step.ts && currentAnalysisStep.text === step.text;
                  return (
                    <div key={i} className={`flex items-center gap-2 rounded-xl px-2 py-1.5 text-[11px] ${isCurrent ? "bg-primary/10 text-on-surface" : "text-on-surface/55"}`}>
                      <span className="w-4 text-center">{step.icon}</span>
                      <span className={`flex-1 truncate ${isCurrent ? "text-on-surface" : step.done ? "text-on-surface/50" : "text-primary"}`}>{step.text}</span>
                      {elapsed && <span className="text-[9px] text-on-surface/25 tabular-nums flex-shrink-0">{elapsed}s</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </aside>
  ) : null;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------
  return (
    <AppLayout contentClassName="overflow-hidden" rightRail={orchestratorRail}>
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
      <div className="flex h-full min-h-0 overflow-hidden">

      {/* Main Chat Area */}
      <div id="main-content" className="flex min-h-0 flex-1 min-w-0 flex-col overflow-hidden bg-surface-container-lowest">
        {/* Header */}
        <header className="border-b border-[rgba(79,70,51,0.15)] bg-surface px-4 py-3 lg:px-6 shrink-0">
          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-primary-container" aria-hidden="true" />
                <span className="section-eyebrow text-primary">Workspace</span>
              </div>
              <div className="mt-1 flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <h1 className="truncate text-base font-medium tracking-[-0.02em] text-on-surface lg:text-lg">
                      {conversationTitle || "Chat"}
                    </h1>
                    <span className="inline-flex items-center rounded-full border border-[rgba(79,70,51,0.15)] bg-surface-container-low px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] text-on-surface/45">
                      {selectedAreaMeta ? `Consulta dirigida · ${selectedAreaMeta.name}` : "Consulta general"}
                    </span>
                    <span className="hidden text-xs text-on-surface/35 lg:inline">
                      {selectedAreaMeta
                        ? `${selectedAreaMeta.name} prioritaria · apoyos automáticos`
                        : "El orquestador decide área principal y apoyos"}
                    </span>
                  </div>
                </div>

                {orchState.phase !== "idle" && (
                  <button
                    type="button"
                    onClick={() => setShowOrchPanel(true)}
                    className="xl:hidden group flex w-[17rem] max-w-[46vw] items-center gap-2.5 rounded-[1.25rem] border border-primary/15 bg-[radial-gradient(circle_at_left,rgba(201,169,97,0.12),transparent_38%),linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0))] px-3 py-2 text-left shadow-[0_12px_28px_rgba(0,0,0,0.08)] transition hover:border-primary/25 hover:bg-primary/5"
                    aria-label="Abrir razonamiento del análisis"
                  >
                    <div className={`relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
                      orchState.phase === "done" ? "bg-emerald-400/12 text-emerald-500" : "bg-primary/12 text-primary"
                    }`}>
                      <span className={`absolute inset-0 rounded-full ${orchState.phase === "done" ? "bg-emerald-400/10" : "bg-primary/10"} animate-ping`} />
                      {orchState.phase === "done" ? <CheckCircle2 className="relative h-4 w-4" /> : <Brain className="relative h-4 w-4" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[10px] font-semibold uppercase tracking-[0.18em] text-primary/80">Mirá el razonamiento</p>
                      <p className="mt-0.5 truncate text-[10px] text-on-surface/58">
                        {currentAnalysisStep?.text || analysisHeadline}
                      </p>
                    </div>
                  </button>
                )}
              </div>
            </div>
            {currentConversationId && (
              <div className="hidden items-center gap-2 md:flex">
                <span className="rounded-lg border border-[rgba(79,70,51,0.15)] bg-surface-container-low px-2 py-1 text-[10px] text-on-surface/35">
                  #{currentConversationId.slice(0, 8)}
                </span>
                <ShellUtilityActions />
              </div>
            )}
            {!currentConversationId && <div className="hidden md:flex"><ShellUtilityActions /></div>}
          </div>
        </header>

        {(messages.length > 0 || (orchestratorStatus && isLoading)) && (
          <div className="flex flex-wrap items-center gap-3 border-b border-[rgba(79,70,51,0.08)] bg-surface-container-lowest px-4 py-2 lg:px-6">
            {messages.length > 0 && (
              <>
                <div className="flex items-center gap-1.5">
                  <svg className="w-3 h-3 text-on-surface/20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2Zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8Z" opacity="0.3"/>
                    <path d="M12 6v6l4 2"/>
                  </svg>
                  <span className="text-[10px] text-on-surface/30 uppercase tracking-wider">Contexto</span>
                </div>
                <div className="flex-1 max-w-xs min-w-32">
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
                  <span className="rounded-full border border-red-400/20 bg-red-400/10 px-2 py-0.5 text-[10px] text-red-400/80">
                    Contexto casi lleno
                  </span>
                )}
              </>
            )}

            {orchestratorStatus && isLoading && (
              <div className="inline-flex items-center gap-2 rounded-full border border-primary-container/20 bg-primary-container/5 px-2.5 py-1">
                <Loader2 className="w-3.5 h-3.5 text-primary-container animate-spin" aria-hidden="true" />
                <span className="text-[11px] text-primary-container/80">{orchestratorStatus}</span>
              </div>
            )}
          </div>
        )}

        {/* No models at all — something is wrong */}
        {availableModels.length === 0 && authToken && (
          <div className="mx-4 mt-3 mb-0 p-4 bg-surface-container border border-[rgba(79,70,51,0.15)] rounded-lg shrink-0 flex items-center gap-3">
            <Lock className="w-4 h-4 text-primary-container shrink-0" />
            <p className="text-sm text-on-surface/60">
              Esta beta funciona con API key propia por usuario. Configurá tu clave para habilitar el chat en{" "}
              <Link href="/configuracion" className="text-primary hover:text-primary/80 font-medium">
                Configuración → API Keys
              </Link>
            </p>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto bg-surface-container-lowest px-3 py-3 sm:px-4 md:px-6 md:py-5" aria-live="polite" aria-label="Mensajes de la consulta">
          {messages.length === 0 ? (
            // Empty state with logo
            <div className="mx-auto flex h-full w-full max-w-3xl flex-col justify-start text-center">
              <div className="panel-base mb-4 rounded-[1.75rem] px-5 py-5 sm:px-6 md:mb-6 md:px-8 md:py-6">
                <Image src="/brand/logo-full.png" className="mx-auto mb-3 w-16 opacity-70 md:mb-4 md:w-20" alt="TukiJuris" width={80} height={80} />
                <p className="section-eyebrow justify-center text-primary/80">Asistente legal inteligente</p>
                <h2 className="mt-2 font-['Newsreader'] text-[2.15rem] leading-[1.02] font-bold tracking-[-0.04em] text-on-surface md:text-4xl">¿En qué puedo ayudarte?</h2>
                <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-on-surface/60 md:text-base md:leading-8">
                  Consultá normativa, jurisprudencia y orientación legal sobre derecho peruano sin perder tiempo buscando desde cero.
                </p>
              </div>

              {/* Template section */}
              <div className="w-full max-w-2xl">
                {selectedArea && QUERY_TEMPLATES[selectedArea] && (
                  <p className="section-eyebrow mb-3 text-on-surface/35">
                    {LEGAL_AREAS.find((a) => a.id === selectedArea)?.name} — consultas frecuentes
                  </p>
                )}
                {!selectedArea && (
                  <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.18em] text-on-surface/38">
                    Sugerencias rápidas
                  </p>
                )}
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {visibleTemplates.map((tpl) => (
                    <button
                      key={tpl.label}
                      onClick={() => setInput(tpl.query)}
                      className="panel-base rounded-[1.4rem] p-4 text-left text-sm text-on-surface/65 transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/30 hover:text-on-surface"
                    >
                      <span className="mb-1 block text-[1.05rem] font-semibold leading-6 text-on-surface">
                        {tpl.label}
                      </span>
                      <span className="line-clamp-2 text-sm leading-6 text-on-surface/45">
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

        {/* Composer */}
        <div className="border-t border-[rgba(79,70,51,0.15)] bg-surface px-3 py-3 shrink-0 sm:px-4 sm:py-4">
          <div className="panel-raised mx-auto max-w-4xl rounded-[1.75rem] p-2.5 sm:p-3.5">
            <div className="mb-2.5 flex flex-wrap items-center gap-2 border-b border-[rgba(79,70,51,0.12)] pb-2.5 sm:mb-3 sm:pb-3">
              {selectedAreaMeta ? (
                <button
                  type="button"
                  onClick={() => setSelectedArea(null)}
                  className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.18em] text-primary"
                >
                  {selectedAreaMeta.name}
                  <X className="h-3 w-3" />
                </button>
              ) : (
                <span className="inline-flex items-center rounded-full border border-[rgba(79,70,51,0.15)] bg-surface px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] text-on-surface/45">
                  Consulta general
                </span>
              )}

              <label htmlFor="model-select" className="sr-only">{t("model.select")}</label>
              {availableModels.length === 0 ? (
                <a
                  href="/configuracion"
                  className="text-xs text-primary/70 hover:text-primary border border-primary/20 rounded-lg px-2 py-1 transition-colors"
                  title="Configurar clave de IA"
                >
                  Configurar modelos
                </a>
              ) : (
                <select
                  id="model-select"
                  value={selectedModel}
                  onChange={(e) => {
                    const newModel = e.target.value;
                    setSelectedModel(newModel);
                    localStorage.setItem("pref_default_model", newModel);
                    if (!modelSupportsThinking(newModel) && reasoningEffort !== null) {
                      setReasoningEffort(null);
                    }
                  }}
                  aria-label={t("model.select")}
                  className="control-surface min-w-[10rem] rounded-xl px-3 py-2 text-xs text-on-surface/75 focus:outline-none focus:border-primary/50"
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

              {(() => {
                const hasThinking = modelSupportsThinking(selectedModel);
                return (
                  <div
                    className="control-surface flex items-center gap-0.5 rounded-xl p-0.5"
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
                          className={`px-2 py-1 rounded text-[10px] font-medium transition-all ${
                            isDisabled
                              ? "text-surface-container-high cursor-not-allowed"
                              : reasoningEffort === opt.value
                                ? "bg-secondary-container text-secondary"
                                : "bg-surface text-on-surface/60 hover:text-on-surface hover:bg-surface-container-high/80"
                          }`}
                        >
                          {opt.label}
                        </button>
                      );
                    })}
                  </div>
                );
              })()}

              <div className="ml-auto flex items-center gap-1 relative">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,.webp,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={() => setShowFormattingTools((v) => !v)}
                  className="control-surface rounded-xl p-2 text-on-surface/45 hover:text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30"
                  title="Opciones de formato"
                  aria-label="Opciones de formato"
                >
                  <Type className="w-4 h-4" aria-hidden="true" />
                </button>
                {showFormattingTools && (
                  <div className="panel-raised absolute bottom-full right-0 z-20 mb-2 w-auto min-w-[220px] rounded-2xl p-2">
                    <div className="mb-1 px-2 pt-1 text-[10px] uppercase tracking-[0.2em] text-on-surface/35">
                      Formato rápido
                    </div>
                    <div className="flex flex-wrap items-center gap-1">
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
                            setShowFormattingTools(false);
                          }}
                          aria-label={label}
                          className="control-surface inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs text-on-surface/65 hover:text-on-surface"
                        >
                          <Icon className="w-3.5 h-3.5" aria-hidden="true" />
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="control-surface rounded-xl p-2 text-on-surface/45 hover:text-primary disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-primary/30"
                  title="Adjuntar archivo"
                  aria-label="Adjuntar archivo"
                >
                  {uploading ? (
                    <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  ) : (
                    <Paperclip className="w-4 h-4" aria-hidden="true" />
                  )}
                </button>
                <HelpPopover onShowShortcuts={handleShowShortcuts} />
              </div>
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
            <form onSubmit={handleSubmit} aria-busy={isLoading} aria-label="Formulario de consulta legal" className="flex items-end gap-2.5 sm:gap-3">
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
                className="panel-base flex-1 resize-none rounded-2xl px-4 py-3 text-sm text-on-surface transition-colors placeholder-on-surface/30 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 min-h-[52px] max-h-28 overflow-y-auto sm:min-h-[56px] sm:max-h-32"
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
                className="gold-gradient self-end rounded-2xl px-4 py-3 text-on-primary shadow-[0_14px_30px_rgba(0,0,0,0.18)] transition-all hover:opacity-95 disabled:bg-surface-container-low disabled:text-on-surface/20 focus:outline-none focus:ring-2 focus:ring-primary/40"
              >
                <Send className="w-5 h-5" aria-hidden="true" />
              </button>
            </form>
            <p className="mt-1.5 px-1 text-[10px] text-on-surface/25 sm:mt-2">
              Enter para enviar, Shift+Enter para nueva linea
            </p>
          </div>
        </div>
      </div>{/* end #main-content */}

      {/* Toggle button when panel is hidden — desktop */}
      {!showOrchPanel && (
        <button
          onClick={() => setShowOrchPanel(true)}
          className="fixed right-0 top-1/2 -translate-y-1/2 z-30 bg-surface border border-[rgba(79,70,51,0.15)] rounded-l-lg p-2 hover:bg-surface-container-low transition hidden md:flex items-center"
          title="Mostrar análisis del caso"
          aria-label="Mostrar panel de análisis del caso"
        >
          <Brain className="w-5 h-5 text-on-surface/40" />
        </button>
      )}

      {/* Tablet/mobile orchestrator drawer */}
      {showOrchPanel && (
        <div className="xl:hidden fixed inset-0 z-40" onClick={() => setShowOrchPanel(false)}>
          <div className="absolute inset-0 bg-black/50" />
          <div
            className="absolute bottom-0 left-0 right-0 bg-surface rounded-t-lg max-h-[70vh] overflow-y-auto md:bottom-0 md:left-auto md:right-0 md:top-0 md:w-[24rem] md:max-h-none md:rounded-none md:border-l md:border-[rgba(79,70,51,0.15)]"
            onClick={e => e.stopPropagation()}
          >
            {/* Drag handle */}
            <div className="flex justify-center py-2">
              <div className="w-10 h-1 rounded-full bg-surface-container-high" />
            </div>
            {/* Compact mobile content */}
            <div className="px-4 pb-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary/70">Análisis de tu caso</span>
                  <p className="mt-1 text-[11px] text-on-surface/60">Identificamos las áreas legales que podrían intervenir.</p>
                </div>
              </div>
              <div className="rounded-[1.4rem] border border-[rgba(255,255,255,0.05)] bg-[radial-gradient(circle_at_top,rgba(167,139,250,0.16),transparent_30%),linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0))] p-3 mb-3">
                <div className="mb-3 flex items-center gap-3">
                  <div className="relative flex h-16 w-16 items-center justify-center rounded-[1rem] border border-white/6 bg-[#111723]">
                    <svg viewBox="0 0 120 120" className="h-12 w-12" aria-hidden="true">
                      <defs>
                        <linearGradient id="analysis-ring-mobile" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#A78BFA" />
                          <stop offset="100%" stopColor="#34D399" />
                        </linearGradient>
                      </defs>
                      <circle cx="60" cy="60" r="34" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1.5" />
                      {radarAreas.map((area, index) => {
                        const positions = [
                          { x: 60, y: 24 },
                          { x: 88, y: 74 },
                          { x: 32, y: 74 },
                        ];
                        const point = positions[index];
                        return (
                          <g key={area.id}>
                            <line x1="60" y1="60" x2={point.x} y2={point.y} stroke="url(#analysis-ring-mobile)" strokeOpacity="0.45" strokeWidth="1.5" strokeDasharray="4 4">
                              <animate attributeName="stroke-dashoffset" values="0;-16" dur="1.8s" repeatCount="indefinite" />
                            </line>
                            <circle cx={point.x} cy={point.y} r="5.5" fill={index === 0 && orchState.phase !== "idle" ? "#34D399" : "#A78BFA"}>
                              <animate attributeName="r" values="5;7;5" dur={`${1.8 + index * 0.25}s`} repeatCount="indefinite" />
                            </circle>
                          </g>
                        );
                      })}
                      <circle cx="60" cy="60" r="10" fill="rgba(201,169,97,0.18)" stroke="url(#analysis-ring-mobile)" strokeWidth="2.5">
                        <animate attributeName="r" values="9;11;9" dur="2.4s" repeatCount="indefinite" />
                      </circle>
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/45">Estado del análisis</p>
                    <p className="mt-1 text-sm font-medium text-on-surface">{analysisHeadline}</p>
                  </div>
                </div>
                <p className="mt-1 text-[11px] leading-relaxed text-on-surface/60">{analysisSupportingText}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {orchState.confidence > 0 && <span className="rounded-full bg-surface-container-high px-2.5 py-1 text-[10px] text-on-surface/60">Confianza {Math.round(orchState.confidence * 100)}%</span>}
                  {orchState.latencyMs > 0 && <span className="rounded-full bg-surface-container-high px-2.5 py-1 text-[10px] text-on-surface/60">{(orchState.latencyMs / 1000).toFixed(1)}s</span>}
                  {orchState.citationCount > 0 && <span className="rounded-full bg-surface-container-high px-2.5 py-1 text-[10px] text-on-surface/60">{orchState.citationCount} referencias</span>}
                </div>
              </div>
              <div className="space-y-2 mb-3">
                <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/45">Áreas legales involucradas</p>
                {LEGAL_AREAS.map(area => {
                  const areaPresentation = getAreaPresentation(area.id);
                  const AreaIcon = area.icon;
                  return (
                    <div key={area.id} className={`rounded-xl border px-3 py-2 ${areaPresentation.containerClass}`}>
                      <div className="flex items-start gap-2.5">
                        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${areaPresentation.iconClass}`}>
                          <AreaIcon className="w-4 h-4" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-[11px] font-medium text-on-surface">{area.label}</span>
                            <span className={`rounded-full px-2 py-0.5 text-[9px] ${areaPresentation.badgeClass}`}>{areaPresentation.badge}</span>
                          </div>
                          <p className="mt-1 text-[10px] leading-relaxed text-on-surface/55">{area.description}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              {orchState.evaluationReason && (
                <p className="text-[10px] text-on-surface/60 leading-relaxed mb-3 border-l-2 border-[#A78BFA]/30 pl-2">
                  {orchState.evaluationReason}
                </p>
              )}
              {orchState.steps.length > 0 && currentAnalysisStep && (
                <div>
                  <button
                    type="button"
                    onClick={() => setIsAnalysisTimelineOpen((prev) => !prev)}
                    className="flex w-full items-center gap-3 rounded-2xl border border-white/5 bg-white/[0.02] px-3 py-3 text-left"
                    aria-expanded={isAnalysisTimelineOpen}
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-primary text-sm">
                      {currentAnalysisStep.icon}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-[10px] uppercase tracking-[0.18em] text-on-surface/42">Seguimiento del análisis</p>
                      <p className="mt-1 truncate text-[10px] text-on-surface/72">{currentAnalysisStep.text}</p>
                    </div>
                    {isAnalysisTimelineOpen ? <ChevronUp className="h-4 w-4 text-on-surface/40" /> : <ChevronDown className="h-4 w-4 text-on-surface/40" />}
                  </button>
                  {isAnalysisTimelineOpen && (
                    <div className="mt-2 space-y-1 rounded-2xl border border-white/5 bg-black/10 p-2.5">
                      {orchState.steps.slice(-6).map((step, i) => {
                        const elapsed = orchState.startTime > 0 ? ((step.ts - orchState.startTime) / 1000).toFixed(1) : null;
                        const isCurrent = currentAnalysisStep.ts === step.ts && currentAnalysisStep.text === step.text;
                        return (
                          <div key={i} className={`flex items-center gap-2 rounded-xl px-2 py-1.5 text-[10px] ${isCurrent ? 'bg-primary/10 text-on-surface' : 'text-on-surface/55'}`}>
                            <span>{step.icon}</span>
                            <span className={`flex-1 truncate ${isCurrent ? 'text-on-surface' : step.done ? 'text-on-surface/50' : 'text-primary'}`}>{step.text}</span>
                            {elapsed && <span className="text-[9px] text-on-surface/25">{elapsed}s</span>}
                          </div>
                        );
                      })}
                    </div>
                  )}
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
