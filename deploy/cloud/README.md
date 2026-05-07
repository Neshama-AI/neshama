# Neshama Cloud Deployment

Deploy the Neshama backend to any cloud server using Docker.

## Quick Start

```bash
# 1. Clone and enter the deploy directory
cd deploy/cloud

# 2. Copy environment template and edit
cp .env.example .env
nano .env

# 3. Start the service
docker compose up -d

# 4. Verify
curl http://localhost:8420/health
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────┐
│  Game Client │────▶│  Neshama API │────▶│  Redis  │
│ (Unity/UE)   │◀────│  (FastAPI)   │     │ (cache) │
└─────────────┘     └──────┬───────┘     └─────────┘
                           │
                    ┌──────▼───────┐
                    │  LLM Provider │
                    │ (OpenAI etc.) │
                    └──────────────┘
```

## Docker Compose

The `docker-compose.yml` includes:
- **neshama-api**: FastAPI application (port 8420)
- **redis**: Optional cache for sessions and rate limiting (port 6379)

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NESHAMA_HOST` | No | `0.0.0.0` | Listen address |
| `NESHAMA_PORT` | No | `8420` | Listen port |
| `NESHAMA_JWT_SECRET` | **Yes** | - | Secret key for JWT tokens |
| `NESHAMA_ADMIN_KEY` | **Yes** | - | Admin API key for management |
| `NESHAMA_LLM_PROVIDER` | No | `openai` | Default LLM provider |
| `NESHAMA_LLM_API_KEY` | **Yes** | - | LLM provider API key |
| `NESHAMA_LLM_MODEL` | No | `gpt-4o-mini` | Default model name |
| `NESHAMA_REDIS_URL` | No | `redis://redis:6379` | Redis connection URL |
| `NESHAMA_FREE_CONVERSATIONS` | No | `1000` | Free tier monthly conversations |
| `NESHAMA_TRIAL_CONVERSATIONS` | No | `50` | Trial mode conversations |
| `NESHAMA_TRIAL_EXPIRY_HOURS` | No | `24` | Trial token expiry in hours |
| `NESHAMA_CORS_ORIGINS` | No | `*` | CORS allowed origins |

## Production Deployment

### TLS/SSL

Use a reverse proxy (nginx/Caddy) for TLS termination:

```nginx
server {
    listen 443 ssl;
    server_name api.neshama.ai;

    ssl_certificate /etc/letsencrypt/live/api.neshama.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.neshama.ai/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8420;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Scaling

```bash
# Scale API instances
docker compose up -d --scale neshama-api=3

# Use external Redis for production
# Set NESHAMA_REDIS_URL in .env
```

### Health Checks

```bash
# Basic health
curl http://localhost:8420/health

# Detailed health
curl http://localhost:8420/health/detailed
```

## Monitoring

- Health endpoint: `GET /health`
- Detailed health: `GET /health/detailed` (requires admin key)
- Docker logs: `docker compose logs -f neshama-api`

## Backup

```bash
# Backup billing data
docker compose exec neshama-api tar czf - /app/billing_data > backup_$(date +%Y%m%d).tar.gz
```
