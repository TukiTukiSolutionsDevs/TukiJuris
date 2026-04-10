# Mejoras aplicadas al stack opencode-anthropic

## Fecha: 2026-04-09

## Shim (`~/.config/opencode/meridian-opencode-shim.js`)

### Antes vs Después

| Aspecto | Antes | Después |
|---------|-------|---------|
| Health | Proxyeaba /health a Meridian (mentía si Meridian caía) | Endpoint propio: reporta `healthy`/`degraded` + stats |
| Logging | 0 líneas útiles (solo startup msg) | Timestamp + reqId + nivel + contexto JSON por cada request |
| Shutdown | Corte abrupto (sin handler) | Graceful: SIGTERM/SIGINT con timeout 5s |
| System prompt | Hardcodeado en JS | Configurable via `OPENCODE_MERIDIAN_SYSTEM_PROMPT` |
| Body protection | Sin límite (OOM posible) | Cap 50MB con respuesta HTTP 413 |
| Error codes | Todo era 500 genérico | 502 (proxy error) vs 413 (too large) vs warn en JSON parse |
| JSON parse | Crash si body no era JSON válido | Try/catch con warning, forwarding raw body |
| Response check | Sin distinción | Log de warning si upstream devuelve >= 400 |

### Stats disponibles en /health

```json
{
  "status": "healthy",
  "shim": "running",
  "meridian": "reachable",
  "target": "http://127.0.0.1:3456",
  "stats": {
    "started": "2026-04-09T...",
    "requests": 42,
    "rewrites": 38,
    "errors": 0
  }
}
```

---

## Wrapper (`~/.local/bin/opencode-anthropic`)

### Comandos nuevos

| Comando | Antes | Después |
|---------|-------|---------|
| `--status` | curl raw a ambos puertos | Secciones separadas [Meridian] [Shim] |
| `--logs` | ✓ ya existía | ✓ sin cambios |
| `--tail` | No existía | `tail -f` ambos logs en vivo |
| `--restart` | No existía | `--stop` + sleep + start automático |
| `--stop` | Solo `lsof` para matar | PID files primero, fallback `lsof` |
| `--help` | No existía | Documentación completa inline |

### Infraestructura nueva

| Feature | Detalle |
|---------|---------|
| PID tracking | `~/.local/state/opencode-anthropic/pids/{meridian,shim}.pid` |
| Log rotation | Rota a `.old` cuando pasa `MAX_LOG_SIZE` (default 5MB) |
| Meridian CLI | Invocación directa `$cli` en vez de `bash -lc "$cli"` (más robusto) |

---

## Pendientes identificados

### P1 — Alta prioridad
- [ ] Evaluar si el plugin Meridian en `opencode.json` (línea 209-211) genera conflicto con el shim
- [ ] Agregar health check periódico en el shim

### P2 — Media prioridad
- [ ] LaunchAgent de macOS para Meridian + shim persistentes
- [ ] Monitoreo de `claude auth status` (alertar si se desloguea)
- [ ] Rotación de logs más sofisticada (mantener N archivos)

### P3 — Baja prioridad
- [ ] Preservar PARTE del contexto env en system prompt sin triggear detección
- [ ] Dashboard web local con stats
- [ ] Tests automatizados del shim (curl smoke test)
