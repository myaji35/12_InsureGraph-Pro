Product Requirements Document (PRD): InsureGraph Pro
Version: 1.0.0 Status: Draft (Pending Architect Review) Date: 2025-05-20 Methodology: BMAD (Breakthrough Method of Agile AI-Driven Development)

1. Executive Summary (Project Vision)
Project Name: InsureGraph Pro (가칭) Type: B2B2C SaaS Platform Target Audience: 법인보험대리점(GA) 소속 보험설계사(FP) 및 향후 보험 소비자

Vision: 한국 보험 시장의 구조적 문제인 '약관의 복잡성'과 '불완전 판매 리스크'를 GraphRAG(Graph Retrieval-Augmented Generation) 기술로 해결하는 지능형 영업 지원 플랫폼입니다. 기존의 단순 키워드 검색이나 Vector RAG가 해결하지 못한 '복합 추론(Multi-hop Reasoning)'과 '상호 참조(Cross-reference) 해석'을 통해, FP에게는 초격차 분석 능력을 제공하고, 고객에게는 신뢰할 수 있는 보장을 제시합니다.

Key Value Proposition:

Deep Analysis: GraphRAG를 통해 수백 페이지 약관 내 숨겨진 보장/면책 조항 간의 인과관계를 시각화 및 분석.

Compliance Safety: 금융규제 샌드박스 및 마이데이터를 준수하며, 설명 의무 위반을 방지하는 AI 준법 감시 기능 내장.

Sales Acceleration: 고객의 보장 공백을 논리적으로 입증하여 '공포 마케팅'이 아닌 '근거 기반 세일즈' 가능.

2. User Personas
2.1. Primary: The "Hybrid" FP (김설계, 34세)
Role: GA 소속 3년 차 설계사. 손해보험/생명보험 교차 판매.

Pain Point: 여러 보험사의 상품을 취급하지만, 약관이 너무 달라 세부 내용을 외울 수 없음. 고객이 "갑상선 전이암 보장돼요?"라고 물을 때 즉답하기 두려움. DB 구매 비용(건당 7~9만 원) 대비 성약률이 낮아 고민.

Goal: 약관을 펴보지 않고도 AI가 찾아주는 근거를 통해 전문가처럼 보이고 싶음. 기존 고객 리스트에서 추가 계약 기회를 자동으로 찾고 싶음.

2.2. Secondary: GA Branch Manager (박지점장, 45세)
Role: 설계사 50명을 관리하는 GA 지점장.

Pain Point: 신입 설계사의 잦은 이탈과 불완전 판매로 인한 민원 발생.

Goal: 설계사들의 상담 품질을 표준화하고, 민원 리스크를 사전에 차단하는 시스템 도입.

2.3. Tertiary: End-User (이보험, 40세) - Phase 2 Expansion
Role: 보험 가입자.

Goal: 내 보험이 실제로 어떤 상황에서 돈이 나오는지 시각적으로 확인하고 싶음. 텍스트가 아닌 그래프나 쉬운 요약본을 원함.

3. Product Architecture & Methodology (BMAD Focus)
이 프로젝트는 BMAD Method를 따르며, LLM의 할루시네이션을 최소화하기 위해 GraphRAG 아키텍처를 핵심 엔진으로 사용합니다.

3.1. Core Tech Stack
LLM: Upstage Solar Pro (한국어 문서 이해 특화) or GPT-4o (복합 추론).

Graph Database: Neo4j (Graph Algorithm 및 Vector Index 하이브리드 지원).

Vector Database: Milvus or Pinecone (비정형 텍스트 임베딩).

Backend: Python (FastAPI, LangChain/LangGraph).

Frontend: Next.js (React), D3.js or Cytoscape.js (그래프 시각화).

OCR: Upstage Document Parse or Naver Clova OCR (표/서식 인식 필수).

3.2. Conceptual Model: The "Insurance Knowledge Graph"
Nodes: Product(상품), Clause(조항), Disease(질병/KCD코드), Coverage(담보), Exclusion(면책), Condition(지급조건).

Edges: COVERS(보장하다), EXCLUDES(면책하다), REQUIRES(조건을 요하다), LINKED_TO(참조하다), PRECEDES(우선하다).

4. Epics & User Stories
Epic 1: Data Ingestion & Knowledge Graph Construction (Backend)
약관 PDF를 구조화된 지식 그래프로 변환하는 핵심 파이프라인

Feature 1.1: Intelligent OCR & Parsing

Story: 시스템은 PDF 약관을 업로드하면 텍스트, 표, 플로우차트를 인식하여 Markdown 형식으로 변환해야 한다.

Story: 텍스트 내에서 '제1조', '①항', '다만' 등의 법률적 계층 구조를 식별하여 청크(Chunk) 단위로 분할해야 한다.

Feature 1.2: Entity & Relation Extraction (LLM Agent)

Story: LLM은 청크에서 주체(Subject), 행위(Action), 객체(Object), 조건(Condition)을 추출하여 Triple(S-P-O)을 생성해야 한다. (예: 갑상선암 --면책기간--> 90일)

Story: 추출된 Entity를 표준 용어(Ontology)에 매핑해야 한다. (예: '악성신생물' -> '암'으로 통일).

Epic 2: GraphRAG Query Engine (Logic)
사용자 질문을 그래프 쿼리(Cypher)로 변환하고 답변을 생성

Feature 2.1: Hybrid Retrieval

Story: 사용자가 자연어로 질문하면, Vector Search로 관련 텍스트를 찾고(Local), Graph Traversal로 연결된 숨겨진 조항(Global)을 동시에 탐색해야 한다.

Story (Conflict Detection): "A상품과 B상품 중복 보장돼?" 질문 시, 그래프상에서 비례보상 속성 노드가 두 상품에 모두 연결되어 있는지 검사하여 충돌을 감지해야 한다.

Feature 2.2: Reasoning Path Visualization

Story: 답변과 함께 AI가 어떤 경로(Node -> Edge -> Node)를 통해 결론을 내렸는지 시각적 그래프로 보여주어 FP가 고객에게 설명할 근거를 제공해야 한다.

Epic 3: FP Workspace & Analysis Dashboard (Frontend)
FP가 업무를 수행하는 메인 인터페이스

Feature 3.1: Customer Portfolio Upload (MyData)

Story: FP는 고객의 동의 하에 '내보험다보여' 또는 'MyData API'를 통해 기가입 증권을 원클릭으로 불러올 수 있어야 한다.

Constraint: PII(주민번호 뒷자리 등)는 마스킹 처리되어 DB에 저장되어야 한다.

Feature 3.2: Sales Opportunity Alert

Story: 시스템은 고객의 약관을 분석하여 "2011년 이전 가입 암보험 보유 -> 갑상선 림프절 전이 일반암 청구 가능성 높음"과 같은 Actionable Insight를 알림으로 제공해야 한다.

Epic 4: Compliance & Security (Non-Functional)
Feature 4.1: Logical Network Separation (Sandbox)

Story: SaaS 형태로 제공되지만, 데이터 처리 구간은 논리적 망분리 규정을 준수하여 외부 침입을 차단해야 한다 (금융규제 샌드박스 요건 충족).

Story: 모든 상담 스크립트 생성 시 "설명 의무" 필수 키워드가 포함되었는지 검증하는 로직이 돌아가야 한다.

5. Functional Requirements (Detailed Specs for Devs)
5.1. Graph Schema Design (Draft)
개발자는 아래 스키마를 기준으로 Neo4j를 모델링할 것.

Cypher
(:Product {name, insurer, launch_date})
(:Coverage {name, code, amount})
(:Disease {kcd_code, name, type:['minor', 'general', 'ci']})
(:Condition {type:['waiting_period', 'reduction_period'], days: int, percentage: float})

(Product)-->(Coverage)
(Coverage)-->(Disease)
(Coverage)-->(Disease)
(Coverage)-->(Condition)
(Product)-->(Product) // 파생 관계 (Pre-computed)
5.2. API Endpoints (FastAPI)
POST /api/v1/ingest/policy: PDF 업로드 및 그래프 파이프라인 트리거.

POST /api/v1/analysis/query: 사용자 자연어 질문 입력 -> GraphRAG 결과 반환.

GET /api/v1/customer/{id}/gap-analysis: 고객 보장 공백 분석 리포트 생성.

POST /api/v1/compliance/check-script: 생성된 세일즈 스크립트의 법적 리스크 검증.

6. UI/UX Guidelines
Tone: Professional, Trustworthy, Sharp. (금융 전문가용 툴 느낌)

Visuals:

텍스트 중심이 아닌 **카드(Card)**와 노드(Node) 중심 인터페이스.

복잡한 약관은 '요약 카드'를 먼저 보여주고, 클릭 시 원문과 그래프가 펼쳐지는 Drill-down 방식.

Mobile First: FP들의 외근이 잦으므로 모바일/태블릿 뷰 최적화 필수.

7. Go-to-Market Strategy (Phasing)
Phase 1: MVP (Months 1-3)
Focus: 특정 암보험/뇌심혈관 질환 약관 50종 학습.

Target: 얼리어답터 FP 100명 베타 테스트.

Core Feature: PDF 업로드 시 자동 분석 및 "질병 코드별 보장 여부 O/X 퀴즈" 기능.

Phase 2: Commercial Launch (Months 4-6)
Focus: MyData API 연동 및 전 보험사 약관 확장.

Feature: 고객용 '보장 분석 리포트' 공유 기능 (카카오톡 연동).

Pricing: Freemium (기본 무료, 심층 분석 건당 과금 또는 월 구독).

Phase 3: B2C Expansion (Month 7+)
Focus: 일반 고객이 직접 자신의 보험을 진단하고 FP에게 상담을 요청하는 '역경매' 매칭 시스템.

8. Risks & Mitigation
Risk	Impact	Mitigation Strategy
Hallucination	치명적 (오안내로 인한 배상 책임)	GraphRAG의 '근거 기반' 답변만 출력하도록 설정. 답변 하단에 "약관 원문 제X조 X항 참조" 링크 필수 첨부.
Regulatory	서비스 중단	금융규제 샌드박스 '혁신금융서비스' 사전 신청 및 지정 획득. 개인정보 비식별화 모듈 최우선 개발.
Data Quality	분석 오류	LLM이 아닌 Rule-based 파서와 병행하여 약관의 숫자(금액, 기간) 데이터 정확도 이중 검증.
Note to Developers (BMAD Context):

Analyst Agent: Has verified the market need for "C77 thyroid cancer" like specific use cases.

Architect Agent: Needs to design the GraphRetriever class to specifically handle the schema defined in section 5.1.

Scrum Master: Prioritize "Ingestion Pipeline" stories as they are blockers for Query features.

