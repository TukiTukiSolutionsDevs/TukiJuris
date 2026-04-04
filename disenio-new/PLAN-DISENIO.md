# TukiJuris — Plan de Rediseño Visual v1.0.0-beta

> Documento maestro de diseño. Todo lo necesario para el rediseño visual completo
> de TukiJuris, desde la identidad de marca hasta cada pantalla del aplicativo.

---

## 1. Contexto del Proyecto

### Qué es TukiJuris
Plataforma jurídica inteligente especializada en derecho peruano. Usa IA (modelo BYOK — el usuario trae su propia API key) para consultas legales, búsqueda normativa y análisis de casos.

### Stack Técnico
- **Frontend**: Next.js 16 (App Router), Tailwind CSS
- **Backend**: FastAPI, PostgreSQL, Redis, PGVector
- **IA**: LangGraph orchestrator, 11 agentes legales especializados
- **Pagos**: MercadoPago + Culqi (soles peruanos)
- **Dominio**: tukijuris.net.pe

### Estado Actual
- Backend 100% funcional (Sprints 25-34 completados)
- Frontend funcional pero con diseño genérico/placeholder
- Auth completo (email+password, OAuth Google/Microsoft)
- Billing integrado (MercadoPago + Culqi, S/70/mes plan Base)
- 22+ pantallas existentes, alineadas con backend (auditoría Sprint 34)

### Objetivo del Rediseño
Transformar la interfaz de un prototipo funcional a un producto profesional con identidad visual propia, manteniendo toda la funcionalidad existente intacta.

---

## 2. Identidad de Marca

### Logo
Tucán abogado con traje navy, maletín y balanza de la justicia.
Texto: "TUKIJURIS ABOGADOS"
Archivo: [logo en carpeta de assets del proyecto]

### Personalidad de Marca
- **Profesional pero accesible** — como un abogado que te explica con paciencia
- **Confiable** — traje navy, balanza de justicia = autoridad legal
- **Moderno** — tecnología al servicio del derecho
- **Peruano** — tucán tropical, derecho peruano, soles

### Tono Visual
- Serio pero no intimidante
- Tecnológico pero humano (el tucán le da calidez)
- Dark mode como base (moderno, enfocado, profesional)
- Acentos dorados (justicia, excelencia, premium)

---

## 3. Design System

### 3.1 Paleta de Colores

#### Colores extraídos del logo
| Elemento       | Color   | Hex       | Rol en la app                           |
|----------------|---------|-----------|------------------------------------------|
| Traje tucán    | Navy    | `#2C3E50` | Superficies, cards destacadas, nav       |
| Pico/Balanza   | Gold    | `#EAB308` | Primary CTA, badges, links activos       |
| Corbata        | Rojo    | `#B91C1C` | Alertas, errores (uso mínimo)            |
| Cuerpo tucán   | Negro   | `#1A1A1A` | Fondos profundos                         |
| Pecho tucán    | Blanco  | `#FFFFFF` | Texto principal sobre dark               |

#### Paleta completa para la app

**Fondos (Dark Mode)**
| Token                | Hex       | Uso                                |
|----------------------|-----------|------------------------------------|
| `bg-base`            | `#0A0A0F` | Fondo principal de la app          |
| `bg-surface`         | `#111116` | Fondo de cards, modales            |
| `bg-surface-raised`  | `#1A1A22` | Cards elevadas, sidebar            |
| `bg-surface-overlay` | `#22222E` | Dropdowns, popovers, tooltips      |

**Bordes**
| Token           | Hex       | Uso                          |
|-----------------|-----------|------------------------------|
| `border-subtle` | `#1E1E2A` | Bordes entre secciones       |
| `border-default`| `#2A2A35` | Bordes de inputs, cards      |
| `border-strong` | `#3A3A48` | Bordes activos, hover        |

**Texto**
| Token           | Hex       | Uso                          |
|-----------------|-----------|------------------------------|
| `text-primary`  | `#F5F5F5` | Texto principal              |
| `text-secondary`| `#9CA3AF` | Texto auxiliar, labels       |
| `text-muted`    | `#6B7280` | Placeholders, hints          |
| `text-disabled` | `#4B5563` | Texto deshabilitado          |

**Brand / Accent**
| Token              | Hex       | Uso                                 |
|--------------------|-----------|--------------------------------------|
| `brand-primary`    | `#EAB308` | CTAs principales, links activos      |
| `brand-primary-hover`| `#D4A00A`| Hover sobre CTAs                   |
| `brand-secondary`  | `#2C3E50` | Cards destacadas, nav selected       |
| `brand-navy-light` | `#34495E` | Hover sobre navy                     |

**Semánticos**
| Token           | Hex       | Uso                          |
|-----------------|-----------|------------------------------|
| `success`       | `#34D399` | Confirmaciones, checks       |
| `success-bg`    | `#34D39915` | Background de success toast |
| `error`         | `#F87171` | Errores, validación          |
| `error-bg`      | `#F8717115` | Background de error toast   |
| `warning`       | `#FBBF24` | Warnings                     |
| `info`          | `#60A5FA` | Info, tips                   |

**Plan Badges**
| Plan         | Color bg          | Color text     |
|--------------|-------------------|----------------|
| Free/Beta    | `#6B728020`       | `#9CA3AF`      |
| Base         | `#EAB30820`       | `#EAB308`      |
| Enterprise   | `#A78BFA20`       | `#A78BFA`      |

### 3.2 Tipografía

| Rol          | Fuente     | Peso          | Uso                                |
|--------------|------------|---------------|-------------------------------------|
| Headlines    | **DM Sans**| Bold (700)    | Títulos, headings, hero text        |
| Body         | **Inter**  | Regular (400) | Párrafos, labels, inputs            |
| Body bold    | **Inter**  | Semibold (600)| Subtítulos, botones, emphasis       |
| Mono/Code    | **Geist Mono** | Regular   | Code blocks, API docs, IDs         |

#### Escala tipográfica
| Level     | Size   | Line Height | Uso                    |
|-----------|--------|-------------|------------------------|
| display   | 48px   | 1.1         | Hero heading           |
| h1        | 32px   | 1.2         | Page titles            |
| h2        | 24px   | 1.3         | Section headings       |
| h3        | 20px   | 1.4         | Card titles            |
| h4        | 16px   | 1.5         | Subsections            |
| body-lg   | 16px   | 1.6         | Body text emphasis     |
| body      | 14px   | 1.6         | Default body text      |
| body-sm   | 13px   | 1.5         | Secondary text         |
| caption   | 12px   | 1.4         | Labels, hints, badges  |
| micro     | 10px   | 1.3         | Tags, plan badges      |

### 3.3 Espaciado

| Token  | Value | Uso                               |
|--------|-------|-----------------------------------|
| xs     | 4px   | Padding mínimo, gaps tight        |
| sm     | 8px   | Padding de badges, gaps menores   |
| md     | 12px  | Padding de botones, inputs        |
| lg     | 16px  | Padding de cards, secciones       |
| xl     | 24px  | Margin entre secciones            |
| 2xl    | 32px  | Margin entre bloques grandes      |
| 3xl    | 48px  | Padding de hero, separadores      |
| 4xl    | 64px  | Margin de página                  |

### 3.4 Bordes y Sombras

| Token          | Value          | Uso                          |
|----------------|----------------|------------------------------|
| radius-sm      | 6px            | Badges, tags, chips          |
| radius-md      | 8px            | Botones, inputs              |
| radius-lg      | 12px           | Cards, modales               |
| radius-xl      | 16px           | Containers grandes           |
| radius-full    | 9999px         | Avatares, pills              |
| shadow-sm      | `0 1px 2px #00000020` | Inputs focus          |
| shadow-md      | `0 4px 12px #00000030` | Cards hover          |
| shadow-lg      | `0 8px 24px #00000040` | Modales, dropdowns   |

### 3.5 Componentes Base

#### Botones
| Variante    | Fondo             | Texto      | Borde     | Uso                    |
|-------------|-------------------|------------|-----------|------------------------|
| Primary     | `#EAB308`         | `#0A0A0F`  | none      | CTA principal          |
| Secondary   | `transparent`     | `#F5F5F5`  | `#2A2A35` | Acciones secundarias   |
| Ghost       | `transparent`     | `#9CA3AF`  | none      | Acciones terciarias    |
| Danger      | `#F8717120`       | `#F87171`  | none      | Eliminar, cancelar     |
| Navy        | `#2C3E50`         | `#F5F5F5`  | none      | Nav items activos      |

#### Inputs
- Background: `#111116`
- Border: `#2A2A35` (default), `#EAB308` (focus)
- Text: `#F5F5F5`
- Placeholder: `#6B7280`
- Border radius: 8px
- Padding: 12px 16px
- Height: 44px

#### Cards
- Background: `#111116`
- Border: `#1E1E2A`
- Border radius: 12px
- Padding: 20px
- Hover: border → `#2A2A35`, shadow-md

---

## 4. Inventario de Pantallas

### Total: 24 pantallas + 3 componentes compartidos

### Pantallas Públicas (pre-login)
| #  | Ruta                    | Pantalla           | Complejidad |
|----|-------------------------|--------------------|-------------|
| P1 | `/landing`              | Landing / Home     | Alta        |
| P2 | `/auth/login`           | Login              | Media       |
| P3 | `/auth/register`        | Register           | Media       |
| P4 | `/auth/reset-password`  | Reset Password     | Baja        |
| P5 | `/onboarding`           | Onboarding Wizard  | Alta        |
| P6 | `/compartido/[id]`      | Conv. Compartida   | Media       |
| P7 | `/status`               | Estado del Sistema | Baja        |
| P8 | `/guia`                 | Guía / FAQ         | Baja        |
| P9 | `/docs`                 | API Docs           | Media       |

### Pantallas Privadas (post-login)
| #   | Ruta               | Pantalla           | Complejidad |
|-----|--------------------|--------------------|-------------|
| A1  | `/`                | Chat Principal     | Muy Alta    |
| A2  | `/buscar`          | Buscador Normativo | Alta        |
| A3  | `/historial`       | Historial Conv.    | Alta        |
| A4  | `/marcadores`      | Marcadores         | Media       |
| A5  | `/analytics`       | Analytics          | Alta        |
| A6  | `/billing`         | Facturación/Planes | Media       |
| A7  | `/organizacion`    | Organización       | Media       |
| A8  | `/configuracion`   | Configuración      | Alta        |
| A9  | `/admin`           | Panel Admin        | Alta        |
| A10 | `/billing/success` | Pago Exitoso       | Baja        |
| A11 | `/billing/cancel`  | Pago Cancelado     | Baja        |

### Componentes Compartidos
| #  | Componente         | Se usa en                    |
|----|--------------------|------------------------------|
| S1 | Header/Nav Público | Landing, Guía, Docs, Status  |
| S2 | Footer Público     | Landing, Guía, Docs, Status  |
| S3 | App Sidebar        | Todas las pantallas privadas |

---

## 5. Orden de Diseño en Stitch

### Metodología por pantalla
```
1. Propuesta en Stitch  →  2. Revisión  →  3. Ajustes  →  4. Aprobación  →  5. Construcción
```

No se avanza a la siguiente hasta aprobar la actual.

### Fases

#### Fase 0 — Fundación (1 paso)
```
0.1  Design System (paleta, tipografía, componentes base)
     → Se crea en Stitch como base para todo lo demás
```

#### Fase 1 — Shell Compartido (2 pasos)
```
1.1  Header / Navbar público
     → Logo tucán + links + CTAs
     → Se reutiliza en todas las páginas públicas

1.2  Footer público
     → Logo + links legales + contacto
     → Se reutiliza en todas las páginas públicas
```

#### Fase 2 — Páginas Públicas (4 pasos)
```
2.1  Landing Page
     → Hero con tucán abogado
     → Propuesta de valor: "Tu asistente jurídico inteligente"
     → Features grid (11 áreas legales, BYOK, búsqueda normativa)
     → Pricing (Free Beta / Base S/70 / Enterprise Contactar)
     → FAQ
     → CTA final

2.2  Login
     → Layout 2 columnas: form + branding con tucán
     → Email + password + OAuth buttons
     → Link "¿Olvidaste tu contraseña?"
     → Link a registro

2.3  Register
     → Misma estructura que login
     → Nombre + email + password + confirmación
     → Validación real-time visual (✓/✗ por regla)
     → Checkbox Terms & Privacy
     → OAuth buttons

2.4  Reset Password
     → Centrado, minimal
     → Input nueva contraseña + confirmación
     → Validación visual
     → Estados: formulario / éxito / token expirado
```

#### Fase 3 — Onboarding (1 paso)
```
3.1  Onboarding Wizard (5 steps)
     → Step 1: Bienvenida (tucán saluda)
     → Step 2: Perfil (nombre, rol, áreas de interés)
     → Step 3: Organización (crear o unirse)
     → Step 4: API Key BYOK (traer tu clave)
     → Step 5: Listo (sugerencias de primera consulta)
     → Progress bar + animaciones de transición
```

#### Fase 4 — App Shell (2 pasos)
```
4.1  Sidebar (app privada)
     → Logo mini tucán (collapsed) / logo completo (expanded)
     → Navegación: Chat, Buscar, Analizar
     → Sección: Historial, Marcadores
     → Sección: Analytics, Org, Billing
     → Plan badge (Beta/Base/Enterprise)
     → User avatar + nombre + menú
     → Notification bell con counter
     → Collapse/expand toggle

4.2  Top Bar Mobile
     → Hamburger menu
     → Logo tucán centrado
     → Notification bell
```

#### Fase 5 — Pantallas Core (2 pasos)
```
5.1  Chat Principal
     → Sidebar con lista de conversaciones (pinned/recent)
     → Área de mensajes con markdown rendering
     → Input con selector de área + modelo
     → Botón upload archivo
     → Respuestas del asistente con:
       - Indicador de "pensando" / agente usado
       - Citas con links a fuentes
       - Botones: 👍/👎, bookmark, copy, export PDF
     → Banner de BYOK si no hay API key
     → Empty state: sugerencias de primera consulta

5.2  Buscador Normativo
     → Input grande con autosuggestions
     → Panel de filtros: área, tipo doc, fecha, jerarquía
     → Lista de resultados con highlight
     → Detalle de documento expandible
     → Búsquedas guardadas + historial
     → Paginación
```

#### Fase 6 — Gestión (3 pasos)
```
6.1  Historial
     → Tabs: Activas / Fijadas / Archivadas
     → Lista con tags de colores + carpetas
     → Acciones: pin, archivar, compartir, eliminar
     → Selección múltiple + acciones bulk
     → Panel lateral: tags CRUD + carpetas CRUD
     → Búsqueda y ordenamiento

6.2  Marcadores
     → Lista de mensajes guardados
     → Preview del contenido
     → Link "Ver conversación completa"
     → Búsqueda
     → Paginación

6.3  Analytics
     → Cards de métricas (consultas, tokens, áreas top)
     → Gráfico de barras: consultas por día
     → Gráfico pie: distribución por área
     → Tabla: consultas recientes
     → Selector de período: 7d / 30d / 90d
     → Export CSV
```

#### Fase 7 — Configuración (3 pasos)
```
7.1  Billing
     → Cards de planes: Free (badge BETA), Base S/70, Enterprise
     → Plan actual highlighted
     → Botón checkout (→ MercadoPago)
     → Logos métodos de pago: Visa, MC, Yape, BCP
     → Info de suscripción activa
     → Contacto soporte para cambios

7.2  Organización
     → Info de org (nombre, slug, plan)
     → Tabla de miembros con roles (owner/admin/member)
     → Invitar miembro (email + rol)
     → Remover miembro
     → Crear nueva org

7.3  Configuración
     → Tab Perfil: nombre, email (readonly)
     → Tab Seguridad: cambiar contraseña
     → Tab Preferencias: modelo default, área default
     → Tab API Keys: lista de keys BYOK, agregar nueva
     → Tab Memoria: toggle, lista de memorias, eliminar
     → Tab Organización: nombre, abandonar org
```

#### Fase 8 — Menores (5 pasos)
```
8.1  Billing Success (3 estados: approved/pending/rejected)
8.2  Billing Cancel
8.3  Conversación Compartida (read-only, público)
8.4  Status (health checks)
8.5  Guía FAQ + Docs API + Admin Panel
```

---

## 6. Reglas de Diseño

### DO (hacer)
- Usar dark mode como base en TODAS las pantallas
- Usar el gold `#EAB308` como accent principal (coherencia con el pico del tucán)
- Usar navy `#2C3E50` como accent secundario (coherencia con el traje)
- Respetar el spacing system (no valores arbitrarios)
- El logo del tucán debe estar presente en:
  - Header público (tamaño completo)
  - Sidebar (mini cuando collapsed, completo cuando expanded)
  - Login/Register (como branding visual)
  - Landing hero (tamaño grande)
  - Favicon (solo cabeza del tucán)
  - Emails transaccionales (ya implementado)
- Inputs y botones siempre con 44px de altura mínima (touch-friendly)
- Feedback visual inmediato en toda interacción (hover, active, focus, loading)

### DON'T (no hacer)
- No usar el rojo de la corbata como color primario (solo para errores/alertas)
- No usar fondos blancos puros (#FFFFFF como background)
- No mezclar border-radius (todo 8px o 12px, no mezclar arbitrariamente)
- No usar más de 2 fuentes (DM Sans + Inter)
- No agregar animaciones que bloqueen la interacción
- No cambiar la estructura de los endpoints/API (solo el visual)
- No eliminar funcionalidad existente al rediseñar

---

## 7. Planes Comerciales (referencia para pricing UI)

| Plan       | Precio    | Límite          | BYOK | Target                    |
|------------|-----------|-----------------|------|---------------------------|
| Free Beta  | S/ 0      | 3 meses gratis  | Sí   | Early adopters            |
| Base       | S/ 70/mes | 100 preguntas/día | Sí | Abogados independientes   |
| Enterprise | Contactar | Ilimitado       | Sí   | Estudios de abogados      |

---

## 8. Archivos del Proyecto Relevantes

### Frontend (lo que se va a rediseñar)
```
apps/web/src/
├── app/
│   ├── layout.tsx              ← Root layout (fonts, meta)
│   ├── page.tsx                ← Chat principal (1052 líneas)
│   ├── landing/page.tsx        ← Landing page
│   ├── auth/
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   ├── reset-password/page.tsx
│   │   └── callback/
│   │       ├── google/page.tsx
│   │       └── microsoft/page.tsx
│   ├── onboarding/page.tsx
│   ├── billing/
│   │   ├── page.tsx
│   │   ├── success/page.tsx
│   │   └── cancel/page.tsx
│   ├── buscar/page.tsx
│   ├── historial/page.tsx
│   ├── marcadores/page.tsx
│   ├── analytics/page.tsx
│   ├── organizacion/page.tsx
│   ├── configuracion/page.tsx
│   ├── admin/page.tsx
│   ├── compartido/[id]/page.tsx
│   ├── status/page.tsx
│   ├── guia/page.tsx
│   └── docs/page.tsx
├── components/
│   ├── AppSidebar.tsx          ← Sidebar principal
│   └── [otros componentes]
├── lib/
│   └── auth.ts                 ← Auth utilities
└── middleware.ts               ← Route protection
```

### Assets necesarios
- Logo tucán abogado (PNG/SVG, fondo transparente)
- Logo mini (solo cabeza del tucán para sidebar collapsed)
- Favicon (cabeza del tucán, 32x32 + 16x16)
- OG Image (para compartir en redes, 1200x630)

---

## 9. Historial de Sprints Completados

| Sprint | Fase | Qué se hizo | Archivos |
|--------|------|-------------|----------|
| 30 | Fase 3 | Auth Hardening (reset-password, CSRF, validación) | 6 |
| 31 | Fase 3 | MercadoPago + Culqi (migración completa de Stripe) | 12 |
| 32 | Fase 3 | Flujo Comercial (success/cancel, emails, daily limits) | 10 |
| 33 | Fase 3 | Production Hardening (docker, version, CORS) | 6 |
| 34 | Fase 3.5 | Fixes pre-diseño (19 bugs de auditoría) | 11 |

**Total Fase 3**: 5 sprints, 39+ tasks, ~45 archivos modificados/creados.

---

## 10. Siguiente Paso

Arrancar Fase 0 en Stitch: crear el Design System con la paleta, tipografía y componentes base definidos en este documento. Una vez aprobado, avanzar pantalla por pantalla según el orden de la Sección 5.

---

*Documento generado: 2026-04-04*
*Versión: 1.0.0-beta*
*Proyecto: TukiJuris — Plataforma Jurídica Inteligente*
