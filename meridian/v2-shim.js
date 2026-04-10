const http = require("node:http")

// ── Config ──────────────────────────────────────────────────────────
const HOST = process.env.OPENCODE_MERIDIAN_SHIM_HOST || "127.0.0.1"
const PORT = Number(process.env.OPENCODE_MERIDIAN_SHIM_PORT || 4568)
const TARGET = process.env.OPENCODE_MERIDIAN_TARGET || "http://127.0.0.1:3456"
const MAX_BODY = 50 * 1024 * 1024

const MINIMAL_SYSTEM =
  process.env.OPENCODE_MERIDIAN_SYSTEM_PROMPT ||
  "You are Claude Code, Anthropic official CLI for Claude. Keep replies short and precise. Use available tools only when necessary."

const MARKERS = [
  "You are OpenCode, the best coding agent on the planet.",
  "You are powered by the model named",
  "<env>",
  "Instructions from:",
]

// ── Stats ───────────────────────────────────────────────────────────
const stats = { started: new Date().toISOString(), requests: 0, rewrites: 0, errors: 0 }

// ── Logging ─────────────────────────────────────────────────────────
function log(level, msg, extra) {
  const ts = new Date().toISOString()
  const line = extra
    ? `[${ts}] [SHIM] ${level}: ${msg} ${JSON.stringify(extra)}`
    : `[${ts}] [SHIM] ${level}: ${msg}`
  process.stdout.write(line + "\n")
}

// ── System prompt rewrite ───────────────────────────────────────────
function shouldRewriteSystem(system) {
  if (typeof system === "string") {
    return MARKERS.some((m) => system.includes(m))
  }
  if (Array.isArray(system)) {
    return system.some(
      (part) => typeof part?.text === "string" && MARKERS.some((m) => part.text.includes(m)),
    )
  }
  return false
}

function rewriteBody(body) {
  if (!body || typeof body !== "object") return { body, rewritten: false }
  if (!shouldRewriteSystem(body.system)) return { body, rewritten: false }
  return {
    body: { ...body, system: [{ type: "text", text: MINIMAL_SYSTEM }] },
    rewritten: true,
  }
}

// ── Health (own endpoint, not proxied) ──────────────────────────────
async function handleHealth(res) {
  let meridianOk = false
  try {
    const r = await fetch(`${TARGET}/health`, { signal: AbortSignal.timeout(3000) })
    meridianOk = r.ok
  } catch {}

  const payload = {
    status: meridianOk ? "healthy" : "degraded",
    shim: "running",
    meridian: meridianOk ? "reachable" : "unreachable",
    target: TARGET,
    stats,
  }
  res.writeHead(meridianOk ? 200 : 503, { "content-type": "application/json" })
  res.end(JSON.stringify(payload))
}

// ── Proxy handler ───────────────────────────────────────────────────
const server = http.createServer((req, res) => {
  if (req.url === "/health" && req.method === "GET") {
    handleHealth(res)
    return
  }

  let bodySize = 0
  const chunks = []

  req.on("data", (chunk) => {
    bodySize += chunk.length
    if (bodySize > MAX_BODY) {
      req.destroy()
      if (!res.headersSent) {
        res.writeHead(413, { "content-type": "application/json" })
        res.end(JSON.stringify({ type: "error", error: { type: "request_too_large", message: `Body exceeds ${MAX_BODY} bytes` } }))
      }
      return
    }
    chunks.push(chunk)
  })

  req.on("end", async () => {
    stats.requests++
    const reqId = `shim-${stats.requests}`

    try {
      const rawBody = Buffer.concat(chunks)
      let outgoingBody = rawBody
      let didRewrite = false

      if (rawBody.length > 0 && req.headers["content-type"]?.includes("application/json")) {
        try {
          const parsed = JSON.parse(rawBody.toString("utf8"))
          const result = rewriteBody(parsed)
          outgoingBody = Buffer.from(JSON.stringify(result.body))
          didRewrite = result.rewritten
        } catch (parseErr) {
          log("WARN", "JSON parse failed, forwarding raw body", { reqId, error: parseErr.message })
        }
      }

      if (didRewrite) {
        stats.rewrites++
        log("INFO", "system prompt rewritten", { reqId, url: req.url })
      }

      const url = new URL(req.url, TARGET)
      const headers = { ...req.headers }
      delete headers.host
      headers["content-length"] = String(outgoingBody.length)

      const upstream = await fetch(url, {
        method: req.method,
        headers,
        body: req.method === "GET" || req.method === "HEAD" ? undefined : outgoingBody,
        duplex: "half",
      })

      const responseHeaders = {}
      upstream.headers.forEach((value, key) => { responseHeaders[key] = value })

      res.writeHead(upstream.status, responseHeaders)

      if (upstream.status >= 400) {
        log("WARN", "upstream error", { reqId, status: upstream.status })
      }

      if (!upstream.body) { res.end(); return }

      for await (const chunk of upstream.body) { res.write(chunk) }
      res.end()
    } catch (error) {
      stats.errors++
      log("ERROR", "proxy error", { reqId, error: String(error) })
      if (!res.headersSent) {
        res.writeHead(502, { "content-type": "application/json" })
        res.end(JSON.stringify({ type: "error", error: { type: "proxy_error", message: String(error) } }))
      }
    }
  })
})

// ── Graceful shutdown ───────────────────────────────────────────────
function shutdown(signal) {
  log("INFO", `${signal} received, shutting down gracefully`)
  server.close(() => process.exit(0))
  setTimeout(() => process.exit(1), 5000)
}
process.on("SIGTERM", () => shutdown("SIGTERM"))
process.on("SIGINT", () => shutdown("SIGINT"))

// ── Start ───────────────────────────────────────────────────────────
server.listen(PORT, HOST, () => {
  log("INFO", `listening on http://${HOST}:${PORT}`, { target: TARGET })
})
