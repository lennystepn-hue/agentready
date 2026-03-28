#!/bin/bash
# AgentReady deployment script for Hetzner VPS
# Usage: ssh into VPS, clone repo, run this script

set -e

echo "=== AgentReady Deployment ==="

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Install docker-compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing docker-compose..."
    apt-get install -y docker-compose-plugin
fi

# Build and start
echo "Building containers..."
docker compose build

# Start without SSL first (for certbot)
echo "Starting services..."
docker compose up -d

# Get SSL certificate
echo "Obtaining SSL certificate..."
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    -d agentcheck.site \
    -d www.agentcheck.site \
    --email noreply@agentcheck.site \
    --agree-tos \
    --no-eff-email

# Restart nginx with SSL
docker compose restart nginx

echo "=== Deployment complete ==="
echo "Visit https://agentcheck.site"
