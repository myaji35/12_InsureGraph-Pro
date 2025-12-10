# Plane 이슈 업데이트 내용

**Plane 이슈 URL**: http://34.158.192.195/spaces/issues/14d8ec1a49934a46b5927d0fc033699f

이 내용을 Plane 이슈에 코멘트로 추가해주세요.

---

## 📊 개발 현황 업데이트 (2025-12-10)

**GitHub**: https://github.com/myaji35/12_InsureGraph-Pro
**커밋**: 892da47

---

### ✅ 완료된 주요 기능

#### 1. LLM 통합 및 최적화
- ✅ **Google Gemini 2.5 Flash** 통합 완료
  - 모델: `gemini-2.5-flash`
  - Temperature: 0.1, Max tokens: 2000
- ✅ 답변 품질 개선 (사과 표현 제거)
- ✅ LLM 모델명 UI 표시
- ✅ 중복 참고 문서 제거
- ✅ 상세 로깅 시스템 구축

**파일**: `backend/app/services/llm_reasoning.py`

#### 2. UI/UX 대폭 개선
- ✅ 폰트 크기 확대: 최소 14px (10pt)
- ✅ 전체 너비 레이아웃 적용
- ✅ 채팅 스타일 UI 구현
- ✅ 고령 사용자 최적화 (노안 대응)
- ✅ 질문/답변 분리 표시

**파일**: `frontend/src/app/ask/page.tsx`

#### 3. Neo4j 검색 확장
- ✅ 노드 타입: **3개 → 9개**로 확장
  - Article, Paragraph, Subclause
  - CoverageItem, Exclusion, BenefitAmount
  - PaymentCondition, Period, Term, Rider
- ✅ 검색 속성 확장: text, source_text, description
- ✅ 전체 노드 커버: **4,018개** (MetLife 데이터)

**파일**: `backend/app/services/local_search.py`

#### 4. Unstructured.io 청킹 시스템
- ✅ 보험 약관 전문 파싱
- ✅ 계층 구조 보존 (제N장, 제N조)
- ✅ 의미 기반 청킹
- ✅ Overlap 설정으로 문맥 유지

**파일**:
- `backend/app/services/smart_insurance_chunker.py`
- `backend/app/services/unstructured_chunker.py`

---

### 📈 성능 지표

| 항목 | 값 |
|------|-----|
| **Neo4j 노드** | 4,018개 |
| **보험사** | MetLife |
| **LLM 모델** | Gemini 2.5 Flash |
| **평균 응답 시간** | 2-3초 |
| **목표 정확도** | 80%+ |

---

### 🔧 기술 스택

**Backend**:
- FastAPI (Python)
- Neo4j 5.14 (APOC)
- PostgreSQL 15
- Redis 7
- Celery

**Frontend**:
- Next.js 14
- TypeScript
- Tailwind CSS

**LLM**:
- Google Gemini 2.5 Flash (주)
- Anthropic Claude (대체)
- OpenAI GPT (대체)
- Upstage Solar (임베딩)

**인프라**:
- Docker Compose
- Coolify
- GitHub

---

### 🐛 알려진 이슈

#### Issue #1: Gemini API Fallback
- **상태**: 디버깅 중
- **증상**: 일부 쿼리에서 23% 신뢰도로 fallback
- **원인**: API 응답 파싱 또는 프롬프트 개선 필요
- **다음 단계**: 상세 로그 분석 및 프롬프트 최적화

#### Issue #2: Unstructured.io 설치
- **상태**: 백그라운드 설치 중
- **다음 단계**: 설치 완료 후 약관 재학습

---

### 📚 생성된 문서

**개발 가이드**:
1. `DEV_SETUP_GUIDE.md` - 개발 환경 설정
2. `AUTH_GUIDE.md` - 인증 시스템
3. `CORS_FIX_SUMMARY.md` - CORS 이슈 해결

**배포 문서**:
4. `COOLIFY_DEPLOYMENT.md` - CLI 배포 가이드
5. `COOLIFY_UI_DEPLOYMENT.md` - UI 배포 상세
6. `COOLIFY_QUICK_DEPLOY.md` - 빠른 배포
7. `DEPLOYMENT_COMPLETE.md` - 배포 완료 보고서

**진행 상황**:
8. `DEVELOPMENT_PROGRESS.md` - 개발 진행 현황
9. `ERROR_RESOLUTION_SUMMARY.md` - 에러 해결

**Plane 연동**:
10. `PLANE_INTEGRATION.md` - Plane 협업 가이드
11. `PLANE_SYNC_README.md` - 동기화 가이드
12. `sync-to-plane.sh` - 자동 동기화 스크립트
13. `update-plane-issue.sh` - 이슈 업데이트 스크립트

---

### 📅 다음 계획

**단기 (이번 주)**:
- [ ] Gemini API 이슈 해결
- [ ] Unstructured.io 활용 재학습
- [ ] 답변 품질 측정 및 개선
- [ ] 사용자 테스트

**중기 (이번 달)**:
- [ ] 신뢰도 80%+ 달성
- [ ] 추가 보험사 데이터 (삼성, 현대, KB)
- [ ] 실시간 스트리밍 응답
- [ ] 모바일 UI 최적화

**장기 (분기)**:
- [ ] Multi-agent 시스템
- [ ] RAG 고도화 (하이브리드 검색)
- [ ] 피드백 학습 시스템
- [ ] Enterprise 기능 (권한, 감사)

---

## 🚀 배포 현황 업데이트 (2025-12-10)

**Coolify**: http://34.64.191.91
**도메인**: https://InsureGraphPro.34.64.191.91

---

### ✅ Coolify CLI 배포 인프라 구축 완료

#### 1. Coolify CLI 설정
- ✅ **CLI 버전**: 1.3.0
- ✅ **Context**: production
- ✅ **API URL**: http://34.64.191.91:8000
- ✅ **API 토큰**: 설정 완료

#### 2. 서버 추가
- ✅ **서버명**: coolify-insuregraph
- ✅ **UUID**: rc0s0w80gcksc00kkso0kwos
- ✅ **IP 주소**: 34.64.191.91
- ✅ **OS**: Linux AMD64
- ✅ **상태**: Reachable ✅, Usable ✅

#### 3. 프로젝트 생성
- ✅ **프로젝트명**: InsureGraphPro
- ✅ **UUID**: rsskss4gcwsgwo8w040gs4ks4
- ✅ **설명**: Insurance Knowledge Graph with GraphRAG
- ✅ **생성 방법**: Coolify API 직접 호출

#### 4. 애플리케이션 구성
- ✅ **애플리케이션명**: insuregraph-pro
- ✅ **UUID**: e04ggk4k4www8kkg44ks0sk4
- ✅ **타입**: Docker Compose (Public Repository)
- ✅ **GitHub**: https://github.com/myaji35/12_InsureGraph-Pro
- ✅ **브랜치**: main
- ✅ **Docker Compose 파일**: docker-compose.coolify.yml

#### 5. 배포 시작
- ✅ **Deployment UUID**: fk4cg804w8o444kggco0gsc4
- ✅ **커밋**: 892da47
- ⏳ **상태**: 환경변수 설정 대기

---

### 🐳 Docker Compose 서비스 구성 (6개)

#### 1. PostgreSQL
- **이미지**: postgres:15
- **컨테이너**: postgres-e04ggk4k4www8kkg44ks0sk4-124348780929
- **볼륨**: e04ggk4k4www8kkg44ks0sk4_postgres-data
- **헬스체크**: pg_isready ✅

#### 2. Redis
- **이미지**: redis:7-alpine
- **컨테이너**: redis-e04ggk4k4www8kkg44ks0sk4-124348822609
- **볼륨**: e04ggk4k4www8kkg44ks0sk4_redis-data
- **헬스체크**: redis-cli ping ✅

#### 3. Neo4j
- **이미지**: neo4j:5.14
- **컨테이너**: neo4j-e04ggk4k4www8kkg44ks0sk4-124348829757
- **볼륨**: neo4j-data, neo4j-logs
- **플러그인**: APOC
- **메모리**: 2G heap
- **헬스체크**: cypher-shell ✅

#### 4. Backend (FastAPI)
- **빌드**: ./backend/Dockerfile
- **컨테이너**: backend-e04ggk4k4www8kkg44ks0sk4-124348841567
- **포트**: 8080
- **헬스체크**: curl /api/v1/health ✅
- **의존성**: postgres, redis, neo4j (healthy 조건)

#### 5. Frontend (Next.js)
- **빌드**: ./frontend/Dockerfile.prod
- **컨테이너**: frontend-e04ggk4k4www8kkg44ks0sk4-124348880822
- **포트**: 3000
- **의존성**: backend

#### 6. Celery Worker
- **빌드**: ./backend/Dockerfile
- **컨테이너**: celery-worker-e04ggk4k4www8kkg44ks0sk4-124348883463
- **명령어**: celery -A app.celery_app worker --loglevel=info --concurrency=4
- **의존성**: postgres, redis, neo4j

---

### 🌐 배포 URL 설정 (통합 도메인)

#### 메인 도메인
- **도메인**: InsureGraphPro.34.64.191.91
- **프로토콜**: HTTPS (Let's Encrypt 예정)

#### 서비스 라우팅 (Traefik)
- **Frontend**: `Host(InsureGraphPro.34.64.191.91) && Path(/)`
- **Backend API**: `Host(InsureGraphPro.34.64.191.91) && PathPrefix(/api)`
- **Neo4j Browser**: `Host(InsureGraphPro.34.64.191.91) && PathPrefix(/neo4j)`

#### 접속 URL
- **메인**: https://InsureGraphPro.34.64.191.91
- **Frontend**: https://InsureGraphPro.34.64.191.91/
- **Backend API**: https://InsureGraphPro.34.64.191.91/api
- **API Docs**: https://InsureGraphPro.34.64.191.91/api/docs
- **Neo4j**: https://InsureGraphPro.34.64.191.91/neo4j

#### 포트 직접 접속 (대체)
- Frontend: http://34.64.191.91:18000
- Backend: http://34.64.191.91:18001
- Neo4j Browser: http://34.64.191.91:17474
- Neo4j Bolt: http://34.64.191.91:17687

---

### 🔧 환경변수 설정 필요 (Coolify Web UI)

```bash
# Database
POSTGRES_PASSWORD=InsureGraph2024!Prod!Secure
NEO4J_PASSWORD=Neo4j2024!Graph!Secure

# Security
SECRET_KEY=7K8mNpQ3rT9vX2bC5dF6gH8jK0lM4nP7qR9sT2uV5wX8yZ
JWT_SECRET_KEY=3aB5cD7eF9gH2iJ4kL6mN8oP0qR2sT4uV6wX8yZ1aB3cD5

# LLM API Keys (실제 키 입력 필요!)
ANTHROPIC_API_KEY=<your-key>
GOOGLE_API_KEY=<your-key>
OPENAI_API_KEY=<your-key>
UPSTAGE_API_KEY=<your-key>

# CORS
CORS_ORIGINS=https://InsureGraphPro.34.64.191.91,http://InsureGraphPro.34.64.191.91,http://localhost:3000

# Frontend
NEXT_PUBLIC_API_URL=https://InsureGraphPro.34.64.191.91/api
```

---

### 📚 배포 문서 (8개)

1. **COOLIFY_DEPLOYMENT.md** - CLI 배포 가이드
2. **COOLIFY_UI_DEPLOYMENT.md** - UI 배포 상세 가이드
3. **COOLIFY_QUICK_DEPLOY.md** - 5단계 빠른 배포
4. **COOLIFY_DEPLOYMENT_STATUS.md** - 배포 현황 보고서
5. **DEPLOYMENT_COMPLETE.md** - 배포 완료 체크리스트
6. **deploy-to-coolify.sh** - 자동 배포 스크립트
7. **.coolify.env** - 환경변수 템플릿
8. **docker-compose.coolify.yml** - Docker Compose 설정

---

### ⏳ 다음 단계

**즉시 (환경변수 설정)**:
1. [ ] Coolify Web UI 접속: http://34.64.191.91
2. [ ] 애플리케이션 선택: insuregraph-pro
3. [ ] Environment 탭: 환경변수 추가
4. [ ] Deploy 버튼: 배포 재시작
5. [ ] 로그 모니터링: 빌드 및 실행 확인

**배포 후 (설정 및 검증)**:
6. [ ] 헬스체크: 모든 서비스 Running 확인
7. [ ] 데이터베이스 마이그레이션: `alembic upgrade head`
8. [ ] Neo4j 인덱스: 검색 최적화 인덱스 생성
9. [ ] 접속 테스트: Frontend, Backend API 확인
10. [ ] 모니터링 설정: 로그, 메트릭 수집

---

### 🔗 관련 링크

**Coolify**:
- 대시보드: http://34.64.191.91
- 프로젝트: http://34.64.191.91/project/rsskss4gcwsgwo8w040gs4ks4
- 애플리케이션: http://34.64.191.91/project/rsskss4gcwsgwo8w040gs4ks4/application/e04ggk4k4www8kkg44ks0sk4

**GitHub**:
- 저장소: https://github.com/myaji35/12_InsureGraph-Pro
- 커밋: https://github.com/myaji35/12_InsureGraph-Pro/commit/892da47

**배포 후 접속**:
- Frontend: https://InsureGraphPro.34.64.191.91
- API: https://InsureGraphPro.34.64.191.91/api
- Docs: https://InsureGraphPro.34.64.191.91/api/docs

---

**상태**: 인프라 구축 완료 ✅, 환경변수 설정 및 배포 대기 ⏳
**우선순위**: High
**담당자**: DevOps / 배포 팀
