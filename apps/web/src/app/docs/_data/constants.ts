export const RATE_LIMITS = [
  { plan: "Anonymous", rpm: "10", notes: "IP-based, no auth required" },
  { plan: "Free", rpm: "30", notes: "JWT or API key" },
  { plan: "Pro", rpm: "120", notes: "JWT or API key" },
  { plan: "Enterprise", rpm: "600", notes: "Custom limits available" },
];

export const ERROR_CODES = [
  { code: "400", title: "Bad Request", desc: "Malformed request body or invalid parameters." },
  { code: "401", title: "Unauthorized", desc: "No valid JWT or API key was provided." },
  { code: "403", title: "Forbidden", desc: "Authenticated, but API key lacks the required scope." },
  { code: "404", title: "Not Found", desc: "The requested resource does not exist." },
  { code: "409", title: "Conflict", desc: "Email already registered (during registration)." },
  { code: "422", title: "Unprocessable Entity", desc: "Validation error — check the `detail` field in the response body." },
  { code: "429", title: "Too Many Requests", desc: "Rate limit exceeded. See X-RateLimit-Limit header." },
  { code: "502", title: "Bad Gateway", desc: "Upstream AI error — LLM or vector database unavailable." },
];
