# TukiJuris — Design System & Production Spec (Workspace del Cliente)

> **Scope**: Este documento cubre **únicamente la zona autenticada del cliente regular** (no admin). Después de hacer login el usuario aterriza en este workspace. Lo que sigue es **el corazón del producto**: dónde el abogado peruano pasa horas analizando casos.
>
> **Relación con otros docs**:
> - [`DESIGN.md`](./DESIGN.md) — sistema base canónico (tokens, fundamentos)
> - [`DESIGN_PUBLIC.md`](./DESIGN_PUBLIC.md) — landing, marketing, auth, legal
> - **[este documento]** — workspace del cliente (post-login)
> - `DESIGN_BACKOFFICE.md` (pendiente) — panel admin
>
> **Version**: 1.0 — 2026-06-25
> **Compatibilidad**: Stitch (Google), Claude design tools, Figma ingest.
> **Frame**: dark theme primario · editorial denso · "estudio jurídico digital del abogado peruano profesional".

---

## 0. Mapa del workspace (post-login)

### 0.1 Inventario de rutas autenticadas

| Sección | Ruta | Propósito | Plan |
|---|---|---|---|
| **Producto-core** | `/analizar` | Pantalla principal — case-analysis con SSE | Todos |
| | `/buscar` | Corpus público (modo auth = AppLayout) | Todos |
| | `/historial` | Conversaciones pasadas + carpetas + tags | Todos |
| | `/marcadores` | Mensajes guardados favoritos | Todos |
| | `/documento/[id]` | Viewer de documento legal individual | Todos |
| | `/compartido/[id]` | Vista de conversación compartida | Sin auth |
| **Workspace** | `/notificaciones` | Bandeja de notificaciones | Todos |
| | `/configuracion` | Perfil, seguridad, preferencias, BYOK, memoria, archivos | Todos |
| | `/organizacion` | Miembros, roles, invitaciones | Todos |
| | `/analytics` | Métricas de uso, costos, top queries | Pro / Estudio |
| | `/billing` | Suscripción, planes, facturas, métodos pago | Todos |
| | `/onboarding` | Wizard 5 pasos primera vez | Nuevo user |
| **Soporte** | `/guia` | Tutoriales (también pública) | Todos |
| | `/docs` | API docs (también pública) | Todos |

### 0.2 Hallazgo crítico — 5 patrones de page-header coexistiendo en zona cliente

| Pattern | Usado en | Estado |
|---|---|---|
| `InternalPageHeader` (canonical) | `/analytics`, `/organizacion`, `/historial`, `/configuracion` | ✅ **canónico v3** |
| Custom header `bg-[#0e0e12]` sticky | `/billing`, `/buscar` (auth), `/analizar` | ⚠️ migrar a `InternalPageHeader` |
| Custom header `bg-[#0e0e14]` sticky | `/marcadores` | ⚠️ migrar a `InternalPageHeader` |
| Slim header sin icon/eyebrow | `/notificaciones` | ⚠️ migrar a `InternalPageHeader` |
| Wizard sin header (onboarding) | `/onboarding` | ✅ aceptable (caso especial) |

**Decisión canónica para v3**: **Toda página interna usa `InternalPageHeader`** con la siguiente signature:

```tsx
<InternalPageHeader
  icon={<Icon className="w-5 h-5 text-primary" />}
  eyebrow="Sección"
  title="Título"
  description="Descripción breve del propósito de esta pantalla."
  utilitySlot={<ShellUtilityActions />}
  actions={<PageActions />}
  compact={false}
/>
```

Excepciones permitidas:
- `/onboarding` — wizard de 5 pasos sin shell
- `/analizar` viewport mobile — header se compacta a 48 px sin description
- `/compartido/[id]` cuando se ve sin auth — usa `PublicLayout` simplificada

### 0.3 Hallazgo crítico — Color hardcoded everywhere

El workspace tiene > 40 hex codes hardcoded fuera del sistema de tokens. Algunos ejemplos detectados:

```
bg-[#0e0e12], bg-[#0e0e14], bg-[#1a3a2a], bg-[#93000a]/20, bg-[#4f3700]/40,
bg-[#2d1f4a], bg-[#0f2d35], bg-[#25242b], bg-[#35343a],
text-[#7c7885], text-[#a09ba8], text-[#6ee7b7], text-[#c4b5fd], text-[#67e8f9],
text-[#ffb4ab], text-[#55535d],
border-[rgba(79,70,51,0.15)], border-[rgba(79,70,51,0.20)], border-[rgba(79,70,51,0.30)]
```

Estos son alias de tokens semánticos legítimos que ya existen o deberían existir:
- `#0e0e12` / `#0e0e14` → `--background` o `--surface-dim`
- `#1a3a2a` / `#6ee7b7` → `--status-success` family
- `#93000a` / `#ffb4ab` → `--error-container` / `--error`
- `#4f3700` → `--primary-container` dark variant
- `#2d1f4a` / `#c4b5fd` → `--status-info` family (lila)
- `#0f2d35` / `#67e8f9` → cyan info family
- `#7c7885` / `#a09ba8` / `#55535d` → `--on-surface-*` variants
- `rgba(79,70,51,0.15)` → `--outline-variant`

**Migración masiva** documentada en §12.

### 0.4 Hallazgo crítico — Confirmaciones con `confirm()` nativo

Todas las acciones destructivas usan `confirm()` nativo del browser:
- `/marcadores` — quitar marcador
- `/historial` — eliminar conversación, eliminar carpeta, eliminar tag, bulk delete
- `/configuracion` — eliminar memoria, eliminar API key, eliminar archivo, "borrar TODA la memoria"
- `/organizacion` — eliminar miembro
- `/notificaciones` — sin confirm (eliminar es silencioso con undo no implementado)

UX consequence: el modal nativo rompe el rhythm visual, no respeta el dark theme, copy en inglés en algunos browsers. **Migrar a `ConfirmDialog` componente que respeta tokens** (ver §6.16).

### 0.5 Principios de UX para la zona cliente

5 principios que ordenan toda decisión en este documento:

#### UX-1. "El abogado conoce el camino al cierre"
Cada pantalla debe responder en < 1 segundo a la pregunta "¿qué hago ahora?". Concretamente:
- CTA principal **siempre visible** (sin scroll) — en `/analizar` es el composer; en `/historial` es "abrir conversación"; en `/configuracion` es "Guardar cambios".
- Empty states con CTA inmediato — nunca un dead-end. "No hay marcadores" → "Ir a /analizar".
- Breadcrumbs implícitos en `InternalPageHeader` eyebrow ("Cuenta", "Consultas", "Organización", "Equipo").

#### UX-2. "Persistencia agresiva del estado"
El abogado abre 3 pestañas y cierra el laptop. Cuando vuelve, el estado debe estar exactamente donde lo dejó:
- `case_state` persistido en DB (JSONB column ya implementado ✅)
- Selección de carpeta/tag en `/historial` → `localStorage` (hoy NO persiste, ver §12)
- Pestaña activa de `/configuracion` y `/analytics` → URL hash (hoy NO persiste, ver §12)
- Tema dark/light → cookie + localStorage ya implementado ✅
- Org seleccionada → `localStorage.tk_selected_org_id` ya implementado ✅

#### UX-3. "Reasoning en vivo es el producto"
El streaming SSE del orquestador NO es una animación de espera — **es el diferenciador competitivo**. El abogado quiere ver el agente "pensando" (intake → investigation → analysis → multi-agente). Decisiones:
- `ReasoningPanel` siempre visible cuando hay un turn activo
- Cada paso con nombre humano + duración (cuando el tiempo > 3 s)
- Modelo + reasoning effort siempre badge visible (badge gold)
- Un click en cualquier paso "done" debe mostrar más detalle (hover tooltip o expand) — **mejora futura**

#### UX-4. "Densidad alta sin ruido"
Abogado pro ≠ casual user. Densidad de información alta, pero sin alarmas innecesarias:
- 14 px body base (no 16 px)
- 36 px de altura para botones medianos (no 48 px)
- Disclosure cards (acordeón) por defecto colapsadas cuando sean secundarias (ej. "Cambiar contraseña", "Borrar memoria")
- Solo 1 toast a la vez (sonner ya lo hace ✅)
- Notificaciones de éxito desaparecen a 3 s, errores a 6 s (auto)
- Confirmaciones destructivas EXIGEN tipear texto (ej. "ELIMINAR") para acciones graves: borrar org, borrar cuenta, "borrar TODA la memoria"

#### UX-5. "Costos y plan siempre transparentes"
El abogado quiere saber qué está pagando y qué consume. Decisiones:
- `ContextBar` en `/analizar` muestra contexto consumido vs límite del modelo
- `UsageBadge` en sidebar footer muestra "X / Y consultas hoy" (hoy NO implementado en sidebar, ver §12)
- En `/billing` el plan actual destacado en `Card/Accent` con fecha de renovación
- En `/analytics` un tab "Costos" con desglose por modelo (ya implementado ✅)
- En `/configuracion` → API Keys, cada provider muestra estado: "Plataforma activa", "Tu key configurada", "Sin configurar"

---

## 1. Brand identity en el workspace

### 1.1 La transición de marketing → producto

El cliente cruzó por landing (aspiracional), auth (compromiso), y ahora aterriza en el workspace. El tono cambia:

| Dimensión | Marketing (landing) | Workspace (cliente) |
|---|---|---|
| **Mascota** | omnipresente (hero, CTAs) | mínima (solo empty states y onboarding) |
| **Animaciones** | abundantes (pulse-glow, float, shimmer) | sutiles (loading, transitions 200ms) |
| **Tipografía display** | hero 60 px shimmer | page-h1 28-32 px sólido |
| **Eyebrows** | "IA Jurídica para el Perú" — aspiracional | "Cuenta", "Equipo", "Consultas" — funcional |
| **CTAs** | "Comenzar Gratis →" gold-gradient pulsando | "Guardar cambios" gold-gradient estático |
| **Layout** | full-width, secciones py-24 | container max-w-6xl, secciones py-6 |
| **Densidad** | baja, mucha respiración | alta, mucha información por pantalla |
| **Color** | gold protagonista | gold acento, gris dominante |

### 1.2 Posicionamiento del workspace

> "TukiJuris para el abogado es como Notion + Linear + ChatGPT — pero hecho para derecho peruano. Lo rápido, denso y respetuoso del tiempo profesional, sin ornamento."

### 1.3 Mascota en el workspace

Reglas:
- ✅ Empty states sin datos: `/marcadores` vacío, `/historial` vacío, `/notificaciones` vacío — usar `logo-full.png` con `opacity-20` w-24 centrada
- ✅ Pantalla de carga `AppLayout` (boot refresh) — usa spinner pequeño, sin mascota
- ✅ Onboarding wizard step 1 (Bienvenida) — mascota grande pulsando
- ❌ Sidebar / topbar / cards / botones — sin mascota
- ❌ Side panel de `/analizar` — sin mascota (compite con ReasoningPanel)
- ❌ Modales — sin mascota

### 1.4 Iconografía del workspace

| Sección | Icono Lucide | Hex | Notas |
|---|---|---|---|
| Analizar caso | `FileSearch` | `--primary` | También en sidebar |
| Buscar corpus | `Search` | `--primary` | |
| Historial | `History` | `--primary` | |
| Marcadores | `Bookmark` | `--primary` | `fill="currentColor"` cuando guardado |
| Notificaciones | `BellRing` | `--primary` | Badge cuando hay unread |
| Analytics | `BarChart3` | `--primary` | |
| Organización | `Users` o `Building2` | `--primary` | |
| Facturación | `CreditCard` | `--primary` | |
| Configuración | `Settings` | `--primary` | |
| Documento | `FileText` | `--primary` | |
| Compartido | `Share2` | `--primary` | |
| Logout | `LogOut` | `--error` | Stroke 1.6 |
| Eliminar | `Trash2` | `--error` | |
| Editar | `Edit2` | `--on-surface-variant` | Aparece on-hover |
| Pin / Fijar | `Pin` | `--primary` cuando activo, `--on-surface-variant` cuando inactive | |
| Archivar | `Archive` | `--on-surface-variant` | |
| Carpeta | `Folder` / `FolderOpen` | `--primary` cuando activa | |
| Tag | `Tag` | el color asignado al tag | |
| Compartir | `Share2` | `--primary` | |

Patrón canónico: stroke-width 1.6, tamaño relacionado al tipo de elemento:
- Inline en text → 12-14 px
- En botones → 14-16 px
- En page header → 20 px
- En empty state → 32-48 px

---

## 2. Estructura informacional canónica

### 2.1 Workspace shell anatomy (desktop ≥ lg)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ ◄ ─ Sidebar ─ ►│  ◄ ─ Topbar ─ ► │  ◄ ─ Right rail (opcional) ─ ►              │
│  284px         │  56px           │  320px                                       │
│ ┌──────────────┼──────────────────────────────────────────────┬──────────────┐ │
│ │ Brand + tag  │ ⚖ Analizar caso / Historial / ...   👁🔔⚙  │              │ │
│ │              │                                              │              │ │
│ │ [+ Nuevo]    ├──────────────────────────────────────────────┤   Side rail  │ │
│ │ ⌘K           │ ╔══════════════════════════════════════════╗ │              │ │
│ │              │ ║ InternalPageHeader (76 px)               ║ │  - Hechos    │ │
│ │ ─ Principal ─│ ║ icon + eyebrow + title + desc + actions  ║ │  - Preguntas │ │
│ │ Analizar     │ ╚══════════════════════════════════════════╝ │  - How it    │ │
│ │ Buscar       │                                              │    works     │ │
│ │              │ ╔══════════════════════════════════════════╗ │              │ │
│ │ ─ Organiz. ─ │ ║                                          ║ │              │ │
│ │ Historial    │ ║         Page content                     ║ │              │ │
│ │ Marcadores   │ ║         (max-w-6xl mx-auto, px-6)        ║ │              │ │
│ │ Notif.       │ ║                                          ║ │              │ │
│ │              │ ║                                          ║ │              │ │
│ │ ─ Gestión ─  │ ║                                          ║ │              │ │
│ │ Analytics    │ ║                                          ║ │              │ │
│ │ Org          │ ║                                          ║ │              │ │
│ │ Billing      │ ║                                          ║ │              │ │
│ │              │ ║                                          ║ │              │ │
│ │ ─ Config ─   │ ╚══════════════════════════════════════════╝ │              │ │
│ │ Config       │                                              │              │ │
│ │ Guía / Docs  │                                              │              │ │
│ │              │                                              │              │ │
│ │ [avatar+menu]│                                              │              │ │
│ └──────────────┴──────────────────────────────────────────────┴──────────────┘ │
└────────────────────────────────────────────────────────────────────────────────┘
```

Dimensions canónicas:
- Sidebar: `284px` expandido / `80px` colapsado / `300px` drawer mobile
- Topbar: `56px` fija
- InternalPageHeader: `76px` con description, `48px` compact mode
- Right rail: `320px` solo en `xl+` (1280px+)
- Content max-width: `1152px` (`max-w-6xl`) centrada con `px-6`

### 2.2 Information architecture — orden mental del usuario

Las 5 secciones del sidebar siguen una pirámide de uso:

```
┌─────────────────────────────────────┐
│ PRINCIPAL (lo que hago todo el día) │  ← 80% del tiempo
│   - Analizar caso                   │
│   - Buscar corpus                   │
├─────────────────────────────────────┤
│ ORGANIZACIÓN (mis casos pasados)    │  ← 15% del tiempo
│   - Historial                       │
│   - Marcadores                      │
│   - Notificaciones                  │
├─────────────────────────────────────┤
│ GESTIÓN (mi equipo y números)       │  ← 4% del tiempo
│   - Analytics (Pro+)                │
│   - Organización                    │
│   - Facturación                     │
├─────────────────────────────────────┤
│ CONFIGURACIÓN (setup ocasional)     │  ← 1% del tiempo
│   - Configuración                   │
│   - Guía                            │
│   - API Docs                        │
└─────────────────────────────────────┘
```

Reglas de orden:
- **Sticky orden** — sin drag-reorder en MVP (evita decisiones erróneas del usuario)
- **Badge de notificaciones** en `Notificaciones` con count + animación pulse
- **Indicador de uso** en `Analizar caso` cuando se acerca al límite del plan (futura)

### 2.3 Visibilidad de items por plan

Item | Free | Pro | Estudio
---|---|---|---
Analizar | ✅ | ✅ | ✅
Buscar | ✅ | ✅ | ✅
Historial | ✅ (7 días) | ✅ ilimitado | ✅ ilimitado
Marcadores | ✅ | ✅ | ✅
Notificaciones | ✅ | ✅ | ✅
Analytics | ⚠️ con upsell modal | ✅ | ✅
Organización | ✅ (1 user) | ✅ (1 user) | ✅ (5+ users)
Facturación | ✅ | ✅ | ✅
Configuración | ✅ | ✅ | ✅
Guía | ✅ | ✅ | ✅
API Docs | ✅ | ✅ | ✅

**Lock pattern**: items disponibles pero gated (Analytics en plan Free) muestran `Lock` icon sutil al lado del label en sidebar. Click → `UpsellModal` con CTA a `/billing`.

---

## 3. Color tokens (workspace)

> Misma fuente canónica que `DESIGN.md` §3. Aquí especifico los tokens específicos del workspace y elimino el caos de hex hardcoded.

### 3.1 Surface stack del workspace

Token | Dark | Light | Uso específico
---|---|---|---
`--background` | `#191918` | `#F5F2EB` | bg root del shell
`--surface-dim` | `#0E0E14` | `#EDE9E0` | sticky page headers (reemplaza `bg-[#0e0e12]` y `bg-[#0e0e14]` actuales)
`--surface` | `#1F1F1E` | `#FFFFFF` | sidebar, cards primarios
`--surface-container-low` | `#1A1F1E` | `#F9F6F0` | cards secundarios, filas alternas
`--surface-container` | `#27272A` | `#F0EDE6` | inputs, hover surfaces, dropdowns
`--surface-container-high` | `#2E2E30` | `#E8E4DB` | active states, sticky bars
`--surface-container-highest` | `#353B48` | `#DDD9D0` | modals sobre modals
`--inverse-surface` | `#F0EBE1` | `#313027` | toast, snackbar

### 3.2 Status palette del workspace

Token | Hex (dark) | Uso |
---|---|---
`--status-success` | `#8BC98B` | Análisis completo, validaciones OK, "Marcar leída", success banners
`--status-success-soft` | `rgba(139,201,139,0.10)` | bg de banners success (reemplaza `bg-[#1a3a2a]/60`)
`--status-success-on` | `#6EE7B7` | texto sobre success-soft (reemplaza `text-[#6ee7b7]`)
`--status-warning` | `#E8B30E` | Contexto 60-85%, advertencias, "Pago pendiente" suave
`--status-warning-soft` | `rgba(232,179,14,0.10)` | bg amarillo suave
`--status-danger` | `#E06B5C` | Errores, eliminar
`--status-danger-soft` | `rgba(224,107,92,0.10)` | bg banner error
`--status-danger-on` | `#FFB4AB` | texto sobre danger-soft (reemplaza `text-[#ffb4ab]`)
`--status-info` | `#B3A4F0` | Jurisprudencia, tips
`--status-info-soft` | `rgba(179,164,240,0.10)` | bg info purple suave
`--status-info-on` | `#C4B5FD` | texto sobre info-soft (reemplaza `text-[#c4b5fd]`)
`--status-cyan` | `#67E8F9` | Memoria/contexto chips
`--status-cyan-soft` | `rgba(103,232,249,0.10)` | bg cyan chip

### 3.3 Áreas legales (29 colores canónicos)

Vienen ya definidos en `apps/web/src/app/chat/constants.ts:LEGAL_AREAS` y `AREA_HEX_COLORS`. **Migrar a tokens CSS**:

```css
--area-civil: #9BB5D8;          /* azul claro, navy soft */
--area-familia: #E8B6D8;        /* rosa familiar */
--area-penal: #E06B5C;          /* rojo lacre apagado */
--area-procesal: #C49EE8;       /* púrpura procesal */
--area-laboral: #C9A84C;        /* gold canónico */
--area-seguridad-social: #D8C58C; /* gold pálido */
--area-tributario: #8BC98B;     /* verde dinero */
--area-aduanas: #7AB89C;        /* verde aduana */
--area-administrativo: #9CC4B8; /* verde-azul gob */
--area-corporativo: #E8B30E;    /* gold cálido */
--area-comercial: #F0C45C;      /* amarillo comercial */
--area-constitucional: #B3A4F0; /* lila TC */
--area-registral: #FFB1D0;      /* pink registral */
--area-notarial: #D8B8E8;       /* lavanda notarial */
--area-competencia: #FFCE6E;    /* gold competencia */
--area-consumidor: #FFA17C;     /* naranja consumidor */
--area-propiedad-intelectual: #D8A8FF; /* lila PI */
--area-datos-personales: #6FE5E5; /* cyan datos */
--area-compliance: #A4C4F0;     /* azul compliance */
--area-comercio-exterior: #4ECDC4; /* turquesa */
--area-financiero: #FFD93D;     /* amarillo finanzas */
--area-mercado-valores: #4ECDC4; /* verde-azul SMV */
--area-seguros: #B5D8E8;        /* azul seguros */
--area-ambiental: #7BAB5A;      /* verde tierra */
--area-minero: #B89968;         /* tierra minera */
--area-hidrocarburos: #E8946E;  /* naranja petróleo */
--area-telecom: #6E94E8;        /* azul telecom */
--area-transporte: #94B86E;     /* verde-pasto */
--area-salud: #E86E94;          /* rojo salud */
--area-contrataciones-estado: #9CC4B8; /* mismo que admin */
```

Patrón de uso de área (consolidado):
- **Chip de área** (en `/analizar`, `/historial`, `/marcadores`, `/buscar`):
  ```css
  background: rgba(area, 0.14);
  color: var(--area-X);
  border: 1px solid rgba(area, 0.20);
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-weight: 600;
  ```
- **Dot indicator** en analytics: `width: 8px; height: 8px; background: var(--area-X);`
- **Bar fill** en stats: `background: var(--area-X);`

### 3.4 Plan colors (consolidar duplicación)

Hoy duplicado en `/billing/page.tsx` y `/organizacion/page.tsx`. Centralizar en `globals.css`:

```css
.plan-badge-free {
  background: var(--surface-container);
  color: var(--on-surface-variant);
  border: 1px solid var(--outline-variant);
}
.plan-badge-pro {
  background: var(--primary-soft);
  color: var(--primary);
  border: 1px solid rgba(201,168,76,0.25);
}
.plan-badge-studio {
  background: var(--status-info-soft);
  color: var(--status-info-on);
  border: 1px solid rgba(179,164,240,0.25);
}
```

### 3.5 Rol colors (consolidar duplicación)

Hoy en `/organizacion`. Centralizar:

```css
.role-badge-owner {
  background: var(--primary-soft);
  color: var(--primary);
}
.role-badge-admin {
  background: var(--secondary-container);
  color: var(--on-secondary-container);
}
.role-badge-member {
  background: var(--surface-container-low);
  color: var(--on-surface-variant);
  border: 1px solid var(--outline-variant);
}
```

---

## 4. Typography del workspace

### 4.1 Densidad alta — escala compacta

El workspace tiene una densidad mayor que landing. Type scale específica:

Token | Family | Size | Line-height | Weight | Uso
---|---|---|---|---|---
`page-h1` | display | 28-32 px | 1.20 | 700 | InternalPageHeader title
`page-eyebrow` | body | 10 px | 1.40 | 800 | "CUENTA", "EQUIPO", "CONSULTAS" en page header (uppercase tracking 0.16em)
`page-description` | body | 13 px | 1.50 | 400 | Description al lado del page h1
`section-h2` | display | 21 px | 1.25 | 700 | SectionHeader title (DisclosureCard, SectionCard)
`section-eyebrow` | body | 10 px | 1.40 | 800 | Eyebrow de sección (uppercase 0.22em tracking) — utility `.section-eyebrow`
`card-h3` | display | 17 px | 1.30 | 600 | Card titles secundarios
`card-h3-newsreader` | display | 17-20 px | 1.30 | 500 | Card titles editorial (Newsreader)
`stat-value` | display | 28 px | 1.15 | 700 | Números grandes en StatCard
`body` | body | 14 px | 1.55 | 400 | Texto base UI
`body-tight` | body | 14 px | 1.45 | 400 | Tablas, listas densas
`body-sm` | body | 13 px | 1.50 | 400 | Secondary text
`micro` | body | 11.5 px | 1.40 | 400 | Helper, timestamps
`label-input` | body | 11 px | 1.35 | 500 | Labels de inputs (uppercase tracking 0.18em) — utility `.label-input`
`badge` | body | 10.5 px | 1.30 | 700 | Chips, area badges (uppercase tracking 0.12em)
`code-mono` | mono | 12 px | 1.50 | 400 | Modelos, IDs, scores numéricos (`tabular-nums`)

### 4.2 Newsreader vs Manrope reglas en workspace

| Elemento | Family | Por qué |
|---|---|---|
| Logo wordmark, page-h1, section-h2 | Newsreader | Brand editorial |
| Body, labels, botones, chips | Manrope | Legibilidad densa |
| StatCard value (números grandes) | Newsreader | Editorial — números importantes |
| Mensajes del agente (markdown content) | **Mixto** — Newsreader para H1/H2/H3 dentro del análisis, Manrope para body | Replica documento legal |
| Modelo IDs, scores BM25, latencias | mono (Geist/SF Mono) | Datos técnicos |
| Fechas | Manrope tabular-nums | Densidad |

### 4.3 Highlights canónicos en markdown del agente

Para destacar conceptos legales en mensajes del orquestador:

```css
.message-strong {
  font-weight: 600;
  color: var(--on-surface);
  background: linear-gradient(to top, rgba(201,168,76,0.28) 40%, transparent 40%);
  padding: 0 3px;
}
```

Este patrón (highlight gold soft inferior) ya está en `globals.css` namespace `.c-em` — promover a canónico.

---

## 5. Spacing & layout (workspace)

### 5.1 Container max-widths por sección

Sección | Max-width | Tailwind | Justificación
---|---|---|---
`/analizar` con side panel | `none` (fill) + grid 1fr 320px | `grid lg:grid-cols-[1fr_320px]` | Necesita ancho completo
`/historial` | `none` (fill) + sidebar 260px | `flex gap-5` | Sidebar carpetas + tags
`/marcadores`, `/notificaciones`, `/billing` | 1024 px | `max-w-4xl` o `max-w-5xl` | Lectura cómoda
`/buscar` (auth) | 1024 px | `max-w-5xl` | Resultados como cards |
`/configuracion` | 1280 px | `max-w-7xl` | Tabs verticales + content
`/analytics` | 1280 px | `max-w-7xl` | Charts + tables wide |
`/organizacion` | full width | `w-full` | Members table + side stats
`/onboarding` | 896 px | `max-w-4xl` | Wizard centrado

### 5.2 Padding canónico

Element | Padding | Tailwind
---|---|---
Page content | `px-4` mobile, `px-6` desktop, `py-6` | `px-4 py-6 sm:py-8 lg:px-6 xl:px-8`
Card | `p-5` mobile, `p-6` desktop | `p-5 sm:p-6`
Form group | gap 16 px vertical | `space-y-4`
Tab content | gap 16 px vertical | `space-y-4`
Sidebar item | `8px 12px` | `px-3 py-2`
Page header | `px-6 py-5` | `px-6 py-5`

### 5.3 Grid de side panel y conversation

```css
/* /analizar — grid de 2 columnas */
grid-template-columns: 1fr 320px;
gap: 24px;

/* < xl (1280px): side panel se oculta */
@media (max-width: 1279px) {
  grid-template-columns: 1fr;
}
.side-panel { display: none; }
```

### 5.4 Sticky elements

| Element | Top | z-index | Bg |
|---|---|---|---|
| TopBar | 0 | 50 | `--background` |
| InternalPageHeader (sticky cuando hay scroll) | 56 px (debajo de TopBar) | 40 | `--surface-dim` |
| Sidebar | 0 | 30 | `--surface` |
| Right rail (sticky parts dentro del rail) | 76 px (debajo de TopBar + header) | 20 | inherit |
| Toast container (sonner) | 16 px | 60 | inherit |
| Modal | 0 | 100 | backdrop `rgba(0,0,0,0.6) blur(8px)` |

---

## 6. Components canónicos del workspace

### 6.1 `WorkspaceShell` (canonical)

Path: `apps/web/src/components/shell/WorkspaceShell.tsx`

Slots:
- `sidebar` (obligatorio) — `<AppSidebar />`
- `topbar` (obligatorio) — `<ShellTopbar />`
- `mobileDrawer` (obligatorio) — `<ShellMobileDrawer />`
- `children` — page content
- `rightRail` (opcional) — para `/analizar`, futuro `/historial?conversation=X`
- `contentClassName` — override del wrapper de contenido

**Reglas**:
- Width sidebar: 284 px desktop, 80 px collapsed, hidden < lg
- Right rail width: 320 px, oculto < xl
- Content: `flex-1 min-w-0 overflow-y-auto bg-background`
- Si `isLoading` o `!user` → mostrar loading shell con spinner (ya implementado ✅)

### 6.2 `AppSidebar` (canonical)

Path: `apps/web/src/components/AppSidebar.tsx`

Ya implementado con namespace `.n-*` — para v3 migrar tokens a canónicos.

Estructura:
```
┌────────────────────────────┐
│ [Logo] TukiJuris           │  ← header 76 px
│        — Abogados —        │
├────────────────────────────┤
│ ⊕ Nuevo caso (gold-grad)   │  ← Quick actions 60 px
│ 🔍 Buscar workspace ⌘K     │
├────────────────────────────┤
│ PRINCIPAL                  │  ← Section labels 10px uppercase
│   📄 Analizar caso         │
│   🔍 Buscar                │
│                            │
│ ORGANIZACIÓN               │
│   🕒 Historial             │
│   🔖 Marcadores            │
│   🔔 Notificaciones    (3) │  ← Badge de unread count
│                            │
│ GESTIÓN                    │
│   📊 Analytics             │
│   🏢 Organización          │
│   💳 Facturación           │
│                            │
│ CONFIGURACIÓN              │
│   ⚙ Configuración          │
│   ❓ Guía                  │
│   📘 API Docs              │
├────────────────────────────┤
│ [avatar] Nombre        PRO │  ← Footer 76 px
│ email@dominio.pe           │
│ [↔] [☀] [🔔3] [⏻]          │  ← Actions row
└────────────────────────────┘
```

**Estados**:
- `idle` — gris medio
- `hover` — bg `--surface-container`
- `active` — bg `--surface-container-high` + accent bar gold 3px izquierda
- `focus-visible` — outline gold

**Collapsed (80 px)**:
- Solo iconos centrados
- Tooltips on hover (definir copy)
- Badge se convierte en dot
- Footer apila vertical
- Botón "expandir" en footer

### 6.3 `ShellTopbar` (canonical)

Path: `apps/web/src/components/shell/ShellTopbar.tsx`

```
┌────────────────────────────────────────────────────────────────────┐
│ ⌘ Tukijuris ›  Analizar caso             [☀] [❓] [🔔3] | [+]      │
└────────────────────────────────────────────────────────────────────┘
```

- height: 56 px
- bg: `--background` (más sutil que sidebar)
- border-bottom: 1px `--outline-variant`
- Mobile: hamburger en lugar de logo

**Slots**:
- Breadcrumb (logo + path) — left
- Status chip (opcional) "Conectado", "Procesando" — center-left
- Utility actions (theme, help, notifications) — right
- Primary action (opcional) — far right

### 6.4 `InternalPageHeader` (canonical — ESTE ES EL COMPONENTE A UNIVERSALIZAR)

Path: `apps/web/src/components/shell/InternalPageHeader.tsx` (ya existe)

Ya implementado en `/analytics`, `/organizacion`, `/historial`, `/configuracion`. **Migrar todas las demás pantallas a este patrón**.

Spec canónica:

```tsx
<InternalPageHeader
  icon={<History className="w-5 h-5 text-primary" />}
  eyebrow="Consultas"
  title="Historial"
  description="Revisá conversaciones, carpetas y estados sin romper la jerarquía del shell privado."
  utilitySlot={<div className="hidden md:flex"><ShellUtilityActions /></div>}
  actions={<DateRangeSelector + ExportButton + RefreshButton />}
  compact={false}
/>
```

Anatomy:
```
┌─────────────────────────────────────────────────────────────────────┐
│ [icon]  EYEBROW                              [utility]  [actions]   │
│         Title                                                       │
│         Description                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

- Container: `border-b border-outline-variant px-6 py-5 sticky top-0 z-10 bg-surface-dim`
- Icon: 20 px en círculo o cuadrado bg-primary/10 rounded-xl (opcional)
- Eyebrow: `page-eyebrow` (10 px uppercase tracking 0.16em) color `primary/80`
- Title: `page-h1` (28 px Newsreader weight 700)
- Description: `page-description` (13 px) color `on-surface/50`
- Layout: eyebrow + title + description en columna left; utility + actions en row right
- En mobile (< md): description oculta, actions wrap

Variant `compact={true}`:
- Sin description
- height total 48 px
- Solo title + utility

### 6.5 `ShellUtilityActions` (canonical)

Path: `apps/web/src/components/shell/ShellUtilityActions.tsx` (ya existe)

Renders: theme toggle, help popover, notifications bell, divider, settings link

Props:
- `compact?: boolean` — versión sin labels
- `showSettingsLink?: boolean` — útil para que `/configuracion` no muestre el link a sí mismo

### 6.6 `Composer` para `/analizar` (canonical)

Componente de input multilinea con paperclip + send. Hoy inline en `/analizar/page.tsx:835-887`. **Extraer a `apps/web/src/components/analizar/Composer.tsx`** para reusabilidad.

Spec:
```
┌──────────────────────────────────────────────────────────┐
│ [📎]  Describe tu situación...                    [▶]   │
│                                                          │
└──────────────────────────────────────────────────────────┘
El agente irá pidiendo datos progresivamente. Cuando tenga lo
suficiente, pasará al análisis final.
```

- Container: `border border-outline-variant hover:border-primary/50 rounded-lg bg-surface p-1 flex items-end gap-1`
- Paperclip: 40px square ghost button (hoy disabled con toast "próximamente")
- Textarea: `rows={2}` autogrow hasta `rows={6}`, `bg-transparent` sin border interno
- Send: `gold-gradient` 40px square con `FileText` icon (o `Send` mejor), disabled cuando empty o loading
- Helper: `text-[10px] text-on-surface/30 px-1 pt-1`
- Enter sends, Shift+Enter newline
- Estado loading: spinner en send, textarea deshabilitada
- Composer **siempre visible** incluso en phase=complete (permite continuar caso)

**Mejora UX-1 (recomendada)**: enviar con `Ctrl/Cmd+Enter` también para usuarios mac-style.

### 6.7 `ReasoningPanel` (canonical)

Ya implementado en `/analizar/page.tsx:90-199`. Documentado en `DESIGN.md §6.8`.

**Mejora UX-3 propuesta** para v3:
- Mostrar duración de cada paso cuando > 3 s (ej. `"Recuperando jurisprudencia... 4.2s"`)
- Tooltip on hover sobre paso `done` que expande: "Encontrados 12 fragmentos · Áreas: Civil, Constitucional"
- Animación `fade-in-up` 200 ms al agregar fila nueva
- Active row con bg `primary-soft` para destacar (hoy es solo color del texto)

### 6.8 `ContextBar` (canonical)

Ya implementado en `/analizar/page.tsx:227-284`. Documentado en `DESIGN.md §6.9`.

**Mejora UX-5 propuesta**:
- Hover en counter → tooltip con desglose: "Mensajes: 12K · Hechos: 800 · System: 3K"
- Cuando se acerca al 85%, banner `Card/Sunken` debajo con "Considera iniciar un nuevo caso"

### 6.9 `CaseStatusBar` (canonical)

Ya implementado en `/analizar/page.tsx:290-354`. Documentado en `DESIGN.md §6.10`.

**Mejora UX-2 propuesta**:
- Cuando carga `?conversation=X`, mostrar chip adicional "Continuando caso de [fecha relativa]"

### 6.10 `SidePanel` (right rail de `/analizar`) (canonical)

Componente actual: `<aside className="hidden lg:flex flex-col gap-4">` en `/analizar/page.tsx:891-961`.

**Extraer a `apps/web/src/components/analizar/SidePanel.tsx`**.

3 sub-cards:
- `CaseFactsCard` — Hechos extraídos del intake
- `PendingQuestionsCard` — Preguntas abiertas
- `HowItWorksCard` — Solo en empty state, explica intake/investigation/analysis

**Mejora UX-4 propuesta**:
- `CaseFactsCard` editable inline: click en valor → input → enter para guardar (futuro)
- Drag-reorder de facts (futuro)

### 6.11 `MessageBubble` (canonical)

Mensaje user vs assistant. Hoy inline en `/analizar/page.tsx:760-801`. Extraer a `apps/web/src/components/analizar/MessageBubble.tsx`.

Anatomy:
```
[avatar] ┌────────────────────────────────────┐
         │ AGENT META · area                  │
         │ Markdown rendered content          │
         │                                    │
         │ [💾 Guardar] [↗ Compartir] [⋮]    │ ← solo en assistant
         └────────────────────────────────────┘
```

Variants:
- `user` — avatar primary bg, mensaje right-aligned, bg `primary/10`
- `assistant` — avatar surface bg con border, mensaje left-aligned, bg `surface-container-low`

Actions on assistant (mostrar on hover):
- Bookmark toggle (Bookmark icon, fill cuando guardado)
- Copy markdown (Copy icon)
- Share message (Share2 icon)
- More menu (MoreHorizontal icon) — futuro: regenerar, calificar

### 6.12 `StatCard` (canonical)

Ya implementado en `/analytics/page.tsx:130-150`. Extraer a `apps/web/src/components/ui/StatCard.tsx`.

```
┌──────────────────────────┐
│ LABEL                 [icon]│
│                            │
│ 1,234                     │  ← Newsreader 28px bold primary
│                            │
│ ↑ +12% vs ayer            │  ← TrendIndicator
└──────────────────────────┘
```

- Container: `panel-base rounded-xl p-6`
- Label: `section-eyebrow` color `--on-surface-subtle`
- Value: `stat-value` color `--primary`
- Sub: row con trend o secondary metric
- Loading: replace value/sub con `Skeleton`

### 6.13 `TrendIndicator` (canonical)

Ya implementado en `/analytics/page.tsx:302-334`. Extraer a `apps/web/src/components/ui/TrendIndicator.tsx`.

```tsx
<TrendIndicator value={+12.5} suffix="%" />
// Renders: ↑ +12.5% (green)

<TrendIndicator value={-8.2} suffix="%" />
// Renders: ↓ -8.2% (red)

<TrendIndicator value={0} />
// Renders: − 0% (gray)

<TrendIndicator value={null} />
// Renders: — (gray)
```

### 6.14 `LatencyBadge` (canonical)

Ya en `/analytics`. Extraer.
- ms < 2000 → verde
- ms < 5000 → gold
- ms ≥ 5000 → rojo
- mono font `tabular-nums`

### 6.15 `AreaBadge` (canonical)

Ya en `/analytics`, `/marcadores`, `/historial`, `/buscar`. **Centralizar** en `apps/web/src/components/ui/AreaBadge.tsx`:

```tsx
<AreaBadge area="laboral" size="sm" /> 
// dot + label, área hex color from --area-laboral
```

Variants:
- `size="sm"` — 10 px text + 5 px dot
- `size="md"` — 12 px text + 6 px dot
- `size="lg"` — 14 px text + 8 px dot
- `variant="solid"` — bg full area color soft, text area color
- `variant="dot"` — solo dot + label sin bg

### 6.16 `ConfirmDialog` (canonical — A CREAR)

**Reemplaza `confirm()` nativo**.

```tsx
<ConfirmDialog
  open={open}
  onOpenChange={setOpen}
  title="Eliminar conversación"
  description="Esta acción es irreversible. La conversación y sus mensajes se eliminarán permanentemente."
  variant="danger"
  confirmLabel="Eliminar"
  cancelLabel="Cancelar"
  requireTyping="ELIMINAR"   // opcional — para acciones graves
  onConfirm={handleDelete}
/>
```

Variants:
- `default` — confirm gold-gradient, cancel ghost
- `danger` — confirm `bg-error-container text-on-error`, cancel ghost
- `warning` — confirm `bg-status-warning-soft text-status-warning`, cancel ghost

`requireTyping` activa un input obligatorio que debe tener exactamente ese texto para habilitar el botón confirm.

Modal spec:
- Width: 480 px (480px max-w)
- Padding: 24 px
- Title: section-h2 (Newsreader 21 px)
- Description: body-tight (14 px)
- Footer: 2 botones right-aligned con gap 8 px
- Backdrop: `bg-inverse-surface/60 backdrop-blur-sm`
- Enter to confirm (si no hay requireTyping), Esc to cancel

**Adopción**: reemplazar TODOS los `confirm()` calls (encontrados en `/marcadores`, `/historial` (8+ usos), `/configuracion` (4+ usos), `/organizacion`).

### 6.17 `DisclosureCard` (canonical)

Ya implementado en `/configuracion/page.tsx:145-189`. **Centralizar** en `apps/web/src/components/ui/DisclosureCard.tsx`.

Patrón de acordeón con icon + title + description + chevron + body. Body se colapsa a "Oculto para reducir ruido visual" cuando cerrado.

### 6.18 `SectionCard` (canonical)

Ya en `/configuracion`. Centralizar.

```tsx
<SectionCard className="overflow-hidden">
  <SectionHeader icon={<User />} title="..." description="..." />
  <form>...</form>
</SectionCard>
```

### 6.19 `Skeleton` (canonical)

Hoy en `/analytics:110-116`. Centralizar.

```tsx
<Skeleton className="h-3 w-24" />
```

- bg: `--surface-container` o `--surface-container-high`
- animation: `pulse` (Tailwind default) o `shimmer` (más elegante)
- border-radius: 4 px default, override via className

Patrón shimmer recomendado:
```css
.skeleton {
  background: linear-gradient(90deg, var(--surface-container) 0%, var(--surface-container-high) 50%, var(--surface-container) 100%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: 4px;
}
```

### 6.20 `EmptyState` (canonical — A CREAR como patrón unificado)

Hoy hay 4 variantes en el workspace (`/marcadores`, `/historial`, `/notificaciones`, `/organizacion`). Consolidar:

```tsx
<EmptyState
  icon={<Bookmark className="w-12 h-12" />}   // o `mascot={true}` para usar logo opacity 20
  title="No hay marcadores guardados"
  description="Guarda las respuestas más útiles haciendo clic en el icono de marcador en cualquier mensaje del asistente."
  action={
    <Link href="/analizar" className="cta-primary-md">
      <Scale className="w-4 h-4" />
      Ir a analizar
    </Link>
  }
/>
```

Layout: centered, max-w-md, py-20.

Variants:
- `mascot={true}` — usa `logo-full.png` opacity 20 w-24
- `icon` — Lucide icon en circle bg primary/10

### 6.21 `Toast` (sonner, ya implementado)

Ya configurado en `layout.tsx:77`. **Eliminar el toast custom de `/notificaciones`** y migrar a sonner.

Reglas de copy:
- Éxito: "Marcador guardado", "Cambios aplicados", "Conversación archivada" (corto, pasado)
- Error: "No se pudo eliminar el archivo. Intentá de nuevo." (claro, accionable)
- Info: "Tu sesión expira en 5 minutos"
- Warning: "Quedan 2 consultas en tu plan"

Duración:
- success / info → 3 s
- warning → 4.5 s
- error → 6 s
- destructive con undo → infinite con close

### 6.22 `BarChart` y `DonutChart` (canonical)

Ya en `/analytics`. **Centralizar** en `apps/web/src/components/ui/charts/`:
- `BarChart.tsx` — pure CSS bars
- `DonutChart.tsx` — conic-gradient SVG mask

Reglas:
- Color principal: `--primary`
- Hover state: `--primary-container`
- Tooltip on hover con `bg-surface border border-outline-variant` + caption text
- Cuando empty: "Sin datos en este periodo" centrado

Para charts más complejos (futuros: heatmap, line chart de tiempo), considerar `recharts` integration.

### 6.23 `OrgSwitcher` (canonical)

Ya implementado en `/components/OrgSwitcher.tsx`. Aparece en:
- `/analytics` header (cuando orgs > 1)
- `/billing` header (cuando orgs > 1)

Dropdown que cambia `localStorage.tk_selected_org_id` y re-fetcha data.

### 6.24 `UsageBadge` (canonical — A CREAR para sidebar footer)

Mostrar consumo del plan en sidebar footer:

```
┌──────────────────────────┐
│ ▓▓▓▓▓░░░░░  3/4 hoy      │  ← compact
└──────────────────────────┘
```

- Solo en plan Free (Pro = ilimitado)
- Color: `--status-success` < 60%, `--status-warning` 60-80%, `--status-danger` ≥ 80%
- Tooltip on hover: "3 normales + 1 razonamiento usados de 4+1 hoy"

### 6.25 `FeatureGate` y `UpsellModal` (ya existen)

`apps/web/src/components/FeatureGate.tsx` envuelve features pago-gated. Cuando el usuario no tiene plan suficiente, muestra `UpsellModal` (overlay) con CTA a `/billing`.

Aplicar a:
- Analytics tab (free → upsell)
- BYOK section en `/configuracion` → texto "Solo Empresarial — contacta a ventas"
- "Exportar PDF" buttons → upsell si free

---

## 7. Page templates — anatomía del workspace

### 7.1 `/analizar` — La pantalla principal del producto

**Importancia**: 80% del tiempo del cliente. Toda decisión de UX se justifica primero aquí.

#### Estado A: Empty (no caso activo)

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚖ Analizar caso                                  [Nuevo caso]      │  ← Page header
│ Asistente legal multi-agente. Describe tu situación...              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ [Fase: idle ✨] [⚖ —] [🤖 gpt-5.5] [⚡ MEDIUM]                       │  ← CaseStatusBar
│                                                                     │
│ [CONTEXTO  ░░░░░░░░░  3K/128K] (verde)                              │  ← ContextBar
│                                                                     │
│ ┌─────────────────────────────────────────────┬─────────────────┐  │
│ │                                             │ HOW IT WORKS    │  │
│ │ Bienvenido — describe tu situación con el  │                 │  │
│ │ detalle que recuerdes.                      │ 1. Intake       │  │
│ │ Voy a identificar la rama del derecho que   │ 2. Investigación│  │
│ │ aplica, hacerte preguntas puntuales...      │ 3. Análisis     │  │
│ │                                             │    multi-agente │  │
│ │ ESCENARIOS DE EJEMPLO                       │                 │  │
│ │ ┌─────────────────┐ ┌─────────────────┐    │                 │  │
│ │ │ ⚖ Despido      │ │ ⚖ Acoso laboral │    │                 │  │
│ │ │ injustificado   │ │                 │    │                 │  │
│ │ └─────────────────┘ └─────────────────┘    │                 │  │
│ │ ┌─────────────────┐ ┌─────────────────┐    │                 │  │
│ │ │ ⚖ Conflicto    │ │ ⚖ Multa SUNAT   │    │                 │  │
│ │ │ vecinal         │ │                 │    │                 │  │
│ │ └─────────────────┘ └─────────────────┘    │                 │  │
│ │                                             │                 │  │
│ │ ┌──────────────────────────────────────┐   │                 │  │
│ │ │ 📎 Describe tu situación...      [▶] │   │                 │  │
│ │ └──────────────────────────────────────┘   │                 │  │
│ │ El agente irá pidiendo datos...             │                 │  │
│ └─────────────────────────────────────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Mejoras UX propuestas v3 sobre el estado actual**:

1. **Reemplazar emojis de escenarios por iconos Lucide** con color por área:
   - 💼 Despido → `<Briefcase>` con `text-area-laboral`
   - ⚖ Acoso → `<AlertCircle>` con `text-area-laboral`
   - 🏠 Vecino → `<Home>` con `text-area-civil`
   - 💰 SUNAT → `<DollarSign>` con `text-area-tributario`

2. **Hover de escenario** muestra preview del análisis estimado:
   ```
   ┌─────────────────────────────────┐
   │ ⚖ Despido injustificado        │
   │ 3 años con contrato firmado... │
   │                                 │
   │ ↓ Análisis ~ 2 min · gpt-5.5   │  ← preview en hover
   └─────────────────────────────────┘
   ```

3. **Composer focus al cargar la pantalla** — auto-focus en el textarea con `useRef` + `useEffect`

4. **Tip flotante al pasar 30 s sin acción**: "Sin saber por dónde empezar? Click en un escenario de ejemplo"

#### Estado B: Investigating (caso activo, agente preguntando)

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚖ Analizar caso                                                    │
├─────────────────────────────────────────────────────────────────────┤
│ [Fase: investigación · 4/8 datos] [⚖ Laboral] [🤖 gpt-5.5] [⚡ MED]│
│ [Skip → Pasar al análisis]                       [CONTEXTO 28K/128]│
│                                                                     │
│ ┌─────────────────────────────────────────────┬─────────────────┐  │
│ │                                             │ HECHOS (4)      │  │
│ │ [usuario]                                   │   ANTIGÜEDAD    │  │
│ │ Trabajaba 5 años y me despidieron sin...   │   5 años        │  │
│ │                                             │                 │  │
│ │ [agente] laboral_intake                    │   SUELDO        │  │
│ │ Antes de avanzar necesito 3 datos:         │   S/3200        │  │
│ │ 1. ¿Tipo de contrato?                       │                 │  │
│ │ 2. ¿Recibiste carta de despido?             │   ...           │  │
│ │ 3. ¿Estuviste en sindicato?                 │                 │  │
│ │                                             │ PREGUNTAS (3)   │  │
│ │ [usuario]                                   │   ○ ¿Carta?     │  │
│ │ Contrato indeterminado, sin carta...        │   ○ ¿Sindicato? │  │
│ │                                             │   ○ ¿Proceso?   │  │
│ │ [agente]                                    │                 │  │
│ │ 🧠 ORQUESTADOR · investigation              │                 │  │
│ │   ✓ intake_classify                         │                 │  │
│ │   ✓ investigation_extract                   │                 │  │
│ │   ◌ phase_start analysis           ← active │                 │  │
│ │                                             │                 │  │
│ │ ┌──────────────────────────────────────┐   │                 │  │
│ │ │ 📎 Responde la pregunta...        [▶] │   │                 │  │
│ │ └──────────────────────────────────────┘   │                 │  │
│ └─────────────────────────────────────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

#### Estado C: Complete (análisis listo)

Banner gold soft "✨ Caso ya analizado. Si llegaron papeles nuevos o querés sumar contexto..." + mensaje del agente con markdown rico + composer aún visible para continuar.

**Mejora UX propuesta**:
- Después del mensaje final del análisis, mostrar `MessageActions` row:
  - `[🔖 Guardar este análisis]` → /marcadores
  - `[↗ Compartir]` → genera link público (`/compartido/X`)
  - `[📤 Exportar PDF]` → si plan Pro+
  - `[🔄 Continuar caso]` → focus composer
  - `[+ Nuevo caso]` → reset

### 7.2 `/historial` — Workspace de gestión de casos

Anatomía (ya implementada):
```
┌─────────────────────────────────────────────────────────────────────┐
│ 🕒 Historial                                          [utility]     │  ← InternalPageHeader
│ Revisá conversaciones, carpetas y estados sin romper la jerarquía. │
├──────────────┬──────────────────────────────────────────────────────┤
│ CARPETAS     │  [🔍 Buscar conversaciones...]      [▼ Más recientes]│
│  📂 Todas    │                                                       │
│  📂 Laboral 12│  Filtrando por: [⚖ Laboral ×]                       │
│  📂 Tributario│                                                       │
│  📂 Cliente X │  ┌─ tabs ─────────────────────────────────────────┐  │
│  + Nueva     │  │ Activas (87) · Fijadas (3) · Archivadas (12)   │  │
│              │  └────────────────────────────────────────────────┘  │
│ ETIQUETAS    │                                                       │
│  ● Urgente   │  [☐ Seleccionar todas]  3 seleccionadas              │
│  ● Vista 1ra │  [📦 Archivar] [🗑 Eliminar]                          │
│  ● Hito      │                                                       │
│  + Nueva tag │  ┌──────────────────────────────────────────────────┐ │
│              │  │ [☐] 📌 [📂 Laboral] Despido injustificado       │ │
│              │  │     Hace 2h · 14 mensajes · ⚖ Laboral           │ │
│              │  │     ● Urgente  ● Vista 1ra                  ⋮  │ │
│              │  └──────────────────────────────────────────────────┘ │
│              │  ┌──────────────────────────────────────────────────┐ │
│              │  │ [☐] [📂 Laboral] Acoso vecinal                  │ │
│              │  │     Ayer · 8 mensajes · ⚖ Civil                 │ │
│              │  └──────────────────────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────────────────┘
```

**Mejoras UX propuestas**:

1. **Atajo `n` para nuevo caso desde cualquier item** del historial.
2. **Atajo `j/k` para navegar arriba/abajo** entre items (estilo Linear).
3. **Atajo `e` para archivar** item con foco.
4. **Drag carpeta sobre carpeta** para anidar (futuro).
5. **Skeleton screens** durante el load inicial (hoy es spinner centrado).
6. **Quick filters** chips arriba del search: "Sin leer", "Esta semana", "Compartidas" (configurables).
7. **Sort por relevancia** cuando hay search activa (full-text-search) — hoy solo es client-side filter.
8. **Bulk move to folder** — agregar al bulk action bar.

### 7.3 `/buscar` — Corpus público (modo auth)

Ya documentada en `DESIGN_PUBLIC.md`. En modo auth aparece dentro de `AppLayout` con `InternalPageHeader`:

```tsx
<InternalPageHeader
  icon={<Search className="w-5 h-5 text-primary" />}
  eyebrow="Conocimiento"
  title="Buscar en el corpus"
  description="Explorá los 2001 fragmentos del corpus público — sin IA, sin gating."
/>
```

Resto del componente (search bar + chips + result cards) idéntico a la versión pública.

### 7.4 `/marcadores` — Mensajes favoritos

Anatomía (ya implementada con header custom — **migrar a InternalPageHeader**):

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🔖 Marcadores                                       [🔍 filtrar]    │
│ Tus respuestas más útiles, agrupadas por área del derecho.         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ⚖ LABORAL (3)                                                       │
│ ┌──────────────────────────────────────────────────────────────┐   │
│ │ Bot · "Caso despido injustificado 2026-06-23"                │   │
│ │ Markdown content preview...                                  │   │
│ │ [⚖ Laboral] · 2 jun 2026 14:30          [🔖 fill]            │   │
│ │ ─────────────────────────────────────────                    │   │
│ │ Ver conversación completa →                                   │   │
│ └──────────────────────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────────────────────┐   │
│ │ ... otro marcador laboral ...                                │   │
│ └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│ ⚖ CIVIL (5)                                                         │
│ ┌──────────────────────────────────────────────────────────────┐   │
│ │ ... marcadores civil ...                                     │   │
│ └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│ [Anterior]  1 de 3  [Siguiente]                                    │
└─────────────────────────────────────────────────────────────────────┘
```

**Mejoras UX propuestas**:
1. **Skeleton screens** durante load.
2. **Empty state** debe usar `EmptyState` canonical con mascot opacity 20.
3. **Bulk select** para borrar/exportar varios marcadores.
4. **Search más potente** — incluir contenido + título + agent name.
5. **Filter por área chips** arriba (igual que `/buscar`).
6. **Export selected as PDF** para plan Pro+.
7. **Drag a folder** desde marcador (futuro — conexión con folders de historial).

### 7.5 `/notificaciones` — Bandeja

Anatomía (ya implementada — **migrar a InternalPageHeader**):

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🔔 Notificaciones                       [✓✓ Marcar todas leídas]   │
│ Eventos, invitaciones y avisos de uso.                              │
├─────────────────────────────────────────────────────────────────────┤
│ [Sin leer]  [Uso] [Invitaciones] [Sistema] [Facturación] [Bienv.]   │  ← chips
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ⚠ Uso del plan al 80%                              hace 2h  •      │
│ Estás cerca del límite mensual...                                  │
│   [Marcar leída]  [🗑 Eliminar]                                    │
├─────────────────────────────────────────────────────────────────────┤
│ ➕ Invitación de Carlos para "Estudio Pérez"        ayer    ○      │
│ Aceptar o rechazar la invitación...                                │
│   [Ver]  [🗑 Eliminar]                                              │
├─────────────────────────────────────────────────────────────────────┤
│ [Anterior]  Página 1 de 4  [Siguiente]                             │
└─────────────────────────────────────────────────────────────────────┘
```

**Mejoras UX propuestas**:
1. **Reemplazar el toast custom** por sonner unificado (eliminar `toastTimerRef`).
2. **Eliminar con undo**: al borrar mostrar toast "Eliminada · [Deshacer]" durante 5 s.
3. **Click en notificación**: marca leída + navega a action_url (hoy parcialmente implementado en el `<a>` interno).
4. **Pin notificación importante** — útil para invitaciones aún sin responder.
5. **Empty state filter** con CTA "Limpiar filtros" (ya implementado ✅).
6. **Polling cada 30 s** ya implementado ✅ — agregar indicador sutil de "actualizando" cuando se ejecuta.

### 7.6 `/analytics` — Métricas

3 tabs ya implementados:
- **Resumen** — 4 StatCards + BarChart trend + DonutChart áreas + tabla áreas + tabla modelos + tabla queries recientes
- **Costos** — 3 StatCards + tabla desglose por modelo
- **Frecuentes** — top queries del periodo

**Mejoras UX propuestas**:
1. **Selector de fechas custom** además de "7d / 30d / 90d".
2. **Export CSV** ya implementado ✅.
3. **Tooltip on hover en bars del BarChart** — ya parcialmente implementado.
4. **Comparativa entre periodos**: "vs 30d anteriores" en stat cards (parcialmente con `change_pct` por área).
5. **Drill-down**: click en barra del BarChart → modal con desglose por día.
6. **Tab navigation con URL hash** para deep-linking: `/analytics#costos`.
7. **Saved views** (futuro): "Reporte mensual cliente Pérez" guarda configuración.

### 7.7 `/organizacion` — Equipo

Anatomía (ya implementada):

```
┌─────────────────────────────────────────────────────────────────────┐
│ 👥 Organización                                     [utility]       │
│ Gestioná miembros, roles, plan y uso compartido.                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌──────────────────────────────────────────────────────────────┐   │
│ │ 🏢 Estudio Pérez SAC                              [PRO]      │   │
│ │ /estudio-perez                                                │   │
│ └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│ ┌─ Miembros (5) ────────────────────────┬─ Uso del Plan ────────┐  │
│ │                                       │                       │  │
│ │ ┌─────────────────────────────────┐ │ Consultas este mes:    │  │
│ │ │ Carlos Pérez       [OWNER 👑]   │ │ ▓▓▓▓░░░░ 320/Ilim.    │  │
│ │ │ carlos@perez.pe                 │ │                       │  │
│ │ │ desde 1 jun 2026                │ │ Plan actual: PRO       │  │
│ │ ├─────────────────────────────────┤ │                       │  │
│ │ │ María Sánchez      [ADMIN]      │ │ Ver planes →          │  │
│ │ │ maria@perez.pe              [🗑]│ │                       │  │
│ │ └─────────────────────────────────┘ │                       │  │
│ │                                       │                       │  │
│ │ INVITAR MIEMBRO                       │                       │  │
│ │ [✉ correo@ejemplo.com]                │                       │  │
│ │ [Rol ▼] [+ Invitar]                   │                       │  │
│ └───────────────────────────────────────┴───────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Mejoras UX propuestas**:
1. **Pending invitations section** — mostrar invitaciones enviadas aún no aceptadas.
2. **Resend invitation** button al lado de email.
3. **Bulk invite** — paste de varios emails comma-separated.
4. **Change role** dropdown inline en cada member (hoy solo eliminar).
5. **Audit log** — quién hizo qué cuándo (futuro).
6. **Transfer ownership** flow (acción muy crítica — requiere `ConfirmDialog` con typing del email del nuevo owner).

### 7.8 `/configuracion` — Settings

6 tabs ya implementados:
- **Perfil** — info + cambio contraseña + sesiones + logout-all
- **Organización** — datos org + danger zone (delete org)
- **Preferencias** — modelo default + área default
- **Memoria** — categorías de memoria + delete all
- **API Keys** — list providers + add/test/delete keys
- **Archivos** — uploaded docs management

Layout: sidebar vertical desktop (260 px), horizontal scroll mobile.

**Mejoras UX propuestas**:
1. **URL hash por tab** — `/configuracion#memoria` para deep-link.
2. **Búsqueda dentro de configuración** — `Cmd+K` para buscar setting (ej. "model").
3. **Unsaved changes warning** al navegar saliendo del tab.
4. **API Key test inline** con feedback visual immediate (loading → success/error).
5. **BYOK badge** "Solo plan Empresarial" debería ser un `Card/Accent` informativo, no un disabled state.
6. **Memory categories** con iconos por categoría (profesión, intereses, casos, preferencias, contexto).
7. **Archivos** con preview thumbnail si es PDF/imagen + tags.
8. **Eliminar TODAS las sesiones** debe ser `ConfirmDialog` con typing.
9. **Eliminar cuenta** flow (no existe — agregarlo): tab "Eliminar cuenta" rojo dentro del danger.

### 7.9 `/billing` — Suscripción

Anatomía actual (ya implementada — **migrar el header a InternalPageHeader**):

Bloques:
- Beta banner (solo si payments_enabled=false)
- Plan actual card
- BYOK info banner
- Trial retry banner (si applicable)
- 3 plan comparison cards (Gratuito, Profesional featured, Estudio)
- Métodos de pago aceptados
- Invoice history
- Danger zone (cancel subscription)

**Mejoras UX propuestas**:
1. **Plan switching flow** — modal con preview de qué cambia (features +/-) antes de confirmar.
2. **Downgrade warning** — "Perderás acceso a Analytics, Carpetas, ..."
3. **Pause subscription** (futuro) — útil para vacaciones del estudio.
4. **Add team seats** (Estudio plan) — UI directa sin tener que contactar.
5. **Receipt/Invoice download** desde invoice history.
6. **Apply promo code** input visible.

### 7.10 `/onboarding` — Wizard 5 pasos

Ya implementado con stepper + transitions + components separados en `_components/`.

Steps:
1. **Bienvenida** — mascota grande + "Empezar el setup" CTA
2. **Perfil** — nombre + foto (futuro)
3. **Organización** — opcional crear org
4. **API Key** — opcional configurar BYOK (Pro+ idealmente)
5. **Listo** — resumen + "Ir al producto"

**Mejoras UX propuestas**:
1. **Skip granular** — saltar paso específico sin saltar todo.
2. **Progress save** ya implementado en localStorage ✅.
3. **Back button** ya implementado ✅.
4. **Time estimate** — "Setup completo en 3 min" en step 1.
5. **Confetti animation** en step 5 (sobrio, no exagerado — usar tu palette).
6. **Tour interactivo opcional** después de Step 5 — tooltips guiados en `/analizar`.

### 7.11 `/documento/[id]` — Document viewer

Estado actual: poco código visible. Spec recomendada:

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📄 Documento                              [⬇ Descargar] [🔖 Guardar]│
│ Código Civil — Decreto Legislativo 295                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─────────────────┬──────────────────────────────────────────────┐ │
│ │ TOC             │ ARTÍCULO 924                                  │ │
│ │ ▾ Libro V       │ Las limitaciones del derecho de propiedad...  │ │
│ │   Art. 921      │                                               │ │
│ │   Art. 922      │ [highlight] humos, hollín, emanaciones,       │ │
│ │ ▸ Art. 924      │ [highlight] ruidos, vibraciones,              │ │
│ │   Art. 925      │ [highlight] olores y otros similares...       │ │
│ │   ...           │                                               │ │
│ └─────────────────┴──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

Features:
- TOC navegable con highlight de sección activa
- Body en Newsreader 16 px para lectura larga
- Highlight de keyword si vienes de `/buscar?q=ruido`
- Citar fragment → genera link a este punto exacto
- "Usar en /analizar" → crea nuevo caso con este artículo en contexto

### 7.12 `/compartido/[id]` — Vista de conversación compartida (público)

Spec:
- PublicLayout reducido (logo + "Iniciar sesión" + ningún nav)
- Banner top: "Esta conversación fue compartida desde TukiJuris"
- Mensajes en read-only mode (sin composer, sin actions)
- CTA al final: "Quieres probarlo? Empieza gratis →"
- Si user logged in: opción "Importar a mis casos"

---

## 8. Flujos de usuario críticos (UX path)

### 8.1 Onboarding del nuevo cliente

```
[/auth/register] → success → 
[/onboarding step 1: Bienvenida] → 
[/onboarding step 2: Perfil] → 
[/onboarding step 3: Organización opcional] → 
[/onboarding step 4: API Key opcional] → 
[/onboarding step 5: Listo] → "Ir al producto" →
[/analizar] empty state con tooltip "Empieza describiendo tu caso"
```

**Tiempo target**: 3 minutos desde registro hasta primera consulta.

### 8.2 Primer caso completo

```
[/analizar empty] →
  Click "Despido injustificado" escenario o tipea →
[Estado B: investigating] → 
  Agente pregunta, usuario responde 2-3 turnos →
[Estado C: complete] →
  Agente entrega análisis con citas →
  Toolbar aparece: [🔖 Guardar] [↗ Compartir] [📤 PDF] [🔄 Continuar] →
  Click "Guardar" → toast "Análisis guardado en marcadores" →
[Sidebar → Marcadores] →
  Análisis ahí, agrupado por área Laboral
```

**Mejora UX propuesta**: Al terminar el primer caso, mostrar tooltip "Nice! Tu análisis está guardado. Puedes verlo en Marcadores cuando quieras."

### 8.3 Continuar caso días después

```
[/historial] →
  Filter por carpeta "Cliente Pérez" →
  Buscar "despido" →
  Click en conversación →
[/analizar?conversation=X] →
  Carga case_state desde DB →
  Restaura mensajes + facts + pending →
  Si phase=complete: banner gold "Caso ya analizado. Si llegaron papeles..." +
  Composer pre-focused →
  Usuario escribe "Llegó la carta de respuesta del MTPE..." →
  Orquestador corre con todo el case_state + nuevo contexto →
  Nuevo análisis incrementa
```

### 8.4 Compartir un análisis con cliente

```
[/analizar] en complete →
  Click "↗ Compartir" en assistant message →
  Modal: "Esta conversación será visible para cualquiera con el link" →
  Toggle: "Incluir hechos del caso? [✓]" →
  CTA "Generar link" →
  Toast "Link copiado al portapapeles" + link: tukijuris.com.pe/compartido/abc123 →
[/compartido/abc123] cliente lo abre →
  Ve la conversación en read-only →
  CTA invisible: "Quieres probarlo gratis?"
```

### 8.5 Invitar a un colega al estudio

```
[/organizacion] →
  Tipea email en "Invitar miembro" →
  Selecciona rol "Administrador" →
  Click "+ Invitar" →
  Toast "Invitación enviada a maria@perez.pe" →
[Maria recibe email] →
  Click "Aceptar invitación" →
[/auth/register?invite=token] →
  Form pre-filled con email →
  Crea cuenta →
[/onboarding step 3] →
  "Carlos te invitó a Estudio Pérez · Aceptar / Crear mi propia" →
  Aceptar →
[/analizar] como miembro del estudio
```

### 8.6 Cambio de plan Free → Pro

```
[/analytics] sin acceso (gated) →
  Click en tab "Analytics" → 
[UpsellModal] muestra "Analytics está en plan Profesional" + CTA "Mejorar" →
[/billing] →
  Click "Actualizar a Profesional" en plan card →
[Culqi checkout external] →
  Pago exitoso →
[/billing?success=1] →
  Toast verde "Bienvenido a Profesional!" →
  Plan actual badge: Pro →
[Sidebar] Analytics ahora accesible sin lock icon
```

### 8.7 BYOK setup (plan Empresarial only)

```
[/configuracion#apikeys] →
  Lista de providers con estado →
  "Plataforma activa" (Gemini, Groq, DeepSeek) →
  Cards adicionales con "+ Agregar tu propia key" en OpenAI, Anthropic, xAI →
  Click "+ Agregar tu propia key" en Anthropic →
  Inline form: API key + label opcional →
  "Probar conexión" → loading 2s → "✓ OK · 845ms latency" →
  "Guardar" → toast "Clave guardada"
[Sidebar /configuracion] → 
  Provider muestra "Tu key configurada" + opciones eliminar/probar
```

**Nota**: Plan Free/Pro/Studio NO ven cards "+ Agregar" — solo el `UpsellModal` "BYOK es exclusivo del plan Empresarial · Contactar ventas".

### 8.8 Eliminar cuenta (no implementado actualmente — agregar)

```
[/configuracion#perfil] → scroll bottom →
[Danger Zone] card con "Eliminar cuenta permanente" botón rojo ghost →
  Click → 
[ConfirmDialog requireTyping="ELIMINAR MI CUENTA"] →
  Lista qué se elimina: 
    - X conversaciones
    - X marcadores
    - X archivos
    - Tu org si eres único owner
  Tipea exactamente "ELIMINAR MI CUENTA" →
  Click "Eliminar permanentemente" →
  POST /api/auth/delete-account →
  Logout + redirect /landing con toast "Tu cuenta y datos fueron eliminados"
```

---

## 9. Microinteracciones del workspace

### 9.1 Catálogo de animaciones específicas del workspace

| Pattern | Duration | Easing | Uso |
|---|---|---|---|
| Sidebar collapse/expand | 200 ms | ease-in-out | width animation |
| Tab change | 200 ms | ease | opacity + transform Y |
| Card hover lift | 200 ms | ease | translateY(-1px) + shadow |
| Loading spinner (Loader2) | 1 s | linear loop | rotate 360deg |
| Skeleton shimmer | 1.5 s | ease-in-out loop | bg-position gradient |
| Toast enter | 240 ms | cubic-bezier(0.22, 1, 0.36, 1) | translateY + opacity |
| Modal enter | 200 ms | ease-out | scale(0.96 → 1) + opacity |
| Drawer mobile slide | 250 ms | ease | translateX(-100% → 0) |
| Pin toggle | 150 ms | ease | scale(0.9 → 1) + fill |
| Bookmark toggle | 150 ms | ease | same + ripple primary/20 |
| Page transition | 250 ms | ease | opacity (Next.js Suspense) |

### 9.2 Patrones específicos del workspace

**Optimistic UI** (ya parcialmente implementado):
- Mark notification as read → instantáneo en UI, request en background
- Delete notification → instantáneo + snapshot rollback si falla (ya implementado ✅)
- Toggle bookmark → instantáneo
- Pin/Archive conversation → instantáneo
- Move to folder → instantáneo

**Loading states tiered**:
- < 200 ms: no loading state (instant)
- 200ms - 1s: spinner inline
- 1s - 3s: skeleton screens
- > 3s: skeleton + helper text "Cargando..."

**Empty states con CTA**:
- Sin marcadores → "Ve a /analizar y guarda tu primer marcador"
- Sin historial → "Empieza un nuevo caso"
- Sin notificaciones → "Te avisaremos cuando haya algo nuevo"
- Sin org → "Crea tu organización (opcional)"
- Sin miembros → "Invita a tu primer colaborador"

**Real-time feedback**:
- ContextBar updates como agente extrae facts (debounce 500 ms)
- ReasoningPanel adds row con `animate-fade-in-up` 240 ms
- CaseFactsCard adds item con stagger 80 ms

### 9.3 Atajos de teclado canónicos

| Shortcut | Acción | Donde |
|---|---|---|
| `⌘K` / `Ctrl+K` | Open command palette / search global | Todo el workspace |
| `⌘N` / `Ctrl+N` | Nuevo caso (link a `/analizar`) | Todo |
| `⌘/` / `Ctrl+/` | Toggle help popover | Todo |
| `Esc` | Cerrar modal / drawer / dropdown | Cuando aplicable |
| `Cmd+Enter` | Enviar mensaje (composer) | /analizar |
| `n` | Nuevo caso (sin modifier) | /historial cuando lista enfocada |
| `j` / `k` | Down/up entre items | /historial, /marcadores, /notificaciones |
| `e` | Archivar item con foco | /historial |
| `p` | Pin item con foco | /historial |
| `?` | Mostrar atajos disponibles | Todo |

Componente `KeyboardShortcuts.tsx` ya existe parcialmente. Documentar la lista completa y exponer via help popover.

### 9.4 Reduced motion

Respetar `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

Excepciones que SÍ deben respetar reduced motion incluso si gustan visualmente:
- ReasoningPanel ping halo
- Sidebar collapse (importante mostrar el cambio de estado)

---

## 10. Accessibility (workspace)

### 10.1 Keyboard navigation completa

Cada feature del workspace debe ser usable con teclado:
- Tab cycle por todos los elementos interactivos
- Enter activa botones/links
- Space toggle checkboxes/toggles
- Arrow keys navega listas/menús
- Esc cierra overlays

### 10.2 Screen readers

- `aria-label` en buttons icon-only
- `aria-live="polite"` en ReasoningPanel para anunciar pasos
- `aria-live="assertive"` solo en errores críticos
- `role="status"` en loading shells
- `role="alert"` en error banners
- `aria-current="page"` en sidebar item activo
- `aria-expanded` en disclosure cards y dropdowns
- `aria-selected` en tabs

### 10.3 Focus management

- Cuando se abre modal: focus primer input or close button
- Cuando se cierra modal: focus back al trigger
- Cuando se cambia de page: focus al H1 (Next.js no lo hace por default — implementar)
- Cuando se abre drawer mobile: focus primer item de navegación

### 10.4 Contraste verificado (workspace tokens)

Combinación | Ratio | Verdict
---|---|---
`--on-surface` sobre `--surface-container-low` | 13.0:1 | ✅ AAA
`--on-surface-variant` sobre `--surface-container` | 4.8:1 | ✅ AA
`--primary` sobre `--surface-dim` | 6.5:1 | ✅ AA
`--primary` sobre `--surface` | 6.2:1 | ✅ AA
`--status-success-on` sobre `--status-success-soft` | 7.1:1 | ✅ AA
`--status-danger-on` sobre `--status-danger-soft` | 5.8:1 | ✅ AA
`text-on-surface/40` (placeholders) | ~2.0:1 | ❌ Solo decorativo, no info crítica
`text-on-surface/30` (hints) | ~1.7:1 | ❌ Solo decorativo

### 10.5 Forms accesibles

- Labels conectados via `htmlFor` ✅ (mayoría ya implementado)
- Error messages con `aria-describedby`
- Required indicators visibles (asterisco rojo + `aria-required="true"`)
- Fieldset/legend para grupos de campos relacionados
- Autocomplete attributes (email, current-password, new-password, name) ✅

### 10.6 Tap targets en mobile (workspace)

- Sidebar items: 36 px ⚠️ aumentar a 44 px en mobile breakpoint
- Action buttons inline: 14 px icon — pad to 32 px clickable area
- Bookmark/Pin toggles: pad a 32 px
- Bulk select checkbox: pad a 32 px

---

## 11. Performance (workspace)

### 11.1 Performance budgets específicos

| Page | LCP | INP | CLS |
|---|---|---|---|
| `/analizar` | < 1.5 s | < 200 ms | < 0.1 |
| `/historial` | < 2.0 s | < 200 ms | < 0.1 |
| `/marcadores` | < 1.5 s | < 200 ms | < 0.1 |
| `/notificaciones` | < 1.0 s | < 100 ms | < 0.05 |
| `/analytics` | < 2.5 s | < 300 ms | < 0.1 |
| `/configuracion` | < 1.5 s | < 200 ms | < 0.1 |

### 11.2 Optimizaciones canónicas

- **Code splitting** por route — Next.js App Router ya lo hace ✅
- **Suspense boundaries** alrededor de slow components
- **Server components** donde possible — la mayoría del workspace usa `"use client"`. Migrar a server por defecto, client solo cuando hay state.
- **Streaming SSR** para `/historial` con 100+ conversaciones — load primeros 20 server, rest client
- **Image optimization** — `next/image` para mascot, screenshots, avatars
- **Virtual lists** para `/historial` cuando > 100 conversations (futuro)
- **Debounce search** ya implementado ✅
- **Polling intervals** sensatos: notifications 30 s ✅, no polling en otras
- **Cache TTL** en SWR / React Query si se migra (futuro)

### 11.3 Real-time perf (SSE streaming)

- Keep-alive heartbeat cada 10 s ✅
- Bypass Next.js dev proxy ✅
- TextDecoder + buffer parsing ✅
- Cleanup task cancellation en unmount ✅

### 11.4 Bundle size targets

- Initial JS (sidebar + topbar + auth): < 150 kb gzip
- Per-route JS chunks: < 80 kb gzip
- CSS total: < 30 kb gzip

---

## 12. Production checklist + Migration debt

### 12.1 Migración prioritaria (zona cliente) — Estimado total: ~ 4 días

#### 🔴 P0 — Critical (bloquean rollout v3)

1. **Migrar TODAS las pages a `InternalPageHeader`** (~ 4 horas)
   - [ ] `/analizar` reemplaza `<div className="border-b ... bg-[#0e0e12]">` por `<InternalPageHeader>`
   - [ ] `/buscar` mismo cambio
   - [ ] `/marcadores` mismo cambio
   - [ ] `/billing` mismo cambio
   - [ ] `/notificaciones` mismo cambio

2. **Eliminar todos los hex hardcoded** (~ 8 horas) — usar el mapeo §3.2/§3.3
   - [ ] Find/replace `#0e0e12`, `#0e0e14` → `bg-surface-dim`
   - [ ] `rgba(79,70,51,0.15)` → `border-outline-variant`
   - [ ] Status colors `#1a3a2a`, `#6ee7b7`, `#ffb4ab`, `#93000a` → tokens semánticos
   - [ ] Gray scale `#7c7885`, `#a09ba8`, `#55535d` → `on-surface-*`
   - [ ] Memory category colors `#4f3700`, `#2d1f4a`, `#c4b5fd` → status tokens

3. **Reemplazar `confirm()` nativos con `<ConfirmDialog>`** (~ 6 horas)
   - [ ] Crear `apps/web/src/components/ui/ConfirmDialog.tsx` (no existe aún)
   - [ ] Reemplazar 13+ calls a `confirm()` en `/marcadores`, `/historial`, `/configuracion`, `/organizacion`

4. **Toast unificado a sonner** (~ 1 hora)
   - [ ] Eliminar el toast custom de `/notificaciones` (`toastTimerRef` setup)
   - [ ] Usar sonner consistentemente en todo el workspace

#### 🟡 P1 — Importantes (mejoran UX significativamente)

5. **Componentes a extraer** (~ 8 horas)
   - [ ] `Composer.tsx` (de `/analizar`)
   - [ ] `MessageBubble.tsx` (de `/analizar`)
   - [ ] `SidePanel.tsx` con sub-cards (de `/analizar`)
   - [ ] `StatCard.tsx` (de `/analytics`)
   - [ ] `TrendIndicator.tsx` (de `/analytics`)
   - [ ] `LatencyBadge.tsx` (de `/analytics`)
   - [ ] `AreaBadge.tsx` (centralizar — hoy 4 implementaciones)
   - [ ] `BarChart.tsx`, `DonutChart.tsx` (de `/analytics`)
   - [ ] `DisclosureCard.tsx` (de `/configuracion`)
   - [ ] `SectionCard.tsx`, `SectionHeader.tsx` (de `/configuracion`)
   - [ ] `Skeleton.tsx` (de `/analytics`)
   - [ ] `EmptyState.tsx` (consolidar 4 variantes)
   - [ ] `UsageBadge.tsx` (nuevo — para sidebar footer)

6. **`KeyboardShortcuts` completo** (~ 3 horas)
   - [ ] Implementar `Cmd+K` command palette
   - [ ] Atajos `j/k` para navegación en `/historial`, `/marcadores`
   - [ ] Help popover con lista completa de shortcuts

7. **URL hash para tabs** (~ 2 horas)
   - [ ] `/configuracion#perfil`, `#organizacion`, etc.
   - [ ] `/analytics#overview`, `#costos`, `#frecuentes`
   - [ ] `/billing` mantener estado de UI

8. **Skeleton screens en lugar de spinners** (~ 4 horas)
   - [ ] `/historial` lista de conversaciones
   - [ ] `/marcadores` cards
   - [ ] `/notificaciones` filas
   - [ ] `/configuracion` cuando tab cambia

9. **Reasoning Panel mejoras** (~ 4 horas)
   - [ ] Duración por paso (mostrar tiempo > 3s)
   - [ ] Active row con `bg-primary-soft`
   - [ ] Tooltip detalle on hover en steps done
   - [ ] Animation `fade-in-up` por fila nueva

10. **Message actions row después del análisis final** (~ 3 horas)
    - [ ] `[🔖 Guardar]` botón
    - [ ] `[↗ Compartir]` flow
    - [ ] `[📤 Exportar PDF]` (Pro+ con FeatureGate)
    - [ ] `[🔄 Continuar]` focus composer
    - [ ] `[+ Nuevo caso]` reset

#### 🟢 P2 — Nice-to-have

11. **Tour interactivo opcional** después de onboarding (~ 6 horas)
12. **Drag-reorder de facts** en SidePanel (~ 4 horas)
13. **Edit fact inline** click-to-edit (~ 3 horas)
14. **Bulk move to folder** en `/historial` (~ 2 horas)
15. **Quick filters chips** configurables en `/historial` (~ 3 horas)
16. **Saved analytics views** (~ 4 horas)
17. **Eliminar cuenta** flow completo (~ 3 horas)
18. **Audit log** en `/organizacion` (~ 6 horas)
19. **Pending invitations** UI en `/organizacion` (~ 2 horas)
20. **Receipt download** en `/billing` invoice history (~ 2 horas)

### 12.2 Testing checklist (zona cliente)

- [ ] Lighthouse desktop ≥ 90 en `/analizar`, `/historial`, `/configuracion`
- [ ] Lighthouse mobile ≥ 80 en mismas pages
- [ ] axe DevTools sin violaciones en forms críticos (auth, config, billing)
- [ ] Keyboard navigation completa por sidebar + cada page
- [ ] VoiceOver test en `/analizar` flujo completo
- [ ] Mobile real: iPhone SE — sidebar drawer + composer mobile
- [ ] Dark + light paridad por cada page
- [ ] Streaming SSE no se rompe con reload del page
- [ ] Persist `case_state` después de F5 verificado
- [ ] Visual regression con Playwright sobre las 10 pages principales

### 12.3 Analytics events del workspace

| Event | When | Props |
|---|---|---|
| `case_started` | Primera consulta del caso | `area_hint` |
| `case_phase_changed` | Cambio de fase | `from`, `to`, `area` |
| `case_completed` | Análisis terminado | `area`, `model`, `duration_ms`, `agent_count` |
| `case_skip_to_analysis` | Botón Skip clickeado | `facts_count` |
| `case_reopened` | Cargar `?conversation=X` | `conversation_id`, `previous_phase` |
| `message_bookmarked` | Toggle bookmark on | `area`, `message_id` |
| `message_shared` | Generar share link | `area`, `message_id` |
| `bookmark_removed` | Quitar marcador | `area` |
| `historial_filter_applied` | Filter por carpeta/tag | `filter_type`, `filter_value` |
| `folder_created` | Nueva carpeta | `name_length` |
| `tag_created` | Nueva etiqueta | `name_length`, `color` |
| `conversation_archived` | Archive | `area`, `message_count` |
| `conversation_deleted` | Delete | `area`, `message_count` |
| `bulk_action` | Bulk archive/delete | `action`, `count` |
| `notification_marked_read` | Mark read | `type` |
| `org_member_invited` | Send invite | `role` |
| `analytics_export_csv` | Export CSV | `tab`, `days` |
| `analytics_date_range_changed` | Change 7/30/90d | `days` |
| `api_key_added` | BYOK setup | `provider` |
| `api_key_tested` | Test connection | `provider`, `success` |
| `theme_changed` | Toggle dark/light | `to` |
| `sidebar_collapsed` | Collapse/expand | `state` |
| `upsell_modal_shown` | Feature locked | `feature`, `current_plan` |

---

## 13. Appendix

### 13.1 File map (zona cliente)

```
apps/web/src/app/
  analizar/page.tsx                 ← Pantalla principal con SSE
  buscar/page.tsx                   ← Corpus público (auth + anon)
  historial/page.tsx                ← Lista de casos + folders + tags
  marcadores/page.tsx               ← Mensajes guardados
  notificaciones/page.tsx           ← Bandeja
  analytics/page.tsx                ← Métricas (Pro+)
  organizacion/page.tsx             ← Equipo + miembros
  billing/page.tsx                  ← Suscripción
  configuracion/page.tsx            ← Settings 6 tabs
  onboarding/page.tsx               ← Wizard 5 pasos
    layout.tsx
    _constants.ts
    _types.ts
    _components/                    ← Step components
  documento/[id]/page.tsx           ← Document viewer
  compartido/[id]/page.tsx          ← Public share view
  guia/, docs/                      ← Help (también pública)

apps/web/src/components/
  AppLayout.tsx                     ← Shell wrapper auth
  AppSidebar.tsx                    ← Sidebar 5 secciones
  shell/
    WorkspaceShell.tsx              ← Grid layout
    ShellTopbar.tsx                 ← Top 56px
    InternalPageHeader.tsx          ← Page header canonical
    ShellUtilityActions.tsx         ← Theme + help + bell
    ShellMobileDrawer.tsx           ← Drawer mobile
  configuracion/
    DevApiKeysSection.tsx
    SessionsList.tsx
  billing/_components/
    TrialRetryBanner.tsx
    InvoiceHistorySection.tsx
  HelpPopover.tsx
  FeatureGate.tsx                   ← Plan gating
  UpsellModal.tsx                   ← Plan upgrade prompt
  OrgSwitcher.tsx                   ← Multi-org dropdown
  NotificationBell.tsx              ← Bell + dropdown
  UsageBadge.tsx                    ← TODO (no existe)
  ThemeProvider.tsx
  ThemeToggle.tsx
  KeyboardShortcuts.tsx             ← TODO completar

apps/web/src/lib/
  auth/AuthContext.tsx              ← User + authFetch
  api/notifications.ts              ← Client de /api/notifications
  models.ts                         ← MODEL_CATALOG
  markdown.ts                       ← renderMarkdown
  llm/providerLabels.ts             ← PROVIDER_LABELS

apps/web/src/app/chat/
  constants.ts                      ← LEGAL_AREAS, AREA_HEX_COLORS, AREA_LABELS
```

### 13.2 Stitch-ready prompt template (workspace)

Para generar pantallas adicionales coherentes con el workspace del cliente, usar este prompt base:

> Design a **workspace screen** for **TukiJuris**, the Spanish-language (Peruvian Spanish, es-PE) legal AI SaaS for working lawyers. This is the **post-login zone** — the user is a professional Peruvian lawyer using this 4+ hours/day.
>
> **Layout convention**: WorkspaceShell with persistent left sidebar (284px expanded / 80px collapsed), top bar (56px), and main content area centered with `max-w-6xl mx-auto px-6`. Some screens have a 320px right rail (`/analizar` mostly). Each page starts with `InternalPageHeader` (76px) containing: icon (20px primary) + eyebrow (10px uppercase tracking-0.16em primary/80) + title (28-32px Newsreader weight 700) + description (13px on-surface/50) + utility slot right + actions right.
>
> **Visual identity**: editorial dark theme. Background `#191918`, surface `#1F1F1E`, surface-dim `#0E0E14` for sticky headers, outline-variant `#2C2C2B`. Primary gold `#C9A84C`, with `gold-gradient` for primary CTAs. Text `#ECEAE3` primary, `#9B9991` muted, `#6B6962` subtle. Status: success `#8BC98B`, warning `#E8B30E`, danger `#E06B5C`, info `#B3A4F0`.
>
> **Typography**: Newsreader (serif) for page titles, section headers, brand wordmark, big numbers in StatCards, and Markdown H1/H2/H3 inside agent messages. Manrope (sans) for body, labels, buttons, chips. SF Mono / Geist Mono for model IDs, scores, latencies (`tabular-nums`).
>
> **Density**: high. Body base 14px (not 16px). Buttons medium 36px height. Card padding 20-24px. Card border-radius 12px (`rounded-xl`). Gaps between sections 16-24px. Page top section gap 16px.
>
> **Components**: use canonical `StatCard`, `AreaBadge`, `DisclosureCard`, `SectionCard`, `EmptyState`, `Skeleton`, `Toast` (via sonner), `ConfirmDialog`. Lucide icons stroke-width 1.6.
>
> **Tone**: profesional pero cercano. Tuteo informal en CTAs ("Guardar cambios"), usted neutro en mensajes legales formales. Disclaimers de IA orientativa cuando aparezcan resultados.
>
> **Signature components**: `ContextBar` (verde/amarillo/rojo), `ReasoningPanel` (live SSE steps), `CaseStatusBar` (phase + area + model + effort badges), Composer (textarea + paperclip + gold-gradient send), SidePanel with Case Facts + Pending Questions. These ARE the product differentiation — render them prominently.
>
> **Optimistic UI**: instant feedback on toggles (bookmark, pin, archive, mark-read). Backend sync silent. Rollback on error with toast.
>
> **Empty states**: never dead-end. Always include CTA + occasionally `logo-full.png` opacity 20 w-24.
>
> **Mobile**: sidebar becomes drawer (300px, slide-in). Topbar shows hamburger. Tables → cards. Page header description hides < md. Bulk action bar fixed bottom.

Variantes específicas para Stitch:
- "Show the empty state for [page]"
- "Show the loading state with skeleton screens (no spinners)"
- "Show the error state with retry CTA"
- "Show the upsell modal when user clicks Pro-gated feature"
- "Show the mobile drawer expanded"
- "Show the ConfirmDialog with requireTyping for destructive action"

### 13.3 Decisiones pendientes para próxima iteración

- **Command palette (`Cmd+K`)** — Diseñar componente. Va contra el slot `ShellUtilityActions` o como overlay global? Decisión sugerida: overlay global con shortcut.
- **Mobile UX en `/analizar`** — el side panel se oculta < xl. ¿Reemplazar con bottom-sheet con tab? Decisión sugerida: tab "Hechos" abajo del composer en mobile.
- **Compartir conversación públicamente** — privacy concern: ¿advertir al user que la conversación será pública? Sí. Decisión: modal con toggle "Incluir hechos del caso" + warning.
- **Voice input** en composer (futuro) — útil para abogados en movimiento.
- **PWA / offline mode** (futuro) — preserva último análisis offline.
- **Multi-cuenta switcher** (futuro) — abogado con cuentas Free + Estudio.
- **Comments / annotations** en análisis (futuro) — colaboración entre miembros del estudio.

### 13.4 Versioning

| Version | Date | Status | Notes |
|---|---|---|---|
| 1.0 | 2026-06-25 | Production-ready | Documento focalizado en workspace del cliente. Cubre 12 pages internas + 24 componentes canónicos + 8 flujos UX críticos. |

---

**Fin de DESIGN_CLIENT.md** — listo para Stitch / Claude design tools / Figma ingest.

Próximo entregable: **`DESIGN_BACKOFFICE.md`** cubriendo `/admin` (gestión de plataforma, gestión de keys de la plataforma, audit log, gestión de orgs, usuarios, observabilidad).
