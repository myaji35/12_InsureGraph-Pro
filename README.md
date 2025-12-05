# InsureGraph Pro

**보험 약관 분석을 위한 GraphRAG 기반 지능형 플랫폼**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)
[![Neo4j](https://img.shields.io/badge/neo4j-5.x-green.svg)](https://neo4j.com/)

---

## 📋 프로젝트 개요

InsureGraph Pro는 GraphRAG(Graph Retrieval-Augmented Generation) 기술을 활용하여 복잡한 보험 약관을 자동으로 분석하고, 보험설계사(FP)가 고객에게 정확한 정보를 제공할 수 있도록 돕는 B2B2C SaaS 플랫폼입니다.

### 핵심 가치 제안

- 🔍 **Deep Analysis**: 수백 페이지 약관의 숨겨진 조항 간 관계를 그래프로 시각화
- ✅ **Compliance Safety**: 금융규제 준수 및 불완전 판매 방지
- ⚡ **Sales Acceleration**: 고객 보장 공백을 논리적으로 입증하여 근거 기반 세일즈 가능

### 주요 기능

1. **약관 자동 파싱**: PDF 업로드 → Neo4j 지식 그래프 자동 변환
2. **자연어 질의응답**: "갑상선암 보장돼요?" → 정확한 답변 + 근거 조항
3. **보장 공백 분석**: 고객 포트폴리오 분석 → 추가 필요 담보 추천
4. **상품 비교**: 여러 보험 상품 side-by-side 비교
5. **모바일 PWA**: 외근 중에도 태블릿/스마트폰에서 사용 가능

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                   Client Layer                           │
│  Next.js (React) + Cytoscape.js + PWA                   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS / JWT
┌────────────────────▼────────────────────────────────────┐
│              API Gateway (Kong)                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│         Application Layer (FastAPI + LangGraph)         │
│  Parser → Extractor → Validator → Reasoner → Formatter │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼─────────┐    ┌─────────▼────────┐
│  Data Layer     │    │   LLM Layer      │
│  - Neo4j        │    │  - Upstage Solar │
│  - PostgreSQL   │    │  - GPT-4o        │
│  - Redis        │    │                  │
│  - Cloud Storage│    └──────────────────┘
└─────────────────┘
```

**기술 스택**:
- **Backend**: FastAPI, LangGraph, Python 3.11+
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Graph DB**: Neo4j 5.x Enterprise (with Vector Index)
- **Relational DB**: PostgreSQL 15
- **Cache**: Redis 7
- **LLM**: Upstage Solar Pro (primary), GPT-4o (fallback)
- **Cloud**: Google Cloud Platform (GKE, Cloud SQL, Compute Engine)
- **Infrastructure**: Kubernetes, Docker, Terraform

---

## 📂 프로젝트 구조

이 프로젝트는 **모노레포(Monorepo)** 구조로 구성되어 있으며, Turborepo와 pnpm workspaces를 사용합니다.

```
InsureGraph Pro/
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── api/               # API 엔드포인트
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── ingestion.py
│   │   │       ├── query.py
│   │   │       └── crawler_urls.py
│   │   ├── core/              # 핵심 설정
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── services/          # 비즈니스 로직
│   │   │   ├── ingestion/
│   │   │   ├── query/
│   │   │   └── compliance/
│   │   ├── models/            # 데이터 모델
│   │   └── main.py            # FastAPI 앱 엔트리포인트
│   ├── alembic/               # 데이터베이스 마이그레이션
│   │   └── versions/
│   ├── tests/                 # 테스트
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/                   # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   ├── components/        # React 컴포넌트
│   │   ├── lib/               # 유틸리티
│   │   └── styles/            # CSS/Tailwind
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── packages/                   # 공유 패키지 (Monorepo)
│   └── shared-types/          # 프론트엔드-백엔드 공유 TypeScript 타입
│       ├── src/
│       │   └── index.ts       # 공통 타입 정의
│       ├── package.json
│       └── tsconfig.json
├── docs/                       # 문서
│   ├── architecture.md
│   ├── api-specifications.md
│   ├── gcp-infrastructure-setup.md
│   ├── sprint-planning.md
│   └── epics/
├── scripts/                    # 유틸리티 스크립트
│   ├── run_pg_migrations.py
│   ├── run_neo4j_migrations.py
│   └── seed_test_data.py
├── pnpm-workspace.yaml         # pnpm workspace 설정
├── turbo.json                  # Turborepo 파이프라인 설정
├── package.json                # 루트 패키지 설정
├── prd.md
├── graphrag-implementation-strategy.md
└── README.md                   # 이 파일
```

### 모노레포의 이점

1. **코드 공유**: `packages/shared-types`를 통해 프론트엔드와 백엔드가 동일한 타입 정의 사용
2. **원자적 커밋**: API 변경 시 프론트엔드와 백엔드를 동시에 업데이트
3. **일관된 개발 환경**: 모든 패키지가 동일한 도구 및 설정 사용
4. **효율적인 빌드**: Turborepo의 캐싱으로 변경된 패키지만 재빌드

---

## 🚀 빠른 시작

### Prerequisites

- **Python**: 3.11+
- **Node.js**: 20+
- **Docker**: 24.0+
- **Neo4j**: 5.x Enterprise
- **PostgreSQL**: 15+
- **Redis**: 7+

### 1. 저장소 클론

```bash
git clone https://github.com/YOUR_ORG/insuregraph-pro.git
cd insuregraph-pro
```

### 2. 모노레포 의존성 설치

```bash
# pnpm을 사용하여 워크스페이스 의존성 설치
pnpm install

# 공유 타입 패키지 빌드
cd packages/shared-types
pnpm build
cd ../..
```

### 3. 백엔드 설정

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집 (데이터베이스 연결 정보 등)

# 데이터베이스 마이그레이션 실행
bash scripts/apply_migration.sh 004_add_crawler_urls_table

# 개발 서버 실행 (포트 3030)
uvicorn app.main:app --host 0.0.0.0 --port 3030 --reload
```

**API 확인**: http://localhost:3030/docs (Swagger UI)

### 4. 프론트엔드 설정

```bash
cd frontend

# 환경 변수 설정
cp .env.example .env.local
# .env.local 파일 편집

# 개발 서버 실행
pnpm dev
```

**앱 확인**: http://localhost:3000

### 5. Turborepo로 전체 실행 (권장)

```bash
# 루트 디렉토리에서 모든 서비스 동시 실행
pnpm dev

# 또는 개별 실행
pnpm dev:web    # 프론트엔드만
pnpm dev:api    # 백엔드만
```

### 6. Docker Compose로 전체 실행

```bash
# 루트 디렉토리에서
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 중지
docker-compose down
```

---

## 📖 문서

### 개발 문서

- [Architecture Document](./docs/architecture.md) - 전체 시스템 아키텍처
- [API Specifications](./docs/api-specifications.md) - RESTful API 상세 스펙
- [Database Migrations](./backend/migrations/README.md) - DB 마이그레이션 가이드
- [GCP Infrastructure Setup](./docs/gcp-infrastructure-setup.md) - GCP 인프라 구축 가이드

### 기획 문서

- [PRD (Product Requirements Document)](./prd.md) - 제품 요구사항 정의
- [GraphRAG Implementation Strategy](./graphrag-implementation-strategy.md) - GraphRAG 기술 구현 전략

### Sprint & Epic 문서

- [Sprint Planning Guide](./docs/sprint-planning.md) - 16 스프린트 계획 (32주)
- [Epic 1: Data Ingestion](./docs/epics/epic-01-data-ingestion.md) - 약관 수집 파이프라인 (9 stories)
- [Epic 2: GraphRAG Query Engine](./docs/epics/epic-02-graphrag-query-engine.md) - 질의응답 엔진 (8 stories)
- [Epic 3: FP Workspace](./docs/epics/epic-03-fp-workspace.md) - 프론트엔드 워크스페이스 (7 stories)
- [Epic 4: Compliance & Security](./docs/epics/epic-04-compliance-security.md) - 보안 및 준법 (6 stories)

---

## 🧪 테스트

### 백엔드 테스트

```bash
cd backend

# 단위 테스트
pytest tests/unit/

# 통합 테스트
pytest tests/integration/

# 커버리지 리포트
pytest --cov=app --cov-report=html tests/

# E2E 테스트
pytest tests/e2e/
```

### 프론트엔드 테스트

```bash
cd frontend

# 단위 테스트
npm test

# E2E 테스트 (Playwright)
npm run test:e2e

# Storybook
npm run storybook
```

---

## 🔒 보안

### 취약점 보고

보안 취약점을 발견하신 경우 security@insuregraph.com으로 보고해주세요. 공개 이슈로 등록하지 마세요.

### 보안 기능

- ✅ JWT 인증 (Access + Refresh Token)
- ✅ RBAC (Role-Based Access Control)
- ✅ PII 암호화 (AES-256)
- ✅ Audit Logging (전 작업 추적)
- ✅ WAF (Cloud Armor)
- ✅ SAST/DAST 통합 (CI/CD)
- ✅ 금융규제 샌드박스 준수

---

## 🌐 배포

### 개발 환경 배포

```bash
# GKE 클러스터 연결
gcloud container clusters get-credentials insuregraph-cluster \
  --region=asia-northeast3 \
  --project=insuregraph-dev

# Kubernetes 배포
kubectl apply -f infrastructure/kubernetes/dev/

# 배포 확인
kubectl get pods
kubectl get ingress
```

### 프로덕션 배포

```bash
# CI/CD 파이프라인 (Cloud Build)을 통한 자동 배포
# main 브랜치에 머지 시 자동 트리거

# 또는 수동 배포
gcloud builds submit --config=cloudbuild.yaml
```

**배포 전 체크리스트**:
- [ ] 모든 테스트 통과
- [ ] 보안 스캔 통과 (SAST/DAST)
- [ ] DB 마이그레이션 실행
- [ ] 환경 변수 설정 확인
- [ ] Rollback 계획 준비

---

## 🤝 기여

기여를 환영합니다! 다음 절차를 따라주세요:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**코딩 스타일**:
- Python: PEP 8, Black formatter
- TypeScript: Airbnb style guide, Prettier
- Commit: Conventional Commits

---

## 📊 프로젝트 현황

### Sprint 진행 상황

| Sprint | Period | Status | Epic |
|--------|--------|--------|------|
| Sprint 1 | Week 1-2 | 🚧 In Progress | Epic 1: Data Ingestion |
| Sprint 2 | Week 3-4 | ⏳ Planned | Epic 1: Data Ingestion |
| ... | ... | ... | ... |
| Sprint 16 | Week 31-32 | ⏳ Planned | MVP Launch |

**Total Progress**: 0 / 260 Story Points (0%)

### 마일스톤

- [ ] **Sprint 4**: Epic 1 완료 (약관 10개 수집 완료)
- [ ] **Sprint 8**: Query Engine 완료 (E2E 질의응답 동작)
- [ ] **Sprint 12**: 프론트엔드 완료 (모바일 PWA)
- [ ] **Sprint 15**: 보안/준법 완료 (금융 샌드박스 승인)
- [ ] **Sprint 16**: MVP 런칭 (베타 테스터 100명 온보딩)

---

## 📞 팀 & 연락처

| 역할 | 담당자 | 연락처 |
|------|--------|--------|
| Product Manager | TBD | pm@insuregraph.com |
| Tech Lead (Backend) | TBD | backend@insuregraph.com |
| Tech Lead (Frontend) | TBD | frontend@insuregraph.com |
| DevOps Engineer | TBD | devops@insuregraph.com |

**Slack**: #insuregraph-dev
**Jira**: https://insuregraph.atlassian.net

---

## 📜 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 🙏 감사의 말

- [Upstage](https://upstage.ai/) - 한국어 특화 LLM 및 OCR 제공
- [Neo4j](https://neo4j.com/) - Graph Database 기술
- [LangChain](https://langchain.com/) - LLM 오케스트레이션 프레임워크
- [FastAPI](https://fastapi.tiangolo.com/) - 고성능 Python 웹 프레임워크
- [Next.js](https://nextjs.org/) - React 프레임워크

---

**Built with ❤️ by InsureGraph Team**

**Last Updated**: 2025-11-25
