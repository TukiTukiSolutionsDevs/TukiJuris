/**
 * API client for Agente Derecho backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatResponse {
  conversation_id: string;
  message: string;
  agent_used: string;
  legal_area: string;
  citations: Record<string, unknown>[] | null;
  model_used: string;
  tokens_used: number | null;
  latency_ms: number;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
}

export interface LLMModel {
  id: string;
  provider: string;
  name: string;
  description: string;
  tier: string;
  available: boolean;
}

export async function sendQuery(
  message: string,
  options?: {
    model?: string;
    legal_area?: string;
    conversation_id?: string;
  }
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      model: options?.model,
      legal_area: options?.legal_area,
      conversation_id: options?.conversation_id,
    }),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }

  return res.json();
}

export async function getAgents(): Promise<Agent[]> {
  const res = await fetch(`${API_URL}/api/chat/agents`);
  const data = await res.json();
  return data.agents;
}

export async function getModels(): Promise<LLMModel[]> {
  const res = await fetch(`${API_URL}/api/chat/models`);
  const data = await res.json();
  return data.models;
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_URL}/api/health`);
  return res.json();
}
