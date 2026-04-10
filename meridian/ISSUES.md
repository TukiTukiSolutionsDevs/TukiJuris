# Issues investigados — Meridian + OpenCode + Anthropic

## Meridian (rynfar/meridian)

| Issue | Problema | Estado | Impacto |
|-------|----------|--------|---------|
| #319 | Detección por harness/system prompt | Abierto | DIRECTO — nuestro problema exacto |
| #255 | Extra usage / harnesses detectados | Abierto | Billing classification |
| #278 | Stripping beta headers | Resuelto en v1.34 | Bajo |
| #221 | OpenCode persona configs | Abierto | Medio |

**Posición del maintainer**: Meridian no sanitiza prompts por diseño. Lo dejó del lado del harness.

## OpenCode (anomalyco/opencode)

| Issue/PR | Problema | Estado |
|----------|----------|--------|
| PR #18186 | Anthropic pidió legalmente remover OAuth | Mergeado |
| #18267 | Anthropic provider removido | Cerrado |
| #18329 | 429/auth errors post-remoción | Cerrado |
| #20079 | Feature request: Claude Code bridge | Abierto |

## Claude Code (anthropics/claude-code)

| Issue | Problema | Estado |
|-------|----------|--------|
| #45016 | "Third-party apps" billing bug | Abierto |
| #45134 | Mismo error en CLI oficial para algunos | Abierto |

**Nota**: #45016 y #45134 muestran que el error aparece incluso en el CLI oficial,
lo que sugiere que el gating tiene falsos positivos o que el billing routing tiene bugs.

## Repos comunitarios auditados

### 1. cemalturkcan/opencode-anthropic-login-via-cli
- **Tipo**: Plugin OAuth + credential bridge
- **Calidad**: Buena — modularizado (introspection, credentials, pkce, fetch, transforms), con tests
- **Problema**: No sanitiza system prompt → gateado por Anthropic
- **Estado**: Activo con fixes recientes

### 2. griffinmartin/opencode-claude-auth
- **Tipo**: Plugin de autenticación
- **Problema**: No declara `oc-plugin` targets → `opencode plugin install` falla
- **Estado**: Activo

### 3. lehdqlsl/opencode-claude-auth-sync
- **Tipo**: Script de sync de credenciales
- **Ventaja**: Simple, auditable
- **Problema**: Solo sync tokens, no reescribe headers ni prompts

### 4. dotCipher/opencode-claude-bridge
- **Tipo**: Bridge in-process
- **Problema**: Alto acoplamiento a cambios de Anthropic

## Riesgos documentados

### Técnicos
- Anthropic puede cambiar heurísticas de detección en cualquier momento
- Meridian depende de credenciales de Claude CLI (expiran → re-login)
- Los MARKERS del shim pueden necesitar update si OpenCode cambia su prompt

### Compliance
- Consumer Terms prohíben acceso automatizado salvo via API key
- PR #18186 confirma pedido legal de Anthropic para la remoción
- Usar con tokens Pro/Max es zona gris contractual

### Mitigaciones implementadas
- Kill switch implícito: si Anthropic bloquea, falla limpio (502)
- Logs con cada rewrite y error para diagnóstico rápido
- --status verifica salud real de ambos componentes
- Graceful shutdown para no cortar requests en vuelo
