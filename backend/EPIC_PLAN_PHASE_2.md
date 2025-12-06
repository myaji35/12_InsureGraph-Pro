# Epic Plan: InsureGraph Pro Phase 2 - 차별화 기능 구현

**작성일**: 2025-12-05
**버전**: 1.0
**목표**: 내보험다보여 차별화 + AI 기반 보험 컨설팅 플랫폼 구축

---

## 📋 Executive Summary

### 핵심 목표
1. **Google Contacts 연동**: #고객 태그 기반 고객 관리
2. **보장내역 분석**: AI 기반 보장 갭 분석 및 추천
3. **내보험다보여 차별화**: GraphRAG 기반 심층 해석
4. **계약서 OCR**: 스캔 → DOC/XLSX 자동 생성
5. **AI 컨설팅**: 24/7 자동 상담 시스템

### 예상 개발 기간
- **Phase 2.1 (Core)**: 4-6주
- **Phase 2.2 (Advanced)**: 6-8주
- **Phase 2.3 (Premium)**: 4-6주
- **총 예상**: 14-20주 (3.5-5개월)

### 개발 우선순위
1. **P0 (Critical)**: Epic 1, Epic 2.1-2.2
2. **P1 (High)**: Epic 3, Epic 4.1-4.2
3. **P2 (Medium)**: Epic 4.3-4.4, Epic 5.1-5.2
4. **P3 (Nice-to-have)**: Epic 5.3-5.4

---

## Epic 1: Google Contacts 연동 & 고객 관리 시스템

**Epic ID**: EPIC-2.1
**예상 기간**: 4주
**Story Points**: 34
**비즈니스 가치**: 고객 데이터 기반 맞춤형 서비스 제공

### Story 1.1: Google OAuth 2.0 인증 구현

**Story Points**: 8
**예상 기간**: 1주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] Google Cloud Console에서 OAuth 클라이언트 생성
- [ ] `/api/v1/google/auth/login` 엔드포인트 구현
- [ ] OAuth callback 처리 (`/api/v1/google/auth/callback`)
- [ ] Access Token + Refresh Token 저장
- [ ] 프론트엔드에 "Google 주소록 연동" 버튼 추가
- [ ] 연동 성공 시 사용자 알림 표시

#### Technical Tasks
```
1. Backend:
   - Google OAuth 라이브러리 설치 (google-auth-oauthlib)
   - OAuth 설정 모델 (app/models/google_oauth.py)
   - 인증 엔드포인트 (app/api/v1/endpoints/google_auth.py)
   - Token 저장 (PostgreSQL: google_tokens 테이블)

2. Frontend:
   - Google 로그인 버튼 컴포넌트 (GoogleAuthButton.tsx)
   - OAuth 콜백 페이지 (/google-callback)
   - 연동 상태 표시 (Settings 페이지)

3. Database Schema:
   CREATE TABLE google_tokens (
     id UUID PRIMARY KEY,
     user_id UUID REFERENCES users(id),
     access_token TEXT NOT NULL,
     refresh_token TEXT,
     expires_at TIMESTAMP,
     scopes TEXT[],
     created_at TIMESTAMP DEFAULT NOW()
   );
```

#### Dependencies
- None (독립 실행 가능)

#### API 요구사항
- Google People API (contacts.readonly)
- OAuth 2.0 scopes: `https://www.googleapis.com/auth/contacts.readonly`

---

### Story 1.2: #고객 태그 필터링 및 동기화

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] Google Contacts API에서 #고객 태그 연락처만 가져오기
- [ ] 연락처 정보를 PostgreSQL에 저장
- [ ] 주기적 동기화 (1일 1회 자동)
- [ ] 수동 동기화 버튼 제공
- [ ] 동기화 진행률 표시
- [ ] 중복 연락처 병합 로직

#### Technical Tasks
```
1. Backend:
   - Google Contacts API 통합
   - 연락처 동기화 서비스 (app/services/google_contacts_sync.py)
   - Celery 비동기 작업 (worker_google_sync.py)
   - 연락처 API 엔드포인트

2. Frontend:
   - 연락처 목록 페이지 (/fp/customers)
   - 동기화 상태 모니터링
   - 연락처 검색 및 필터링

3. Database Schema:
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

4. Celery Task:
   @celery_app.task
   def sync_google_contacts(user_id: str):
       # 1. Google API 호출
       # 2. #고객 필터링
       # 3. DB 저장/업데이트
       # 4. 중복 병합
```

#### Dependencies
- Story 1.1 (OAuth 인증 필요)

#### API 요구사항
- Google People API: `people.connections.list`
- Filter: `contactGroups/myContacts` + tag filtering

---

### Story 1.3: 고객 프로필 통합 관리

**Story Points**: 8
**예상 기간**: 1주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] FP 고객 프로필 페이지 (/fp/customers/:id)
- [ ] Google 주소록 정보 + 보험 가입 내역 통합 표시
- [ ] 고객별 메모 기능
- [ ] 고객별 태그 관리
- [ ] 고객 정보 수동 편집 가능
- [ ] 보험 가입 이력 타임라인 표시

#### Technical Tasks
```
1. Frontend:
   - CustomerProfileView.tsx (고객 상세 페이지)
   - CustomerInsuranceTimeline.tsx (가입 이력)
   - CustomerNotes.tsx (메모 컴포넌트)
   - CustomerTagManager.tsx (태그 관리)

2. Backend:
   - 고객 프로필 API (/api/v1/fp/customers/:id)
   - 메모 CRUD API
   - 태그 관리 API

3. Database Schema:
   CREATE TABLE customer_notes (
     id UUID PRIMARY KEY,
     customer_id UUID REFERENCES fp_customers(id),
     created_by UUID REFERENCES users(id),
     content TEXT,
     created_at TIMESTAMP DEFAULT NOW()
   );
```

#### Dependencies
- Story 1.2 (연락처 데이터 필요)

---

### Story 1.4: 라이프사이클 이벤트 자동 감지

**Story Points**: 5
**예상 기간**: 3일
**우선순위**: P2 (Medium)

#### Acceptance Criteria
- [ ] 생일 30일 전 자동 알림 (생일 축하 + 보험 리뷰)
- [ ] 결혼 기념일 감지 (Google Calendar 연동)
- [ ] 자녀 출생 이벤트 감지 (연락처 변경)
- [ ] 퇴직 예정일 계산 (생년월일 기반)
- [ ] 이벤트별 추천 보험 자동 제안

#### Technical Tasks
```
1. Backend:
   - 이벤트 감지 서비스 (app/services/lifecycle_events.py)
   - Celery 스케줄러 (매일 오전 9시 실행)
   - 알림 생성 API

2. Frontend:
   - 이벤트 알림 표시 (NotificationBell.tsx 확장)
   - 이벤트별 추천 보험 카드

3. Celery Task:
   @celery_app.task
   def detect_lifecycle_events():
       # 1. 고객별 생일/기념일 확인
       # 2. 이벤트 발생 시 알림 생성
       # 3. AI 기반 보험 추천
```

#### Dependencies
- Story 1.2, Story 1.3

---

## Epic 2: 보장내역 분석 & 갭 탐지 시스템

**Epic ID**: EPIC-2.2
**예상 기간**: 6주
**Story Points**: 55
**비즈니스 가치**: AI 기반 맞춤형 보험 추천으로 매출 증대

### Story 2.1: 내보험다보여 API 연동

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] 내보험다보여 API 인증 구현
- [ ] 사용자 보험 가입 내역 조회
- [ ] 보험사별/상품별 파싱
- [ ] PostgreSQL에 정규화하여 저장
- [ ] 중복 제거 및 병합
- [ ] 프론트엔드에 "내보험다보여 연동" 버튼

#### Technical Tasks
```
1. Backend:
   - 내보험다보여 API 클라이언트 (app/services/myinsurance_api.py)
   - 데이터 파싱 서비스 (app/services/insurance_parser.py)
   - 정규화 모델 (app/models/user_insurance.py)
   - API 엔드포인트 (/api/v1/myinsurance/sync)

2. Frontend:
   - MyInsuranceSync.tsx (연동 컴포넌트)
   - 연동 상태 표시
   - 가입 내역 목록 표시

3. Database Schema:
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
     source TEXT DEFAULT 'myinsurance',
     raw_data JSONB,
     created_at TIMESTAMP DEFAULT NOW()
   );
```

#### Dependencies
- None (독립 실행 가능)

#### API 요구사항
- 내보험다보여 API (공공데이터포털)
- 인증: 공인인증서 or 간편인증

---

### Story 2.2: AI 기반 보장 갭 분석 엔진

**Story Points**: 21
**예상 기간**: 3주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] 사용자 나이/직업/가족 구성 기반 필수 보장 계산
- [ ] 현재 가입 보험과 필수 보장 비교
- [ ] 부족 보장 (Gap) 자동 탐지
- [ ] 중복 보장 (Overlap) 자동 탐지
- [ ] GraphRAG 기반 관련 보험 상품 추천
- [ ] 분석 결과 리포트 생성

#### Technical Tasks
```
1. Backend:
   - 보장 갭 분석 엔진 (app/services/coverage_gap_analyzer.py)
   - 필수 보장 계산 로직
   - GraphRAG 기반 추천 시스템
   - 분석 리포트 생성 API

2. Frontend:
   - CoverageGapReport.tsx (분석 결과 페이지)
   - GapVisualization.tsx (차트/그래프)
   - RecommendedProducts.tsx (추천 상품 카드)

3. Analysis Logic:
   class CoverageGapAnalyzer:
       def analyze(self, user_profile, current_insurances):
           # 1. 필수 보장 계산
           required = self._calculate_required_coverage(user_profile)

           # 2. 현재 보장 집계
           current = self._aggregate_current_coverage(current_insurances)

           # 3. 갭 탐지
           gaps = self._detect_gaps(required, current)
           overlaps = self._detect_overlaps(current)

           # 4. GraphRAG 추천
           recommendations = self._get_recommendations(gaps)

           return {
               "gaps": gaps,
               "overlaps": overlaps,
               "recommendations": recommendations,
               "score": self._calculate_coverage_score(current, required)
           }
```

#### Dependencies
- Story 2.1 (보험 데이터 필요)
- Epic 3 (GraphRAG 최적화)

---

### Story 2.3: 가족 통합 포트폴리오 분석

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] 가족 구성원 추가 기능
- [ ] 가족 전체 보장 내역 통합 표시
- [ ] 가족 단위 보장 갭 분석
- [ ] 가족 보험료 총액 계산
- [ ] 가족 보험 최적화 제안 (중복 제거)
- [ ] 가족 보험 타임라인 시각화

#### Technical Tasks
```
1. Frontend:
   - FamilyPortfolio.tsx (가족 포트폴리오 페이지)
   - FamilyMemberManager.tsx (가족 구성원 관리)
   - FamilyGapAnalysis.tsx (가족 갭 분석)

2. Backend:
   - 가족 관리 API (/api/v1/family/members)
   - 가족 분석 API (/api/v1/family/analysis)

3. Database Schema:
   CREATE TABLE family_members (
     id UUID PRIMARY KEY,
     user_id UUID REFERENCES users(id),
     name TEXT,
     relationship TEXT,
     birth_date DATE,
     customer_id UUID REFERENCES fp_customers(id),
     created_at TIMESTAMP DEFAULT NOW()
   );
```

#### Dependencies
- Story 2.2 (갭 분석 엔진 필요)

---

### Story 2.4: 보험료 절감 시뮬레이터

**Story Points**: 8
**예상 기간**: 1주
**우선순위**: P2 (Medium)

#### Acceptance Criteria
- [ ] 현재 보험료 vs 최적화 후 보험료 비교
- [ ] 중복 보장 제거 시 절감액 계산
- [ ] 보험사 변경 시 절감액 계산
- [ ] 시뮬레이션 결과 저장 및 공유
- [ ] "최적화 실행" 버튼 (컨설팅 요청)

#### Technical Tasks
```
1. Frontend:
   - PremiumSimulator.tsx (시뮬레이터 페이지)
   - OptimizationResult.tsx (최적화 결과)

2. Backend:
   - 시뮬레이션 API (/api/v1/simulation/premium)
   - 최적화 알고리즘
```

#### Dependencies
- Story 2.2, Story 2.3

---

## Epic 3: 내보험다보여 차별화 - GraphRAG 심층 해석

**Epic ID**: EPIC-2.3
**예상 기간**: 4주
**Story Points**: 34
**비즈니스 가치**: 경쟁사 대비 핵심 차별화 요소

### Story 3.1: GraphRAG 기반 약관 해석 엔진

**Story Points**: 21
**예상 기간**: 3주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] 사용자 보험 상품별 약관 자동 조회
- [ ] GraphRAG로 관련 조항 탐색
- [ ] LLM 기반 자연어 해석 생성
- [ ] "이런 경우 보험금을 받을 수 있나요?" 질문 답변
- [ ] 약관 비교 기능 (상품 A vs 상품 B)
- [ ] 해석 결과 저장 및 재사용

#### Technical Tasks
```
1. Backend:
   - 약관 해석 서비스 (app/services/policy_interpreter.py)
   - GraphRAG 쿼리 최적화
   - LLM 프롬프트 엔지니어링

2. Frontend:
   - PolicyInterpreter.tsx (약관 해석 페이지)
   - CompareProducts.tsx (상품 비교)
   - InterpretationHistory.tsx (해석 이력)

3. GraphRAG Query Example:
   async def interpret_policy(product_name: str, user_question: str):
       # 1. 상품명으로 Neo4j에서 약관 노드 조회
       query = '''
       MATCH (p:Product {name: $product_name})
       -[:HAS_COVERAGE]->(c:Coverage)
       -[:HAS_CONDITION]->(cond:Condition)
       RETURN c, cond
       '''

       # 2. 관련 조항 GraphRAG 탐색
       contexts = graph_rag.search(user_question, product_name)

       # 3. LLM 해석
       answer = llm.reason(
           system="보험 약관 전문가",
           user=f"질문: {user_question}\n\n약관: {contexts}"
       )

       return answer
```

#### Dependencies
- Story 2.1 (보험 데이터 필요)
- 기존 GraphRAG 인프라

---

### Story 3.2: AI 챗봇 - 보험 Q&A

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] 24/7 AI 챗봇 (/ask 페이지 확장)
- [ ] 사용자 보험 기반 맥락 인식
- [ ] "내 보험으로 이 병원비 청구 가능?" 질문 답변
- [ ] 대화 히스토리 저장
- [ ] 추천 질문 제시
- [ ] 음성 입력 지원 (선택)

#### Technical Tasks
```
1. Frontend:
   - InsuranceChatbot.tsx (챗봇 컴포넌트)
   - ChatHistory.tsx (대화 이력)
   - SuggestedQuestions.tsx (추천 질문)

2. Backend:
   - 챗봇 API (/api/v1/chatbot/ask)
   - 대화 히스토리 관리
   - 맥락 인식 프롬프트

3. LLM Prompt:
   system = f"""
   당신은 보험 전문가입니다.
   사용자의 보험 정보:
   - 삼성화재 실손보험 (2023.01.01~)
   - KB손해보험 운전자보험 (2022.05.01~)

   사용자 질문에 위 보험 기준으로 답변하세요.
   """
```

#### Dependencies
- Story 3.1 (약관 해석 엔진)

---

## Epic 4: 계약서 OCR & 문서 생성

**Epic ID**: EPIC-2.4
**예상 기간**: 4주
**Story Points**: 34
**비즈니스 가치**: 사용자 편의성 극대화

### Story 4.1: Upstage Document Parse 통합

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] Upstage API 인증 및 연동
- [ ] PDF/이미지 업로드 → OCR 처리
- [ ] 표 추출 및 구조화
- [ ] OCR 결과 PostgreSQL 저장
- [ ] 하이브리드 전략 (간단한 문서는 pdfplumber)
- [ ] 처리 진행률 표시

#### Technical Tasks
```
1. Backend:
   - Upstage API 클라이언트 (app/services/upstage_client.py)
   - 하이브리드 처리 로직 (streaming_pdf_processor.py 확장)
   - 복잡도 판단 알고리즘

2. Frontend:
   - DocumentUpload.tsx (파일 업로드)
   - OCRProgress.tsx (처리 진행률)

3. Hybrid Strategy:
   async def process_contract(file_path: str):
       # 1. 복잡도 판단
       complexity = calculate_complexity(file_path)

       # 2. 전략 선택
       if complexity < 0.5:
           text = pdfplumber_extract(file_path)  # 무료
       else:
           text = upstage_extract(file_path)      # 유료

       return text
```

#### Dependencies
- Upstage API 키 발급

---

### Story 4.2: LLM 기반 정보 추출

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] OCR 텍스트에서 주요 정보 추출
  - 보험사명, 상품명, 계약번호
  - 피보험자, 수익자
  - 보장 내용, 보험금액
  - 보험료, 납입 기간
- [ ] 추출 정확도 90% 이상
- [ ] 추출 결과 수동 편집 가능
- [ ] 추출 결과 검증 UI

#### Technical Tasks
```
1. Backend:
   - LLM 기반 추출 서비스 (app/services/contract_info_extractor.py)
   - 추출 검증 로직

2. LLM Prompt:
   system = """
   보험계약서에서 다음 정보를 JSON 형식으로 추출하세요:
   {
     "insurer": "보험사명",
     "product": "상품명",
     "contract_number": "계약번호",
     "insured": "피보험자",
     "beneficiary": "수익자",
     "coverages": [
       {"type": "보장종류", "amount": 금액}
     ],
     "premium": 보험료,
     "period": "납입기간"
   }
   """
```

#### Dependencies
- Story 4.1 (OCR 결과 필요)

---

### Story 4.3: DOCX 요약서 생성

**Story Points**: 5
**예상 기간**: 3일
**우선순위**: P2 (Medium)

#### Acceptance Criteria
- [ ] 추출 정보를 DOCX 템플릿에 삽입
- [ ] 깔끔한 포맷팅 (표, 굵기, 색상)
- [ ] 회사 로고 삽입
- [ ] 다운로드 버튼
- [ ] 이메일 전송 기능

#### Technical Tasks
```
1. Backend:
   - DOCX 생성 서비스 (app/services/docx_generator.py)
   - python-docx 활용
   - 템플릿 파일 (data/templates/insurance_summary.docx)

2. Frontend:
   - DownloadSummary.tsx (다운로드 버튼)
```

#### Dependencies
- Story 4.2 (추출 정보 필요)

---

### Story 4.4: XLSX 비교표 생성

**Story Points**: 3
**예상 기간**: 2일
**우선순위**: P2 (Medium)

#### Acceptance Criteria
- [ ] 여러 보험 상품 비교표 생성
- [ ] 보장 종류별 행, 상품별 열
- [ ] 조건부 서식 (높은 금액 강조)
- [ ] 차트 자동 생성
- [ ] 다운로드 버튼

#### Technical Tasks
```
1. Backend:
   - XLSX 생성 서비스 (app/services/xlsx_generator.py)
   - openpyxl 활용
   - 차트 생성 로직

2. Example:
   from openpyxl import Workbook
   from openpyxl.chart import BarChart

   def generate_comparison(insurances: List[dict]):
       wb = Workbook()
       ws = wb.active

       # 헤더
       ws.append(["보장종류", "상품A", "상품B", "상품C"])

       # 데이터
       for coverage in ["사망", "암", "뇌졸중"]:
           row = [coverage]
           for ins in insurances:
               row.append(ins.get(coverage, 0))
           ws.append(row)

       # 차트
       chart = BarChart()
       wb.save("comparison.xlsx")
```

#### Dependencies
- Story 4.2 (추출 정보 필요)

---

## Epic 5: AI 컨설팅 고도화

**Epic ID**: EPIC-2.5
**예상 기간**: 6주
**Story Points**: 34
**비즈니스 가치**: 프리미엄 서비스 차별화

### Story 5.1: 개인화 추천 알고리즘

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P2 (Medium)

#### Acceptance Criteria
- [ ] 사용자 프로필 기반 추천 (나이, 직업, 가족)
- [ ] 보험 가입 이력 기반 협업 필터링
- [ ] GraphRAG 기반 유사 사례 추천
- [ ] A/B 테스트로 추천 정확도 개선
- [ ] 추천 이유 설명 생성

#### Technical Tasks
```
1. Backend:
   - 추천 엔진 (app/services/recommendation_engine.py)
   - 협업 필터링 알고리즘
   - GraphRAG 유사도 계산

2. Algorithm:
   def recommend(user_profile, current_insurances):
       # 1. Content-based: 유사 프로필 사용자의 보험
       similar_users = find_similar_users(user_profile)
       popular_insurances = get_popular_insurances(similar_users)

       # 2. GraphRAG: 현재 보험과 자주 같이 가입하는 보험
       related = graph_rag.find_related_products(current_insurances)

       # 3. Hybrid
       recommendations = combine(popular_insurances, related)

       return recommendations
```

#### Dependencies
- Story 2.2 (갭 분석 엔진)

---

### Story 5.2: 보험료 갱신 알림 자동화

**Story Points**: 8
**예상 기간**: 1주
**우선순위**: P2 (Medium)

#### Acceptance Criteria
- [ ] 보험 만기일 30일 전 자동 알림
- [ ] 갱신 시 예상 보험료 계산
- [ ] 더 나은 상품 추천
- [ ] "갱신하기" / "상담 신청" 버튼
- [ ] 알림 설정 관리

#### Technical Tasks
```
1. Backend:
   - Celery 스케줄러 (매일 갱신 대상 확인)
   - 갱신 알림 생성 로직

2. Celery Task:
   @celery_app.task
   def check_renewal_alerts():
       # 1. 만기 30일 이내 보험 조회
       expiring = db.query(UserInsurance).filter(
           UserInsurance.end_date.between(
               date.today(),
               date.today() + timedelta(days=30)
           )
       )

       # 2. 알림 생성
       for insurance in expiring:
           create_notification(
               user_id=insurance.user_id,
               type="renewal_alert",
               message=f"{insurance.product_name} 갱신 예정"
           )
```

#### Dependencies
- Story 2.1 (보험 데이터 필요)

---

### Story 5.3: 청구 도우미 위저드

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P3 (Nice-to-have)

#### Acceptance Criteria
- [ ] "보험금 청구하기" 버튼
- [ ] 단계별 청구 가이드 (위저드 UI)
- [ ] 필요 서류 자동 안내
- [ ] 서류 업로드 및 OCR
- [ ] AI 기반 청구 가능 여부 사전 판단
- [ ] 보험사별 청구 프로세스 안내

#### Technical Tasks
```
1. Frontend:
   - ClaimWizard.tsx (청구 위저드)
   - ClaimDocumentUpload.tsx (서류 업로드)
   - ClaimResult.tsx (사전 판단 결과)

2. Backend:
   - 청구 판단 API (/api/v1/claim/assess)
   - LLM 기반 판단 로직
```

#### Dependencies
- Story 3.1 (약관 해석 엔진)
- Story 4.1 (OCR)

---

## 📊 개발 로드맵

### Phase 2.1: Core Infrastructure (4-6주)

**목표**: 기본 연동 및 데이터 수집

```
Week 1-2:
  ✅ Story 1.1: Google OAuth 구현
  ✅ Story 2.1: 내보험다보여 연동

Week 3-4:
  ✅ Story 1.2: 주소록 동기화
  ✅ Story 1.3: 고객 프로필 관리

Week 5-6:
  ✅ Story 2.2: 보장 갭 분석 엔진 (Part 1)
  ✅ Story 4.1: Upstage OCR 통합
```

**Deliverables**:
- Google Contacts 연동 완료
- 내보험다보여 데이터 수집 완료
- 기본 갭 분석 기능

---

### Phase 2.2: Advanced Features (6-8주)

**목표**: AI 기반 분석 및 추천

```
Week 7-9:
  ✅ Story 2.2: 보장 갭 분석 엔진 (Part 2)
  ✅ Story 3.1: GraphRAG 약관 해석

Week 10-12:
  ✅ Story 2.3: 가족 포트폴리오 분석
  ✅ Story 3.2: AI 챗봇

Week 13-14:
  ✅ Story 4.2: LLM 정보 추출
  ✅ Story 5.1: 개인화 추천 알고리즘
```

**Deliverables**:
- AI 기반 보장 갭 분석
- GraphRAG 약관 해석
- 24/7 AI 챗봇

---

### Phase 2.3: Premium Services (4-6주)

**목표**: 프리미엄 기능 및 사용자 경험 개선

```
Week 15-16:
  ✅ Story 1.4: 라이프사이클 이벤트
  ✅ Story 2.4: 보험료 절감 시뮬레이터

Week 17-18:
  ✅ Story 4.3: DOCX 생성
  ✅ Story 4.4: XLSX 생성
  ✅ Story 5.2: 갱신 알림 자동화

Week 19-20:
  ✅ Story 5.3: 청구 도우미 위저드
  ✅ 전체 QA 및 버그 수정
```

**Deliverables**:
- 계약서 스캔 → DOC/XLSX 자동 생성
- 보험료 절감 시뮬레이터
- 청구 도우미

---

## 🏗️ 기술 아키텍처

### 시스템 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                  │
├─────────────────────────────────────────────────────────┤
│  - /fp/customers (고객 관리)                            │
│  - /analysis/gap (갭 분석)                              │
│  - /analysis/family (가족 분석)                         │
│  - /ask (AI 챗봇)                                       │
│  - /documents/ocr (계약서 OCR)                          │
│  - /settings (Google/내보험다보여 연동)                 │
└─────────────────────────────────────────────────────────┘
                          ↓ REST API
┌─────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                     │
├─────────────────────────────────────────────────────────┤
│  - Google OAuth 2.0                                     │
│  - 내보험다보여 API                                      │
│  - Upstage Document Parse                               │
│  - Coverage Gap Analyzer                                │
│  - GraphRAG Query Engine                                │
│  - LLM Reasoning (Anthropic)                            │
└─────────────────────────────────────────────────────────┘
         ↓                  ↓                  ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Neo4j     │  │    Redis     │
│  (관계형 DB)  │  │  (그래프 DB)  │  │   (캐시)      │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ - users      │  │ - Product    │  │ - Sessions   │
│ - fp_cust... │  │ - Coverage   │  │ - Cache      │
│ - user_ins...│  │ - Article    │  │              │
│ - family_... │  │ - Condition  │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│                    Celery Workers                       │
├─────────────────────────────────────────────────────────┤
│  - worker_google_sync.py (주소록 동기화)                │
│  - worker_lifecycle_events.py (이벤트 감지)             │
│  - worker_renewal_alerts.py (갱신 알림)                 │
└─────────────────────────────────────────────────────────┘
```

---

### 데이터베이스 스키마 (주요 테이블)

```sql
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

-- Google 주소록 (FP 고객)
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

-- 사용자 보험 가입 내역
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
  source TEXT DEFAULT 'myinsurance',  -- 'myinsurance', 'manual', 'ocr'
  raw_data JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 가족 구성원
CREATE TABLE family_members (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  name TEXT,
  relationship TEXT,  -- 'spouse', 'child', 'parent'
  birth_date DATE,
  customer_id UUID REFERENCES fp_customers(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 보장 갭 분석 결과
CREATE TABLE coverage_gap_analysis (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  analysis_date TIMESTAMP DEFAULT NOW(),
  gaps JSONB,  -- [{"type": "암보험", "required": 5000, "current": 3000, "gap": 2000}]
  overlaps JSONB,
  recommendations JSONB,
  coverage_score NUMERIC,  -- 0-100
  created_at TIMESTAMP DEFAULT NOW()
);

-- 고객 메모
CREATE TABLE customer_notes (
  id UUID PRIMARY KEY,
  customer_id UUID REFERENCES fp_customers(id),
  created_by UUID REFERENCES users(id),
  content TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 라이프사이클 이벤트
CREATE TABLE lifecycle_events (
  id UUID PRIMARY KEY,
  customer_id UUID REFERENCES fp_customers(id),
  event_type TEXT,  -- 'birthday', 'anniversary', 'retirement'
  event_date DATE,
  notification_sent BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔌 API 통합 요구사항

### 1. Google APIs

**필요한 API**:
- Google People API (Contacts)
- Google OAuth 2.0

**인증 스코프**:
```
https://www.googleapis.com/auth/contacts.readonly
https://www.googleapis.com/auth/userinfo.profile
```

**요청 예시**:
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

service = build('people', 'v1', credentials=creds)
results = service.people().connections().list(
    resourceName='people/me',
    pageSize=1000,
    personFields='names,emailAddresses,phoneNumbers,birthdays,userDefined'
).execute()
```

---

### 2. 내보험다보여 API

**API 엔드포인트** (공공데이터포털):
```
https://api.odcloud.kr/api/xxx/v1/insurance
```

**인증 방식**:
- 공인인증서
- 카카오톡 간편인증

**요청 예시**:
```python
import requests

response = requests.post(
    "https://api.odcloud.kr/api/insurance/v1/list",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json={
        "name": "홍길동",
        "resident_number": "901010-1******"
    }
)
```

---

### 3. Upstage Document Parse API

**API 엔드포인트**:
```
https://api.upstage.ai/v1/document-ai/document-parse
```

**요청 예시**:
```python
import requests

files = {"document": open("contract.pdf", "rb")}
headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}

response = requests.post(
    "https://api.upstage.ai/v1/document-ai/document-parse",
    headers=headers,
    files=files,
    data={"ocr": "force"}
)

result = response.json()
text = result["content"]["text"]
tables = result["content"]["tables"]
```

---

## 📈 성공 지표 (KPI)

### 비즈니스 지표

| 지표 | 목표 | 측정 방법 |
|-----|------|----------|
| **Google 주소록 연동률** | 60% | (연동 사용자 / 전체 사용자) * 100 |
| **보장 갭 분석 사용률** | 80% | (분석 실행 / 전체 사용자) * 100 |
| **AI 챗봇 사용률** | 50% | (챗봇 사용 / 전체 사용자) * 100 |
| **계약서 OCR 성공률** | 90% | (성공 / 전체 시도) * 100 |
| **추천 보험 전환율** | 10% | (가입 / 추천 클릭) * 100 |

### 기술 지표

| 지표 | 목표 | 측정 방법 |
|-----|------|----------|
| **API 응답 시간** | < 2초 | Sentry APM |
| **OCR 정확도** | > 95% | 수동 검증 샘플링 |
| **LLM 답변 정확도** | > 85% | 사용자 피드백 |
| **시스템 가용성** | > 99% | Uptime 모니터링 |

---

## 💰 예상 비용

### 월간 운영 비용 (사용자 1,000명 기준)

| 항목 | 예상 비용 | 비고 |
|-----|----------|------|
| **Anthropic API** | $200-500 | 월 50만 토큰 |
| **Upstage OCR** | $50-150 | 월 500건 처리 |
| **Google Cloud** | $20 | OAuth + Storage |
| **Neo4j AuraDB** | $65 | Professional |
| **PostgreSQL** | $25 | AWS RDS t3.small |
| **Redis** | $15 | AWS ElastiCache |
| **서버 호스팅** | $100 | AWS EC2 t3.medium |
| **총계** | **$475-875/월** | 사용자당 $0.48-0.88 |

### 비용 절감 전략

1. **하이브리드 OCR**: Upstage 사용률 50% 절감
2. **LLM 캐싱**: 동일 질문 Redis 캐싱으로 70% 절감
3. **스팟 인스턴스**: AWS 비용 60% 절감

---

## 🎯 우선순위 결정 기준

### P0 (Critical) - 즉시 구현 필요
- Epic 1 Story 1.1-1.2 (Google 연동)
- Epic 2 Story 2.1-2.2 (내보험다보여 + 갭 분석)
- Epic 3 Story 3.1 (GraphRAG 해석)

### P1 (High) - 4주 내 구현
- Epic 1 Story 1.3 (고객 프로필)
- Epic 2 Story 2.3 (가족 분석)
- Epic 3 Story 3.2 (AI 챗봇)
- Epic 4 Story 4.1-4.2 (OCR + 정보 추출)

### P2 (Medium) - 8주 내 구현
- Epic 1 Story 1.4 (라이프사이클)
- Epic 2 Story 2.4 (시뮬레이터)
- Epic 4 Story 4.3-4.4 (DOC/XLSX)
- Epic 5 Story 5.1-5.2 (추천 + 알림)

### P3 (Nice-to-have) - 여유 있을 때
- Epic 5 Story 5.3 (청구 도우미)

---

## ✅ Definition of Done (DoD)

각 Story는 다음 조건을 **모두 만족**해야 완료:

1. **코드 완성**
   - [ ] 모든 Acceptance Criteria 충족
   - [ ] 단위 테스트 작성 (커버리지 > 80%)
   - [ ] 통합 테스트 통과
   - [ ] 코드 리뷰 완료

2. **문서화**
   - [ ] API 문서 작성 (Swagger)
   - [ ] README 업데이트
   - [ ] 사용자 가이드 작성

3. **배포**
   - [ ] Staging 환경 배포 및 테스트
   - [ ] Production 배포 승인
   - [ ] 모니터링 설정 (Sentry)

4. **검증**
   - [ ] QA 테스트 통과
   - [ ] 성능 테스트 통과 (응답시간 < 2초)
   - [ ] 보안 검토 완료

---

## 🚀 Quick Start - 다음 단계

### 1주차: 환경 설정 및 Google OAuth 구현

```bash
# 1. Google Cloud Console 설정
- 프로젝트 생성: InsureGraph-Pro
- OAuth 2.0 클라이언트 ID 생성
- Redirect URI: http://localhost:8000/api/v1/google/auth/callback

# 2. 백엔드 패키지 설치
cd backend
pip install google-auth-oauthlib google-api-python-client

# 3. 환경 변수 추가 (.env)
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/google/auth/callback

# 4. 데이터베이스 마이그레이션
alembic revision --autogenerate -m "Add google_tokens table"
alembic upgrade head

# 5. 개발 시작
- Story 1.1: Google OAuth 구현
```

---

## 📞 팀 구성 권장사항

### Minimum Viable Team (3명)

1. **Full-stack Developer** (1명)
   - Frontend (Next.js/React)
   - Backend (FastAPI)
   - Story 1.1-1.3, 2.1

2. **AI/ML Engineer** (1명)
   - LLM 통합 (Anthropic)
   - GraphRAG 최적화
   - Story 2.2, 3.1-3.2, 5.1

3. **Backend Developer** (1명)
   - API 통합 (Google, 내보험다보여, Upstage)
   - Celery 워커
   - Story 1.2, 4.1-4.2, 5.2

### Ideal Team (5명)

위 3명 + 추가:
4. **Frontend Developer** (1명) - UI/UX 개선
5. **QA Engineer** (1명) - 테스트 자동화

---

## 🎉 결론

### 핵심 차별화 포인트

1. **Google 주소록 연동** → 자동 고객 관리
2. **내보험다보여 + GraphRAG** → 단순 조회 → AI 해석
3. **보장 갭 분석** → 부족/중복 자동 탐지
4. **계약서 OCR** → 스캔만으로 자동 요약
5. **24/7 AI 챗봇** → 즉시 답변

### 예상 효과

- **사용자 편의성**: 5배 향상 (수동 입력 → 자동 연동)
- **컨설팅 품질**: 3배 향상 (사람 → AI + 사람)
- **운영 비용**: 60% 절감 (자동화)
- **매출**: 2배 증가 (추천 전환율 10%)

### 시작하기

```bash
# Epic Plan 승인 후 바로 시작
cd backend
git checkout -b feature/epic-2.1-google-oauth
# Story 1.1 개발 시작!
```

---

**작성자**: Claude (AI Assistant)
**검토 필요**: Product Owner, Tech Lead
**다음 단계**: Story 1.1 개발 착수 승인

