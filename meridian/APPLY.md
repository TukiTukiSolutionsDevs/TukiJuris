# Pasos para aplicar mejoras v2

## IMPORTANTE
NO corras `opencode-anthropic --stop` desde DENTRO de opencode-anthropic.
Abrí una terminal NUEVA para hacer cambios.

## Paso 1 — Parar stack (terminal nueva)
```bash
opencode-anthropic --stop
```

## Paso 2 — Verificar archivos v2
Los archivos ya fueron escritos. Verificá:
```bash
head -3 ~/.config/opencode/meridian-opencode-shim.js
# Debe mostrar: const http = require("node:http")

head -3 ~/.local/bin/opencode-anthropic
# Debe mostrar: #!/usr/bin/env bash
```

## Paso 3 — Permisos
```bash
chmod +x ~/.local/bin/opencode-anthropic
```

## Paso 4 — Verificar
```bash
opencode-anthropic --help
opencode-anthropic --status
```

## Paso 5 — Smoke test
```bash
opencode-anthropic run --agent meridian-smoke "Reply only with OK"
```

## Paso 6 — Test con tools
```bash
opencode-anthropic run "Use tools if needed to tell me how many files named README.md exist in this repository. Reply only with the number."
```

## Paso 7 — Uso interactivo
```bash
opencode-anthropic
```

---

## Troubleshooting

### Shim no arranca
```bash
node --version        # Necesita 18.13+
ls -la ~/.config/opencode/meridian-opencode-shim.js
```

### Meridian no arranca
```bash
npm list -g @rynfar/meridian    # Verificar instalación
claude auth status               # Verificar auth
claude login                     # Re-login si expiró
```

### "Third-party apps" sigue apareciendo
```bash
opencode-anthropic --tail
# Buscar "system prompt rewritten" en los logs
# Si NO aparece, OpenCode cambió su prompt → actualizar MARKERS en el shim
```

### Logs crecen mucho
Los logs rotan automáticamente a .old al pasar 5MB.
Para limpiar manualmente:
```bash
> ~/.local/state/opencode-anthropic/meridian.log
> ~/.local/state/opencode-anthropic/shim.log
```

### Quiero cambiar el system prompt
```bash
OPENCODE_MERIDIAN_SYSTEM_PROMPT="Tu prompt custom" opencode-anthropic
```

### Puertos ocupados por procesos zombie
```bash
opencode-anthropic --stop          # Intenta PID files primero
lsof -ti tcp:3456 | xargs kill    # Fallback manual
lsof -ti tcp:4568 | xargs kill
```
