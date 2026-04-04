#!/bin/bash
# Initialize Let's Encrypt SSL certificates for tukijuris.net.pe
# Run ONCE on the production server before starting nginx with HTTPS

set -e

DOMAIN="tukijuris.net.pe"
EMAIL="admin@tukijuris.net.pe"  # Change to real email
STAGING=0  # Set to 1 for testing (avoids rate limits)

echo "=== Requesting SSL certificate for $DOMAIN ==="

# Create required directories
mkdir -p /var/www/certbot
mkdir -p /etc/letsencrypt

# Request certificate
if [ "$STAGING" = "1" ]; then
    STAGING_ARG="--staging"
else
    STAGING_ARG=""
fi

docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v /var/www/certbot:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    $STAGING_ARG

echo "=== Certificate obtained! ==="
echo "Certificate: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
echo "Key: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
