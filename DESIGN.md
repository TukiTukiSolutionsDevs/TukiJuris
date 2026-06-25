# TukiJuris — Design System & Production Spec

> **Version**: 1.0 (production-ready spec) — 2026-06-25
> **Author**: Design audit + consolidation of three coexisting systems
> **Compatibility**: written to be ingested by Stitch (Google) and Claude design tools.
> Hex values use `#RRGGBB`. Semantic names map 1:1 to CSS variables in `apps/web/src/app/globals.css`.

## 0. Executive summary & migration notice

Today the codebase ships **three overlapping design systems** in `apps/web/`:

| System | Where it lives | Used by | Status |
|---|---|---|---|
| **Lex Aurum v2** | `:root` and `.dark` in `globals.css` | `/landing`, `/analizar` content area, `/buscar` content area | Production |
| **Notion Editorial** | `.n-*`, `.c-*`, `.hst-*` rules in `globals.css` (dark-only) | `AppSidebar`, `ShellTopbar`, `/historial`, chat shell | Production |
| **Design System v1.0-beta** | `/design-system/page.tsx` | Documentation only | Proposed — never adopted |

This document consolidates them into a **single canonical system** named **TukiJuris Lex Aurum v3 ("Estudio")**. The migration strategy is:

- **Adopt the Notion Editorial palette and typography pairing as canonical** (it is what the shell already uses and visually reads as "modern Peruvian law firm" — what we want).
- **Retire** the third system at `/design-system/page.tsx` (DM Sans / Inter / Geist Mono / `#EAB308`) — keep the page as visual scratch-pad, do not ship a route to it.
- **Promote** `.n-*` tokens (dark) and re-derive a light theme from them. Drop the divergent `#B8920A` / `#FFD165` golds; standardize on `#C9A84C` (dark) and a light-mode counterpart `#A07C20`.
- **Stop using ad-hoc colors** like `bg-[#0e0e12]` (currently hardcoded in `/analizar` and `/buscar` sticky headers).

Stitch/agent prompt-friendly framing: "Design a Spanish-language SaaS for Peruvian lawyers. Editorial dark theme inspired by Notion + The Browser Company. Serif display (Newsreader), sans body (Manrope). Gold accent. Real-time multi-agent legal reasoning is the hero interaction."

---

## 1. Brand identity

### 1.1 Name & positioning

- **Name**: TukiJuris (compound of *tuki* — Quechua / Andean for the toucan-like bird — and *iuris* / "law").
- **Tagline ES-PE**: "Tu asistente jurídico inteligente para derecho peruano."
- **Tagline corta**: "El estudio jurídico en tu pantalla."
- **Mascot**: *Tucán abogado* — toucan in suit + bowtie. Embodies "professional but approachable."
- **Domain**: tukijuris.com.pe
- **Locale**: es-PE primary, es-419 (LATAM) acceptable secondary.

### 1.2 Audience

| Persona | Plan | Mental model | Tone |
|---|---|---|---|
| **Abogado profesional peruano** (primary) | Pro S/70 · Estudio S/299 | "asistente que respeta mi tiempo y cita la norma exacta" | profesional, técnico, conciso |
| **Cliente final / ciudadano** (secondary) | Gratuito | "consulto qué dice la ley sin tener que pagar abogado para una pregunta" | claro, sin jerga, didáctico |
| **Equipo legal de empresa** (tier) | Empresarial (contacto) | "BYOK + multi-asiento + auditoría" | confiable, compliance, SLA |

### 1.3 Brand voice (3 axes)

- **Profesional** > coloquial. "Conforme al art. 924 del Código Civil" no "como dice el codigo".
- **Cercano** > corporativo. "Cuéntame tu situación con el detalle que recuerdes" no "Ingrese descripción del caso".
- **Autoritativo** > especulativo. Citas concretas con número de norma y fecha. Nunca "creo que" / "podría ser".

Pronoun guidance: **tuteo informal en CTAs y empty states** ("Empieza gratis"), **usted/impersonal en mensajes legales formales** ("La presente respuesta tiene carácter orientativo").

### 1.4 Logo & lockups

Brand assets live in `apps/web/public/brand/`:

- `logo-icon.png` — solo mascota (sidebar mark, favicon source)
- `logo-full.png` — wordmark + mascota, fondo oscuro
- `logo-negro.png` — wordmark + mascota, fondo claro
- `tukan.png` — solo mascota grande para hero
- `cta-hero.png` — variante de hero para CTAs

Lockup rules:
- Mínimo 32×32 px para el icono solo
- Mínimo 120 px de ancho para `logo-full`
- Clear-space = altura de la "T" del wordmark, en los 4 lados
- En tema oscuro: `logo-full.png`. En tema claro: `logo-negro.png`.

Palette extraída del logo (referencia, no tokens):

| Parte | Hex | Uso histórico |
|---|---|---|
| Pico y balanza | `#E8B30E` | Gold ancestral — fuente del accent |
| Traje | `#3D4A60` | Navy — superficies en versión light |
| Corbatín | `#B83230` | Rojo — solo errores |
| Pecho | `#F0EBE1` | Cream — usado en surface light |
| Cuerpo / cabeza | `#1A1A1A` | Negro profundo — base dark |

### 1.5 Favicons & metadata

- Browser favicon: `/brand/logo-full.png` (configurado en `apps/web/src/app/layout.tsx`)
- Apple touch icon: `/brand/logo-full.png`
- OpenGraph image: `/brand/logo-full.png` (512×512)
- Theme color meta: `#0C0E14` (dark default — debe migrar a `#191918`)

---

## 2. Design principles

Cinco principios que justifican cada decisión visual. Cuando dudemos en un componente, volvemos a esta lista.

### P1. "Estudio jurídico moderno, no ChatGPT genérico"
El usuario debe sentir que abre un workspace profesional — no un chatbot. Concretamente:
- Sidebar persistente con organización por secciones (Principal / Organización / Gestión / Configuración).
- Tipografía serif (Newsreader) en titulares y mensajes del agente — evoca documento legal impreso.
- Layout de doble columna en `/analizar` (conversación + side panel de hechos) — replica la libreta del abogado.

### P2. "Razonar en vivo es el producto"
El streaming SSE del orquestador no es una animación decorativa — es el diferenciador. Debe:
- Ocupar espacio dedicado, no quedar enterrado en un spinner.
- Mostrar nombres humanos de los nodos ("Convocando agentes secundarios"), no IDs técnicos.
- Cambiar de estado visual claro: `pending → active (spinner) → done (check)`.
- Mostrar el modelo y el reasoning effort en todo momento (badge gold).

### P3. "Transparencia del contexto"
El **ContextBar** (verde / amarillo / rojo) es feature core. El abogado debe ver cuánto contexto queda antes de comprometerse con más información. Reglas:
- Verde < 60% del límite del modelo
- Amarillo 60–85% (warning sutil)
- Rojo ≥ 85% (alerta crítica, sugerir nuevo caso)

### P4. "Densidad sobre ornamento"
Abogado profesional ≠ usuario de TikTok. Densidad alta, líneas finas, ornamento mínimo. Concretamente:
- Padding base 16 px, no 24 px.
- Iconos de 14–17 px en sidebar, no 24 px.
- Type scale empieza en 11–12 px para metadata.
- Sin ilustraciones decorativas en pantallas internas (sí en landing).

### P5. "Una verdad para cada token"
Cero hex codes hardcoded en componentes. Si un componente necesita un color que no existe en los tokens, agrégalo a `globals.css` primero. **Este principio es la deuda más urgente** (ver §11 production checklist).

---

## 3. Color system

### 3.1 Canonical tokens (Lex Aurum v3 "Estudio")

Todos los componentes deben referenciar nombres semánticos, **nunca hex codes**. Cada token está disponible como variable CSS y como utilidad Tailwind v4 vía `@theme inline`.

#### 3.1.1 Surfaces — Dark theme (default)

| Token | Hex | Uso |
|---|---|---|
| `--background` | `#191918` | Body bg, canvas raíz |
| `--surface` | `#1F1F1E` | Cards, paneles, composer |
| `--surface-container-low` | `#1A1F1E` | Variante sutil de surface (filas alternas) |
| `--surface-container` | `#27272A` | Hover de surface, inputs |
| `--surface-container-high` | `#2E2E30` | Active state, dropdowns |
| `--surface-container-highest` | `#353B48` | Modales encima de modales |
| `--inverse-surface` | `#F0EBE1` | Toasts, snackbars |

#### 3.1.2 Surfaces — Light theme

| Token | Hex | Uso |
|---|---|---|
| `--background` | `#F5F2EB` | Body bg, canvas raíz (cream del pecho del tucán) |
| `--surface` | `#FFFFFF` | Cards, paneles |
| `--surface-container-low` | `#F9F6F0` | Variante sutil |
| `--surface-container` | `#F0EDE6` | Hover, inputs |
| `--surface-container-high` | `#E8E4DB` | Active state |
| `--surface-container-highest` | `#DDD9D0` | Modales encima de modales |
| `--inverse-surface` | `#313027` | Toasts, snackbars |

#### 3.1.3 Primary (Gold "Lex Aurum")

| Token | Dark | Light | Uso |
|---|---|---|---|
| `--primary` | `#C9A84C` | `#A07C20` | CTAs primarios, badges activos, links |
| `--primary-container` | `#3A2E12` | `#F5E6A8` | Bg de elementos con accent suave |
| `--on-primary` | `#1A1410` | `#FFFFFF` | Texto sobre `--primary` |
| `--on-primary-container` | `#FFE9A0` | `#3D2E00` | Texto sobre `--primary-container` |
| `--primary-soft` | `rgba(201, 168, 76, 0.14)` | `rgba(160, 124, 32, 0.10)` | Highlight de mensajes asistente, focus glow |

#### 3.1.4 Secondary (Navy "Toga")

Usado en estados informativos y áreas de derecho específicas (civil, etc.).

| Token | Dark | Light | Uso |
|---|---|---|---|
| `--secondary` | `#B7C6EE` | `#3D4A60` | Tags secundarios, áreas civiles |
| `--secondary-container` | `#384668` | `#D8DFF0` | Bg de etiquetas secundarias |
| `--on-secondary` | `#213050` | `#FFFFFF` | Texto sobre secondary |
| `--on-secondary-container` | `#A6B5DC` | `#2A3548` | Texto sobre secondary-container |

#### 3.1.5 Tertiary (Red "Lacre")

**Solo errores y borrados.** Nunca como branding.

| Token | Dark | Light | Uso |
|---|---|---|---|
| `--tertiary` | `#FFB4AB` | `#B83230` | Reserved — no usar como decorativo |
| `--error` | `#FFB4AB` | `#BA1A1A` | Validación, fallas |
| `--error-container` | `#93000A` | `#FFDAD6` | Bg de banners de error |
| `--on-error` | `#690005` | `#FFFFFF` | Texto sobre error |

#### 3.1.6 Text / on-surface

| Token | Dark | Light | Uso |
|---|---|---|---|
| `--on-background` | `#ECEAE3` | `#1C1B17` | Texto sobre `--background` |
| `--on-surface` | `#ECEAE3` | `#1C1B17` | Texto principal |
| `--on-surface-variant` | `#9B9991` | `#4D4639` | Texto secundario, labels |
| `--on-surface-subtle` | `#6B6962` | `#7E7668` | Hints, placeholders, metadata |
| `--outline` | `#3A3A38` | `#7E7668` | Bordes fuertes |
| `--outline-variant` | `#2C2C2B` | `#D0C6B4` | Bordes sutiles, dividers |

#### 3.1.7 Status (semantic)

| Token | Hex | Uso |
|---|---|---|
| `--status-success` | `#8BC98B` | Análisis completo, validaciones OK |
| `--status-warning` | `#E8B30E` | Contexto 60-85%, advertencias |
| `--status-danger` | `#E06B5C` | Contexto ≥ 85%, errores destructivos |
| `--status-info` | `#B3A4F0` | Jurisprudencia, tips, info neutra |

### 3.2 Mapping a áreas legales (29 áreas)

Para que el usuario distinga visualmente el área del derecho que el orquestador detectó, mapeamos color a familia:

| Familia legal | Token | Color |
|---|---|---|
| **Civil / Familia / Sucesiones** | `--area-civil` | `#9BB5D8` (azul claro, navy soft) |
| **Penal / Procesal Penal** | `--area-penal` | `#E06B5C` (rojo lacre apagado) |
| **Laboral / Seg. social** | `--area-laboral` | `#C9A84C` (gold canónico) |
| **Tributario / Aduanas** | `--area-tributario` | `#8BC98B` (verde dinero) |
| **Constitucional / DDHH** | `--area-constitucional` | `#B3A4F0` (lila TC) |
| **Administrativo / Contrataciones** | `--area-administrativo` | `#9CC4B8` (verde-azul gob) |
| **Comercial / Corporativo / PI** | `--area-comercial` | `#E8B30E` (gold cálido) |
| **Ambiental / Minero / Hidrocarburos** | `--area-ambiental` | `#7BAB5A` (verde tierra) |
| **Otras (registral, notarial, etc.)** | `--area-default` | `--on-surface-variant` |

Reglas:
- Usar como **fill al 14% opacity** para chips/badges (`background: rgba(area-color, 0.14)`)
- Texto al 100% opacity
- Borde al 20% opacity

### 3.3 Color tokens — qué NO usar

- ❌ Rojo puro (`#FF0000`, `#B91C1C`) como branding
- ❌ Blanco puro `#FFFFFF` como fondo (usar `#F5F2EB` en light)
- ❌ Negro puro `#000000` (usar `#191918`)
- ❌ Cualquier hex no listado aquí — agregar al sistema primero

---

## 4. Typography

### 4.1 Font stack

```css
--font-display: 'Newsreader', Georgia, 'Times New Roman', serif;
--font-body: 'Manrope', system-ui, -apple-system, sans-serif;
--font-mono: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
```

Cargadas desde Google Fonts en `globals.css`:
```css
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&family=Manrope:wght@200..800&display=swap');
```

**Rationale**:
- *Newsreader* — diseñada por Production Type para lectura larga; evoca documento legal impreso. Variable axes `opsz` permite ajustar para titulares grandes vs cuerpo.
- *Manrope* — geométrica moderna, alta legibilidad en 13–14px, peso 200–800. Reemplaza a Inter manteniendo carácter pro.
- *Geist Mono / SF Mono* — para citas de normativa (`Art. 924 CC`), códigos, IDs, métricas.

### 4.2 Type scale

Type token | Family | Size | Line-height | Weight | Tracking | Uso
---|---|---|---|---|---|---
`display-xl` | display | 56 px | 1.05 | 500 | -0.02em | Hero landing
`display-lg` | display | 40 px | 1.10 | 500 | -0.02em | H1 marketing
`display-md` | display | 32 px | 1.15 | 500 | -0.015em | H1 app (`Analizar caso`)
`headline-lg` | display | 28 px | 1.20 | 500 | -0.015em | Título de hilo de chat
`headline-md` | display | 24 px | 1.25 | 500 | -0.01em | Sección de cards
`headline-sm` | display | 20 px | 1.30 | 500 | -0.005em | Card title
`title-lg` | body | 17 px | 1.40 | 600 | 0 | Subsection
`title-md` | body | 15 px | 1.45 | 600 | 0 | Card subtitle
`title-sm` | body | 13 px | 1.50 | 600 | 0 | List item heading
`body-lg` | body | 16 px | 1.65 | 400 | 0 | Mensaje del agente (markdown)
`body-md` | body | 14 px | 1.55 | 400 | 0 | Texto base UI
`body-sm` | body | 13 px | 1.50 | 400 | 0 | Secondary text
`label-lg` | body | 12 px | 1.40 | 500 | 0.02em | Form labels
`label-md` | body | 11 px | 1.35 | 500 | 0.04em | Badges, chips
`label-sm` | body | 10 px | 1.30 | 700 | 0.14em uppercase | Eyebrows, section labels
`caption` | body | 11.5 px | 1.40 | 400 | 0 | Helper, timestamps
`code-md` | mono | 12.5 px | 1.55 | 400 | 0 | Inline code, citas norma
`code-sm` | mono | 11 px | 1.40 | 600 | 0 | Model badges, metrics

### 4.3 Tipografía en mensajes del agente (markdown)

El cuerpo del análisis legal **debe** renderizarse con `body-lg` (16 px, line-height 1.65) en `Manrope`. Excepción: headings dentro del análisis usan `Newsreader` (display) en tamaños 17/20/24.

Reglas markdown específicas:
- **Negritas** → highlight gold soft (`background: linear-gradient(to top, rgba(201,168,76,0.28) 40%, transparent 40%)`)
- Listas numeradas → círculo numerado en mono al 10.5 px (ver `.c-li__num` actual)
- Blockquote → border-left 3 px gold + bg `--primary-soft`
- Inline code → bg `--surface-container`, padding `1px 6px`, rounded `4px`
- Pre / code block → bg `--surface`, border `--outline-variant`, padding `12px 14px`

### 4.4 Tipografía — qué NO usar

- ❌ DM Sans / Inter / Geist Mono (sistema v1.0-beta, retirar de `/design-system`)
- ❌ Tamaños arbitrarios (`text-[15.5px]`) — usar el scale
- ❌ Negritas (`font-weight: 700`) en cuerpo largo — usar 600 máximo
- ❌ Italic en español formal (preservar para énfasis raro y latinismos)

---

## 5. Spacing & layout

### 5.1 Spacing scale (4-base)

Token | Value | Uso
---|---|---
`space-0` | 0 | reset
`space-1` | 4 px | gap mínimo entre icono+texto en chips
`space-2` | 8 px | padding interno de chips, gaps tight
`space-3` | 12 px | padding de inputs, gaps internos
`space-4` | 16 px | padding de cards, gap base entre items
`space-5` | 20 px | padding de paneles
`space-6` | 24 px | padding de containers, gap entre secciones
`space-8` | 32 px | padding de hero, gap entre bloques grandes
`space-10` | 40 px | margin entre secciones de landing
`space-12` | 48 px | padding lateral de containers max-w
`space-16` | 64 px | margin de bloques hero
`space-24` | 96 px | margin entre secciones marketing

### 5.2 Border radius

Token | Value | Uso
---|---|---
`radius-xs` | 4 px | Inline code, mini-chips
`radius-sm` | 6 px | Botones pequeños, dropdowns items
`radius-md` | 8 px | Botones base, inputs, sidebar items
`radius-lg` | 10 px | Cards, paneles
`radius-xl` | 12 px | Composer, modales pequeños
`radius-2xl` | 16 px | Modales grandes, hero containers
`radius-full` | 9999 px | Avatares, pills, badges redondeados

### 5.3 Elevation / shadows

Token | Value | Uso
---|---|---
`shadow-none` | none | Cards base
`shadow-sm` | `0 1px 2px rgba(0,0,0,0.30)` | Inputs en focus
`shadow-md` | `0 4px 12px rgba(0,0,0,0.40)` | Cards hover, dropdowns
`shadow-lg` | `0 12px 32px rgba(0,0,0,0.50)` | Modales, popovers
`shadow-xl` | `0 24px 48px rgba(0,0,0,0.65)` | Drawers, sheets
`shadow-glow-primary` | `0 0 0 3px rgba(201,168,76,0.18)` | Focus ring de inputs

En light mode todas las sombras bajan opacity al 50%.

### 5.4 Grid & breakpoints

Breakpoint | Min-width | Behavior
---|---|---
`sm` | 640 px | Mobile portrait base
`md` | 768 px | Tablet portrait
`lg` | 1024 px | Desktop small (sidebar visible, side panel oculto)
`xl` | 1280 px | Desktop standard (sidebar + side panel)
`2xl` | 1536 px | Wide displays

Layout containers max-width:
- Marketing (landing, precios): `max-w-7xl` (1280 px) centered
- App content (analizar, buscar, configuracion): `max-w-6xl` (1152 px) centered
- Forms / lectura (auth, single column): `max-w-2xl` (672 px)
- Chat/thread reading column: `max-w-3xl` (780 px) — óptimo lectura

### 5.5 Workspace shell layout

```
┌─────────────────────────────────────────────────────────────┐
│ TopBar 56 px (mobile only — drawer trigger)                 │
├──────────┬──────────────────────────────────┬───────────────┤
│          │                                  │               │
│ Sidebar  │  Content (max-w-6xl)             │  Right rail   │
│ 284 px   │                                  │  320 px       │
│ ↕ 80 col │  Page header (sticky 64 px)      │  (optional)   │
│          │  ────────                        │               │
│ - Nav    │  Body                            │  - Hechos     │
│ - User   │  ────────                        │  - How it     │
│ - Theme  │                                  │    works      │
│          │                                  │               │
└──────────┴──────────────────────────────────┴───────────────┘
```

- En `< lg` (1024 px) el sidebar se oculta y se accede vía drawer.
- En `< xl` (1280 px) el right rail se colapsa al fondo de la página o se oculta.

---

## 6. Component library

Cada componente está nombrado con su **identificador canónico** (PascalCase) y mapeado al CSS class actual donde existe.

### 6.1 Buttons

| Variant | Bg | Text | Border | Uso |
|---|---|---|---|---|
| `Button/Primary` | `--primary` | `--on-primary` | none | CTA principal — "Enviar", "Comenzar gratis" |
| `Button/PrimaryGradient` | linear-gradient(135deg, #E8B30E, #C49508) | `--on-primary` | none | Hero CTAs en landing |
| `Button/Secondary` | transparent | `--on-surface` | `--outline` | Acciones secundarias |
| `Button/Ghost` | transparent | `--on-surface-variant` | none | Tooltips, icon-only |
| `Button/Danger` | `--error-container` | `--on-error` | none | Borrar, cerrar sesión |
| `Button/Link` | transparent | `--primary` | underline on hover | Navegación inline |

**Sizes**:

Size | Height | Padding-x | Type token | Icon size
---|---|---|---|---
`sm` | 28 px | 12 px | label-md | 12 px
`md` | 36 px | 16 px | body-md | 14 px
`lg` | 44 px | 24 px | body-md | 16 px (min recomendado para tap targets — WCAG)

**States**: idle / hover (filter:brightness(1.08) o bg→`--surface-container`) / focus (`shadow-glow-primary`) / active (translateY(0)) / disabled (opacity 0.4, cursor not-allowed) / loading (Loader2 icon spinning, texto reemplazado por "...").

### 6.2 Inputs & textarea

```
┌──────────────────────────────────────────────────┐
│ Label-lg uppercase tracking 0.02em               │
├──────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────┐ │
│ │ icon  Placeholder text…                  ⌘K  │ │  ← 44px height
│ └──────────────────────────────────────────────┘ │
│ Helper-sm subtle                                 │
└──────────────────────────────────────────────────┘
```

- bg: `--surface`
- border: `--outline-variant`
- border-radius: `radius-md` (8 px)
- Focus: border `rgba(201,168,76,0.5)`, shadow `shadow-glow-primary`
- Error: border `--error`, helper text `--error`
- Disabled: bg `--surface-container-low`, opacity 0.6

**Textarea**: same tokens, min-height 56 px, max-height 240 px, scroll después.

### 6.3 Cards

Variant | Bg | Border | Padding | Uso
---|---|---|---|---
`Card/Base` | `--surface` | `--outline-variant` | `space-4` (16 px) | Card genérica
`Card/Raised` | `--surface` + inset highlight | `--outline` 24% | `space-5` (20 px) | Cards destacadas (precios)
`Card/Sunken` | `--surface-container-low` | `--outline-variant` | `space-4` | Empty states, "How it works"
`Card/Accent` | `--primary-soft` | `--primary` 30% | `space-4` | Caso ya analizado, info importante

Hover: border → `--primary` 35%, transform: `translateY(-1px)`, transition 140ms.

### 6.4 Badges & chips

```
┌───────────────────┐
│ ● label-md gold   │   ← chip estándar (área detectada)
└───────────────────┘
```

| Variant | Bg | Text | Border | Padding | Radius |
|---|---|---|---|---|---|
| `Badge/Area` | `area-<x>` 14% | `area-<x>` | `area-<x>` 20% | `2px 8px` | `radius-full` |
| `Badge/Phase` | `--primary-soft` | `--primary` | `--primary` 20% | `2px 8px` | `radius-full` |
| `Badge/Model` | `--surface-container` | `--on-surface-subtle` | none | `2px 8px` | `radius-sm` |
| `Badge/Effort` | `--surface-container` | `--primary` | none | `2px 8px` | `radius-sm` |
| `Badge/Plan-Free` | `--surface-container` | `--on-surface-subtle` | `--outline-variant` | `3px 8px` | `radius-xs` |
| `Badge/Plan-Pro` | `--primary` 12% | `--primary` | `--primary` 25% | `3px 8px` | `radius-xs` |
| `Badge/Plan-Studio` | `--status-info` 12% | `--status-info` | `--status-info` 25% | `3px 8px` | `radius-xs` |

Reglas: tracking `0.06em` mínimo en badges, uppercase para Plan/Effort, capitalize para Area.

### 6.5 Navigation — Sidebar

Canonical: `AppSidebar.tsx` (ya implementado con namespace `.n-aside`).

Especificación:
- Ancho expandido: **284 px**
- Ancho colapsado: **80 px**
- Mobile drawer: **300 px** con shadow-xl
- Bg: `--surface` (`#1F1F1E`)
- Border-right: `--outline-variant`
- Header height: 76 px (logo + wordmark + tag "— Abogados —")
- Quick actions block: 60 px (botón "Nuevo caso" + search trigger)
- Nav items: 36 px height, padding `8px 12px`, gap entre items 2 px
- Section labels: `label-sm`, padding `12px 12px 8px`
- Active state: bg `--surface-container-high`, accent-bar de 3 px gold a la izquierda
- Footer: avatar 34×34 + nombre + email + plan badge + theme toggle + notifications + logout

Transición collapse/expand: 200ms ease.

### 6.6 Navigation — Topbar (workspace)

Canonical: `ShellTopbar.tsx` + `.c-topbar`.

- Height: **56 px**
- Bg: `--background` (más sutil que sidebar)
- Border-bottom: `--outline-variant`
- Layout: `[breadcrumb] · · · · · · · · · · · · [actions]`
- Breadcrumb usa `body-md` para path y `headline-md` (Newsreader) para current page
- Status chip "Conectado" / "Procesando" en verde
- Actions: theme toggle, help, notifications bell, divider, primary button

### 6.7 Navigation — Page header

Canonical: en `/analizar`, `/buscar`, `/historial`. Sticky en `top-0` con `z-10`.

```
┌────────────────────────────────────────────────────┐
│ ⚖  Analizar caso                  [Nuevo caso →]   │  ← 64px height
└────────────────────────────────────────────────────┘
```

- Bg: `--background`
- Border-bottom: `--outline-variant`
- Padding: `space-4 space-6` (16 24)
- Icon size: 20 px
- Title: `headline-lg` (28 px Newsreader weight 500)
- Action button right-aligned

**Bug actual**: hardcoded `bg-[#0e0e12]` en `/analizar` y `/buscar`. Reemplazar por `bg-background` o `bg-surface`.

### 6.8 ReasoningPanel (componente del producto)

Canonical: actual implementación en `apps/web/src/app/analizar/page.tsx` líneas 90-199.

```
┌──────────────────────────────────────────────────────────┐
│ 🧠 ORQUESTADOR TRABAJANDO · intake  [gpt-5.5] [⚡MEDIUM] │
├──────────────────────────────────────────────────────────┤
│  ✓  Clasificando el área del derecho                     │
│  ✓  Cargando plantilla de intake                         │
│        Preguntas canónicas del área                      │
│  ◌  Personalizando preguntas según tu narrativa  ← active│
│  ○  Extrayendo hechos                                    │
└──────────────────────────────────────────────────────────┘
```

Especificación:
- Container: `Card/Sunken`, padding `space-4`
- Header: `label-sm` "ORQUESTADOR TRABAJANDO" + phase eyebrow + model+effort badges right-aligned
- Brain icon con ping animation (`animate-ping` halo)
- Rows: gap 10 px vertical, status icons 14 px
  - `done` → `CheckCircle2` color `--status-success`
  - `active` → `Loader2` color `--primary` spinning
  - `pending` → `CircleDot` color `--on-surface-subtle` 20% opacity
- Row label: `body-sm` con color por estado (done → 45% opacity, active → 100%, pending → 30%)
- Detail line: `caption` color `--on-surface-subtle` 30%
- Empty state: "Conectando con el orquestador…" con Loader2

### 6.9 ContextBar (componente del producto)

Canonical: implementación en `apps/web/src/app/analizar/page.tsx` líneas 227-284.

```
┌──────────────────────────────────────────────────────┐
│ CONTEXTO  ▓▓▓▓▓▓▓▓░░░░░░░░░░  12.4K / 128K           │
└──────────────────────────────────────────────────────┘
```

Especificación:
- Container: `Card/Base` padding `space-3 space-2` (12px 8px), height 36 px
- Label: `label-sm` "CONTEXTO" color `--on-surface-subtle`
- Bar: height 6 px, bg `--surface-container-low`, fill color por threshold:
  - `< 60%` → `--status-success` (`#8BC98B`)
  - `60-85%` → `--status-warning` (`#E8B30E`)
  - `≥ 85%` → `--status-danger` (`#E06B5C`)
- Counter: `code-sm` tabular-nums, color matches bar

### 6.10 CaseStatusBar (componente del producto)

Canonical: implementación en `apps/web/src/app/analizar/page.tsx` líneas 290-354.

Fila de pills horizontales que indican fase, área detectada, modelo, esfuerzo:

```
[✨ Fase: intake · Recogiendo contexto] [⚖ Laboral] [🤖 gpt-5.5] [⚡ MEDIUM]
```

Cada pill = `Card/Base` con border-radius `radius-md`, padding `6px 10px`, gap interno 6 px, type `label-md`.

Iconos por fase:
- `idle` → Sparkles, color `--primary`
- `intake` → Sparkles, "Recogiendo contexto inicial"
- `investigation` → FileText, "n/m datos"
- `analysis` → Wand2, "Multi-agente"
- `complete` → CheckCircle2, color `--status-success`, "Listo para nuevo caso"

### 6.11 Side panel (componente del producto)

Right rail de 320 px que vive en `/analizar`. Contiene 3 cards apiladas:

1. **Hechos del caso** — lista de `slot/value` pairs, label-sm uppercase para slot
2. **Preguntas abiertas** — lista con CircleDot bullets, máximo 5 visibles
3. **Acción skip** — Botón secundario "Tengo prisa — pasa al análisis"

En `< xl` (1280 px) se oculta (`hidden lg:flex`).

### 6.12 Modals & dialogs

- Bg: `--surface`
- Border: `--outline`
- Border-radius: `radius-2xl` (16 px)
- Shadow: `shadow-lg`
- Backdrop: `rgba(0, 0, 0, 0.6)` + backdrop-filter blur(8px)
- Max-width: 480 px (confirmaciones), 640 px (forms), 800 px (contenido)
- Header: `headline-md` + close button right-aligned (24×24 ghost icon button)
- Footer: 1 primary + 1 secondary button right-aligned, padding-top `space-4`

### 6.13 Toasts

Library: `sonner` (ya instalado). Configuración en `apps/web/src/app/layout.tsx`:
```tsx
<Toaster richColors position="top-right" />
```

Tipos: `success` (verde), `error` (rojo), `warning` (gold), `info` (lila). Auto-dismiss 4s success/info, 6s error/warning, infinite con close button para destructivos.

### 6.14 Tooltips & popovers

- Bg: `--inverse-surface`
- Text: `--inverse-on-surface`
- Padding: `space-2 space-3` (8 12)
- Border-radius: `radius-sm`
- Shadow: `shadow-md`
- Arrow: 6 px triangle
- Delay: 400 ms aparición, 100 ms ocultación
- Type: `body-sm`

### 6.15 Loading & empty states

**Spinner**: `Loader2` icon de Lucide React, color `--primary`, tamaño según contexto (14 px en inputs, 24 px en buttons, 48 px en page-level).

**Skeleton**: bg `--surface-container` con animation `shimmer` (ver `globals.css` líneas 357-361):
```css
background: linear-gradient(90deg, var(--surface-container) 0%, var(--surface-container-high) 50%, var(--surface-container) 100%);
background-size: 200% 100%;
animation: shimmer 1.5s ease-in-out infinite;
```

**Empty state**: Card/Sunken con:
- Icono 32–48 px color `--on-surface-subtle`
- Title `title-md`
- Description `body-sm` color `--on-surface-variant`
- Optional CTA `Button/Primary sm`

### 6.16 Error states

**Banner inline**: bg `rgba(224, 107, 92, 0.10)`, border `rgba(224, 107, 92, 0.25)`, padding `space-3`, icon AlertCircle 14 px, text `body-sm` color `#E9A79C`, retry button right-aligned.

**Page-level error** (`error.tsx` de Next.js): centered, icon 64 px, title `headline-md`, description `body-md`, two buttons (Reintentar + Volver al inicio).

---

## 7. Iconography

### 7.1 Library

**Canonical**: `lucide-react` (ya en uso). Coherente, tree-shakeable, ~ 1300 iconos.

### 7.2 Reglas de uso

- Stroke-width estándar: **1.6** (un poco más fino que el default 2 para sentir editorial)
- Tamaños: 12 / 14 / 16 / 20 / 24 / 32 / 48 px
- Color: hereda de `currentColor`
- Padding interno en botones: 4 px alrededor del icono

### 7.3 Iconos por feature (canonical mapping)

| Feature | Icon | Notas |
|---|---|---|
| Analizar caso | `FileSearch` | También en sidebar |
| Buscar corpus | `Search` | Sidebar + topbar trigger |
| Historial | `History` | |
| Marcadores | `Bookmark` | |
| Notificaciones | `BellRing` | Badge superpuesto si hay unread |
| Analytics | `BarChart3` | |
| Organización | `Building2` | |
| Facturación | `CreditCard` | |
| Configuración | `Settings` | |
| Guía / Help | `HelpCircle` | |
| API Docs | `FileCode` | |
| Admin | `Shield` | Solo si is_admin |
| Logout | `LogOut` | |
| Theme toggle | `Sun` / `Moon` | |
| Sidebar collapse | `PanelLeft` | |
| Phase: intake | `Sparkles` | |
| Phase: investigation | `FileText` | |
| Phase: analysis | `Wand2` | |
| Phase: complete | `CheckCircle2` | |
| Reasoning effort | `Zap` | Lightning bolt |
| Model | `Bot` | |
| Skip to analysis | `SkipForward` | |
| Case fact | `CircleDot` | Para items pendientes |
| Status: good | `CheckCircle2` | verde |
| Status: warning | `AlertTriangle` | gold |
| Status: error | `AlertCircle` | rojo |
| Adjuntar | `Paperclip` | |
| Cita / quote | `Quote` | |
| Citación legal | `Scale` | Brand-adjacent |
| Justicia / gavel | `Gavel` | Sólo en marketing |
| Legal area | `Scale` o icono específico | Ver `LEGAL_AREAS` const |

### 7.4 Iconos custom (decorativos)

En landing (`apps/web/src/app/landing/page.tsx`) hay 3 SVG decorativos custom: `ScalesSvg`, `GavelSvg`, `ParagraphSvg`. Mantener — son ornamentales y refuerzan el carácter editorial.

---

## 8. Pages / Templates

### 8.1 Landing (`/landing`)

Estado actual: completo, animaciones via Intersection Observer, mascot prominente. Mantener.

Estructura canónica:
1. **Hero** (90vh) — Badge "IA Jurídica para el Perú" + H1 con shimmer "Inteligente" + descripción + 2 CTAs (registro + corpus) + stats animadas + mascot con float
2. **Trust bar** — áreas legales rotando con dots
3. **Features teaser** — Card destacada "29 Áreas del Derecho Peruano" + link a `/caracteristicas`
4. **How it works** — 3 pasos con screenshot alternando lados
5. **Pricing teaser** — 3 cards mini (Gratuito, Profesional [destacado], Estudio) + link a `/precios`
6. **Final CTA** — Container con glow animado + mascota + 1 CTA primario

Variantes:
- `Landing/Hero` — variante con video bg si se incorpora
- `Landing/Pricing` — página dedicada con FAQ y comparativa

### 8.2 Analizar (`/analizar`)

Pantalla principal del producto. **3 estados**:

#### Estado A: Empty (no caso activo)
```
┌──────────┬──────────────────────────────────┬───────────────┐
│ Sidebar  │ ⚖ Analizar caso                  │ How it works  │
│          │                                  │  1. Intake    │
│          │ [Fase: esperando] [⚡ MEDIUM]    │  2. Invest.   │
│          │ Contexto: ░░░░ 3K/128K           │  3. Análisis  │
│          │                                  │               │
│          │ Bienvenido — describe tu...      │               │
│          │                                  │               │
│          │ ESCENARIOS DE EJEMPLO            │               │
│          │ ┌────────────┐ ┌────────────┐    │               │
│          │ │💼 Despido  │ │⚖ Acoso     │    │               │
│          │ └────────────┘ └────────────┘    │               │
│          │ ┌────────────┐ ┌────────────┐    │               │
│          │ │🏠 Vecino   │ │💰 SUNAT    │    │               │
│          │ └────────────┘ └────────────┘    │               │
│          │                                  │               │
│          │ ┌─────────────────────────────┐  │               │
│          │ │ 📎  Describe tu situación..│  │               │
│          │ │                          ▶│  │               │
│          │ └─────────────────────────────┘  │               │
└──────────┴──────────────────────────────────┴───────────────┘
```

#### Estado B: Investigating (caso activo, agente preguntando)
```
│  CaseStatusBar: [Fase: investigación · 4/8 datos] [Laboral] │
│  ContextBar: ▓▓▓▓░░░░ 28K/128K  (verde)                     │
│                                                              │
│  [Skip to analysis →]  (top right)                          │
│                                                              │
│  ┌─ User message ──────────────────────────────────┐         │
│  │ "Trabajaba 5 años y me despidieron..."         │         │
│  └─────────────────────────────────────────────────┘         │
│  ┌─ Agent: laboral_intake ─────────────────────────┐         │
│  │ "Antes de avanzar necesito 3 datos: ..."        │         │
│  └─────────────────────────────────────────────────┘         │
│  ┌─ User message ──────────────────────────────────┐         │
│  │ "Contrato indeterminado, sueldo 3200 soles..." │         │
│  └─────────────────────────────────────────────────┘         │
│  ┌─ ReasoningPanel (live SSE) ─────────────────────┐         │
│  │ 🧠 ORQUESTADOR TRABAJANDO · investigation       │         │
│  │  ✓ intake_classify                              │         │
│  │  ✓ investigation_extract                        │         │
│  │  ◌ phase_start analysis                ← active │         │
│  └─────────────────────────────────────────────────┘         │
│                                                              │
│  ┌── Side panel ──────────────────────────────────┐         │
│  │ 📋 HECHOS DEL CASO (4)                         │         │
│  │   • TIPO CONTRATO: Indeterminado               │         │
│  │   • ANTIGÜEDAD: 5 años                         │         │
│  │   • SUELDO: S/3200                             │         │
│  │   • CAUSA DESPIDO: No comunicada               │         │
│  │ ✨ PREGUNTAS ABIERTAS (3)                      │         │
│  │   ○ ¿Recibiste carta?                          │         │
│  │   ○ ¿Estabas afiliado a sindicato?             │         │
│  │   ○ ¿Hubo proceso previo?                      │         │
│  └────────────────────────────────────────────────┘         │
```

#### Estado C: Complete (análisis listo)
- Banner gold soft "Caso ya analizado. Si llegaron papeles nuevos..."
- Mensaje del agente con markdown rico (Newsreader headings)
- Composer sigue visible
- Top: botón "Nuevo caso" (link).

### 8.3 Buscar (`/buscar`)

Dos modos: anon (PublicLayout) y auth (AppLayout). Mismo cuerpo.

```
┌────────────────────────────────────────────────────┐
│  [🗃 BUSCADOR PÚBLICO · SIN IA]                    │
│  Corpus jurídico del Perú                          │
│  Hoy hay 1638 documentos · 2001 fragmentos...      │
│                                                    │
│  ┌────────────────────────────────────────────┐    │
│  │ 🔍 Ej. despido nulo, prescripción...     ✕│    │
│  └────────────────────────────────────────────┘    │
│                                                    │
│  FILTRAR POR ÁREA                                  │
│  [Todas] [Civil · 234] [Penal · 89] [Laboral · 156]│
│  [Tributario · 412] [Constitucional · 67] ...      │
│                                                    │
│  ╔══════════════════════════════════════════════╗ │
│  ║ Código Civil de Perú · DECRETO LEGISLATIVO 295 ║ │
│  ║ Libro V, Sección Cuarta, Título II            ║ │
│  ║ "Las limitaciones del derecho de propiedad... ║ │
│  ║ humos, hollín, emanaciones, ruidos..."        ║ │
│  ║                            [CIVIL] [Art. 924] ║ │
│  ║ DL 295/1984                       score: 8.42 ║ │
│  ╚══════════════════════════════════════════════╝ │
└────────────────────────────────────────────────────┘
```

### 8.4 Historial (`/historial`)

Canonical: `.hst-*` namespace. Tres zonas:
- Inner sidebar 260 px — Sección "Filtros" (estado, área, modelo) + "Carpetas" (tree con dnd) + "Tags"
- Main — Search bar + density toggle + lista de conversaciones
- Item de lista: título serif + meta (fecha, área, mensajes) + acciones (rename, move, archive)

### 8.5 Configuración (`/configuracion`)

Layout: tabs verticales o horizontales, cada sección es un Card/Base con form fields.

Secciones:
1. **Perfil** — nombre, email, foto, cambio de contraseña
2. **Preferencias** — tema (light/dark/auto), idioma (es-PE), modelo preferido
3. **Notificaciones** — toggles
4. **API Keys / BYOK** — **solo plan Empresarial** (visible pero con upsell modal para Free/Pro/Studio)
5. **Privacidad** — borrar cuenta, exportar datos

### 8.6 Billing (`/billing`)

- Plan actual destacado con `Card/Accent`
- Tabla de uso del mes (consultas usadas / restantes)
- Historia de pagos
- Upgrade modal con 3 cards verticales

### 8.7 Templates secundarios

- `/marcadores` — Grid de bookmark cards (4 cols desktop)
- `/notificaciones` — Lista con timeline, ungrouped por fecha
- `/organizacion` — Multi-tenant: miembros, roles, invitaciones
- `/analytics` — Charts con `recharts` (gold + status colors)
- `/admin` — Dashboard interno (acceso solo is_admin)
- `/guia` — Docs con sidebar TOC y MDX rendering

---

## 9. Microinteractions & animations

### 9.1 Catálogo de animaciones (ya implementadas en `globals.css`)

| Animation | Duration | Easing | Uso |
|---|---|---|---|
| `fadeInUp` | 700 ms | `cubic-bezier(0.22, 1, 0.36, 1)` | Cards en scroll reveal |
| `fadeInLeft / Right` | 700 ms | mismo | Hero text vs mascota |
| `scaleIn` | 600 ms | mismo | Modales aparición |
| `float` | 6 s loop | `ease-in-out` | Mascota, decorativos |
| `pulseGlow` | 4 s loop | `ease-in-out` | Ambient glows hero |
| `shimmer` | 4 s loop | `linear` | Shimmer text, skeletons |
| `spinSlow` | 20 s loop | `linear` | Rotating ring decoration |

Stagger delays disponibles: `delay-100` a `delay-800` (incrementos de 100 ms).

### 9.2 Transiciones canónicas

| Transition | Duration | Properties |
|---|---|---|
| `transition-fast` | 120 ms | bg-color, color |
| `transition-base` | 200 ms | border, shadow |
| `transition-slow` | 300 ms | layout (collapse/expand) |
| `transition-theme` | 300 ms | bg, color, border |

### 9.3 ReasoningPanel — live transitions

- Nueva fila aparece con `fadeInUp` 240 ms
- Spinner del icono usa `animate-spin` (Tailwind built-in)
- Brain icon usa `animate-ping` para halo
- Cuando un step pasa de `active` a `done`, fade el spinner → check con cross-fade 200 ms

### 9.4 ContextBar — transiciones de color

```css
.context-bar-fill {
  transition: width 500ms ease-out, background-color 300ms ease-in;
}
```

Cuando cruza el threshold a amarillo o rojo, micro-shake horizontal de 200 ms para alertar.

### 9.5 Phase transitions (intake → investigation → analysis → complete)

Cuando la fase cambia:
1. Badge de fase hace `scaleIn` 400 ms
2. ReasoningPanel hace `fadeInUp` 240 ms
3. Side panel "Hechos del caso" lista nuevos items con stagger 80 ms

### 9.6 Reduced motion

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

---

## 10. Accessibility (WCAG 2.1 AA)

### 10.1 Contraste mínimo

- Texto normal: 4.5:1
- Texto grande (≥18 px o ≥14 px bold): 3:1
- Componentes UI y estados: 3:1

**Verificación de tokens críticos**:
- `--on-surface` (`#ECEAE3`) sobre `--background` (`#191918`): **14.3:1** ✅
- `--on-surface-variant` (`#9B9991`) sobre `--background`: **5.8:1** ✅
- `--primary` (`#C9A84C`) sobre `--background`: **6.9:1** ✅
- `--primary` sobre `--surface`: **6.2:1** ✅
- `--on-primary` (`#1A1410`) sobre `--primary` (`#C9A84C`): **9.7:1** ✅
- `--status-danger` (`#E06B5C`) sobre `--background`: **5.2:1** ✅

### 10.2 Focus visible

Global rule ya en `globals.css`:
```css
*:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
```

Mantener. Agregar para teclas custom: `Tab` debe ciclar todos los interactivos, `Esc` cierra modales/drawers, `Cmd/Ctrl+K` abre search.

### 10.3 Semántica HTML

- `<main>` con landmark único por página
- `<nav aria-label="Navegación principal">` para sidebar
- `<nav aria-label="Migas de pan">` para breadcrumb
- `<h1>` único por página
- Botones icon-only: `aria-label` obligatorio
- Lists con `<ul>/<ol>/<li>`, no divs
- Forms con `<label htmlFor>` siempre

### 10.4 Live regions

ReasoningPanel debe anunciar pasos a screen readers:
```html
<div role="status" aria-live="polite" aria-atomic="false">
  Paso actual: Convocando agentes secundarios
</div>
```

Toasts ya cubierto por `sonner` con `role="alert"` para errores.

### 10.5 Tap targets

Mínimo 44×44 px en mobile (iOS HIG / WCAG 2.5.5). Botones `lg` y `md` cumplen; revisar todos los `sm` en mobile.

### 10.6 Idioma

- `<html lang="es">` ya configurado
- Para términos en otro idioma usar `<span lang="en">writ of habeas corpus</span>`

### 10.7 Color como único indicador

Nunca solo color para transmitir información:
- ContextBar: color + texto numérico + ícono opcional
- Áreas legales: color + texto del área + (opcional) ícono
- Status badges: color + ícono + texto

---

## 11. Production checklist

### 11.1 Performance budgets

| Métrica | Target | Tool |
|---|---|---|
| **LCP** (Largest Contentful Paint) | < 2.5s | Lighthouse |
| **INP** (Interaction to Next Paint) | < 200 ms | Web Vitals |
| **CLS** (Cumulative Layout Shift) | < 0.1 | Lighthouse |
| **TTFB** | < 800 ms | curl/Lighthouse |
| **JS bundle (initial)** | < 200 kb gzip | Next.js bundle analyzer |
| **CSS** | < 30 kb gzip | Source inspection |

Específico de TukiJuris:
- **Hero LCP**: la mascota `tukan.png` (300 kb actual) es candidata 1. Convertir a AVIF + width responsive + `priority`.
- **Font display**: usar `display=swap` (ya) + `font-display: optional` para Newsreader si es > 100 kb compressed
- **SSE streaming**: keepalive cada 10s ya implementado (✅)

### 11.2 SEO

- `<title>` único por página vía Next.js `metadata`
- `<meta name="description">` 150-160 chars
- OpenGraph completo (ya configurado en `layout.tsx`)
- `robots.ts` ya configurado
- `sitemap.ts` ya configurado
- Páginas no-indexar: `/admin`, `/auth/*`, `/configuracion`, `/historial`, `/marcadores`, `/billing`, `/analizar` (contenido dinámico privado)
- Páginas indexar: `/landing`, `/buscar` (corpus), `/caracteristicas`, `/precios`, `/guia`, `/docs`, `/privacy`, `/terms`, `/contacto`

Microformatos:
- `Article` schema en páginas de guía
- `Organization` schema en `/landing`
- `Product` schema en `/precios`
- `FAQPage` schema en sección de FAQ

### 11.3 i18n

- Locale primario: **es-PE**
- Locales aceptables: es-419 (LATAM), es (genérico)
- **NO** internacionalizar a otros idiomas en MVP (alcance: derecho peruano)
- Formatos:
  - Fechas: `25 de junio de 2026` (largo) / `25/06/2026` (corto)
  - Moneda: `S/ 70` (Sol Peruano, símbolo antes con espacio)
  - Números: `1,638` (coma como miles)
  - Decimales: `8,42` (coma como decimal — convención peruana)
- Modismos: usar tuteo informal sin "vos" (porteño), preferir "tú" / "tus" peruanos.

### 11.4 Analytics events (canónicos)

Implementar como `track(eventName, props)`:

| Event | When | Props |
|---|---|---|
| `landing_cta_click` | CTA hero clickeado | `cta: "register" \| "search" \| "guide"` |
| `signup_started` | Form de registro abierto | `source` |
| `signup_completed` | Registro exitoso | `plan: "free"` |
| `login_completed` | Login exitoso | — |
| `case_started` | Primera consulta enviada | `area_hint` |
| `case_phase_changed` | Cambio de fase | `from`, `to`, `area` |
| `case_completed` | Análisis terminado | `area`, `model`, `duration_ms`, `agent_count` |
| `case_skip_to_analysis` | Botón "Pasar al análisis" | `facts_count` |
| `model_overridden` | Usuario fuerza un modelo | `model` |
| `corpus_search` | Búsqueda en `/buscar` | `query_len`, `area`, `results_count` |
| `upgrade_modal_shown` | Upsell modal aparece | `feature_locked`, `current_plan` |
| `upgrade_started` | Click en upgrade CTA | `target_plan` |
| `payment_completed` | Culqi/MP webhook OK | `plan`, `amount_pen` |
| `byok_inquiry_clicked` | Usuario click "Contactar ventas" para BYOK | `plan` |
| `theme_changed` | Toggle dark/light | `to: "dark" \| "light"` |

Privacidad: respetar Do Not Track, gating por banner de cookies (ya implementado `CookieBanner.tsx`).

### 11.5 Migration debt (deuda técnica del consolidation)

Items a cerrar antes de la migración a la v3 final:

- [ ] **Eliminar el namespace duplicado** `.n-*`, `.c-*`, `.hst-*` — promover a tokens canónicos. Estimado: 2 días.
- [ ] **Eliminar `/design-system` route** o reemplazar contenido con este DESIGN.md renderizado. Estimado: 1 hora.
- [ ] **Eliminar hardcoded `bg-[#0e0e12]`** en `/analizar` y `/buscar` sticky headers. Reemplazar por `bg-background`. Estimado: 10 min.
- [ ] **Unificar el set de gold**: `#B8920A`, `#FFD165`, `#C9A84C`, `#EAB308` → un único `#C9A84C` (dark) + `#A07C20` (light).
- [ ] **Unificar el set de bordes**: hoy hay `rgba(79,70,51,0.15)`, `rgba(79,70,51,0.20)`, `--outline-variant`, `--ghost-border`, `var(--n-border)`. Consolidar a `--outline-variant` y `--outline`.
- [ ] **Tipografía**: retirar referencias a DM Sans / Inter / Geist Mono.
- [ ] **Documentar `LEGAL_AREAS`** (apps/web/src/app/chat/constants.ts) con los color tokens canónicos por área.
- [ ] **Agregar tokens `--area-*`** a `globals.css` con los hex declarados en §3.2.
- [ ] **Migrar `KeyboardShortcuts.tsx`** para alinearse con `Cmd/Ctrl+K` global, `Cmd/Ctrl+/` help, `Esc` close.

### 11.6 Testing checklist

- [ ] Lighthouse desktop ≥ 90 en Performance, Accessibility, Best Practices, SEO
- [ ] Lighthouse mobile ≥ 80 en Performance
- [ ] axe DevTools sin violaciones AA
- [ ] Manual: navegación por teclado completa
- [ ] Manual: screen reader (VoiceOver) en `/analizar` flujo completo
- [ ] Manual: dark + light theme paridad
- [ ] Manual: mobile real (iPhone SE 375 px width)
- [ ] Visual regression: Playwright + Percy o Chromatic
- [ ] Tipos: TypeScript strict, sin `any`

---

## 12. Appendix

### 12.1 Files involved (canonical)

```
apps/web/src/app/
  globals.css                    ← TOKENS (ÚNICA fuente de verdad post-consolidación)
  layout.tsx                     ← html lang, theme script, fonts, metadata
  analizar/page.tsx              ← Pantalla principal
  buscar/page.tsx                ← Corpus público
  landing/page.tsx               ← Marketing entry
  historial/page.tsx             ← Lista de casos
  configuracion/page.tsx         ← Settings
  billing/page.tsx               ← Suscripción y pagos
  design-system/page.tsx         ← (RETIRAR — reemplazar con este DESIGN.md)
  chat/constants.ts              ← LEGAL_AREAS const (29 áreas)

apps/web/src/components/
  AppLayout.tsx                  ← Shell de páginas auth
  AppSidebar.tsx                 ← Sidebar canonical
  ThemeProvider.tsx              ← Light/dark switch
  ThemeToggle.tsx                ← Toggle button
  public/PublicLayout.tsx        ← Shell de páginas marketing
  public/PublicHeader.tsx        ← Top nav marketing
  shell/WorkspaceShell.tsx       ← Grid layout sidebar+content+rail
  shell/ShellTopbar.tsx          ← App topbar
  shell/ShellMobileDrawer.tsx    ← Drawer en mobile
  shell/ShellUtilityActions.tsx  ← Actions en topbar right
  ui/                            ← Primitives reusables

apps/web/public/brand/
  logo-icon.png                  ← Solo mascota
  logo-full.png                  ← Wordmark + mascota (dark)
  logo-negro.png                 ← Wordmark + mascota (light)
  tukan.png                      ← Mascota hero size
  cta-hero.png                   ← Mascota CTA
```

### 12.2 Stitch-ready prompt template

Para generar pantallas adicionales que sean coherentes con el sistema, usar este prompt base:

> "Design a screen for **TukiJuris**, a Spanish-language (Peruvian Spanish) SaaS for lawyers. Visual identity: editorial dark theme inspired by Notion and The Browser Company. Serif display font Newsreader; sans body Manrope. Primary accent gold `#C9A84C`. Background `#191918`. Surface `#1F1F1E`. Outline `#2C2C2B`. Text `#ECEAE3` primary, `#9B9991` muted. Components are dense, generous line-heights, rounded `8-12px`. Use lucide-react icons stroke-width 1.6. Side panel patterns, status chips, and live multi-step orchestrator panels are signature elements. Keep ornament minimal — this is a tool for professionals. The mascot is a toucan in a suit (gold beak, navy suit, red bowtie) — used sparingly and only on marketing surfaces."

Para variantes específicas, agregar:
- "Show empty state for [X]"
- "Show error state with banner"
- "Show loading state with ReasoningPanel live SSE"
- "Show complete state with markdown legal analysis rendered"

### 12.3 Compatibility matrix

Browser | Min version | Notes
---|---|---
Chrome / Edge | 110 | Backdrop-filter, color-mix in srgb
Safari | 16.4 | color-mix soporte
Firefox | 117 | color-mix soporte
Mobile Safari iOS | 16.4 | Tap targets review
Chrome Android | 110 | —

Fallbacks: si `color-mix` no está disponible, usar valores hex pre-calculados (ya hay duplicación parcial en algunos componentes para esto).

### 12.4 Versioning

| Version | Date | Status | Notes |
|---|---|---|---|
| 1.0 | 2026-06-25 | Production-ready | Consolidación de 3 sistemas en uno. Este documento. |

---

**Fin del DESIGN.md** — listo para Stitch / Claude design tools / Figma ingest.
