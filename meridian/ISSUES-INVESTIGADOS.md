# Issues y repos investigados

## Repos comunitarios auditados

### 1. cemalturkcan/opencode-anthropic-login-via-cli
- **Mecanismo**: Plugin OpenCode que lee credenciales de Claude CLI (Keychain/credentials.json),
  hace introspection del binario, soporta OAuth PKCE, intercepta requests Anthropic
- **Arquitectura**: Modular (introspection.ts, credentials.ts, pkce.ts, fetch.ts, transforms.ts, model-config.ts)
- **Tests**: fetch.test.ts, http.test.ts, introspection.test.ts, model-config.test.ts, pkce.test.ts, transforms.test.ts
- **Estado**: Plugin carga correctamente en OpenCode pero falla con "Third-party apps" error
- **Conclusion**: Arregla auth y wire protocol pero no el prompt fingerprinting

### 2. griffinmartin/opencode-claude-auth
- **Mecanismo**: Plugin bridge in-process dentro de OpenCode
- **Estado**: No declaraba `oc-plugin` targets en package.json; `opencode plugin` lo rechazaba
- **Conclusion**: No pudimos instalarlo via canal oficial

### 3. lehdqlsl/opencode-claude-auth-sync
- **Mecanismo**: Sync de credenciales de Claude CLI al auth store de OpenCode
- **Estado**: Solo sync, no incluye headers/user-agent/beta flags/prompt shaping
- **Conclusion**: Insuficiente para OpenCode 1.3+

### 4. dotCipher/opencode-claude-bridge
- **Mecanismo**: Bridge externo
- **Conclusion**: Mismo problema de fondo

## Issues de Meridian investigados

### #319 — Anthropic changes / harness detection
- Confirmado: Meridian pasa el system prompt del harness al SDK via `systemPrompt: { preset: "claude_code", append: systemContext }`
- El maintainer no modifica prompts en el proxy
- Workaround recomendado: shim externo (lo que implementamos)

### #255 — Extra usage / harnesses
- Reportes de OpenCode/Pi/OpenClaw bloqueados
- El gating depende del shape del request, no solo del nombre del harness

### #278 — Beta headers
- Discusion sobre stripping headers `anthropic-beta`
- Meridian los deja pasar transparentemente

### #221 — OpenCode persona configs
- Configuraciones de agente de OpenCode afectan lo que Meridian recibe

## Issues de OpenCode investigados

### anomalyco/opencode#18186 (PR)
- **Titulo**: "anthropic legal requests"
- **Accion**: Removieron soporte oficial Anthropic OAuth, referencias al provider y hints
- **Causa**: Pedido legal directo de Anthropic

### anomalyco/opencode#18267
- Discusion sobre auth changes post-remocion

### anomalyco/opencode#18329
- Error 429 relacionado con auth

### anomalyco/opencode#20079
- Feature request para Claude Code bridge

## Issues de Claude Code oficiales

### anthropics/claude-code#45016
- "Third-party apps now draw from your extra usage" reportado en CLI oficial
- Algunos usuarios lo resolvieron actualizando a 2.1.96+
- NO prueba compatibilidad con OpenCode

### anthropics/claude-code#45134
- Mismo error en CLI/extension oficial para algunos usuarios

## Evidencia de Consumer Terms de Anthropic

Seccion 3 de Consumer Terms:
- Prohibe acceso por medios automatizados o no humanos salvo via API key o permiso explicito
- Prohibe reverse engineering
- Prohibe bypass de medidas/protective systems

## Conclusion tecnica

El problema se desplazo de auth (resuelto por Meridian) hacia:
1. **Prompt fingerprinting** — Anthropic detecta system prompts de harnesses third-party
2. **Billing classification** — requests clasificados como "third-party" van a extra usage
3. **Request shape** — no solo el nombre del harness sino el shape completo del request

La solucion implementada (shim de system prompt) ataca el punto 1 directamente.
