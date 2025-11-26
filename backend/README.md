# InsureGraph Pro - Backend API

GraphRAG 기반 보험 질의응답 시스템의 백엔드 API

**Version**: 1.0.0
**Framework**: FastAPI
**Python**: 3.10+

---

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [시작하기](#시작하기)
- [API 문서](#api-문서)
- [프로젝트 구조](#프로젝트-구조)
- [개발 가이드](#개발-가이드)
- [테스트](#테스트)
- [배포](#배포)

---

## 🎯 개요

InsureGraph Pro는 GraphRAG(Graph Retrieval-Augmented Generation) 기술을 활용하여 보험 약관 분석 및 질의응답 서비스를 제공하는 플랫폼입니다.

### 핵심 가치

- **Deep Analysis**: GraphRAG를 통한 복합 추론 및 상호 참조 분석
- **High Accuracy**: 85%+ 답변 정확도
- **Real-time**: 500ms 이내 응답 시간
- **Scalable**: 마이크로서비스 아키텍처

---

## ✨ 주요 기능

### 1. GraphRAG Query Engine (Epic 2)
- 자연어 질의 분석
- 하이브리드 검색 (Vector + Graph)
- LLM 기반 답변 생성
- Query orchestration

### 2. Document Management (Epic 1)
- PDF 업로드 및 OCR 처리
- 법률 문서 구조 파싱
- 지식 그래프 구축
- 엔티티 추출 및 관계 매핑

### 3. API Layer (Epic 3)
- RESTful API
- JWT 인증/인가
- Rate limiting
- Monitoring & Metrics

---

## 🛠 기술 스택

### Core
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.10+
- **API Documentation**: OpenAPI 3.0 (Swagger/ReDoc)

### Databases
- **Graph**: Neo4j 5.x (지식 그래프)
- **Vector**: Milvus/Qdrant (임베딩 검색)
- **RDBMS**: PostgreSQL 15+ (메타데이터, 사용자)
- **Cache**: Redis 7.x (세션, rate limiting)

### AI/ML
- **LLM**: Upstage Solar Pro, OpenAI GPT-4
- **Embeddings**: OpenAI text-embedding-ada-002
- **OCR**: Upstage Document Parse

### Infrastructure
- **Cloud**: GCP (GCS, Cloud Run, GKE)
- **Monitoring**: Prometheus, Grafana
- **Logging**: Loguru
- **Testing**: Pytest

---

## 🚀 시작하기

### 사전 요구사항

```bash
# Python 3.10+
python --version

# Poetry (패키지 관리)
curl -sSL https://install.python-poetry.org | python3 -

# Docker & Docker Compose (로컬 DB)
docker --version
docker-compose --version
```

### 설치

```bash
# 1. Clone repository
git clone https://github.com/your-org/insuregraph-pro.git
cd insuregraph-pro/backend

# 2. Install dependencies
poetry install

# 3. Activate virtual environment
poetry shell

# 4. Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# 5. Start local databases (Docker)
docker-compose up -d

# 6. Run database migrations
alembic upgrade head

# 7. Start development server
uvicorn app.main:app --reload --port 8000
```

### 환경 변수 (.env)

```bash
# Application
APP_NAME="InsureGraph Pro"
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-here

# Databases
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=insuregraph
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

REDIS_HOST=localhost
REDIS_PORT=6379

# GCP
GCP_PROJECT_ID=your-project-id
GCS_BUCKET_POLICIES=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# LLM APIs
UPSTAGE_API_KEY=your-upstage-key
OPENAI_API_KEY=your-openai-key

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=1
```

### 서버 실행 확인

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

---

## 📚 API 문서

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Guides

- [API Guide](./docs/API_GUIDE.md) - 전체 API 사용 가이드
- [Authentication Guide](./docs/AUTHENTICATION_GUIDE.md) - 인증/인가 가이드

### Quick Start

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123!",
    "username": "user",
    "full_name": "User Name"
  }'

# 2. Login (after admin approval)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123!"
  }'

# 3. Use API with access token
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer {access_token}"
```

### Default Admin Account

```
Email: admin@insuregraph.com
Password: Admin123!
```

**⚠️ Change this password in production!**

---

## 📂 프로젝트 구조

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # API 엔드포인트
│   │       │   ├── auth.py     # 인증
│   │       │   ├── query.py    # 질의응답
│   │       │   ├── documents.py # 문서 관리
│   │       │   └── monitoring.py # 모니터링
│   │       ├── models/         # API 모델 (Pydantic)
│   │       └── router.py       # API 라우터
│   │
│   ├── core/
│   │   ├── config.py           # 설정
│   │   ├── security.py         # 인증/보안
│   │   ├── database.py         # DB 연결
│   │   ├── rate_limit.py       # Rate limiting
│   │   └── logging.py          # 로깅/메트릭
│   │
│   ├── models/                 # 도메인 모델
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── query.py
│   │   └── ...
│   │
│   ├── services/               # 비즈니스 로직
│   │   ├── orchestration/      # Query orchestration
│   │   ├── analysis/           # Query analysis
│   │   ├── search/             # Hybrid search
│   │   ├── generation/         # Response generation
│   │   └── ingestion/          # Document ingestion
│   │
│   └── main.py                 # FastAPI app
│
├── tests/                      # 테스트
│   ├── test_api_auth.py
│   ├── test_api_query.py
│   ├── test_api_documents.py
│   └── test_monitoring.py
│
├── docs/                       # 문서
│   ├── API_GUIDE.md
│   └── AUTHENTICATION_GUIDE.md
│
├── alembic/                    # DB migrations
├── pyproject.toml              # Dependencies
├── docker-compose.yml          # Local dev environment
└── README.md
```

---

## 💻 개발 가이드

### Code Style

```bash
# Format code
black app/ tests/

# Lint
ruff app/ tests/

# Type check
mypy app/
```

### Adding New Endpoint

```python
# 1. Create model (app/api/v1/models/your_model.py)
from pydantic import BaseModel

class YourRequest(BaseModel):
    field: str

class YourResponse(BaseModel):
    result: str

# 2. Create endpoint (app/api/v1/endpoints/your_endpoint.py)
from fastapi import APIRouter

router = APIRouter(prefix="/your-endpoint", tags=["Your Tag"])

@router.post("", response_model=YourResponse)
async def your_endpoint(request: YourRequest) -> YourResponse:
    # Your logic here
    return YourResponse(result="Success")

# 3. Add to router (app/api/v1/router.py)
from app.api.v1.endpoints import your_endpoint

api_router.include_router(your_endpoint.router)
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add user table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 🧪 테스트

### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_api_auth.py

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/test_api_auth.py::TestLogin::test_login_admin_success -v
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

### Writing Tests

```python
# tests/test_your_feature.py
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_your_endpoint():
    response = client.get("/api/v1/your-endpoint")
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

---

## 🚢 배포

### Docker Build

```bash
# Build image
docker build -t insuregraph-pro-backend:latest .

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  insuregraph-pro-backend:latest
```

### GCP Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/${PROJECT_ID}/insuregraph-pro-backend

# Deploy to Cloud Run
gcloud run deploy insuregraph-pro-backend \
  --image gcr.io/${PROJECT_ID}/insuregraph-pro-backend \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated
```

### Environment Variables (Production)

```bash
# Set environment variables
gcloud run services update insuregraph-pro-backend \
  --set-env-vars "ENVIRONMENT=production" \
  --set-env-vars "DEBUG=False"
```

---

## 📊 Monitoring

### Metrics

```bash
# Prometheus metrics
curl http://localhost:8000/api/v1/monitoring/metrics

# System stats
curl http://localhost:8000/api/v1/monitoring/stats

# Detailed health
curl http://localhost:8000/api/v1/monitoring/health/detailed
```

### Logs

```bash
# Application logs
tail -f logs/app.log

# Access logs
tail -f logs/access.log
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

Copyright © 2025 InsureGraph Pro

---

## 🆘 Support

- **Documentation**: http://localhost:8000/docs
- **Issues**: https://github.com/your-org/insuregraph-pro/issues
- **Email**: support@insuregraph.com

---

## 🏗️ Project Status

### Completed Epics

✅ **Epic 1**: Data Ingestion & Knowledge Graph
- PDF upload, OCR, parsing
- Entity extraction, graph construction

✅ **Epic 2**: GraphRAG Query Engine
- Query analysis, hybrid search
- Response generation, orchestration

✅ **Epic 3**: API & Service Layer
- REST API, authentication
- Rate limiting, monitoring

### In Progress

⏳ **Epic 4**: Compliance & Security
⏳ **Frontend**: FP Workspace (Next.js)

---

**Last Updated**: 2025-11-25
**Version**: 1.0.0
