# OpenCode + Anthropic via Meridian — Plan Completo

## Contexto

OpenCode removió soporte oficial de Anthropic OAuth por pedido legal (PR `anomalyco/opencode#18186`).
La comunidad creó bridges/plugins, pero Anthropic empezó a gatear requests de third-party apps
con el mensaje: `"Third-party apps now draw from your extra usage, not your plan limits"`.

Después de investigar 4 repos comunitarios, capturar requests reales y aislar variables,
descubrimos que **la causa raíz es el system prompt que OpenCode manda**, no las tools ni headers.

## Arquitectura actual

```
┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌───────────┐
│ OpenCode │────>│ Shim (:4568) │────>│ Meridian │────>│ Anthropic │
│          │     │ rewrite sys  │     │ (:3456)  │     │   API     │
└──────────┘     └──────────────┘     └──────────┘     └───────────┘
```

- **OpenCode** manda requests con system prompt branded + env + AGENTS.md
- **Shim** intercepta, detecta markers, reemplaza `system` por prompt mínimo
- **Meridian** hace auth con Claude CLI credentials (Keychain) y proxea a Anthropic
- **Anthropic** recibe un request que parece Claude Code oficial

## Archivos del stack

| Archivo | Rol |
|---------|-----|
| `~/.local/bin/opencode-anthropic` | Wrapper CLI: levanta stack, ejecuta OpenCode |
| `~/.config/opencode/meridian-opencode-shim.js` | Proxy HTTP: reescribe system prompt |
| `~/.config/opencode/agents/meridian-smoke.md` | Agente mínimo para smoke tests |
| `~/.config/opencode/opencode.json` | Config OpenCode (tiene plugin Meridian) |
| `~/.local/state/opencode-anthropic/` | Logs + PIDs |

## Comandos

```bash
opencode-anthropic              # Abre OpenCode interactivo via Anthropic
opencode-anthropic run [args]   # Ejecuta prompt directo
opencode-anthropic --status     # Estado de Meridian y shim
opencode-anthropic --logs       # Rutas de logs
opencode-anthropic --tail       # Seguir logs en vivo
opencode-anthropic --restart    # Reiniciar stack completo
opencode-anthropic --stop       # Detener todo
opencode-anthropic --help       # Ayuda
```

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MERIDIAN_HOST` | `127.0.0.1` | Host de Meridian |
| `MERIDIAN_PORT` | `3456` | Puerto de Meridian |
| `OPENCODE_MERIDIAN_SHIM_PORT` | `4568` | Puerto del shim |
| `OPENCODE_MERIDIAN_SYSTEM_PROMPT` | (ver shim) | System prompt personalizado |
| `MAX_LOG_SIZE` | `5242880` | Tamaño máximo de log antes de rotar (5MB) |

## Prerequisitos

1. **Claude CLI** instalado y logueado (`claude auth status` → loggedIn + subscriptionType=max)
2. **Meridian** instalado globalmente (`npm install -g @rynfar/meridian`)
3. **Node.js 18.13+** (para `fetch` + `duplex: "half"`)
