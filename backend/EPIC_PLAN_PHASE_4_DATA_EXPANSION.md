# Epic Plan: Phase 4 - 데이터 확장 전략

**작성일**: 2025-12-05
**버전**: 1.0
**목표**: 30개 보험사 × 전상품 × 법원판례 통합 데이터베이스 구축

---

## 📋 Executive Summary

### 핵심 목표
1. **30개 보험사 관리 시스템**: CRUD, 메타데이터 관리
2. **전상품 데이터 수집**: 2025년 12월 기준 판매 중인 전체 상품
3. **법원판례 통합**: 보험 분쟁 형사/민사 판례 크롤링
4. **연도별 히스토리**: 1년 단위 과거 자료 순차 학습

### 예상 개발 기간
- **Phase 4.1 (보험사 관리)**: 2주
- **Phase 4.2 (상품 데이터 수집)**: 12주
- **Phase 4.3 (법원판례)**: 8주
- **총 예상**: 22주 (5.5개월)

### 개발 우선순위
1. **P0 (Critical)**: Epic 4.1 (보험사 관리)
2. **P0 (Critical)**: Epic 4.2 (1차 상품 수집)
3. **P1 (High)**: Epic 4.3 (법원판례)
4. **P2 (Medium)**: Epic 4.4 (과거 자료 확장)

---

## Epic 4.1: 30개 보험사 관리 시스템

**Epic ID**: EPIC-4.1
**예상 기간**: 2주
**Story Points**: 13
**비즈니스 가치**: 데이터 수집 기반 구축

### Story 4.1.1: 보험사 마스터 관리

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] 보험사 30개 CRUD (생성/조회/수정/삭제)
- [ ] 보험사 메타데이터 관리
  - 상호명
  - 대표 URL
  - 전화번호
  - 주소
  - 사업자등록번호
  - 대표이사
- [ ] 상품 목록과 연동 (Foreign Key)
- [ ] 보험사별 크롤러 설정 관리
- [ ] 관리자 UI (보험사 목록, 추가, 수정, 삭제)

#### Technical Tasks
```
1. Backend:
   - 보험사 모델 (app/models/insurer.py)
   - CRUD API (/api/v1/insurers)
   - 크롤러 설정 관리

2. Frontend:
   - InsurerList.tsx (보험사 목록)
   - InsurerForm.tsx (추가/수정 폼)
   - InsurerDetail.tsx (상세 페이지)

3. Database Schema:
   CREATE TABLE insurers (
     id UUID PRIMARY KEY,
     name TEXT NOT NULL UNIQUE, -- 상호명
     display_name TEXT, -- 표시명 (예: "삼성화재")
     website_url TEXT, -- 대표 URL
     phone TEXT, -- 전화번호
     address TEXT, -- 주소
     business_number TEXT UNIQUE, -- 사업자등록번호
     ceo_name TEXT, -- 대표이사
     insurer_type TEXT, -- 'life', 'non-life', 'both'
     logo_url TEXT, -- 로고 이미지 URL
     is_active BOOLEAN DEFAULT TRUE,
     crawler_config JSONB, -- 크롤러 설정
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );

   -- 30개 보험사 초기 데이터
   INSERT INTO insurers (name, display_name, website_url, insurer_type) VALUES
   -- 생명보험
   ('Samsung Life Insurance', '삼성생명', 'https://www.samsunglife.com', 'life'),
   ('Hanwha Life Insurance', '한화생명', 'https://www.hanwhalife.com', 'life'),
   ('Kyobo Life Insurance', '교보생명', 'https://www.kyobo.co.kr', 'life'),
   ('Shinhan Life Insurance', '신한생명', 'https://www.shinhanlife.co.kr', 'life'),
   ('MetLife Korea', '메트라이프생명', 'https://www.metlife.co.kr', 'life'),
   ('DGB Life Insurance', 'DGB생명', 'https://www.dgbfnlife.com', 'life'),
   ('KB Life Insurance', 'KB생명', 'https://www.kbli.co.kr', 'life'),
   ('IBK연금보험', 'IBK연금보험', 'https://www.ibkpension.com', 'life'),
   ('KDB Life Insurance', 'KDB생명', 'https://www.kdblife.co.kr', 'life'),
   ('BNP Paribas Cardif Life', '카디프생명', 'https://www.bnpparibascardif.co.kr', 'life'),

   -- 손해보험
   ('Samsung Fire & Marine', '삼성화재', 'https://www.samsungfire.com', 'non-life'),
   ('Hyundai Marine & Fire', '현대해상', 'https://www.hi.co.kr', 'non-life'),
   ('DB Insurance', 'DB손해보험', 'https://www.idbins.com', 'non-life'),
   ('KB Insurance', 'KB손해보험', 'https://www.kbinsure.co.kr', 'non-life'),
   ('Meritz Fire & Marine', '메리츠화재', 'https://www.meritzfire.com', 'non-life'),
   ('Heungkuk Fire & Marine', '흥국화재', 'https://www.heungkukfire.co.kr', 'non-life'),
   ('Lotte Insurance', '롯데손해보험', 'https://www.lotteins.co.kr', 'non-life'),
   ('MG Insurance', 'MG손해보험', 'https://www.mginsurance.co.kr', 'non-life'),
   ('Hanhwa General Insurance', '한화손해보험', 'https://www.hwgeneralins.com', 'non-life'),
   ('AXA Insurance', 'AXA손해보험', 'https://www.axa.co.kr', 'non-life'),
   ('Chubb Insurance Korea', '처브손해보험', 'https://www.chubb.com/kr', 'non-life'),
   ('AIG Insurance Korea', 'AIG손해보험', 'https://www.aig.co.kr', 'non-life'),
   ('Allianz Global Assistance', '알리안츠손해보험', 'https://www.allianz.co.kr', 'non-life'),

   -- 겸영보험
   ('Dongbu Insurance', '동부화재', 'https://www.idongbu.com', 'both'),
   ('The K Non-Life Insurance', '더케이손해보험', 'https://www.theknonlife.com', 'both'),
   ('BNP Paribas Cardif General', '카디프손해보험', 'https://www.cardif.co.kr', 'both'),

   -- 전업 자동차보험
   ('Carrot General Insurance', '캐롯손해보험', 'https://www.carrotins.com', 'non-life'),
   ('HI Indemnity', 'Hi보험', 'https://www.hi-indemnity.co.kr', 'non-life'),
   ('AJ Rent-a-car Insurance', 'AJ렌터카보험', 'https://www.ajrentacar.co.kr', 'non-life'),
   ('Hana Insurance', '하나손해보험', 'https://www.hanainsure.co.kr', 'non-life');

4. API Endpoints:
   GET    /api/v1/insurers              # 목록 조회
   GET    /api/v1/insurers/:id          # 상세 조회
   POST   /api/v1/insurers              # 생성
   PUT    /api/v1/insurers/:id          # 수정
   DELETE /api/v1/insurers/:id          # 삭제 (soft delete)
   GET    /api/v1/insurers/:id/products # 보험사별 상품 목록

5. 관리자 UI:
   /admin/insurers                      # 보험사 관리 페이지
```

#### Dependencies
- None (독립 실행 가능)

---

## Epic 4.2: 전상품 데이터 수집 (1차)

**Epic ID**: EPIC-4.2
**예상 기간**: 12주
**Story Points**: 89
**비즈니스 가치**: 서비스 출시 기반 데이터

### Story 4.2.1: 상품 카테고리 체계 구축

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] 표준 상품 카테고리 분류 체계 정의
  - 생명보험: 종신, 정기, 연금, 변액, 저축성
  - 손해보험: 자동차, 실손, 암, 여행, 배상책임
  - 특약: 재해, 질병, 수술, 입원
- [ ] 카테고리 계층 구조 (대분류 → 중분류 → 소분류)
- [ ] 카테고리별 필수 메타데이터 정의
- [ ] 관리자 UI (카테고리 관리)

#### Technical Tasks
```
1. Database Schema:
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

   -- 초기 카테고리 데이터
   INSERT INTO product_categories (name, display_name, category_type) VALUES
   -- 대분류
   ('life_insurance', '생명보험', 'major'),
   ('non_life_insurance', '손해보험', 'major'),
   ('special_contracts', '특약', 'major');

   -- 중분류 (생명보험)
   INSERT INTO product_categories (parent_id, name, display_name, category_type)
   SELECT id, 'whole_life', '종신보험', 'middle' FROM product_categories WHERE name = 'life_insurance';
   -- ... (계속)

2. API Endpoints:
   GET /api/v1/categories              # 전체 트리 구조
   GET /api/v1/categories/:id/children # 하위 카테고리
   POST /api/v1/categories             # 카테고리 추가

3. Frontend:
   /admin/categories                    # 카테고리 관리
```

#### Dependencies
- Story 4.1.1 (보험사 마스터 필요)

---

### Story 4.2.2: 상품 메타데이터 모델 설계

**Story Points**: 8
**예상 기간**: 1주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] 상품 기본 정보 모델
  - 상품명, 보험사, 카테고리
  - 판매 시작일, 판매 종료일
  - 보험 기간, 납입 기간
- [ ] 문서 관리 (상품설명서, 약관, 특약)
- [ ] 학습 상태 관리 (미학습, 학습, 초기화)
- [ ] 버전 관리 (연도별 개정)

#### Technical Tasks
```
1. Database Schema:
   CREATE TABLE products (
     id UUID PRIMARY KEY,
     insurer_id UUID REFERENCES insurers(id),
     category_id UUID REFERENCES product_categories(id),
     product_code TEXT, -- 보험사 상품 코드
     name TEXT NOT NULL,
     display_name TEXT,
     description TEXT,
     sale_start_date DATE,
     sale_end_date DATE,
     insurance_period TEXT, -- '10년', '평생' 등
     payment_period TEXT,
     min_age INT,
     max_age INT,
     is_selling BOOLEAN DEFAULT TRUE, -- 현재 판매 여부
     version INT DEFAULT 1, -- 버전 (연도별 개정)
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );

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

   -- 학습 상태 추적
   CREATE TABLE document_learning_logs (
     id UUID PRIMARY KEY,
     document_id UUID REFERENCES product_documents(id),
     status TEXT, -- 'started', 'completed', 'failed', 'reset'
     started_at TIMESTAMP,
     completed_at TIMESTAMP,
     error_message TEXT,
     metadata JSONB, -- 추출된 엔티티 개수 등
     created_at TIMESTAMP DEFAULT NOW()
   );
```

#### Dependencies
- Story 4.2.1 (카테고리 체계 필요)

---

### Story 4.2.3: 보험사별 크롤러 구현 (30개)

**Story Points**: 55
**예상 기간**: 8주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] 30개 보험사 각각 크롤러 구현
- [ ] 상품 목록 페이지 크롤링
- [ ] 상품설명서 PDF 다운로드
- [ ] 약관 PDF 다운로드
- [ ] 특약 PDF 다운로드
- [ ] 크롤링 진행률 표시
- [ ] 실패 시 재시도 로직
- [ ] 크롤링 결과 검증 (필수 파일 누락 확인)

#### Technical Tasks
```
1. Crawler Implementation:
   # 보험사별 크롤러 클래스
   app/services/crawlers/
   ├── samsung_life_crawler.py       (삼성생명)
   ├── hanwha_life_crawler.py        (한화생명)
   ├── kyobo_life_crawler.py         (교보생명)
   ├── samsung_fire_crawler.py       (삼성화재)
   ├── hyundai_marine_crawler.py     (현대해상)
   ├── db_insurance_crawler.py       (DB손해보험)
   └── ... (총 30개)

2. Base Crawler:
   class BaseProductCrawler:
       def crawl_product_list(self) -> List[dict]:
           """상품 목록 크롤링"""
           pass

       def download_brochure(self, product_url: str) -> str:
           """상품설명서 다운로드"""
           pass

       def download_terms(self, product_url: str) -> str:
           """약관 다운로드"""
           pass

       def download_riders(self, product_url: str) -> List[str]:
           """특약 다운로드"""
           pass

       def validate_documents(self, product_id: str) -> dict:
           """필수 문서 누락 확인"""
           required = ['brochure', 'terms']
           downloaded = self.get_downloaded_documents(product_id)
           missing = [doc for doc in required if doc not in downloaded]
           return {
               "valid": len(missing) == 0,
               "missing": missing
           }

3. Crawler Registry:
   CRAWLER_MAP = {
       'Samsung Life Insurance': SamsungLifeCrawler,
       'Hanwha Life Insurance': HanwhaLifeCrawler,
       # ... (30개 매핑)
   }

   def get_crawler(insurer_name: str):
       crawler_class = CRAWLER_MAP.get(insurer_name)
       if not crawler_class:
           raise ValueError(f"No crawler found for {insurer_name}")
       return crawler_class()

4. Celery Task (병렬 처리):
   @celery_app.task
   def crawl_all_insurers():
       insurers = db.query(Insurer).filter(Insurer.is_active == True).all()

       for insurer in insurers:
           # 보험사별 크롤링 비동기 실행
           crawl_insurer_products.delay(insurer.id)

   @celery_app.task
   def crawl_insurer_products(insurer_id: str):
       insurer = db.query(Insurer).get(insurer_id)
       crawler = get_crawler(insurer.name)

       # 1. 상품 목록 크롤링
       products = crawler.crawl_product_list()

       # 2. 각 상품별 문서 다운로드
       for product in products:
           # DB에 상품 저장
           db_product = create_product(product)

           # 문서 다운로드
           brochure_url = crawler.download_brochure(product['url'])
           terms_url = crawler.download_terms(product['url'])
           riders_urls = crawler.download_riders(product['url'])

           # 문서 메타데이터 저장
           save_product_documents(db_product.id, {
               'brochure': brochure_url,
               'terms': terms_url,
               'riders': riders_urls
           })

5. Progress Tracking:
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

6. Admin UI:
   /admin/crawlers                     # 크롤러 관리
   - 보험사별 크롤링 진행률
   - 실패 목록 및 재시도
   - 수동 크롤링 시작
```

#### Dependencies
- Story 4.2.2 (상품 모델 필요)

---

### Story 4.2.4: 학습 관리 시스템

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] 문서별 학습 상태 관리 (미학습/학습/초기화)
- [ ] 학습 시작 버튼 (관리자)
- [ ] 학습 진행률 실시간 표시
- [ ] 학습 결과 검증 (엔티티 추출 개수)
- [ ] 초기화 기능 (재학습)
- [ ] 학습 이력 조회

#### Technical Tasks
```
1. Learning Service:
   class DocumentLearningService:
       async def learn_document(self, document_id: str):
           document = db.query(ProductDocument).get(document_id)

           # 1. 상태 업데이트 (미학습 → 학습 중)
           document.learning_status = 'learning'
           log = DocumentLearningLog(
               document_id=document_id,
               status='started',
               started_at=datetime.now()
           )
           db.add(log)
           db.commit()

           try:
               # 2. PDF 텍스트 추출
               text = await self.extract_text(document.file_url)

               # 3. 스마트 청킹
               chunks = chunk_document(text, document_id)

               # 4. 엔티티 추출
               entities = []
               for chunk in chunks:
                   extracted = extract_entities(chunk['text'])
                   entities.extend(extracted)

               # 5. Neo4j 저장
               save_to_neo4j(entities)

               # 6. 완료 처리
               document.learning_status = 'learned'
               document.learned_at = datetime.now()
               log.status = 'completed'
               log.completed_at = datetime.now()
               log.metadata = {
                   "entity_count": len(entities),
                   "chunk_count": len(chunks)
               }
               db.commit()

           except Exception as e:
               # 실패 처리
               document.learning_status = 'failed'
               log.status = 'failed'
               log.error_message = str(e)
               db.commit()
               raise

       def reset_document(self, document_id: str):
           """초기화 (재학습 준비)"""
           document = db.query(ProductDocument).get(document_id)
           document.learning_status = 'pending'
           document.learned_at = None

           # Neo4j에서 해당 문서 엔티티 삭제
           delete_from_neo4j(document_id)

           db.commit()

2. Celery Task (대량 학습):
   @celery_app.task
   def learn_all_documents():
       pending_docs = db.query(ProductDocument).filter(
           ProductDocument.learning_status == 'pending'
       ).all()

       for doc in pending_docs:
           learn_single_document.delay(doc.id)

   @celery_app.task
   def learn_single_document(document_id: str):
       service = DocumentLearningService()
       service.learn_document(document_id)

3. Admin UI:
   /admin/learning                      # 학습 관리
   - 문서별 학습 상태 표시
   - 학습 시작/중지/초기화 버튼
   - 진행률 실시간 업데이트
   - 학습 결과 통계 (엔티티 개수 등)
```

#### Dependencies
- Story 4.2.3 (크롤링 완료 문서 필요)

---

## Epic 4.3: 법원판례 통합

**Epic ID**: EPIC-4.3
**예상 기간**: 8주
**Story Points**: 55
**비즈니스 가치**: 법률 컨텍스트 강화

### Story 4.3.1: 판례 데이터 모델 설계

**Story Points**: 8
**예상 기간**: 1주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] 판례 기본 정보 모델
  - 사건번호, 사건명, 법원, 판결일
  - 사건 종류 (형사/민사)
  - 원고, 피고
- [ ] 판결문 텍스트 저장
- [ ] 핵심 쟁점 추출
- [ ] 판결 요지 저장
- [ ] 관련 보험 상품 연결

#### Technical Tasks
```
1. Database Schema:
   CREATE TABLE court_cases (
     id UUID PRIMARY KEY,
     case_number TEXT UNIQUE, -- 사건번호 (예: 2023다12345)
     case_name TEXT, -- 사건명
     court_name TEXT, -- 법원명 (예: 서울중앙지방법원)
     case_type TEXT, -- 'criminal', 'civil'
     judgment_date DATE, -- 판결일
     plaintiff TEXT, -- 원고
     defendant TEXT, -- 피고
     judgment_summary TEXT, -- 판결 요지
     full_text TEXT, -- 판결문 전문
     key_issues JSONB, -- 핵심 쟁점 (AI 추출)
     related_products TEXT[], -- 관련 보험 상품
     source_url TEXT, -- 원본 URL
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

#### Dependencies
- None (독립 실행 가능)

---

### Story 4.3.2: 대법원 판례 크롤러 구현

**Story Points**: 21
**예상 기간**: 3주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] 대법원 종합법률정보 크롤링
- [ ] 검색 조건: "보험" + 최근 1년 (2024.12-2025.12)
- [ ] 형사/민사 판례 분리
- [ ] 판결문 전문 다운로드
- [ ] 페이징 처리 (전체 데이터 수집)
- [ ] 중복 제거

#### Technical Tasks
```
1. Crawler Implementation:
   class CourtCaseCrawler:
       BASE_URL = "https://glaw.scourt.go.kr"

       def search_cases(self, keyword: str, start_date: str, end_date: str, case_type: str):
           """판례 검색"""
           params = {
               "keyword": keyword,
               "start_date": start_date,
               "end_date": end_date,
               "case_type": case_type,
               "page": 1,
               "page_size": 100
           }

           cases = []
           while True:
               response = requests.get(f"{self.BASE_URL}/search", params=params)
               results = self.parse_search_results(response.text)

               if not results:
                   break

               cases.extend(results)
               params["page"] += 1

           return cases

       def download_full_text(self, case_url: str) -> str:
           """판결문 전문 다운로드"""
           response = requests.get(case_url)
           soup = BeautifulSoup(response.text, 'html.parser')
           full_text = soup.find('div', class_='judgment-text').get_text()
           return full_text

2. Celery Task:
   @celery_app.task
   def crawl_court_cases_2024():
       crawler = CourtCaseCrawler()

       # 2024.12 - 2025.12 보험 관련 판례
       cases = crawler.search_cases(
           keyword="보험",
           start_date="2024-12-01",
           end_date="2025-12-31",
           case_type="all"  # 형사 + 민사
       )

       for case in cases:
           # 중복 확인
           existing = db.query(CourtCase).filter(
               CourtCase.case_number == case['case_number']
           ).first()

           if existing:
               continue

           # 판결문 전문 다운로드
           full_text = crawler.download_full_text(case['url'])

           # DB 저장
           db_case = CourtCase(
               case_number=case['case_number'],
               case_name=case['name'],
               court_name=case['court'],
               case_type=case['type'],
               judgment_date=case['date'],
               plaintiff=case['plaintiff'],
               defendant=case['defendant'],
               judgment_summary=case['summary'],
               full_text=full_text,
               source_url=case['url']
           )
           db.add(db_case)
           db.commit()
```

#### Dependencies
- Story 4.3.1 (판례 모델 필요)

---

### Story 4.3.3: 판례 AI 분석 및 학습

**Story Points**: 21
**예상 기간**: 3주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] LLM 기반 핵심 쟁점 추출
- [ ] 관련 보험 종류 자동 태깅
- [ ] 판결 요지 자동 요약
- [ ] Neo4j 저장 (판례 노드)
- [ ] 보험 상품 노드와 연결
- [ ] 판례 검색 API

#### Technical Tasks
```
1. AI Analysis:
   class CourtCaseAnalyzer:
       def analyze_case(self, case_id: str):
           case = db.query(CourtCase).get(case_id)

           # 1. 핵심 쟁점 추출
           issues = self.extract_key_issues(case.full_text)

           # 2. 관련 보험 종류 태깅
           related_products = self.tag_insurance_types(case.full_text)

           # 3. 판결 요지 요약 (이미 있으면 스킵)
           if not case.judgment_summary:
               summary = self.summarize_judgment(case.full_text)
               case.judgment_summary = summary

           # 4. DB 업데이트
           case.key_issues = issues
           case.related_products = related_products
           db.commit()

           # 5. Neo4j 저장
           self.save_to_neo4j(case)

       def extract_key_issues(self, full_text: str) -> List[dict]:
           """LLM으로 핵심 쟁점 추출"""
           prompt = f"""
           다음 판결문에서 핵심 쟁점을 3-5개 추출하세요.

           판결문:
           {full_text[:5000]}  # 처음 5000자만

           출력 형식:
           [
             {{"issue": "보험금 부지급 사유의 정당성", "type": "coverage"}},
             {{"issue": "고지의무 위반 여부", "type": "disclosure"}},
             ...
           ]
           """

           response = llm.generate(prompt)
           issues = json.loads(response)
           return issues

       def tag_insurance_types(self, full_text: str) -> List[str]:
           """관련 보험 종류 태깅"""
           insurance_keywords = {
               "실손보험": ["실손", "실손의료보험"],
               "암보험": ["암", "암진단", "암보험"],
               "자동차보험": ["자동차", "차량", "교통사고"],
               "종신보험": ["종신", "사망보험"],
               "연금보험": ["연금", "노후"],
           }

           tagged = []
           for insurance_type, keywords in insurance_keywords.items():
               if any(keyword in full_text for keyword in keywords):
                   tagged.append(insurance_type)

           return tagged

       def save_to_neo4j(self, case: CourtCase):
           """Neo4j에 판례 노드 저장"""
           query = """
           CREATE (c:CourtCase {
             id: $case_id,
             case_number: $case_number,
             case_name: $case_name,
             judgment_date: $judgment_date,
             summary: $summary,
             key_issues: $key_issues
           })
           """

           neo4j_driver.execute_query(query, {
               "case_id": str(case.id),
               "case_number": case.case_number,
               "case_name": case.case_name,
               "judgment_date": case.judgment_date.isoformat(),
               "summary": case.judgment_summary,
               "key_issues": json.dumps(case.key_issues)
           })

           # 관련 보험 상품과 연결
           for product_name in case.related_products:
               connect_query = """
               MATCH (c:CourtCase {id: $case_id})
               MATCH (p:Product) WHERE p.name CONTAINS $product_name
               CREATE (c)-[:RELATED_TO]->(p)
               """
               neo4j_driver.execute_query(connect_query, {
                   "case_id": str(case.id),
                   "product_name": product_name
               })

2. Celery Task:
   @celery_app.task
   def analyze_all_cases():
       pending_cases = db.query(CourtCase).filter(
           CourtCase.key_issues == None
       ).all()

       for case in pending_cases:
           analyze_single_case.delay(case.id)

   @celery_app.task
   def analyze_single_case(case_id: str):
       analyzer = CourtCaseAnalyzer()
       analyzer.analyze_case(case_id)
```

#### Dependencies
- Story 4.3.2 (판례 크롤링 완료 필요)

---

### Story 4.3.4: 판례 검색 및 활용

**Story Points**: 5
**예상 기간**: 3일
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] 판례 검색 API (키워드, 날짜, 보험 종류)
- [ ] 질의응답 시 관련 판례 자동 표시
- [ ] "유사한 판례가 있습니다" 안내
- [ ] 판례 상세 페이지

#### Technical Tasks
```
1. API Endpoints:
   GET /api/v1/cases?keyword={}&insurance_type={}&date_from={}&date_to={}
   GET /api/v1/cases/:id
   GET /api/v1/cases/related?query={}

2. Frontend:
   /cases                              # 판례 검색 페이지
   /cases/:id                          # 판례 상세 페이지

3. Query Integration:
   # 질의응답 시 관련 판례 자동 조회
   def answer_query_with_cases(query: str):
       # 1. 기본 GraphRAG 답변
       answer = graphrag.answer(query)

       # 2. 관련 판례 검색
       related_cases = search_related_cases(query)

       # 3. 통합 응답
       return {
           "answer": answer,
           "related_cases": related_cases,
           "has_precedent": len(related_cases) > 0
       }
```

#### Dependencies
- Story 4.3.3 (판례 분석 완료 필요)

---

## Epic 4.4: 과거 자료 확장 (2차-5차)

**Epic ID**: EPIC-4.4
**예상 기간**: 연간 지속
**Story Points**: N/A (반복 작업)
**비즈니스 가치**: 히스토리 데이터 축적

### Story 4.4.1: 상품 히스토리 수집 (연도별)

**Story Points**: N/A
**예상 기간**: 연 1회 (3개월)
**우선순위**: P2 (Medium)

#### Acceptance Criteria
- [ ] 1차 완료 후 1년 단위 과거 자료 수집
- [ ] 2차: 2024년 판매 상품 (2025년 완료 후)
- [ ] 3차: 2023년 판매 상품 (2026년 완료 후)
- [ ] 버전 관리 (동일 상품의 연도별 개정)
- [ ] 차이 분석 (올해 vs 작년)

#### Technical Tasks
```
1. Versioning Strategy:
   products 테이블에 version 컬럼 활용

   예: "삼성화재 실손보험"
   - version 1: 2023년 버전
   - version 2: 2024년 버전
   - version 3: 2025년 버전 (현재)

2. Crawler Extension:
   def crawl_historical_products(insurer_id: str, year: int):
       """과거 연도 상품 크롤링"""
       # 보험사 홈페이지 > 상품 아카이브 페이지
       # 또는 금융감독원 공시자료 활용

3. Diff Analysis:
   def analyze_product_changes(product_name: str):
       """연도별 변경 사항 분석"""
       versions = db.query(Product).filter(
           Product.name == product_name
       ).order_by(Product.version).all()

       changes = []
       for i in range(len(versions) - 1):
           old = versions[i]
           new = versions[i + 1]

           # 약관 텍스트 비교
           diff = compare_texts(old.terms_text, new.terms_text)
           changes.append({
               "from_version": old.version,
               "to_version": new.version,
               "changes": diff
           })

       return changes
```

#### Dependencies
- Epic 4.2 (1차 수집 완료)

---

### Story 4.4.2: 판례 히스토리 수집 (연도별)

**Story Points**: N/A
**예상 기간**: 연 1회 (1개월)
**우선순위**: P2 (Medium)

#### Acceptance Criteria
- [ ] 1차 완료 후 1년 단위 과거 판례 수집
- [ ] 2차: 2023년 판례 (2025년 완료 후)
- [ ] 3차: 2022년 판례 (2026년 완료 후)
- [ ] 연도별 통계 (판례 개수, 주요 쟁점)

#### Technical Tasks
```
1. Historical Crawler:
   @celery_app.task
   def crawl_cases_by_year(year: int):
       crawler = CourtCaseCrawler()
       cases = crawler.search_cases(
           keyword="보험",
           start_date=f"{year}-01-01",
           end_date=f"{year}-12-31",
           case_type="all"
       )
       # ... 수집 및 저장

2. Annual Statistics:
   def generate_annual_case_stats(year: int):
       cases = db.query(CourtCase).filter(
           extract('year', CourtCase.judgment_date) == year
       ).all()

       stats = {
           "year": year,
           "total_cases": len(cases),
           "criminal_cases": sum(1 for c in cases if c.case_type == 'criminal'),
           "civil_cases": sum(1 for c in cases if c.case_type == 'civil'),
           "top_issues": get_top_issues(cases),
           "top_insurance_types": get_top_insurance_types(cases)
       }

       return stats
```

#### Dependencies
- Epic 4.3 (1차 수집 완료)

---

## 📊 개발 로드맵

### Phase 4 전체 일정 (22주)

```
Week 1-2: Epic 4.1 (보험사 관리)
  ✅ Story 4.1.1: 보험사 마스터 CRUD

Week 3-12: Epic 4.2 (상품 데이터 수집)
  Week 3-4:   Story 4.2.1 카테고리 체계
  Week 5:     Story 4.2.2 상품 모델
  Week 6-13:  Story 4.2.3 30개 크롤러 (병렬)
  Week 14-15: Story 4.2.4 학습 관리

Week 16-23: Epic 4.3 (법원판례)
  Week 16:    Story 4.3.1 판례 모델
  Week 17-19: Story 4.3.2 판례 크롤러
  Week 20-22: Story 4.3.3 AI 분석
  Week 23:    Story 4.3.4 검색 및 활용

🎉 Week 23: 1차 데이터 수집 완료 → 서비스 개시

연간 반복: Epic 4.4 (과거 자료 확장)
  매년 Q1: 전년도 상품 수집 (3개월)
  매년 Q2: 전년도 판례 수집 (1개월)
```

---

## 📊 예상 데이터 규모

### 1차 수집 (2025년 현재)

| 데이터 | 예상 규모 |
|--------|----------|
| **보험사** | 30개 |
| **상품** | 500-1,000개 |
| **문서** | 2,000-3,000개 |
| **판례 (1년)** | 500-1,000건 |

### 5차 수집 (2029년, 5년 누적)

| 데이터 | 예상 규모 |
|--------|----------|
| **보험사** | 30개 |
| **상품 (버전 포함)** | 3,000-5,000개 |
| **문서** | 10,000-15,000개 |
| **판례 (5년)** | 2,500-5,000건 |

---

## 💰 예상 비용

### 개발 비용 (22주)

| 항목 | 예상 비용 |
|-----|----------|
| **Backend 개발** | $80,000 |
| **크롤러 개발 (30개)** | $60,000 |
| **AI 분석 개발** | $40,000 |
| **QA 및 테스트** | $20,000 |
| **총계** | **$200,000** |

### 연간 운영 비용

| 항목 | 예상 비용 |
|-----|----------|
| **스토리지 (10TB)** | $200/월 |
| **크롤링 서버** | $150/월 |
| **LLM API (판례 분석)** | $300/월 |
| **총계** | **$650/월** |

---

## 🎯 성공 지표 (KPI)

### 1차 수집 목표

| 지표 | 목표 |
|-----|------|
| **보험사 커버리지** | 100% (30개) |
| **상품 수집률** | > 90% |
| **문서 완전성** | > 95% (필수 문서) |
| **크롤링 성공률** | > 85% |
| **학습 성공률** | > 90% |
| **판례 수집** | > 500건 |

---

## ✅ Definition of Done

### 1차 수집 완료 기준

- [ ] 30개 보험사 모두 크롤러 구현 완료
- [ ] 각 보험사당 평균 20개 이상 상품 수집
- [ ] 상품별 필수 문서 (설명서, 약관) 95% 이상 확보
- [ ] 전체 문서 90% 이상 학습 완료
- [ ] Neo4j에 50,000개 이상 엔티티 저장
- [ ] 2024-2025년 보험 판례 500건 이상 수집
- [ ] 판례 AI 분석 90% 이상 완료
- [ ] 서비스 출시 승인

---

## 🚀 Quick Start

### Week 1: 보험사 마스터 구축

```bash
# 1. 데이터베이스 마이그레이션
cd backend
alembic revision --autogenerate -m "Add Phase 4 tables"
alembic upgrade head

# 2. 30개 보험사 초기 데이터 삽입
python scripts/seed_insurers.py

# 3. 관리자 UI 접속
http://localhost:3000/admin/insurers

# 4. 개발 시작
git checkout -b feature/epic-4.1-insurer-management
```

---

## 🎉 결론

### 비전

```
1차 (Week 23)
  └─ 2025년 현재 전상품 + 1년 판례 ✅
     → 서비스 개시

2차 (2026년)
  └─ + 2024년 상품 + 2년 판례

3차 (2027년)
  └─ + 2023년 상품 + 3년 판례

4차 (2028년)
  └─ + 2022년 상품 + 4년 판례

5차 (2029년)
  └─ + 2021년 상품 + 5년 판례
     → 5년 히스토리 완성 🎉
```

### 예상 효과

**1차 완료 시**:
- 전보험사 현재 상품 데이터 확보
- 즉시 서비스 출시 가능
- 경쟁사 대비 데이터 우위

**5차 완료 시**:
- 5년간 상품 변화 추적 가능
- 5년간 판례 분석으로 법률 전문성 확보
- 시장 트렌드 예측 가능

---

**작성자**: Claude (AI Assistant)
**최종 수정**: 2025-12-05
**다음 리뷰**: 1차 수집 완료 시 (Week 23)

**승인 필요**: Product Owner, Legal Team
**다음 액션**: Epic 4.1 개발 착수

