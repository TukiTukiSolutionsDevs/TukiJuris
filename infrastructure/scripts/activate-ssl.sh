#!/bin/bash
# Activate TukiJuris SSL in the gateway nginx
# Run this after certbot obtains the certificate
set -e

NGINX_CONF="/root/torolococayma/ToroLocoCayma/docker/nginx/nginx.conf"
CERT_PATH="/root/torolococayma/ToroLocoCayma/docker/certbot/conf/live/tukijuris.net.pe/fullchain.pem"

# Check cert exists
if [ ! -f "$CERT_PATH" ]; then
    echo "ERROR: SSL certificate not found at $CERT_PATH"
    echo "Run certbot first:"
    echo '  docker run --rm -v /root/torolococayma/ToroLocoCayma/docker/certbot/conf:/etc/letsencrypt -v /root/torolococayma/ToroLocoCayma/docker/certbot/www:/var/www/certbot certbot/certbot certonly --webroot --webroot-path=/var/www/certbot -d tukijuris.net.pe -d www.tukijuris.net.pe --non-interactive --agree-tos --email admin@tukijuris.net.pe'
    exit 1
fi

echo "SSL cert found. Activating full HTTPS config..."

# Backup current config
cp "$NGINX_CONF" "${NGINX_CONF}.bak.$(date +%Y%m%d%H%M%S)"

echo "Restarting gateway..."
docker restart toroloco-gateway

sleep 3
if docker ps --filter name=toroloco-gateway --format '{{.Status}}' | grep -q "Up"; then
    echo "Gateway restarted successfully!"
    echo "TukiJuris is now live at https://tukijuris.net.pe"
else
    echo "ERROR: Gateway failed to start. Check logs:"
    echo "  docker logs toroloco-gateway --tail 20"
fi
