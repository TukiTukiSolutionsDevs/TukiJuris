# TukiJuris — Guía de despliegue a `tukijuris.com.pe`

> Esta guía consolida todo lo que necesitas para llevar el SaaS a producción.
> Compañera del `ROADMAP.md`. Léela linealmente: cada sección bloquea la siguiente.

---

## 0. Prerrequisitos en el host

- VPS con Docker y Docker Compose ≥ v2.
- `git` y `make` instalados.
- El gateway compartido `toroloco-gateway` ya levantado (nginx + certbot) y manejando SSL para otros sitios de Toroloco.
- Acceso DNS al dominio `tukijuris.com.pe`.
- Cuenta verificada en Resend con DKIM + SPF correctos.
- Cuenta en Google Cloud Console (para OAuth 2.0 Client).
- Sentry (opcional pero recomendado).

---

## 1. Generar `.env.production`

En tu máquina local:

```bash
cp .env.production.example .env.production

# Generar secretos
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
BYOK_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
INTERNAL_TICK_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

echo "JWT_SECRET=$JWT_SECRET"
echo "BYOK_ENCRYPTION_KEY=$BYOK_ENCRYPTION_KEY"
echo "INTERNAL_TICK_TOKEN=$INTERNAL_TICK_TOKEN"
echo "DB_PASSWORD=$DB_PASSWORD"
echo "REDIS_PASSWORD=$REDIS_PASSWORD"
```

Edita `.env.production` y rellena:

| Variable | Origen / cómo obtener |
|---|---|
| `JWT_SECRET` | Comando arriba |
| `BYOK_ENCRYPTION_KEY` | Comando arriba (Fernet 44 chars) |
| `INTERNAL_TICK_TOKEN` | Comando arriba |
| `DB_PASSWORD` + `REDIS_PASSWORD` | Comandos arriba |
| `DATABASE_URL` + `DATABASE_URL_SYNC` | Pegar el `DB_PASSWORD` en la URL |
| `REDIS_URL` | Pegar el `REDIS_PASSWORD` en la URL |
| `GOOGLE_OAUTH_CLIENT_ID/SECRET` | Google Cloud Console → APIs & Services → Credentials |
| `RESEND_API_KEY` | Resend dashboard |
| `SENTRY_DSN` | Sentry → Settings → Client Keys |
| `CULQI_*` | Vacío por ahora; lo recibes T+15d |
| `BETA_MODE` | `true` mientras Culqi no esté activo |
| `TRIALS_ENABLED` | `false` hasta que Culqi habilite |

Sube el archivo al VPS por SCP (NO commit a git):

```bash
scp .env.production user@vps:/opt/tukijuris/app/.env.production
chmod 600 /opt/tukijuris/app/.env.production
```

---

## 2. Red Docker compartida

En el VPS:

```bash
# Solo si no existe ya
docker network create shared-gateway

# Conectar el gateway externo a la misma red
docker network connect shared-gateway toroloco-gateway
```

> Verifica con `docker network inspect shared-gateway` que el gateway aparece.

---

## 3. DNS de `tukijuris.com.pe`

En tu registrador (NIC.pe / Cloudflare / etc.):

```
A      tukijuris.com.pe         <IP_VPS>      TTL 300
A      www.tukijuris.com.pe     <IP_VPS>      TTL 300
TXT    @                        v=spf1 include:_spf.resend.com ~all
TXT    resend._domainkey        <valor DKIM de Resend>
TXT    _dmarc                   v=DMARC1; p=quarantine; rua=mailto:postmaster@tukijuris.com.pe
```

Si en algún momento agregas subdominios (`api.tukijuris.com.pe`, etc.), recuerda mantener HSTS coherente con el gateway.

---

## 4. Google OAuth Client

1. https://console.cloud.google.com → APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID.
2. Application type: Web application.
3. Authorized JavaScript origins: `https://tukijuris.com.pe`.
4. Authorized redirect URIs: `https://tukijuris.com.pe/auth/callback/google`.
5. Copia `Client ID` y `Client secret` a `.env.production`.

OAuth consent screen → User type: External. Llena los campos de privacy/terms con `https://tukijuris.com.pe/privacy` y `/terms`.

---

## 5. Configuración del gateway (`toroloco-gateway`)

Agrega un server-block para `tukijuris.com.pe` con esta plantilla (ajusta a la realidad de tu nginx):

```nginx
server {
    listen 443 ssl http2;
    server_name tukijuris.com.pe www.tukijuris.com.pe;

    ssl_certificate     /etc/letsencrypt/live/tukijuris.com.pe/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tukijuris.com.pe/privkey.pem;

    client_max_body_size 12m;

    # SSE (chat streaming) — disable buffering, long read timeout
    location /api/stream/ {
        proxy_pass http://tukijuris-api:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        chunked_transfer_encoding off;
    }

    # All /api/* → API
    location /api/ {
        proxy_pass http://tukijuris-api:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header Host $host;
        proxy_read_timeout 60s;
    }

    # Everything else → web (Next.js)
    location / {
        proxy_pass http://tukijuris-web:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header Host $host;
    }
}

server {
    listen 80;
    server_name tukijuris.com.pe www.tukijuris.com.pe;
    return 301 https://tukijuris.com.pe$request_uri;
}
```

Recarga el gateway:

```bash
docker exec toroloco-gateway nginx -t
docker exec toroloco-gateway nginx -s reload
```

---

## 6. Build y arranque

En el VPS:

```bash
cd /opt/tukijuris/app
git pull origin main

# Build con build-args para que NEXT_PUBLIC_* queden baked
make prod-build

# Levantar
make prod-up

# Ver logs (bootstrap aplica migraciones)
make prod-logs
```

Espera la línea `[BOOT 100%] BOOT  Starting uvicorn on 0.0.0.0:8000` antes de pasar al siguiente paso.

---

## 7. Smoke tests post-arranque

```bash
# 1. API health
curl -s https://tukijuris.com.pe/api/health
# → {"status":"ok","service":"agente-derecho-api"}

# 2. Web responde
curl -sI https://tukijuris.com.pe/landing | head -3
# → HTTP/2 200

# 3. HSTS presente
curl -sI https://tukijuris.com.pe/api/health | grep -i strict-transport
# → strict-transport-security: max-age=31536000; includeSubDomains

# 4. Migración al día
make prod-current
# → 020_indexes_and_sunat_prep (head)

# 5. Tablas críticas
docker exec tukijuris-db psql -U $DB_USER -d $DB_NAME -c "\dt" | grep -E "users|organizations|invoices|trials|refresh_tokens|platform_llm_keys"

# 6. Forzar un 500 para verificar Sentry (cuando esté activo)
curl -s https://tukijuris.com.pe/api/no-existe
```

Luego, en el navegador:

- Visita `https://tukijuris.com.pe/landing` → debe verse la home.
- Pulsa "Comenzar gratis" → registro funciona.
- Pulsa "Términos" en el footer sin estar logueado → debe abrir `/terms` (no debe redirigir a login).
- Acepta el banner de cookies → desaparece y no vuelve.
- Loguéate → `/` carga el chat.
- Cambia el tema desde el sidebar → debe alternar.
- Ve a `/configuracion` → cambia tu contraseña → debe redirigir a `/auth/login`, no a un 404.

---

## 8. Activar Google OAuth

1. En `.env.production`, asegúrate que `GOOGLE_OAUTH_CLIENT_ID/SECRET` están seteados.
2. `make prod-down && make prod-up` para recargar.
3. En el navegador, intenta `Iniciar sesión con Google`. Debes ser redirigido a Google, autenticarte, y volver a `/chat`.

> Si el primer Google sign-in falla con `email_not_verified_at_idp`, significa que la cuenta de Google del usuario tiene `email_verified=false`. Es por diseño: lo bloqueamos para evitar account-takeover.

---

## 9. Cron jobs

```bash
make setup-cron
# Esto añade:
#   - Backup diario 02:00 → /opt/tukijuris/backups/
#   - (Legacy) renovación de certificados certbot — ignorable si el gateway maneja SSL
```

Verifica con `crontab -l`.

---

## 10. Uptime externo

Crea un check en Healthchecks.io o UptimeRobot:

- URL: `https://tukijuris.com.pe/api/health`
- Frecuencia: 5 min
- Alerta: email + Slack/Telegram

---

## 11. Cuando Culqi habilite (T+15d)

1. Recibe `pk_live_xxx`, `sk_live_xxx`, `whsec_xxx` del soporte Culqi.
2. Actualiza `.env.production`:
   ```
   CULQI_PUBLIC_KEY=pk_live_xxx
   CULQI_SECRET_KEY=sk_live_xxx
   CULQI_WEBHOOK_SECRET=whsec_xxx
   NEXT_PUBLIC_CULQI_PUBLIC_KEY=pk_live_xxx
   BETA_MODE=false
   TRIALS_ENABLED=true
   ```
3. En el dashboard Culqi, configura la URL del webhook: `https://tukijuris.com.pe/api/billing/webhook/culqi`.
4. `make prod-down && make prod-build && make prod-up` (rebuild para que `NEXT_PUBLIC_CULQI_PUBLIC_KEY` quede baked).
5. La página `/billing/checkout` ya no mostrará el modo "habilitando".

---

## 12. Rollback rápido

Si algo sale mal después de un deploy:

```bash
# Backup pre-deploy ya está en /opt/tukijuris/backups/
git checkout <commit-anterior>
make prod-build
make prod-down
make db-restore FILE=backups/tukijuris_YYYYMMDD_HHMMSS.dump
make prod-up
```

---

## Apéndice — Variables de entorno (referencia rápida)

| Variable | Crítica en prod | Ejemplo / fuente |
|---|---|---|
| `JWT_SECRET` | ✅ | 64 chars random |
| `BYOK_ENCRYPTION_KEY` | ✅ | Fernet 44 chars |
| `DB_PASSWORD` / `REDIS_PASSWORD` | ✅ | random 32+ chars |
| `DATABASE_URL` / `DATABASE_URL_SYNC` / `REDIS_URL` | ✅ | con pasword embebido |
| `INTERNAL_TICK_TOKEN` | ✅ | random 32 chars |
| `COOKIE_DOMAIN` | recomendado vacío para apex | "" o ".tukijuris.com.pe" si hay subdominios |
| `CORS_ORIGINS` | ✅ | `["https://tukijuris.com.pe","https://www.tukijuris.com.pe"]` |
| `FRONTEND_URL` | ✅ | `https://tukijuris.com.pe` |
| `NEXT_PUBLIC_API_URL` | ✅ (build-arg) | `https://tukijuris.com.pe` |
| `NEXT_PUBLIC_APP_URL` | ✅ (build-arg) | `https://tukijuris.com.pe` |
| `INTERNAL_API_URL` | ✅ | `http://api:8000` |
| `BETA_MODE` | ✅ explícito | `true` mientras Culqi no esté activo |
| `TRIALS_ENABLED` | ✅ explícito | `false` hasta Culqi |
| `SCHEDULER_ENABLED` | ✅ | `true` en la única instancia API |
| `GOOGLE_OAUTH_CLIENT_ID/SECRET` | opcional | desde Google Cloud Console |
| `RESEND_API_KEY` | recomendado | desde Resend dashboard |
| `SENTRY_DSN` | recomendado | desde Sentry |
| `CULQI_*` | T+15d | desde Culqi |
| `NEXT_PUBLIC_CULQI_PUBLIC_KEY` | T+15d (build-arg) | desde Culqi |
