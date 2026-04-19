#!/bin/bash
# Renew Let's Encrypt certificates and reload nginx
# Add to crontab: 0 3 * * * /path/to/renew-certs.sh

docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v /var/www/certbot:/var/www/certbot \
    certbot/certbot renew --quiet

# Reload nginx to pick up new certs
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload

echo "$(date): Certificate renewal check completed" >> /var/log/certbot-renew.log
