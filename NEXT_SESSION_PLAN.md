# Next Session Plan: Frontend Admin Dashboard

**Priority**: HIGH
**Estimated Time**: 2-3 hours
**Goal**: Complete metadata curation dashboard, then deploy to production

---

## 🎯 Session Objective

Build the **Admin Metadata Curation Dashboard** to complete Story 1.0 (Human-in-the-Loop system).

**Why This Matters**:
- Backend API is 100% ready
- Without UI, admins can't curate policies
- Completes the entire data collection workflow
- Ready for production deployment

---

## 📋 Task Breakdown

### Phase 1: Core Dashboard (60 min) ⭐

**Page**: `/admin/metadata`

**Components to Build**:

1. **Policy List Table** (30 min)
```typescript
// frontend/src/app/(authenticated)/admin/metadata/page.tsx

Features:
- Display policies from GET /api/v1/metadata/policies
- Columns: Status, Insurer, Policy Name, Publication Date, Actions
- Sortable columns
- Color-coded status badges
- Checkbox for bulk selection
- Pagination controls (50 items/page)
```

2. **Filter Panel** (15 min)
```typescript
// components/metadata/FilterPanel.tsx

Filters:
- Status dropdown (DISCOVERED, QUEUED, COMPLETED, etc.)
- Insurer text input (partial match)
- Category dropdown
- Date range picker
- Search input (policy name, file name)
- [Apply Filters] button
```

3. **Queue Button** (15 min)
```typescript
// components/metadata/QueueButton.tsx

Features:
- Bulk action for selected policies
- Calls POST /api/v1/metadata/queue
- Shows success/error toast
- Refreshes table after queuing
- Disabled if no selection or invalid status
```

---

### Phase 2: Statistics Dashboard (30 min)

**Page**: `/admin/metadata/stats`

**Components**:

1. **Stats Cards** (15 min)
```typescript
// components/metadata/StatsCards.tsx

Display:
- Total policies discovered
- By status (pie chart or badges)
- By insurer (bar chart)
- Recent discoveries (last 7 days)
```

2. **Charts** (15 min) - Optional
```typescript
// Use recharts or chart.js

Charts:
- Status distribution (pie)
- Policies by insurer (bar)
- Discovery timeline (line)
```

---

### Phase 3: Polish & Testing (30 min)

**Tasks**:

1. **API Integration** (10 min)
```typescript
// frontend/src/lib/api/metadata.ts

export async function fetchPolicies(params) {
  const query = new URLSearchParams(params);
  const res = await fetch(`${API_URL}/api/v1/metadata/policies?${query}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.json();
}

export async function queuePolicies(policyIds: string[]) {
  return fetch(`${API_URL}/api/v1/metadata/queue`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ policy_ids: policyIds }),
  });
}
```

2. **Error Handling** (10 min)
- Loading states
- Error messages
- Empty states ("No policies found")

3. **Manual Testing** (10 min)
- Test with backend dev seed data
- Test filtering
- Test queueing
- Test pagination

---

## 🛠 Quick Start Commands

### Backend (Terminal 1)

```bash
cd backend
source venv/bin/activate

# Seed test data
python -c "
import asyncio
from app.api.v1.endpoints.metadata import _policy_metadata_store
from app.models.policy_metadata import PolicyMetadata, PolicyMetadataStatus, PolicyCategory
from datetime import datetime

# Create sample policies
policies = [
    PolicyMetadata(
        insurer='삼성생명',
        category=PolicyCategory.CANCER,
        policy_name='종합암보험 2.0 약관',
        file_name='cancer_v2.pdf',
        publication_date=datetime(2025, 11, 1),
        download_url='https://www.samsunglife.com/download/cancer_v2.pdf',
        status=PolicyMetadataStatus.DISCOVERED,
    ),
    PolicyMetadata(
        insurer='한화생명',
        category=PolicyCategory.LIFE,
        policy_name='무배당 행복한 종신보험',
        publication_date=datetime(2025, 10, 15),
        download_url='https://www.hanwhalife.com/download/life.pdf',
        status=PolicyMetadataStatus.DISCOVERED,
    ),
    PolicyMetadata(
        insurer='KB손해보험',
        category=PolicyCategory.CARDIOVASCULAR,
        policy_name='심혈관질환보장보험',
        publication_date=datetime(2025, 9, 20),
        download_url='https://www.kbinsurance.com/download/cardio.pdf',
        status=PolicyMetadataStatus.COMPLETED,
    ),
]

for p in policies:
    _policy_metadata_store[p.id] = p

print(f'✅ Seeded {len(policies)} policies')
"

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

**Test URLs**:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000/docs
- Metadata API: http://localhost:8000/api/v1/metadata/policies

---

## 📂 Files to Create

```
frontend/src/
├── app/(authenticated)/admin/metadata/
│   ├── page.tsx                    # Main dashboard
│   └── stats/
│       └── page.tsx                # Statistics page
│
├── components/metadata/
│   ├── PolicyTable.tsx             # Core table component
│   ├── FilterPanel.tsx             # Filters sidebar
│   ├── QueueButton.tsx             # Bulk queue action
│   ├── StatusBadge.tsx             # Status indicator
│   └── StatsCards.tsx              # Statistics display
│
├── lib/api/
│   └── metadata.ts                 # API client functions
│
└── types/
    └── metadata.ts                 # TypeScript types
```

---

## 🎨 UI Design Reference

### Status Badge Colors

```typescript
const statusColors = {
  DISCOVERED: 'bg-blue-100 text-blue-800',
  QUEUED: 'bg-yellow-100 text-yellow-800',
  DOWNLOADING: 'bg-purple-100 text-purple-800',
  PROCESSING: 'bg-orange-100 text-orange-800',
  COMPLETED: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  IGNORED: 'bg-gray-100 text-gray-800',
};
```

### Table Structure

```
┌──────────────────────────────────────────────────────────────┐
│ [ Filter Panel ]                                  [Queue (2)] │
├──────────────────────────────────────────────────────────────┤
│ ☐  Status      Insurer       Policy Name        Date  Actions│
├──────────────────────────────────────────────────────────────┤
│ ☐  🔵 DISCOVERED  삼성생명  종합암보험 2.0     2025-11-01  ⋯ │
│ ☐  🟡 QUEUED      한화생명  무배당 종신보험     2025-10-15  ⋯ │
│ ☑  🟢 COMPLETED   KB손보    심혈관질환보험      2025-09-20  ⋯ │
├──────────────────────────────────────────────────────────────┤
│                        « 1 2 3 4 5 »             50/250       │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔗 API Integration Examples

### Fetch Policies

```typescript
const { data, error } = await fetchPolicies({
  status: 'DISCOVERED',
  insurer: '삼성',
  page: 1,
  page_size: 50,
});
```

### Queue Policies

```typescript
const selectedIds = ['uuid1', 'uuid2'];
const result = await queuePolicies(selectedIds);

if (result.queued_count > 0) {
  toast.success(`${result.queued_count} policies queued`);
  refreshTable();
}
```

---

## ✅ Acceptance Criteria

**Must Have**:
- [ ] Can view list of policies from API
- [ ] Can filter by status, insurer, category
- [ ] Can select policies with checkboxes
- [ ] Can queue selected policies (Admin only)
- [ ] Status updates in real-time after queueing
- [ ] Pagination works correctly
- [ ] Error states handled gracefully

**Nice to Have**:
- [ ] Statistics dashboard with charts
- [ ] Search functionality
- [ ] Bulk ignore action
- [ ] Export to CSV

---

## 🚀 After Frontend Completion

### Deployment Sequence

**1. Test Locally** (10 min)
```bash
# Backend with seed data
cd backend && uvicorn app.main:app

# Frontend
cd frontend && npm run dev

# Test full workflow:
# - View policies
# - Filter policies
# - Queue policies
# - Check status changes
```

**2. Deploy Backend** (10 min)
```bash
cd backend
./deploy.sh production
# Save the Cloud Run URL
```

**3. Update Frontend Config** (2 min)
```bash
cd frontend
# Edit .env.production
NEXT_PUBLIC_API_URL=https://insuregraph-backend-xxxxx.run.app
```

**4. Deploy Frontend** (5 min)
```bash
vercel --prod
# Save the Vercel URL
```

**5. Update Backend CORS** (2 min)
```bash
gcloud run services update insuregraph-backend \
  --region asia-northeast3 \
  --set-env-vars "CORS_ORIGINS=https://insuregraph-pro.vercel.app"
```

**6. Test Production** (5 min)
- Visit Vercel URL
- Login as admin
- Test metadata dashboard
- Queue a policy
- Verify in backend logs

**Total Deployment Time**: ~30 minutes

---

## 📚 Reference Documents

**Already Complete**:
- ✅ `STORY_1.0_PROGRESS.md` - Backend progress (90%)
- ✅ `DEPLOYMENT_GUIDE.md` - Full deployment guide
- ✅ Backend API ready at `/api/v1/metadata/*`

**API Documentation**:
- Swagger UI: http://localhost:8000/docs
- Endpoints: `/api/v1/metadata/policies`, `/queue`, `/stats`

---

## 🎯 Success Definition

**Session Complete When**:
1. ✅ Admin can view discovered policies
2. ✅ Admin can queue policies for learning
3. ✅ UI updates status after queueing
4. ✅ Production deployment successful
5. ✅ End-to-end workflow tested

**Deliverables**:
- Working admin dashboard (frontend)
- Deployed to Vercel + GCP
- Story 1.0 100% complete
- Ready for real insurer data collection

---

## 💡 Pro Tips

**Time-Savers**:
1. Use existing component libraries (shadcn/ui already installed)
2. Copy-paste from similar tables in the app
3. Use TanStack Table for advanced features
4. Start simple, add features incrementally

**Testing Strategy**:
1. Use backend `/dev/seed` endpoint for quick data
2. Test with different statuses
3. Test edge cases (empty list, errors)
4. Test on mobile viewport

**Common Issues**:
- CORS errors → Check backend CORS_ORIGINS
- Auth errors → Verify JWT token in localStorage
- Empty table → Check API response in Network tab

---

## 🎬 Start Here

```bash
# 1. Open this document
cat NEXT_SESSION_PLAN.md

# 2. Start backend with test data
cd backend
uvicorn app.main:app --reload

# 3. Start frontend
cd frontend
npm run dev

# 4. Create first component
mkdir -p src/app/\(authenticated\)/admin/metadata
touch src/app/\(authenticated\)/admin/metadata/page.tsx

# 5. Start coding! 🚀
```

---

**Estimated Total Time**: 2-3 hours
**Priority**: HIGH (blocks production deployment)
**Dependencies**: None (backend ready)
**Next Epic**: Frontend complete → Production deployment → Story 1.0 ✅

---

**Good luck! 🚀**

See you in the next session!
