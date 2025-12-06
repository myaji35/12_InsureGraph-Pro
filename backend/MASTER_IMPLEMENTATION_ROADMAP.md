# InsureGraph Pro - 통합 구현 로드맵

**작성일**: 2025-12-05
**버전**: 2.0
**목표**: Phase 1 (기반) → Phase 2 (차별화) → Phase 3 (관리) 통합 구현

---

## 📋 전체 시스템 개요

### 핵심 비전
```
"AI 기반 보험 Graph RAG 플랫폼에서
 FP 루틴 관리 및 팀 성과 예측,
 전보험사 데이터 통합까지"

Phase 1: 기술 기반 구축 (완료)
  └─ GraphRAG, Neo4j, LLM 통합

Phase 2: 비즈니스 차별화 ⭐ 현재
  └─ Google 연동, 보장 분석, 내보험다보여

Phase 3: 조직 관리 혁신 ⭐ 신규
  └─ FP 루틴, 팀장 코칭, 실적 예측

Phase 4: 데이터 확장 ⭐ 신규
  └─ 30개 보험사, 전상품, 법원판례 통합
```

---

## 🎯 통합 Epic 구조

```
InsureGraph Pro
├── Phase 1: 기반 시스템 (완료) ✅
│   ├── Epic 1.1: GraphRAG 엔진
│   ├── Epic 1.2: 문서 크롤링
│   ├── Epic 1.3: 엔티티 추출
│   └── Epic 1.4: 질의응답 시스템
│
├── Phase 2: 비즈니스 차별화 (진행중) 🔄
│   ├── Epic 2.1: Google Contacts 연동
│   ├── Epic 2.2: 보장 갭 분석
│   ├── Epic 2.3: 내보험다보여 차별화
│   ├── Epic 2.4: 계약서 OCR & 문서 생성
│   └── Epic 2.5: AI 컨설팅 고도화
│
├── Phase 3: 조직 관리 혁신 (신규) 🆕
│   ├── Epic 3.1: FP 루틴 자동화
│   ├── Epic 3.2: 팀장 성과 관리
│   ├── Epic 3.3: 코칭 시스템
│   └── Epic 3.4: 실적 예측 & 지점장 대시보드
│
└── Phase 4: 데이터 확장 (신규) 🆕
    ├── Epic 4.1: 30개 보험사 관리 시스템
    ├── Epic 4.2: 전상품 데이터 수집 (1차)
    ├── Epic 4.3: 법원판례 통합
    └── Epic 4.4: 과거 자료 확장 (연간 반복)
```

---

## 📅 통합 개발 일정

### 전체 타임라인 (62주 = 15.5개월)

```
┌─────────────────────────────────────────────────────────┐
│  Timeline Overview                                      │
├─────────────────────────────────────────────────────────┤
│  Phase 1 (완료): Week -20 ~ Week 0  [████████████] 100%│
│  Phase 2 (진행): Week 1  ~ Week 20  [████░░░░░░░]  40% │
│  Phase 3 (예정): Week 21 ~ Week 40  [░░░░░░░░░░]   0% │
│  Phase 4 (예정): Week 41 ~ Week 62  [░░░░░░░░░░]   0% │
└─────────────────────────────────────────────────────────┘

현재 위치: Week 8 (Phase 2 진행 중)
다음 마일스톤: Week 20 (Phase 2 완료)
최종 마일스톤: Week 62 (Phase 4 완료, 서비스 개시)
```

---

## Phase 2: 비즈니스 차별화 (Week 1-20)

### Epic 2.1: Google Contacts 연동 & 고객 관리

**기간**: Week 1-4 (4주)
**Story Points**: 34
**담당**: Backend 1명, Frontend 1명

#### Stories
```
Week 1:
  ✅ Story 2.1.1: Google OAuth 2.0 인증 (8pt)
    - OAuth 클라이언트 설정
    - Token 관리
    - 프론트엔드 연동 버튼

Week 2-3:
  🔄 Story 2.1.2: #고객 태그 필터링 및 동기화 (13pt)
    - Google Contacts API 통합
    - Celery 비동기 동기화
    - 중복 병합 로직

Week 4:
  ⏳ Story 2.1.3: 고객 프로필 통합 관리 (8pt)
    - 프로필 페이지
    - 메모 기능
    - 태그 관리

  ⏳ Story 2.1.4: 라이프사이클 이벤트 자동 감지 (5pt)
    - 생일 알림
    - 결혼 기념일
    - 퇴직 예정일
```

#### Deliverables
- [ ] `/api/v1/google/auth` 엔드포인트
- [ ] `/fp/customers` 고객 목록 페이지
- [ ] `/fp/customers/:id` 고객 상세 페이지
- [ ] Celery worker: `worker_google_sync.py`

---

### Epic 2.2: 보장 갭 분석 & 추천

**기간**: Week 5-10 (6주)
**Story Points**: 55
**담당**: Backend 2명, Frontend 1명, AI Engineer 1명

#### Stories
```
Week 5-6:
  ⏳ Story 2.2.1: 내보험다보여 API 연동 (13pt)
    - API 클라이언트
    - 데이터 파싱
    - PostgreSQL 저장

Week 7-9:
  ⏳ Story 2.2.2: AI 기반 보장 갭 분석 엔진 (21pt)
    - 필수 보장 계산
    - 갭/중복 탐지
    - GraphRAG 추천
    - 리포트 생성

Week 10:
  ⏳ Story 2.2.3: 가족 통합 포트폴리오 (13pt)
    - 가족 구성원 관리
    - 가족 갭 분석
    - 최적화 제안

  ⏳ Story 2.2.4: 보험료 절감 시뮬레이터 (8pt)
    - 절감액 계산
    - 최적화 실행
```

#### Deliverables
- [ ] `/api/v1/myinsurance/sync`
- [ ] `/api/v1/analysis/gap`
- [ ] `/api/v1/family/portfolio`
- [ ] `/analysis/gap` 갭 분석 페이지
- [ ] `/analysis/family` 가족 분석 페이지

---

### Epic 2.3: 내보험다보여 차별화

**기간**: Week 11-14 (4주)
**Story Points**: 34
**담당**: Backend 1명, Frontend 1명, AI Engineer 1명

#### Stories
```
Week 11-13:
  ⏳ Story 2.3.1: GraphRAG 약관 해석 엔진 (21pt)
    - 약관 자동 조회
    - GraphRAG 탐색
    - LLM 해석
    - 약관 비교

Week 14:
  ⏳ Story 2.3.2: AI 챗봇 - 보험 Q&A (13pt)
    - 24/7 챗봇
    - 맥락 인식
    - 대화 히스토리
```

#### Deliverables
- [ ] `/api/v1/policy/interpret`
- [ ] `/api/v1/chatbot/ask`
- [ ] `/ask` 챗봇 페이지 확장

---

### Epic 2.4: 계약서 OCR & 문서 생성

**기간**: Week 15-18 (4주)
**Story Points**: 34
**담당**: Backend 1명, Frontend 1명

#### Stories
```
Week 15-16:
  ⏳ Story 2.4.1: Upstage Document Parse 통합 (13pt)
    - Upstage API 연동
    - 하이브리드 전략
    - 처리 진행률

Week 17:
  ⏳ Story 2.4.2: LLM 정보 추출 (13pt)
    - 보험사명, 상품명 추출
    - 보장 내용 추출
    - 검증 UI

Week 18:
  ⏳ Story 2.4.3: DOCX 요약서 생성 (5pt)
    - python-docx 활용
    - 템플릿 삽입
    - 다운로드

  ⏳ Story 2.4.4: XLSX 비교표 생성 (3pt)
    - openpyxl 활용
    - 차트 생성
```

#### Deliverables
- [ ] `/api/v1/ocr/upload`
- [ ] `/api/v1/documents/docx`
- [ ] `/api/v1/documents/xlsx`
- [ ] `/documents/ocr` OCR 페이지

---

### Epic 2.5: AI 컨설팅 고도화

**기간**: Week 19-20 (2주)
**Story Points**: 21
**담당**: AI Engineer 1명, Backend 1명

#### Stories
```
Week 19:
  ⏳ Story 2.5.1: 개인화 추천 알고리즘 (13pt)
    - 협업 필터링
    - GraphRAG 유사도
    - A/B 테스트

Week 20:
  ⏳ Story 2.5.2: 보험료 갱신 알림 자동화 (8pt)
    - Celery 스케줄러
    - 갱신 알림
    - 추천 상품
```

#### Deliverables
- [ ] `/api/v1/recommendations/personal`
- [ ] `worker_renewal_alerts.py`

---

## Phase 3: 조직 관리 혁신 (Week 21-40)

### Epic 3.1: FP 루틴 자동화

**기간**: Week 21-26 (6주)
**Story Points**: 55
**담당**: Backend 2명, Frontend 1명

#### Stories
```
Week 21-22:
  ⏳ Story 3.1.1: 일일 루틴 시스템 (13pt)
    - 데일리 체크인
    - 문자 일괄 발송
    - 전화 스크립트
    - 데일리 리뷰

Week 23-24:
  ⏳ Story 3.1.2: 주간 루틴 시스템 (13pt)
    - Weekly Planning
    - 우선순위 고객 선정
    - Weekly Review

Week 25-26:
  ⏳ Story 3.1.3: 월간 루틴 시스템 (21pt)
    - 월간 목표 설정
    - 중간 점검
    - Monthly Review

  ⏳ Story 3.1.4: 고객 접점 스토리 자동 생성 (8pt)
    - 생일 고객 스토리
    - 신규 고객 육성 스토리
```

#### Deliverables
- [ ] `/api/v1/fp/routine/daily`
- [ ] `/api/v1/fp/routine/weekly`
- [ ] `/api/v1/fp/routine/monthly`
- [ ] `/fp/dashboard` FP 대시보드
- [ ] `/fp/customers/:id/story` 고객 접점 스토리

---

### Epic 3.2: 팀장 성과 관리

**기간**: Week 27-32 (6주)
**Story Points**: 55
**담당**: Backend 2명, Frontend 1명, Data Scientist 1명

#### Stories
```
Week 27-28:
  ⏳ Story 3.2.1: 팀원 활동 실시간 모니터링 (13pt)
    - 활동 로그 집계
    - 실시간 업데이트 (WebSocket)
    - 목표 대비 달성률

Week 29-30:
  ⏳ Story 3.2.2: 즉시 조치 알림 시스템 (13pt)
    - 활동량 부족 감지
    - 전화 연결률 낮음 감지
    - 푸시 알림

Week 31-32:
  ⏳ Story 3.2.3: 일일 팀 현황 대시보드 (21pt)
    - 팀 진행률
    - FP별 활동 테이블
    - AI 인사이트
    - 트렌드 차트

  ⏳ Story 3.2.4: 주간 팀 성과 리포트 (8pt)
    - Best Practice 추출
    - PDF 생성
    - 이메일 자동 발송
```

#### Deliverables
- [ ] `/api/v1/team/activity/realtime`
- [ ] `/api/v1/team/alerts`
- [ ] `/api/v1/team/dashboard`
- [ ] `/team/dashboard` 팀장 대시보드
- [ ] `/team/reports` 주간 리포트
- [ ] `worker_weekly_report.py`

---

### Epic 3.3: 코칭 시스템

**기간**: Week 33-38 (6주)
**Story Points**: 55
**담당**: Backend 2명, Frontend 1명, AI Engineer 1명

#### Stories
```
Week 33-34:
  ⏳ Story 3.3.1: FP 개인 성과 분석 (13pt)
    - 점수 계산
    - 강점/약점 진단
    - 성과 리포트

Week 35-37:
  ⏳ Story 3.3.2: 원포인트 레슨 자동 생성 (21pt)
    - 10종 템플릿
    - AI 커스터마이징
    - 진행 추적

Week 37-38:
  ⏳ Story 3.3.3: 4주 코칭 플랜 (13pt)
    - 주차별 목표
    - 일일 체크리스트
    - 진행률 시각화

  ⏳ Story 3.3.4: 팀 코칭 회의 자료 (8pt)
    - 공통 패턴 분석
    - PPT 생성
```

#### Deliverables
- [ ] `/api/v1/coaching/analysis`
- [ ] `/api/v1/coaching/lesson`
- [ ] `/api/v1/coaching/plan`
- [ ] `/team/coaching` 코칭 페이지
- [ ] `/team/coaching/:fpId` 개인 코칭 플랜

---

### Epic 3.4: 실적 예측 & 지점장 대시보드

**기간**: Week 39-40 (2주)
**Story Points**: 34
**담당**: Data Scientist 1명, Backend 1명, Frontend 1명

#### Stories
```
Week 39:
  ⏳ Story 3.4.1: 월간 실적 예측 엔진 (21pt)
    - 단순 예측
    - AI 보정
    - 신뢰 구간
    - 정확도 추적

Week 40:
  ⏳ Story 3.4.2: 연간 실적 예측 (13pt)
    - 시나리오 분석
    - 월별 목표 배분
    - ROI 계산

  ⏳ Story 3.4.3: 지점장 통합 대시보드 (선택)
    - 팀별 비교
    - Top/Bottom Performer
    - 트렌드 분석
```

#### Deliverables
- [ ] `/api/v1/prediction/monthly`
- [ ] `/api/v1/prediction/yearly`
- [ ] `/api/v1/branch/dashboard`
- [ ] `/branch/dashboard` 지점장 대시보드
- [ ] `/branch/predictions` 실적 예측 페이지

---

## Phase 4: 데이터 확장 (Week 41-62)

### Epic 4.1: 30개 보험사 관리 시스템

**기간**: Week 41-42 (2주)
**Story Points**: 13
**담당**: Backend 1명, Frontend 1명

#### Stories
```
Week 41-42:
  ⏳ Story 4.1.1: 보험사 마스터 관리 (13pt)
    - 30개 보험사 CRUD
    - 메타데이터 관리 (상호명, URL, 전화번호, 주소, 사업자번호, 대표이사)
    - 상품 목록 연동
    - 크롤러 설정 관리
    - 관리자 UI
```

#### Deliverables
- [ ] `/api/v1/insurers` CRUD 엔드포인트
- [ ] `/admin/insurers` 보험사 관리 페이지
- [ ] 30개 보험사 초기 데이터 Seed

---

### Epic 4.2: 전상품 데이터 수집 (1차)

**기간**: Week 43-54 (12주)
**Story Points**: 89
**담당**: Backend 3명, Frontend 1명, Crawler Engineer 2명

#### Stories
```
Week 43-44:
  ⏳ Story 4.2.1: 상품 카테고리 체계 구축 (13pt)
    - 생명보험: 종신, 정기, 연금, 변액, 저축성
    - 손해보험: 자동차, 실손, 암, 여행, 배상책임
    - 특약: 재해, 질병, 수술, 입원
    - 카테고리 계층 구조 (대분류→중분류→소분류)

Week 45:
  ⏳ Story 4.2.2: 상품 메타데이터 모델 설계 (8pt)
    - 상품 기본 정보 모델
    - 문서 관리 (설명서, 약관, 특약)
    - 학습 상태 관리 (미학습/학습/초기화)
    - 버전 관리

Week 46-53:
  ⏳ Story 4.2.3: 보험사별 크롤러 구현 (55pt, 8주)
    - 30개 보험사 각각 크롤러 구현
    - 상품 목록 페이지 크롤링
    - 상품설명서/약관/특약 PDF 다운로드
    - 크롤링 진행률 표시
    - 실패 재시도 로직
    - 결과 검증

Week 54:
  ⏳ Story 4.2.4: 학습 관리 시스템 (13pt)
    - 문서별 학습 상태 관리
    - 학습 시작 및 진행률 표시
    - 학습 결과 검증
    - 초기화 기능 (재학습)
    - 학습 이력 조회
```

#### Deliverables
- [ ] `/api/v1/categories` 카테고리 API
- [ ] `/api/v1/products` 상품 API
- [ ] 30개 보험사 크롤러 클래스
- [ ] `/admin/crawlers` 크롤러 관리 UI
- [ ] `/admin/learning` 학습 관리 UI
- [ ] `worker_product_crawler.py` Celery worker
- [ ] `worker_document_learner.py` Celery worker

**예상 데이터 규모**:
- 보험사: 30개
- 상품: 500-1,000개
- 문서: 2,000-3,000개

---

### Epic 4.3: 법원판례 통합

**기간**: Week 55-62 (8주)
**Story Points**: 55
**담당**: Backend 2명, AI Engineer 1명, Frontend 1명

#### Stories
```
Week 55:
  ⏳ Story 4.3.1: 판례 데이터 모델 설계 (8pt)
    - 판례 기본 정보 (사건번호, 법원, 판결일)
    - 사건 종류 (형사/민사)
    - 원고/피고
    - 판결문 텍스트
    - 핵심 쟁점
    - 관련 보험 상품

Week 56-58:
  ⏳ Story 4.3.2: 대법원 판례 크롤러 구현 (21pt)
    - 대법원 종합법률정보 크롤링
    - 검색 조건: "보험" + 2024.12-2025.12
    - 형사/민사 판례 분리
    - 판결문 전문 다운로드
    - 페이징 처리
    - 중복 제거

Week 59-61:
  ⏳ Story 4.3.3: 판례 AI 분석 및 학습 (21pt)
    - LLM 기반 핵심 쟁점 추출
    - 관련 보험 종류 자동 태깅
    - 판결 요지 자동 요약
    - Neo4j 저장 (판례 노드)
    - 보험 상품 노드와 연결

Week 62:
  ⏳ Story 4.3.4: 판례 검색 및 활용 (5pt)
    - 판례 검색 API
    - 질의응답 시 관련 판례 표시
    - 판례 상세 페이지
```

#### Deliverables
- [ ] `/api/v1/cases` 판례 API
- [ ] `/cases` 판례 검색 페이지
- [ ] `/cases/:id` 판례 상세 페이지
- [ ] `worker_case_crawler.py` Celery worker
- [ ] `worker_case_analyzer.py` Celery worker

**예상 데이터 규모**:
- 판례 (1년): 500-1,000건

---

### Epic 4.4: 과거 자료 확장

**기간**: 연간 반복 (Week 62 이후)
**Story Points**: N/A
**담당**: Maintenance Team

#### Stories
```
연간 반복:
  ⏳ Story 4.4.1: 상품 히스토리 수집 (연도별)
    - 1차 완료 후 1년 단위 과거 상품 수집
    - 버전 관리 (동일 상품의 연도별 개정)
    - 차이 분석 (올해 vs 작년)

  ⏳ Story 4.4.2: 판례 히스토리 수집 (연도별)
    - 1차 완료 후 1년 단위 과거 판례 수집
    - 연도별 통계 (판례 개수, 주요 쟁점)
```

#### Deliverables
- [ ] 연간 크롤링 스케줄러
- [ ] 버전 비교 분석 도구
- [ ] 연도별 통계 리포트

**5년 누적 예상 데이터**:
- 상품 (버전 포함): 3,000-5,000개
- 문서: 10,000-15,000개
- 판례 (5년): 2,500-5,000건

---

## 🏗️ 기술 스택 통합

### Frontend
```typescript
- Next.js 14 (App Router)
- React 18
- TypeScript
- Tailwind CSS
- ReactFlow (그래프 시각화)
- Recharts (차트)
- WebSocket (실시간 업데이트)
```

### Backend
```python
- FastAPI
- Python 3.11+
- SQLAlchemy (ORM)
- Alembic (마이그레이션)
- Celery (비동기 작업)
- WebSocket (실시간)
```

### Databases
```
- PostgreSQL 15 (관계형 데이터)
- Neo4j 5.x (그래프 데이터)
- Redis 7.x (캐시, Celery 브로커)
```

### AI/ML
```python
- Anthropic Claude 3.5 Sonnet (LLM)
- OpenAI GPT-4 (대안 LLM)
- Upstage Document Parse (OCR)
- scikit-learn (ML 모델)
- sentence-transformers (임베딩)
```

### Infrastructure
```
- Docker & Docker Compose
- AWS EC2 / Google Cloud
- GitHub Actions (CI/CD)
- Sentry (모니터링)
```

---

## 📊 데이터베이스 스키마 통합

### 핵심 테이블 구조

```sql
-- =============================================
-- Phase 1: 기반 시스템 (완료)
-- =============================================

-- 사용자 및 인증
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE,
  hashed_password TEXT,
  name TEXT,
  role TEXT, -- 'fp', 'team_leader', 'branch_manager', 'admin'
  created_at TIMESTAMP DEFAULT NOW()
);

-- 문서 및 크롤링
CREATE TABLE crawler_documents (
  id UUID PRIMARY KEY,
  url TEXT,
  title TEXT,
  content TEXT,
  metadata JSONB,
  status TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- Phase 2: 비즈니스 차별화
-- =============================================

-- Google OAuth 토큰
CREATE TABLE google_tokens (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  access_token TEXT NOT NULL,
  refresh_token TEXT,
  expires_at TIMESTAMP,
  scopes TEXT[],
  created_at TIMESTAMP DEFAULT NOW()
);

-- FP 고객 (Google 주소록)
CREATE TABLE fp_customers_google (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  google_id TEXT UNIQUE,
  name TEXT,
  email TEXT,
  phone TEXT,
  birthday DATE,
  tags TEXT[],
  notes TEXT,
  last_synced_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 사용자 보험 가입 내역 (내보험다보여)
CREATE TABLE user_insurances (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  insurer_name TEXT,
  product_name TEXT,
  contract_number TEXT,
  coverage_type TEXT,
  coverage_amount NUMERIC,
  premium NUMERIC,
  start_date DATE,
  end_date DATE,
  source TEXT, -- 'myinsurance', 'manual', 'ocr'
  raw_data JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 보장 갭 분석 결과
CREATE TABLE coverage_gap_analysis (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  analysis_date TIMESTAMP DEFAULT NOW(),
  gaps JSONB,
  overlaps JSONB,
  recommendations JSONB,
  coverage_score NUMERIC,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 가족 구성원
CREATE TABLE family_members (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  name TEXT,
  relationship TEXT,
  birth_date DATE,
  customer_id UUID REFERENCES fp_customers(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- Phase 3: 조직 관리 혁신
-- =============================================

-- 조직 구조
CREATE TABLE branches (
  id UUID PRIMARY KEY,
  name TEXT,
  manager_id UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE teams (
  id UUID PRIMARY KEY,
  name TEXT,
  branch_id UUID REFERENCES branches(id),
  leader_id UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- FP-팀 매핑
CREATE TABLE team_members (
  id UUID PRIMARY KEY,
  team_id UUID REFERENCES teams(id),
  fp_id UUID REFERENCES users(id),
  joined_at TIMESTAMP DEFAULT NOW()
);

-- FP 활동 로그
CREATE TABLE fp_activity_logs (
  id UUID PRIMARY KEY,
  fp_id UUID REFERENCES users(id),
  activity_type TEXT, -- 'message', 'call', 'meeting', 'contract'
  activity_date DATE,
  activity_time TIME,
  customer_id UUID,
  result TEXT,
  duration_minutes INT,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- FP 일일 목표
CREATE TABLE fp_daily_targets (
  id UUID PRIMARY KEY,
  fp_id UUID REFERENCES users(id),
  target_date DATE,
  message_target INT DEFAULT 25,
  call_target INT DEFAULT 8,
  meeting_target INT DEFAULT 3,
  contract_target INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 팀 알림
CREATE TABLE team_alerts (
  id UUID PRIMARY KEY,
  team_id UUID REFERENCES teams(id),
  fp_id UUID REFERENCES users(id),
  alert_type TEXT,
  priority TEXT,
  message TEXT,
  action TEXT,
  is_read BOOLEAN DEFAULT FALSE,
  is_resolved BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- FP 성과 점수
CREATE TABLE fp_performance_scores (
  id UUID PRIMARY KEY,
  fp_id UUID REFERENCES users(id),
  period_type TEXT,
  period_start DATE,
  period_end DATE,
  total_score NUMERIC,
  activity_score NUMERIC,
  efficiency_score NUMERIC,
  performance_score NUMERIC,
  rank_in_team INT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 약점 진단
CREATE TABLE fp_weakness_diagnoses (
  id UUID PRIMARY KEY,
  fp_id UUID REFERENCES users(id),
  diagnosis_date DATE,
  category TEXT,
  severity TEXT,
  gap_value NUMERIC,
  root_cause TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 원포인트 레슨
CREATE TABLE one_point_lessons (
  id UUID PRIMARY KEY,
  fp_id UUID REFERENCES users(id),
  team_leader_id UUID REFERENCES users(id),
  lesson_type TEXT,
  title TEXT,
  problem TEXT,
  solution TEXT,
  checklist JSONB,
  success_metric TEXT,
  status TEXT DEFAULT 'pending',
  assigned_date DATE,
  completed_date DATE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 코칭 플랜 진행 상황
CREATE TABLE coaching_plan_progress (
  id UUID PRIMARY KEY,
  plan_id UUID REFERENCES one_point_lessons(id),
  week_number INT,
  checklist_item TEXT,
  is_completed BOOLEAN DEFAULT FALSE,
  completed_date DATE,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 실적 예측
CREATE TABLE performance_predictions (
  id UUID PRIMARY KEY,
  team_id UUID REFERENCES teams(id),
  prediction_date DATE,
  prediction_type TEXT,
  current_performance INT,
  simple_prediction NUMERIC,
  ai_prediction NUMERIC,
  confidence_min NUMERIC,
  confidence_max NUMERIC,
  target INT,
  gap INT,
  achievement_probability NUMERIC,
  actual_performance INT,
  accuracy NUMERIC,
  created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================
-- Phase 4: 데이터 확장
-- =============================================

-- 보험사 마스터
CREATE TABLE insurers (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  display_name TEXT,
  website_url TEXT,
  phone TEXT,
  address TEXT,
  business_number TEXT UNIQUE,
  ceo_name TEXT,
  insurer_type TEXT, -- 'life', 'non-life', 'both'
  logo_url TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  crawler_config JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 상품 카테고리
CREATE TABLE product_categories (
  id UUID PRIMARY KEY,
  parent_id UUID REFERENCES product_categories(id),
  name TEXT NOT NULL,
  display_name TEXT,
  category_type TEXT, -- 'major', 'middle', 'minor'
  sort_order INT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 보험 상품
CREATE TABLE products (
  id UUID PRIMARY KEY,
  insurer_id UUID REFERENCES insurers(id),
  category_id UUID REFERENCES product_categories(id),
  product_code TEXT,
  name TEXT NOT NULL,
  display_name TEXT,
  description TEXT,
  sale_start_date DATE,
  sale_end_date DATE,
  insurance_period TEXT,
  payment_period TEXT,
  min_age INT,
  max_age INT,
  is_selling BOOLEAN DEFAULT TRUE,
  version INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 상품 문서
CREATE TABLE product_documents (
  id UUID PRIMARY KEY,
  product_id UUID REFERENCES products(id),
  document_type TEXT, -- 'brochure', 'terms', 'rider'
  title TEXT,
  file_url TEXT,
  file_size BIGINT,
  crawled_at TIMESTAMP,
  learning_status TEXT DEFAULT 'pending', -- 'pending', 'learned', 'reset'
  learned_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 문서 학습 이력
CREATE TABLE document_learning_logs (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES product_documents(id),
  status TEXT, -- 'started', 'completed', 'failed', 'reset'
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  error_message TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 크롤링 진행 상황
CREATE TABLE crawler_progress (
  id UUID PRIMARY KEY,
  insurer_id UUID REFERENCES insurers(id),
  total_products INT,
  crawled_products INT,
  failed_products INT,
  status TEXT, -- 'running', 'completed', 'failed'
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 법원 판례
CREATE TABLE court_cases (
  id UUID PRIMARY KEY,
  case_number TEXT UNIQUE,
  case_name TEXT,
  court_name TEXT,
  case_type TEXT, -- 'criminal', 'civil'
  judgment_date DATE,
  plaintiff TEXT,
  defendant TEXT,
  judgment_summary TEXT,
  full_text TEXT,
  key_issues JSONB,
  related_products TEXT[],
  source_url TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 판례 학습 이력
CREATE TABLE case_learning_logs (
  id UUID PRIMARY KEY,
  case_id UUID REFERENCES court_cases(id),
  status TEXT,
  entity_count INT,
  learned_at TIMESTAMP,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📊 성과 지표 (종합 KPI)

### Phase 2 목표 (Week 1-20)

| 지표 | 목표 |
|-----|------|
| **Google 주소록 연동률** | 60% |
| **보장 갭 분석 사용률** | 80% |
| **계약서 OCR 성공률** | 90% |
| **AI 챗봇 사용률** | 50% |
| **추천 보험 전환율** | 10% |

### Phase 3 목표 (Week 21-40)

| 지표 | 목표 |
|-----|------|
| **FP 일일 활동량** | +200% |
| **팀장 관리 시간** | -75% |
| **코칭 정확도** | 90% |
| **실적 예측 정확도** | 85% |
| **FP 이탈률** | -67% |

### Phase 4 목표 (Week 41-62)

| 지표 | 목표 |
|-----|------|
| **보험사 커버리지** | 100% (30개) |
| **상품 수집률** | > 90% |
| **문서 완전성** | > 95% |
| **크롤링 성공률** | > 85% |
| **학습 성공률** | > 90% |
| **판례 수집** | > 500건 |

---

## 💰 통합 예산

### 개발 비용

| Phase | 기간 | 인력 | 예상 비용 |
|-------|------|------|----------|
| **Phase 2** | 20주 | 4명 | $150,000 |
| **Phase 3** | 20주 | 4명 | $150,000 |
| **Phase 4** | 22주 | 6명 | $200,000 |
| **총계** | 62주 | | **$500,000** |

### 월간 운영 비용 (FP 15명 + 데이터 확장)

| 항목 | 비용 |
|-----|------|
| **Anthropic API** | $200-500 |
| **Upstage OCR** | $50-150 |
| **서버 호스팅** | $200 |
| **데이터베이스 (PostgreSQL)** | $100 |
| **스토리지 (10TB, Phase 4)** | $200 |
| **크롤링 서버 (Phase 4)** | $150 |
| **LLM API - 판례 분석 (Phase 4)** | $300 |
| **총계** | **$1,200-1,600/월** |

---

## 🚀 구현 시작 가이드

### Phase 2 시작 (현재)

```bash
# 1. 환경 설정
cd backend
cp .env.example .env
# GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET 설정

# 2. 데이터베이스 마이그레이션
alembic revision --autogenerate -m "Add Phase 2 tables"
alembic upgrade head

# 3. 개발 시작
git checkout -b feature/epic-2.1-google-oauth

# 4. Story 2.1.1 개발
- Google OAuth 구현
- 프론트엔드 연동
```

### Phase 3 시작 (Week 21)

```bash
# 1. Phase 3 테이블 추가
alembic revision --autogenerate -m "Add Phase 3 team management tables"
alembic upgrade head

# 2. 개발 시작
git checkout -b feature/epic-3.1-fp-routine

# 3. Story 3.1.1 개발
- FP 일일 루틴 시스템
- 활동 로그 수집
```

---

## 📞 팀 구성 (통합)

### 현재 팀 (Phase 2)

1. **Backend Developer** (2명)
   - Google OAuth, 내보험다보여 연동
   - 보장 갭 분석 엔진
   - OCR 통합

2. **Frontend Developer** (1명)
   - 고객 관리 UI
   - 갭 분석 대시보드
   - 문서 생성 UI

3. **AI Engineer** (1명)
   - GraphRAG 최적화
   - LLM 프롬프트 엔지니어링
   - 추천 알고리즘

### Phase 3 팀 (추가 필요)

4. **Data Scientist** (1명) - 신규 채용
   - 실적 예측 모델
   - ML 알고리즘
   - 통계 분석

5. **QA Engineer** (1명) - 신규 채용
   - 테스트 자동화
   - 통합 테스트
   - 성능 테스트

---

## 🎯 마일스톤

### 2025년 Q4 (현재-Week 13)

```
✅ Week 0: Phase 1 완료
🔄 Week 1-4: Epic 2.1 (Google Contacts)
⏳ Week 5-10: Epic 2.2 (보장 갭 분석)
⏳ Week 11-13: Epic 2.3 (내보험다보여)
```

### 2026년 Q1 (Week 14-26)

```
⏳ Week 14-18: Epic 2.4 (OCR & 문서 생성)
⏳ Week 19-20: Epic 2.5 (AI 컨설팅)
🎉 Week 20: Phase 2 완료 (MVP 출시)

⏳ Week 21-26: Epic 3.1 (FP 루틴)
```

### 2026년 Q2 (Week 27-40)

```
⏳ Week 27-32: Epic 3.2 (팀장 성과 관리)
⏳ Week 33-38: Epic 3.3 (코칭 시스템)
⏳ Week 39-40: Epic 3.4 (실적 예측)
🎉 Week 40: Phase 3 완료 (Enterprise 출시)
```

### 2026년 Q3 (Week 41-54)

```
⏳ Week 41-42: Epic 4.1 (30개 보험사 관리)
⏳ Week 43-54: Epic 4.2 (전상품 데이터 수집 1차)
```

### 2026년 Q4 (Week 55-62)

```
⏳ Week 55-62: Epic 4.3 (법원판례 통합)
🎉 Week 62: Phase 4 완료 → 서비스 개시
```

### 2027년 이후 (연간 반복)

```
📅 매년 Q1: Epic 4.4.1 (전년도 상품 수집, 3개월)
📅 매년 Q2: Epic 4.4.2 (전년도 판례 수집, 1개월)
```

---

## ✅ Definition of Done (통합)

모든 Story는 다음 조건을 충족해야 완료:

### 1. 기능 완성
- [ ] 모든 Acceptance Criteria 충족
- [ ] 단위 테스트 작성 (커버리지 > 80%)
- [ ] 통합 테스트 통과
- [ ] E2E 테스트 통과 (Playwright)
- [ ] 코드 리뷰 완료

### 2. 성능
- [ ] API 응답 시간 < 2초
- [ ] 페이지 로딩 시간 < 3초
- [ ] 실시간 업데이트 지연 < 1초

### 3. 보안
- [ ] SQL Injection 방어
- [ ] XSS 방어
- [ ] CSRF 토큰 적용
- [ ] API Key 암호화
- [ ] 개인정보 마스킹

### 4. 문서화
- [ ] API 문서 작성 (Swagger)
- [ ] README 업데이트
- [ ] 사용자 가이드
- [ ] 개발자 문서

### 5. 배포
- [ ] Staging 테스트 완료
- [ ] Production 배포 승인
- [ ] 모니터링 설정 (Sentry)
- [ ] 롤백 계획 수립

---

## 🎉 결론

### 비전 달성 로드맵

```
현재 (Week 8)
  └─ GraphRAG 기반 보험 Q&A 시스템 ✅

Week 20 (Phase 2 완료)
  └─ 내보험다보여 차별화 플랫폼 🎯
     - Google 주소록 연동
     - 보장 갭 분석
     - 계약서 OCR

Week 40 (Phase 3 완료)
  └─ Enterprise 조직 관리 플랫폼 🚀
     - FP 루틴 자동화
     - 팀장 코칭 시스템
     - 실적 예측 AI

Week 62 (Phase 4 완료)
  └─ 통합 보험 데이터 플랫폼 🌟
     - 30개 보험사 전상품 데이터
     - 법원판례 통합
     - 서비스 개시 준비 완료
```

### 예상 ROI

**Phase 2**:
- 투자: $150,000
- 연간 매출 증대: $500,000+
- ROI: **333%**

**Phase 3**:
- 투자: $150,000
- 연간 생산성 향상: $1,200,000+
- ROI: **800%**

**Phase 4**:
- 투자: $200,000
- 데이터 자산 가치: $2,000,000+
- 시장 경쟁력 확보: 무형 자산
- ROI: **1000%+**

**총 ROI**: **740%**

---

### 다음 단계

1. **즉시**: Epic 2.1 Story 2.1.2 완료 (Google 동기화)
2. **Week 9**: Epic 2.2 착수 (보장 갭 분석)
3. **Week 20**: Phase 2 완료 → MVP 출시
4. **Week 21**: Phase 3 착수 → Enterprise 전환
5. **Week 41**: Phase 4 착수 → 데이터 확장
6. **Week 62**: Phase 4 완료 → 서비스 개시

---

**작성자**: Claude (AI Assistant)
**최종 수정**: 2025-12-05
**버전**: 3.0 (Phase 4 통합)
**다음 리뷰**: Week 20 (Phase 2 완료 시), Week 40 (Phase 3 완료 시), Week 62 (Phase 4 완료 시)

**승인 필요**: Product Owner, CTO, CFO, Legal Team (Phase 4 판례 수집)
**다음 액션**: Epic 2.1 개발 지속

---

## 📎 관련 문서

- [EPIC_PLAN_PHASE_2.md](./EPIC_PLAN_PHASE_2.md) - Phase 2 상세 Epic 계획
- [EPIC_PLAN_TEAM_MANAGEMENT.md](./EPIC_PLAN_TEAM_MANAGEMENT.md) - Phase 3 상세 Epic 계획
- [EPIC_PLAN_PHASE_4_DATA_EXPANSION.md](./EPIC_PLAN_PHASE_4_DATA_EXPANSION.md) - Phase 4 상세 Epic 계획
- [FP_ROUTINE_SYSTEM_DESIGN.md](./FP_ROUTINE_SYSTEM_DESIGN.md) - FP 루틴 시스템 설계
- [TEAM_MANAGEMENT_COACHING_SYSTEM.md](./TEAM_MANAGEMENT_COACHING_SYSTEM.md) - 팀 관리 코칭 시스템

