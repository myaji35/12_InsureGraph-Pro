# GCP Infrastructure Setup Guide

**Project**: InsureGraph Pro
**Cloud Provider**: Google Cloud Platform (GCP)
**Region**: asia-northeast3 (Seoul)
**Environment**: Development → Staging → Production
**Version**: 1.0
**Date**: 2025-11-25

---

## 📋 Overview

This guide provides step-by-step instructions to set up the InsureGraph Pro infrastructure on Google Cloud Platform, replacing the AWS architecture with GCP equivalents.

### GCP Service Mapping (AWS → GCP)

| AWS Service | GCP Equivalent | Purpose |
|-------------|----------------|---------|
| **EKS** | GKE (Google Kubernetes Engine) | Container orchestration |
| **RDS PostgreSQL** | Cloud SQL for PostgreSQL | Metadata database |
| **EC2/RDS (Neo4j)** | Compute Engine (Neo4j) | Graph database |
| **ElastiCache Redis** | Memorystore for Redis | Caching layer |
| **S3** | Cloud Storage | Object storage (PDFs, reports) |
| **KMS** | Cloud KMS | Encryption key management |
| **CloudWatch** | Cloud Monitoring + Cloud Logging | Observability |
| **WAF** | Cloud Armor | Web application firewall |
| **CloudFront** | Cloud CDN | Content delivery |
| **ALB** | Cloud Load Balancing | Load balancing |
| **VPC** | VPC (same name) | Network isolation |
| **IAM** | IAM (same name) | Identity & access management |

---

## 🚀 Prerequisites

### Required Accounts & Permissions

1. **GCP Account**
   - Billing account enabled
   - Organization or project admin access
   - Quota sufficient for:
     - 20 vCPUs (Compute Engine)
     - 100 GB disk (Cloud SQL + Compute)
     - 500 GB Cloud Storage

2. **Required APIs to Enable**
   ```bash
   gcloud services enable compute.googleapis.com
   gcloud services enable container.googleapis.com
   gcloud services enable sqladmin.googleapis.com
   gcloud services enable cloudkms.googleapis.com
   gcloud services enable storage-api.googleapis.com
   gcloud services enable redis.googleapis.com
   gcloud services enable monitoring.googleapis.com
   gcloud services enable logging.googleapis.com
   ```

3. **Local Tools**
   - `gcloud` CLI (v450.0.0+)
   - `kubectl` (v1.28+)
   - `terraform` (v1.6+) - optional but recommended
   - `docker` (v24.0+)

---

## 📂 Project Structure

### GCP Projects

We recommend 3 separate GCP projects for isolation:

```
insuregraph-dev       (Development)
insuregraph-staging   (Staging)
insuregraph-prod      (Production)
```

**Setup**:
```bash
# Set project ID variables
export PROJECT_ID_DEV="insuregraph-dev"
export PROJECT_ID_STAGING="insuregraph-staging"
export PROJECT_ID_PROD="insuregraph-prod"
export ORGANIZATION_ID="YOUR_ORG_ID"  # Get from: gcloud organizations list

# Create projects
gcloud projects create $PROJECT_ID_DEV --organization=$ORGANIZATION_ID --name="InsureGraph Pro Dev"
gcloud projects create $PROJECT_ID_STAGING --organization=$ORGANIZATION_ID --name="InsureGraph Pro Staging"
gcloud projects create $PROJECT_ID_PROD --organization=$ORGANIZATION_ID --name="InsureGraph Pro Prod"

# Link billing account
export BILLING_ACCOUNT_ID="YOUR_BILLING_ACCOUNT_ID"  # Get from: gcloud billing accounts list
gcloud billing projects link $PROJECT_ID_DEV --billing-account=$BILLING_ACCOUNT_ID
gcloud billing projects link $PROJECT_ID_STAGING --billing-account=$BILLING_ACCOUNT_ID
gcloud billing projects link $PROJECT_ID_PROD --billing-account=$BILLING_ACCOUNT_ID

# Set default project (Dev)
gcloud config set project $PROJECT_ID_DEV
```

---

## 🌐 Step 1: VPC Network Setup

### Create VPC with Subnets

```bash
# Create VPC
gcloud compute networks create insuregraph-vpc \
    --subnet-mode=custom \
    --bgp-routing-mode=regional

# Create subnets
# Public subnet (for Load Balancer)
gcloud compute networks subnets create insuregraph-public \
    --network=insuregraph-vpc \
    --region=asia-northeast3 \
    --range=10.0.1.0/24 \
    --enable-flow-logs

# Private subnet (for GKE, application)
gcloud compute networks subnets create insuregraph-private \
    --network=insuregraph-vpc \
    --region=asia-northeast3 \
    --range=10.0.10.0/24 \
    --enable-private-ip-google-access \
    --enable-flow-logs

# Data subnet (for databases)
gcloud compute networks subnets create insuregraph-data \
    --network=insuregraph-vpc \
    --region=asia-northeast3 \
    --range=10.0.20.0/24 \
    --enable-private-ip-google-access \
    --enable-flow-logs
```

### Firewall Rules

```bash
# Allow internal communication
gcloud compute firewall-rules create insuregraph-allow-internal \
    --network=insuregraph-vpc \
    --allow=tcp,udp,icmp \
    --source-ranges=10.0.0.0/8

# Allow SSH from IAP (Identity-Aware Proxy)
gcloud compute firewall-rules create insuregraph-allow-ssh-iap \
    --network=insuregraph-vpc \
    --allow=tcp:22 \
    --source-ranges=35.235.240.0/20

# Allow health checks from Google LB
gcloud compute firewall-rules create insuregraph-allow-health-check \
    --network=insuregraph-vpc \
    --allow=tcp \
    --source-ranges=35.191.0.0/16,130.211.0.0/22

# Deny all other ingress by default (implicit)
```

### Cloud NAT (for outbound internet from private instances)

```bash
# Create Cloud Router
gcloud compute routers create insuregraph-router \
    --network=insuregraph-vpc \
    --region=asia-northeast3

# Create Cloud NAT
gcloud compute routers nats create insuregraph-nat \
    --router=insuregraph-router \
    --region=asia-northeast3 \
    --auto-allocate-nat-external-ips \
    --nat-all-subnet-ip-ranges
```

---

## ☸️ Step 2: GKE (Kubernetes) Cluster

### Create GKE Cluster

```bash
gcloud container clusters create insuregraph-cluster \
    --region=asia-northeast3 \
    --network=insuregraph-vpc \
    --subnetwork=insuregraph-private \
    --enable-private-nodes \
    --enable-private-endpoint \
    --master-ipv4-cidr=172.16.0.0/28 \
    --enable-ip-alias \
    --num-nodes=3 \
    --machine-type=e2-standard-4 \
    --disk-type=pd-ssd \
    --disk-size=100 \
    --enable-autoscaling \
    --min-nodes=3 \
    --max-nodes=10 \
    --enable-autorepair \
    --enable-autoupgrade \
    --maintenance-window-start=2025-01-01T00:00:00Z \
    --maintenance-window-duration=4h \
    --enable-stackdriver-kubernetes \
    --addons=HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver \
    --workload-pool=$PROJECT_ID_DEV.svc.id.goog \
    --enable-shielded-nodes \
    --shielded-secure-boot \
    --shielded-integrity-monitoring
```

**Key Configuration Explained**:
- `--enable-private-nodes`: Nodes have no external IP (security)
- `--enable-autoscaling`: Scale 3-10 nodes based on load
- `--machine-type=e2-standard-4`: 4 vCPUs, 16 GB RAM per node
- `--enable-stackdriver-kubernetes`: Monitoring & logging
- `--workload-pool`: Workload Identity for secure GCP service access

### Get Cluster Credentials

```bash
gcloud container clusters get-credentials insuregraph-cluster \
    --region=asia-northeast3 \
    --project=$PROJECT_ID_DEV

# Verify access
kubectl get nodes
```

### Install Ingress Controller (nginx-ingress)

```bash
# Add Helm repo
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install nginx-ingress
helm install nginx-ingress ingress-nginx/ingress-nginx \
    --namespace ingress-nginx \
    --create-namespace \
    --set controller.service.type=LoadBalancer \
    --set controller.service.annotations."cloud\.google\.com/load-balancer-type"="External"
```

---

## 🗄️ Step 3: Cloud SQL (PostgreSQL)

### Create Cloud SQL Instance

```bash
gcloud sql instances create insuregraph-postgres \
    --database-version=POSTGRES_15 \
    --tier=db-custom-4-16384 \
    --region=asia-northeast3 \
    --network=projects/$PROJECT_ID_DEV/global/networks/insuregraph-vpc \
    --no-assign-ip \
    --storage-type=SSD \
    --storage-size=100GB \
    --storage-auto-increase \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=4 \
    --database-flags=max_connections=200,shared_buffers=4GB \
    --enable-point-in-time-recovery \
    --retained-backups-count=7
```

**Key Settings**:
- `--tier=db-custom-4-16384`: 4 vCPUs, 16 GB RAM
- `--no-assign-ip`: Private IP only (security)
- `--enable-point-in-time-recovery`: Restore to any point in last 7 days
- `--storage-auto-increase`: Auto-expand disk when full

### Create Database & User

```bash
# Create database
gcloud sql databases create insuregraph \
    --instance=insuregraph-postgres

# Create user
gcloud sql users create insuregraph_user \
    --instance=insuregraph-postgres \
    --password=CHANGE_ME_STRONG_PASSWORD

# Get connection name (for application config)
gcloud sql instances describe insuregraph-postgres \
    --format="value(connectionName)"
# Output: PROJECT_ID:asia-northeast3:insuregraph-postgres
```

### Connect to Cloud SQL from GKE

**Option A: Cloud SQL Proxy (Recommended)**

```yaml
# kubernetes/cloudsql-proxy-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloudsql-proxy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cloudsql-proxy
  template:
    metadata:
      labels:
        app: cloudsql-proxy
    spec:
      serviceAccountName: cloudsql-sa
      containers:
      - name: cloud-sql-proxy
        image: gcr.io/cloudsql-docker/gce-proxy:latest
        command:
          - "/cloud_sql_proxy"
          - "-instances=PROJECT_ID:asia-northeast3:insuregraph-postgres=tcp:0.0.0.0:5432"
        ports:
        - containerPort: 5432
        securityContext:
          runAsNonRoot: true
---
apiVersion: v1
kind: Service
metadata:
  name: cloudsql-proxy-service
spec:
  selector:
    app: cloudsql-proxy
  ports:
  - port: 5432
    targetPort: 5432
```

**Setup Workload Identity** (for Cloud SQL Proxy):

```bash
# Create GCP service account
gcloud iam service-accounts create cloudsql-sa \
    --display-name="Cloud SQL Proxy Service Account"

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding $PROJECT_ID_DEV \
    --member="serviceAccount:cloudsql-sa@$PROJECT_ID_DEV.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# Create Kubernetes service account
kubectl create serviceaccount cloudsql-sa -n default

# Bind K8s SA to GCP SA (Workload Identity)
gcloud iam service-accounts add-iam-policy-binding \
    cloudsql-sa@$PROJECT_ID_DEV.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:$PROJECT_ID_DEV.svc.id.goog[default/cloudsql-sa]"

kubectl annotate serviceaccount cloudsql-sa \
    iam.gke.io/gcp-service-account=cloudsql-sa@$PROJECT_ID_DEV.iam.gserviceaccount.com
```

**Option B: Private IP Connection** (Direct, no proxy)

Application connects to Cloud SQL's private IP directly (retrieved from VPC network).

---

## 🔴 Step 4: Memorystore for Redis

### Create Redis Instance

```bash
gcloud redis instances create insuregraph-redis \
    --size=5 \
    --region=asia-northeast3 \
    --network=projects/$PROJECT_ID_DEV/global/networks/insuregraph-vpc \
    --redis-version=redis_7_0 \
    --tier=standard \
    --replica-count=1 \
    --enable-auth
```

**Settings**:
- `--size=5`: 5 GB memory
- `--tier=standard`: High availability with replica
- `--enable-auth`: Require AUTH token

### Get Redis Connection Info

```bash
gcloud redis instances describe insuregraph-redis \
    --region=asia-northeast3 \
    --format="value(host,port,authString)"

# Output: 10.0.20.5 6379 AUTH_TOKEN
```

**Application Config**:
```python
REDIS_HOST = "10.0.20.5"
REDIS_PORT = 6379
REDIS_PASSWORD = "AUTH_TOKEN"  # Store in Secret Manager
```

---

## 🟢 Step 5: Neo4j on Compute Engine

GCP doesn't have a managed Neo4j service, so we'll deploy on Compute Engine.

### Create Compute Engine Instance

```bash
gcloud compute instances create insuregraph-neo4j \
    --zone=asia-northeast3-a \
    --machine-type=n2-standard-8 \
    --subnet=insuregraph-data \
    --no-address \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=200GB \
    --boot-disk-type=pd-ssd \
    --metadata=startup-script='#!/bin/bash
# Install Neo4j
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add -
echo "deb https://debian.neo4j.com stable latest" > /etc/apt/sources.list.d/neo4j.list
apt-get update
apt-get install -y neo4j-enterprise=1:5.15.0

# Configure Neo4j
sed -i "s/#server.default_listen_address=0.0.0.0/server.default_listen_address=0.0.0.0/" /etc/neo4j/neo4j.conf
sed -i "s/#dbms.security.auth_enabled=true/dbms.security.auth_enabled=true/" /etc/neo4j/neo4j.conf

# Enable vector index
echo "db.index.vector.enabled=true" >> /etc/neo4j/neo4j.conf

# Set initial password (change this!)
neo4j-admin dbms set-initial-password CHANGE_ME_NEO4J_PASSWORD

# Start Neo4j
systemctl enable neo4j
systemctl start neo4j
'
```

**Firewall Rule** (allow Neo4j port from GKE):

```bash
gcloud compute firewall-rules create insuregraph-allow-neo4j \
    --network=insuregraph-vpc \
    --allow=tcp:7687,tcp:7474 \
    --source-ranges=10.0.10.0/24 \
    --target-tags=neo4j
```

### Install Neo4j via Helm (Alternative: In-cluster)

If you prefer Neo4j inside GKE:

```bash
helm repo add neo4j https://neo4j.github.io/helm-charts
helm install neo4j neo4j/neo4j \
    --namespace default \
    --set neo4j.password=CHANGE_ME \
    --set volumes.data.mode=dynamic \
    --set volumes.data.dynamic.storageClassName=standard-rw
```

**Note**: Compute Engine approach is recommended for production (easier scaling, backups).

---

## 📦 Step 6: Cloud Storage (Object Storage)

### Create Buckets

```bash
# Bucket for uploaded PDFs
gcloud storage buckets create gs://insuregraph-policies-dev \
    --location=asia-northeast3 \
    --uniform-bucket-level-access \
    --public-access-prevention

# Bucket for generated reports
gcloud storage buckets create gs://insuregraph-reports-dev \
    --location=asia-northeast3 \
    --uniform-bucket-level-access \
    --public-access-prevention
```

### Enable Versioning (Optional)

```bash
gcloud storage buckets update gs://insuregraph-policies-dev \
    --versioning
```

### Set Lifecycle Policy (Auto-delete old objects)

```bash
# Create lifecycle.json
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF

gcloud storage buckets update gs://insuregraph-policies-dev \
    --lifecycle-file=lifecycle.json
```

### Grant Access to GKE (Workload Identity)

```bash
# Create service account
gcloud iam service-accounts create insuregraph-storage-sa \
    --display-name="Storage Access Service Account"

# Grant Storage Object Admin role
gcloud storage buckets add-iam-policy-binding gs://insuregraph-policies-dev \
    --member="serviceAccount:insuregraph-storage-sa@$PROJECT_ID_DEV.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Bind to K8s service account
kubectl create serviceaccount insuregraph-storage-sa -n default

gcloud iam service-accounts add-iam-policy-binding \
    insuregraph-storage-sa@$PROJECT_ID_DEV.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:$PROJECT_ID_DEV.svc.id.goog[default/insuregraph-storage-sa]"

kubectl annotate serviceaccount insuregraph-storage-sa \
    iam.gke.io/gcp-service-account=insuregraph-storage-sa@$PROJECT_ID_DEV.iam.gserviceaccount.com
```

---

## 🔐 Step 7: Cloud KMS (Key Management)

### Create Keyring & Key

```bash
# Create keyring
gcloud kms keyrings create insuregraph-keyring \
    --location=asia-northeast3

# Create encryption key (for PII encryption)
gcloud kms keys create pii-encryption-key \
    --location=asia-northeast3 \
    --keyring=insuregraph-keyring \
    --purpose=encryption \
    --rotation-period=90d \
    --next-rotation-time=$(date -u -d "+90 days" +%Y-%m-%dT%H:%M:%SZ)
```

### Grant Access to Application

```bash
# Create service account
gcloud iam service-accounts create insuregraph-kms-sa \
    --display-name="KMS Access Service Account"

# Grant Cloud KMS CryptoKey Encrypter/Decrypter
gcloud kms keys add-iam-policy-binding pii-encryption-key \
    --location=asia-northeast3 \
    --keyring=insuregraph-keyring \
    --member="serviceAccount:insuregraph-kms-sa@$PROJECT_ID_DEV.iam.gserviceaccount.com" \
    --role="roles/cloudkms.cryptoKeyEncrypterDecrypter"

# Bind to K8s SA (Workload Identity)
kubectl create serviceaccount insuregraph-kms-sa -n default

gcloud iam service-accounts add-iam-policy-binding \
    insuregraph-kms-sa@$PROJECT_ID_DEV.iam.gserviceaccount.com \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:$PROJECT_ID_DEV.svc.id.goog[default/insuregraph-kms-sa]"

kubectl annotate serviceaccount insuregraph-kms-sa \
    iam.gke.io/gcp-service-account=insuregraph-kms-sa@$PROJECT_ID_DEV.iam.gserviceaccount.com
```

---

## 🛡️ Step 8: Cloud Armor (WAF)

### Create Security Policy

```bash
# Create Cloud Armor policy
gcloud compute security-policies create insuregraph-waf \
    --description="WAF for InsureGraph Pro"

# Rule 1: Block SQL injection
gcloud compute security-policies rules create 1000 \
    --security-policy=insuregraph-waf \
    --expression="evaluatePreconfiguredExpr('sqli-stable')" \
    --action=deny-403

# Rule 2: Block XSS
gcloud compute security-policies rules create 1001 \
    --security-policy=insuregraph-waf \
    --expression="evaluatePreconfiguredExpr('xss-stable')" \
    --action=deny-403

# Rule 3: Rate limiting (2000 requests per minute per IP)
gcloud compute security-policies rules create 1002 \
    --security-policy=insuregraph-waf \
    --expression="true" \
    --action=rate-based-ban \
    --rate-limit-threshold-count=2000 \
    --rate-limit-threshold-interval-sec=60 \
    --ban-duration-sec=600

# Default rule: Allow
gcloud compute security-policies rules create 2147483647 \
    --security-policy=insuregraph-waf \
    --action=allow
```

### Attach to Load Balancer

```bash
# Get backend service name (from GKE ingress)
kubectl get ingress -o yaml | grep backend-service

# Attach Cloud Armor policy
gcloud compute backend-services update BACKEND_SERVICE_NAME \
    --security-policy=insuregraph-waf \
    --global
```

---

## 📊 Step 9: Monitoring & Logging

### Create Monitoring Dashboard

```bash
# Install monitoring agent (GKE automatically has it)
# Create custom dashboard via Cloud Console or Terraform

# Example: Create alert for high error rate
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High API Error Rate" \
    --condition-display-name="Error rate > 5%" \
    --condition-threshold-value=5 \
    --condition-threshold-duration=300s \
    --condition-filter='resource.type="k8s_container" AND metric.type="logging.googleapis.com/user/error_count"'
```

### Log Sink for Audit Logs

```bash
# Create BigQuery dataset for log storage
bq mk --dataset --location=asia-northeast3 $PROJECT_ID_DEV:audit_logs

# Create log sink
gcloud logging sinks create audit-log-sink \
    bigquery.googleapis.com/projects/$PROJECT_ID_DEV/datasets/audit_logs \
    --log-filter='resource.type="k8s_container" AND jsonPayload.action=~"customer_pii_accessed|auth:login"'
```

---

## 🚢 Step 10: CI/CD with Cloud Build

### Create Cloud Build Trigger

```yaml
# cloudbuild.yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/insuregraph-api:$SHORT_SHA', './backend']

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/insuregraph-api:$SHORT_SHA']

  # Deploy to GKE
  - name: 'gcr.io/cloud-builders/kubectl'
    args:
      - 'set'
      - 'image'
      - 'deployment/insuregraph-api'
      - 'insuregraph-api=gcr.io/$PROJECT_ID/insuregraph-api:$SHORT_SHA'
    env:
      - 'CLOUDSDK_COMPUTE_REGION=asia-northeast3'
      - 'CLOUDSDK_CONTAINER_CLUSTER=insuregraph-cluster'

images:
  - 'gcr.io/$PROJECT_ID/insuregraph-api:$SHORT_SHA'
```

**Create Trigger**:

```bash
gcloud builds triggers create github \
    --repo-name=insuregraph-pro \
    --repo-owner=YOUR_GITHUB_ORG \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml
```

---

## 📝 Configuration Summary

### Environment Variables for Application

Store in Kubernetes Secret:

```yaml
# kubernetes/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: insuregraph-secrets
type: Opaque
stringData:
  # PostgreSQL
  POSTGRES_HOST: "cloudsql-proxy-service"
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "insuregraph"
  POSTGRES_USER: "insuregraph_user"
  POSTGRES_PASSWORD: "CHANGE_ME"

  # Neo4j
  NEO4J_URI: "bolt://10.0.20.10:7687"
  NEO4J_USER: "neo4j"
  NEO4J_PASSWORD: "CHANGE_ME"

  # Redis
  REDIS_HOST: "10.0.20.5"
  REDIS_PORT: "6379"
  REDIS_PASSWORD: "AUTH_TOKEN"

  # Cloud Storage
  GCS_BUCKET_POLICIES: "insuregraph-policies-dev"
  GCS_BUCKET_REPORTS: "insuregraph-reports-dev"

  # Cloud KMS
  KMS_KEY_NAME: "projects/PROJECT_ID/locations/asia-northeast3/keyRings/insuregraph-keyring/cryptoKeys/pii-encryption-key"

  # API Keys
  UPSTAGE_API_KEY: "YOUR_UPSTAGE_KEY"
  OPENAI_API_KEY: "YOUR_OPENAI_KEY"
```

Apply:
```bash
kubectl apply -f kubernetes/secrets.yaml
```

---

## 💰 Cost Estimation (Monthly, Dev Environment)

| Service | Configuration | Estimated Cost (USD) |
|---------|--------------|---------------------|
| **GKE Cluster** | 3 x e2-standard-4 nodes | ~$365 |
| **Cloud SQL** | db-custom-4-16384 | ~$320 |
| **Compute Engine (Neo4j)** | n2-standard-8 | ~$290 |
| **Memorystore Redis** | 5 GB Standard | ~$110 |
| **Cloud Storage** | 500 GB + ops | ~$15 |
| **Cloud Load Balancing** | ~1M requests | ~$20 |
| **Cloud Armor** | 1M requests | ~$10 |
| **Cloud Monitoring** | Standard | ~$50 |
| **Egress (Internet)** | 100 GB | ~$12 |
| **Total** | | **~$1,192/month** |

**Production environment**: ~$2,500-3,000/month (with autoscaling, HA, backups)

**Optimization Tips**:
- Use Committed Use Discounts (save 37% on compute)
- Preemptible VMs for non-critical workloads (save 80%)
- Archive old Cloud Storage objects to Nearline/Coldline

---

## ✅ Verification Checklist

After completing setup, verify:

- [ ] GKE cluster running with 3 nodes
- [ ] kubectl can connect to cluster
- [ ] Cloud SQL accessible via Cloud SQL Proxy
- [ ] Neo4j accessible from GKE (test connection)
- [ ] Redis accessible from GKE
- [ ] Cloud Storage buckets created and accessible
- [ ] Cloud KMS key created
- [ ] Cloud Armor policy attached to LB
- [ ] Monitoring dashboard showing metrics
- [ ] Secrets created in Kubernetes
- [ ] Workload Identity bindings working

---

## 🆘 Troubleshooting

### Issue: Cannot connect to Cloud SQL

**Solution**:
```bash
# Check Cloud SQL Proxy logs
kubectl logs deployment/cloudsql-proxy

# Test connection manually
gcloud sql connect insuregraph-postgres --user=insuregraph_user
```

### Issue: GKE pods can't access Cloud Storage

**Solution**:
```bash
# Verify Workload Identity annotation
kubectl describe sa insuregraph-storage-sa

# Test from pod
kubectl run -it --rm test --image=google/cloud-sdk:slim --serviceaccount=insuregraph-storage-sa -- gsutil ls gs://insuregraph-policies-dev
```

### Issue: Neo4j connection timeout

**Solution**:
```bash
# Check firewall rules
gcloud compute firewall-rules list --filter="name:neo4j"

# Check Neo4j status
gcloud compute ssh insuregraph-neo4j --zone=asia-northeast3-a
systemctl status neo4j
```

---

## 🔄 Next Steps

1. **Deploy Application**:
   - Build Docker images
   - Create Kubernetes deployments
   - Apply ingress configuration

2. **Setup Monitoring**:
   - Create custom dashboards
   - Configure alerts (error rate, latency, etc.)

3. **Load Testing**:
   - Use `locust` or `k6` to test performance
   - Tune autoscaling parameters

4. **Security Hardening**:
   - Enable Binary Authorization
   - Setup VPC Service Controls
   - Run vulnerability scanning

5. **Documentation**:
   - Document all credentials in secure vault
   - Create runbook for incidents
   - Train team on GCP tools

---

**Document Owner**: DevOps Engineer
**Last Updated**: 2025-11-25
**Next Review**: After Sprint 1 completion
