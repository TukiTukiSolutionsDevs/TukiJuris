# TukiJuris — Design System & Production Spec (Zona Pública)

> **Scope**: Este documento cubre **únicamente la superficie pública / no autenticada** de TukiJuris: landing, marketing, legal (PE), auth y errores. La zona de aplicación (después del login: `/analizar`, `/historial`, etc.) tendrá su propio `DESIGN_APP.md`.
>
> **Version**: 1.0 — 2026-06-25
> **Compatibilidad**: Stitch (Google), Claude design tools, Figma ingest.
> **Frame**: dark theme primario, light theme paritario. Editorial moderno · "estudio jurídico digital peruano".

---

## 0. Inventario de la zona pública

### 0.1 Rutas (single source: `apps/web/src/lib/constants.ts:PUBLIC_PATHS`)

| Tipo | Ruta | Auth | Layout actual | Purpose |
|---|---|---|---|---|
| **Marketing** | `/landing` | público | `PublicLayout` | Home, hero, value prop |
| | `/caracteristicas` | público | `PublicLayout` | Features showcase |
| | `/precios` | público | `PublicLayout` | Planes + FAQ |
| | `/buscar` | público | `PublicLayout` (auth opcional) | Corpus público sin IA |
| | `/contacto` | público | `PublicLayout` | Canales de contacto |
| | `/guia` | público | `PublicLayout` | Onboarding educativo |
| | `/docs` | público | `PublicLayout` | API docs / referencia |
| | `/compartido` | público | `PublicLayout` | Links de share |
| | `/status` | público | propio | Health (db/redis/etc) |
| **Legal PE** | `/privacy` | público | `LegalHeader/Footer` ⚠️ | Política de privacidad (Ley 29733) |
| | `/terms` | público | `LegalHeader/Footer` ⚠️ | Términos y condiciones |
| | `/libro-reclamaciones` | público | `LegalHeader` ⚠️ | Libro de Reclamaciones (Ley 29571) |
| **Auth** | `/auth/login` | público | dual-column propio | Login + SSO + reset modal |
| | `/auth/register` | público | dual-column propio | Registro + password rules + SSO |
| | `/auth/reset-password` | público | dual-column propio | Reset con token email |
| | `/auth/callback` | público | full-screen loader | OAuth Google / Microsoft return |
| | `/auth/rate-limited` | público | centered card | Demasiados intentos |
| **Errores** | `not-found.tsx` | n/a | centered card | 404 |
| | `error.tsx` | n/a | centered card | 500 / runtime |

### 0.2 Hallazgo crítico — 4 shells coexistiendo

La zona pública sufre el mismo problema de fragmentación que la app:

1. **`PublicLayout`** (PublicHeader + PublicFooter) — `apps/web/src/components/public/` — usado por landing, marketing, contacto, buscar (anon).
2. **`LegalHeader` + `LegalFooter` custom** — duplicado in-file en `/privacy`, `/terms`, `/libro-reclamaciones`. Bordes `style={{ borderBottom: "1px solid rgba(79, 70, 51, 0.15)" }}` hardcodeados, sin theme toggle, sin nav links.
3. **Dual-column auth shells** en `/auth/login` y `/auth/register` con `panel-raised`, sin reuso entre ambas (cada página redefine el branded panel).
4. **Centered card shells** en `not-found`, `error`, `auth/rate-limited`.

**Decisión canónica para v3**: una sola `PublicLayout` configurable con dos modos:
- `mode="marketing"` (default) — header completo con nav + footer completo
- `mode="legal"` — header reducido (logo + CTAs) + footer reducido (links legales)

Y un único `AuthShell` con prop `variant="login" | "register" | "reset" | "callback" | "rate-limited"`.

---

## 1. Brand identity (público)

### 1.1 Posicionamiento desde landing → auth

El usuario público viaja por 3 estados emocionales y la UI debe acompañarlos:

| Estado | Pantallas | Tono | Densidad | Ornamento |
|---|---|---|---|---|
| **Descubrimiento** | landing, caracteristicas, precios | aspiracional, narrativo | baja (16-24 px gap) | alto (mascota, ambient glows, animaciones) |
| **Evaluación** | buscar (anon), guia, docs, contacto | informativo, claro | media (12-16 px gap) | medio (eyebrows, dot-grid, sin mascota) |
| **Compromiso** | auth/login, auth/register | confianza, seguridad | alta (8-12 px gap) | bajo (un solo glow, sin mascota en formulario) |
| **Legal** | privacy, terms, libro-reclamaciones | sobrio, formal | densa lectura larga | ninguno (sin gradients, sin animaciones) |

### 1.2 Pilares de copy en zona pública

- **Tuteo informal** en CTAs y marketing: "Empieza gratis", "Conoce tu plan ideal"
- **Usted neutro** en mensajes legales: "El usuario es responsable de..."
- **Voseo evitado** (porteño): nunca "vos podés" — usar "puedes" (peruano)
- **Disclaimer obligatorio**: siempre que aparezca un CTA legal, incluir "Las respuestas de TukiJuris son orientativas y no constituyen asesoría legal vinculante" (Ley 29571 + buena práctica frente a Colegio de Abogados)
- **Razón social visible**: "TukiTuki Solutions SAC — RUC 20613614509" en footer y páginas legales
- **Emails canónicos**:
  - `soporte@tukijuris.com.pe` — soporte general
  - `ventas@tukijuris.com.pe` — plan Estudio / Empresarial
  - `privacidad@tukijuris.com.pe` — derechos ARCO (Ley 29733)
  - `legal@tukijuris.com.pe` — términos, PI
  - `reclamos@tukijuris.com.pe` — Libro de Reclamaciones

### 1.3 Assets de marca usados en superficie pública

Path | Uso | Donde
---|---|---
`/brand/logo-icon.png` | Solo mascota (favicon, mark) | PublicHeader, PublicFooter, auth mobile
`/brand/logo-full.png` | Wordmark + mascota (dark) | LegalHeader
`/brand/logo-negro.png` | Wordmark + mascota (light) | Theme dependent
`/brand/tukan.png` | Mascota hero | Landing hero, auth left column
`/landing/cta-hero.png` | Mascota CTA | Landing final, precios final
`/landing/feature-areas.png` | Screenshot 29 áreas | Landing teaser, caracteristicas
`/landing/feature-search.png` | Screenshot búsqueda | Caracteristicas
`/landing/feature-byok.png` | Screenshot BYOK | Caracteristicas
`/landing/screenshot-chat.png` | Screenshot chat | How it works step 1
`/landing/screenshot-analytics.png` | Screenshot analytics | How it works step 2
`/landing/screenshot-search-results.png` | Screenshot resultados | How it works step 3

### 1.4 Reglas de uso de mascota

- ✅ Hero de landing, CTA final de landing, CTA final de precios, columna izquierda de auth (login/register)
- ✅ Tamaño hero: `w-56 sm:w-72 lg:w-[380px]` con `drop-shadow-[0_20px_50px_rgba(0,0,0,0.20)]` + `animate-float-slow`
- ❌ No usar en páginas legales (privacy, terms, libro-reclamaciones)
- ❌ No usar en `/buscar`, `/contacto`, `/docs`, `/guia` (densidad media — distrae)
- ❌ No usar en pantallas de error (not-found, error) — momento equivocado para el tono lúdico

---

## 2. Color system (público)

> Misma tabla canónica que `DESIGN.md` §3 — **no duplicamos** tokens. Aquí solo listamos los que se usan en superficie pública.

### 2.1 Tokens usados en zona pública

#### Dark (default — `theme-color` meta `#0C0E14` actual, **migrar a `#191918`**)

Token | Hex | Usado en
---|---|---
`--background` | `#191918` | body bg de todas las páginas públicas
`--surface` | `#1F1F1E` | PublicHeader (con `/80 backdrop-blur`), cards de pricing/feature/contacto, form card de auth
`--surface-container-low` | `#1A1F1E` | Card de feature, FAQ container, contacto channel card
`--surface-container` | `#27272A` | Hover de cards, inputs
`--surface-container-high` | `#2E2E30` | Active de toggle, dropdowns
`--primary` | `#C9A84C` | CTAs gold-gradient, links, eyebrows, headlines accent
`--primary-soft` | `rgba(201, 168, 76, 0.14)` | Bg de eyebrow pills, bg de "MÁS POPULAR" badge
`--on-primary` | `#1A1410` | Texto sobre gold-gradient
`--secondary-container` | `#384668` | bg `/20` del branded panel izquierdo en auth
`--on-surface` | `#ECEAE3` | Texto principal
`--on-surface-variant` | `#9B9991` | Texto secundario, descriptions
`--outline-variant` / `--ghost-border` | `#2C2C2B` | Bordes de cards, dividers
`--error` | `#FFB4AB` | Banners de error en forms
`--error-container` | `#93000A` | bg `/10` de banners de error
`--status-success` | `#8BC98B` | Password rules checked, reset password success

#### Light (paritario)

Token | Hex | Notas
---|---|---
`--background` | `#F5F2EB` | Cream del pecho del tucán
`--surface` | `#FFFFFF` | Cards
`--primary` | `#A07C20` | Gold más oscuro para contraste sobre bg cream
`--on-primary` | `#FFFFFF` | Texto sobre primary
`--ghost-border` | `rgba(77, 70, 57, 0.12)` | Bordes sutiles

### 2.2 Color hardcoded a eliminar en superficie pública

- ❌ `style={{ borderBottom: "1px solid rgba(79, 70, 51, 0.15)" }}` en LegalHeader (privacy:16, terms:17, libro-reclamaciones:15) → usar `border-outline-variant`
- ❌ `style={{ background: "linear-gradient(135deg, var(--gold-gradient-from)..." }}` inline en LegalHeader → usar `className="gold-gradient"`
- ❌ `text-[#4ade80]` en register password rules → usar `text-status-success`
- ❌ `bg-green-500/10 border-green-500/20 text-green-400` en password reset success → usar tokens de status
- ❌ `bg-black/70` en password reset overlay → `bg-inverse-surface/70` o token de overlay
- ❌ `style={{ border: "1px solid rgba(255,209,101,0.15)" }}` en disclaimer boxes (privacy:212, terms:135) → `border-primary/15`

### 2.3 Gradient gold canónico

Definido en `globals.css` como utility `.gold-gradient`:
```css
.gold-gradient {
  background: linear-gradient(135deg, var(--gold-gradient-from) 0%, var(--gold-gradient-to) 100%);
}
```

Variables:
- Dark: `--gold-gradient-from: #FFD165`, `--gold-gradient-to: #EAB308`
- Light: `--gold-gradient-from: #E8B30E`, `--gold-gradient-to: #C49508`

**Uso obligatorio** en:
- CTA primario "Comenzar gratis" / "Empezar" / "Crear cuenta gratis"
- "MÁS POPULAR" badge en pricing
- Botones de submit en forms de auth
- Botones de páginas de error ("Volver al inicio", "Intentar de nuevo")

---

## 3. Typography (público)

### 3.1 Font families canónicas (igual que app)

```css
--font-display: 'Newsreader', Georgia, serif;     /* via @theme inline */
--font-body: 'Manrope', system-ui, sans-serif;
```

**Cargadas en `globals.css:1`**:
```css
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&family=Manrope:wght@200..800&display=swap');
```

### 3.2 Type scale específica de la superficie pública

Token | Tag visible | Family | Size (sm → lg) | Weight | Uso
---|---|---|---|---|---
`hero-h1` | `<h1>` | Newsreader | 30 / 48 / 60 px (text-3xl/5xl/6xl) | 700 | Hero landing
`page-h1` | `<h1>` | Newsreader | 30 / 36 / 48 px | 700 | H1 caracteristicas/precios/contacto/legal
`section-h2` | `<h2>` | Newsreader | 24 / 32 px (text-2xl/4xl) | 700 | Section titles
`card-h3` | `<h3>` | Newsreader | 20 / 24 px (text-xl/2xl) | 700 | Card titles, feature names
`small-h2` | `<h2>` | Newsreader | 18 / 20 px (text-lg/xl) | 700 | Legal section titles ("1. Identificación...")
`lead` | `<p>` | Manrope | 16 / 18 px (text-base/lg) | 400 | Hero descriptions
`body` | `<p>` | Manrope | 14 / 16 px (text-sm/base) | 400 | Card descriptions, body
`body-tight` | `<p>` | Manrope | 14 px (text-sm) | 400 leading-relaxed | Legal body
`caption` | `<p>` | Manrope | 12 / 13 px (text-xs/sm) | 400 | Disclaimers, helper
`eyebrow` | `<span>` | Manrope | 12 px (text-xs) | 500 uppercase tracking-wider | Section eyebrow pills
`micro` | `<span>` | Manrope | 10 / 11 px | 700 uppercase tracking-[0.14em] | Trust words

### 3.3 Patterns de tipografía pública

**Hero H1 con accent shimmer** (landing):
```tsx
<h1 className="font-headline text-3xl sm:text-5xl lg:text-6xl font-bold text-on-surface leading-[1.1]">
  Tu Asistente Jurídico{" "}
  <span className="shimmer-text">Inteligente</span>
</h1>
```
La palabra clave se envuelve en `.shimmer-text` (definido en globals.css L407-421) — gradient gold animado.

**H1 con accent estático** (precios, caracteristicas, contacto, legal):
```tsx
<h1 className="font-headline text-3xl sm:text-5xl font-bold text-on-surface mb-4">
  Planes simples, <span className="text-primary">sin sorpresas</span>
</h1>
```

**Eyebrow pill** (consistente en todas las páginas marketing):
```tsx
<span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-medium uppercase tracking-wider mb-6">
  Planes
</span>
```

**Section eyebrow** (versión inline sobre H2):
```tsx
<span className="section-eyebrow text-primary mb-4 block">Proceso</span>
<h2 className="font-headline text-2xl sm:text-4xl font-bold text-on-surface">¿Cómo funciona?</h2>
```
Utility `.section-eyebrow`:
```css
.section-eyebrow {
  letter-spacing: 0.22em;
  text-transform: uppercase;
  font-size: 10px;
  font-weight: 800;
}
```

**Páginas legales — H2 dorado**:
```tsx
<h2 className="font-headline text-xl font-bold text-primary mb-3">
  1. Identificación del prestador
</h2>
```

### 3.4 Reemplazos a hacer

- ❌ `font-['Newsreader']` (hardcoded en libro-reclamaciones, terms, privacy) → `font-headline`
- ❌ `font-['Manrope']` → `font-body` (o omitir, ya está en body globalmente)
- ❌ Mezclar `font-headline italic` con weight 200 (auth) y weight 700 (hero) sin sistema → documentar variantes

---

## 4. Spacing & layout (público)

### 4.1 Container max-widths canónicas para zona pública

Page | Max-width | Tailwind | Aplicado en
---|---|---|---
Hero landing | 1280 px | `max-w-7xl` | landing hero, caracteristicas, precios
FAQ y formularios | 768 px | `max-w-3xl` | precios FAQ, contacto, /docs lectura
Páginas legales | 896 px | `max-w-4xl` | terms, privacy
Libro de reclamaciones | 768 px | `max-w-3xl` | libro-reclamaciones
Auth form card | 440-512 px | `max-w-lg` (login) / `max-w-[440px]` (register) | auth/login, auth/register

### 4.2 Padding canónico de secciones públicas

Variant | Mobile | Tablet | Desktop | Uso
---|---|---|---|---
Section padding-y | `py-16` (64 px) | `py-20` (80 px) | `py-24` (96 px) | secciones de marketing
Container padding-x | `px-4` (16 px) | `px-4` (16 px) | `px-8` (32 px) | borde lateral
Card padding | `p-6` (24 px) | `p-7` (28 px) | `p-8` (32 px) | pricing, feature
Auth form padding | `p-6` | `p-8` | `p-10/12` | form card

### 4.3 Header / Footer dimensions

| Elemento | Mobile | Desktop |
|---|---|---|
| `PublicHeader` height | 64 px (`h-16`) | 80 px (`h-20`) |
| `PublicHeader` z-index | 50 (fixed) | 50 (fixed) |
| `PublicHeader` bg | `bg-surface/80 backdrop-blur-md` | mismo |
| `LegalHeader` height | 64 px (`h-16`) | 64 px |
| Main `padding-top` | `pt-16` | `pt-20` (offset por header fixed) |
| `PublicFooter` padding | `py-12` (48 px) | `py-12` |
| Auth left column | hidden | 50% width, min-h-screen |
| Auth right column | full | 50% width |

### 4.4 Breakpoints

Igual que el sistema base (`sm: 640`, `md: 768`, `lg: 1024`, `xl: 1280`, `2xl: 1536`).

**Específico para auth**: `md:flex` (768 px) — debajo de 768 px solo se ve la columna del formulario con un header compacto.

---

## 5. Componentes públicos canónicos

### 5.1 `PublicHeader` (canonical — consolidar `LegalHeader` aquí)

**Spec actual** (`apps/web/src/components/public/PublicHeader.tsx`):

```
┌────────────────────────────────────────────────────────────────┐
│ [🦜 TukiJuris] [Buscar corpus] [Características] [Precios] ... │  h: 64/80 px
│ [Documentación]                            [☀] [Iniciar] [CTA] │  bg: surface/80 backdrop-blur
└────────────────────────────────────────────────────────────────┘
```

**Slots**:
- Brand: logo-icon (48 px) + wordmark "TukiJuris" en `font-headline` weight 700
- Nav (desktop md+): 4 links — Buscar corpus, Características, Precios, Documentación
- Right: theme toggle (Sun/Moon 16 px ghost), "Iniciar Sesión" (text link), "Comenzar Gratis" (gold-gradient CTA)
- Mobile: hamburger (Menu icon) → drawer slide-down con mismos links + auth CTAs

**Para v3 (canónico)**:
- Aceptar prop `variant: "marketing" | "legal"` 
- `legal` oculta los 4 nav links pero mantiene CTAs y theme toggle
- Reemplazar el actual `LegalHeader` custom de `/privacy`, `/terms`, `/libro-reclamaciones` por `<PublicHeader variant="legal" />`

### 5.2 `PublicFooter` (canonical — consolidar `LegalFooter` aquí)

**Layout actual** (3 cols en `sm+`):

```
┌────────────────────────────────────────────────────────────────┐
│ 🦜 TukiJuris        TÉRMINOS · PRIVACIDAD ·       soporte@...  │
│ Plataforma jurídica  LIBRO RECLAMACIONES ·         📓 Libro    │
│ TukiTuki Solutions   DOCS · STATUS · CONTACTO                  │
│ RUC 20613614509                                                │
├────────────────────────────────────────────────────────────────┤
│ © 2026 TukiJuris...                  Respuestas orientativas... │
└────────────────────────────────────────────────────────────────┘
```

**Refinamiento v3**:
- ❌ Eliminar emoji `📓` (rompe código editorial) → usar icono Lucide `BookOpen` 12 px
- Aceptar prop `variant: "full" | "legal"` 
- `legal` muestra solo el bottom row (sin grid de 3 cols)

### 5.3 `AuthShell` (canonical — consolidar `/auth/*`)

**Patrón dual-column**:

```
┌──────────────────────────┬──────────────────────────────────┐
│                          │                                  │
│   🦜  (mascota)          │   [Volver al inicio]             │
│   TukiJuris              │                                  │
│   ─ ABOGADOS ─           │   Iniciar Sesión                 │
│                          │   INGRESA A TU CUENTA            │
│   ─────                  │                                  │
│                          │   ┌──────────────────┐           │
│   Asistente Legal IA     │   │ CORREO            │           │
│   Consultas inteligentes │   │ [             ]   │           │
│                          │   └──────────────────┘           │
│                          │   ┌──────────────────┐           │
│   PRECISIÓN · AUTORIDAD  │   │ CONTRASEÑA      👁│           │
│   · EFICIENCIA           │   │ [             ]   │           │
│                          │   └──────────────────┘           │
│                          │                                  │
│                          │   [¿Olvidaste tu contraseña?]    │
│                          │                                  │
│                          │   [    INICIAR SESIÓN    ]       │
│                          │                                  │
│                          │   ─── o continuar con ───         │
│                          │   [Google] [Microsoft]           │
│                          │                                  │
│                          │   ¿No tienes cuenta? Regístrate  │
└──────────────────────────┴──────────────────────────────────┘
```

**Spec**:
- Container: `flex flex-col md:flex-row min-h-screen bg-background`
- Left col (desktop only): `md:w-1/2 min-h-screen flex-col justify-center items-center px-16 relative overflow-hidden bg-secondary-container/20`
  - 2 radial glows (top-right + bottom-left) `bg-primary/5` y `bg-secondary/5` con `blur-3xl`
  - Mascota `tukan.png` 40-220 px según viewport
  - Wordmark + tagline italic + trust words divider
- Right col: `w-full md:w-1/2 bg-background min-h-screen flex flex-col justify-center px-4 md:px-16`
  - Inner: `max-w-lg mx-auto`
  - Form card: `panel-raised rounded-xl p-6 sm:p-8 md:p-12`

**Variantes a soportar**:
- `variant="login"` — form actual + reset modal
- `variant="register"` — form actual con password rules y terms checkbox
- `variant="reset"` — solo email field para enviar magic link
- `variant="callback"` — full-screen loader sin shell dual (OAuth return)
- `variant="rate-limited"` — centered card sobre fondo background, mascot pequeño + mensaje + countdown

### 5.4 Botones públicos canónicos

| Variant | Class | Uso |
|---|---|---|
| `cta-primary-lg` | `inline-flex items-center justify-center gap-2 font-bold rounded-xl h-12 px-8 transition-all hover:opacity-90 text-on-primary gold-gradient hover:shadow-xl hover:shadow-primary/25 hover:scale-[1.02]` | Hero CTA, final CTA |
| `cta-primary-md` | `inline-flex items-center justify-center rounded-xl h-11 px-6 transition-all hover:opacity-90 text-sm font-bold text-on-primary gold-gradient` | Pricing card CTA |
| `cta-secondary-lg` | `inline-flex items-center justify-center gap-2 rounded-xl h-12 px-6 transition-all text-on-surface hover:text-primary border border-ghost-border hover:border-primary/30 bg-surface-container-high/20 hover:bg-surface-container-high/40 hover:scale-[1.01]` | "Explorar corpus", "Ver Precios" |
| `cta-tertiary` | `inline-flex items-center gap-2 text-primary font-medium text-sm hover:gap-3 transition-all` | "Ver todas las características →" |
| `cta-submit-form` | `w-full h-12 text-on-primary font-bold uppercase tracking-widest text-xs rounded-lg flex items-center justify-center gap-2 transition-all hover:opacity-90 disabled:opacity-50 gold-gradient hover:shadow-lg hover:shadow-primary/20` | Submit en auth forms |
| `cta-header` | `text-sm font-bold rounded-lg h-10 px-5 transition-opacity hover:opacity-90 whitespace-nowrap text-on-primary gold-gradient` | "Comenzar Gratis" en PublicHeader |

**Animaciones obligatorias en CTAs primarios**:
- `hover:scale-[1.02]`
- `hover:shadow-xl hover:shadow-primary/25` (o `/20` en versiones medianas)
- Hero CTAs adicionalmente: `animate-pulse-glow`

### 5.5 Pricing card (`/precios` + landing teaser)

**Standard card**:
```tsx
<div className="bg-surface-container-low hover:bg-surface-container rounded-xl p-6 sm:p-8 flex flex-col gap-5 border border-ghost-border card-lift gradient-border">
  <div>
    <span className="text-on-surface/60 bg-on-surface/10 rounded-lg text-xs px-2 py-0.5 font-medium uppercase tracking-widest">Gratis</span>
    <h3 className="font-headline text-xl sm:text-2xl font-bold text-on-surface mt-3 mb-1">Gratuito</h3>
    <div className="flex items-baseline gap-1">
      <span className="font-headline text-3xl sm:text-4xl font-bold text-on-surface">S/ 0</span>
      <span className="text-on-surface/60 text-sm">/mes</span>
    </div>
  </div>
  <ul>...features con CheckCircle2 + text-on-surface-variant...</ul>
  <CTA />
</div>
```

**Featured card** (Profesional):
- Border: `border-2 border-primary shadow-xl shadow-primary/10`
- Scale: `md:scale-[1.03]`
- Badge absoluto top center: `<span className="text-on-primary text-xs font-bold px-3 py-1 rounded-lg uppercase tracking-widest gold-gradient shadow-lg shadow-primary/20">MÁS POPULAR</span>`
- Eyebrow chip distinta: `bg-primary/10 text-primary` (vs `bg-on-surface/10 text-on-surface/60`)
- Card hover lift via `.card-lift` utility (definir en globals.css si no existe — actualmente referenciado pero no aparece en globals.css que leí, **verificar**)

### 5.6 Feature card (`/caracteristicas`)

```tsx
<div className="group bg-surface-container-low hover:bg-surface-container rounded-xl p-6 sm:p-8 border border-ghost-border card-lift gradient-border cursor-default">
  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-5 icon-glow group-hover:bg-primary/20 group-hover:scale-110 transition-all">
    <Icon className="w-5 h-5 text-primary group-hover:scale-110 transition-transform" />
  </div>
  <h3 className="font-headline font-semibold text-on-surface text-base sm:text-lg mb-2 group-hover:text-primary transition-colors">{title}</h3>
  <p className="text-sm text-on-surface-variant leading-relaxed">{desc}</p>
</div>
```

### 5.7 Showcase feature (alternating image/text)

```
┌──────────────────────────────────────────────────────────────┐
│  ┌────────────────────┐    [icon-glow gold]                  │
│  │                    │    29 ÁREAS DEL DERECHO              │
│  │   screenshot       │    PERUANO                           │
│  │                    │    Cobertura del ordenamiento...     │
│  │                    │    [Civil][Penal][Laboral][+25 más]  │
│  └────────────────────┘                                      │
└──────────────────────────────────────────────────────────────┘
```

Grid: `grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center`. Alternar lado vía `isReverse && "lg:direction-rtl"` + `lg:order-2`/`lg:order-1`.

### 5.8 FAQ accordion (`/precios`)

```tsx
<div className="border-b border-ghost-border">
  <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between py-5 text-left gap-4 group">
    <span className="font-headline text-base sm:text-lg font-semibold text-on-surface group-hover:text-primary transition-colors">{q}</span>
    <ChevronDown className={cn("w-5 h-5 text-on-surface-variant shrink-0 transition-transform duration-300", open && "rotate-180 text-primary")} />
  </button>
  <div className={cn("overflow-hidden transition-all duration-300 ease-in-out", open ? "max-h-48 opacity-100 pb-5" : "max-h-0 opacity-0")}>
    <p className="text-sm text-on-surface-variant leading-relaxed pr-8">{a}</p>
  </div>
</div>
```

### 5.9 Contact channel card (`/contacto`)

```tsx
<div className="rounded-xl border border-ghost-border bg-surface-container-low p-5 flex flex-col gap-2">
  <span className="text-primary text-xs font-bold uppercase tracking-widest">{label}</span>
  <a href={`mailto:${email}`} className="text-on-surface font-medium hover:text-primary transition-colors text-sm break-all">
    {email}
  </a>
  <p className="text-on-surface-variant text-xs leading-relaxed">{description}</p>
</div>
```

Grid: `grid-cols-1 sm:grid-cols-2 gap-4`.

### 5.10 Stats counter animado (landing hero)

Componente: `useCounter(endValue, duration=1800)` con easeOutCubic + IntersectionObserver. Solo dispara una vez (al entrar en viewport).

Spec visual:
```tsx
<span ref={counter.ref} className="font-headline text-2xl sm:text-3xl font-bold text-primary tabular-nums">
  {counter.count.toLocaleString()}+
</span>
<span className="text-xs text-on-surface/50 uppercase tracking-widest">fragmentos legales</span>
```

`tabular-nums` es **obligatorio** para evitar layout shift mientras el contador anima.

### 5.11 Reveal wrapper (consistente entre landing/caracteristicas/precios)

Hook duplicado actualmente en 3 archivos — debe extraerse a `@/lib/hooks/useReveal.ts`:

```tsx
export function useReveal<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add("visible");
          observer.unobserve(el);
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return ref;
}
```

CSS asociado (verificar que esté en `globals.css`):
```css
.reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 700ms cubic-bezier(0.22, 1, 0.36, 1), transform 700ms cubic-bezier(0.22, 1, 0.36, 1);
}
.reveal.visible {
  opacity: 1;
  transform: translateY(0);
}
```

### 5.12 Input + label canónico para forms públicos

```tsx
<label htmlFor="id" className="block text-xs uppercase tracking-widest mb-2 text-on-surface-variant/60">
  Correo electrónico
</label>
<input
  id="id"
  type="email"
  className="w-full h-12 rounded-lg px-4 text-on-surface placeholder-on-surface/30 transition-all duration-200 control-surface focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20"
  placeholder="tu@email.com"
  required
  autoComplete="email"
/>
```

`.control-surface` (definida en globals.css L251-264):
- `border: 1px solid color-mix(in srgb, var(--outline-variant) 58%, transparent)`
- `background: color-mix(in srgb, var(--surface) 90%, transparent)`
- Hover border → `color-mix(primary 28%, outline-variant)`

Variante con icono (register):
```tsx
<div className="relative">
  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none text-on-surface-variant/40" />
  <input className="pl-10 ..." />
</div>
```

### 5.13 SSO buttons (Google + Microsoft)

Grid `grid-cols-1 sm:grid-cols-2 gap-3`. Cada botón:
- `h-12 rounded-lg flex items-center justify-center gap-2.5 text-sm control-surface hover:border-primary/30 text-on-surface-variant transition-all`
- SVG inline 16 px con colores oficiales (NO usar logos vectoriales tipo Lucide — Google y Microsoft son brand)
- Estado loading: `<Loader2 className="w-4 h-4 animate-spin" />`

### 5.14 Password rules indicator (register)

```tsx
{password.length > 0 && (
  <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5">
    {PASSWORD_RULES.map((rule) => {
      const ok = rule.test(password);
      return (
        <div key={rule.label} className="flex items-center gap-2">
          {ok ? <CheckCircle2 className="w-3.5 h-3.5 text-status-success" /> : <Circle className="w-3.5 h-3.5 text-on-surface/20" />}
          <span className={`text-[11px] uppercase tracking-wider ${ok ? "text-status-success" : "text-on-surface-variant/60"}`}>{rule.label}</span>
        </div>
      );
    })}
  </div>
)}
```

**Rules canónicas**:
- Mínimo 8 caracteres
- Una mayúscula
- Una minúscula  
- Un número

### 5.15 Reset password modal (overlay)

- Backdrop: `fixed inset-0 bg-inverse-surface/70 backdrop-blur-sm flex items-center justify-center z-50 px-4`
- Card: `w-full max-w-md rounded-xl p-8 relative panel-raised`
- Close button: `absolute top-4 right-4 p-1 rounded-lg` con `X` icon ghost
- Headline gold + divider gold 1 px x 64 px
- Form: igual al input canónico
- Success state: green box (`bg-status-success/10 border border-status-success/20`)
- Error state: error box (`bg-error-container/10 border border-error/20`)

### 5.16 Error banner inline (auth forms)

```tsx
{error && (
  <div className="flex items-start gap-3 bg-error-container/10 border border-error/20 rounded-lg p-4 text-error text-sm mb-6">
    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
    <span>{error}</span>
  </div>
)}
```

### 5.17 Disclaimer box (legal + landing hero)

```tsx
<div className="p-4 rounded-lg bg-primary/5 border border-primary/15">
  <p className="text-primary font-medium text-sm">
    TukiJuris NO constituye un estudio de abogados...
  </p>
  <p className="text-on-surface-variant text-xs mt-1">
    Las consultas... NO están protegidas por el secreto profesional...
  </p>
</div>
```

### 5.18 Trust bar (landing)

```tsx
<section className="py-6 sm:py-8 px-4 lg:px-8 border-y border-ghost-border bg-surface-container-low/20 overflow-hidden">
  <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-center gap-4 sm:gap-8">
    {AREAS.map((area, i) => (
      <span key={area} className="flex items-center gap-2 text-xs uppercase tracking-[0.15em] text-on-surface/30 font-medium" style={{ animationDelay: `${i * 100}ms` }}>
        <span className="w-1.5 h-1.5 rounded-full bg-primary/30" />
        {area}
      </span>
    ))}
  </div>
</section>
```

### 5.19 Iconography pública

Library: `lucide-react`. Stroke-width: 1.5–2 (default).

Iconos críticos por feature:
- `Scale` — balanza / áreas legales
- `Sparkles` — eyebrow "IA Jurídica"
- `ArrowRight` — CTAs
- `ChevronDown` — FAQ accordion + select
- `CheckCircle2` — feature checks, password rules ok
- `Circle` — password rules pending
- `AlertCircle` — error banner
- `AlertTriangle` — error.tsx page
- `Search` / `Mail` / `Lock` / `User` — input icons
- `Eye` / `EyeOff` — password show/hide
- `Loader2` — spinners (siempre con `animate-spin`)
- `Sun` / `Moon` — theme toggle
- `Menu` / `X` — mobile drawer
- `ArrowLeft` — "Volver al inicio" links
- `Shield` / `BarChart3` / `Users` / `Key` — feature grid
- `BookOpen` — corpus, libro de reclamaciones (reemplaza emoji 📓)
- `Home` / `RotateCcw` — botones de error page

**SVG decorativos custom**: `ScalesSvg`, `GavelSvg`, `ParagraphSvg` (definidos inline en landing) — mantener como adorno editorial flotante con `animate-float`.

---

## 6. Page templates — anatomía pública

### 6.1 `/` (root)

Layout: ninguno. Server component que hace `redirect('/analizar')` o `redirect('/landing')` según auth.

**Implementación actual**: `apps/web/src/app/page.tsx` siempre redirige a `/analizar`. Si no hay sesión, el middleware redirige luego a `/landing`. **Verificar comportamiento**.

### 6.2 `/landing` — Home marketing

**Estructura canónica** (orden de secciones):

1. **Hero** — h-90vh, 2 cols (text + mascota)
   - Ambient glows `animate-pulse-glow` (top-left + center-right)
   - Floating SVG decorativos (`ScalesSvg`, `GavelSvg`, `ParagraphSvg`) escondidos en mobile (`hidden lg:block`)
   - Dot grid background (`dot-grid` utility)
   - Badge eyebrow + H1 con shimmer + lead + 2 CTAs + stats animados (3 counters)
   - Mascota con ring rotativo + 2 mini badges flotantes ("29 Áreas", "Citas verificables")

2. **Trust bar** — slim, `py-6/8`, lista de 5-6 áreas + "+ 24 más"

3. **Features teaser** — 1 showcase block + link a `/caracteristicas`

4. **How it works** — 3 pasos con screenshot alternando lados

5. **Pricing teaser** — 3 cards mini (price + name only) + link a `/precios`

6. **Final CTA** — Container glow + mascota + H2 con shimmer + 1 CTA primario

7. **Footer** (vía PublicLayout)

### 6.3 `/caracteristicas` — Features showcase

1. **Hero** — eyebrow "Capacidades" + H1 + lead, centered
2. **Showcase features** — 3 bloques alternados (image/text), badges chips por feature, BYOK card destaca plan Empresarial
3. **Grid features** — 3 cols con icon + title + desc, hover lift
4. **Extra features checklist** — 8 items en grid 4 cols con CheckCircle2
5. **CTA** — H2 + 2 CTAs (registro + ver precios)

### 6.4 `/precios` — Pricing + FAQ

1. **Hero** — eyebrow "Planes" + H1 con "sin sorpresas" en primary + lead que menciona BYOK como exclusivo Empresarial + disclaimer
2. **3 pricing cards** — Gratuito (S/0), Profesional (S/70, featured), Estudio (Contactar)
3. **FAQ accordion** — 7 items
4. **CTA final** — container glow + mascot + H2 + CTA

### 6.5 `/buscar` (anon mode)

**Variant pública** del corpus browser:
- Hero: badge "BUSCADOR PÚBLICO · SIN IA" + H1 "Corpus jurídico del Perú" + stats live (1638 docs · 2001 fragmentos)
- Search bar con icon Search + clear button
- Area filter chips con conteos por área
- Cards de resultados con título, área badge, snippet, score BM25, document_number

Layout dinámico: `Layout = user ? AppLayout : PublicLayout`. En anon mode usa PublicLayout.

### 6.6 `/contacto`

1. **Hero compacto** — eyebrow + H1 "¿En qué podemos ayudarte?" + lead con horario Lima
2. **Channel grid** — 5 channel cards (soporte, ventas, privacidad, legal, reclamos)
3. **Datos prestador box** — Card con razón social + link a Libro de Reclamaciones

### 6.7 `/docs` y `/guia`

**Estado actual**: existen pero contenido vacío o placeholder. Para producción:

- `/docs` — Sidebar TOC + content area con MDX. API reference. Width: 1024 max para legibilidad.
- `/guia` — Wizard-like, sin sidebar, scroll vertical de tutoriales en secciones colapsables.

**Layout**: `PublicLayout` con `mode="marketing"`.

### 6.8 `/privacy`, `/terms` — Páginas legales

**Anatomía**:
```
┌─ LegalHeader (a canonizar como PublicHeader variant="legal") ─┐

┌─── max-w-4xl px-4 lg:px-8 pt-28 pb-20 ────────────────────────┐
│                                                                │
│  PRIVACIDAD (eyebrow primary)                                  │
│  Política de Privacidad        (H1 Newsreader 4xl)             │
│  Última actualización: 31 mayo 2026     (caption)              │
│  ────────────────                                              │
│                                                                │
│  Intro paragraph (body-tight)                                  │
│                                                                │
│  1. Datos que recopilamos      (H2 Newsreader xl text-primary) │
│     Subsection 1.1 ...         (H3 text-sm font-semibold)      │
│     ul list-disc...            (body-tight ul)                 │
│                                                                │
│  2. ...                                                        │
│                                                                │
│  [Disclaimer box bg-primary/5 border-primary/15]               │
│                                                                │
│  N. Contacto                                                   │
│                                                                │
└────────────────────────────────────────────────────────────────┘

┌─ LegalFooter (a canonizar como PublicFooter variant="legal") ──┐
```

**Secciones canónicas para v3**:
1. Identificación del prestador
2. Aceptación / Objeto
3. Descripción del servicio
4. Naturaleza (disclaimer IA — orientativa)
5. BYOK (solo plan Empresarial)
6. Registro y cuentas
7. Planes, pagos y cancelación
8. Uso aceptable
9. Propiedad intelectual
10. Disponibilidad
11. Limitación de responsabilidad
12. Libro de Reclamaciones (link)
13. Legislación aplicable (Perú)
14. Contacto

### 6.9 `/libro-reclamaciones`

Requerimiento legal Ley 29571 + D.S. 011-2011-PCM.

**Bloques obligatorios**:
- Identificación del proveedor (TukiTuki Solutions SAC + RUC + servicio)
- ¿Cómo presentar tu reclamo? (email + datos requeridos: nombre, DNI, contacto, tipo Reclamo/Queja, hechos, pretensión)
- Plazo de respuesta (30 días calendario art. 24 Código del Consumidor)
- Vías alternas (INDECOPI)
- Nota validez legal (art. 8 D.S. 011-2011-PCM)

### 6.10 `/auth/login`

Spec en §5.3. Variante específica:
- Form fields: email + password
- Link "¿Olvidaste tu contraseña?" → abre reset modal
- Submit text: "Iniciar Sesión" / "Ingresando..."
- SSO buttons Google + Microsoft
- Link inferior: "¿No tienes cuenta? Regístrate"
- Modal overlay para reset

### 6.11 `/auth/register`

Spec en §5.3. Variante específica:
- Form fields: nombre + email + password (con rules indicator)
- Terms checkbox custom con SVG check animado
- Disable submit hasta cumplir: email + password válida + terms aceptados
- Submit text: "Crear Cuenta Gratis" / "Creando cuenta..."
- SSO buttons Google + Microsoft
- Link inferior: "¿Ya tenés cuenta? Iniciar sesión"

Left column de register tiene CTA aspiracional:
- H1 "Únete a la plataforma jurídica del futuro" (Newsreader 4xl/5xl)
- Stats row: "Gratis para empezar · Sin tarjeta · 100% seguro"
- Trust words divider

### 6.12 `/auth/reset-password`

(Página separada de `/auth/login` modal — para recibir el token email)

Spec sugerida:
- Card centered single column (no dual-column)
- H1 "Restablecer contraseña"
- 2 fields: nueva contraseña + confirmar
- Password rules indicator (igual que register)
- Submit "Cambiar contraseña"
- Success: redirect a login con toast verde

### 6.13 `/auth/callback`

Full-screen loader con mascota + spinner gold + texto "Iniciando sesión con Google..." / "...con Microsoft...".

Layout: `min-h-screen flex items-center justify-center bg-background`.

### 6.14 `/auth/rate-limited`

Centered card sobre fondo:
- Icon `AlertTriangle` 32 px tertiary
- H1 "Demasiados intentos"
- Body explicando el plazo (e.g., "Espera 60 segundos antes de intentar nuevamente")
- Countdown numérico tabular
- CTA "Volver al inicio"

### 6.15 `not-found.tsx` (404)

```
┌────────────────────────┐
│   [📦 Search icon]      │   (en bg primary/10 rounded-2xl)
│                        │
│   404                   │   (Newsreader 6xl primary bold)
│   Página no encontrada  │   (Newsreader xl on-surface)
│                        │
│   La página que buscas │
│   no existe...         │   (body-sm on-surface-variant)
│                        │
│  [🏠 Volver] [Ver docs]│   (gold-gradient + ghost-border)
└────────────────────────┘
```

### 6.16 `error.tsx` (500)

```
┌────────────────────────┐
│  [⚠ AlertTriangle]     │   (en bg tertiary/10 rounded-2xl)
│                        │
│  Algo salió mal         │   (Newsreader 2xl)
│                        │
│  Ocurrió un error...   │
│  contactanos a         │
│  soporte@...           │
│                        │
│  Ref: <error.digest>   │   (mono caption muted — útil para soporte)
│                        │
│  [🔄 Intentar] [🏠 Inicio]│
└────────────────────────┘
```

---

## 7. Microinteracciones en zona pública

### 7.1 Animaciones ya disponibles (en `globals.css`)

| Animation | Duration | Loop | Uso |
|---|---|---|---|
| `fadeInUp` | 700 ms | once | Hero badges, stats, CTAs (con stagger `delay-100` a `delay-400`) |
| `fadeInRight` | 700 ms | once | Hero mascota |
| `pulseGlow` | 4 s | infinite | Hero ambient orbs, CTA glow, final CTA glow |
| `float` | 6 s | infinite | SVGs decorativos, mini badges flotantes |
| `floatSlow` | 8 s | infinite | Mascota |
| `spinSlow` | 20 s | infinite | Rotating ring de mascota |
| `shimmer` | 4 s | infinite | `.shimmer-text` en hero H1 |
| `reveal` (via `.reveal`/`.visible`) | 700 ms | once on scroll | Todas las secciones reveal con IntersectionObserver |

### 7.2 Hover canónico de CTAs

```css
.cta-primary {
  transition: all 200ms;
}
.cta-primary:hover {
  opacity: 0.9;
  transform: scale(1.02);
  box-shadow: 0 25px 50px -12px rgba(201, 168, 76, 0.25);
}
```

### 7.3 `card-lift` utility (verificar definición)

Pricing y feature cards la usan pero no se ve definida en `globals.css`. Debe ser:
```css
.card-lift {
  transition: transform 200ms, box-shadow 200ms;
}
.card-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px var(--shadow);
}
```

### 7.4 Reduced motion

Respetar `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  .reveal { opacity: 1 !important; transform: none !important; }
}
```

---

## 8. Accessibility (público)

### 8.1 Contraste de tokens críticos

Combinación | Ratio | Verdict
---|---|---
`--primary` (#C9A84C) sobre `--background` (#191918) | 6.9:1 | ✅ AA
`--on-surface` (#ECEAE3) sobre `--background` | 14.3:1 | ✅ AAA
`--on-surface-variant` (#9B9991) sobre `--background` | 5.8:1 | ✅ AA
`--on-primary` (#1A1410) sobre `--primary` (#C9A84C) | 9.7:1 | ✅ AAA
`--primary` sobre `--surface` (#1F1F1E) | 6.2:1 | ✅ AA
`text-on-surface/60` sobre `--surface-container-low` | ~3.2:1 | ⚠️ marginal — solo para texto ≥18px
`text-on-surface/40` (placeholders, hints) | ~2.0:1 | ❌ no AA — pero usado solo en hints decorativos, fuera de información crítica

### 8.2 Forms públicos

- `<label htmlFor>` obligatorio en login + register
- `aria-label` en password toggle button
- `aria-label="Formulario de inicio de sesión"` en `<form>`
- `aria-live="polite"` para error banner cuando aparece
- `required` + `autoComplete` (email, current-password, new-password, name) en todos los inputs
- Tab order natural: top → bottom, izquierda → derecha
- Focus visible global ya está cubierto por `*:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }`

### 8.3 Skip links

Cada layout público debe tener un skip link visible-on-focus:
```tsx
<a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:bg-surface focus:text-on-surface focus:px-4 focus:py-2 focus:rounded-lg focus:z-[60]">
  Saltar al contenido
</a>
```

### 8.4 Reduced motion respect

Ya cubierto en §7.4. Verificar que `.reveal` no genere "salto" cuando se respeta reduced motion.

### 8.5 Mobile tap targets

- CTAs h-12 = 48 px ✅
- Theme toggle `p-2` = ~32 px ⚠️ — incrementar a `p-3` para alcanzar 44 px mínimo WCAG 2.5.5
- Mobile hamburger `p-2` = ~32 px ⚠️ — mismo
- Footer links `gap-4` sin padding visible — pueden ser difíciles de tocar en mobile, **incrementar a `py-1`**

### 8.6 Lang attribute

`<html lang="es">` ya configurado en `layout.tsx:65`. Términos en otro idioma (e.g., "JWT", "Fernet", "AES") deberían envolverse en `<span lang="en">` por estricto WCAG, aunque en práctica suelen pasarse sin marcar.

---

## 9. SEO + OpenGraph + Sitemap (público)

### 9.1 Páginas que indexar

Path | Indexar | Notas
---|---|---
`/landing` | ✅ | Home — top priority
`/caracteristicas` | ✅ |
`/precios` | ✅ |
`/buscar` | ✅ | Página de búsqueda — alta autoridad SEO
`/contacto` | ✅ |
`/guia` | ✅ |
`/docs` | ✅ | Cada doc como sub-route
`/privacy` | ✅ | Legal
`/terms` | ✅ | Legal
`/libro-reclamaciones` | ✅ | Legal
`/auth/login` | ⚠️ noindex | No queremos indexar logins
`/auth/register` | ⚠️ noindex | Idem
`/auth/reset-password` | ❌ noindex | Token URL
`/auth/callback` | ❌ noindex | OAuth handshake
`/auth/rate-limited` | ❌ noindex |
`/compartido/*` | ⚠️ noindex | Links personales
`/status` | ❌ noindex |

### 9.2 Metadata por página

Cada page debe exportar `metadata` con `title`, `description`, `keywords`, OpenGraph:

```ts
export const metadata: Metadata = {
  title: "Página | TukiJuris",
  description: "Descripción de 150-160 caracteres con keywords + value prop + brand.",
  openGraph: {
    title: "Página — TukiJuris",
    description: "OG description (puede ser distinta).",
    images: [{ url: "/og/<page>.png", width: 1200, height: 630 }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Página — TukiJuris",
    images: ["/og/<page>.png"],
  },
};
```

**Crear assets OG por página**:
- `/og/landing.png` — hero mascota + tagline
- `/og/precios.png` — 3 cards
- `/og/caracteristicas.png` — feature grid
- `/og/buscar.png` — search hero
- `/og/legal.png` — fallback para terms/privacy/libro-reclamaciones

Tamaño: 1200×630 px, formato AVIF + PNG fallback.

### 9.3 Schema.org JSON-LD

Implementar en `landing` (Organization), `precios` (Product), `caracteristicas` (Article).

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "TukiJuris",
  "url": "https://tukijuris.com.pe",
  "logo": "https://tukijuris.com.pe/brand/logo-full.png",
  "sameAs": ["https://...linkedin..."],
  "founder": "TukiTuki Solutions SAC",
  "areaServed": "PE",
  "knowsLanguage": "es-PE"
}
```

FAQPage schema en `/precios` (auto-generable desde el array `FAQ_ITEMS`).

### 9.4 Sitemap

`apps/web/src/app/sitemap.ts` ya existe. Verificar que incluya:
- `/landing`, `/caracteristicas`, `/precios`, `/buscar`, `/contacto`, `/guia`, `/docs`
- `/privacy`, `/terms`, `/libro-reclamaciones`
- Excluir `/auth/*`, `/compartido/*`, `/status`

### 9.5 Robots

`apps/web/src/app/robots.ts` ya existe. Verificar:
- `Allow: /landing`, `/caracteristicas`, `/precios`, `/buscar`, `/contacto`, `/guia`, `/docs`, `/privacy`, `/terms`, `/libro-reclamaciones`
- `Disallow: /admin`, `/auth`, `/analizar`, `/historial`, `/marcadores`, `/configuracion`, `/billing`, `/organizacion`, `/analytics`, `/onboarding`, `/notificaciones`

---

## 10. Production checklist (zona pública)

### 10.1 Performance budgets — pública

Métrica | Target | Página crítica
---|---|---
LCP | < 2.0 s | landing (mascota es candidato 1)
INP | < 200 ms | precios (FAQ accordion)
CLS | < 0.05 | landing (contadores con `tabular-nums` ✅ ya implementado)
TTFB | < 600 ms | todas las SSR

**Optimizaciones específicas**:
- Convertir `tukan.png` (probablemente 300+ kb) a AVIF con responsive `sizes` + `priority`
- Cargar Newsreader + Manrope con `display=swap` ✅
- Considerar `font-display: optional` para Newsreader en > 1MB compressed
- `/landing/feature-*.png` lazy load (excepto la primera visible)
- Eliminar `console.error` en `error.tsx` antes de producción (usar Sentry)

### 10.2 Migration debt (zona pública)

Items urgentes para consolidar:

- [ ] **Eliminar `LegalHeader` y `LegalFooter` duplicados** en `/privacy`, `/terms`, `/libro-reclamaciones` → reemplazar con `<PublicLayout variant="legal">`. (1 día)
- [ ] **Extraer `useReveal` hook** a `@/lib/hooks/useReveal.ts` — hoy duplicado en landing/caracteristicas/precios. (30 min)
- [ ] **Extraer `Reveal` component** a `@/components/ui/Reveal.tsx`. (15 min)
- [ ] **Definir `.card-lift` utility** en `globals.css` (usado en 3 archivos sin definición visible). (10 min)
- [ ] **Definir `.gradient-border` utility** si falta (gradient border hover de pricing cards).
- [ ] **Eliminar `font-['Newsreader']` y `font-['Manrope']` hardcoded** en libro-reclamaciones/terms/privacy → `font-headline` / `font-body`. (10 min)
- [ ] **Eliminar emoji 📓** en PublicFooter:69 y libro-reclamaciones → icono `BookOpen` 12 px. (5 min)
- [ ] **Reemplazar hex hardcoded** `text-[#4ade80]`, `bg-green-500/10` por tokens `text-status-success`, `bg-status-success/10`. (15 min)
- [ ] **Sincronizar el "Comenzar gratis" CTA** entre PublicHeader y LegalHeader (libro-reclamaciones no lo tiene, terms/privacy sí). Decisión: incluir SIEMPRE en zona pública. (5 min)
- [ ] **Aumentar tap targets de theme toggle y mobile hamburger** a 44 px mínimo. (5 min)
- [ ] **Crear `Status` page real** (`/status`) con health endpoint del backend (db/redis/embedding coverage). Hoy `/status` está PUBLIC_PATHS pero la página está vacía o desactualizada.
- [ ] **Implementar `/docs` y `/guia` con contenido real** — hoy son placeholders.
- [ ] **Crear OG images** por página (1200×630 AVIF + PNG).
- [ ] **Auditar `metadata` export** en cada page pública — varias usan default de `layout.tsx` cuando deberían tener título específico.
- [ ] **Verificar `sitemap.ts` y `robots.ts`** contra esta tabla canónica.
- [ ] **Disclaimer IA en `/buscar`** — agregar nota al pie del hero "Las respuestas de TukiJuris son orientativas..." (consistencia con landing).
- [ ] **Test Lighthouse mobile** específicamente sobre landing — el `tukan.png` con `priority` puede estar comiendo LCP.

### 10.3 Testing checklist público

- [ ] Lighthouse desktop ≥ 95 / 95 / 95 / 95 (Perf/A11y/BP/SEO) en `/landing`, `/precios`, `/caracteristicas`
- [ ] Lighthouse mobile ≥ 85 / 95 / 95 / 95 en mismas páginas
- [ ] axe DevTools sin violaciones en `/auth/login` + `/auth/register`
- [ ] Manual con VoiceOver: registro completo end-to-end
- [ ] Manual con teclado: tab por todos los CTAs del landing
- [ ] Manual mobile: iPhone SE 375 px width — sidebar drawer + auth dual collapse + FAQ accordion
- [ ] Manual dark + light: hero, pricing, legal page paridad
- [ ] Manual SSO: Google + Microsoft round-trip + returnTo respetado
- [ ] Manual password reset: email → token → nueva contraseña → login
- [ ] Visual regression: Playwright sobre landing, precios, caracteristicas, contacto, terms

---

## 11. Appendix

### 11.1 File map (zona pública)

```
apps/web/src/app/
  page.tsx                          ← Redirect a /analizar o /landing
  layout.tsx                        ← Root con ThemeProvider, AuthProvider, Toaster, CookieBanner
  globals.css                       ← TOKENS canónicos (consolidar post-migración)
  not-found.tsx                     ← 404
  error.tsx                         ← 500 / runtime
  robots.ts                         ← SEO
  sitemap.ts                        ← SEO
  landing/page.tsx                  ← Home marketing
  caracteristicas/page.tsx          ← Features showcase
  precios/page.tsx                  ← Pricing + FAQ
  buscar/page.tsx                   ← Corpus público (también auth)
  contacto/page.tsx                 ← Canales
  guia/page.tsx                     ← TODO contenido real
  docs/page.tsx                     ← TODO contenido real
  compartido/                       ← Share links
  status/page.tsx                   ← TODO real health
  privacy/page.tsx                  ← Legal (LegalHeader propio → migrar)
  terms/page.tsx                    ← Legal (LegalHeader propio → migrar)
  libro-reclamaciones/page.tsx      ← Legal PE (LegalHeader propio → migrar)
  auth/
    login/page.tsx                  ← Dual-column propio
    register/page.tsx               ← Dual-column propio
    reset-password/page.tsx         ← Single card
    callback/page.tsx               ← Full-screen loader
    rate-limited/page.tsx           ← Centered card

apps/web/src/components/
  ThemeProvider.tsx
  ThemeToggle.tsx
  CookieBanner.tsx
  BFCacheGuard.tsx
  public/
    PublicLayout.tsx                ← Header + Footer wrapper
    PublicHeader.tsx                ← Fixed top, nav, theme toggle, auth CTAs
    PublicFooter.tsx                ← 3-col grid + bottom row

apps/web/src/lib/
  constants.ts                      ← PUBLIC_PATHS, ROUTE_AFTER_LOGIN, AUTH_BOUNCE
  auth/
    AuthContext.tsx
    redirects.ts                    ← resolvePostLoginDestination()
    authClient.ts
  utils.ts                          ← cn() helper

apps/web/public/brand/
  logo-icon.png                     ← Mark solo
  logo-full.png                     ← Wordmark dark
  logo-negro.png                    ← Wordmark light
  tukan.png                         ← Hero mascota
apps/web/public/landing/
  cta-hero.png                      ← CTA mascota
  feature-areas.png
  feature-search.png
  feature-byok.png
  screenshot-chat.png
  screenshot-analytics.png
  screenshot-search-results.png
```

### 11.2 Stitch-ready prompt template (zona pública)

Para generar pantallas adicionales coherentes con esta superficie pública, usar este prompt:

> Design a **public-facing screen** for **TukiJuris**, a Spanish-language (Peruvian Spanish, es-PE) SaaS for lawyers and citizens. **Editorial dark theme** with light mode parity. Visual identity inspired by Vercel + The Browser Company + serif-driven editorial sites.
>
> **Fonts**: Serif display `Newsreader` (variable, weights 200-800, optical size axis) for all H1/H2/H3 and brand wordmark. Sans body `Manrope` (weights 200-800) for body, labels, UI.
>
> **Palette** (dark):
> - Background: `#191918`
> - Surface: `#1F1F1E` (cards), `#1A1F1E` (sunken)
> - Primary: `#C9A84C` gold, with gradient `linear-gradient(135deg, #FFD165 0%, #EAB308 100%)` for CTAs
> - Text: `#ECEAE3` primary, `#9B9991` secondary, `#6B6962` subtle
> - Outline: `#2C2C2B`
> - Status success `#8BC98B`, danger `#E06B5C`
>
> **Layout**: max-width 1280px (`max-w-7xl`) for marketing, 896px (`max-w-4xl`) for legal long-form, 768px (`max-w-3xl`) for FAQ/contact, 440-512px for auth forms. Padding `px-4 lg:px-8`, `py-16 sm:py-24` for sections.
>
> **Hero** convention: 2-col grid (text + mascota). Mascota is **a toucan in a navy suit with red bowtie and gold beak/scales** (`/brand/tukan.png`). Place ambient `bg-primary/5` orbs with `blur-3xl` and `animate-pulse-glow`. Add floating decorative SVGs (scales, gavel, paragraph) with `animate-float`. H1 uses `font-headline text-3xl sm:text-5xl lg:text-6xl font-bold leading-[1.1]` with one accent word in `shimmer-text` gradient. CTAs are `gold-gradient` primary (h-12 px-8 rounded-xl) + ghost-border secondary.
>
> **Eyebrow pattern**: `<span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-medium uppercase tracking-wider">Section Name</span>`
>
> **Cards**: rounded-xl (12px), `bg-surface-container-low hover:bg-surface-container`, border `border-ghost-border` (a subtle 12% on-surface mix), padding `p-6 sm:p-8`, hover lift `translateY(-2px)` + soft shadow. Featured cards add `border-2 border-primary shadow-xl shadow-primary/10` and scale `md:scale-[1.03]`.
>
> **Forms** (auth): dual-column. Left = branded panel with mascota + radial glows + tagline + trust words (`PRECISIÓN · AUTORIDAD · EFICIENCIA`). Right = form card with `panel-raised` utility (subtle inset highlight + 20px shadow). Inputs h-12 with `control-surface` utility (color-mix borders), labels uppercase tracking-widest text-xs. Submit `gold-gradient` h-12 with uppercase tracking-widest text-xs.
>
> **Tone**: profesional pero cercano. Tuteo informal en CTAs ("Empieza gratis"). Usted neutro en mensajes legales. Disclaimer obligatorio en cualquier CTA legal: "Las respuestas de TukiJuris son orientativas — no constituyen asesoría legal vinculante ni reemplazan la consulta con un abogado colegiado."
>
> **Razón social visible**: "TukiTuki Solutions SAC — RUC 20613614509".
>
> **Iconography**: `lucide-react` only, stroke-width 1.5-2. Never use emoji in body content (editorial code).
>
> **Microinteractions**: `animate-fade-in-up` for hero elements with stagger delays (100/200/300/400 ms). `animate-pulse-glow` on ambient orbs and primary CTAs. `animate-float-slow` (8s loop) on mascota. `IntersectionObserver`-based `.reveal` class for scroll-triggered fade for cards.

Variantes para Stitch:
- "Show empty state for [page]"
- "Show legal long-form page (sober, no animations, no mascota)"
- "Show pricing table with featured tier highlighted"
- "Show auth form with SSO buttons and password rules indicator"
- "Show error page (404/500) with friendly recovery actions"

### 11.3 Decisiones aún por tomar

- **Light mode prevalente?** Hoy la cookie `tukijuris-theme` decide por preferencia de OS pero por defecto resuelve a dark si `prefers-color-scheme: light` NO está activo. Sugerencia: cambiar a "respect system preference" estricto y dar al usuario un toggle en el header.
- **Footer del PublicFooter en libro-reclamaciones / privacy / terms** debe ser el mismo (`PublicFooter`) o uno reducido (`LegalFooter`)? Decisión recomendada en este doc: usar `PublicFooter variant="legal"` con solo bottom row.
- **Newsletter signup en footer**? Actualmente no hay. Si se agrega, definir tono ("Suscríbete a novedades del derecho peruano + lanzamientos de TukiJuris").
- **Blog público**? Si se agrega `/blog`, definir layout específico para post detail (max-w-3xl reading column + Newsreader 18 px body).

### 11.4 Versioning

| Version | Date | Status | Notes |
|---|---|---|---|
| 1.0 | 2026-06-25 | Production-ready | Documento focalizado en superficie pública. Reemplaza la sección equivalente de DESIGN.md. |

---

**Fin de DESIGN_PUBLIC.md** — listo para Stitch / Claude design tools.
Próximo entregable: `DESIGN_APP.md` cubriendo la zona autenticada (`/analizar`, `/historial`, `/marcadores`, `/notificaciones`, `/configuracion`, `/billing`, `/organizacion`, `/analytics`, `/admin`).
