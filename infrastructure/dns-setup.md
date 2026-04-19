# DNS Setup — tukijuris.net.pe

## Required DNS Records

| Type  | Name                 | Value                              | TTL  |
|-------|----------------------|------------------------------------|------|
| A     | tukijuris.net.pe     | <SERVER_IP>                        | 300  |
| A     | www.tukijuris.net.pe | <SERVER_IP>                        | 300  |
| CNAME | www                  | tukijuris.net.pe                   | 300  |
| TXT   | @                    | v=spf1 include:_spf.google.com ~all | 3600 |
| MX    | @                    | (if using email)                   | 3600 |

## Steps

1. Log into your domain registrar (where you bought tukijuris.net.pe)
2. Find DNS management settings
3. Add the A record pointing to your server IP
4. Add the www CNAME record
5. Wait for propagation (5-30 minutes for .net.pe)
6. Verify: `dig tukijuris.net.pe` should show your server IP

## After DNS is pointing:

1. Run `bash infrastructure/certbot/init-letsencrypt.sh`
2. Run `make prod-up`
3. Verify HTTPS works: `curl -I https://tukijuris.net.pe`

## Auto-renewal

Add to crontab: `0 3 * * * /path/to/infrastructure/certbot/renew-certs.sh`
