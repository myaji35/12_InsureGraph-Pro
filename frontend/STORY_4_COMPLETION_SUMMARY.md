# Frontend Story 4 완료 요약

**Story**: 그래프 시각화
**Story Points**: 4
**Status**: ✅ COMPLETED
**완료일**: 2025-11-25

## 📋 Story 목표

지식 그래프 시각화 시스템 구현 (React Flow 기반 인터랙티브 그래프)

## ✅ 완료된 작업

### 1. 타입 정의 업데이트

#### Types 업데이트 (`src/types/index.ts`)
**추가된 타입**: ~40 lines

**그래프 타입**:
```typescript
export type NodeType = 'document' | 'entity' | 'concept' | 'clause'

export interface GraphNode {
  id: string
  type: NodeType
  label: string
  properties?: Record<string, any>
  metadata?: {
    document_id?: string
    document_name?: string
    entity_type?: string
    importance?: number
    [key: string]: any
  }
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label?: string
  type?: string
  weight?: number
  properties?: Record<string, any>
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata?: {
    total_nodes: number
    total_edges: number
    document_ids?: string[]
    [key: string]: any
  }
}
```

**기존 타입 업데이트**:
- Document 타입 완전 재정의 (15+ 필드)
- QueryRequest, QueryResponse 업데이트
- PaginatedResponse 필드 추가 (has_next, has_prev)

### 2. API 클라이언트 확장

#### API Client 업데이트 (`src/lib/api-client.ts`)
**추가된 메서드**: 2개

```typescript
// Graph APIs
async getGraph(params?: {
  document_ids?: string[]
  node_types?: string[]
  max_nodes?: number
}): Promise<GraphData>

async getNodeDetails(nodeId: string): Promise<GraphNode>
```

### 3. 상태 관리

#### Graph Store (`src/store/graph-store.ts`)
**라인 수**: 105 lines

**상태 필드**:
```typescript
interface GraphState {
  graphData: GraphData | null
  selectedNode: GraphNode | null
  filters: GraphFilters
  isLoading: boolean
  error: string | null
}
```

**필터 구조**:
```typescript
interface GraphFilters {
  documentIds: string[]
  nodeTypes: NodeType[]
  searchQuery: string
}
```

**구현된 액션**:
- `fetchGraph(params)` - 그래프 데이터 로드 (문서, 노드 타입, 최대 노드 수)
- `fetchNodeDetails(nodeId)` - 노드 상세 정보 로드
- `setSelectedNode(node)` - 선택된 노드 설정
- `updateFilters(filters)` - 필터 업데이트
- `clearFilters()` - 필터 초기화
- `clearError()` - 에러 초기화

### 4. 그래프 시각화

#### GraphVisualization 컴포넌트 (`src/components/GraphVisualization.tsx`)
**라인 수**: 180 lines

**주요 기능**:

1. **React Flow 통합**
   - 노드 & 엣지 렌더링
   - 배경 그리드
   - 줌/팬 컨트롤
   - 미니맵
   - fitView (자동 화면 맞춤)

2. **레이아웃 알고리즘**
   - Dagre 라이브러리 사용
   - Hierarchical layout (TB - Top to Bottom)
   - 노드 간격: 100px
   - 레벨 간격: 150px

3. **노드 스타일링**
   - 타입별 색상 구분
     - document: blue-500
     - entity: green-500
     - concept: amber-500
     - clause: violet-500
   - 선택된 노드: 진한 파란색 테두리 (3px)
   - 크기: 180x60px
   - 둥근 모서리 (8px)

4. **엣지 스타일링**
   - smoothstep 타입
   - 화살표 마커
   - weight 기반 선 두께
   - 라벨 표시 (작은 폰트)

5. **인터랙션**
   - 노드 클릭 이벤트
   - 드래그 가능
   - 줌 (0.1x ~ 2x)

6. **빈 상태**
   - 그래프 아이콘
   - 안내 메시지

**Dagre 레이아웃 로직**:
```typescript
const getLayoutedElements = (nodes, edges) => {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setGraph({ rankdir: 'TB', nodesep: 100, ranksep: 150 })

  // Add nodes and edges
  nodes.forEach(node => dagreGraph.setNode(node.id, { width: 180, height: 60 }))
  edges.forEach(edge => dagreGraph.setEdge(edge.source, edge.target))

  // Compute layout
  dagre.layout(dagreGraph)

  // Apply positions
  return layoutedNodes
}
```

### 5. 노드 상세 정보

#### NodeDetail 컴포넌트 (`src/components/NodeDetail.tsx`)
**라인 수**: 145 lines

**표시 정보**:

1. **헤더**
   - 노드 타입 아이콘 (색상 배경)
   - 노드 타입 라벨 (문서/엔티티/개념/조항)
   - 노드 이름
   - 닫기 버튼

2. **노드 ID**
   - 회색 배경 박스
   - mono 폰트

3. **메타데이터 섹션**
   - 문서명
   - 엔티티 유형
   - 중요도 (프로그레스 바)

4. **속성 섹션**
   - key-value 쌍
   - JSON 객체는 stringify

5. **추가 정보**
   - 기타 메타데이터

**노드 타입 아이콘**:
- document: DocumentTextIcon
- entity: TagIcon
- concept: CubeIcon
- clause: ScaleIcon

### 6. 그래프 컨트롤

#### GraphControls 컴포넌트 (`src/components/GraphControls.tsx`)
**라인 수**: 180 lines

**필터 옵션**:

1. **노드 검색**
   - 텍스트 입력
   - 실시간 필터링
   - MagnifyingGlassIcon

2. **노드 유형 선택**
   - 4가지 타입 체크박스
   - 개별 선택/해제
   - 선택된 개수 표시

3. **문서 선택**
   - 준비된 문서 목록
   - 체크박스 선택
   - 스크롤 가능 (max-h-60)
   - 문서명 + 보험사 표시

4. **적용 버튼**
   - "그래프 생성" 버튼
   - 문서 미선택 시 disabled

5. **접기/펼치기**
   - 토글 버튼
   - 공간 절약

**UI 패턴**:
- 체크박스 카드
- 선택 시 primary-50 배경
- 체크 아이콘 표시

### 7. 그래프 페이지

#### Graph 페이지 (`src/app/graph/page.tsx`)
**라인 수**: 200 lines

**레이아웃**: 3열 그리드 (lg:grid-cols-4)
- 왼쪽 (1/4): 컨트롤 + 통계
- 가운데 (2/4): 그래프 시각화
- 오른쪽 (1/4): 노드 상세

**주요 섹션**:

1. **컨트롤 영역**
   - GraphControls 컴포넌트
   - 통계 카드 (노드/엣지 수)
   - 필터링된 노드 수

2. **그래프 영역**
   - 에러 메시지 (상단)
   - 로딩 스피너
   - GraphVisualization (600px 높이)
   - 범례 (노드 타입별 색상)

3. **상세 정보 영역**
   - NodeDetail (노드 선택 시)
   - 빈 상태 (미선택 시)

**기능**:
- 필터 적용 → fetchGraph 호출
- 노드 클릭 → setSelectedNode
- 검색 쿼리 → 클라이언트 측 필터링

**Dynamic Import**:
```typescript
const GraphVisualization = dynamic(
  () => import('@/components/GraphVisualization'),
  { ssr: false }
)
```
- SSR 이슈 방지 (React Flow)

### 8. Sidebar 업데이트

#### Sidebar 내비게이션 추가
- "지식 그래프" 메뉴 항목
- CircleStackIcon
- /graph 라우트

### 9. 의존성 추가

#### package.json 업데이트
**추가된 패키지**:
```json
"reactflow": "^11.10.4"      // React Flow 라이브러리
"dagre": "^0.8.5"             // 그래프 레이아웃 알고리즘
"@types/dagre": "^0.7.52"     // Dagre TypeScript 타입
```

**React Flow 기능**:
- 노드 & 엣지 렌더링
- 인터랙티브 그래프 (드래그, 줌)
- 배경, 컨트롤, 미니맵
- 타입 안전성 (TypeScript)

**Dagre 기능**:
- Hierarchical 레이아웃
- Force-directed 알고리즘
- 자동 노드 배치

## 📊 통계

### 생성된 파일
- **상태 관리**: 1개 (graph-store.ts)
- **컴포넌트**: 3개 (GraphVisualization, NodeDetail, GraphControls)
- **페이지**: 1개 (graph/page.tsx)
- **타입 업데이트**: 1개 (types/index.ts)
- **API 업데이트**: 1개 (api-client.ts)
- **Sidebar 업데이트**: 1개

**총 파일 수**: 8개 (6 new, 2 updates)

### 코드 라인 수
```
Graph Store:             105 lines
GraphVisualization:      180 lines
NodeDetail:              145 lines
GraphControls:           180 lines
Graph Page:              200 lines
Type Updates:            ~50 lines
API Updates:             ~15 lines
--------------------------------------
Total:                   ~875 lines
```

### 구현된 기능
- ✅ React Flow 그래프 시각화
- ✅ Dagre 레이아웃 알고리즘
- ✅ 노드 타입별 색상 구분 (4가지)
- ✅ 노드 클릭 상세 정보
- ✅ 줌/팬 컨트롤
- ✅ 미니맵
- ✅ 문서 선택 필터
- ✅ 노드 타입 필터
- ✅ 노드 검색 (클라이언트 측)
- ✅ 통계 표시 (노드/엣지 수)
- ✅ 범례
- ✅ 에러 핸들링
- ✅ 로딩 상태
- ✅ 빈 상태
- ✅ 반응형 레이아웃

## 🎯 Acceptance Criteria 달성

### 1. 지식 그래프 시각화 ✅
- ✅ React Flow 사용
- ✅ 노드 & 엣지 렌더링
- ✅ 4가지 노드 타입 (문서, 엔티티, 개념, 조항)
- ✅ 색상 구분
- ✅ 레이블 표시

### 2. 레이아웃 알고리즘 ✅
- ✅ Dagre hierarchical layout
- ✅ 자동 노드 배치
- ✅ 적절한 간격 (100px/150px)

### 3. 인터랙티브 기능 ✅
- ✅ 줌 인/아웃 (0.1x ~ 2x)
- ✅ 팬 (드래그)
- ✅ 노드 클릭
- ✅ 미니맵
- ✅ fitView

### 4. 노드 상세 정보 ✅
- ✅ 노드 클릭 → 상세 패널
- ✅ 메타데이터 표시
- ✅ 속성 표시
- ✅ 중요도 시각화

### 5. 그래프 필터링 ✅
- ✅ 문서 선택
- ✅ 노드 타입 선택
- ✅ 노드 검색
- ✅ 실시간 필터링

### 6. 통계 & 범례 ✅
- ✅ 노드/엣지 개수
- ✅ 필터링된 노드 수
- ✅ 노드 타입 범례

## 🎨 UI/UX 개선사항

### 그래프 시각화
- 타입별 색상 구분 (직관적)
- 선택된 노드 강조 (진한 테두리)
- 화살표 마커 (방향성)
- weight 기반 선 두께
- 라벨 표시

### 인터랙션
- 부드러운 줌/팬
- 노드 클릭 즉시 반응
- 드래그 가능
- 미니맵으로 전체 구조 파악

### 레이아웃
- 3열 그리드 (컨트롤/그래프/상세)
- 반응형 (모바일: 1열)
- 600px 그래프 높이
- 스크롤 가능한 컨트롤

### 필터링
- 체크박스 카드 UI
- 선택 시 시각적 피드백
- 접기/펼치기 (공간 절약)
- 실시간 검색

### 상세 정보
- 타입별 아이콘 & 색상
- 구조화된 정보 표시
- 프로그레스 바 (중요도)
- 스크롤 가능

## 🔧 기술적 의사결정

### 1. React Flow 선택
**이유**:
- React 컴포넌트 기반
- 풍부한 인터랙티브 기능
- D3.js보다 간단한 API
- TypeScript 지원
- 커스터마이징 가능

**Trade-off**: D3.js보다 유연성은 적지만 구현 속도 빠름

### 2. Dagre 레이아웃 알고리즘
**이유**:
- Hierarchical layout 지원
- 자동 노드 배치
- React Flow와 호환
- 안정적인 결과

**대안**: force-directed (d3-force) - 더 동적이지만 복잡

### 3. 클라이언트 측 검색 필터링
**이유**:
- 실시간 응답
- 서버 부하 없음
- 그래프 데이터가 상대적으로 작음 (최대 200 노드)

### 4. Dynamic Import for SSR
**이유**:
- React Flow는 브라우저 전용
- SSR 시 window/document 에러 방지
- Next.js dynamic import 사용

```typescript
const GraphVisualization = dynamic(
  () => import('@/components/GraphVisualization'),
  { ssr: false }
)
```

### 5. 최대 노드 제한 (200개)
**이유**:
- 성능 최적화
- 시각적 복잡도 제한
- 충분한 정보 제공

## 📝 다음 단계 (Story 5 & 6)

**Story 5: 고객 포트폴리오 관리 (3 pts)**
- 고객 목록
- 고객 상세 정보
- 포트폴리오 분석
- 추천 보험 상품

**Story 6: 반응형 UI & 모바일 최적화 (3 pts)**
- 모바일 레이아웃 최적화
- 터치 제스처
- 성능 최적화
- 접근성 개선

## ✅ 테스트 가이드

### 수동 테스트 시나리오

#### 1. 그래프 생성 테스트
```
1. /graph 페이지 접근
2. 왼쪽 패널에서 문서 1-2개 선택
3. 노드 타입 선택 (선택사항)
4. "그래프 생성" 버튼 클릭
5. 로딩 스피너 확인
6. 그래프 렌더링 확인
7. 노드 & 엣지 표시 확인
```

#### 2. 인터랙션 테스트
```
1. 마우스 휠로 줌 인/아웃
2. 드래그로 팬
3. 노드 클릭하여 상세 정보 표시
4. 미니맵 클릭하여 네비게이션
5. Controls 버튼 사용 (+ - fit)
```

#### 3. 필터링 테스트
```
1. 검색창에 노드 이름 입력
2. 필터링된 그래프 확인
3. 노드 타입 체크박스 변경
4. "그래프 생성" 버튼 클릭
5. 다른 그래프 확인
6. 통계 업데이트 확인
```

#### 4. 노드 상세 테스트
```
1. 노드 클릭
2. 오른쪽 패널에 상세 정보 표시 확인
3. 메타데이터 확인
4. 속성 확인
5. 중요도 프로그레스 바 확인
6. 닫기 버튼 클릭
```

#### 5. 레이아웃 테스트
```
1. Dagre 레이아웃 확인 (Top-Bottom)
2. 노드 간격 적절한지 확인
3. 엣지 화살표 방향 확인
4. 라벨 가독성 확인
```

#### 6. 반응형 테스트
```
1. 브라우저 창 크기 조절
2. Mobile: 1열 레이아웃 확인
3. Tablet: 2열 레이아웃 확인
4. Desktop: 3열 레이아웃 확인
```

## 🎉 결론

Story 4가 성공적으로 완료되었습니다. 모든 Acceptance Criteria를 만족하며, 완전한 지식 그래프 시각화 시스템을 구축했습니다.

**주요 성과**:
- ✅ 8개 파일, ~875 lines 코드 생성
- ✅ React Flow 기반 인터랙티브 그래프
- ✅ Dagre hierarchical 레이아웃
- ✅ 4가지 노드 타입 (색상 구분)
- ✅ 노드 클릭 상세 정보
- ✅ 줌/팬/미니맵 컨트롤
- ✅ 문서/타입/검색 필터링
- ✅ 통계 & 범례
- ✅ 반응형 레이아웃

**기술 스택**:
- React Flow 11.10.4
- Dagre 0.8.5
- Zustand (상태 관리)
- TypeScript (타입 안전성)
- Tailwind CSS (스타일링)

---

**Story Points**: 4 / 4
**Completion**: 100%
**Status**: ✅ READY FOR STORY 5
**Total Progress**: 19/25 points (76%)
