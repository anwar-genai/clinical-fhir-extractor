# Production Setup Guide

Complete guide for deploying the Clinical FHIR Extractor as a production-ready full-stack application.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React/Vite)  │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start (Development)

### 1. Backend Setup

```bash
# Install dependencies
uv sync

# Create .env file
cp .env.example .env
# Edit .env with your OpenAI API key and JWT secret

# Start backend
uv run python main.py
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🐳 Docker Deployment

### Option 1: Docker Compose (Recommended)

```bash
# Create .env file with production values
cat > .env << EOF
OPENAI_API_KEY=your-openai-api-key
JWT_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://postgres:password@db:5432/clinical_fhir
EOF

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Option 2: Individual Docker Containers

```bash
# Build backend
docker build -t clinical-fhir-api .

# Build frontend
cd frontend
docker build -t clinical-fhir-frontend .

# Run with docker-compose
docker-compose up -d
```

## ☁️ Cloud Deployment

### AWS Deployment

#### 1. Backend (AWS ECS/Fargate)

```yaml
# task-definition.json
{
  "family": "clinical-fhir-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/clinical-fhir-api:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "OPENAI_API_KEY", "value": "your-key"},
        {"name": "JWT_SECRET_KEY", "value": "your-secret"},
        {"name": "DATABASE_URL", "value": "postgresql://..."}
      ]
    }
  ]
}
```

#### 2. Frontend (AWS S3 + CloudFront)

```bash
# Build frontend
cd frontend
npm run build

# Upload to S3
aws s3 sync dist/ s3://your-bucket-name --delete

# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

#### 3. Database (AWS RDS)

```bash
# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier clinical-fhir-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password your-secure-password \
  --allocated-storage 20
```

### Google Cloud Platform

#### 1. Backend (Cloud Run)

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/clinical-fhir-api', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/clinical-fhir-api']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'clinical-fhir-api', '--image', 'gcr.io/$PROJECT_ID/clinical-fhir-api', '--platform', 'managed', '--region', 'us-central1']
```

#### 2. Frontend (Firebase Hosting)

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Build frontend
cd frontend
npm run build

# Deploy to Firebase
firebase deploy --only hosting
```

### Azure Deployment

#### 1. Backend (Azure Container Instances)

```bash
# Create resource group
az group create --name clinical-fhir-rg --location eastus

# Deploy container
az container create \
  --resource-group clinical-fhir-rg \
  --name clinical-fhir-api \
  --image your-registry/clinical-fhir-api:latest \
  --ports 8000 \
  --environment-variables \
    OPENAI_API_KEY=your-key \
    JWT_SECRET_KEY=your-secret
```

#### 2. Frontend (Azure Static Web Apps)

```bash
# Install Azure CLI
npm install -g @azure/static-web-apps-cli

# Deploy
swa deploy --app-location frontend/dist --output-location .
```

## 🔧 Production Configuration

### Environment Variables

```bash
# Backend (.env)
OPENAI_API_KEY=sk-your-actual-openai-key
JWT_SECRET_KEY=your-64-character-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
RATE_LIMIT_PER_MINUTE=100
DEBUG=false

# Frontend (.env)
VITE_API_URL=https://api.yourdomain.com
VITE_DEBUG=false
```

### Security Checklist

- [ ] **Change JWT_SECRET_KEY** to a secure random string (64+ chars)
- [ ] **Use HTTPS** for all communications
- [ ] **Configure CORS** to specific domains only
- [ ] **Set up SSL certificates** (Let's Encrypt recommended)
- [ ] **Enable database encryption** at rest
- [ ] **Configure firewall rules** (only necessary ports)
- [ ] **Set up monitoring** and alerting
- [ ] **Enable audit logging** to secure storage
- [ ] **Implement backup strategy** for database
- [ ] **Set up rate limiting** and DDoS protection

### Database Setup (PostgreSQL)

```sql
-- Create database
CREATE DATABASE clinical_fhir;

-- Create user
CREATE USER fhir_user WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE clinical_fhir TO fhir_user;

-- Enable extensions
\c clinical_fhir;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Nginx Configuration (Reverse Proxy)

```nginx
# /etc/nginx/sites-available/clinical-fhir
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        root /var/www/clinical-fhir-frontend;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

## 📊 Monitoring & Observability

### Application Monitoring

```python
# Add to app/main.py
import time
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Health Checks

```python
# Add to app/main.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.2.0"
    }

@app.get("/readiness")
async def readiness_check():
    # Check database connection
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database not ready")
```

### Logging Configuration

```python
# Add to app/main.py
import logging
from pythonjsonlogger import jsonlogger

# Configure structured logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: |
          pip install -r requirements.txt
          pytest

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      # Build and push Docker images
      - name: Build API
        run: docker build -t ${{ secrets.REGISTRY }}/clinical-fhir-api:${{ github.sha }} .
      
      - name: Build Frontend
        run: |
          cd frontend
          docker build -t ${{ secrets.REGISTRY }}/clinical-fhir-frontend:${{ github.sha }} .
      
      # Deploy to production
      - name: Deploy
        run: |
          docker-compose -f docker-compose.prod.yml up -d
```

## 🚨 Backup & Recovery

### Database Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/clinical-fhir"
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > $BACKUP_DIR/backup_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +30 -delete
```

### Disaster Recovery

1. **Database Recovery**
   ```bash
   # Restore from backup
   psql $DATABASE_URL < backup_20240115_120000.sql
   ```

2. **Application Recovery**
   ```bash
   # Redeploy from latest image
   docker-compose down
   docker-compose pull
   docker-compose up -d
   ```

## 📈 Performance Optimization

### Backend Optimizations

```python
# Add connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)

# Add Redis caching
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiry=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiry, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### Frontend Optimizations

```typescript
// Add service worker for caching
// public/sw.js
const CACHE_NAME = 'clinical-fhir-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});
```

## 🔐 Security Hardening

### SSL/TLS Configuration

```nginx
# Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

### Security Headers

```python
# Add to app/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## 📞 Support & Maintenance

### Monitoring Setup

1. **Application Performance Monitoring (APM)**
   - New Relic, DataDog, or Sentry
   - Track response times, error rates, throughput

2. **Infrastructure Monitoring**
   - CPU, memory, disk usage
   - Database performance metrics
   - Network latency

3. **Log Aggregation**
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Centralized logging for debugging

### Maintenance Tasks

- **Weekly**: Review audit logs, check system health
- **Monthly**: Update dependencies, security patches
- **Quarterly**: Performance review, capacity planning
- **Annually**: Security audit, disaster recovery testing

---

## 🎯 Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups scheduled
- [ ] Monitoring and alerting configured
- [ ] Security headers implemented
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Error handling and logging
- [ ] Performance optimizations
- [ ] Disaster recovery plan
- [ ] Documentation updated
- [ ] Team training completed

**Your Clinical FHIR Extractor is now production-ready! 🚀**
