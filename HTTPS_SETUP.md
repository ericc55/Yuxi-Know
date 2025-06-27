# HTTPS Setup for yuknow.net

This guide will help you set up HTTPS access for your application at `https://yuknow.net`.

## Prerequisites

1. **Domain Configuration**: Ensure that `yuknow.net` and `www.yuknow.net` are pointing to your server's IP address
2. **Port Access**: Make sure ports 80 and 443 are open and accessible from the internet
3. **Docker**: Docker and Docker Compose must be installed and running

## Quick Setup

Run the automated deployment script:

```bash
./scripts/deploy-https.sh
```

This script will:
- Stop existing services
- Start core services (API, web, database services)
- Initialize SSL certificates via Let's Encrypt
- Start nginx reverse proxy with HTTPS

## Manual Setup (if needed)

If you prefer to set up manually:

1. **Start core services**:
   ```bash
   docker compose up -d api web graph etcd minio milvus
   ```

2. **Initialize SSL certificates**:
   ```bash
   ./scripts/init-letsencrypt.sh
   ```

3. **Start nginx**:
   ```bash
   docker compose up -d nginx certbot
   ```

## Configuration Details

### Nginx Configuration
- **HTTP (port 80)**: Redirects all traffic to HTTPS
- **HTTPS (port 443)**: Serves your application with SSL
- **Let's Encrypt**: Handles automatic certificate renewal

### Services
- **nginx**: Reverse proxy handling SSL termination
- **certbot**: Automatic SSL certificate management
- **web**: Your frontend application (Vue.js with Vite)
- **api**: Your backend API

### URL Structure
- `https://yuknow.net/` → Web application
- `https://yuknow.net/api/` → API endpoints

## Verification

After setup, verify your installation:

1. **Check services**:
   ```bash
   docker compose ps
   ```

2. **Check logs**:
   ```bash
   docker compose logs nginx
   docker compose logs certbot
   ```

3. **Test access**:
   - Visit `https://yuknow.net` in your browser
   - Verify SSL certificate is valid

## Troubleshooting

### Certificate Issues
- Check Let's Encrypt rate limits (5 certificates per domain per week)
- For testing, edit `scripts/init-letsencrypt.sh` and set `staging=1`

### Connection Issues
- Verify domain DNS is pointing to your server
- Check firewall rules for ports 80 and 443
- Ensure services are running: `docker compose ps`

### Service Logs
```bash
# Check nginx logs
docker compose logs nginx

# Check certbot logs  
docker compose logs certbot

# Check application logs
docker compose logs web
docker compose logs api
```

## Certificate Renewal

Certificates automatically renew every 12 hours via the certbot container. Manual renewal:

```bash
docker compose exec certbot certbot renew
docker compose exec nginx nginx -s reload
```

## Security Features

The nginx configuration includes:
- HTTPS redirect for all HTTP traffic
- Modern TLS protocols (1.2, 1.3)
- Security headers (HSTS, X-Frame-Options, etc.)
- WebSocket support for Vite HMR

## Notes

- First-time certificate generation may take a few minutes
- Let's Encrypt has rate limits - use staging for testing
- Certificates are valid for 90 days and auto-renew 