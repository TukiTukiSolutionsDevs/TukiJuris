# TukiJuris — Roadmap de Estructura Frontend

> Estado: Diagnóstico completado, implementación pendiente
> Última actualización: 2026-04-10
> Objetivo: Dejar el app shell, navegación, scroll y responsive sólidos antes del rediseño visual fino.

---

## 1. Principio rector

Primero corregimos **estructura y flujo**, después diseño visual.

Esto significa:

- un único modelo de layout para todo el producto;
- comportamiento responsive consistente;
- reglas claras para sidebar, header, panel derecho y zonas de scroll;
- superficies estables para luego decidir con criterio dónde viven notificaciones, acciones globales, CTA y elementos de contexto.

---

## 2. Diagnóstico estructural actual

### Hallazgos confirmados

1. **Shell duplicado y frágil**
   - `AppLayout.tsx` y `AdminLayout.tsx` repiten la misma idea con reglas distintas.
   - Ambos hacen auth guard client-side con `useEffect`, lo que puede causar flashes, pantallas vacías y mala percepción de estabilidad.

2. **Demasiadas regiones con scroll**
   - Sidebar izquierda scrollable.
   - Main content scrollable.
   - Panel derecho/orquestador scrollable.
   - En varias pantallas esto crea sensación de layout “roto” o difícil de controlar.

3. **Jerarquía inconsistente entre páginas**
   - `/` usa shell tipo chat con panel derecho.
   - `/buscar`, `/configuracion`, `/analytics`, `/historial` viven dentro del mismo layout pero no comparten una convención clara de encabezado, ancho útil, rail secundario o acciones primarias.
   - `/onboarding` rompe completamente el shell del app, lo cual puede estar bien como excepción, pero hoy no está definido como sistema.

4. **Header principal sobrecargado en chat**
   - Título contextual + notificaciones + selector de modelo + reasoning depth + otros controles compiten en una sola barra pequeña.
   - Eso dificulta escalabilidad y responsive.

5. **Panel derecho sin estrategia transversal**
   - El orquestador existe en desktop, pero no hay un modelo compartido para “right rail contextual” reutilizable en otras páginas.
   - Tampoco hay contrato claro para tablet/mobile (drawer, sheet, collapse, etc.).

6. **Sidebar con mezcla de navegación global y utilidades**
   - Navegación principal, secciones secundarias, notificaciones, tema, plan y logout conviven sin una jerarquía de producto unificada.
   - El link de notificaciones todavía está acoplado a configuración.

---

## 3. Referencias UX investigadas

### Fuentes consultadas

- Smashing Magazine — *Designing Sticky Menus: UX Guidelines*
- Smashing Magazine — *Overview of Responsive Navigation Patterns*
- Eleken — *UX Navigation Design: Common Patterns and Best Practices*
- Eleken — *SaaS Application Interface Examples*

### Conclusiones aplicables a TukiJuris

1. **Sidebar persistente en desktop funciona bien para SaaS complejos**
   - especialmente cuando la IA, historial, configuración y herramientas viven en el mismo producto.

2. **Evitar múltiples scrollbars cuando no son imprescindibles**
   - múltiples panes sticky/scrollables degradan orientación y descubribilidad.

3. **El panel derecho contextual debe ser opcional y claramente secundario**
   - útil en desktop si aporta contexto real (orquestador, detalles, inspector),
   - pero en tablet/mobile debe degradar a drawer o bottom sheet.

4. **Top bar compacta, no recargada**
   - sticky sí, pero solo con acciones globales o contextuales críticas.

5. **Responsive complejo necesita reglas explícitas por breakpoint**
   - desktop: persistencia;
   - tablet: colapso / drawer lateral;
   - mobile: navegación y panel contextual bajo demanda.

---

## 4. Arquitectura objetivo del app shell

## Modelo canónico

### Desktop (≥ 1280px)
- **Left rail persistente**: navegación principal + cuenta + utilidades globales.
- **Center workspace dominante**: contenido principal de cada página.
- **Right contextual rail opcional**: orquestador, inspector, metadata, activity stream.
- **Top bar compacta** sobre el workspace, no sobre todo el viewport.

### Tablet (768px–1279px)
- sidebar izquierda **colapsable** o fija en icon mode;
- panel derecho pasa a **drawer contextual**;
- top bar simplificada;
- cero dependencia de tres columnas simultáneas.

### Mobile (< 768px)
- sidebar como **drawer**;
- panel contextual como **bottom sheet / drawer**;
- top bar mínima con solo acciones clave;
- contenido principal siempre prioritario.

---

## 5. Reglas estructurales a implementar

1. **Una sola fuente de verdad para layouts autenticados**
   - crear un `AppShell` compartido;
   - `AdminLayout` debe derivar del mismo sistema, no competir con él.

2. **Una sola estrategia de scroll por vista**
   - priorizar scroll principal del workspace;
   - rails laterales solo scrollean si su contenido realmente lo exige;
   - evitar stacks con 3 scrolls visibles al mismo tiempo.

3. **Header por página, no header gigante global**
   - el shell define estructura;
   - cada pantalla define su app bar contextual con slots claros.

4. **Right rail como patrón del sistema**
   - no solo para chat;
   - mismo comportamiento, mismos breakpoints, misma API visual.

5. **Notificaciones y utilidades globales viven en zona estable**
   - idealmente top bar o utility cluster consistente;
   - no enterradas en configuraciones ni duplicadas.

6. **Onboarding y auth quedan fuera del shell principal por diseño**
   - excepción permitida, pero conscientemente definida.

---

## 6. Roadmap por sprints

## Sprint A — Auditoría y contrato estructural
**Objetivo:** definir la arquitectura oficial del frontend.

### Entregables
- [ ] Documento de arquitectura de layout unificado.
- [ ] Mapa por página: qué usa left rail, top bar, right rail y footer.
- [ ] Reglas de scroll por tipo de pantalla.
- [ ] Breakpoints oficiales del producto.

### Resultado esperado
Todo el equipo entiende cuál es el shell correcto antes de tocar UI fina.

---

## Sprint B — Refactor del App Shell
**Objetivo:** reemplazar layouts duplicados por un sistema único.

### Entregables
- [ ] Crear `AppShell`/`WorkspaceShell` reutilizable.
- [ ] Unificar `AppLayout` y `AdminLayout` bajo el mismo patrón.
- [ ] Definir slots: `sidebar`, `topbar`, `content`, `rightRail`, `mobileDrawer`.
- [ ] Quitar dependencias de layout improvisadas por página.

### Resultado esperado
Base frontend coherente y mantenible.

---

## Sprint C — Scroll, viewport y sticky behavior
**Objetivo:** eliminar scroll roto y comportamiento inconsistente.

### Entregables
- [ ] Normalizar alturas y `min-h-0` / `overflow` en shell.
- [ ] Eliminar scrollbars redundantes donde no aportan valor.
- [ ] Definir cuándo sidebar y right rail scrollean y cuándo no.
- [ ] Corregir headers sticky, focus targets y anchors.

### Resultado esperado
Navegación y lectura limpias, sin sensación de app quebrada.

---

## Sprint D — Responsive del producto completo
**Objetivo:** asegurar comportamiento impecable entre desktop, tablet y mobile.

### Entregables
- [ ] Sidebar persistente desktop / drawer mobile.
- [ ] Right rail → drawer/sheet en tablet/mobile.
- [ ] Header compacta adaptativa.
- [ ] Reglas para cards, grids y anchos máximos del workspace.

### Resultado esperado
App usable en cualquier tamaño antes del polish visual.

---

## Sprint E — Jerarquía funcional del home/chat
**Objetivo:** convertir `/` en la referencia estructural del producto.

### Entregables
- [ ] Limpiar top bar del chat.
- [ ] Redefinir posición de notificaciones y utilidades globales.
- [ ] Clarificar relación entre conversación, input y orquestador.
- [ ] Establecer empty state, stateful panels y responsive behavior como patrón maestro.

### Resultado esperado
El home/chat se vuelve el estándar para las pantallas privadas.

---

## Sprint F — Aplicación del shell a páginas internas
**Objetivo:** llevar la estructura correcta a todo el app.

### Páginas foco
- [ ] `/buscar`
- [ ] `/historial`
- [ ] `/configuracion`
- [ ] `/analytics`
- [ ] `/admin`
- [ ] `/organizacion`

### Resultado esperado
Todas las páginas comparten la misma lógica espacial y de navegación.

---

## Sprint G — Sistema de placement UI
**Objetivo:** decidir con base firme dónde vive cada acción global.

### Entregables
- [ ] Política de placement para notificaciones.
- [ ] Política para perfil, plan, logout y theme toggle.
- [ ] Política para acciones primarias/secundarias por página.
- [ ] Política para rail contextual y tool panels.

### Resultado esperado
Después de este sprint, el diseño visual ya se apoya sobre una arquitectura sólida.

---

## 7. Estado del roadmap

### Completados
- [x] Sprint A — Auditoría y contrato estructural
- [x] Sprint B — Refactor del App Shell
- [x] Sprint C — Scroll, viewport y sticky behavior
- [x] Sprint D — Responsive del producto completo
- [x] Sprint E — Jerarquía funcional del home/chat
- [x] Sprint F — Aplicación del shell a páginas internas
- [x] Sprint G — Sistema de placement UI
- [x] Sprint H — Saneamiento de deuda técnica visual/lint

### Pendientes
- [ ] Refinamiento visual global

---

## 8. Compromiso de seguimiento

Este roadmap se actualizará **cada vez que se complete algo importante**:

- diagnóstico cerrado;
- shell unificado implementado;
- scroll corregido;
- responsive estable;
- home/chat reestructurado;
- placement global definido.

No se usa como documento decorativo. Se usa como plano vivo del refactor.
