# TukiJuris — Roadmap de Diseño en Stitch

Mascota: Tucán abogado con traje navy, corbata roja, pico dorado, balanza dorada, maletín negro.

---

## PROMPT 00 — Design System (paleta + tipografía)

```
Design system for "TukiJuris" — a legal AI platform for Peruvian lawyers.

Colors from logo: navy blue #1B2A4A (suit), gold #EAB308 (beak/scales), red #DC2626 (tie), white #FFFFFF, black #0A0A0F (background).

Dark mode app. Primary: gold #EAB308. Background: #0A0A0F. Cards: #111116. Borders: #1E1E2A. Text: #F5F5F5. Muted: #6B7280.

Professional, premium, trustworthy. Not playful — this is for lawyers.
```

---

## PROMPT 01 — Landing Page `/landing`

```
Landing page for "TukiJuris — Asistente Legal IA para el Derecho Peruano".

Dark background #0A0A0F.

Hero: big headline "Tu bufete de abogados con IA", subtitle "11 especialistas en derecho peruano. Respuestas con citas de ley. Tu propia API key.", two buttons: "Comenzar gratis" (gold) and "Ver demo" (outline).

6 feature cards in grid: "11 Áreas del Derecho", "Búsqueda Normativa Inteligente", "Tu Propia Clave de IA (BYOK)", "Respuestas con Citas", "Analytics Avanzado", "Equipos y Organizaciones". Each card has icon, title, short description.

Pricing section: 3 plans — Gratuito (S/0), Profesional (S/39/mes), Estudio (S/99/mes). Feature lists. Gold highlight on Profesional.

Footer: logo, links to Guía, API Docs, Estado, Términos, Privacidad.

Stats bar: "24+ normas indexadas", "11 agentes especializados", "5 providers de IA".
```

---

## PROMPT 02 — Login `/auth/login`

```
Login page, dark background #0A0A0F, split layout.

Left half: dark navy #1B2A4A area with logo centered, tagline "Asistente Legal IA" below.

Right half: login form card on #111116.
- Title "Iniciar Sesión"
- Input: Email (email type, required)
- Input: Contraseña (password with show/hide eye icon, required)
- Link: "¿Olvidaste tu contraseña?"
- Button: "Iniciar Sesión" (gold #EAB308, full width)
- Divider "o continúa con"
- Two SSO buttons: "Google" and "Microsoft" (outline style with logos)
- Bottom text: "¿No tenés cuenta?" link to registro

Clean, minimal, no decorations.
```

---

## PROMPT 03 — Registro `/auth/register`

```
Register page, same split layout as login.

Left half: navy with logo.

Right half: register form card.
- Title "Crear Cuenta"
- Input: Nombre completo (text, required)
- Input: Email (email, required)
- Input: Contraseña (password with show/hide, required)
- Password strength rules shown below: "8+ caracteres", "Una mayúscula", "Una minúscula", "Un número" — each with check/circle icon
- Checkbox: "Acepto los términos y condiciones"
- Button: "Crear Cuenta" (gold, full width)
- Divider "o continúa con"
- Two SSO buttons: Google, Microsoft
- Bottom: "¿Ya tenés cuenta?" link to login
```

---

## PROMPT 04 — Reset Password `/auth/reset-password`

```
Simple centered card on dark background.

- Logo top
- Title "Recuperar Contraseña"
- Input: Email (email, required)
- Button: "Enviar enlace" (gold)
- Success state: green check "Revisa tu email"
- Link: "Volver al login"
```

---

## PROMPT 05 — Onboarding (5 steps) `/onboarding`

```
Full-screen wizard, dark background, centered card, progress bar top (5 steps).

Step 1 "Bienvenida": logo, welcome text, "Comenzar" button.

Step 2 "Perfil": select role from list (Abogado, Paralegal, Estudiante, Corporativo, Otro). Grid of 11 legal area chips to select preferred areas.

Step 3 "Organización": input nombre de org, input slug, toggle "Crear organización" or skip.

Step 4 "API Key": select provider (Google, OpenAI, Anthropic, Groq, DeepSeek, xAI), input API key (password type with show/hide), "Verificar key" button with loading state.

Step 5 "Listo": success check, summary of what was configured, "Ir al Chat" button (gold).

Navigation: back/next buttons bottom. Step indicator dots.
```

---

## PROMPT 06 — Chat Principal `/` (desktop)

```
3-column layout, dark background.

LEFT: Sidebar 240px — logo top, nav links (Chat, Buscar, Historial, Marcadores, Analytics, Organización, Facturación, Configuración, Guía, Docs, Estado). User avatar + name + logout at bottom. Collapsible.

CENTER: Chat area.
- Header bar: model selector dropdown, 4 reasoning buttons (Auto, Rápida, Moderada, Profunda), area filter dropdown.
- Messages area: user bubbles right (dark card), assistant bubbles left (darker card with bot icon). Assistant messages show markdown. Footer on each assistant msg: agent name badge, model name, latency in seconds, "Multi-área" tag, thumbs up/down, bookmark.
- Collapsible citations section "📜 N referencias normativas" with tags.
- Input bar bottom: textarea with "Escribe tu consulta legal...", attach file button, send button (gold).

RIGHT: Orchestrator panel 280px.
- Header: "Orquestador" + model badge + reasoning level badge.
- Brain icon circle (animated while working, green check when done).
- Stats: confidence %, latency, citation count.
- "Motivo de convocatoria" section with evaluator reason.
- 11 agent list: dot + icon + name. Primary = gold, Secondary = purple, inactive = gray. Typing dots while working, check when done.
- Timeline: steps with emoji, text, relative timestamp.
```

---

## PROMPT 07 — Chat Principal (mobile)

```
Single column, dark background.

Top bar: hamburger menu, logo, model selector compact.

Chat messages full width. Same bubbles as desktop.

Bottom: input bar + send button.

Floating pill bottom-center during processing: brain icon + status text, pulsing gold. Turns green when done with "✅ N agentes · Xs".

Tap pill opens bottom drawer with: model, reasoning level, stats row, active agents as chips, evaluation reason, timeline compact (last 6 steps).
```

---

## PROMPT 08 — Configuración `/configuracion`

```
AppLayout with sidebar. Page title "Configuración".

5 tabs horizontal: Perfil, Organización, Preferencias, Memoria, API Keys.

TAB Perfil:
- Input: Nombre (text)
- Input: Email (readonly, grayed)
- Button: "Guardar cambios"
- Danger zone: "Cerrar sesión" button red outline

TAB Organización:
- Shows current org name, slug, plan badge
- Input: rename org
- Members list: email + role badge (admin/member)
- Invite input: email + "Invitar" button

TAB Preferencias:
- Select: Modelo predeterminado (dropdown of 22 models)
- Select: Área legal preferida (dropdown of 11 areas + "Sin preferencia")
- Select: Idioma (Español/English)
- Toggle: Modo oscuro
- Button: "Guardar"

TAB Memoria:
- Toggle: "Habilitar memoria de contexto"
- List of extracted memory items with delete buttons
- Button: "Limpiar toda la memoria"

TAB API Keys:
- Cards per provider: Google, OpenAI, Anthropic, Groq, DeepSeek, xAI
- Each card: provider logo, key hint (AIz...tZHg), status dot green/red, "Probar" button, "Eliminar" button
- "Agregar nueva key" section: select provider, input key (password), "Guardar y verificar" button
- Links to provider consoles (external)
```

---

## PROMPT 09 — Historial `/historial`

```
AppLayout. Title "Historial de Consultas".

Search bar top. Filter buttons: "Todas", "Hoy", "Esta semana", "Este mes".

List of conversation cards:
- Title (auto-generated from first message)
- Preview text (truncated)
- Legal area badge (colored)
- Date relative ("hace 2 horas")
- Actions: open, pin, archive, delete

Pagination or infinite scroll.
```

---

## PROMPT 10 — Marcadores `/marcadores`

```
AppLayout. Title "Marcadores".

Grid of bookmarked message cards:
- Message content preview (truncated)
- Agent used badge
- Legal area badge
- Date
- Actions: open conversation, remove bookmark
```

---

## PROMPT 11 — Buscar `/buscar`

```
AppLayout. Title "Búsqueda Normativa".

Big search input centered top with search icon.

Filter row: legal area dropdown, document type dropdown (Ley, Decreto, Resolución, Constitución), date range.

Results list:
- Document title
- Type badge
- Legal area badge
- Relevance score bar
- Preview snippet with highlighted matches
- "Ver completo" link

Empty state: illustration + "Ingresa un término para buscar en la base normativa".
```

---

## PROMPT 12 — Analizar Documento `/analizar`

```
AppLayout. Title "Analizar Documento".

Upload zone centered: drag & drop area with dashed border, icon, "Arrastra un PDF, DOCX o TXT aquí". File size limit note "Máx. 10MB".

Button: "Seleccionar archivo"

After upload: file name, size, type badge, "Analizar" button (gold).

Processing state: progress bar + "Extrayendo texto..."

Results: extracted text preview, "Consultar sobre este documento" button that opens chat with context.
```

---

## PROMPT 13 — Analytics `/analytics`

```
AppLayout. Title "Analytics".

Top stats row (4 cards): Total consultas, Consultas hoy, Áreas más consultadas, Tokens usados.

Charts section:
- Line chart: consultas por día (últimos 30 días)
- Pie chart: distribución por área legal
- Bar chart: modelos más usados
- Table: últimas 10 consultas con fecha, área, modelo, tokens, latencia

Export buttons: "Exportar CSV", "Exportar PDF".

Date range picker top right.
```

---

## PROMPT 14 — Organización `/organizacion`

```
AppLayout. Title "Mi Organización".

Org header card: name, slug, plan badge, created date.

Members section:
- Table: nombre, email, rol (Admin/Miembro), fecha ingreso, actions (change role, remove)
- "Invitar miembro" button opens inline form: email input + role select + "Enviar invitación"

Settings section:
- Input: rename org
- Danger zone: "Eliminar organización" with confirmation
```

---

## PROMPT 15 — Facturación `/billing`

```
AppLayout. Title "Facturación".

Current plan card: plan name, status badge (Activo/Trial), period dates.

3 plan cards side by side:
- Gratuito S/0: features list, "Plan actual" disabled button
- Profesional S/39/mes: features list, "Actualizar" gold button, "Recomendado" badge
- Estudio S/99/mes: features list, "Actualizar" button

Payment methods: MercadoPago and Culqi logos.

BYOK note: "Todos los planes usan tu propia API key. Sin costos ocultos de IA."
```

---

## PROMPT 16 — Admin `/admin`

```
AppLayout with AdminSidebar. Title "Panel de Administración".

Stats cards top: Total usuarios, Usuarios activos hoy, Total consultas, Total organizaciones.

Users table: name, email, plan, org, queries count, last active, actions (disable/enable).

Search + filter bar above table.

Quick actions: "Exportar usuarios CSV".
```

---

## PROMPT 17 — Guía `/guia`

```
AppLayout. Title "Guía de Uso".

Accordion sections:
- "¿Qué es TukiJuris?" — description
- "¿Cómo hacer una consulta?" — steps with screenshots
- "¿Qué son los niveles de razonamiento?" — Auto/Rápida/Moderada/Profunda explained
- "¿Cómo configurar mi API key?" — step by step per provider
- "¿Qué áreas del derecho cubre?" — 11 areas listed
- "¿Cómo funciona el orquestador?" — pipeline explained
- "¿Puedo subir documentos?" — file upload guide
- "¿Cómo exportar mis consultas?" — export guide
```

---

## PROMPT 18 — API Docs `/docs`

```
AppLayout. Title "Documentación API".

Left nav: endpoint groups (Auth, Chat, Conversations, Search, Keys, Usage, Admin).

Right content: for each endpoint:
- Method badge (GET green, POST blue, PUT yellow, DELETE red) + path
- Description
- Request body example (JSON)
- Response example (JSON)
- Auth: "Requiere Bearer token"

Interactive "Try it" button optional.
```

---

## PROMPT 19 — Estado del Sistema `/status`

```
AppLayout. Title "Estado del Sistema".

Service cards grid:
- API Backend: status dot (green/red) + latency
- Database (PostgreSQL): status + connections
- Redis Cache: status
- RAG (Embeddings): status + docs indexed count
- LLM Providers: Google, OpenAI, Anthropic, Groq, DeepSeek, xAI — each with status dot

Uptime chart: last 30 days bar chart.

Last check timestamp + "Verificar ahora" button.
```

---

## PROMPT 20 — Documento Detalle `/documento/[id]`

```
AppLayout. Title: document name.

Metadata bar: type badge, legal area badge, date, author.

Full document text rendered with markdown.

Sidebar right (or bottom on mobile): related documents list, "Consultar sobre este documento" button.
```

---

## PROMPT 21 — Compartido `/compartido/[id]`

```
Public page (no sidebar, no login required).

Top bar: TukiJuris logo + "Iniciar sesión" link.

Shared conversation view: read-only messages. Agent badges, citations visible.

Footer: "Generado por TukiJuris — Asistente Legal IA" + CTA "Crea tu cuenta gratis".
```

---

## PROMPT 22 — Billing Success `/billing/success`

```
Centered card on dark background.

Green check icon big.
Title: "¡Pago exitoso!"
Subtitle: "Tu plan ha sido actualizado a [plan name]."
Button: "Ir al Chat" (gold)
```

---

## PROMPT 23 — Billing Cancel `/billing/cancel`

```
Centered card on dark background.

Yellow warning icon.
Title: "Pago cancelado"
Subtitle: "No se realizó ningún cargo. Podés intentar de nuevo."
Button: "Volver a Facturación"
```

---

## Resumen de pantallas: 24 total

| # | Pantalla | Ruta | Tipo |
|---|----------|------|------|
| 00 | Design System | — | Paleta/tokens |
| 01 | Landing | /landing | Marketing |
| 02 | Login | /auth/login | Auth |
| 03 | Registro | /auth/register | Auth |
| 04 | Reset Password | /auth/reset-password | Auth |
| 05 | Onboarding | /onboarding | Wizard 5 pasos |
| 06 | Chat (desktop) | / | Core app |
| 07 | Chat (mobile) | / | Core app |
| 08 | Configuración | /configuracion | Settings 5 tabs |
| 09 | Historial | /historial | List |
| 10 | Marcadores | /marcadores | Grid |
| 11 | Buscar | /buscar | Search |
| 12 | Analizar | /analizar | Upload |
| 13 | Analytics | /analytics | Dashboard |
| 14 | Organización | /organizacion | Management |
| 15 | Facturación | /billing | Pricing |
| 16 | Admin | /admin | Admin panel |
| 17 | Guía | /guia | Help |
| 18 | API Docs | /docs | Reference |
| 19 | Estado | /status | Monitoring |
| 20 | Documento | /documento/[id] | Detail |
| 21 | Compartido | /compartido/[id] | Public |
| 22 | Billing Success | /billing/success | Feedback |
| 23 | Billing Cancel | /billing/cancel | Feedback |
