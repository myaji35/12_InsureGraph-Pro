# Frontend Story 3 완료 요약

**Story**: 질의응답 인터페이스
**Story Points**: 5
**Status**: ✅ COMPLETED
**완료일**: 2025-11-25

## 📋 Story 목표

AI 기반 질의응답 시스템 구현 (문서 선택, 질의 입력, 답변 표시, 인용 출처, 히스토리)

## ✅ 완료된 작업

### 1. 상태 관리

#### Query Store (`src/store/query-store.ts`)
**라인 수**: 95 lines

**상태 필드**:
```typescript
interface QueryState {
  currentQuery: QueryResponse | null
  queryHistory: QueryHistoryItem[]  // 최대 50개 저장
  isLoading: boolean
  error: string | null
}
```

**구현된 액션**:
- `executeQuery(data)` - 질의 실행 및 히스토리에 자동 추가
- `getQueryStatus(queryId)` - 질의 상태 조회 (히스토리에서 선택 시)
- `clearError()` - 에러 초기화
- `clearCurrentQuery()` - 현재 질의 초기화
- `addToHistory(query)` - 히스토리에 질의 추가 (최대 50개)

**특징**:
- 자동 히스토리 관리 (executeQuery 시 자동 추가)
- 최대 50개까지 저장 (FIFO)
- timestamp 자동 추가

### 2. 문서 선택 인터페이스

#### DocumentSelector 컴포넌트 (`src/components/DocumentSelector.tsx`)
**라인 수**: 165 lines

**주요 기능**:

1. **문서 검색**
   - 실시간 클라이언트 측 검색
   - 상품명, 보험사 필터링
   - MagnifyingGlassIcon 사용

2. **문서 선택**
   - 개별 선택 (체크박스)
   - 전체 선택/해제 토글
   - 선택된 문서 수 표시
   - 시각적 피드백 (선택 시 primary-50 배경)

3. **문서 카드**
   - 상품명 (truncate)
   - 보험사
   - 태그 표시 (최대 3개 + 더보기)
   - 체크 아이콘 표시

4. **빈 상태**
   - 문서가 없을 때 안내
   - 검색 결과 없을 때 안내

**API 연동**:
- `fetchDocuments({ status: 'ready', page_size: 100 })` - 준비된 문서만 로드
- useDocumentStore 사용

### 3. 답변 표시 시스템

#### AnswerDisplay 컴포넌트 (`src/components/AnswerDisplay.tsx`)
**라인 수**: 140 lines

**구현된 섹션**:

1. **상태별 표시**
   - **pending/processing**: 로딩 스피너 + 상태 메시지
   - **failed**: 빨간색 에러 메시지 카드
   - **completed**: 답변 + 인용 출처

2. **답변 섹션**
   - CheckCircleIcon (녹색)
   - ReactMarkdown 렌더링
   - remarkGfm 플러그인 (GitHub Flavored Markdown)
   - prose 스타일 적용
   - 신뢰도 점수 표시 (프로그레스 바)
     - 80% 이상: 녹색
     - 60-80%: 노란색
     - 60% 이하: 빨간색

3. **인용 출처 섹션**
   - DocumentTextIcon (primary)
   - 인용 개수 표시
   - 인용 카드 (번호 배지 + 내용)
   - 관련도 점수 표시
   - 메타데이터 표시 (페이지 번호, 섹션)
   - 호버 효과 (border-primary-300)

4. **처리 시간**
   - 하단에 작은 텍스트로 표시

**마크다운 렌더링**:
```typescript
<ReactMarkdown remarkPlugins={[remarkGfm]}>
  {query.answer}
</ReactMarkdown>
```

**신뢰도 표시**:
```typescript
<div className="w-32 h-2 bg-gray-200 rounded-full">
  <div
    className="h-full rounded-full bg-green-500"
    style={{ width: `${score * 100}%` }}
  />
</div>
```

### 4. 질의 히스토리

#### QueryHistory 컴포넌트 (`src/components/QueryHistory.tsx`)
**라인 수**: 70 lines

**주요 기능**:
- 최근 질의 내역 표시 (최대 50개)
- 질의 클릭하여 재조회
- 상태 배지 (완료/처리중/실패/대기)
- 질문 텍스트 미리보기 (line-clamp-2)
- 타임스탬프 표시
- 인용 개수 표시
- 스크롤 가능 (max-h-96)
- 호버 효과 (border-primary-300, bg-primary-50)

**빈 상태**:
- ChatBubbleLeftRightIcon
- "아직 질의 내역이 없습니다" 메시지

### 5. 메인 Query 페이지

#### Query 페이지 (`src/app/query/page.tsx`)
**라인 수**: 180 lines

**레이아웃**:
- 2열 그리드 (lg:grid-cols-3)
  - 왼쪽 (1/3): 질의 입력 + 히스토리
  - 오른쪽 (2/3): 답변 표시

**질의 입력 폼**:
1. **질문 입력**
   - textarea (4 rows)
   - placeholder 예시
   - disabled when loading

2. **문서 선택**
   - "문서 선택" 버튼으로 토글
   - DocumentSelector 컴포넌트 통합
   - 선택된 문서 수 표시
   - 배지로 간단한 요약 표시

3. **에러 메시지**
   - 빨간색 배너

4. **제출 버튼**
   - PaperAirplaneIcon
   - "질문하기" 텍스트
   - 로딩 중: 스피너 + "처리 중..."
   - disabled: 질문 없음 or 문서 미선택

**답변 표시 영역**:
- currentQuery가 있으면 AnswerDisplay
- 없으면 빈 상태 (예시 질문 3개)
  - "질문을 입력하세요" 헤딩
  - 설명 텍스트
  - 3개 예시 질문 카드

**폼 제출 로직**:
```typescript
const handleSubmit = async (e) => {
  e.preventDefault()

  // Validation
  if (!question.trim()) return
  if (selectedDocumentIds.length === 0) {
    alert('문서를 선택해주세요')
    return
  }

  // Execute query
  await executeQuery({
    question: question.trim(),
    document_ids: selectedDocumentIds,
  })

  // Don't clear form (사용자가 질문 확인 가능)
}
```

**히스토리 선택**:
```typescript
const handleSelectFromHistory = async (queryId) => {
  await getQueryStatus(queryId)
  // currentQuery 업데이트됨
}
```

### 6. 스타일링 개선

#### Markdown Prose 스타일 (`src/styles/globals.css`)
**추가된 스타일**: ~70 lines

**구현된 요소**:
- `.prose` - 기본 텍스트 스타일
- `.prose h1, h2, h3` - 헤딩 스타일
- `.prose p` - 문단 여백
- `.prose ul, ol` - 리스트 스타일
- `.prose a` - 링크 (primary-600)
- `.prose strong, em` - 강조
- `.prose code, pre` - 코드 블록
- `.prose blockquote` - 인용구 (border-l-4, primary-500)
- `.prose table, th, td` - 테이블

**특징**:
- Tailwind @apply 사용
- 일관된 색상 팔레트
- 적절한 여백 및 간격

### 7. 의존성 추가

#### package.json 업데이트
**추가된 패키지**:
```json
"react-markdown": "^9.0.1"   // 마크다운 렌더링
"remark-gfm": "^4.0.0"        // GitHub Flavored Markdown
```

**기능**:
- 테이블, 체크리스트, strikethrough 등 지원
- 안전한 HTML 렌더링
- 커스텀 컴포넌트 지원

## 📊 통계

### 생성된 파일
- **상태 관리**: 1개 (query-store.ts)
- **컴포넌트**: 3개 (DocumentSelector, AnswerDisplay, QueryHistory)
- **페이지**: 1개 (query/page.tsx)
- **스타일**: globals.css 업데이트

**총 파일 수**: 5개 (1 new page, 3 new components, 1 store, 1 style update)

### 코드 라인 수
```
Query Store:             95 lines
DocumentSelector:        165 lines
AnswerDisplay:           140 lines
QueryHistory:            70 lines
Query Page:              180 lines
Prose Styles:            ~70 lines
--------------------------------------
Total:                   ~720 lines
```

### 구현된 기능
- ✅ 질의 상태 관리 (Zustand)
- ✅ 문서 검색 & 선택 (개별/전체)
- ✅ 질의 입력 폼 (textarea, validation)
- ✅ 질의 실행 & 로딩 상태
- ✅ 답변 표시 (마크다운 렌더링)
- ✅ 신뢰도 점수 시각화
- ✅ 인용 출처 표시 (카드)
- ✅ 질의 히스토리 (최대 50개)
- ✅ 히스토리에서 재조회
- ✅ 상태별 UI (pending/processing/completed/failed)
- ✅ 에러 핸들링
- ✅ 빈 상태 (예시 질문)

## 🎯 Acceptance Criteria 달성

### 1. 질의 입력 폼 ✅
- ✅ textarea 질문 입력
- ✅ placeholder & 예시
- ✅ 유효성 검사 (질문, 문서 선택)
- ✅ 제출 버튼 (disabled 상태)
- ✅ 로딩 상태 표시

### 2. 문서 선택 인터페이스 ✅
- ✅ 준비된 문서 목록 표시
- ✅ 검색 기능
- ✅ 개별 선택 (체크박스)
- ✅ 전체 선택/해제
- ✅ 선택된 문서 수 표시
- ✅ 토글 UI (열기/닫기)

### 3. 질의 실행 & 진행 상태 ✅
- ✅ API 호출 (executeQuery)
- ✅ 로딩 스피너
- ✅ 상태 메시지 (대기/처리중)
- ✅ 에러 핸들링

### 4. 답변 표시 (마크다운) ✅
- ✅ ReactMarkdown 렌더링
- ✅ remarkGfm 플러그인
- ✅ Prose 스타일 (h1-h3, ul, ol, code, table 등)
- ✅ 신뢰도 점수 표시 (프로그레스 바)
- ✅ 처리 시간 표시

### 5. 인용 출처 표시 ✅
- ✅ 인용 카드 (번호 배지)
- ✅ 인용 내용 표시
- ✅ 문서명
- ✅ 관련도 점수
- ✅ 메타데이터 (페이지, 섹션)
- ✅ 호버 효과

### 6. 질의 히스토리 ✅
- ✅ 최근 질의 목록 (최대 50개)
- ✅ 질의 클릭하여 재조회
- ✅ 상태 배지
- ✅ 타임스탬프
- ✅ 인용 개수
- ✅ 스크롤 가능

## 🎨 UI/UX 개선사항

### 반응형 레이아웃
- Mobile: 1열 (스택)
- Desktop: 3열 그리드 (1:2 비율)
- 모든 컴포넌트 반응형

### 인터랙티브 요소
- 문서 선택: 클릭 가능 카드, 체크박스
- 히스토리: 클릭하여 재조회
- 문서 선택기: 토글 열기/닫기
- 검색: 실시간 필터링

### 시각적 피드백
- 선택된 문서: primary-50 배경
- 로딩: 스피너 + 메시지
- 에러: 빨간색 배너
- 신뢰도: 색상 구분 (녹/노/빨)
- 호버 효과: shadow, border 변경

### 빈 상태
- 답변 없음: 예시 질문 3개
- 히스토리 없음: 안내 메시지
- 문서 없음: 아이콘 + 메시지

## 🔧 기술적 의사결정

### 1. react-markdown 선택
**이유**:
- React 컴포넌트 기반
- 안전한 HTML 렌더링 (XSS 방지)
- remarkGfm으로 확장 가능
- TypeScript 지원

### 2. 히스토리 최대 50개
**이유**:
- 메모리 효율성
- 충분한 히스토리 제공
- FIFO 방식으로 자동 관리

### 3. 클라이언트 측 문서 검색
**이유**:
- 빠른 응답
- 서버 부하 감소
- 100개 이하 문서에 적합
- 실시간 필터링

### 4. 토글 방식 문서 선택기
**이유**:
- 화면 공간 절약
- 선택 후 폼에 집중 가능
- 선택된 문서 수만 표시
- 필요할 때만 열기

### 5. 폼 초기화 안 함
**이유**:
- 사용자가 질문 확인 가능
- 다시 질문하기 편함
- 히스토리에 저장됨

## 📝 다음 단계 (Story 4)

**Story 4: 그래프 시각화 (4 pts)**

구현 예정:
- 지식 그래프 시각화 (D3.js or React Flow)
- 노드 & 엣지 표시
- 인터랙티브 그래프 (줌, 드래그)
- 노드 클릭 상세 정보
- 그래프 필터링

## ✅ 테스트 가이드

### 수동 테스트 시나리오

#### 1. 문서 선택 테스트
```
1. 질의응답 페이지 접근 (/query)
2. "문서 선택" 버튼 클릭
3. 검색창에 보험사 이름 입력
4. 필터링 확인
5. 문서 클릭하여 선택
6. 체크 아이콘 확인
7. "전체 선택" 클릭
8. 모든 문서 선택 확인
9. "선택 해제" 클릭
10. 모든 선택 해제 확인
```

#### 2. 질의 실행 테스트
```
1. 문서 1-2개 선택
2. 질문 입력 (예: "암 진단 시 보장 내용은?")
3. "질문하기" 버튼 클릭
4. 로딩 스피너 확인
5. 답변 표시 확인
6. 마크다운 렌더링 확인 (헤딩, 리스트 등)
7. 신뢰도 점수 확인
8. 인용 출처 카드 확인
9. 처리 시간 확인
```

#### 3. 마크다운 렌더링 테스트
```
답변에 다음 요소가 포함되었는지 확인:
- 헤딩 (# ## ###)
- 리스트 (- or 1.)
- 강조 (**bold**, *italic*)
- 코드 (`code`)
- 링크
- 테이블 (| | |)

각 요소가 올바르게 렌더링되는지 확인
```

#### 4. 히스토리 테스트
```
1. 여러 질의 실행 (3-5개)
2. 히스토리 목록 확인
3. 가장 최근 질의가 맨 위에 있는지 확인
4. 히스토리에서 이전 질의 클릭
5. 해당 질의의 답변 표시 확인
6. 상태 배지 확인 (완료/처리중/실패)
```

#### 5. 에러 처리 테스트
```
1. 문서 선택 없이 "질문하기" 클릭
2. 경고 메시지 확인
3. 질문 입력 없이 "질문하기" 클릭
4. 버튼 disabled 확인
5. 네트워크 에러 시뮬레이션 (개발자 도구)
6. 에러 메시지 표시 확인
```

#### 6. 반응형 테스트
```
1. 브라우저 창 크기 조절
2. Mobile: 1열 레이아웃 확인
3. Desktop: 3열 레이아웃 확인
4. 문서 선택기 토글 동작 확인
5. 스크롤 동작 확인 (히스토리, 인용 출처)
```

## 🎉 결론

Story 3가 성공적으로 완료되었습니다. 모든 Acceptance Criteria를 만족하며, 완전한 질의응답 시스템을 구축했습니다.

**주요 성과**:
- ✅ 5개 파일, ~720 lines 코드 생성
- ✅ 완전한 질의응답 플로우
- ✅ 마크다운 렌더링 (react-markdown + remarkGfm)
- ✅ 인용 출처 표시 (신뢰도, 관련도)
- ✅ 질의 히스토리 (최대 50개)
- ✅ 문서 검색 & 선택 (개별/전체)
- ✅ 상태별 UI (pending/processing/completed/failed)
- ✅ 반응형 레이아웃

다음 Story 4에서는 지식 그래프 시각화를 구현합니다.

---

**Story Points**: 5 / 5
**Completion**: 100%
**Status**: ✅ READY FOR STORY 4
