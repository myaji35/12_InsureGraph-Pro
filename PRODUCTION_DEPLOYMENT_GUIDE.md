# InsureGraph Pro - Production Deployment Guide

**Last Updated**: 2025-12-01
**Version**: 1.0.0

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Database Migration](#database-migration)
3. [Environment Variables](#environment-variables)
4. [PWA Icons](#pwa-icons)
5. [Backend Deployment (GCP Cloud Run)](#backend-deployment)
6. [Frontend Deployment (Vercel)](#frontend-deployment)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Rollback Plan](#rollback-plan)

---

## 🔍 Pre-Deployment Checklist

### Required Before Deployment:

- [ ] All tests passing
- [ ] Database migrations prepared
- [ ] Environment variables documented
- [ ] PWA icons generated
- [ ] Backend build successful
- [ ] Frontend build successful
- [ ] Production credentials ready

---

## 💾 Database Migration

### Step 1: Run Migrations

All database migrations must be applied in order:

```bash
cd backend

# 1. Customers tables (if not already applied)
./scripts/apply_migration.sh alembic/versions/004_add_customers_tables.sql

# 2. Query history table (NEW - from Task A)
./scripts/apply_migration.sh alembic/versions/005_add_query_history_table.sql
```

### Step 2: Verify Migrations

```sql
-- Connect to your production database
-- PostgreSQL
\dt

-- Should see these tables:
-- - users
-- - customers
-- - customer_policies
-- - query_history
-- - ingestion_jobs
-- - documents

-- Verify query_history structure
\d query_history

-- Should have columns:
-- - id (UUID)
-- - user_id (UUID)
-- - customer_id (UUID, nullable)
-- - query_text (TEXT)
-- - intent (VARCHAR)
-- - answer (TEXT)
-- - confidence (DECIMAL)
-- - source_documents (JSONB)
-- - reasoning_path (JSONB)
-- - execution_time_ms (INTEGER)
-- - created_at (TIMESTAMP)
```

### Migration Scripts Location

- `backend/alembic/versions/004_add_customers_tables.sql`
- `backend/alembic/versions/005_add_query_history_table.sql`

---

## 🔐 Environment Variables

### Backend (`backend/.env.production`)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/insuregraph_prod

# JWT Authentication
SECRET_KEY=<generate-secure-random-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OpenAI (for LLM reasoning)
OPENAI_API_KEY=sk-...

# Neo4j (for GraphRAG)
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<secure-password>

# GCS (for document storage)
GCS_BUCKET_NAME=insuregraph-documents-prod
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# CORS
ALLOWED_ORIGINS=https://insuregraph-pro.vercel.app,https://www.yourdomain.com

# Environment
ENVIRONMENT=production
DEBUG=false
```

### Generate SECRET_KEY

```python
# Run this in Python
import secrets
print(secrets.token_urlsafe(32))
```

### Frontend (`frontend/.env.production`)

```bash
# API URL
NEXT_PUBLIC_API_URL=https://your-backend-domain.com

# Clerk (if using)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...

# Environment
NEXT_PUBLIC_ENVIRONMENT=production
```

---

## 🎨 PWA Icons

### Required Icons:

1. **icon-192x192.png** (192x192px)
2. **icon-512x512.png** (512x512px)

### Location:
- `frontend/public/icon-192x192.png`
- `frontend/public/icon-512x512.png`

### Design Guidelines:

- **Background**: Transparent or #0ea5e9 (primary color)
- **Content**: InsureGraph Pro logo or "IG" monogram
- **Style**: Modern, professional
- **Format**: PNG with transparency

### Tools for Generation:

#### Option 1: Figma/Sketch
1. Create 512x512px artboard
2. Design icon
3. Export as PNG (192x192 and 512x512)

#### Option 2: PWA Asset Generator
```bash
cd frontend

# If you have a logo.svg or logo.png
npx pwa-asset-generator logo.svg public --icon-only --path-override /

# This will generate:
# - icon-192x192.png
# - icon-512x512.png
# - icon-384x384.png (bonus)
```

#### Option 3: Favicon Generator
- Visit: https://realfavicongenerator.net/
- Upload your logo
- Download PWA icons package

### Temporary Solution:

If you need to deploy urgently without custom icons:

```bash
cd frontend/public

# Create placeholder icons (solid color)
# Use any image editing tool or online generator
# Ensure they are 192x192 and 512x512
```

### Verification:

After generating icons, verify in `manifest.json`:

```json
{
  "icons": [
    {
      "src": "/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

---

## 🚀 Backend Deployment (GCP Cloud Run)

### Step 1: Build Docker Image

```bash
cd backend

# Build for production
docker build -f Dockerfile -t insuregraph-backend:latest .

# Tag for GCR
docker tag insuregraph-backend:latest gcr.io/YOUR_PROJECT_ID/insuregraph-backend:latest

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/insuregraph-backend:latest
```

### Step 2: Deploy to Cloud Run

```bash
gcloud run deploy insuregraph-backend \
  --image gcr.io/YOUR_PROJECT_ID/insuregraph-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=$DATABASE_URL,SECRET_KEY=$SECRET_KEY,..." \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10
```

### Step 3: Configure Service Account

```bash
# Create service account for GCS access
gcloud iam service-accounts create insuregraph-backend

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member serviceAccount:insuregraph-backend@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role roles/storage.objectAdmin
```

### Alternative: Using Existing Config

If you have `backend/cloudbuild.yaml`:

```bash
cd backend
gcloud builds submit --config cloudbuild.yaml
```

---

## 🌐 Frontend Deployment (Vercel)

### Step 1: Connect GitHub Repository

1. Go to https://vercel.com
2. Click "New Project"
3. Import your GitHub repository
4. Select `frontend` as root directory

### Step 2: Configure Build Settings

**Build Command**:
```bash
npm run build
```

**Output Directory**:
```bash
.next
```

**Install Command**:
```bash
npm install
```

### Step 3: Environment Variables

In Vercel dashboard, add:

- `NEXT_PUBLIC_API_URL`: Your backend URL (from Cloud Run)
- Other environment variables from `.env.production`

### Step 4: Deploy

```bash
# Manual deploy from local
cd frontend
vercel --prod

# Or push to main branch (auto-deploy)
git push origin main
```

### Custom Domain (Optional)

1. Vercel Dashboard → Project → Settings → Domains
2. Add your custom domain
3. Configure DNS records as instructed

---

## ✅ Post-Deployment Verification

### 1. Backend Health Check

```bash
curl https://your-backend-domain.com/api/v1/health

# Expected response:
{
  "status": "healthy",
  "neo4j_connected": true,
  "llm_available": true
}
```

### 2. Frontend Access

Visit: https://your-frontend-domain.com

- [ ] Homepage loads
- [ ] Login works
- [ ] Dashboard displays
- [ ] Query execution works
- [ ] Query history saves (check /query-history)
- [ ] Customer detail page works
- [ ] GA Manager view (if FP_MANAGER role)

### 3. PWA Verification

On mobile device:

1. Visit site
2. Look for "Add to Home Screen" prompt
3. Install app
4. Verify offline functionality
5. Check app icon on home screen

### 4. Database Verification

```sql
-- Check query history is being populated
SELECT COUNT(*) FROM query_history;

-- Check recent queries
SELECT query_text, intent, confidence, created_at
FROM query_history
ORDER BY created_at DESC
LIMIT 10;
```

### 5. Monitoring Setup

1. **Backend**: Cloud Run logs
   ```bash
   gcloud logging read "resource.type=cloud_run_revision" --limit 50
   ```

2. **Frontend**: Vercel Analytics
   - Check deployment logs
   - Monitor function invocations

3. **Database**: PostgreSQL monitoring
   - Connection pool
   - Query performance
   - Disk usage

---

## 🔄 Rollback Plan

### If Deployment Fails:

#### Backend Rollback

```bash
# List revisions
gcloud run revisions list --service insuregraph-backend

# Rollback to previous revision
gcloud run services update-traffic insuregraph-backend \
  --to-revisions=REVISION_NAME=100
```

#### Frontend Rollback

```bash
# In Vercel dashboard:
# 1. Go to Deployments
# 2. Find previous successful deployment
# 3. Click "Promote to Production"

# Or via CLI:
vercel rollback
```

#### Database Rollback

```sql
-- If migration fails, run rollback script
-- (Create rollback scripts for each migration)

-- Example for 005_add_query_history_table:
DROP TABLE IF EXISTS query_history CASCADE;
```

---

## 📊 Performance Benchmarks

### Expected Metrics:

- **Backend API Response**: < 500ms (p95)
- **Query Execution**: 2-5s (depends on LLM)
- **Dashboard Load**: < 2s
- **Lighthouse Score**: > 90

### Optimization Tips:

1. **Backend**:
   - Enable Redis caching for frequently accessed data
   - Optimize database queries with EXPLAIN ANALYZE
   - Use connection pooling

2. **Frontend**:
   - Enable Next.js caching
   - Optimize images
   - Lazy load non-critical components

---

## 🆘 Troubleshooting

### Common Issues:

#### 1. CORS Errors

**Symptom**: Frontend can't access backend API

**Solution**:
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2. Database Connection Fails

**Symptom**: Backend can't connect to PostgreSQL

**Solution**:
- Check DATABASE_URL format
- Verify firewall rules (allow Cloud Run IP ranges)
- Check service account permissions

#### 3. PWA Not Installing

**Symptom**: No "Add to Home Screen" prompt

**Solution**:
- Verify manifest.json is accessible
- Check icon files exist
- Ensure HTTPS is enabled
- Check browser console for errors

#### 4. Query History Not Saving

**Symptom**: /query-history shows no data

**Solution**:
- Check migration 005 was applied
- Verify user authentication is working
- Check backend logs for save errors
- Ensure database has write permissions

---

## 📞 Support

For deployment issues:

1. Check logs:
   - Backend: Cloud Run logs
   - Frontend: Vercel deployment logs
   - Database: PostgreSQL logs

2. Review documentation:
   - `backend/DEPLOYMENT_GUIDE.md`
   - `frontend/README.md`

3. Common commands:
   ```bash
   # Backend logs
   gcloud logging tail --service insuregraph-backend

   # Frontend logs
   vercel logs

   # Database connection test
   psql $DATABASE_URL -c "SELECT 1"
   ```

---

## ✅ Deployment Checklist

### Pre-Deployment

- [ ] All migrations tested locally
- [ ] Environment variables documented
- [ ] PWA icons generated
- [ ] Tests passing
- [ ] Code reviewed and merged to main

### Deployment

- [ ] Database migrations applied
- [ ] Backend deployed to Cloud Run
- [ ] Frontend deployed to Vercel
- [ ] Environment variables set
- [ ] Custom domains configured (if applicable)

### Post-Deployment

- [ ] Health checks passing
- [ ] Frontend accessible
- [ ] Authentication working
- [ ] Query execution working
- [ ] Query history saving
- [ ] PWA installable
- [ ] Monitoring configured
- [ ] Team notified

---

**Deployment Status**: Ready ✅
**Estimated Time**: 1-2 hours (excluding icon generation)
**Risk Level**: Low (existing infrastructure)

---

*Generated with Claude Code - 2025-12-01*
