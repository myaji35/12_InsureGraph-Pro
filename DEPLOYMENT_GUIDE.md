# Deployment Guide: Vercel + GCP Cloud Run

**Frontend**: Vercel
**Backend**: GCP Cloud Run
**Created**: 2025-11-28

---

## 🎯 Architecture Overview

```
┌──────────────────────┐         ┌───────────────────────┐
│  Vercel              │  HTTPS  │  GCP Cloud Run        │
│  insuregraph.vercel  │ ───────>│  Backend API          │
│  .app                │         │  (Cloud SQL, Neo4j)   │
└──────────────────────┘         └───────────────────────┘
```

---

## 📋 Prerequisites

### Required Accounts
- ✅ Google Cloud Platform account
- ✅ Vercel account (connected to GitHub)
- ✅ GitHub repository

### Required Tools
```bash
# GCP CLI
gcloud --version

# Vercel CLI
npm i -g vercel
vercel --version

# Node.js & npm
node --version
npm --version
```

---

## 🚀 Part 1: Backend Deployment (GCP Cloud Run)

### Step 1: GCP Project Setup

```bash
# 1. Set project
gcloud config set project insuregraph-dev

# 2. Enable required APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com
```

### Step 2: Create Production Environment Variables

Create secrets in Google Secret Manager:

```bash
# Navigate to backend
cd backend

# Create secrets (replace with actual values)
echo -n "your-actual-secret-key" | gcloud secrets create SECRET_KEY --data-file=-
echo -n "your-jwt-secret-key" | gcloud secrets create JWT_SECRET_KEY --data-file=-
echo -n "your-upstage-api-key" | gcloud secrets create UPSTAGE_API_KEY --data-file=-
echo -n "your-openai-api-key" | gcloud secrets create OPENAI_API_KEY --data-file=-
echo -n "your-postgres-password" | gcloud secrets create POSTGRES_PASSWORD --data-file=-
echo -n "your-neo4j-password" | gcloud secrets create NEO4J_PASSWORD --data-file=-
```

### Step 3: Deploy to Cloud Run

```bash
# Build and deploy
gcloud run deploy insuregraph-backend \
  --source . \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars "ENVIRONMENT=production,DEBUG=false" \
  --set-secrets "SECRET_KEY=SECRET_KEY:latest,JWT_SECRET_KEY=JWT_SECRET_KEY:latest,UPSTAGE_API_KEY=UPSTAGE_API_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest"
```

### Step 4: Get Backend URL

```bash
# Get the deployed URL
gcloud run services describe insuregraph-backend \
  --region asia-northeast3 \
  --format 'value(status.url)'
```

**Example Output**: `https://insuregraph-backend-xxxxx-an.a.run.app`

**Save this URL** - you'll need it for frontend configuration!

---

## 🌐 Part 2: Frontend Deployment (Vercel)

### Step 1: Update Frontend Environment

```bash
cd frontend

# Create .env.production
cat > .env.production << 'EOF'
# Backend API URL (replace with your Cloud Run URL)
NEXT_PUBLIC_API_URL=https://insuregraph-backend-xxxxx-an.a.run.app

# App Configuration
NEXT_PUBLIC_APP_NAME=InsureGraph Pro
NEXT_PUBLIC_APP_ENV=production
EOF
```

### Step 2: Update CORS in Backend

**Important**: After getting Vercel URL, update backend CORS settings.

Add to GCP Secret Manager or Cloud Run environment:

```bash
# After first Vercel deployment, update CORS
gcloud run services update insuregraph-backend \
  --region asia-northeast3 \
  --update-env-vars "CORS_ORIGINS=https://insuregraph-pro.vercel.app,https://insuregraph-pro-*.vercel.app"
```

### Step 3: Deploy to Vercel

**Method 1: CLI (Recommended for first deployment)**

```bash
cd frontend

# Login to Vercel
vercel login

# Deploy to production
vercel --prod
```

**Method 2: Git Push (Auto-deploy)**

```bash
# Push to main branch
git add .
git commit -m "chore: Configure production deployment"
git push origin main

# Vercel will auto-deploy if connected to GitHub
```

### Step 4: Configure Vercel Project

In Vercel Dashboard:
1. Go to Project Settings
2. Environment Variables
3. Add:
   - `NEXT_PUBLIC_API_URL` = `https://insuregraph-backend-xxxxx-an.a.run.app`

---

## 🔐 Security Checklist

### Backend (GCP Cloud Run)

- [x] Use Secret Manager for sensitive data
- [ ] Enable Cloud SQL Auth Proxy
- [ ] Configure VPC connector (if needed)
- [ ] Set up Cloud Armor (DDoS protection)
- [ ] Enable Cloud Logging
- [ ] Configure health checks

### Frontend (Vercel)

- [ ] Use environment variables for API URL
- [ ] Enable HTTPS only
- [ ] Configure security headers
- [ ] Set up Vercel Analytics (optional)

---

## 🧪 Testing Deployment

### 1. Test Backend Health

```bash
# Replace with your Cloud Run URL
curl https://insuregraph-backend-xxxxx-an.a.run.app/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {...}
}
```

### 2. Test Frontend

Visit your Vercel URL: `https://insuregraph-pro.vercel.app`

### 3. Test CORS

Open browser console on Vercel URL and run:
```javascript
fetch('https://insuregraph-backend-xxxxx-an.a.run.app/api/v1/')
  .then(res => res.json())
  .then(console.log)
```

Should return API info without CORS errors.

---

## 📊 Monitoring & Logs

### Backend Logs (GCP)

```bash
# View logs
gcloud run logs read insuregraph-backend \
  --region asia-northeast3 \
  --limit 50

# Stream logs
gcloud run logs tail insuregraph-backend \
  --region asia-northeast3
```

### Frontend Logs (Vercel)

Visit: `https://vercel.com/your-project/logs`

---

## 💰 Cost Estimation

### GCP Cloud Run

**Free Tier**:
- 2 million requests/month
- 360,000 GB-seconds compute
- 180,000 vCPU-seconds

**Estimated Cost** (after free tier):
- ~$10-30/month for small traffic
- ~$50-100/month for medium traffic

### Vercel

**Free (Hobby) Plan**:
- 100 GB bandwidth/month
- Unlimited requests
- 100 GB-hours compute

**Pro Plan** ($20/month):
- 1 TB bandwidth
- Advanced analytics

---

## 🔄 Continuous Deployment

### Auto-deploy on Git Push

**Backend (GCP)**:
Create Cloud Build trigger:

```yaml
# cloudbuild.yaml (already exists in backend/)
steps:
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'insuregraph-backend'
      - '--source=.'
      - '--region=asia-northeast3'
      - '--platform=managed'
```

**Frontend (Vercel)**:
- Auto-configured when connecting GitHub
- Deploys on push to `main` branch

---

## 🆘 Troubleshooting

### Backend Won't Start

```bash
# Check logs
gcloud run logs read insuregraph-backend --region asia-northeast3

# Common issues:
# 1. Missing environment variables
# 2. Database connection timeout
# 3. Port binding (must use PORT=8080)
```

### CORS Errors

```bash
# Update CORS origins
gcloud run services update insuregraph-backend \
  --region asia-northeast3 \
  --set-env-vars "CORS_ORIGINS=https://your-vercel-url.vercel.app"
```

### Frontend Can't Connect to Backend

1. Check `NEXT_PUBLIC_API_URL` in Vercel env vars
2. Verify backend is accessible: `curl <backend-url>/api/v1/health`
3. Check browser console for CORS errors

---

## 📝 Next Steps

After successful deployment:

1. **Setup Custom Domain** (Optional)
   - Backend: `api.insuregraph.com`
   - Frontend: `insuregraph.com`

2. **Configure Cloud SQL**
   - Create PostgreSQL instance
   - Enable Cloud SQL Auth Proxy
   - Update connection string

3. **Setup Monitoring**
   - Cloud Monitoring dashboards
   - Alerting rules
   - Uptime checks

4. **Enable CI/CD**
   - Cloud Build triggers
   - Automated testing
   - Staging environment

---

## 🎯 Quick Commands Reference

```bash
# Backend: Deploy
gcloud run deploy insuregraph-backend --source . --region asia-northeast3

# Backend: View logs
gcloud run logs tail insuregraph-backend --region asia-northeast3

# Backend: Update env vars
gcloud run services update insuregraph-backend \
  --region asia-northeast3 \
  --set-env-vars "KEY=value"

# Frontend: Deploy
vercel --prod

# Frontend: View deployment
vercel ls

# Frontend: Check logs
vercel logs
```

---

**Last Updated**: 2025-11-28
**Status**: Ready for deployment
