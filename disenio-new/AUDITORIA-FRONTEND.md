# Auditoría Frontend↔Backend — Resultados Completos

> Auditoría realizada el 2026-04-04, Sprint 34.
> Todos los bugs críticos fueron corregidos en Sprint 34.

---

## Resumen Ejecutivo

| Categoría | Encontrados | Corregidos | Pendientes |
|-----------|-------------|------------|------------|
| Críticos  | 10          | 10         | 0          |
| Warnings  | 17          | 10         | 7          |
| Info      | 12          | 0          | 12         |

---

## Pantallas Públicas — Estado Post-Fix

### Landing `/landing` — ✅ Alineada
- Stats "8 Precedentes TC" hardcodeado (info, no bloqueante)
- No hay sección de pricing (se agregará en rediseño)

### Login `/auth/login` — ✅ 100% Alineada
- Todos los campos, API calls y acciones correctos
- Rate limit (429) se muestra genéricamente (aceptable)

### Register `/auth/register` — ✅ 95% Alineada
- Pendiente: checkbox Terms & Privacy (se agregará en rediseño)
- API_URL duplicado en componente y lib/auth.ts (menor)

### Reset Password `/auth/reset-password` — ✅ 100% Alineada
- La página mejor implementada del conjunto

### OAuth Callbacks — ✅ CORREGIDO Sprint 34
- Suspense wrapper agregado a Google y Microsoft

### Onboarding `/onboarding` — ✅ Limpiado
- Dead code MODELS eliminado (47 líneas)
- Pendiente: role/areas solo en localStorage (se evaluará en rediseño)

### Compartido `/compartido/[id]` — ✅ 100% Alineada

### Status `/status` — ✅ 95% Alineada
- Redis verificado indirectamente (aceptable)

### Guía `/guia` — ✅ CORREGIDO Sprint 34
- FAQ API Keys actualizado (ya no dice "Próximamente")

### Docs `/docs` — ✅ CORREGIDO Sprint 34
- Links Swagger/ReDoc apuntan al backend
- JWT "7 days" → "60 minutos"

### Billing Success `/billing/success` — ✅ CORREGIDO Sprint 34
- Reescrito con Suspense + 3 estados MercadoPago
- Refresca plan del usuario post-pago

### Billing Cancel `/billing/cancel` — ✅ Funcional
- Backend URL corregida (billing.py)

---

## Pantallas Privadas — Estado Post-Fix

### Chat Principal `/` — ⚠️ Funcional con notas
- **Funcional**: streaming SSE, upload, feedback, bookmarks, export
- Pendiente (info): citations del evento SSE `done` no se muestran en UI
- Pendiente (info): `limit=30` param ignorado por backend
- Pendiente (info): evento `classification` del stream ignorado
- Daily usage indicator: TODO placeholder (Sprint 33)

### Historial `/historial` — ✅ Bien Alineada
- Tags y carpetas CRUD 100% funcionales
- Pendiente (info): sin paginación con muchas conversaciones
- Pendiente (info): editar nombre de carpeta no tiene UI

### Billing `/billing` — ✅ CORREGIDO Sprint 34
- `started_at` → `current_period_start` corregido
- Pendiente (info): planes hardcodeados vs dinámicos
- Pendiente (info): `usage` y `hasPaidSubscription` calculados pero no usados

### Buscador `/buscar` — ✅ Bien Alineada
- Todos los endpoints correctos
- Pendiente (info): filtro `source` no expuesto, export PDF no expuesto

### Configuración `/configuracion` — ✅ CORREGIDO Sprint 34
- "Abandonar org" implementado (endpoint backend existía)
- Pendiente (warning): memory toggle no persiste
- Pendiente (warning): preferencias solo en localStorage

### Organización `/organizacion` — ✅ CORREGIDO Sprint 34
- fetchMembers() agregado (tabla ya no está vacía)
- PLAN_COLORS/LABELS: "pro" → "base"

### Analytics `/analytics` — ✅ Bien Alineada
- Todos los endpoints correctos
- Pendiente (info): sin paginación en consultas recientes

### Admin `/admin` — ✅ CORREGIDO Sprint 34
- Endpoint cambiado: `/admin/queries/recent` → `/admin/activity`
- 5 field mismatches corregidos
- PLAN_COLORS actualizado

### Marcadores `/marcadores` — ✅ Bien Alineada
- Pendiente (info): sin deep-link a mensaje específico

### Notifications (componente) — ✅ Bien Alineada
- Pendiente (warning): link "Notificaciones" va a /configuracion

---

## Warnings Pendientes (no corregidos, menores)

| # | Área | Detalle | Impacto | Cuándo arreglar |
|---|------|---------|---------|-----------------|
| 1 | Chat | Citations no mostradas en UI | UX | Rediseño del chat |
| 2 | Settings | Memory toggle no persiste | UX | Necesita endpoint backend |
| 3 | Settings | Preferencias solo localStorage | UX | Necesita endpoint backend |
| 4 | Billing | Planes hardcodeados | Mantenimiento | Cuando cambien planes |
| 5 | Sidebar | Link notificaciones → /configuracion | UX | Rediseño sidebar |
| 6 | Auth | Sin token refresh mechanism | UX | Post-beta |
| 7 | Register | Sin Terms & Privacy checkbox | Legal | Rediseño register |

---

*Auditoría completada. Frontend listo para rediseño visual.*
