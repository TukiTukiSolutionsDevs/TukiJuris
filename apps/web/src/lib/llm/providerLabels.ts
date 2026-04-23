/**
 * PROVIDER_LABELS — single source of branding truth for LLM providers.
 * Maps provider IDs to display metadata used in Configuración and anywhere
 * a provider name or visual style needs to be rendered consistently.
 */

export type ProviderLabel = {
  displayName: string;
  iconUrl?: string;
  docsUrl?: string;
  brandColor?: string;
  /** Tailwind text-color class */
  color?: string;
  /** Tailwind gradient / border tone classes for card backgrounds */
  tone?: string;
};

export const PROVIDER_LABELS: Record<string, ProviderLabel> = {
  google: {
    displayName: "Google (Gemini)",
    docsUrl: "https://aistudio.google.com/apikey",
    brandColor: "#4285F4",
    color: "text-blue-400",
    tone: "from-blue-500/12 to-blue-500/5 border-blue-500/20",
  },
  groq: {
    displayName: "Groq",
    docsUrl: "https://console.groq.com/keys",
    brandColor: "#F55036",
    color: "text-orange-400",
    tone: "from-orange-500/12 to-orange-500/5 border-orange-500/20",
  },
  deepseek: {
    displayName: "DeepSeek",
    docsUrl: "https://platform.deepseek.com/api_keys",
    brandColor: "#00C4CC",
    color: "text-cyan-400",
    tone: "from-cyan-500/12 to-cyan-500/5 border-cyan-500/20",
  },
  openai: {
    displayName: "OpenAI",
    docsUrl: "https://platform.openai.com/api-keys",
    brandColor: "#10A37F",
    color: "text-green-400",
    tone: "from-green-500/12 to-green-500/5 border-green-500/20",
  },
  anthropic: {
    displayName: "Anthropic",
    docsUrl: "https://console.anthropic.com/settings/keys",
    brandColor: "#D97706",
    color: "text-amber-400",
    tone: "from-amber-500/12 to-amber-500/5 border-amber-500/20",
  },
  xai: {
    displayName: "xAI (Grok)",
    docsUrl: "https://console.x.ai",
    brandColor: "#A855F7",
    color: "text-purple-400",
    tone: "from-purple-500/12 to-purple-500/5 border-purple-500/20",
  },
};

/**
 * Returns branding metadata for a provider. Always returns a valid object —
 * never throws. Unknown providers get a generic fallback with a dev-mode warning.
 */
export function labelForProvider(providerId: string, backendName?: string): ProviderLabel {
  const overlay = PROVIDER_LABELS[providerId];
  if (overlay) return overlay;
  if (process.env.NODE_ENV !== "production") {
    console.warn(`[labelForProvider] Unknown provider: "${providerId}" — using generic fallback`);
  }
  return { displayName: backendName ?? providerId };
}
