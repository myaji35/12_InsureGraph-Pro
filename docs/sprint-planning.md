# Sprint Planning Guide: InsureGraph Pro

**Project**: InsureGraph Pro
**Methodology**: BMAD (Breakthrough Method of Agile AI-Driven Development)
**Phase**: Phase 1 (MVP)
**Total Duration**: 16 Sprints (32 weeks / ~8 months)
**Sprint Length**: 2 weeks
**Version**: 1.0
**Date**: 2025-11-25

---

## 📋 Executive Summary

This document provides a comprehensive sprint planning guide for the InsureGraph Pro MVP development. The project is structured into 4 major epics spanning 16 sprints (8 months).

### Success Criteria for MVP Launch

- ✅ 50+ insurance policies ingested and validated
- ✅ Query engine achieving > 85% answer accuracy
- ✅ FP workspace fully functional on mobile and desktop
- ✅ Compliance requirements met (Financial Sandbox approved)
- ✅ 100 beta testers onboarded (FPs from partner GAs)
- ✅ Zero critical security vulnerabilities
- ✅ System performance meets targets (< 500ms simple queries)

---

## 🏗️ Project Overview

### Epic Breakdown

| Epic | Duration | Story Points | Priority | Dependencies |
|------|----------|--------------|----------|--------------|
| **Epic 1: Data Ingestion & Knowledge Graph** | 8 weeks (4 sprints) | 78 | P0 | None |
| **Epic 2: GraphRAG Query Engine** | 8 weeks (4 sprints) | 73 | P0 | Epic 1 |
| **Epic 3: FP Workspace & Dashboard** | 8 weeks (4 sprints) | 62 | P1 | Epic 2 |
| **Epic 4: Compliance & Security** | 7 weeks (3.5 sprints) | 47 | P0 | Epic 1-3 |
| **Integration & Testing** | 1 week (0.5 sprint) | - | P0 | All Epics |

**Total**: 260 story points, 16 sprints

### Team Composition

| Role | Count | Responsibilities |
|------|-------|------------------|
| **Backend Engineers** | 2 | FastAPI, LangGraph, Neo4j, PostgreSQL |
| **ML Engineers** | 1 | LLM integration, GraphRAG, embeddings |
| **Frontend Engineers** | 2 | Next.js, React, Cytoscape.js, PWA |
| **DevOps Engineer** | 1 | AWS infrastructure, CI/CD, monitoring |
| **QA Engineer** | 1 | Testing, validation, quality assurance |
| **Product Manager** | 1 | Backlog, stakeholder communication |
| **UX Designer** | 0.5 | UI/UX design (part-time consultant) |
| **Security Engineer** | 0.5 | Security review, compliance (part-time) |

**Total**: 9 FTEs

### Velocity Assumptions

- **Team Velocity**: 16-18 story points per sprint (for 9-person team)
- **Buffer**: 20% for bugs, tech debt, unplanned work
- **Sprint Duration**: 2 weeks (10 working days)

---

## 📅 Sprint Schedule

### Phase 1: Foundation (Sprints 1-4) - Epic 1

**Goal**: Build the core data ingestion pipeline and knowledge graph.

---

#### Sprint 1: Ingestion Pipeline Foundation

**Duration**: Week 1-2
**Sprint Goal**: Setup project foundation and implement PDF upload + OCR.
**Key Deliverables**:
- Project repository setup (monorepo with backend/frontend)
- CI/CD pipeline (GitHub Actions)
- PDF upload API functional
- Upstage Document Parse integration working

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 1.1 PDF Upload & Job Management | 5 | Backend Eng 1 | ✅ |
| 1.2 OCR & Document Preprocessing | 8 | Backend Eng 2 | ✅ |
| Infrastructure setup (AWS, Neo4j, PostgreSQL) | 5 | DevOps | ✅ |

**Total**: 18 points

**Sprint Activities**:
- Day 1: Sprint planning, story breakdown
- Day 2-8: Development
- Day 9: Code review, testing
- Day 10: Sprint review, retrospective

**Success Metrics**:
- [ ] PDF upload successful (10 test files)
- [ ] OCR accuracy > 95% on test set
- [ ] Job status tracking functional
- [ ] Infrastructure provisioned (dev environment)

---

#### Sprint 2: Legal Structure Parsing

**Duration**: Week 3-4
**Sprint Goal**: Parse Korean legal document structure with high accuracy.
**Key Deliverables**:
- Hierarchical clause tree from OCR text
- 90%+ parsing accuracy on 10 sample policies

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 1.3 Legal Structure Parsing (Rule-based) | 13 | Backend Eng 1 | 🚧 |
| 1.4 Critical Data Extraction (Rule-based) | 5 | Backend Eng 2 | 🚧 |

**Total**: 18 points

**Risks**:
- ⚠️ Complex layouts may break parsing logic
- ⚠️ Korean legal syntax edge cases

**Mitigation**:
- Extensive unit tests with diverse samples
- Graceful degradation for unparseable sections
- Flag for manual review if confidence < 80%

**Success Metrics**:
- [ ] 90%+ articles correctly identified
- [ ] Hierarchical structure validated
- [ ] 100% accuracy on critical data (amounts, periods)

---

#### Sprint 3: LLM Relationship Extraction

**Duration**: Week 5-6
**Sprint Goal**: Extract relationships using LLM with validation.
**Key Deliverables**:
- Upstage Solar Pro + GPT-4o cascade working
- Relation extraction with > 85% accuracy

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 1.5 LLM Relationship Extraction with Validation | 13 | ML Engineer | 🔜 |
| 1.6 Entity Linking & Ontology Mapping | 5 | ML Engineer | 🔜 |

**Total**: 18 points

**Challenges**:
- LLM prompt engineering for accuracy
- Cost optimization (Solar Pro vs. GPT-4o)
- Validation logic complexity

**Success Metrics**:
- [ ] Relation extraction accuracy > 85%
- [ ] LLM cost per policy < $2
- [ ] Validation catches 100% of test errors

---

#### Sprint 4: Graph Construction & Pipeline Orchestration

**Duration**: Week 7-8
**Sprint Goal**: Complete end-to-end ingestion pipeline with LangGraph.
**Key Deliverables**:
- Neo4j knowledge graph fully populated
- Pipeline processes 10 policies successfully
- Vector embeddings generated

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 1.7 Neo4j Graph Construction | 13 | Backend Eng 1 | 🔜 |
| 1.8 Ingestion Pipeline Orchestration (LangGraph) | 8 | Backend Eng 2 | 🔜 |
| 1.9 Validation & Quality Assurance | 5 | QA Engineer | 🔜 |

**Total**: 26 points (high-load sprint)

**Critical Path**:
- This sprint is a major milestone - full pipeline must work end-to-end
- Recommend 3-day buffer for integration issues

**Success Metrics**:
- [ ] 10 policies ingested successfully
- [ ] Knowledge graph queryable
- [ ] Ingestion speed < 5 min per policy
- [ ] Validation passes on all test policies

**Sprint Review Demo**:
- Live demo: Upload PDF → Show knowledge graph in Neo4j Browser
- Showcase graph visualization (nodes, relationships)

---

### Phase 2: Intelligence (Sprints 5-8) - Epic 2

**Goal**: Build the GraphRAG query engine for natural language Q&A.

---

#### Sprint 5: Hybrid Retrieval Foundation

**Duration**: Week 9-10
**Sprint Goal**: Implement query classification and vector search.
**Key Deliverables**:
- Query classifier functional
- Vector search returning relevant clauses

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 2.1 Query Classification & Routing | 5 | Backend Eng 2 | 🔜 |
| 2.2 Vector Search Implementation | 8 | ML Engineer | 🔜 |
| Setup monitoring dashboards (Prometheus, Grafana) | 3 | DevOps | 🔜 |

**Total**: 16 points

**Success Metrics**:
- [ ] Query classification accuracy > 90%
- [ ] Vector search precision@10 > 0.7
- [ ] Search latency < 100ms (p95)

---

#### Sprint 6: Graph Traversal & Multi-hop Reasoning

**Duration**: Week 11-12
**Sprint Goal**: Enable complex multi-hop queries via graph traversal.
**Key Deliverables**:
- Graph traversal functional for common patterns
- Path confidence scoring working

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 2.3 Graph Traversal for Multi-hop Reasoning | 13 | Backend Eng 1 | 🔜 |
| 2.4 LLM Reasoning Layer (start) | 5 | ML Engineer | 🔜 |

**Total**: 18 points

**Challenges**:
- Cypher query optimization for performance
- Handling conflicting graph paths

**Success Metrics**:
- [ ] Multi-hop queries succeed (3+ hops)
- [ ] Traversal latency < 500ms
- [ ] Conflict detection working

---

#### Sprint 7: LLM Reasoning & Validation

**Duration**: Week 13-14
**Sprint Goal**: Complete LLM reasoning layer with 4-stage validation.
**Key Deliverables**:
- Natural language answers with high confidence
- Validation pipeline functional

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 2.4 LLM Reasoning Layer (complete) | 8 | ML Engineer | 🔜 |
| 2.5 Answer Validation (4-Stage Defense) | 8 | Backend Eng 2 | 🔜 |
| 2.6 Query API Implementation | 5 | Backend Eng 1 | 🔜 |

**Total**: 21 points (high-load sprint)

**Critical Milestone**:
- End-to-end query flow working (user question → validated answer)

**Success Metrics**:
- [ ] Answer accuracy > 85% on test set
- [ ] Confidence scoring calibrated (AUC > 0.85)
- [ ] Validation rejects 100% of test violations
- [ ] API response time < 3s (complex queries)

**Sprint Review Demo**:
- Live demo: Ask "갑상선암 보장돼요?" → Show full answer with sources
- Showcase reasoning path visualization

---

#### Sprint 8: Advanced Features (Gap Analysis & Comparison)

**Duration**: Week 15-16
**Sprint Goal**: Implement gap analysis and product comparison features.
**Key Deliverables**:
- Gap analysis recommending products
- Product comparison side-by-side

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 2.7 Gap Analysis Feature | 13 | Backend Eng 1 + ML | 🔜 |
| 2.8 Product Comparison Feature | 8 | Backend Eng 2 | 🔜 |

**Total**: 21 points

**Success Metrics**:
- [ ] Gap analysis identifies 90%+ of true gaps
- [ ] Product comparison accurate
- [ ] Recommendations actionable

---

### Phase 3: User Experience (Sprints 9-12) - Epic 3

**Goal**: Build the FP workspace frontend with mobile support.

---

#### Sprint 9: Authentication & Query Interface

**Duration**: Week 17-18
**Sprint Goal**: FPs can log in and ask questions via web interface.
**Key Deliverables**:
- Login/logout functional
- Query interface with answer display

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 3.1 Authentication & User Management | 8 | Frontend Eng 1 | 🔜 |
| 3.2 Query Interface with NL Input | 8 | Frontend Eng 2 | 🔜 |

**Total**: 16 points

**Design Review**:
- UX designer review on Day 3
- Usability testing with 2-3 FP beta users

**Success Metrics**:
- [ ] Login functional on desktop + mobile
- [ ] Query submission smooth (< 100ms perceived latency)
- [ ] Answer display clear and readable

---

#### Sprint 10: Graph Visualization & Error Handling

**Duration**: Week 19-20
**Sprint Goal**: Visual reasoning path and comprehensive error handling.
**Key Deliverables**:
- Interactive graph visualization (Cytoscape.js)
- Toast notifications and error boundaries

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 3.3 Graph Visualization (Reasoning Path) | 13 | Frontend Eng 1 | 🔜 |
| 3.7 Error Handling & User Feedback | 5 | Frontend Eng 2 | 🔜 |

**Total**: 18 points

**Challenges**:
- Cytoscape.js performance with large graphs
- Mobile touch interactions

**Success Metrics**:
- [ ] Graph renders smoothly (60fps) with 100 nodes
- [ ] All error states handled gracefully
- [ ] Mobile usability score > 90 (Lighthouse)

---

#### Sprint 11: Customer Management & Dashboard

**Duration**: Week 21-22
**Sprint Goal**: FPs can manage customers and view analytics dashboard.
**Key Deliverables**:
- Customer list and detail pages
- Analytics dashboard

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 3.4 Customer Portfolio Management | 13 | Frontend Eng 1 | 🔜 |
| 3.5 Dashboard & Analytics | 8 | Frontend Eng 2 | 🔜 |

**Total**: 21 points

**Success Metrics**:
- [ ] Customer CRUD operations working
- [ ] Dashboard loads < 2s
- [ ] Charts rendering correctly

---

#### Sprint 12: Mobile Optimization & PWA

**Duration**: Week 23-24
**Sprint Goal**: Mobile-first optimization and PWA features.
**Key Deliverables**:
- Fully responsive on all devices
- PWA installable

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 3.6 Mobile Responsiveness & PWA | 8 | Frontend Eng 1 + 2 | 🔜 |
| Performance optimization (code splitting, caching) | 5 | Frontend Eng 1 | 🔜 |
| UI polish and bug fixes | 5 | Frontend Eng 2 | 🔜 |

**Total**: 18 points

**Testing Focus**:
- Extensive device testing (iOS, Android, tablets)
- Lighthouse audit (target: > 90 all metrics)
- Beta user feedback session

**Success Metrics**:
- [ ] Lighthouse scores: Performance > 90, Accessibility > 95
- [ ] PWA installable on iOS and Android
- [ ] Offline mode functional

**Sprint Review Demo**:
- Live demo on mobile device (install PWA, use offline)
- Showcase responsive layouts

---

### Phase 4: Security & Compliance (Sprints 13-15) - Epic 4

**Goal**: Meet regulatory requirements and secure the platform.

---

#### Sprint 13: Authentication & PII Protection

**Duration**: Week 25-26
**Sprint Goal**: RBAC and PII encryption fully implemented.
**Key Deliverables**:
- Role-based access control working
- All PII encrypted at rest

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 4.1 Authentication & Authorization (RBAC) | 8 | Backend Eng 1 | 🔜 |
| 4.2 PII Encryption & Data Protection | 8 | Backend Eng 2 | 🔜 |
| AWS KMS setup | 3 | DevOps | 🔜 |

**Total**: 19 points

**Security Review**:
- Security engineer review on Day 8
- Penetration testing (preliminary)

**Success Metrics**:
- [ ] RBAC enforced on all endpoints
- [ ] Zero PII leaks in logs (audit complete)
- [ ] Encryption key rotation tested

---

#### Sprint 14: Audit Logging & Compliance

**Duration**: Week 27-28
**Sprint Goal**: Comprehensive audit logs and compliance validation.
**Key Deliverables**:
- Audit logs for all sensitive operations
- Sales script compliance validation

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 4.3 Comprehensive Audit Logging | 5 | Backend Eng 1 | 🔜 |
| 4.4 Sales Script Compliance Validation | 8 | Backend Eng 2 + ML | 🔜 |
| Compliance documentation | 3 | Product Manager | 🔜 |

**Total**: 16 points

**Success Metrics**:
- [ ] 100% audit trail coverage verified
- [ ] Script validator catches 95%+ violations
- [ ] Compliance checklist 100% complete

---

#### Sprint 15: Infrastructure Security & Testing

**Duration**: Week 29-30
**Sprint Goal**: Secure infrastructure and pass security testing.
**Key Deliverables**:
- VPC with network isolation
- WAF rules active
- Security testing passed

| Story | Points | Owner | Status |
|-------|--------|-------|--------|
| 4.5 Infrastructure Security & Network Isolation | 13 | DevOps + Security Eng | 🔜 |
| 4.6 Security Testing & Vulnerability Management | 5 | Security Engineer | 🔜 |

**Total**: 18 points

**Critical Milestone**:
- Pass external penetration testing
- Financial Sandbox compliance audit

**Success Metrics**:
- [ ] Zero critical vulnerabilities
- [ ] WAF blocking test attacks
- [ ] Compliance audit passed

---

### Phase 5: Integration & Launch (Sprint 16)

**Goal**: Final integration, testing, and MVP launch preparation.

---

#### Sprint 16: MVP Launch Preparation

**Duration**: Week 31-32
**Sprint Goal**: Final integration, beta testing, and launch.
**Key Deliverables**:
- All systems integrated and tested
- 50 policies ingested and validated
- 100 beta testers onboarded

| Task | Points | Owner | Status |
|------|--------|-------|--------|
| End-to-end integration testing | 8 | QA Engineer | 🔜 |
| Performance optimization & tuning | 5 | Backend + DevOps | 🔜 |
| Load testing (100 concurrent users) | 3 | DevOps | 🔜 |
| Beta user onboarding & training | 5 | Product Manager | 🔜 |
| Launch documentation & runbooks | 3 | All | 🔜 |
| Bug fixes & polish | 8 | All | 🔜 |

**Total**: 32 points (all-hands sprint)

**Testing Focus**:
- End-to-end user flows
- Performance under load
- Security stress testing
- Beta user feedback

**Launch Checklist**:
- [ ] 50+ policies ingested and validated
- [ ] Query accuracy > 85% on test set
- [ ] All critical bugs resolved
- [ ] Performance targets met
- [ ] Security audit passed
- [ ] Compliance documentation complete
- [ ] 100 beta testers onboarded
- [ ] Monitoring and alerting configured
- [ ] Incident response plan documented
- [ ] Production deployment successful

**Sprint Review: MVP Launch**
- Demo to stakeholders
- Celebrate team success!
- Plan for Phase 2 roadmap

---

## 🎯 Sprint Ceremonies

### Sprint Planning (Day 1)
**Duration**: 4 hours
**Attendees**: Full team
**Agenda**:
1. Review sprint goal and priorities
2. Refine stories from backlog (break down if needed)
3. Estimate story points (Planning Poker)
4. Commit to sprint backlog
5. Define success criteria

**Outputs**:
- Sprint backlog (stories committed)
- Sprint goal statement
- Task breakdown for first 2-3 days

---

### Daily Standup (Every day, 15 min)
**Time**: 10:00 AM (team timezone)
**Format**: Async (Slack) + Sync (video 2x/week)
**Questions**:
- What did I complete yesterday?
- What am I working on today?
- Any blockers?

**Slack Template**:
```
🗓️ Standup - [Date]

✅ Yesterday: [Completed tasks]
🚧 Today: [Planned tasks]
🚫 Blockers: [None / Description]
```

---

### Code Review (Continuous)
**Process**:
1. Create PR with description and screenshots
2. Request 1-2 reviewers
3. Address feedback within 24 hours
4. Merge after approval (and CI passing)

**Review Checklist**:
- [ ] Code follows style guide
- [ ] Tests included and passing
- [ ] No security vulnerabilities (SAST pass)
- [ ] Documentation updated
- [ ] Performance acceptable

---

### Sprint Review (Day 10, 2 hours)
**Attendees**: Full team + stakeholders
**Agenda**:
1. Demo completed stories (live, not slides!)
2. Review sprint metrics (velocity, bugs, etc.)
3. Gather feedback from stakeholders
4. Update product backlog

**Demo Format**:
- Show user-facing features (not code)
- Real data (not mocks if possible)
- Interactive (let stakeholders try)

---

### Sprint Retrospective (Day 10, 1.5 hours)
**Attendees**: Full team (no stakeholders)
**Agenda**:
1. What went well?
2. What didn't go well?
3. Action items for improvement

**Format**: Mad, Sad, Glad (categorize feedback)
**Outputs**: 2-3 concrete action items for next sprint

---

## 📊 Metrics & Monitoring

### Sprint Health Metrics

| Metric | Target | Tracking |
|--------|--------|----------|
| **Velocity** | 16-18 points/sprint | Jira/Linear |
| **Sprint Commitment** | 90%+ stories completed | Sprint burndown |
| **Bug Escape Rate** | < 5% to production | Bug tracker |
| **Code Coverage** | > 80% | Jest, Pytest |
| **CI/CD Success Rate** | > 95% | GitHub Actions |
| **Deployment Frequency** | 2x per sprint minimum | Deployment logs |

### Product Quality Metrics

| Metric | Target | Tracking |
|--------|--------|----------|
| **Ingestion Accuracy** | > 95% | Manual validation |
| **Query Accuracy** | > 85% | Manual evaluation |
| **Query Latency (simple)** | < 500ms (p95) | Prometheus |
| **Query Latency (complex)** | < 3s (p95) | Prometheus |
| **System Uptime** | > 99.5% | Status page |
| **Error Rate** | < 1% | Sentry |

### User Engagement Metrics (Post-Launch)

| Metric | Target | Tracking |
|--------|--------|----------|
| **Daily Active Users (DAU)** | 70+ (70% of 100 beta users) | Analytics |
| **Queries per User** | 5+ per day | Analytics |
| **User Retention (Week 1)** | > 80% | Cohort analysis |
| **NPS Score** | > 40 | User surveys |

---

## 🚨 Risk Management

### Top Risks & Mitigation

| Risk | Impact | Probability | Mitigation | Owner |
|------|--------|-------------|------------|-------|
| **LLM hallucination** | Critical | High | 4-layer validation; expert review queue | ML Engineer |
| **OCR accuracy < 95%** | High | Medium | Use Upstage (best Korean OCR); manual review | Backend Eng |
| **Performance issues** | High | Medium | Load testing early; caching; optimization | DevOps |
| **Security breach** | Critical | Low | Pentest; SAST/DAST; security review | Security Eng |
| **Scope creep** | Medium | High | Strict backlog prioritization; "Phase 2" parking lot | Product Manager |
| **Team burnout** | High | Medium | Realistic sprint planning; 20% buffer; no overtime | All |
| **Integration issues** | High | Medium | Integration tests; early cross-team sync | Tech Leads |
| **Compliance failure** | Critical | Low | Regular self-audits; external review | Compliance Officer |

### Risk Review Cadence
- **Weekly**: Tech Lead + PM review top 5 risks
- **Every Sprint**: Team retrospective discusses risks
- **Monthly**: Stakeholder risk report

---

## 🤝 Team Communication

### Channels

| Channel | Purpose | Response Time |
|---------|---------|---------------|
| **Slack #insuregraph-dev** | Daily dev discussions | 2 hours |
| **Slack #insuregraph-alerts** | CI/CD, monitoring alerts | Immediate |
| **GitHub Issues** | Bug tracking, feature requests | 1 day |
| **Linear/Jira** | Sprint planning, backlog | Real-time |
| **Notion** | Documentation, decisions | Async |
| **Zoom** | Standups (2x/week), reviews | Scheduled |

### Communication Norms
- 🟢 **Working hours**: 9 AM - 6 PM (with flexibility)
- 🔴 **No-meeting blocks**: 2-5 PM (focus time)
- 📢 **Major decisions**: Documented in Notion
- 💬 **Quick questions**: Slack (public channels preferred)
- 📧 **Email**: External stakeholders only

---

## 📚 Definition of Done (DoD)

### Story DoD
- [ ] Code written and follows style guide
- [ ] Unit tests written (coverage > 80%)
- [ ] Integration tests written (if applicable)
- [ ] Code reviewed and approved (1+ reviewers)
- [ ] CI/CD pipeline passing (all checks green)
- [ ] Documentation updated (API docs, README, etc.)
- [ ] Deployed to dev environment
- [ ] Manual testing completed
- [ ] Acceptance criteria met (verified by PM/QA)
- [ ] No P0/P1 bugs

### Sprint DoD
- [ ] All committed stories completed (90%+ target)
- [ ] Sprint goal achieved
- [ ] Demo prepared and delivered
- [ ] Retrospective completed with action items
- [ ] Next sprint planned

### Epic DoD
- [ ] All stories in epic completed
- [ ] End-to-end testing passed
- [ ] Performance benchmarks met
- [ ] Security review passed (if applicable)
- [ ] Documentation complete
- [ ] Stakeholder sign-off

---

## 🎓 Onboarding for New Team Members

### Week 1: Setup & Context
- Day 1: Accounts, access, tools setup
- Day 2: Repository walkthrough, architecture review
- Day 3: Run project locally, read docs
- Day 4: Shadow team member, pair programming
- Day 5: Pick up first "good first issue" story (1-2 points)

### Week 2: First Contribution
- Take on small story (3-5 points)
- Participate in standup, code reviews
- Ask questions (no dumb questions!)

### Resources
- [Architecture Document](./docs/architecture.md)
- [PRD](./prd.md)
- [Epic Documents](./docs/epics/)
- [Development Guide](./README.md)
- [Code Style Guide](./docs/code-style.md)

---

## 🚀 Deployment Strategy

### Environments

| Environment | Purpose | Deployment | Access |
|-------------|---------|------------|--------|
| **Local** | Development | Manual | Developers |
| **Dev** | Integration testing | Auto (on merge to `develop`) | Team |
| **Staging** | Pre-production testing | Manual (tag release) | Team + Stakeholders |
| **Production** | Live system | Manual (approval required) | End Users |

### Deployment Process

1. **Development**
   - Create feature branch from `develop`
   - Develop and test locally
   - Create PR to `develop`
   - Code review + CI checks
   - Merge → Auto-deploy to Dev

2. **Staging Release**
   - Tag release: `v0.1.0-rc.1`
   - Manual deployment to Staging
   - QA testing (smoke tests, regression)
   - Stakeholder review
   - Bug fixes (hotfix branches if needed)

3. **Production Release**
   - Tag stable release: `v0.1.0`
   - Create PR: `develop` → `main`
   - Approval required (2+ approvers)
   - Merge → Manual deployment to Production
   - Monitor for 1 hour post-deployment
   - Rollback plan ready

### Rollback Procedure
If critical issues are detected:
1. Revert deployment (previous Docker image)
2. Notify team immediately (Slack #alerts)
3. Investigate root cause
4. Fix and re-deploy

---

## 📖 Appendix

### Glossary

| Term | Definition |
|------|------------|
| **FP** | Financial Planner (보험설계사) |
| **GA** | General Agency (법인보험대리점) |
| **GraphRAG** | Graph Retrieval-Augmented Generation |
| **PII** | Personal Identifiable Information |
| **RBAC** | Role-Based Access Control |
| **SAST** | Static Application Security Testing |
| **DAST** | Dynamic Application Security Testing |
| **KCD** | Korean Classification of Disease |
| **DoD** | Definition of Done |
| **MVP** | Minimum Viable Product |

### References
- [PRD Document](./prd.md)
- [Architecture Document](./docs/architecture.md)
- [GraphRAG Implementation Strategy](./graphrag-implementation-strategy.md)
- [Epic 1: Data Ingestion](./docs/epics/epic-01-data-ingestion.md)
- [Epic 2: GraphRAG Query Engine](./docs/epics/epic-02-graphrag-query-engine.md)
- [Epic 3: FP Workspace](./docs/epics/epic-03-fp-workspace.md)
- [Epic 4: Compliance & Security](./docs/epics/epic-04-compliance-security.md)

---

**Document Owner**: Product Manager
**Last Updated**: 2025-11-25
**Next Review**: After Sprint 4 (end of Epic 1)

---

## 🎉 Success! Let's Build InsureGraph Pro!

This sprint plan is your roadmap to success. Remember:
- **Stay focused** on the sprint goal
- **Communicate early and often** about blockers
- **Prioritize quality** over speed
- **Celebrate wins** (big and small!)
- **Learn from failures** and iterate

Good luck, team! 🚀
