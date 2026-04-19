"use client";

import { useState, useRef, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Loader2,
  Lock,
  Pin,
  Archive,
  Share2,
  Trash2,
  Pencil,
  Check,
  PanelRightOpen,
} from "lucide-react";
import type { Message, ChatHistory, ContextMenu, OrchestratorState } from "./chat/types";
import { INITIAL_ORCH_STATE } from "./chat/types";
import { ChatEmptyState } from "./chat/components/ChatEmptyState";
import { ChatBubble } from "./chat/components/ChatBubble";
import { ChatComposer } from "./chat/components/ChatComposer";
import { ChatHeader } from "./chat/components/ChatHeader";
import { OrchestratorPanel } from "./chat/components/OrchestratorPanel";
import KeyboardShortcuts from "@/components/KeyboardShortcuts";
import { AppLayout } from "@/components/AppLayout";
import { useAuth, useHasFeature } from "@/lib/auth/AuthContext";
import { UpsellModal } from "@/components/UpsellModal";
import { t } from "@/lib/i18n";
import { MODEL_CATALOG, availableModelsForProviders, modelSupportsThinking } from "@/lib/models";





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
  const [contextMenu, setContextMenu] = useState<ContextMenu | null>(null);
  const [contextActionLoading, setContextActionLoading] = useState<string | null>(null);
  const [copiedShareId, setCopiedShareId] = useState<string | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [conversationTitle, setConversationTitle] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
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
  const [orchState, setOrchState] = useState<OrchestratorState>(INITIAL_ORCH_STATE);

  const { authFetch } = useAuth();
  const hasFileUpload = useHasFeature("file_upload");
  const hasPdfExport = useHasFeature("pdf_export");
  const [upsellFeature, setUpsellFeature] = useState<string | null>(null);

  // Beta BYOK-only: fetch available models strictly from the user's own keys.
  useEffect(() => {
    authFetch(`/api/keys/llm-keys`)
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
    try {
      const res = await authFetch(`/api/conversations/${id}`);
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
      try {
        await authFetch(`/api/feedback/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
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
  const fetchHistory = useCallback(async () => {
    try {
      const res = await authFetch(`/api/conversations/?status=active&limit=30`);
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
    fetchHistory();
  }, [fetchHistory]);

  // Context menu action helper
  const contextAction = useCallback(async (
    convId: string,
    endpoint: string,
    method = "PUT"
  ) => {
    setContextActionLoading(endpoint);
    try {
      const res = await authFetch(`/api/conversations/${convId}/${endpoint}`, {
        method,
      });
      if (!res.ok) return;
      await fetchHistory();
    } finally {
      setContextActionLoading(null);
      setContextMenu(null);
    }
  }, [fetchHistory]);

  const contextShare = useCallback(async (convId: string) => {
    setContextActionLoading("share");
    try {
      const res = await authFetch(`/api/conversations/${convId}/share`, {
        method: "POST",
      });
      if (!res.ok) return;
      const data = await res.json();
      const appBase = process.env.NEXT_PUBLIC_APP_URL || "https://tukijuris.net.pe";
      const url = data.url ?? `${appBase}/compartido/${data.share_id}`;
      await navigator.clipboard.writeText(url);
      setCopiedShareId(convId);
      setTimeout(() => setCopiedShareId(null), 2500);
      await fetchHistory();
    } finally {
      setContextActionLoading(null);
      setContextMenu(null);
    }
  }, [fetchHistory]);

  const startNewChat = useCallback(() => {
    setMessages([]);
    setSelectedArea(null);
    setCurrentConversationId(null);
    setConversationTitle(null);
    setAttachedFile(null);
  }, []);

  const handleFileUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!hasFileUpload) {
        setUpsellFeature("file_upload");
        return;
      }
      const file = e.target.files?.[0];
      if (!file) return;

      setUploading(true);
      try {
        const formData = new FormData();
        formData.append("file", file);
        if (currentConversationId) {
          formData.append("conversation_id", currentConversationId);
        }

        const res = await authFetch(`/api/upload/`, {
          method: "POST",
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
      }
    },
    [currentConversationId]
  );

  const handleDownloadPDF = async (assistantMsg: Message) => {
    if (!hasPdfExport) {
      setUpsellFeature("pdf_export");
      return;
    }
    const msgIndex = messages.findIndex((m) => m.id === assistantMsg.id);
    const precedingUser = messages
      .slice(0, msgIndex)
      .reverse()
      .find((m) => m.role === "user");

    const query = precedingUser?.content ?? "Consulta legal";
    const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, "");

    try {
      const res = await authFetch(`/api/export/consultation/pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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

    try {
      await authFetch(`/api/bookmarks/${msg.id}`, { method: "PUT" });
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
      const res = await authFetch(`/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
                fetchHistory();

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

  const orchestratorRail = showOrchPanel ? (
    <OrchestratorPanel variant="rail" orchState={orchState} onClose={() => setShowOrchPanel(false)} />
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
        <ChatHeader
          conversationTitle={conversationTitle}
          selectedArea={selectedArea}
          currentConversationId={currentConversationId}
          orchPhase={orchState.phase}
          orchStatusText={orchState.statusText}
          onShowOrchPanel={() => setShowOrchPanel(true)}
        />

        {/* No models at all — something is wrong */}
        {availableModels.length === 0 && (
          <div className="mx-4 mt-3 mb-0 p-4 bg-surface-container border-2 border-outline-variant/30 rounded-lg shrink-0 flex items-center gap-3">
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
            <ChatEmptyState selectedArea={selectedArea} onSelectTemplate={setInput} />
          ) : (
            <div className="mx-auto max-w-3xl space-y-6">
              {messages.map((msg) => (
                <ChatBubble
                  key={msg.id}
                  message={msg}
                  onFeedback={handleFeedback}
                  onToggleBookmark={handleToggleBookmark}
                  onDownloadPDF={handleDownloadPDF}
                />
              ))}
              {isLoading && (
                <div className="flex gap-2.5" role="status" aria-label={t("chat.analyzing")}>
                  <div className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-primary/10" aria-hidden="true">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                  </div>
                  <div className="panel-base rounded-2xl rounded-tl-md border-2 border-outline-variant/30 px-4 py-3">
                    <p className="animate-pulse text-sm text-on-surface/50">{t("chat.analyzing")}</p>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* TODO: Sprint 33 — Daily usage indicator when /api/billing/daily-usage endpoint is ready */}

        <ChatComposer
          input={input}
          onInputChange={setInput}
          onSubmit={handleSubmit}
          isLoading={isLoading}
          disabled={availableModels.length === 0}
          disabledPlaceholder="Configurá tu API key..."
          selectedArea={selectedArea}
          onClearArea={() => setSelectedArea(null)}
          selectedModel={selectedModel}
          onModelChange={(m) => {
            setSelectedModel(m);
            localStorage.setItem("pref_default_model", m);
            if (!modelSupportsThinking(m)) setReasoningEffort(null);
          }}
          availableModels={availableModels}
          reasoningEffort={reasoningEffort}
          onReasoningChange={setReasoningEffort}
          attachedFile={attachedFile}
          onFileUpload={handleFileUpload}
          onRemoveFile={() => setAttachedFile(null)}
          uploading={uploading}
          inputRef={inputRef}
        />
      </div>{/* end #main-content */}

      {/* Toggle button — desktop, shown when panel is hidden */}
      {!showOrchPanel && (
        <button
          onClick={() => setShowOrchPanel(true)}
          className="fixed right-0 top-1/2 -translate-y-1/2 z-30 bg-surface border border-outline-variant/30 rounded-l-lg p-2 hover:bg-surface-container-low transition hidden md:flex items-center"
          title="Mostrar análisis del caso"
          aria-label="Mostrar panel de análisis del caso"
        >
          <PanelRightOpen className="w-5 h-5 text-on-surface/40" />
        </button>
      )}

      {/* Tablet/mobile orchestrator drawer */}
      {showOrchPanel && (
        <div className="xl:hidden fixed inset-0 z-40" onClick={() => setShowOrchPanel(false)}>
          <div className="absolute inset-0 bg-black/50" />
          <div
            className="absolute bottom-0 left-0 right-0 md:bottom-0 md:left-auto md:right-0 md:top-0 md:w-[24rem] md:rounded-none"
            onClick={e => e.stopPropagation()}
          >
            <OrchestratorPanel variant="sheet" orchState={orchState} onClose={() => setShowOrchPanel(false)} />
          </div>
        </div>
      )}

      </div>{/* end outer flex row */}

      {/* Context menu — right-click on conversation */}
      {contextMenu && (
        <div
          className="fixed z-50 bg-surface-container border-2 border-outline-variant/30 rounded-lg shadow-lg shadow-black/40 py-1 min-w-[180px]"
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
              if (!newTitle) { setContextMenu(null); return; }
              setContextActionLoading("rename");
              authFetch(`/api/conversations/${contextMenu.convId}/rename`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: newTitle }),
              }).then(() => fetchHistory()).finally(() => {
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
      {/* Feature upsell modal — shown when user tries a gated action */}
      {upsellFeature && (
        <UpsellModal
          feature={upsellFeature}
          onClose={() => setUpsellFeature(null)}
        />
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
          ? "text-error hover:bg-error/10"
          : "text-on-surface hover:bg-surface-container-high"
      }`}
    >
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : icon}
      {label}
    </button>
  );
}
