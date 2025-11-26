# Epic 3: FP Workspace & Dashboard

**Epic ID**: EPIC-03
**Priority**: High (P1)
**Phase**: Phase 1 (MVP)
**Estimated Duration**: 3-4 weeks
**Team**: Frontend Engineers, UX Designer

---

## Executive Summary

Build the FP (Financial Planner) workspace - the primary user interface where insurance agents interact with the GraphRAG engine, manage customers, and generate insights. This is the "face" of the product that users interact with daily.

### Business Value

- **User Adoption**: Intuitive UI drives user retention and satisfaction
- **Competitive Advantage**: Fast, mobile-optimized interface for field work
- **Revenue**: Polished UX converts freemium to paid tiers
- **Viral Growth**: Impressive graph visualizations drive word-of-mouth

### Success Criteria

- ✅ Query response in < 500ms (perceived performance)
- ✅ Graph visualization loads in < 2s with smooth interactions
- ✅ Mobile responsive (works on tablets/phones in the field)
- ✅ > 90% user satisfaction (SUS score > 80)
- ✅ Zero accessibility violations (WCAG 2.1 AA)

---

## User Stories

### Story 3.1: Authentication & User Management

**Story ID**: STORY-3.1
**Priority**: Critical (P0)
**Story Points**: 8

#### User Story

```
As an FP user,
I want to securely log in and manage my profile,
So that I can access the platform and my customer data.
```

#### Acceptance Criteria

**Given** I am a new user with credentials from my GA manager
**When** I visit the login page
**Then** I should:
- See a professional login form
- Be able to log in with email + password
- Receive a JWT token upon successful login
- Be redirected to the dashboard

**Given** I am logged in
**When** I navigate the app
**Then** my session should:
- Persist across page refreshes (localStorage)
- Auto-refresh before token expiry (refresh token)
- Logout automatically after 24 hours of inactivity

**Given** I enter wrong credentials
**When** I try to log in
**Then** I should:
- See a clear error message
- Be rate-limited after 5 failed attempts
- Have option to reset password

#### Technical Tasks

- [ ] Design login/signup UI (Figma)
- [ ] Implement authentication pages (Next.js)
  - [ ] Login page (`/login`)
  - [ ] Password reset page (`/reset-password`)
  - [ ] Profile settings page (`/settings/profile`)
- [ ] Integrate with backend auth API
  - [ ] `POST /api/v1/auth/login`
  - [ ] `POST /api/v1/auth/refresh`
  - [ ] `POST /api/v1/auth/logout`
- [ ] Implement JWT token management
  - [ ] Store tokens in httpOnly cookies or localStorage
  - [ ] Auto-refresh logic (refresh 5 min before expiry)
  - [ ] Clear tokens on logout
- [ ] Implement protected routes (Next.js middleware)
- [ ] Add form validation (Zod schema)
- [ ] Write E2E tests (Playwright)
- [ ] Test on mobile devices

#### Dependencies

- Backend auth API ready (Epic 4)
- UI component library setup

#### Technical Notes

**Next.js Authentication Pattern**:

```typescript
// lib/auth.ts
import { jwtDecode } from 'jwt-decode';

export async function login(email: string, password: string) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error('Login failed');
  }

  const { access_token, refresh_token } = await response.json();

  // Store tokens
  localStorage.setItem('access_token', access_token);
  localStorage.setItem('refresh_token', refresh_token);

  return { access_token, refresh_token };
}

export function getAccessToken(): string | null {
  return localStorage.getItem('access_token');
}

export function isTokenExpired(token: string): boolean {
  const decoded = jwtDecode(token);
  return decoded.exp * 1000 < Date.now();
}

export async function refreshAccessToken(): Promise<string> {
  const refresh_token = localStorage.getItem('refresh_token');

  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token }),
  });

  const { access_token } = await response.json();
  localStorage.setItem('access_token', access_token);

  return access_token;
}

// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token');

  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Login/logout functional
- [ ] Token refresh working
- [ ] Protected routes enforced
- [ ] E2E tests passing
- [ ] Mobile responsive
- [ ] Deployed to dev environment

---

### Story 3.2: Query Interface with Natural Language Input

**Story ID**: STORY-3.2
**Priority**: Critical (P0)
**Story Points**: 8

#### User Story

```
As an FP user,
I want to ask policy questions in natural Korean language,
So that I can get instant answers without reading thick policy documents.
```

#### Acceptance Criteria

**Given** I am on the query page
**When** I type a question (e.g., "갑상선암 보장돼요?")
**Then** I should:
- See auto-suggestions as I type (recent queries, common questions)
- Be able to submit with Enter key
- See a loading indicator while processing
- Receive an answer within 3 seconds

**Given** the answer is ready
**When** it displays
**Then** I should see:
- A clear summary (2-3 sentences)
- Detailed breakdown by product/coverage
- Source clause references (clickable to view original text)
- Confidence indicator (high/medium/low)
- Option to expand reasoning path (graph visualization)

**Given** I'm on a mobile device
**When** I use the query interface
**Then** it should:
- Work smoothly with touch keyboard
- Auto-focus on input field
- Display results in mobile-optimized format

#### Technical Tasks

- [ ] Design query interface UI (Figma)
  - [ ] Search input with auto-complete
  - [ ] Answer display cards
  - [ ] Source references panel
  - [ ] Confidence badge
- [ ] Implement QueryInterface component (React)
  - [ ] Search input with debouncing
  - [ ] Auto-suggestions (fetch recent queries)
  - [ ] Submit handler (call query API)
- [ ] Implement AnswerDisplay component
  - [ ] Summary section
  - [ ] Details accordion
  - [ ] Source references list
  - [ ] Confidence badge with color coding
- [ ] Integrate with backend query API
  - [ ] `POST /api/v1/analysis/query`
  - [ ] Handle loading states
  - [ ] Handle errors gracefully
- [ ] Add query history sidebar
- [ ] Implement mobile responsive layout
- [ ] Write component tests (Jest + React Testing Library)
- [ ] E2E tests for query flow

#### Dependencies

- Story 2.6 completed (Query API ready)
- Story 3.1 completed (Authentication working)

#### Technical Notes

**QueryInterface Component**:

```typescript
// components/QueryInterface.tsx
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

export function QueryInterface() {
  const [query, setQuery] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ['policy-query', query],
    queryFn: () => fetchPolicyQuery(query),
    enabled: submitted && query.length > 5,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="query-interface">
      <form onSubmit={handleSubmit} className="search-form">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="약관 내용을 물어보세요 (예: 갑상선암 보장돼요?)"
          className="search-input"
          autoFocus
        />
        <button type="submit" disabled={query.length < 5}>
          질문하기
        </button>
      </form>

      {isLoading && <LoadingSpinner />}

      {error && (
        <ErrorMessage>
          질문 처리 중 오류가 발생했습니다. 다시 시도해주세요.
        </ErrorMessage>
      )}

      {data && <AnswerDisplay answer={data.answer} sources={data.sources} />}
    </div>
  );
}

// lib/api.ts
async function fetchPolicyQuery(query: string) {
  const token = getAccessToken();

  const response = await fetch('/api/v1/analysis/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error('Query failed');
  }

  return response.json();
}
```

**AnswerDisplay Component**:

```typescript
// components/AnswerDisplay.tsx
export function AnswerDisplay({ answer, sources }) {
  const [showDetails, setShowDetails] = useState(false);

  const confidenceBadge = {
    high: { color: 'green', text: '높은 신뢰도' },
    medium: { color: 'yellow', text: '중간 신뢰도' },
    low: { color: 'red', text: '낮은 신뢰도' },
  }[getConfidenceLevel(answer.confidence)];

  return (
    <div className="answer-card">
      <div className="answer-header">
        <h3>답변</h3>
        <Badge color={confidenceBadge.color}>{confidenceBadge.text}</Badge>
      </div>

      <div className="answer-summary">
        <p>{answer.summary}</p>
      </div>

      <button onClick={() => setShowDetails(!showDetails)}>
        {showDetails ? '간단히 보기' : '상세 보기'}
      </button>

      {showDetails && (
        <div className="answer-details">
          {answer.details.map((detail, idx) => (
            <DetailCard key={idx} detail={detail} />
          ))}
        </div>
      )}

      <div className="sources">
        <h4>근거 조항</h4>
        {sources.map((source) => (
          <SourceReference key={source.clause_id} source={source} />
        ))}
      </div>

      <div className="disclaimer">
        <InfoIcon />
        <span>{answer.disclaimer}</span>
      </div>
    </div>
  );
}
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Query interface functional
- [ ] Answer display polished
- [ ] Mobile responsive
- [ ] Component tests passing
- [ ] E2E tests passing
- [ ] Deployed to dev environment

---

### Story 3.3: Graph Visualization (Reasoning Path)

**Story ID**: STORY-3.3
**Priority**: High (P1)
**Story Points**: 13

#### User Story

```
As an FP user,
I want to see a visual graph of how the AI reached its answer,
So that I can understand and explain the reasoning to my customer.
```

#### Acceptance Criteria

**Given** I receive an answer to my query
**When** I click "Show Reasoning Path"
**Then** I should see:
- An interactive graph visualization
- Nodes: Product, Coverage, Disease, Condition, Clause
- Edges: COVERS, EXCLUDES, REQUIRES, with labels
- The traversal path highlighted (e.g., in blue)
- Ability to click nodes to see details

**Given** the graph is complex (many nodes)
**When** it renders
**Then** it should:
- Use smart layout algorithm (hierarchical or force-directed)
- Be zoomable and pannable
- Not lag (60 fps smooth interactions)
- Support fullscreen mode

**Given** I click on a Clause node
**When** the detail panel opens
**Then** I should see:
- Full clause text (원문)
- Article/paragraph number
- Page number (link to PDF if available)

#### Technical Tasks

- [ ] Evaluate graph visualization libraries
  - [ ] Cytoscape.js (recommended in architecture)
  - [ ] React Flow (alternative)
  - [ ] D3.js (most flexible, more work)
- [ ] Design graph visual style (colors, icons, layout)
- [ ] Implement GraphVisualization component
  - [ ] Convert API graph data to Cytoscape format
  - [ ] Render graph with layout algorithm
  - [ ] Implement zoom/pan controls
  - [ ] Highlight reasoning path
- [ ] Implement node click interactions
  - [ ] Show detail panel/modal
  - [ ] Load additional data on demand
- [ ] Optimize performance for large graphs
  - [ ] Lazy rendering (only render visible nodes)
  - [ ] Limit max nodes (100-200)
- [ ] Add fullscreen mode
- [ ] Write component tests
- [ ] Performance testing (graph with 100+ nodes)

#### Dependencies

- Story 2.6 completed (reasoning_path data available from API)
- Story 3.2 completed (answer display ready)

#### Technical Notes

**Cytoscape.js Integration**:

```typescript
// components/GraphVisualization.tsx
'use client';

import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';

cytoscape.use(dagre);

export function GraphVisualization({ reasoning_path }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Convert API data to Cytoscape format
    const elements = formatGraphData(reasoning_path);

    // Initialize Cytoscape
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#0ea5e9',
            label: 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            width: 60,
            height: 60,
          },
        },
        {
          selector: 'node[type="Product"]',
          style: {
            'background-color': '#8b5cf6',
          },
        },
        {
          selector: 'node[type="Coverage"]',
          style: {
            'background-color': '#0ea5e9',
          },
        },
        {
          selector: 'node[type="Disease"]',
          style: {
            'background-color': '#f59e0b',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 3,
            'line-color': '#cbd5e1',
            'target-arrow-color': '#cbd5e1',
            'target-arrow-shape': 'triangle',
            label: 'data(label)',
            'curve-style': 'bezier',
          },
        },
        {
          selector: '.highlighted',
          style: {
            'line-color': '#3b82f6',
            'target-arrow-color': '#3b82f6',
            width: 5,
          },
        },
      ],
      layout: {
        name: 'dagre',
        rankDir: 'LR',
        nodeSep: 50,
        rankSep: 100,
      },
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
    });

    // Highlight reasoning path
    highlightPath(cyRef.current, reasoning_path.highlighted_edges);

    // Node click handler
    cyRef.current.on('tap', 'node', (evt) => {
      const node = evt.target;
      onNodeClick(node.data());
    });

    // Cleanup
    return () => {
      cyRef.current?.destroy();
    };
  }, [reasoning_path]);

  return (
    <div className="graph-container">
      <div ref={containerRef} className="cytoscape-canvas" />
      <GraphControls cy={cyRef.current} />
    </div>
  );
}

function formatGraphData(reasoning_path) {
  const nodes = reasoning_path.nodes.map((node) => ({
    data: {
      id: node.id,
      label: node.name,
      type: node.type,
      ...node.properties,
    },
  }));

  const edges = reasoning_path.edges.map((edge) => ({
    data: {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.type,
    },
    classes: edge.is_highlighted ? 'highlighted' : '',
  }));

  return { nodes, edges };
}

function highlightPath(cy: cytoscape.Core, edge_ids: string[]) {
  edge_ids.forEach((id) => {
    cy.$(`#${id}`).addClass('highlighted');
  });
}
```

**GraphControls Component**:

```typescript
function GraphControls({ cy }) {
  const handleZoomIn = () => cy?.zoom(cy.zoom() * 1.2);
  const handleZoomOut = () => cy?.zoom(cy.zoom() * 0.8);
  const handleFit = () => cy?.fit();
  const handleFullscreen = () => {
    document.querySelector('.graph-container')?.requestFullscreen();
  };

  return (
    <div className="graph-controls">
      <button onClick={handleZoomIn}>+</button>
      <button onClick={handleZoomOut}>-</button>
      <button onClick={handleFit}>Fit</button>
      <button onClick={handleFullscreen}>Fullscreen</button>
    </div>
  );
}
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Graph visualization functional with Cytoscape.js
- [ ] Interactive (zoom, pan, node click)
- [ ] Reasoning path highlighted
- [ ] Performance smooth (60fps) with 100 nodes
- [ ] Fullscreen mode working
- [ ] Component tests passing
- [ ] Deployed to dev environment

---

### Story 3.4: Customer Portfolio Management

**Story ID**: STORY-3.4
**Priority**: High (P1)
**Story Points**: 13

#### User Story

```
As an FP user,
I want to manage my customer list and their policies,
So that I can track who I'm working with and analyze their coverage.
```

#### Acceptance Criteria

**Given** I am logged in
**When** I navigate to the Customers page
**Then** I should see:
- List of my customers (name, age, last contact date)
- Search/filter functionality
- Option to add new customer
- Option to view customer details

**Given** I click on a customer
**When** the detail page loads
**Then** I should see:
- Customer profile (age, gender, occupation)
- List of current policies
- Coverage summary (heatmap or chart)
- Gap analysis results
- History of queries related to this customer

**Given** I want to add a new customer
**When** I fill out the form
**Then** I should:
- Enter name, birth year, gender, phone (masked)
- Optionally add policies manually
- Save with customer consent checkbox
- See the new customer in my list

#### Technical Tasks

- [ ] Design customer management UI (Figma)
  - [ ] Customer list page with table
  - [ ] Customer detail page
  - [ ] Add/edit customer modal
- [ ] Implement CustomerList component
  - [ ] Fetch customers from API
  - [ ] Search and filter
  - [ ] Pagination
- [ ] Implement CustomerDetail component
  - [ ] Profile section
  - [ ] Policies table
  - [ ] Coverage heatmap (chart.js or recharts)
  - [ ] Gap analysis panel
- [ ] Implement AddCustomer form
  - [ ] Form validation (Zod)
  - [ ] PII handling (client-side masking)
  - [ ] Consent checkbox
- [ ] Integrate with backend APIs
  - [ ] `GET /api/v1/customers`
  - [ ] `POST /api/v1/customers`
  - [ ] `GET /api/v1/customers/:id`
  - [ ] `PUT /api/v1/customers/:id`
- [ ] Write component tests
- [ ] E2E tests for customer flow

#### Dependencies

- Backend customer API ready (Epic 4)
- Story 3.1 completed (authentication)

#### Technical Notes

**CustomerList Component**:

```typescript
// components/CustomerList.tsx
'use client';

import { useQuery } from '@tanstack/react-query';

export function CustomerList() {
  const { data: customers, isLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: fetchCustomers,
  });

  const [search, setSearch] = useState('');

  const filteredCustomers = customers?.filter((c) =>
    c.name.includes(search)
  );

  return (
    <div className="customer-list">
      <div className="header">
        <h2>고객 목록</h2>
        <input
          type="search"
          placeholder="고객 검색..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button onClick={() => setShowAddModal(true)}>+ 고객 추가</button>
      </div>

      {isLoading && <LoadingSpinner />}

      <table>
        <thead>
          <tr>
            <th>이름</th>
            <th>나이</th>
            <th>성별</th>
            <th>마지막 상담</th>
            <th>보유 보험</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {filteredCustomers?.map((customer) => (
            <tr key={customer.id}>
              <td>{customer.name}</td>
              <td>{calculateAge(customer.birth_year)}세</td>
              <td>{customer.gender === 'M' ? '남' : '여'}</td>
              <td>{formatDate(customer.last_contact)}</td>
              <td>{customer.policy_count}건</td>
              <td>
                <Link href={`/customers/${customer.id}`}>상세보기</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

**CustomerDetail Component**:

```typescript
// app/customers/[id]/page.tsx
export default function CustomerDetailPage({ params }) {
  const { data: customer } = useQuery({
    queryKey: ['customer', params.id],
    queryFn: () => fetchCustomer(params.id),
  });

  const { data: gapAnalysis } = useQuery({
    queryKey: ['gap-analysis', params.id],
    queryFn: () => fetchGapAnalysis(params.id),
  });

  return (
    <div className="customer-detail">
      <CustomerProfile customer={customer} />

      <section>
        <h3>보유 보험</h3>
        <PolicyTable policies={customer.policies} />
      </section>

      <section>
        <h3>보장 현황</h3>
        <CoverageHeatmap policies={customer.policies} />
      </section>

      <section>
        <h3>보장 공백 분석</h3>
        <GapAnalysisPanel analysis={gapAnalysis} />
      </section>

      <section>
        <h3>상담 기록</h3>
        <QueryHistory customerId={params.id} />
      </section>
    </div>
  );
}
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Customer list functional
- [ ] Customer detail page complete
- [ ] Add/edit customer working
- [ ] PII properly masked
- [ ] Component tests passing
- [ ] E2E tests passing
- [ ] Deployed to dev environment

---

### Story 3.5: Dashboard & Analytics

**Story ID**: STORY-3.5
**Priority**: Medium (P2)
**Story Points**: 8

#### User Story

```
As an FP user,
I want to see a dashboard with my key metrics,
So that I can track my performance and identify opportunities.
```

#### Acceptance Criteria

**Given** I log in
**When** I land on the dashboard
**Then** I should see:
- Total customers
- Active customers (contacted in last 30 days)
- Total queries this month
- Average query confidence score
- Top questions (most frequently asked)
- Recent activity feed

**Given** I'm a GA manager (not regular FP)
**When** I view the dashboard
**Then** I should additionally see:
- Team-wide metrics (all FPs in my GA)
- Top performing FPs
- Compliance risk alerts

#### Technical Tasks

- [ ] Design dashboard UI (Figma)
- [ ] Implement Dashboard page
  - [ ] Metric cards (KPIs)
  - [ ] Charts (recharts or chart.js)
  - [ ] Activity feed
- [ ] Integrate with analytics API
  - [ ] `GET /api/v1/analytics/overview`
  - [ ] `GET /api/v1/analytics/queries`
  - [ ] `GET /api/v1/analytics/team` (for GA managers)
- [ ] Implement real-time updates (optional: WebSocket or polling)
- [ ] Add date range selector
- [ ] Write component tests

#### Dependencies

- Backend analytics API ready
- Story 3.1 completed (authentication with role)

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Dashboard functional
- [ ] Charts rendering correctly
- [ ] Mobile responsive
- [ ] Component tests passing
- [ ] Deployed to dev environment

---

### Story 3.6: Mobile Responsiveness & PWA

**Story ID**: STORY-3.6
**Priority**: High (P1)
**Story Points**: 8

#### User Story

```
As an FP user,
I want to use the app on my phone or tablet in the field,
So that I can assist customers during face-to-face meetings.
```

#### Acceptance Criteria

**Given** I access the app on a mobile device
**When** I use any feature
**Then** it should:
- Display correctly on screens 360px wide (iPhone SE)
- Be touch-friendly (buttons > 44px)
- Load quickly on 4G networks
- Work offline for basic features (PWA)

**Given** I'm on a slow network
**When** I submit a query
**Then** I should:
- See optimistic UI updates
- Get notified when the request completes
- Have the option to retry if it fails

**Given** I install the app as PWA
**When** I open it
**Then** it should:
- Launch in fullscreen (no browser chrome)
- Show splash screen
- Cache static assets for offline use

#### Technical Tasks

- [ ] Audit all pages for mobile responsiveness
- [ ] Implement responsive layouts (Tailwind CSS)
  - [ ] Mobile-first approach
  - [ ] Breakpoints: sm (640px), md (768px), lg (1024px)
- [ ] Optimize touch targets (min 44x44px)
- [ ] Implement PWA features
  - [ ] Service worker for caching
  - [ ] Web app manifest (icons, splash screen)
  - [ ] Offline fallback page
- [ ] Optimize bundle size
  - [ ] Code splitting
  - [ ] Lazy loading routes
  - [ ] Image optimization (next/image)
- [ ] Test on real devices
  - [ ] iPhone (Safari)
  - [ ] Android (Chrome)
  - [ ] iPad
- [ ] Lighthouse audit (score > 90)

#### Dependencies

- All previous frontend stories completed

#### Technical Notes

**PWA Configuration**:

```typescript
// next.config.js
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
});

module.exports = withPWA({
  // ... other config
});

// public/manifest.json
{
  "name": "InsureGraph Pro",
  "short_name": "InsureGraph",
  "description": "보험 약관 분석 플랫폼",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#0ea5e9",
  "icons": [
    {
      "src": "/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Responsive Layout Example**:

```typescript
// Tailwind CSS utility classes
<div className="
  px-4 py-6                    /* Mobile: padding */
  md:px-8 md:py-10             /* Tablet: larger padding */
  lg:px-12 lg:py-12            /* Desktop: even larger */
  max-w-7xl mx-auto            /* Centered with max width */
">
  <div className="
    grid
    grid-cols-1                 /* Mobile: 1 column */
    md:grid-cols-2              /* Tablet: 2 columns */
    lg:grid-cols-3              /* Desktop: 3 columns */
    gap-4 md:gap-6 lg:gap-8
  ">
    {/* Content cards */}
  </div>
</div>
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] All pages responsive (tested on 3+ devices)
- [ ] PWA installable on iOS and Android
- [ ] Lighthouse score > 90 (Performance, Accessibility, Best Practices, SEO)
- [ ] Bundle size optimized (< 500KB gzipped)
- [ ] Offline mode functional
- [ ] Deployed to production

---

### Story 3.7: Error Handling & User Feedback

**Story ID**: STORY-3.7
**Priority**: High (P1)
**Story Points**: 5

#### User Story

```
As an FP user,
I want clear feedback when something goes wrong,
So that I know what happened and what to do next.
```

#### Acceptance Criteria

**Given** a network error occurs
**When** I'm using the app
**Then** I should:
- See a toast notification with error message
- Have option to retry the action
- Not lose my work (form data preserved)

**Given** I submit invalid data
**When** form validation fails
**Then** I should:
- See inline validation errors (red text below field)
- Have errors cleared as I correct them
- Be prevented from submitting until valid

**Given** an unexpected error occurs
**When** the app crashes
**Then** I should:
- See a friendly error boundary page
- Have option to report the issue
- Be able to return to home page

#### Technical Tasks

- [ ] Implement global error handling
  - [ ] React Error Boundaries
  - [ ] API error interceptor (axios/fetch)
- [ ] Implement toast notification system
  - [ ] Success, error, warning, info variants
  - [ ] Auto-dismiss after 5 seconds
  - [ ] Stackable (multiple toasts)
- [ ] Implement form validation feedback
  - [ ] Inline error messages
  - [ ] Field-level validation (Zod + react-hook-form)
- [ ] Implement error reporting
  - [ ] Capture errors to Sentry or similar
  - [ ] Include user context (anonymized)
- [ ] Write error scenarios tests
- [ ] Test error states in Storybook

#### Dependencies

- None (can be done in parallel)

#### Technical Notes

**Error Boundary**:

```typescript
// components/ErrorBoundary.tsx
'use client';

import { Component, ReactNode } from 'react';

export class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log to error reporting service
    console.error('Error caught by boundary:', error, errorInfo);
    // Send to Sentry, etc.
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-page">
          <h2>앗, 문제가 발생했습니다</h2>
          <p>죄송합니다. 예상치 못한 오류가 발생했습니다.</p>
          <button onClick={() => window.location.href = '/'}>
            홈으로 돌아가기
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Toast Notification System**:

```typescript
// components/Toast.tsx
import { createContext, useContext, useState } from 'react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="toast-container">
        {toasts.map((toast) => (
          <Toast key={toast.id} {...toast} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}

// Usage
function SomeComponent() {
  const { addToast } = useToast();

  const handleAction = async () => {
    try {
      await someApiCall();
      addToast('저장되었습니다', 'success');
    } catch (error) {
      addToast('저장 실패: ' + error.message, 'error');
    }
  };
}
```

#### Definition of Done

- [ ] Code merged to main branch
- [ ] Error boundaries working
- [ ] Toast notifications functional
- [ ] Form validation with clear feedback
- [ ] Error reporting integrated
- [ ] Error states tested
- [ ] Deployed to dev environment

---

## Epic Dependencies

```
Story 3.1 (Authentication)
    ↓
Story 3.2 (Query Interface) ──┐
    ↓                          │
Story 3.3 (Graph Viz)          │
                               │
Story 3.4 (Customers) ─────────┤
    ↓                          │
Story 3.5 (Dashboard)          │
                               │
Story 3.6 (Mobile/PWA) ◄───────┘
Story 3.7 (Error Handling) ◄───┘
```

---

## Technical Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Graph viz performance issues** | High | Medium | Limit nodes to 100; lazy rendering; optimize Cytoscape config |
| **Poor mobile UX** | High | Low | Mobile-first design; extensive device testing |
| **Slow API responses** | Medium | Medium | Optimistic UI; loading skeletons; caching |
| **Browser compatibility** | Medium | Low | Test on Safari, Chrome, Firefox; polyfills for older browsers |
| **PWA adoption low** | Low | High | Educate users; show install prompt; offer incentives |

---

## Sprint Recommendations

### Sprint 9 (2 weeks)
- Story 3.1 (Authentication)
- Story 3.2 (Query Interface)

### Sprint 10 (2 weeks)
- Story 3.3 (Graph Visualization)
- Story 3.7 (Error Handling)

### Sprint 11 (2 weeks)
- Story 3.4 (Customer Management)
- Story 3.5 (Dashboard)

### Sprint 12 (1-2 weeks)
- Story 3.6 (Mobile/PWA)
- Final polish & bug fixes

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Page Load Time** | < 2s (FCP) | Lighthouse, Real User Monitoring |
| **Mobile Usability** | 100% Lighthouse score | Automated testing |
| **User Satisfaction** | SUS > 80 | User surveys |
| **PWA Install Rate** | > 30% | Analytics |
| **Bounce Rate** | < 20% | Analytics |

---

**Epic Owner**: Frontend Tech Lead
**Stakeholders**: Product Manager, UX Designer, FP Beta Users
**Next Review**: After Sprint 10 completion
