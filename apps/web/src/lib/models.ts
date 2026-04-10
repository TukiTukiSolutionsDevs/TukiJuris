/**
 * Unified model catalog — single source of truth for all model lists.
 * Used in: Chat (page.tsx), Configuración (preferencias), Onboarding.
 *
 * Tiers:
 *   free     → included in free plan or very cheap
 *   standard → moderate cost, great quality
 *   pro      → premium, most capable
 */

export interface ModelDef {
  id: string;
  name: string;
  provider: string;
  tier: "free" | "standard" | "pro";
  description?: string;
  /** Whether this model supports reasoning_effort / thinking mode */
  supportsThinking?: boolean;
}

export const MODEL_CATALOG: ModelDef[] = [
  // ─── Google (prefix: gemini/) ────────────────────────────
  { id: "gemini/gemini-2.5-flash",              name: "Gemini 2.5 Flash",        provider: "google",    tier: "free",     description: "Rápido y gratuito",                 supportsThinking: true },
  { id: "gemini/gemini-2.5-pro",                name: "Gemini 2.5 Pro",          provider: "google",    tier: "standard", description: "1M contexto, documentos largos",     supportsThinking: true },
  { id: "gemini/gemini-3.1-flash-lite-preview", name: "Gemini 3.1 Flash-Lite",   provider: "google",    tier: "standard", description: "$0.25/M, alta eficiencia" },
  { id: "gemini/gemini-3.1-pro-preview",        name: "Gemini 3.1 Pro",          provider: "google",    tier: "pro",      description: "$2/M, flagship de Google",           supportsThinking: true },

  // ─── Groq (ultra rápido — sin thinking mode) ──────────────
  { id: "groq/llama-3.3-70b-versatile",   name: "Llama 3.3 70B — Groq",   provider: "groq",      tier: "free",     description: "280 t/s, versátil" },
  { id: "groq/llama-3.1-8b-instant",      name: "Llama 3.1 8B — Groq",    provider: "groq",      tier: "free",     description: "560 t/s, instantáneo" },
  { id: "groq/qwen/qwen3-32b",           name: "Qwen3 32B — Groq",       provider: "groq",      tier: "standard", description: "400 t/s, razonamiento" },
  { id: "groq/openai/gpt-oss-120b",      name: "GPT-OSS 120B — Groq",    provider: "groq",      tier: "pro",      description: "500 t/s, open-weight potente" },

  // ─── DeepSeek ────────────────────────────────────────────
  { id: "deepseek/deepseek-chat",         name: "DeepSeek V3.2",           provider: "deepseek",  tier: "free",     description: "$0.28/M, 128K contexto" },
  { id: "deepseek/deepseek-reasoner",     name: "DeepSeek Reasoner",       provider: "deepseek",  tier: "standard", description: "Thinking mode, análisis profundo",   supportsThinking: true },

  // ─── OpenAI (prefix: openai/) ────────────────────────────
  { id: "openai/gpt-5.4-nano",           name: "GPT-5.4 Nano",           provider: "openai",    tier: "standard", description: "$0.20/M, tareas simples" },
  { id: "openai/gpt-5.4-mini",           name: "GPT-5.4 Mini",           provider: "openai",    tier: "pro",      description: "$0.75/M, 400K contexto",             supportsThinking: true },
  { id: "openai/gpt-5.4",                name: "GPT-5.4",                provider: "openai",    tier: "pro",      description: "$2.50/M, flagship 1M ctx",            supportsThinking: true },

  // ─── Anthropic (prefix: anthropic/) ──────────────────────
  { id: "anthropic/claude-haiku-4-5",     name: "Claude Haiku 4.5",       provider: "anthropic", tier: "standard", description: "$1/M, el más rápido" },
  { id: "anthropic/claude-sonnet-4-6",    name: "Claude Sonnet 4.6",      provider: "anthropic", tier: "pro",      description: "$3/M, velocidad + inteligencia",     supportsThinking: true },
  { id: "anthropic/claude-opus-4-6",      name: "Claude Opus 4.6",        provider: "anthropic", tier: "pro",      description: "$5/M, el más inteligente",            supportsThinking: true },

  // ─── xAI Grok (prefix: xai/) ────────────────────────────
  { id: "xai/grok-3-mini-fast-latest",       name: "Grok 3 Mini Fast",       provider: "xai",  tier: "free",     description: "$0.30/M, 131K ctx, rápido" },
  { id: "xai/grok-3-fast-latest",            name: "Grok 3 Fast",            provider: "xai",  tier: "standard", description: "$3/M, 131K ctx, razonamiento" },
  { id: "xai/grok-4-1-fast-reasoning",       name: "Grok 4.1 Fast",          provider: "xai",  tier: "standard", description: "$0.20/M, 2M ctx, mejor valor",        supportsThinking: true },
  { id: "xai/grok-4-0709",                   name: "Grok 4",                 provider: "xai",  tier: "pro",      description: "$3/M, 256K ctx, reasoning profundo",   supportsThinking: true },
  { id: "xai/grok-4.20-reasoning-latest",    name: "Grok 4.20 Reasoning",    provider: "xai",  tier: "pro",      description: "$2/M, 2M ctx, menor alucinación",     supportsThinking: true },
];

/**
 * Free tier models — platform-provided, no BYOK key needed.
 * These are always available to free plan users.
 */
export const FREE_TIER_MODELS: ModelDef[] = [
  { id: "gemini/gemini-2.5-flash",         name: "Gemini 2.5 Flash",       provider: "google", tier: "free", description: "Incluido gratis — rápido y capaz" },
  { id: "groq/llama-3.3-70b-versatile",    name: "Llama 3.3 70B — Groq",  provider: "groq",   tier: "free", description: "Incluido gratis — versátil" },
  { id: "groq/llama-3.1-8b-instant",       name: "Llama 3.1 8B — Groq",   provider: "groq",   tier: "free", description: "Incluido gratis — ultra rápido" },
];

/** Group labels for display */
export const TIER_LABELS: Record<string, string> = {
  free: "Gratis / Económicos",
  standard: "Estándar",
  pro: "Avanzados",
};

/** Get all model IDs that belong to a specific provider */
export function modelsForProvider(provider: string): string[] {
  return MODEL_CATALOG.filter((m) => m.provider === provider).map((m) => m.id);
}

/** Get model IDs available given a list of configured providers */
export function availableModelsForProviders(providers: string[]): string[] {
  return MODEL_CATALOG.filter((m) => providers.includes(m.provider)).map((m) => m.id);
}

/** Check if a model supports thinking / reasoning_effort */
export function modelSupportsThinking(modelId: string): boolean {
  const model = MODEL_CATALOG.find((m) => m.id === modelId);
  return model?.supportsThinking === true;
}

/** Get a display-friendly list grouped by tier */
export function modelsByTier(): Record<string, ModelDef[]> {
  const groups: Record<string, ModelDef[]> = {};
  for (const tier of ["free", "standard", "pro"]) {
    groups[tier] = MODEL_CATALOG.filter((m) => m.tier === tier);
  }
  return groups;
}
