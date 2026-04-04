#!/bin/bash
# TukiJuris -- VPS Server Setup
# Run once on a fresh Ubuntu 22.04+ server
# Usage: sudo bash infrastructure/scripts/setup-server.sh

set -euo pipefail

echo "=== TukiJuris Server Setup ==="

# 1. System updates
apt update && apt upgrade -y

# 2. Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# 3. Install Docker Compose v2
apt install -y docker-compose-plugin

# 4. Create app user (non-root)
useradd -m -s /bin/bash -G docker tukijuris || true
echo "tukijuris ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/tukijuris

# 5. Security hardening

# Firewall
apt install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Fail2ban
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# SSH hardening (only change if not already set)
if grep -q "^#PasswordAuthentication yes" /etc/ssh/sshd_config; then
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
elif grep -q "^PasswordAuthentication yes" /etc/ssh/sshd_config; then
    sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
fi
systemctl restart sshd

# 6. Create app directory
mkdir -p /opt/tukijuris/app
chown tukijuris:tukijuris /opt/tukijuris/app

# 7. Create directories for volumes
mkdir -p /opt/tukijuris/backups
mkdir -p /var/www/certbot
chown -R tukijuris:tukijuris /opt/tukijuris

# 8. Install useful tools
apt install -y htop curl jq git certbot

# 9. Setup swap (2GB) -- idempotent
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap created: 2GB"
else
    echo "Swap already exists -- skipping"
fi

# 10. Set timezone
timedatectl set-timezone America/Lima

echo ""
echo "=== Server setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Clone repo: git clone <repo> /opt/tukijuris/app"
echo "  2. Copy .env: cp .env.production.example .env.production"
echo "  3. Edit .env.production with real values"
echo "  4. Run certbot: bash infrastructure/certbot/init-letsencrypt.sh"
echo "  5. Build: make prod-build"
echo "  6. Start: make prod-up"
