"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  Bot,
  Brain,
  Briefcase,
  CheckCircle2,
  CircleDot,
  DollarSign,
  FileSearch,
  FileText,
  Gavel,
  Home,
  Loader2,
  Paperclip,
  Plus,
  Scale,
  Send,
  SkipForward,
  Sparkles,
  User,
  Wand2,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { AppLayout } from "@/components/AppLayout";
import { InternalPageHeader } from "@/components/shell/InternalPageHeader";
import { ShellUtilityActions } from "@/components/shell/ShellUtilityActions";
import { renderMarkdown } from "@/lib/markdown";
import { useAuth } from "@/lib/auth/AuthContext";
import { LEGAL_AREAS } from "@/app/chat/constants";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type CasePhase = "intake" | "investigation" | "analysis" | "complete";

interface CaseState {
  case_phase: CasePhase;
  case_facts: { slot: string; value: string }[];
  case_pending: string[];
  case_turn_count: number;
  case_area_hint: string;
}

interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  phase?: CasePhase;
  area?: string;
  agent?: string;
}

// ---------------------------------------------------------------------------
// Loading "razonamiento" panel — driven by real SSE events from the backend.
// Each `step` event from /api/chat/stream-case appends a row; the last row in
// state 'start' is the active one. See NODE_LABELS for the human copy.
// ---------------------------------------------------------------------------

interface LiveStep {
  node: string;
  status: "start" | "done";
  phase: string;
  meta?: Record<string, unknown>;
}

const NODE_LABELS: Record<string, { label: string; detail?: string }> = {
  // Intake phase
  intake_classify: { label: "Clasificando el área del derecho" },
  intake_template: { label: "Cargando plantilla de intake", detail: "Preguntas canónicas del área" },
  intake_llm: { label: "Personalizando preguntas según tu narrativa" },
  // Investigation phase
  investigation_extract: { label: "Extrayendo hechos y actualizando el case-file" },
  // Analysis phase (LangGraph nodes)
  classify: { label: "Re-clasificando con el case-file completo" },
  retrieve: { label: "Recuperando jurisprudencia y normativa", detail: "RAG · embeddings + FTS" },
  primary_agent: { label: "Agente principal redactando análisis" },
  evaluate: { label: "Evaluando si hace falta más especialistas" },
  enrich: { label: "Convocando agentes secundarios" },
  synthesize: { label: "Sintetizando todas las opiniones" },
  format_simple: { label: "Formateando respuesta final" },
};

function labelForNode(step: LiveStep): { label: string; detail?: string } {
  const base = NODE_LABELS[step.node] ?? { label: step.node };
  const area = step.meta?.area as string | undefined;
  if (step.node === "primary_agent" && area) {
    return { label: `Agente principal: ${area}` };
  }
  if (step.node === "retrieve" && area) {
    return { ...base, detail: `${base.detail ?? "RAG"} · área: ${area}` };
  }
  return base;
}

function ReasoningPanel({
  liveSteps,
  phase,
  model,
  reasoningEffort,
}: {
  liveSteps: LiveStep[];
  phase: CasePhase | undefined;
  model: string | null;
  reasoningEffort: string;
}) {
  // Collapse start/done pairs into a single row per node. The last row in
  // 'start' state (no matching 'done') is the active step.
  const rows = useMemo(() => {
    const ordered: { key: string; step: LiveStep; done: boolean }[] = [];
    for (const s of liveSteps) {
      const existing = ordered.find((r) => r.key === `${s.phase}:${s.node}`);
      if (existing) {
        if (s.status === "done") existing.done = true;
      } else {
        ordered.push({
          key: `${s.phase}:${s.node}`,
          step: s,
          done: s.status === "done",
        });
      }
    }
    return ordered;
  }, [liveSteps]);

  // Implicit done: every step before the last started one is finished.
  const lastStartedIdx = rows
    .map((r, i) => (r.step.status === "start" && !r.done ? i : -1))
    .filter((i) => i !== -1)
    .pop();

  return (
    <div className="card-canon-sunken p-4 text-xs">
      <div className="mb-3 flex items-center gap-2.5">
        <div className="relative h-2 w-2">
          <span className="absolute inset-0 rounded-full bg-primary" />
          <span className="absolute inset-0 animate-ping rounded-full bg-primary" />
        </div>
        <span className="text-[10px] font-extrabold uppercase tracking-[0.14em] text-primary">
          Orquestador
        </span>
        {phase && (
          <span className="text-[9px] uppercase tracking-[0.14em] text-on-surface-subtle">
            · {phase}
          </span>
        )}
        <span className="ml-auto flex items-center gap-1.5">
          {model && (
            <span className="rounded-md bg-surface px-2 py-0.5 font-mono text-[10px] text-on-surface-variant">
              {model}
            </span>
          )}
          <span className="status-pill-accent inline-flex items-center gap-1 px-2 py-0.5 text-[9.5px]">
            <Zap className="h-2.5 w-2.5" fill="currentColor" />
            {reasoningEffort}
          </span>
        </span>
      </div>

      {rows.length === 0 ? (
        <div className="flex items-center gap-2 text-on-surface-variant">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          Conectando con el orquestador…
        </div>
      ) : (
        <ol className="flex flex-col gap-0.5">
          {rows.map((r, i) => {
            const isActive = i === lastStartedIdx;
            const done = r.done || (lastStartedIdx !== undefined && i < lastStartedIdx);
            const { label, detail } = labelForNode(r.step);
            const rowBg = isActive ? "bg-[rgba(201,168,76,0.06)]" : "";
            const labelColor = done
              ? "text-on-surface-subtle"
              : isActive
                ? "text-on-surface-strong"
                : "text-on-surface-faint";
            return (
              <li
                key={r.key}
                className={`flex items-start gap-2.5 rounded-md px-2 py-1.5 ${rowBg}`}
              >
                <span className="mt-0.5 inline-flex h-[15px] w-[15px] shrink-0 items-center justify-center">
                  {done ? (
                    <CheckCircle2
                      className="h-3.5 w-3.5 text-status-success"
                      strokeWidth={2.4}
                    />
                  ) : isActive ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                  ) : (
                    <CircleDot className="h-3.5 w-3.5 text-on-surface-faint" />
                  )}
                </span>
                <div className="flex-1">
                  <div className={`font-mono text-[12.5px] leading-snug ${labelColor}`}>
                    {label}
                  </div>
                  {detail && (
                    <div className="mt-0.5 text-[10px] text-on-surface-subtle">{detail}</div>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Context window — approximate token budget per model.
// Tokens estimated as char-count / 4 (works well enough for ES/EN narrative).
// Update this map when the catalog adds models with different context sizes.
// ---------------------------------------------------------------------------

const MODEL_CONTEXT_LIMITS: Record<string, number> = {
  "gpt-5.5": 128_000,
  "gpt-5.4-mini": 400_000,
  "gpt-5.4": 1_000_000,
  "groq/llama-3.3-70b-versatile": 128_000,
  "groq/llama-3.1-8b-instant": 128_000,
  "gemini/gemini-2.5-flash": 1_000_000,
  "gemini/gemini-2.5-pro": 2_000_000,
  "anthropic/claude-haiku-4-5": 200_000,
  "anthropic/claude-sonnet-4-6": 1_000_000,
};
const DEFAULT_CONTEXT_LIMIT = 128_000;

function estimateTokens(text: string): number {
  if (!text) return 0;
  // ~4 chars per token for mixed ES/EN text; rounded up so the bar errs on
  // the side of "you're running out".
  return Math.ceil(text.length / 4);
}

function ContextBar({
  turns,
  caseState,
  model,
}: {
  turns: ChatTurn[];
  caseState: CaseState | null;
  model: string | null;
}) {
  const limit = (model && MODEL_CONTEXT_LIMITS[model]) || DEFAULT_CONTEXT_LIMIT;
  // Rough estimate: messages + facts + pending questions. We also reserve
  // ~3k tokens for the system prompts the orchestrator injects every turn.
  const messagesTokens = turns.reduce(
    (acc, t) => acc + estimateTokens(t.content),
    0,
  );
  const factsTokens = (caseState?.case_facts ?? []).reduce(
    (acc, f) => acc + estimateTokens(`${f.slot}: ${f.value}`),
    0,
  );
  const pendingTokens = (caseState?.case_pending ?? []).reduce(
    (acc, q) => acc + estimateTokens(q),
    0,
  );
  const SYSTEM_PROMPT_RESERVE = 3000;
  const used = messagesTokens + factsTokens + pendingTokens + SYSTEM_PROMPT_RESERVE;
  const pct = Math.min(100, (used / limit) * 100);

  let barColor = "var(--status-success)";
  let textColor = "text-on-surface-variant";
  if (pct >= 85) {
    barColor = "var(--status-danger)";
    textColor = "text-status-danger";
  } else if (pct >= 60) {
    barColor = "var(--status-warning)";
    textColor = "text-status-warning";
  }

  const fmt = (n: number) =>
    n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}K` : `${n}`;

  return (
    <div className="card-canon-sunken flex items-center gap-3 px-3.5 py-2.5">
      <span className="text-[9.5px] font-extrabold uppercase tracking-[0.16em] text-on-surface-subtle">
        Contexto
      </span>
      <div className="h-1.5 min-w-[80px] flex-1 overflow-hidden rounded-full bg-surface-container">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
      <span className={`font-mono text-[11.5px] font-semibold tabular-nums ${textColor}`}>
        {fmt(used)} / {fmt(limit)}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Compact case-status row (always visible above the conversation).
// ---------------------------------------------------------------------------

function CaseStatusBar({
  caseState,
  model,
  reasoningEffort,
}: {
  caseState: CaseState | null;
  model: string | null;
  reasoningEffort: string;
}) {
  const areaMeta = caseState?.case_area_hint
    ? LEGAL_AREAS.find((a) => a.id === caseState.case_area_hint)
    : null;

  // Phase: dot color + label + extra info
  let phaseDot = "var(--on-surface-subtle)";
  let phaseGlow = "rgba(107, 105, 98, 0.3)";
  let phaseLabel = "esperando";
  let phaseExtra: string | null = null;

  if (caseState?.case_phase === "intake") {
    phaseDot = "var(--primary)";
    phaseGlow = "rgba(201,168,76,0.25)";
    phaseLabel = "intake";
    phaseExtra = "recogiendo contexto";
  } else if (caseState?.case_phase === "investigation") {
    phaseDot = "var(--status-info)";
    phaseGlow = "rgba(179,164,240,0.25)";
    const total = caseState.case_pending.length + caseState.case_facts.length;
    phaseLabel = "investigación";
    phaseExtra = `${caseState.case_facts.length}/${total || "?"} datos`;
  } else if (caseState?.case_phase === "analysis") {
    phaseDot = "var(--status-warning)";
    phaseGlow = "rgba(232,179,14,0.3)";
    phaseLabel = "análisis";
    phaseExtra = "multi-agente";
  } else if (caseState?.case_phase === "complete") {
    phaseDot = "var(--status-success)";
    phaseGlow = "rgba(139,201,139,0.3)";
    phaseLabel = "completo";
    phaseExtra = "listo para nuevo caso";
  }

  return (
    <div className="flex flex-wrap items-center gap-2.5">
      <span className="status-pill">
        <span
          className="h-[7px] w-[7px] shrink-0 rounded-full"
          style={{ background: phaseDot, boxShadow: `0 0 0 3px ${phaseGlow}` }}
        />
        Fase: {phaseLabel}
        {phaseExtra && <span className="font-normal text-on-surface-variant"> · {phaseExtra}</span>}
      </span>

      {areaMeta && (
        <span className="status-pill">
          <Scale className={`h-3.5 w-3.5 ${areaMeta.color}`} strokeWidth={2} />
          {areaMeta.label}
        </span>
      )}

      {model && (
        <span className="status-pill status-pill-mono">
          <Bot className="h-3.5 w-3.5" strokeWidth={1.8} />
          {model}
        </span>
      )}

      <span className="status-pill status-pill-accent">
        <Zap className="h-3 w-3" fill="currentColor" />
        {reasoningEffort}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state (richer — explains what's about to happen + offers scenarios)
// ---------------------------------------------------------------------------

// Scenario cards in empty state — icon + area give the user immediate visual
// recognition of "what kind of case this is". Avoids emojis (editorial code).
const SCENARIO_EXAMPLES: {
  label: string;
  description: string;
  shortDescription: string;
  icon: typeof Briefcase;
  iconColor: string;
  iconBg: string;
  areaLabel: string;
  areaColor: string;
}[] = [
  {
    label: "Despido injustificado",
    description:
      "Hace 3 años trabajo en una empresa privada con contrato firmado. Hoy me despidieron sin causa y sin pagarme nada. ¿Qué puedo hacer?",
    shortDescription: "5 años con contrato firmado, sin carta de despido",
    icon: Briefcase,
    iconColor: "#C9A84C",
    iconBg: "rgba(201,168,76,0.12)",
    areaLabel: "Laboral",
    areaColor: "#C9A84C",
  },
  {
    label: "Acoso laboral",
    description:
      "Mi jefe me grita y discrimina hace meses delante de mis compañeros. Tengo capturas de WhatsApp y hay testigos. ¿Cómo procedo?",
    shortDescription: "Hostigamiento del jefe directo de forma reiterada",
    icon: AlertCircle,
    iconColor: "#C9A84C",
    iconBg: "rgba(201,168,76,0.12)",
    areaLabel: "Laboral",
    areaColor: "#C9A84C",
  },
  {
    label: "Conflicto vecinal",
    description:
      "Mi vecino construyó una pared invadiendo parte de mi terreno. Tengo escritura inscrita en SUNARP. ¿Qué pasos sigo?",
    shortDescription: "Ruidos, humos y emanaciones del vecino colindante",
    icon: Home,
    iconColor: "#9BB5D8",
    iconBg: "rgba(155,181,216,0.12)",
    areaLabel: "Civil",
    areaColor: "#9BB5D8",
  },
  {
    label: "Multa SUNAT",
    description:
      "Recibí una resolución de SUNAT con una multa que no entiendo y tengo 20 días para responder. Ayúdame a evaluar mi caso.",
    shortDescription: "Resolución de multa por declaración fuera de plazo",
    icon: DollarSign,
    iconColor: "#8BC98B",
    iconBg: "rgba(139,201,139,0.12)",
    areaLabel: "Tributario",
    areaColor: "#8BC98B",
  },
];

function HowItWorks() {
  const steps = [
    {
      n: 1,
      title: "Intake",
      desc: "Clasifica la rama del derecho y extrae los hechos clave.",
    },
    {
      n: 2,
      title: "Investigación",
      desc: "Pregunta lo que falta y recupera jurisprudencia del corpus.",
    },
    {
      n: 3,
      title: "Análisis multi-agente",
      desc: "Varios agentes deliberan y entregan el dictamen final.",
    },
  ];
  return (
    <div className="card-canon p-[17px]">
      <p className="mb-3.5 text-[9.5px] font-extrabold uppercase tracking-[0.16em] text-on-surface-subtle">
        Cómo funciona
      </p>
      <ol className="flex flex-col gap-3.5">
        {steps.map((s) => (
          <li key={s.n} className="flex gap-2.5">
            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-[7px] bg-[rgba(201,168,76,0.12)] font-['Newsreader'] text-[12px] font-bold text-primary">
              {s.n}
            </div>
            <div>
              <div className="text-[13px] font-semibold text-on-surface-strong">
                {s.title}
              </div>
              <div className="mt-0.5 text-[11.5px] leading-[1.45] text-on-surface-variant">
                {s.desc}
              </div>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AnalizarPage() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [caseState, setCaseState] = useState<CaseState | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [liveSteps, setLiveSteps] = useState<LiveStep[]>([]);
  const [livePhase, setLivePhase] = useState<CasePhase | undefined>(undefined);
  // Optional model override via ?model=<id> in URL — useful for testing
  // upper-tier models on a free-tier account (or vice-versa).
  const [modelOverride, setModelOverride] = useState<string | null>(null);
  // Default model surfaced from the platform. Today the codex-proxy serves
  // gpt-5.5 / gpt-5.4-mini / gpt-5.4; gpt-5.5 is the configured default in
  // apps/api/.env:DEFAULT_LLM_MODEL. We seed `activeModel` so the badge
  // shows from the first render (it gets overwritten by the real model name
  // returned in each chat response).
  const [activeModel, setActiveModel] = useState<string | null>("gpt-5.5");
  const [isReadOnly, setIsReadOnly] = useState(false);
  // Reasoning effort surfaced from the platform — codex-proxy defaults to
  // medium (CODEX_PROXY_REASONING_EFFORT). Hook this to platform config when
  // we wire per-call overrides.
  const reasoningEffort = "medium";
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { authFetch } = useAuth();

  const handleScenarioPick = (description: string) => {
    setInput(description);
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.focus();
      el.setSelectionRange(el.value.length, el.value.length);
    });
  };

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [turns, loading]);

  // ── Load a past conversation when the URL has ?conversation=<uuid> ──
  // Historial entries link here so the user can review a previous case.
  // We don't have persisted `case_state` yet (backlog), so we drop the user
  // into a read-only "complete" view with the past messages replayed.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const m = params.get("model");
    if (m) setModelOverride(m);
    const convId = params.get("conversation");
    if (!convId) return;

    let cancelled = false;
    (async () => {
      try {
        const res = await authFetch(`/api/conversations/${convId}`);
        if (!res.ok) {
          toast.error("No se pudo cargar la conversación.");
          return;
        }
        const data = await res.json();
        if (cancelled) return;
        const loadedTurns: ChatTurn[] = (data.messages || []).map(
          (m: { role: "user" | "assistant"; content: string; agent_used?: string }) => ({
            role: m.role,
            content: m.content,
            agent: m.agent_used,
            area: data.legal_area,
          }),
        );
        setTurns(loadedTurns);
        // If the backend persisted case_state (conversations created after
        // the 021 migration), restore it verbatim — the user can KEEP
        // adding turns from where they left off. Legacy conversations
        // (case_state=null) fall back to read-only "complete" view.
        if (data.case_state) {
          setCaseState(data.case_state);
          setIsReadOnly(data.case_state.case_phase === "complete");
        } else {
          setCaseState({
            case_phase: "complete",
            case_facts: [],
            case_pending: [],
            case_turn_count: loadedTurns.length,
            case_area_hint: data.legal_area || "",
          });
          setIsReadOnly(true);
        }
      } catch (err) {
        console.error(err);
        toast.error("Error de conexión al cargar la conversación.");
      }
    })();
    return () => {
      cancelled = true;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendMessage = async (message: string) => {
    if (!message.trim() || loading) return;
    setLoading(true);
    setLiveSteps([]);
    setLivePhase(undefined);

    setTurns((prev) => [...prev, { role: "user", content: message }]);
    setInput("");

    try {
      // Hit the API directly (bypassing the Next.js dev proxy) so SSE events
      // stream chunk-by-chunk instead of being buffered until the upstream
      // connection closes. Next.js rewrites buffer slow streams in dev.
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await authFetch(`${API_URL}/api/chat/stream-case`, {
        method: "POST",
        body: JSON.stringify({
          message,
          case_state: caseState,
          ...(modelOverride ? { model: modelOverride } : {}),
        }),
      });

      if (!res.ok || !res.body) {
        const body = await res.json().catch(() => null);
        const detail = body?.detail || `Error ${res.status}`;
        toast.error(typeof detail === "string" ? detail : "No se pudo procesar el mensaje");
        return;
      }

      // ── SSE parse loop ───────────────────────────────────────────────
      // Wire format per event: `event: <type>\ndata: <json>\n\n`
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let donePayload: {
        message: string;
        agent_used: string;
        legal_area: string;
        model_used?: string;
        case_state?: CaseState | null;
      } | null = null;
      let errored = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let boundary: number;
        while ((boundary = buffer.indexOf("\n\n")) !== -1) {
          const rawEvent = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);

          let eventType = "message";
          let dataStr = "";
          for (const line of rawEvent.split("\n")) {
            if (line.startsWith("event:")) eventType = line.slice(6).trim();
            else if (line.startsWith("data:")) dataStr += line.slice(5).trim();
          }
          if (!dataStr) continue;

          let data: Record<string, unknown>;
          try {
            data = JSON.parse(dataStr);
          } catch {
            continue;
          }

          if (eventType === "step") {
            setLiveSteps((prev) => [
              ...prev,
              {
                node: String(data.node ?? "?"),
                status: (data.status as "start" | "done") ?? "start",
                phase: String(data.phase ?? "?"),
                meta: data,
              },
            ]);
          } else if (eventType === "phase_start") {
            const ph = data.phase as CasePhase | undefined;
            if (ph) setLivePhase(ph);
          } else if (eventType === "done") {
            donePayload = data as typeof donePayload;
          } else if (eventType === "error") {
            errored = true;
            const msg = (data.message as string) || "Error en el orquestador";
            toast.error(msg);
          }
        }
      }

      if (errored || !donePayload) return;

      setCaseState(donePayload.case_state ?? null);
      if (donePayload.model_used) setActiveModel(donePayload.model_used);
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content: donePayload!.message,
          phase: donePayload!.case_state?.case_phase,
          area: donePayload!.legal_area,
          agent: donePayload!.agent_used,
        },
      ]);
    } catch (err) {
      console.error(err);
      toast.error("Error de conexión. Intenta de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleSkipToAnalysis = () => {
    sendMessage("Pasa al análisis ahora con lo que ya tienes.");
  };

  const handleNewCase = () => {
    setTurns([]);
    setCaseState(null);
    setInput("");
    setActiveModel(null);
    setIsReadOnly(false);
    // Drop the ?conversation= query string so a refresh stays on a fresh case.
    if (typeof window !== "undefined" && window.location.search) {
      window.history.replaceState({}, "", "/analizar");
    }
  };

  const showSkipButton =
    caseState?.case_phase === "investigation" &&
    caseState.case_facts.length >= 2 &&
    !loading;

  const showNewCaseButton = caseState?.case_phase === "complete";

  return (
    <AppLayout>
      <div className="flex min-h-full flex-col text-on-surface">
        <InternalPageHeader
          icon={<FileSearch className="h-5 w-5" strokeWidth={1.7} />}
          eyebrow="Producto"
          title="Analizar caso"
          description="Asistente legal multi-agente. Describe tu situación y el orquestador identifica la rama, investiga y entrega un análisis fundamentado."
          utilitySlot={<div className="hidden md:flex"><ShellUtilityActions /></div>}
          actions={
            showNewCaseButton ? (
              <button
                onClick={handleNewCase}
                className="gold-gradient inline-flex h-9 items-center gap-1.5 rounded-lg px-3.5 text-[12.5px] font-bold text-on-primary transition-opacity hover:opacity-95"
              >
                <Plus className="h-3.5 w-3.5" strokeWidth={2.2} />
                Nuevo caso
              </button>
            ) : null
          }
        />

        <div className="max-w-6xl w-full mx-auto px-6 py-6 flex-1 flex flex-col gap-4">
          {/* Status bar — always visible */}
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <CaseStatusBar
              caseState={caseState}
              model={activeModel}
              reasoningEffort={reasoningEffort}
            />
            {showSkipButton && (
              <button
                onClick={handleSkipToAnalysis}
                className="flex items-center gap-1.5 text-xs text-primary hover:text-primary-container transition-colors px-3 py-2 rounded-lg border border-primary/30 hover:border-primary/50"
              >
                <SkipForward className="w-3.5 h-3.5" />
                Pasar al análisis
              </button>
            )}
          </div>

          {/* Context window usage */}
          <ContextBar turns={turns} caseState={caseState} model={activeModel} />

          {/* Two-column layout: conversation + side panel */}
          <div className="flex-1 grid lg:grid-cols-[1fr_320px] gap-6 min-h-0">
            {/* ── Conversation column ─────────────────────────────── */}
            <div className="flex flex-col min-h-0">
              <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto space-y-4 pb-4 pr-1"
              >
                {turns.length === 0 && (
                  <div className="space-y-4">
                    <div className="card-canon p-6">
                      <h2 className="font-['Newsreader'] text-[21px] font-semibold text-on-surface-strong">
                        Bienvenido.
                      </h2>
                      <p className="mt-2 max-w-[600px] text-[14px] leading-[1.55] text-on-surface-variant">
                        Describe tu situación con el detalle que recuerdes. Voy a
                        identificar la rama del derecho que aplica, hacerte
                        preguntas puntuales y entregarte un análisis con base legal
                        peruana.
                      </p>
                    </div>

                    <div>
                      <p className="mb-3 px-0.5 text-[10px] font-extrabold uppercase tracking-[0.18em] text-on-surface-subtle">
                        Escenarios de ejemplo
                      </p>
                      <div className="grid gap-3 sm:grid-cols-2">
                        {SCENARIO_EXAMPLES.map((s) => {
                          const Icon = s.icon;
                          return (
                            <button
                              key={s.label}
                              type="button"
                              onClick={() => handleScenarioPick(s.description)}
                              className="card-lift card-canon-sunken flex items-start gap-3 p-4 text-left"
                            >
                              <div
                                className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-[9px]"
                                style={{ background: s.iconBg }}
                              >
                                <Icon
                                  className="h-[17px] w-[17px]"
                                  strokeWidth={1.8}
                                  style={{ color: s.iconColor }}
                                />
                              </div>
                              <div className="min-w-0 flex-1">
                                <div className="text-[13.5px] font-bold text-on-surface-strong">
                                  {s.label}
                                </div>
                                <div className="mt-1 text-[11.5px] leading-[1.4] text-on-surface-variant">
                                  {s.shortDescription}
                                </div>
                                <span
                                  className="mt-2 inline-block rounded-md px-[7px] py-0.5 text-[9px] font-bold uppercase tracking-[0.1em]"
                                  style={{
                                    color: s.areaColor,
                                    background: `${s.areaColor}1F`,
                                  }}
                                >
                                  {s.areaLabel}
                                </span>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}

                {turns.map((t, i) => (
                  <div
                    key={i}
                    className={`flex gap-2.5 ${
                      t.role === "user" ? "flex-row-reverse" : ""
                    }`}
                  >
                    <div
                      className={`flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-lg border ${
                        t.role === "user"
                          ? "border-[rgba(201,168,76,0.3)] bg-[rgba(201,168,76,0.12)] text-primary"
                          : "border-outline-variant bg-surface text-primary"
                      }`}
                    >
                      {t.role === "user" ? (
                        <User className="h-3.5 w-3.5" strokeWidth={2} />
                      ) : (
                        <Scale className="h-3.5 w-3.5" strokeWidth={2} />
                      )}
                    </div>
                    <div
                      className={`max-w-[78%] rounded-[13px] border px-4 py-3 ${
                        t.role === "user"
                          ? "border-[rgba(201,168,76,0.18)] bg-[rgba(201,168,76,0.06)]"
                          : "card-canon-sunken"
                      }`}
                    >
                      {t.role === "assistant" && t.agent && (
                        <div className="mb-2 text-[9.5px] font-extrabold uppercase tracking-[0.12em] text-[#8a7a4a]">
                          {t.agent}
                          {t.area && ` · ${t.area}`}
                        </div>
                      )}
                      <div
                        className="prose prose-invert prose-sm max-w-none text-[13.5px] leading-[1.65] text-on-surface"
                        dangerouslySetInnerHTML={{
                          __html: renderMarkdown(t.content),
                        }}
                      />
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="flex gap-2.5">
                    <div className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-lg border border-outline-variant bg-surface text-primary">
                      <Scale className="h-3.5 w-3.5" strokeWidth={2} />
                    </div>
                    <div className="max-w-[78%] flex-1">
                      <ReasoningPanel
                        liveSteps={liveSteps}
                        phase={livePhase ?? caseState?.case_phase}
                        model={activeModel}
                        reasoningEffort={reasoningEffort}
                      />
                    </div>
                  </div>
                )}
              </div>

          {/* Composer — visible always. When phase=complete, user can keep adding
              context (papers arrived later) and the orchestrator re-runs analysis. */}
          {caseState?.case_phase === "complete" && (
            <div className="mb-3 mt-2 flex items-start gap-2 rounded-[11px] border border-[rgba(201,168,76,0.22)] bg-[rgba(201,168,76,0.08)] px-3.5 py-3 text-[13px] text-[#d8c79a]">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" strokeWidth={1.8} />
              <span>
                Caso analizado. Si llegaron papeles nuevos o querés sumar
                contexto, continuá escribiendo abajo.
              </span>
            </div>
          )}
          <form onSubmit={handleSubmit} className="sticky bottom-0 mt-2 bg-background pt-1.5">
            <div className="flex items-end gap-2 rounded-[13px] border border-outline-variant bg-surface p-2 transition-colors focus-within:border-[rgba(201,168,76,0.5)]">
              <button
                type="button"
                disabled
                onClick={() =>
                  toast.info(
                    "Próximamente — adjuntar archivos llegará en la siguiente iteración.",
                  )
                }
                className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-[9px] text-on-surface-subtle transition-colors hover:bg-surface-container hover:text-on-surface-variant disabled:cursor-not-allowed"
                title="Adjuntar archivos (próximamente)"
              >
                <Paperclip className="h-[17px] w-[17px]" strokeWidth={1.8} />
              </button>
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                rows={2}
                placeholder={
                  turns.length === 0
                    ? "Describe tu situación con el mayor detalle posible..."
                    : "Responde la pregunta del agente o agrega contexto..."
                }
                className="max-h-[140px] flex-1 resize-none border-0 bg-transparent px-1 py-2.5 text-[14px] leading-[1.5] text-on-surface placeholder-on-surface-subtle focus:outline-none"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="gold-gradient flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-[9px] text-on-primary transition-opacity hover:opacity-95 disabled:cursor-not-allowed disabled:grayscale disabled:opacity-50"
                aria-label="Enviar mensaje"
              >
                {loading ? (
                  <Loader2 className="h-[17px] w-[17px] animate-spin" />
                ) : (
                  <Send className="h-[17px] w-[17px]" strokeWidth={2} />
                )}
              </button>
            </div>
            <div className="px-1 pt-1.5 text-[10.5px] text-on-surface-faint">
              El agente irá pidiendo datos progresivamente ·{" "}
              <span className="text-on-surface-subtle">⌘↵ enviar</span>
            </div>
          </form>
        </div>

            {/* ── Side panel ─────────────────────────────────────── */}
            <aside className="hidden lg:flex flex-col gap-4 min-h-0">
              {turns.length === 0 ? (
                <HowItWorks />
              ) : (
                <>
                  {/* Hechos del caso */}
                  <div className="card-canon p-[17px]">
                    <div className="mb-3.5 flex items-center justify-between">
                      <span className="text-[9.5px] font-extrabold uppercase tracking-[0.16em] text-on-surface-subtle">
                        Hechos del caso
                      </span>
                      <span className="rounded-md bg-[rgba(139,201,139,0.1)] px-1.5 py-0.5 text-[10px] font-bold text-status-success">
                        {caseState?.case_facts.length ?? 0}
                      </span>
                    </div>
                    {caseState?.case_facts.length ? (
                      <ul className="flex flex-col gap-2.5">
                        {caseState.case_facts.map((f, i) => (
                          <li key={i} className="flex flex-col border-b border-outline-variant pb-2.5 last:border-b-0 last:pb-0">
                            <span className="text-[9.5px] font-bold uppercase tracking-[0.1em] text-on-surface-subtle">
                              {f.slot}
                            </span>
                            <span className="mt-0.5 text-[13px] font-semibold text-on-surface-strong">
                              {f.value}
                            </span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-[11.5px] text-on-surface-variant">
                        Aún sin hechos estructurados. A medida que respondas, irán
                        apareciendo aquí.
                      </p>
                    )}
                  </div>

                  {/* Preguntas abiertas */}
                  {caseState?.case_pending && caseState.case_pending.length > 0 && (
                    <div className="card-canon p-[17px]">
                      <div className="mb-3.5 flex items-center justify-between">
                        <span className="text-[9.5px] font-extrabold uppercase tracking-[0.16em] text-on-surface-subtle">
                          Preguntas abiertas
                        </span>
                        <span className="rounded-md bg-[rgba(179,164,240,0.1)] px-1.5 py-0.5 text-[10px] font-bold text-status-info">
                          {caseState.case_pending.length}
                        </span>
                      </div>
                      <ul className="flex flex-col gap-2.5">
                        {caseState.case_pending.slice(0, 5).map((q, i) => (
                          <li
                            key={i}
                            className="flex items-start gap-2.5 text-[12.5px] leading-[1.4] text-on-surface-variant"
                          >
                            <span className="mt-px h-3.5 w-3.5 shrink-0 rounded-full border-[1.5px] border-on-surface-faint" />
                            <span>{q}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Skip a análisis */}
                  {showSkipButton && (
                    <button
                      onClick={handleSkipToAnalysis}
                      className="flex w-full items-center justify-center gap-2 rounded-lg border border-[rgba(201,168,76,0.3)] px-3 py-3 text-[12.5px] font-semibold text-primary transition-colors hover:bg-[rgba(201,168,76,0.08)]"
                    >
                      <SkipForward className="h-3.5 w-3.5" />
                      Tengo prisa — pasa al análisis
                    </button>
                  )}
                </>
              )}
            </aside>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
