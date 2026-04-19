// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface Citation {
  type: string;
  text: string;
  reference: string;
}

export interface Message {
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

export interface ChatHistory {
  id: string;
  title: string | null;
  legal_area: string | null;
  date: string;
  is_pinned: boolean;
  is_shared: boolean;
}

export interface ContextMenu {
  convId: string;
  convTitle: string | null;
  x: number;
  y: number;
}

export interface OrchestratorState {
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
}

export const INITIAL_ORCH_STATE: OrchestratorState = {
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
};
