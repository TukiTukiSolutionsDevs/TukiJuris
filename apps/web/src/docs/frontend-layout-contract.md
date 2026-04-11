# Contrato estructural del frontend

## Objetivo

Definir UNA sola arquitectura espacial para la app privada antes de seguir con refinamiento visual.

---

## Shell oficial del producto

### 1. Público
- `landing`, `auth/*`, `reset`, `compartido/[id]`
- Sin app shell privado.
- Header/footer públicos según corresponda.

### 2. Privado estándar
- `/`, `/buscar`, `/historial`, `/marcadores`, `/analytics`, `/billing`, `/configuracion`, `/organizacion`, `/guia`, `/docs`, `/status`, `/analizar`, `/documento/[id]`
- Usa `WorkspaceShell`.
- Slots oficiales:
  - `sidebar`
  - `topbar`
  - `content`
  - `rightRail`
  - `mobileDrawer`

### 3. Privado admin
- `/admin`
- Usa `WorkspaceShell` con navegación admin.
- Mantiene el mismo contrato de slots aunque hoy no use `rightRail`.

---

## Mapa por pantalla

| Pantalla | Sidebar desktop | Top bar mobile | Right rail | Footer interno |
|---|---|---|---|---|
| `/` | Sí | Sí | No por defecto | No |
| `/buscar` | Sí | Sí | No por defecto | No |
| `/historial` | Sí | Sí | No por defecto | No |
| `/marcadores` | Sí | Sí | No por defecto | No |
| `/analytics` | Sí | Sí | No por defecto | No |
| `/billing` | Sí | Sí | No por defecto | No |
| `/configuracion` | Sí | Sí | No por defecto | No |
| `/organizacion` | Sí | Sí | No por defecto | No |
| `/guia` | Sí | Sí | No por defecto | No |
| `/docs` | Sí | Sí | No por defecto | No |
| `/status` | Sí | Sí | No por defecto | No |
| `/analizar` | Sí | Sí | No por defecto | No |
| `/documento/[id]` | Sí | Sí | Opcional contextual | No |
| `/admin` | Sí | Sí | No por defecto | No |

---

## Reglas de scroll

1. El viewport raíz del shell es `h-screen` + `overflow-hidden`.
2. El scroll principal vive en `content` (`main`).
3. `sidebar` y `rightRail` pueden tener scroll interno propio solo si su contenido excede la altura.
4. No se permiten scrollbars duplicados por página salvo necesidad funcional explícita.
5. Headers móviles sticky viven fuera del `main` scrolleable.
6. Páginas inmersivas como chat pueden pedir `contentClassName="overflow-hidden"` y delegar el scroll a regiones internas, sin redefinir un viewport raíz paralelo.

---

## Breakpoints oficiales

- `mobile`: `< md`
- `desktop shell`: `md+`
- `rightRail`: `xl+`

### Reglas
- En mobile, la navegación lateral entra por `mobileDrawer`.
- Desde `md`, el sidebar principal es persistente.
- El `rightRail` es persistente recién en `xl+`.
- Debajo de `xl`, cualquier rail contextual vive como drawer lateral (`md`/`lg`) o bottom sheet (`mobile`).

## Anchos máximos oficiales

- `max-w-3xl`: lectura densa o estados compactos.
- `max-w-5xl`: configuración, billing, organización, detalle documental.
- `max-w-6xl`: vistas operativas medias como guía/historial.
- `max-w-7xl` o `max-w-screen-xl`: data-heavy, docs, admin, analytics, búsqueda.

### Regla
- Cada página privada debe elegir un bucket oficial y no improvisar anchos arbitrarios sin una necesidad real.

---

## Reglas de implementación

1. Ninguna página privada define su propio contenedor raíz de viewport si ya vive dentro del shell.
2. `AppLayout` y `AdminLayout` son adaptadores del contrato, no layouts libres.
3. La lógica de drawer mobile vive en el shell, NO en cada sidebar.
4. La navegación puede variar, pero la estructura espacial no.
5. Las páginas internas deben usar una cabecera consistente de tipo `InternalPageHeader` antes del contenido principal, en vez de improvisar top bars locales incompatibles.

---

## Sistema de placement UI

### Header global / top bar
- Solo navegación shell y utilidades globales compactas.
- Utilidades globales oficiales: notificaciones, tema, acceso a configuración.

### Header de página (`InternalPageHeader` o header maestro del chat)
- Contexto de la pantalla: título, eyebrow, descripción breve.
- Puede mostrar utilidades globales en desktop si no compiten con el shell móvil.
- Las acciones propias de la página viven en `actions`, separadas del contexto.

### Composer / toolbar local
- Controles directamente ligados a la tarea activa.
- En chat: modelo, profundidad, adjuntos, ayuda, formato.
- No deben volver al header global.

### Right rail
- Estado contextual, inspección, telemetría u orquestación.
- No usarlo para utilidades globales recurrentes.

---

## Estado actual

- Sprint A cerrado: contrato estructural documentado.
- Sprint B cerrado: shell unificado implementado sobre `WorkspaceShell`.
