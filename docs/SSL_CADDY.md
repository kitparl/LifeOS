# SSL / Production Deployment with Caddy

> **Note**: This is a deferred appendix. SSL setup is not part of the current redesign sprint.

## Prerequisites
- Ubuntu VPS (22.04+)
- Domain name pointing to your VPS IP
- LifeOS backend running on `localhost:8000`
- LifeOS frontend built to `backend/static/` (served by FastAPI)

## Install Caddy

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy
```

## Caddyfile

Create `/etc/caddy/Caddyfile`:

```caddyfile
yourdomain.com {
    # Automatic HTTPS — Caddy handles cert issuance/renewal via Let's Encrypt
    
    # Reverse proxy to FastAPI backend (which also serves the Angular SPA)
    reverse_proxy localhost:8000
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }
    
    # Compression
    encode gzip
}

# HTTP → HTTPS redirect is automatic with Caddy
```

## Environment variables

In your `.env` file (backend):
```env
COOKIE_SECURE=true
CORS_ORIGINS=https://yourdomain.com
```

## Start services

```bash
# Reload Caddy config
sudo systemctl reload caddy

# Verify status
sudo systemctl status caddy
```

## FastAPI / uvicorn (via systemd)

Create `/etc/systemd/system/lifeos.service`:
```ini
[Unit]
Description=LifeOS FastAPI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/LifeOS/backend
EnvironmentFile=/home/ubuntu/LifeOS/backend/.env
ExecStart=/home/ubuntu/LifeOS/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable lifeos
sudo systemctl start lifeos
```

## Build and deploy frontend

```bash
cd /home/ubuntu/LifeOS/frontend
npm run build
# Angular builds to dist/ — configure angular.json outputPath to backend/static
```

> Make sure `STATIC_DIR` in backend's `config.py` points to `backend/static`.
