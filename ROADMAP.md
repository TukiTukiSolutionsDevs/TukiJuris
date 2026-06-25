# TukiJuris — Roadmap a Producción

> Documento vivo. Última actualización: 2026-05-31 — sesión de hardening pre-deploy.
> Fuente única de verdad para el trabajo hacia `tukijuris.com.pe`.

---

## Estado actual

| Indicador | Valor |
|---|---|
| Branch | `main` |
| Última migración Alembic | `020_indexes_and_sunat_prep` (head) |
| Servicios dev | api ✅ web ✅ db ✅ redis ✅ (healthy) |
| Bloqueadores P0 | **0** (todos resueltos en esta sesión) |
| Hallazgos P1 | la mayoría resueltos — pendientes los que requieren información tuya |
| ¿Listo para deploy a prod? | **Sí**, una vez completes los items marcados `JAIME` |
| Ventana Culqi | 15 días desde deploy — UI ya soporta modo "habilitando" |

## Decisiones vinculantes (registradas)

- **Dominio oficial**: `tukijuris.com.pe`. `.net.pe` eliminado del código.
- **Pricing**: Free S/0 · Pro S/70/mes · Studio "Contactar" (sin precio).
- **Payment provider**: solo Culqi. Stripe y MercadoPago fuera.
- **Empresa**: TukiTuki Solutions SAC — RUC 20613614509.
- **Multitenancy refactor (org_id en datos)**: postergado a FASE 1.
- **SUNAT**: arrancamos con boletas vía SUNAT SOL manual; integración PSE en FASE 2.

## Convención

- `[ ]` pendiente · `[~]` en progreso · `[x]` hecho · `[!]` bloqueado / pendiente info
- Owner: `CLAUDE` (yo lo hago) · `JAIME` (lo haces tú) · `MIXED`

---

## FASE 0 — Pre-deploy ✅ COMPLETA

### F0-OPS — Configuración base

- [x] **F0-OPS-01** · Reemplazo global `.net.pe` → `.com.pe` (29 archivos) — CLAUDE
- [x] **F0-OPS-02** · Dockerfile.prod ejecuta `bootstrap.py` (alembic + schema verify) — CLAUDE
- [x] **F0-OPS-03** · `bootstrap.py` lee `APP_ENV` para alternar `--reload` / `--workers` — CLAUDE
- [x] **F0-OPS-04** · web: `INTERNAL_API_URL=http://api:8000` + `NEXT_PUBLIC_*` como build-args — CLAUDE
- [x] **F0-OPS-05** · healthcheck del servicio `web` (wget /) — CLAUDE
- [x] **F0-OPS-06** · Makefile `prod-*` con `--env-file .env.production` + container names `tukijuris-*` consistentes — CLAUDE
- [x] **F0-OPS-07** · Stripe eliminado de `.env.production.example`; payment config alineado con Culqi — CLAUDE
- [!] **F0-OPS-08** · `.env.production` con valores reales — JAIME (plantilla entregada, ver `deploy_guide.md`)

### F0-DAT — Migraciones

- [x] **F0-DAT-01** · Mounts SQL legacy 002–014 eliminados del compose prod; Alembic es source of truth — CLAUDE
- [x] **F0-DAT-02** · `UsageRecord.reasoning_count` declarado en el ORM (`models/subscription.py`) — CLAUDE

### F0-SEC — Seguridad crítica

- [x] **F0-SEC-01** · OAuth verifica `id_token` (JWKS + iss + aud + exp) Google y Microsoft — CLAUDE
- [x] **F0-SEC-02** · Account-linking exige `email_verified=true`; rechaza con 409 en caso contrario — CLAUDE
- [x] **F0-SEC-03** · `JWT_SECRET` gate por `app_debug=False` (no por env name); rechaza placeholders + secretos < 32ch — CLAUDE
- [x] **F0-SEC-04** · `BYOK_ENCRYPTION_KEY` mandatorio cuando no debug — CLAUDE
- [x] **F0-SEC-05** · `CULQI_WEBHOOK_SECRET` mandatorio cuando Culqi configurado en prod — CLAUDE
- [x] **F0-SEC-06** · Access-token revocation: `mark_user_revoked` + check en `get_current_user` (Redis, fail-open) — CLAUDE
- [x] **F0-SEC-07** · `_set_session_cookies(is_admin=)` propagado en todos los callbacks SSO — CLAUDE
- [x] **F0-SEC-08** · `PUT /api/auth/me` valida `OrgMembership` activo antes de aceptar `default_org_id` — CLAUDE
- [x] **F0-SEC-09** · Rate-limit IP-based de `/api/auth/password-reset` (prefix corregido) — CLAUDE
- [x] **F0-SEC-10** · Upload: pre-check `Content-Length` + cap 10 MB (`MAX_UPLOAD_BYTES`) — CLAUDE
- [x] **F0-SEC-11** · CORS rechaza orígenes `http://` en prod — CLAUDE

### F0-PAY — Pagos consistentes

- [x] **F0-PAY-01** · `STATIC_PLANS` actualizado (Pro S/70, Free 4+1/día, Studio "Contactar") — CLAUDE
- [x] **F0-PAY-02** · Studio UI sin precio numérico, CTA a `ventas@tukijuris.com.pe` — CLAUDE
- [x] **F0-PAY-03** · `/precios` sincronizado con `plans.py` — features, badges, FAQ, voseo → tuteo — CLAUDE
- [x] **F0-PAY-04** · MercadoPago oculto de UI; webhooks siguen aceptando pero sin promotion — CLAUDE
- [x] **F0-PAY-05** · billing `alert()` → `toast` (sonner) — CLAUDE

### F0-LEG — Páginas legales

- [x] **F0-LEG-01** · `/privacy`, `/terms`, `/contacto`, `/libro-reclamaciones` en `PUBLIC_PATHS` — CLAUDE
- [x] **F0-LEG-02** · `/guia` y `/status` migradas a `PublicLayout` — CLAUDE
- [x] **F0-LEG-03** · Tildes corregidas en `/privacy` y `/terms` (reescritos completamente) — CLAUDE
- [x] **F0-LEG-04** · `robots.ts` + `sitemap.ts` (Next 15 metadata route) — CLAUDE
- [x] **F0-LEG-05** · ANPD mencionada como autoridad de reclamo (Ley 29733 art. 22) — CLAUDE
- [x] **F0-LEG-06** · Términos: Libro de Reclamaciones, plazo 30 días cambios materiales, política cancelación + reembolso — CLAUDE
- [x] **F0-LEG-07** · Aviso de IA visible en landing hero + /precios — CLAUDE
- [x] **F0-LEG-08** · Footer público con RUC + razón social + link Libro Reclamaciones + aviso IA — CLAUDE
- [x] **F0-LEG-09** · `CookieBanner` (esencial-only, persistido en localStorage) — CLAUDE
- [x] **F0-LEG-10** · `/libro-reclamaciones` página dedicada con flujo formal — CLAUDE
- [x] **F0-LEG-11** · `/contacto` página dedicada con canales por tipo — CLAUDE

### F0-UX — Botones y flujos

- [x] **F0-UX-01** · `ChatHeader` botón "Analizar" → `<Link href="/analizar">` — CLAUDE
- [x] **F0-UX-02** · `AppSidebar` botones tema conectados a `useTheme()` (Sun/Moon dinámico) — CLAUDE
- [x] **F0-UX-04** · `configuracion` change-password redirect `/login` → `/auth/login` — CLAUDE
- [x] **F0-UX-05** · `/analizar` y `/documento/[id]` usan `authFetch` con manejo 401/403/404 — CLAUDE
- [x] **F0-UX-06** · `/billing` `alert()` → `toast` — CLAUDE
- [x] **F0-UX-07** · Botón "Comandos (próximamente)" eliminado de `ChatComposer` — CLAUDE
- [x] **F0-UX-08** · `/auth/rate-limited` verificada existente — CLAUDE
- [ ] **F0-UX-03** · `KeyboardShortcuts.onToggleSidebar` (no-op residual; sidebar funciona, solo el atajo de teclado no) — bajo impacto, FASE 1
- [x] **F0-UX-09** · Mensaje hardcoded `http://localhost:8000` removido del chat — CLAUDE

### F0-INFRA — Acciones en el VPS (te tocan)

- [!] **F0-INFRA-01** · `docker network create shared-gateway` + conectar `toroloco-gateway` — JAIME
- [!] **F0-INFRA-02** · Configurar upstream del gateway (`/api/*` → `api:8000`, `/*` → `web:3000`, SSE flags) — JAIME
- [!] **F0-INFRA-03** · DNS de `tukijuris.com.pe` (A, MX, SPF, DKIM, DMARC) — JAIME
- [!] **F0-INFRA-04** · Verificar dominio en Resend (DKIM + SPF) — JAIME
- [!] **F0-INFRA-05** · Crear OAuth Client en Google Cloud Console (redirect URI `https://tukijuris.com.pe/auth/callback/google`, scopes `openid email profile`) — JAIME

---

## FASE 1 — Hardening esta semana ✅ PARCIAL

### F1-TEN — Multitenancy

- [x] **F1-TEN-04** · Índices `Invoice.org_id`, `Organization.payment_subscription_id`, `Organization.payment_customer_id` (migración 020) — CLAUDE
- [x] **F1-TEN-03** · `CheckConstraint` para `OrgMembership.role IN ('owner','admin','member')` (migración 020) — CLAUDE
- [ ] **F1-TEN-01** · `org_id` en `conversations/documents/uploads/memory/tags` — refactor grande, postergado por decisión Jaime
- [ ] **F1-TEN-02** · Constraint de owner único por org (partial unique index)
- [ ] **F1-TEN-05** · Endpoint `DELETE /conversations/{id}/share`
- [ ] **F1-TEN-06** · `models/__init__.py` importa todas las clases

### F1-SEC — Seguridad alta

- [ ] **F1-SEC-01** · OAuth state ligado a cookie (HMAC + nonce match)
- [ ] **F1-SEC-02** · `User.is_admin` resincronización en cada refresh
- [ ] **F1-SEC-03** · Audit event en login success/failed
- [ ] **F1-SEC-04** · Microsoft: preferir `mail` verificado sobre `userPrincipalName` (parcial — id_token ya cubre la mayor parte)
- [ ] **F1-SEC-05** · Scrubbing de PII en logs INFO/WARNING
- [ ] **F1-SEC-06** · Login rate-limit combinado email + IP
- [ ] **F1-SEC-07** · Password-reset bloqueado para cuentas SSO
- [!] **F1-SEC-08** · CAPTCHA (Turnstile/hCaptcha) en `/auth/register` — JAIME (cuenta) + CLAUDE (integración)

### F1-LEG — Cumplimiento

- [x] **F1-LEG-02** · Footer con RUC + Libro de Reclamaciones — CLAUDE
- [ ] **F1-LEG-01** · Voseo → tuteo en `/landing`, `/caracteristicas`, `/guia`, onboarding (parcial — hecho en /precios)
- [!] **F1-LEG-03** · OG image 1200×630 dedicada — JAIME (asset gráfico)
- [ ] **F1-LEG-04** · `prefers-reduced-motion` para animaciones
- [x] **F1-LEG-05** · Página `/contacto` con canales por tipo — CLAUDE

### F1-OPS — DevOps

- [x] **F1-OPS-01** · CI básico (`.github/workflows/ci.yml`: ruff + pytest + tsc + next build) — CLAUDE
- [x] **F1-OPS-02** · `sentry.client.config.ts` stub listo (install + DSN para activar) — CLAUDE
- [x] **F1-OPS-06** · `.dockerignore` en root (excluye tests, _pitch, sdks, sdd, .atl, caches) — CLAUDE
- [x] **F1-OPS-07** · `infrastructure/nginx/` y `certbot/` quedan como legacy referencia (gateway externo los reemplaza) — CLAUDE
- [ ] **F1-OPS-03** · Backup encriptado (gpg/age) + retención + restore probado
- [!] **F1-OPS-04** · Uptime externo (UptimeRobot/Healthchecks.io) — JAIME
- [!] **F1-OPS-05** · Aumentar memory limits API a 1G, DB a 1G (validar VPS) — ya hecho en compose; verificar host — JAIME

---

## FASE 2 — Ventana 15 días Culqi

### F2-PAY — Integración Culqi

- [x] **F2-PAY-01** · Loader Culqi.js + `tokenizeCard` helper en `apps/web/src/lib/culqi.ts` — CLAUDE
- [x] **F2-PAY-03** · Página `/billing/checkout` con form PCI-safe (modo "habilitando" si falta key) — CLAUDE
- [!] **F2-PAY-04** · `NEXT_PUBLIC_CULQI_PUBLIC_KEY` (sandbox primero) — JAIME (cuando Culqi habilite)
- [ ] **F2-PAY-02** · Reemplazar input texto en `AddCardModal` por flujo tokenizado (helper ya disponible)
- [ ] **F2-PAY-05** · Verificar firma webhook Culqi vs spec real
- [ ] **F2-PAY-06** · Suscripciones recurrentes (cargo on-demand mensual o subscriptions Culqi)
- [ ] **F2-PAY-07** · Dunning T+1d/T+3d/T+7d, downgrade T+10d
- [ ] **F2-PAY-08** · Firmar `order_id` para evitar tampering
- [ ] **F2-PAY-09** · Anti-abuse trial (1 trial/usuario, fingerprint BIN+last4)
- [ ] **F2-PAY-10** · Eliminar `_TIER_LIMITS_DAY` de `usage.py` (duplicación)
- [ ] **F2-PAY-11** · Prorrateo en upgrade de plan

### F2-SUNAT — Facturación electrónica

- [x] **F2-SUNAT-02** · Campos en `Invoice`: `series`, `correlativo`, `tipo_documento`, `ruc_emisor`, `tipo_documento_cliente`, `numero_documento_cliente` (migración 020) — CLAUDE
- [!] **F2-SUNAT-01** · Decisión PSE/OSE (NubeFact / Efact / Lleida) — JAIME
- [ ] **F2-SUNAT-03** · IGV 18% explícito en `compute_invoice_amounts`
- [ ] **F2-SUNAT-04** · Generación PDF de factura electrónica
- [ ] **F2-SUNAT-05** · Endpoint `GET /billing/{org}/invoices/{id}/pdf`
- [ ] **F2-SUNAT-06** · Integración con PSE seleccionado

---

## FASE 3 — Post-deploy hardening

- [ ] **F3-SEC-01** · Row Level Security en Postgres
- [ ] **F3-SEC-02** · Política consistente soft-delete + purge job
- [ ] **F3-SEC-03** · Rotación de claves BYOK
- [ ] **F3-OPS-01** · Logs centralizados (Loki/Datadog)
- [ ] **F3-OPS-02** · Pipeline CD con tags + rollback automático
- [ ] **F3-OPS-03** · Réplicas horizontales del web
- [ ] **F3-OPS-04** · Restore tests automatizados quincenales
- [ ] **F3-LEG-01** · Cookie banner avanzado si llegan analytics
- [ ] **F3-UX-01** · Consolidar `InternalPageHeader` en todas las pantallas internas
- [ ] **F3-UX-02** · Accesibilidad: keyboard nav en cards, htmlFor en labels
- [ ] **F3-UX-03** · Manejo unificado 429/upsell en chat
- [ ] **F3-UX-04** · Progreso real de upload con porcentaje
- [ ] **F3-TEN-01** · Flujo de aceptación de invitación org

---

## Pendientes que requieren acción tuya

Estos están marcados `[!] JAIME` arriba y consolidados aquí para que no se te escapen:

1. **`.env.production`** — Generar y completar con secretos reales. Ver `deploy_guide.md` (entrega en este commit) para script con `python3 -c "import secrets; …"` y plantilla.
2. **VPS / Gateway** — Crear red `shared-gateway`, conectar `toroloco-gateway`, configurar upstreams `/api/*` → `api:8000` y `/*` → `web:3000`, abrir SSE en `/api/stream/*`.
3. **DNS** — Apuntar `tukijuris.com.pe` y `www.tukijuris.com.pe` al VPS; configurar MX/SPF/DKIM/DMARC para correos de Resend.
4. **Resend** — Verificar dominio `tukijuris.com.pe` y conseguir API key.
5. **Google Cloud Console** — Crear OAuth 2.0 Client; redirect URI `https://tukijuris.com.pe/auth/callback/google`; scopes `openid email profile`.
6. **Sentry** — Crear proyecto (FastAPI + Next.js), obtener DSNs (`SENTRY_DSN` para API, `NEXT_PUBLIC_SENTRY_DSN` para web).
7. **Uptime externo** — Healthchecks.io o UptimeRobot apuntando a `https://tukijuris.com.pe/api/health`.
8. **Multitenancy F1-TEN-01** — Decidir si refactorizamos `org_id` en `conversations/documents/uploads/memory/tags` antes o después de tener primeros clientes pagos.
9. **SUNAT F2-SUNAT-01** — Escoger PSE/OSE (NubeFact ~S/49/mes es el más popular para SaaS).
10. **Asset OG image 1200×630** — Para social previews.
11. **Cuenta CAPTCHA** — Cloudflare Turnstile (gratis) o hCaptcha; me pasas la public key cuando esté.
12. **Culqi (T+15d)** — Recibir credenciales sandbox y producción. Yo activo `NEXT_PUBLIC_CULQI_PUBLIC_KEY` y el AddCardModal swap.

---

## Riesgos conocidos / dependencias externas

- Culqi habilita en T+15 días. El flujo `/billing/checkout` ya muestra el modo "habilitando" en lugar de 404. Operamos con Free hasta entonces.
- Gateway externo `toroloco-gateway` lleva HSTS y `client_max_body_size`; confirmar que coincide con los headers que ya emite la API para no duplicar.
