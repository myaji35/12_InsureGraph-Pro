# InsureGraph Pro 구축 과정 기록

## 프로젝트 개요
- **시스템명**: InsureGraph Pro
- **목적**: 보험 약관 PDF 문서에서 지식 그래프를 자동 생성하여 보험 상품 비교 및 분석 지원
- **핵심 기술**: pdfplumber (PDF 파싱) + Claude API (엔티티 추출) + Neo4j (지식 그래프)

## 시스템 아키텍처

### 1. 기술 스택
- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python), PostgreSQL, Neo4j, Redis
- **AI/ML**: Claude 3.5 Sonnet (Anthropic API)
- **PDF Processing**: pdfplumber 0.11.8
- **Authentication**: Clerk

### 2. 데이터 처리 파이프라인

```
PDF 업로드
  → 텍스트 추출 (pdfplumber)
  → 조항 구조 파싱 (정규식)
  → 엔티티 추출 (Claude API)
  → 지식 그래프 생성 (Neo4j)
  → 결과 저장 (PostgreSQL)
```

## 구현 단계

### Phase 1: 환경 설정 (2025-11-27)

#### 1.1 라이브러리 설치
```bash
pip install pdfplumber==0.11.8
pip install anthropic==0.75.0
pip install Pillow==12.0.0
```

**설치된 주요 의존성**:
- `pdfplumber`: PDF 텍스트 및 테이블 추출
- `anthropic`: Claude API 클라이언트
- `pdfminer.six`: PDF 파싱 엔진
- `pypdfium2`: PDF 렌더링
- `cryptography`: 암호화된 PDF 지원

#### 1.2 개발 이슈
- **문제**: Python 3.14 환경에서 Pillow 10.2.0 빌드 실패
  - 원인: Pillow 10.2.0의 `setup.py`에서 `__version__` KeyError 발생
  - 해결: 최신 버전 Pillow 12.0.0 사용 (Python 3.14 호환)

### Phase 2: PDF 처리 서비스 구현

#### 2.1 설계 방침
1. **모듈화**: PDF 처리 로직을 독립적인 서비스로 분리
2. **확장성**: 다양한 보험사 약관 형식 대응 가능하도록 설계
3. **비동기 처리**: FastAPI의 async/await 활용
4. **진행률 추적**: 실시간 처리 상태 업데이트

#### 2.2 구현 파일
- `/backend/app/services/pdf_processor.py`: PDF 처리 핵심 로직
- `/backend/app/services/knowledge_graph.py`: Neo4j 그래프 생성 로직
- `/backend/app/api/v1/endpoints/documents.py`: 업로드 엔드포인트 연동

### Phase 3: PDF 처리 파이프라인 구현 (2025-11-27)

#### 3.1 PDF 처리 서비스 (`pdf_processor.py`)

**핵심 기능**:
1. **PDF 텍스트 추출** (`extract_text_from_pdf`)
   - pdfplumber로 페이지별 텍스트 추출
   - 테이블 데이터도 텍스트로 변환하여 포함
   - 페이지 번호 태그 추가로 원본 위치 추적

2. **조항 구조 파싱** (`parse_articles`)
   - 정규식으로 한국 보험 약관 구조 인식: `제N조 (제목)`
   - 각 조항의 제목, 내용, 페이지 번호, 단락 추출
   - Article 데이터클래스로 구조화

3. **Claude API 엔티티 추출** (`extract_entities_from_article`)
   - 조항별로 Claude 3.5 Sonnet 호출
   - 6가지 엔티티 타입 추출:
     - COVERAGE (보장 내용)
     - EXCLUSION (면책 사항)
     - CONDITION (보장 조건)
     - TERM (용어 정의)
     - BENEFIT (급여 혜택)
     - REQUIREMENT (요구 사항)
   - JSON 형식으로 구조화된 데이터 반환

4. **파싱 신뢰도 계산**
   - 조항 수, 엔티티 수, 엔티티 신뢰도 기반으로 종합 계산
   - 0.0 ~ 1.0 범위의 신뢰도 점수

**프롬프트 엔지니어링**:
```
- 역할 정의: "당신은 보험 약관 분석 전문가입니다"
- Few-shot 예시 제공으로 엔티티 타입별 추출 기준 명확화
- JSON 형식 출력 강제로 파싱 안정성 확보
- Temperature 0.0으로 일관성 있는 결과 생성
```

#### 3.2 지식 그래프 서비스 (`knowledge_graph.py`)

**Neo4j 스키마 설계**:

1. **노드 타입**:
   - `Document`: 보험 약관 문서
   - `Article`: 개별 조항 (제1조, 제2조 등)
   - `Coverage`, `Exclusion`, `Condition`, `Term`, `Benefit`, `Requirement`: 엔티티 노드

2. **관계 타입**:
   - `HAS_ARTICLE`: Document → Article
   - `EXTRACTED_FROM`: Entity → Article
   - `HAS_CONDITION`: Coverage → Condition
   - `HAS_BENEFIT`: Coverage → Benefit
   - `HAS_EXCLUSION`: Coverage → Exclusion

**핵심 기능**:
1. **그래프 생성** (`create_document_graph`)
   - 문서 노드 생성
   - 조항 노드 생성 및 문서와 연결
   - 엔티티 노드 생성 및 조항과 연결
   - 엔티티 간 관계 추론 (같은 조항 내)

2. **관계 추론**:
   - COVERAGE와 CONDITION을 자동으로 HAS_CONDITION 관계 생성
   - COVERAGE와 BENEFIT을 HAS_BENEFIT 관계로 연결
   - COVERAGE와 EXCLUSION을 HAS_EXCLUSION 관계로 연결

3. **그래프 통계 및 관리**:
   - 노드/관계 생성 통계 제공
   - 문서별 그래프 삭제 기능
   - 엔티티 검색 기능

#### 3.3 백그라운드 작업 통합

**처리 파이프라인**:
```
1. PDF 파일 로딩 (5%)
2. pdfplumber 텍스트 추출 (10-30%)
3. 조항 파싱 (35%)
4. Claude API 엔티티 추출 (40-70%)
5. Neo4j 지식 그래프 생성 (75-90%)
6. 메타데이터 업데이트 (95%)
7. 완료 (100%)
```

**진행률 추적**:
- PostgreSQL `processing_jobs` 테이블에 실시간 진행률 업데이트
- 단계별 `current_step` 메시지 저장
- 프론트엔드에서 폴링으로 진행률 표시 가능

#### 3.4 설정 업데이트

**환경 변수 추가** (`app/core/config.py`):
```python
ANTHROPIC_API_KEY: str  # Claude API 인증
```

**의존성 버전 확정** (`requirements.txt`):
```
pdfplumber==0.11.0
anthropic==0.18.1
Pillow==10.2.0
```

**실제 설치 버전** (Python 3.14 호환):
```
pdfplumber==0.11.8
anthropic==0.75.0
Pillow==12.0.0
```

#### 3.5 개발 중 해결한 이슈

**Issue 1: Python 3.14에서 Pillow 10.2.0 빌드 실패**
- 증상: `KeyError: '__version__'` 발생
- 원인: Pillow 10.2.0의 setup.py가 Python 3.14와 호환되지 않음
- 해결: 최신 버전 Pillow 12.0.0 사용

**Issue 2: UUID 직렬화 오류 (psycopg2)**
- 증상: `can't adapt type 'UUID'`
- 원인: psycopg2가 Python UUID 객체를 PostgreSQL UUID로 변환하지 못함
- 해결: `register_uuid()` 호출로 어댑터 등록 (database.py)

**Issue 3: 파일 업로드 타임아웃**
- 초기 설정: 30초 → 너무 짧음
- 조정: 120초 (2분)로 변경
- 이유: PDF 처리 + DB 저장 + 백그라운드 작업 시작 시간 고려

## 다음 단계
1. ~~PDF 처리 서비스 구현~~ ✅ 완료
2. ~~Claude API 프롬프트 엔지니어링~~ ✅ 완료
3. ~~Neo4j 스키마 정의~~ ✅ 완료
4. ~~백그라운드 작업 통합~~ ✅ 완료
5. **실제 PDF 파일 테스트**
6. **GCS 파일 업로드 연동**
7. **프론트엔드 진행률 UI 개선**
8. **에러 핸들링 및 재시도 로직 추가**
9. **성능 최적화 (Claude API 배치 호출)**

## 참고 문헌
- pdfplumber Documentation: https://github.com/jsvine/pdfplumber
- Anthropic Claude API: https://docs.anthropic.com/
- Neo4j Graph Database: https://neo4j.com/docs/
