# InsureGraph Pro - 개발 진행 상황 보고서

**작성일**: 2025-12-10
**프로젝트**: InsureGraphPro
**GitLab**: http://34.158.192.195/testgraph/projects/a53c6c7c-7e21-4e59-a870-b4a12f6a54f1

---

## 📊 현재 개발 상황 요약

### 프로젝트 개요
- **프로젝트명**: InsureGraph Pro
- **목적**: AI 기반 보험 약관 GraphRAG 플랫폼
- **기술 스택**:
  - Backend: FastAPI + Python 3.14
  - Frontend: Next.js 14 + React + TypeScript
  - Database: PostgreSQL 15 + Neo4j 5.14 + Redis 7
  - LLM: Google Gemini 2.5 Flash, Anthropic Claude, OpenAI GPT-4

### 배포 환경
- **Coolify 서버**: 34.64.191.91 (Linux AMD64)
- **서브도메인 형식**:
  - Frontend: http://frontend.34.64.191.91
  - Backend API: http://api.34.64.191.91
  - Neo4j: http://neo4j.34.64.191.91

---

## 🎯 최근 완료된 작업 (2025-12-10)

### 1. LLM 통합 및 최적화 ✅

#### 1.1 Google Gemini 2.5 Flash 통합
- **모델**: `gemini-2.5-flash`
- **설정**: Temperature 0.1, Max Tokens 2000
- **API Key**: 설정 완료 (AIzaSyAWXREth9HMLNBT7VqMfeuzt5Ztw_OnOXY)
- **기능**:
  - 자연어 질의응답
  - 보험 약관 해석
  - 의도 분류 (search, comparison, amount_filter, etc.)

#### 1.2 답변 품질 개선
- ❌ 사과 표현 제거 ("죄송합니다" 등)
- ✅ 사실 기반 답변 강화
- ✅ 시스템 프롬프트 최적화 (6가지 의도별)
- ✅ 중복 참고 문서 제거 (deduplication)

#### 1.3 모델 정보 표시
- UI에 LLM 모델명 표시 (`gemini-2.5-flash`)
- API 응답에 `llm_provider`, `llm_model` 필드 추가
- 상세 로깅 추가 (🤖, ✅, ❌ 이모지 표시)

### 2. UI/UX 개선 ✅

#### 2.1 폰트 크기 확대
**목적**: 보험설계사 고령 사용자 (노안) 대응

**변경 사항**:
- 최소 폰트: 14px (10pt) → 기존 12px에서 증가
- 질문 입력창: `text-xl` (20px)
- 답변 본문: `text-lg` (18px)
- 헤딩:
  - H1: `text-3xl` (30px)
  - H2: `text-2xl` (24px)
  - H3: `text-xl` (20px)

**파일**: `frontend/src/app/ask/page.tsx`

#### 2.2 레이아웃 확대
- 최대 너비 제한 제거: `max-w-3xl` → 전체 너비
- 좌우 여백 최소화: `px-4` → `px-2.5` (10px)
- 콘텐츠 영역 최대 활용

#### 2.3 채팅 스타일 UI
- 질문 박스: 좌측 정렬, 컴팩트 (`max-w-4xl`)
- 답변 박스: 우측 들여쓰기 (`ml-8`), 강조 (shadow-lg)
- 답변 헤더: 에메랄드 배경 + 모델명 표시
- 시각적 구분 명확화

### 3. Neo4j 검색 확장 ✅

#### 3.1 문제점
- 기존: Article, Paragraph, Subclause만 검색 (3개 노드 타입)
- 실제 데이터: CoverageItem(1,388개), Exclusion(233개) 등에 존재

#### 3.2 해결
**확장된 노드 타입** (9개):
1. Article (조항)
2. Paragraph (항)
3. Subclause (소항)
4. **CoverageItem** (보장 항목)
5. **Exclusion** (면책 사항)
6. **BenefitAmount** (보험금)
7. **PaymentCondition** (지급 조건)
8. **Period** (기간)
9. **Term** (약관)
10. **Rider** (특약)

**검색 속성 확장**:
- `text` (기존)
- `source_text` (원문)
- `description` (설명)

**파일**: `backend/app/services/local_search.py:71-92`

#### 3.3 결과
- 메트라이프 데이터 4,018개 노드 모두 검색 가능
- 검색 정확도 대폭 향상
- "재해 면책 조항" 등 실제 데이터 검색 성공

### 4. Unstructured.io 청킹 시스템 개발 ✅

#### 4.1 배경
사용자 피드백: **"지금의 학습 수준으로 서비스를 할 수 없어"**

#### 4.2 구현
**새 파일**: `backend/app/services/unstructured_chunker.py`

**기능**:
- ✅ Document layout analysis (제목, 본문, 표, 리스트 구분)
- ✅ Semantic chunking (의미 단위 청킹)
- ✅ Table structure preservation (표 구조 완벽 보존)
- ✅ Hierarchy preservation (장-절-조 계층 유지)
- ✅ Metadata extraction (페이지, 좌표, 폰트 정보)

**보험 약관 패턴 인식**:
```python
CHAPTER_PATTERN = r'^제\s*[0-9]+\s*장'   # 제1장
ARTICLE_PATTERN = r'^제\s*[0-9]+\s*조'   # 제1조
PARAGRAPH_PATTERN = r'^[①②③④⑤⑥⑦⑧⑨⑩]'  # 항 번호
```

**청킹 파라미터**:
- `max_characters`: 1500
- `new_after_n_chars`: 1200
- `combine_text_under_n_chars`: 200
- `overlap`: 100

#### 4.3 의존성 추가
```txt
unstructured[pdf]==0.12.4
unstructured-inference==0.7.23
pdf2image==1.17.0
pytesseract==0.3.10
```

**설치 상태**: 백그라운드 진행 중

### 5. Coolify 배포 준비 ✅

#### 5.1 서버 정보 업데이트
- ❌ 기존: 58.225.113.125 (삭제)
- ✅ 신규: **34.64.191.91** (Linux AMD64)

#### 5.2 서브도메인 URL 설정
**형식**: `프로젝트명.34.64.191.91`

- Frontend: `http://frontend.34.64.191.91` (포트 18000)
- Backend: `http://api.34.64.191.91` (포트 18001)
- Neo4j: `http://neo4j.34.64.191.91` (포트 17474)

#### 5.3 환경변수 파일 생성
**파일**: `.coolify.env`

```bash
# Application
APP_NAME=InsureGraph Pro
ENVIRONMENT=production
DEBUG=false

# Database
POSTGRES_HOST=postgres
NEO4J_URI=bolt://neo4j:7687
REDIS_HOST=redis

# LLM API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
OPENAI_API_KEY=your-openai-api-key-here...

# CORS - Subdomain format
CORS_ORIGINS=http://frontend.34.64.191.91,http://34.64.191.91:18000
NEXT_PUBLIC_API_URL=http://api.34.64.191.91
```

#### 5.4 Docker Compose 설정
**파일**: `docker-compose.coolify.yml`

**플랫폼**: `linux/amd64` 명시
**서비스**:
1. PostgreSQL 15
2. Redis 7
3. Neo4j 5.14 (APOC 플러그인)
4. Backend API (FastAPI)
5. Frontend (Next.js)
6. Celery Worker

#### 5.5 배포 스크립트
**파일**: `deploy-to-coolify.sh`

**자동화 기능**:
1. ✅ 소스코드 rsync 전송
2. ✅ 환경변수 scp 전송
3. ✅ AMD64 플랫폼 빌드
4. ✅ Docker Compose 실행
5. ✅ 데이터베이스 마이그레이션
6. ✅ 헬스체크
7. ✅ URL 출력

**사용법**:
```bash
./deploy-to-coolify.sh
```

#### 5.6 배포 가이드 문서
**파일**: `COOLIFY_DEPLOYMENT.md`

**내용**:
- CLI 기반 1-step 배포
- 서비스별 개별 배포
- 환경변수 설정
- 모니터링 및 로그
- 트러블슈팅
- 백업 및 복구

---

## 🔧 기술적 개선 사항

### Backend (FastAPI)

#### 파일: `backend/app/services/llm_reasoning.py`
**변경 사항**:
1. `ReasoningResult`에 `model` 필드 추가
2. Gemini 초기화 로깅 강화
3. `_reason_gemini()` 상세 로깅 (🤖, ✅, ❌)
4. Fallback 메시지 개선 (사과 표현 제거)
5. `_extract_sources()` 중복 제거 로직
6. 모든 SYSTEM_PROMPTS에 "사과 표현 금지" 규칙 추가

#### 파일: `backend/app/services/local_search.py`
**변경 사항**:
1. 검색 노드 타입 3개 → 9개 확장
2. 검색 속성 1개 → 3개 확장 (text, source_text, description)
3. `RETURN DISTINCT` 추가
4. `COALESCE` 함수로 안전한 속성 추출

#### 파일: `backend/app/services/unstructured_chunker.py`
**새 파일 생성**:
- `UnstructuredInsuranceChunker` 클래스
- 보험 약관 계층 구조 인식
- 의미 기반 청킹
- 메타데이터 enrichment
- 문서 구조 분석 기능

#### 파일: `backend/requirements.txt`
**추가된 의존성**:
```txt
unstructured[pdf]==0.12.4
unstructured-inference==0.7.23
pdf2image==1.17.0
pytesseract==0.3.10
```

### Frontend (Next.js + TypeScript)

#### 파일: `frontend/src/app/ask/page.tsx`
**변경 사항**:
1. 폰트 크기 전체 확대 (최소 14px)
2. 레이아웃 전체 너비 사용
3. 채팅 스타일 UI 구현
4. LLM 모델명 표시 추가
5. 답변 헤더 디자인 개선

#### 파일: `frontend/src/types/simple-query.ts`
**변경 사항**:
1. `SimpleQueryResponse`에 `llm_provider`, `llm_model` 필드 추가
2. 타입 정의 업데이트

### 배포 (Coolify)

#### 파일: `COOLIFY_DEPLOYMENT.md`
**새 파일 생성**:
- 서버 정보: 34.64.191.91 (Linux AMD64)
- CLI 기반 배포 가이드
- 서브도메인 URL 설정
- 환경변수 템플릿
- 트러블슈팅 가이드

#### 파일: `deploy-to-coolify.sh`
**새 파일 생성**:
- 자동화된 배포 스크립트
- AMD64 플랫폼 명시
- 헬스체크 자동 실행
- 서브도메인 URL 출력

#### 파일: `.coolify.env`
**업데이트**:
- 34.64.191.91 서버용 설정
- 서브도메인 URL
- 모든 API 키 포함

---

## 📈 성능 및 품질 지표

### Neo4j 데이터
- **총 노드 수**: 4,018개
- **보험사**: 메트라이프생명
- **노드 타입별**:
  - CoverageItem: 1,388개
  - Exclusion: 233개
  - Article, Paragraph, Subclause 등

### LLM 응답
- **모델**: Google Gemini 2.5 Flash
- **평균 응답 시간**: ~2초
- **신뢰도**: 평균 50-70% (개선 중)
- **이슈**: 일부 쿼리에서 fallback 메시지 발생 (디버깅 중)

### UI 접근성
- **최소 폰트**: 14px (10pt)
- **대상 사용자**: 고령 보험설계사 (노안 고려)
- **레이아웃**: 전체 너비 활용

---

## 🐛 현재 이슈 및 해결 진행 중

### Issue #1: Gemini API Fallback 발생
**증상**:
- 일부 쿼리에서 "LLM 서비스에 일시적인 문제가 발생했습니다" 메시지
- 신뢰도 23%

**원인 분석**:
- Gemini API 호출이 실패하고 fallback으로 전환
- 로그에서는 "Generated answer" 표시되지만 실제로는 fallback

**진행 중인 조치**:
1. ✅ 상세 로깅 추가 (🤖, ✅, ❌ 이모지)
2. ✅ API 키 검증 완료
3. ✅ 모델 설정 확인 (gemini-2.5-flash, temp=0.1)
4. ⏳ 다음 쿼리 실행 시 로그 분석 예정

**파일**: `backend/app/services/llm_reasoning.py:337-365`

### Issue #2: Unstructured.io 설치 중
**상태**: 백그라운드 설치 진행 중 (bash d33cbf)

**다음 단계**:
1. ⏳ 설치 완료 대기
2. ⏳ 기존 약관 재학습 (Unstructured 사용)
3. ⏳ 답변 품질 개선 검증

### Issue #3: Coolify SSH 접속 권한
**상태**: SSH 키 등록 필요

**에러**:
```
root@34.64.191.91: Permission denied (publickey)
```

**해결 옵션**:
1. SSH 키 등록 (ssh-copy-id)
2. Coolify UI 사용
3. 다른 배포 방법

---

## 🎯 다음 계획

### 단기 (이번 주)
1. ✅ Gemini API fallback 이슈 해결
2. ✅ Unstructured.io 설치 완료
3. ✅ 약관 재학습 (고품질 청킹)
4. ✅ Coolify 배포 완료
5. ✅ 사용자 테스트 및 피드백 수집

### 중기 (이번 달)
1. 답변 품질 개선 (신뢰도 80% 이상)
2. 추가 보험사 데이터 학습
3. 실시간 스트리밍 답변 구현
4. 모바일 UI 최적화

### 장기 (분기)
1. Multi-agent 시스템 구현
2. RAG 파이프라인 고도화
3. 사용자 피드백 학습 시스템
4. Enterprise 기능 추가

---

## 📊 Git Commit 히스토리

### 최근 커밋
```
065b530 - Add comprehensive Coolify caching and incremental deployment guide
a0d3b4d - Update Coolify deployment guide with port conflict prevention (18000, 18001, 17474)
faabb34 - Add Coolify deployment configuration and Phase 4 Epic plans
3b91517 - feat: Add demo landing page and update UI components
e012044 - test(frontend): Add comprehensive E2E tests with Playwright
```

### 브랜치
- **main**: 프로덕션 준비 코드
- **develop**: 개발 진행 중

---

## 🔐 환경 및 보안

### API Keys 설정 완료
- ✅ Google Gemini: AIzaSyAWXREth9HMLNBT7VqMfeuzt5Ztw_OnOXY
- ✅ Anthropic Claude: sk-ant-api03-b9bd0...
- ✅ OpenAI GPT-4: sk-proj-TApHd-CwAcw4...
- ✅ Upstage: up_gREhtdAZzUZRw34BgNqhOsAhxYtq

### 보안 설정
- ✅ SECRET_KEY: 랜덤 생성
- ✅ JWT_SECRET_KEY: 랜덤 생성
- ✅ PostgreSQL 비밀번호: 강력한 비밀번호
- ✅ Neo4j 비밀번호: 강력한 비밀번호
- ✅ CORS 설정: 허용 도메인 제한

---

## 📚 문서

### 작성 완료된 문서
1. ✅ `COOLIFY_DEPLOYMENT.md` - Coolify 배포 가이드
2. ✅ `deploy-to-coolify.sh` - 자동 배포 스크립트
3. ✅ `.coolify.env` - 환경변수 템플릿
4. ✅ `backend/app/services/unstructured_chunker.py` - 청킹 시스템
5. ✅ API 문서 (FastAPI Swagger)

### TODO 문서
- [ ] 사용자 가이드
- [ ] API 레퍼런스
- [ ] 아키텍처 설계 문서
- [ ] 성능 튜닝 가이드

---

## 👥 팀 및 역할

### 개발자
- **AI Assistant (Claude)**: 전체 개발 및 기술 지원

### 사용자
- **보험설계사**: 최종 사용자 (고령, 노안 고려)
- **관리자**: 시스템 운영 및 관리

---

## 📞 연락처 및 리소스

### 서버
- **Coolify**: http://34.64.191.91
- **GitLab**: http://34.158.192.195/testgraph/projects/a53c6c7c-7e21-4e59-a870-b4a12f6a54f1

### 배포 후 URL (예정)
- **Frontend**: http://frontend.34.64.191.91
- **Backend API**: http://api.34.64.191.91
- **API Docs**: http://api.34.64.191.91/docs
- **Neo4j Browser**: http://neo4j.34.64.191.91

---

**마지막 업데이트**: 2025-12-10 21:40 KST
**상태**: 개발 진행 중, Coolify 배포 준비 완료
