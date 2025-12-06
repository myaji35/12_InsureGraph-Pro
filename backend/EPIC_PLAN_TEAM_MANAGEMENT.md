# Epic Plan: 팀장/지점장 루틴 관리 시스템

**작성일**: 2025-12-05
**버전**: 1.0
**목표**: FP 루틴 데이터 → 팀 분석 → 코칭 → 실적 예측

---

## 📋 Executive Summary

### 핵심 목표
1. **팀장 일일 루틴 자동화**: FP 활동 모니터링 및 즉시 조치
2. **데이터 기반 코칭**: 개인별 맞춤형 원포인트 레슨
3. **실적 예측**: AI 기반 월간/연간 실적 예측
4. **지점 성과 관리**: 팀별 비교 분석 및 전략 수립

### 예상 개발 기간
- **Phase 3.1 (팀장 루틴)**: 6주
- **Phase 3.2 (코칭 시스템)**: 6주
- **Phase 3.3 (예측 시스템)**: 4주
- **총 예상**: 16주 (4개월)

### 개발 우선순위
1. **P0 (Critical)**: Epic 1 (팀장 대시보드), Epic 2.1 (성과 분석)
2. **P1 (High)**: Epic 2.2-2.3 (코칭 시스템)
3. **P2 (Medium)**: Epic 3 (예측 시스템)
4. **P3 (Nice-to-have)**: Epic 4 (모바일 앱)

---

## Epic 1: 팀장 일일 루틴 자동화

**Epic ID**: EPIC-3.1
**예상 기간**: 6주
**Story Points**: 55
**비즈니스 가치**: 팀 관리 시간 75% 절감

### Story 1.1: 팀원 활동 실시간 모니터링

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] 팀원별 일일 활동량 실시간 집계 (문자/전화/미팅/계약)
- [ ] 목표 대비 달성률 자동 계산
- [ ] 활동 상태별 색상 표시 (🟢 우수 / 🟡 보통 / 🔴 부진)
- [ ] 시간대별 활동 분포 차트
- [ ] 팀 전체 활동 요약 (총합, 평균)
- [ ] 실시간 업데이트 (10초 간격)

#### Technical Tasks
```
1. Backend:
   - 활동 로그 집계 서비스 (app/services/activity_tracker.py)
   - 실시간 집계 API (/api/v1/team/activity/realtime)
   - WebSocket 연결 (실시간 업데이트)
   - Redis 캐싱 (성능 최적화)

2. Frontend:
   - TeamActivityMonitor.tsx (실시간 모니터링 컴포넌트)
   - ActivityStatusBadge.tsx (상태 표시)
   - ActivityChart.tsx (시간대별 차트)

3. Database Schema:
   CREATE TABLE fp_activity_logs (
     id UUID PRIMARY KEY,
     fp_id UUID REFERENCES users(id),
     activity_type TEXT, -- 'message', 'call', 'meeting', 'contract'
     activity_date DATE,
     activity_time TIME,
     customer_id UUID,
     result TEXT, -- 'success', 'pending', 'failed'
     duration_minutes INT,
     notes TEXT,
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE fp_daily_targets (
     id UUID PRIMARY KEY,
     fp_id UUID REFERENCES users(id),
     target_date DATE,
     message_target INT DEFAULT 25,
     call_target INT DEFAULT 8,
     meeting_target INT DEFAULT 3,
     contract_target INT DEFAULT 1,
     created_at TIMESTAMP DEFAULT NOW()
   );

4. Aggregation Query:
   -- 일일 활동 집계
   SELECT
     fp_id,
     activity_date,
     COUNT(*) FILTER (WHERE activity_type = 'message') as message_count,
     COUNT(*) FILTER (WHERE activity_type = 'call') as call_count,
     COUNT(*) FILTER (WHERE activity_type = 'meeting') as meeting_count,
     COUNT(*) FILTER (WHERE activity_type = 'contract') as contract_count
   FROM fp_activity_logs
   WHERE activity_date = CURRENT_DATE
   GROUP BY fp_id, activity_date;
```

#### Dependencies
- Epic 1 Phase 2 (FP 루틴 시스템) - 활동 로그 데이터 필요

#### API 요구사항
- WebSocket 지원 (실시간 업데이트)
- Redis 캐싱 (성능)

---

### Story 1.2: 즉시 조치 알림 시스템

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] 활동량 부족 자동 감지 (목표 대비 50% 미달)
- [ ] 전화 연결률 낮음 감지 (40% 미만)
- [ ] 미팅 전환율 낮음 감지 (15% 미만)
- [ ] 지각/조퇴 자동 감지
- [ ] 알림 우선순위 자동 분류 (긴급/중요/일반)
- [ ] 팀장에게 푸시 알림 전송
- [ ] 알림 클릭 → 해당 FP 상세 페이지 이동

#### Technical Tasks
```
1. Backend:
   - 알림 감지 엔진 (app/services/alert_engine.py)
   - 알림 생성 API (/api/v1/team/alerts)
   - 푸시 알림 서비스 (FCM/APNS)

2. Frontend:
   - AlertPanel.tsx (알림 패널)
   - AlertNotification.tsx (푸시 알림)
   - AlertHistory.tsx (알림 이력)

3. Alert Rules:
   class AlertEngine:
       def check_alerts(self, fp_id: str, date: date):
           alerts = []

           # 1. 활동량 부족
           activity = self.get_daily_activity(fp_id, date)
           target = self.get_daily_target(fp_id, date)

           if activity.message_count < target.message_target * 0.5:
               alerts.append({
                   "priority": "urgent",
                   "type": "low_activity",
                   "message": f"{fp.name}: 문자 발송 {activity.message_count}건 (목표 {target.message_target}건의 50% 미달)",
                   "action": "즉시 1:1 면담"
               })

           # 2. 전화 연결률 낮음
           call_rate = self.get_call_connection_rate(fp_id, date)
           if call_rate < 0.4:
               alerts.append({
                   "priority": "important",
                   "type": "low_call_rate",
                   "message": f"{fp.name}: 전화 연결률 {call_rate*100}% (목표 60%)",
                   "action": "통화 시간대 조정 권장"
               })

           # 3. 미팅 전환율 낮음
           meeting_rate = self.get_meeting_conversion_rate(fp_id, date)
           if meeting_rate < 0.15:
               alerts.append({
                   "priority": "important",
                   "type": "low_meeting_conversion",
                   "message": f"{fp.name}: 미팅 전환율 {meeting_rate*100}%",
                   "action": "클로징 스킬 코칭 필요"
               })

           return alerts

4. Database Schema:
   CREATE TABLE team_alerts (
     id UUID PRIMARY KEY,
     team_id UUID REFERENCES teams(id),
     fp_id UUID REFERENCES users(id),
     alert_type TEXT,
     priority TEXT, -- 'urgent', 'important', 'normal'
     message TEXT,
     action TEXT,
     is_read BOOLEAN DEFAULT FALSE,
     is_resolved BOOLEAN DEFAULT FALSE,
     created_at TIMESTAMP DEFAULT NOW()
   );
```

#### Dependencies
- Story 1.1 (활동 데이터 필요)

---

### Story 1.3: 일일 팀 현황 대시보드

**Story Points**: 21
**예상 기간**: 3주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] 팀 전체 목표 vs 실적 진행률 표시
- [ ] FP별 활동 현황 테이블 (정렬/필터 가능)
- [ ] 즉시 조치 필요 알림 패널
- [ ] Today's Insight 자동 생성 (AI 분석)
- [ ] 팀 전체 활동 트렌드 차트 (시간대별)
- [ ] 모바일 반응형 디자인

#### Technical Tasks
```
1. Frontend:
   - TeamDashboard.tsx (메인 대시보드)
   - TeamProgressBar.tsx (진행률 바)
   - FPActivityTable.tsx (FP별 활동 테이블)
   - TodayInsight.tsx (AI 인사이트)
   - TeamTrendChart.tsx (트렌드 차트)

2. Backend:
   - 대시보드 데이터 API (/api/v1/team/dashboard)
   - AI 인사이트 생성 서비스
   - 트렌드 분석 서비스

3. AI Insight Generation:
   class InsightGenerator:
       def generate_daily_insight(self, team_id: str, date: date):
           # 1. 데이터 수집
           team_stats = self.get_team_stats(team_id, date)
           top_performers = self.get_top_performers(team_id, date)
           best_practices = self.extract_best_practices(top_performers)

           # 2. LLM으로 인사이트 생성
           prompt = f"""
           팀 통계:
           - 목표 달성률: {team_stats.achievement_rate}%
           - Top Performer: {top_performers[0].name}
           - Best Practice: {best_practices[0].description}

           오늘의 인사이트를 1문장으로 생성하세요.
           """

           insight = llm.generate(prompt)

           return {
               "insight": insight,
               "top_performer": top_performers[0],
               "best_practice": best_practices[0]
           }

4. UI Layout:
   <TeamDashboard>
     <Header>
       <Title>1팀 현황 (2025-12-05)</Title>
     </Header>

     <ProgressSection>
       <TeamProgressBar
         target={150}
         current={120}
         metrics={['message', 'call', 'meeting', 'contract']}
       />
     </ProgressSection>

     <AlertSection>
       <AlertPanel alerts={urgentAlerts} />
     </AlertSection>

     <ActivitySection>
       <FPActivityTable
         data={fpActivities}
         sortable
         filterable
       />
     </ActivitySection>

     <InsightSection>
       <TodayInsight insight={aiInsight} />
     </InsightSection>

     <TrendSection>
       <TeamTrendChart data={hourlyTrend} />
     </TrendSection>
   </TeamDashboard>
```

#### Dependencies
- Story 1.1, 1.2 (데이터 필요)

---

### Story 1.4: 주간 팀 성과 리포트

**Story Points**: 8
**예상 기간**: 1주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] 주간 목표 vs 실적 비교
- [ ] FP별 성과 순위 (계약 건수/보험료 기준)
- [ ] Best Practice 자동 추출 (상위 20%)
- [ ] 개선 필요 포인트 자동 생성 (하위 20%)
- [ ] 주간 리포트 PDF 다운로드
- [ ] 이메일 자동 발송 (매주 금요일 5시)

#### Technical Tasks
```
1. Backend:
   - 주간 집계 서비스 (app/services/weekly_aggregator.py)
   - Best Practice 추출 알고리즘
   - PDF 생성 서비스 (ReportLab)
   - 이메일 발송 서비스 (Celery)

2. Frontend:
   - WeeklyReport.tsx (주간 리포트)
   - BestPracticeCard.tsx (우수 사례)
   - ImprovementPointCard.tsx (개선 포인트)

3. Best Practice Extraction:
   def extract_best_practices(team_id: str, week_start: date):
       # 1. 상위 20% FP 선정
       top_performers = db.query(FP).filter(
           FP.team_id == team_id,
           FP.weekly_contracts >= percentile(0.8)
       ).all()

       best_practices = []
       for fp in top_performers:
           # 2. 특이 패턴 분석
           if fp.birthday_customer_conversion_rate > 0.7:
               best_practices.append({
                   "fp_name": fp.name,
                   "category": "생일 고객 접근",
                   "metric": f"전환율 {fp.birthday_customer_conversion_rate*100}%",
                   "method": "생일 2일 전 문자 + 당일 전화"
               })

           if fp.gap_analysis_usage_rate == 1.0:
               best_practices.append({
                   "fp_name": fp.name,
                   "category": "보장 분석 활용",
                   "metric": f"활용률 100%",
                   "method": "DOCX 리포트 먼저 발송 → 대면 설명"
               })

       return best_practices

4. Celery Task:
   @celery_app.task
   def send_weekly_report():
       # 매주 금요일 5시 실행
       teams = db.query(Team).all()

       for team in teams:
           # 1. 리포트 생성
           report = generate_weekly_report(team.id)

           # 2. PDF 생성
           pdf = create_pdf(report)

           # 3. 이메일 발송
           send_email(
               to=team.leader.email,
               subject=f"{team.name} 주간 성과 리포트",
               attachment=pdf
           )
```

#### Dependencies
- Story 1.1, 1.3 (주간 데이터 필요)

---

## Epic 2: 데이터 기반 코칭 시스템

**Epic ID**: EPIC-3.2
**예상 기간**: 6주
**Story Points**: 55
**비즈니스 가치**: 코칭 정확도 30%p 향상

### Story 2.1: FP 개인 성과 분석

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P0 (Critical)

#### Acceptance Criteria
- [ ] FP별 주간/월간 성과 상세 분석
- [ ] 팀 평균 대비 비교 (문자/전화/미팅/계약)
- [ ] 활동량 점수 자동 계산 (0-100점)
- [ ] 트렌드 분석 (지난주/지난달 대비)
- [ ] 강점/약점 자동 진단 (AI)
- [ ] 개인 성과 리포트 PDF 생성

#### Technical Tasks
```
1. Backend:
   - 개인 성과 분석 서비스 (app/services/fp_performance_analyzer.py)
   - 점수 계산 알고리즘
   - 강점/약점 진단 AI 모델

2. Frontend:
   - FPPerformanceReport.tsx (개인 성과 리포트)
   - PerformanceScoreCard.tsx (점수 카드)
   - StrengthWeaknessChart.tsx (강점/약점 차트)

3. Score Calculation:
   class PerformanceScoreCalculator:
       def calculate_score(self, fp_id: str, period: str):
           stats = self.get_fp_stats(fp_id, period)
           team_avg = self.get_team_average(fp_id, period)

           score = 0

           # 1. 활동량 (40점)
           message_score = min((stats.message_count / team_avg.message_count) * 20, 20)
           call_score = min((stats.call_count / team_avg.call_count) * 20, 20)
           score += message_score + call_score

           # 2. 효율성 (30점)
           call_rate_score = min((stats.call_connection_rate / 0.6) * 15, 15)
           meeting_rate_score = min((stats.meeting_conversion_rate / 0.3) * 15, 15)
           score += call_rate_score + meeting_rate_score

           # 3. 성과 (30점)
           contract_score = min((stats.contract_count / team_avg.contract_count) * 30, 30)
           score += contract_score

           return round(min(score, 100), 1)

       def diagnose_weakness(self, fp_id: str):
           stats = self.get_fp_stats(fp_id)
           team_avg = self.get_team_average(fp_id)

           weaknesses = []

           # 활동량 부족
           if stats.message_count < team_avg.message_count * 0.6:
               weaknesses.append({
                   "category": "activity_volume",
                   "severity": "critical",
                   "gap": team_avg.message_count - stats.message_count
               })

           # 전화 스킬 부족
           if stats.call_connection_rate < 0.5:
               weaknesses.append({
                   "category": "phone_skill",
                   "severity": "high",
                   "gap": 0.6 - stats.call_connection_rate
               })

           # 클로징 스킬 부족
           if stats.meeting_conversion_rate < 0.2:
               weaknesses.append({
                   "category": "closing",
                   "severity": "medium",
                   "gap": 0.3 - stats.meeting_conversion_rate
               })

           # 우선순위 정렬 (severity)
           return sorted(weaknesses, key=lambda x: SEVERITY_ORDER[x["severity"]])

4. Database Schema:
   CREATE TABLE fp_performance_scores (
     id UUID PRIMARY KEY,
     fp_id UUID REFERENCES users(id),
     period_type TEXT, -- 'weekly', 'monthly'
     period_start DATE,
     period_end DATE,
     total_score NUMERIC,
     activity_score NUMERIC,
     efficiency_score NUMERIC,
     performance_score NUMERIC,
     rank_in_team INT,
     created_at TIMESTAMP DEFAULT NOW()
   );

   CREATE TABLE fp_weakness_diagnoses (
     id UUID PRIMARY KEY,
     fp_id UUID REFERENCES users(id),
     diagnosis_date DATE,
     category TEXT,
     severity TEXT,
     gap_value NUMERIC,
     root_cause TEXT,
     created_at TIMESTAMP DEFAULT NOW()
   );
```

#### Dependencies
- Story 1.1 (활동 데이터 필요)

---

### Story 2.2: 원포인트 레슨 자동 생성

**Story Points**: 21
**예상 기간**: 3주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] 약점별 맞춤형 레슨 템플릿 (10종)
- [ ] AI 기반 레슨 내용 자동 생성
- [ ] 실전 스크립트 예시 포함
- [ ] 실행 체크리스트 자동 생성
- [ ] 성공 지표 자동 설정
- [ ] 레슨 진행 상황 추적

#### Technical Tasks
```
1. Backend:
   - 원포인트 레슨 생성 서비스 (app/services/one_point_lesson_generator.py)
   - 레슨 템플릿 관리
   - LLM 기반 커스터마이징

2. Frontend:
   - OnePointLesson.tsx (레슨 상세)
   - LessonChecklist.tsx (체크리스트)
   - LessonProgress.tsx (진행 상황)

3. Lesson Templates:
   LESSON_TEMPLATES = {
       "activity_volume": {
           "title": "📱 활동량 늘리는 3가지 방법",
           "problem_template": "현재 일일 문자 {current}건 (목표 {target}건)",
           "solution": """
   1. 시스템 알림 활용
      - 오전 9:30 알림 → 즉시 문자 발송
      - 시스템 추천 메시지 사용 (수정만)

   2. 시간 블록 설정
      - 9:30-10:30 문자 집중 시간
      - 방해 요소 차단

   3. 템플릿 활용
      - 상황별 템플릿 5종 준비
      - 고객명만 수정하여 발송
           """,
           "checklist": [
               "□ 매일 9:30 알림 확인",
               "□ 문자 템플릿 5종 준비",
               "□ 1주일 후 목표 달성 확인"
           ],
           "success_metric": "1주일 내 일일 {target}건 이상 달성"
       },

       "phone_skill": {
           "title": "📞 전화 연결률 높이는 황금 시간대",
           "problem_template": "현재 전화 연결률 {current}% (목표 60%)",
           "solution": """
   문제: 오전 9-12시 집중 → 연결률 40%
   해결: 오후 2-4시로 변경 → 연결률 75%

   시간대별 연결률 데이터:
   - 오전 9-12시: 40% (직장인 업무 중)
   - 점심 12-1시: 20% (식사 시간)
   - 오후 2-4시: 75% ✅ (업무 여유)
   - 오후 5-7시: 55% (퇴근 준비)

   실행:
   1. 오전: 문자 발송 집중
   2. 오후 2-4시: 전화 집중
   3. 오후 5시 이후: 팔로업 문자
           """,
           "checklist": [
               "□ 내일부터 오후 2-4시 전화",
               "□ 오전은 문자로 전환",
               "□ 1주일 후 연결률 재측정"
           ],
           "success_metric": "1주일 내 연결률 60% 이상"
       },

       "closing": {
           "title": "🤝 '생각해볼게요' 거절 대응법",
           "problem_template": "미팅 전환율 {current}% (목표 30%)",
           "solution": """
   ❌ 잘못된 대응:
   "빨리 결정하세요"
   → 고객 반감, 계약 실패

   ✅ 올바른 대응:
   "네, 천천히 생각하세요. 중요한 결정이니까요.
    혹시 망설여지는 이유가 뭔가요?"
   → 진짜 이유 파악 → 맞춤 대응

   4단계 스크립트:
   1. 공감: "네, 충분히 생각하세요"
   2. 이유 파악: "혹시 망설여지는 이유가 뭔가요?"
   3. 맞춤 대응:
      - 비싸다 → 필수 보장만 추천
      - 복잡하다 → 간단히 재설명
      - 다른 거랑 비교 → 비교표 제공
   4. 재접촉 약속: "다음주에 다시 연락드릴게요"
           """,
           "checklist": [
               "□ 스크립트 암기 (3회 반복)",
               "□ 다음 미팅 시 즉시 적용",
               "□ 녹음 후 팀장 피드백"
           ],
           "success_metric": "2주 내 미팅 전환율 25% 이상"
       }
   }

4. AI Customization:
   def customize_lesson(template: dict, fp_stats: dict):
       # 템플릿에 개인 데이터 삽입
       lesson = {
           "title": template["title"],
           "problem": template["problem_template"].format(
               current=fp_stats["current_value"],
               target=fp_stats["target_value"]
           ),
           "solution": template["solution"],
           "checklist": template["checklist"],
           "success_metric": template["success_metric"].format(
               target=fp_stats["target_value"]
           )
       }

       # LLM으로 추가 커스터마이징
       customized_solution = llm.generate(f"""
       다음 원포인트 레슨을 FP {fp_stats['name']}님에게 맞게 커스터마이징하세요.

       FP 특성:
       - 경력: {fp_stats['experience_years']}년
       - 강점: {fp_stats['strengths']}
       - 약점: {fp_stats['weaknesses']}

       레슨 내용:
       {lesson['solution']}

       더 구체적이고 실천 가능한 조언으로 수정하세요.
       """)

       lesson["solution"] = customized_solution

       return lesson

5. Database Schema:
   CREATE TABLE one_point_lessons (
     id UUID PRIMARY KEY,
     fp_id UUID REFERENCES users(id),
     team_leader_id UUID REFERENCES users(id),
     lesson_type TEXT,
     title TEXT,
     problem TEXT,
     solution TEXT,
     checklist JSONB,
     success_metric TEXT,
     status TEXT DEFAULT 'pending', -- 'pending', 'in_progress', 'completed'
     assigned_date DATE,
     completed_date DATE,
     created_at TIMESTAMP DEFAULT NOW()
   );
```

#### Dependencies
- Story 2.1 (약점 진단 필요)

---

### Story 2.3: 4주 코칭 플랜 자동 생성

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] 주차별 코칭 목표 자동 설정
- [ ] 일일 체크리스트 자동 생성
- [ ] 진행 상황 자동 추적
- [ ] 주차별 성과 측정 및 피드백
- [ ] 코칭 플랜 진행률 시각화
- [ ] 팀장 알림 (체크리스트 미완료 시)

#### Technical Tasks
```
1. Backend:
   - 코칭 플랜 생성 서비스 (app/services/coaching_plan_generator.py)
   - 진행 상황 추적 서비스
   - 성과 측정 서비스

2. Frontend:
   - CoachingPlan.tsx (4주 플랜)
   - WeeklyGoal.tsx (주차별 목표)
   - DailyChecklist.tsx (일일 체크리스트)
   - ProgressTracker.tsx (진행률)

3. Plan Generation:
   def generate_coaching_plan(fp_id: str, weakness: str):
       # 약점별 4주 플랜
       if weakness == "activity_volume":
           return {
               "week_1": {
                   "goal": "활동량 60% 이상 달성",
                   "actions": [
                       {"day": "월", "task": "팀장 1:1 면담 (30분) - 시스템 활용 교육"},
                       {"day": "화-금", "task": "매일 아침 9시 팀장 체크인"},
                       {"day": "화-금", "task": "일일 목표: 문자 20건, 전화 6건"},
                       {"day": "화-금", "task": "저녁 5시 팀장 리뷰 (10분)"}
                   ],
                   "daily_checklist": [
                       "□ 9:00 시스템 접속 및 오늘 할 일 확인",
                       "□ 9:30 문자 20건 발송",
                       "□ 10:30 전화 6건 시도",
                       "□ 17:00 오늘 활동 기록 및 리뷰"
                   ],
                   "success_metric": "활동량 60% 이상 달성"
               },
               "week_2": {
                   "goal": "전화 스킬 향상 (연결률 50%)",
                   "actions": [
                       {"day": "월", "task": "전화 스크립트 교육 (1시간)"},
                       {"day": "화-금", "task": "통화 시간대 오후 2-4시로 변경"},
                       {"day": "화-금", "task": "스크립트 필수 활용"},
                       {"day": "화-금", "task": "통화 녹음 → AI 분석 → 피드백"}
                   ],
                   "daily_checklist": [
                       "□ 14:00 전화 스크립트 준비",
                       "□ 14:00-16:00 전화 6건 집중",
                       "□ 16:30 통화 녹음 분석 확인",
                       "□ 17:00 개선 포인트 기록"
                   ],
                   "success_metric": "전화 연결률 50% 이상"
               },
               "week_3": {
                   "goal": "클로징 스킬 강화 (미팅 전환율 30%)",
                   "actions": [
                       {"day": "월", "task": "롤플레이 교육 (2시간)"},
                       {"day": "화-금", "task": "미팅 시 보장 분석 리포트 필수"},
                       {"day": "화-금", "task": "계약서 미리 작성해서 지참"},
                       {"day": "목", "task": "팀장 동행 미팅 1회"}
                   ],
                   "daily_checklist": [
                       "□ 미팅 전 보장 분석 리포트 출력",
                       "□ 클로징 스크립트 리뷰",
                       "□ 미팅 후 결과 기록",
                       "□ 팀장에게 피드백 요청"
                   ],
                   "success_metric": "미팅 전환율 30% 이상"
               },
               "week_4": {
                   "goal": "종합 평가 및 다음 목표 설정",
                   "actions": [
                       {"day": "월-목", "task": "1-3주차 학습 내용 적용"},
                       {"day": "금", "task": "월간 성과 리뷰 (1시간)"},
                       {"day": "금", "task": "개선도 측정"},
                       {"day": "금", "task": "다음달 목표 설정"}
                   ],
                   "daily_checklist": [
                       "□ 활동량 목표 달성",
                       "□ 전화 연결률 60% 이상",
                       "□ 미팅 전환율 30% 이상",
                       "□ 계약 건수 목표 달성"
                   ],
                   "success_metric": "월간 목표 80% 이상 달성"
               }
           }

4. Progress Tracking:
   CREATE TABLE coaching_plan_progress (
     id UUID PRIMARY KEY,
     plan_id UUID REFERENCES one_point_lessons(id),
     week_number INT,
     checklist_item TEXT,
     is_completed BOOLEAN DEFAULT FALSE,
     completed_date DATE,
     notes TEXT,
     created_at TIMESTAMP DEFAULT NOW()
   );

5. Celery Task (일일 알림):
   @celery_app.task
   def check_coaching_progress():
       # 매일 저녁 6시 실행
       active_plans = db.query(CoachingPlan).filter(
           CoachingPlan.status == 'in_progress'
       ).all()

       for plan in active_plans:
           # 오늘 체크리스트 완료율 확인
           today_checklist = get_today_checklist(plan.id)
           completion_rate = calculate_completion_rate(today_checklist)

           # 50% 미만 시 팀장에게 알림
           if completion_rate < 0.5:
               send_alert_to_team_leader(
                   plan.team_leader_id,
                   f"{plan.fp.name} 오늘 체크리스트 {completion_rate*100}% 완료"
               )
```

#### Dependencies
- Story 2.2 (원포인트 레슨 필요)

---

### Story 2.4: 팀 코칭 회의 자료 자동 생성

**Story Points**: 8
**예상 기간**: 1주
**우선순위**: P2 (Medium)

#### Acceptance Criteria
- [ ] 주간 팀 성과 총평 자동 생성
- [ ] Best Practice 상위 3개 추출
- [ ] 공통 개선 포인트 자동 도출
- [ ] 개인별 액션 아이템 자동 생성
- [ ] 다음주 팀 목표 자동 설정
- [ ] 회의 자료 PPT/PDF 다운로드

#### Technical Tasks
```
1. Backend:
   - 회의 자료 생성 서비스 (app/services/meeting_material_generator.py)
   - PPT 생성 (python-pptx)
   - 공통 패턴 분석 AI

2. Frontend:
   - MeetingMaterial.tsx (회의 자료)
   - ActionItemList.tsx (액션 아이템)

3. Common Pattern Analysis:
   def analyze_common_patterns(team_id: str, week: int):
       # 1. 전체 팀원 활동 데이터 수집
       fps = db.query(FP).filter(FP.team_id == team_id).all()

       # 2. 공통 약점 분석
       common_weaknesses = {}
       for fp in fps:
           weaknesses = get_fp_weaknesses(fp.id, week)
           for w in weaknesses:
               if w.category not in common_weaknesses:
                   common_weaknesses[w.category] = 0
               common_weaknesses[w.category] += 1

       # 3. 60% 이상이 공통으로 가진 약점 추출
       team_size = len(fps)
       common_issues = {
           category: count
           for category, count in common_weaknesses.items()
           if count >= team_size * 0.6
       }

       return common_issues

   # 예: {"phone_skill": 4, "closing": 3} (5명 중 4명이 전화 스킬 약함)
```

#### Dependencies
- Story 2.1, 2.2 (성과 분석 및 레슨 필요)

---

## Epic 3: AI 기반 실적 예측 시스템

**Epic ID**: EPIC-3.3
**예상 기간**: 4주
**Story Points**: 34
**비즈니스 가치**: 실적 예측 정확도 25%p 향상

### Story 3.1: 월간 실적 예측 엔진

**Story Points**: 21
**예상 기간**: 3주
**우선순위**: P2 (Medium)

#### Acceptance Criteria
- [ ] 현재 실적 기반 단순 예측 (일평균 × 남은 일수)
- [ ] AI 보정 예측 (월초/월중/월말, 요일, 시즌성 반영)
- [ ] 신뢰 구간 계산 (90% 신뢰도)
- [ ] 목표 달성 확률 계산
- [ ] 목표 달성을 위한 일일 필요 실적 계산
- [ ] 예측 정확도 추적 (과거 예측 vs 실제)

#### Technical Tasks
```
1. Backend:
   - 예측 엔진 (app/services/performance_prediction_engine.py)
   - AI 보정 모델 (머신러닝)
   - 신뢰 구간 계산

2. Frontend:
   - PredictionDashboard.tsx (예측 대시보드)
   - PredictionChart.tsx (예측 차트)
   - TargetGapAnalysis.tsx (목표 갭 분석)

3. Prediction Algorithm:
   class PerformancePredictionEngine:
       def predict_monthly(self, team_id: str, current_date: date):
           # 1. 현재 실적
           days_passed = current_date.day
           days_total = calendar.monthrange(
               current_date.year,
               current_date.month
           )[1]

           current_performance = self.get_current_performance(team_id, current_date)

           # 2. 일평균
           daily_avg = current_performance / days_passed

           # 3. 단순 예측
           simple_prediction = current_performance + (daily_avg * (days_total - days_passed))

           # 4. AI 보정
           correction_factor = self.calculate_correction(
               team_id,
               current_date,
               daily_avg
           )

           ai_prediction = simple_prediction * correction_factor

           # 5. 신뢰 구간
           std_dev = self.calculate_std_dev(team_id, current_date)
           confidence_min = ai_prediction - (1.645 * std_dev)  # 90% 신뢰도
           confidence_max = ai_prediction + (1.645 * std_dev)

           # 6. 목표 달성 확률
           target = self.get_monthly_target(team_id, current_date)
           achievement_probability = self.calculate_probability(
               ai_prediction,
               std_dev,
               target
           )

           return {
               "current": current_performance,
               "simple_prediction": round(simple_prediction, 1),
               "ai_prediction": round(ai_prediction, 1),
               "confidence_min": round(confidence_min, 1),
               "confidence_max": round(confidence_max, 1),
               "target": target,
               "gap": target - ai_prediction,
               "achievement_probability": round(achievement_probability * 100, 1),
               "required_daily": self.calculate_required_daily(
                   current_performance,
                   target,
                   days_total - days_passed
               )
           }

       def calculate_correction(self, team_id, current_date, daily_avg):
           # 1. 월초/월중/월말 가중치
           day = current_date.day
           if day <= 10:
               period_weight = 0.9  # 월초 느림
           elif day <= 20:
               period_weight = 1.0  # 월중 평균
           else:
               period_weight = 1.15  # 월말 마감 효과

           # 2. 요일별 패턴
           weekday = current_date.weekday()
           if weekday in [1, 2, 3]:  # 화수목
               weekday_weight = 1.1
           else:
               weekday_weight = 1.0

           # 3. 시즌성
           month = current_date.month
           if month == 12:
               season_weight = 1.2  # 연말
           elif month in [1, 2]:
               season_weight = 0.9  # 신년
           else:
               season_weight = 1.0

           # 4. 팀별 보정 (과거 패턴 학습)
           team_correction = self.get_team_correction_factor(team_id)

           return period_weight * weekday_weight * season_weight * team_correction

4. ML Model Training:
   # 과거 데이터로 보정 계수 학습
   from sklearn.ensemble import RandomForestRegressor

   def train_correction_model():
       # 1. 과거 데이터 수집 (6개월)
       historical_data = db.query(MonthlyPerformance).filter(
           MonthlyPerformance.month >= date.today() - timedelta(days=180)
       ).all()

       # 2. 특징 추출
       X = []  # [day_of_month, weekday, month, team_id, daily_avg]
       y = []  # actual / simple_prediction (보정 계수)

       for record in historical_data:
           X.append([
               record.check_date.day,
               record.check_date.weekday(),
               record.check_date.month,
               record.team_id,
               record.daily_avg
           ])
           y.append(record.actual / record.simple_prediction)

       # 3. 모델 학습
       model = RandomForestRegressor(n_estimators=100)
       model.fit(X, y)

       return model

5. Database Schema:
   CREATE TABLE performance_predictions (
     id UUID PRIMARY KEY,
     team_id UUID REFERENCES teams(id),
     prediction_date DATE,
     prediction_type TEXT, -- 'monthly', 'quarterly', 'yearly'
     current_performance INT,
     simple_prediction NUMERIC,
     ai_prediction NUMERIC,
     confidence_min NUMERIC,
     confidence_max NUMERIC,
     target INT,
     gap INT,
     achievement_probability NUMERIC,
     actual_performance INT, -- 나중에 업데이트
     accuracy NUMERIC, -- actual / ai_prediction
     created_at TIMESTAMP DEFAULT NOW()
   );
```

#### Dependencies
- Story 1.1 (실적 데이터 필요)

---

### Story 3.2: 연간 실적 예측 및 시나리오 분석

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P2 (Medium)

#### Acceptance Criteria
- [ ] 과거 1년 데이터 기반 성장 트렌드 분석
- [ ] 3가지 시나리오 예측 (보수적/기본/공격적)
- [ ] 시나리오별 가정 명시
- [ ] 월별 목표 자동 배분
- [ ] 시나리오별 예상 ROI 계산
- [ ] 지점장 승인 후 목표로 설정

#### Technical Tasks
```
1. Backend:
   - 연간 예측 서비스 (app/services/yearly_prediction_service.py)
   - 시나리오 분석 엔진
   - ROI 계산 서비스

2. Frontend:
   - YearlyPrediction.tsx (연간 예측)
   - ScenarioComparison.tsx (시나리오 비교)
   - MonthlyTargetDistribution.tsx (월별 목표)

3. Scenario Analysis:
   def predict_yearly(team_id: str, year: int):
       # 1. 과거 실적 분석
       past_year = db.query(MonthlyPerformance).filter(
           MonthlyPerformance.team_id == team_id,
           MonthlyPerformance.year == year - 1
       ).all()

       yearly_total = sum([m.contracts for m in past_year])

       # 2. 분기별 성장률 계산
       q1 = sum([m.contracts for m in past_year if m.month in [1,2,3]])
       q2 = sum([m.contracts for m in past_year if m.month in [4,5,6]])
       q3 = sum([m.contracts for m in past_year if m.month in [7,8,9]])
       q4 = sum([m.contracts for m in past_year if m.month in [10,11,12]])

       avg_growth_rate = ((q4 - q1) / q1) / 3  # 분기당 평균 성장률

       # 3. 시나리오 1: 보수적 (+5%)
       scenario_1 = {
           "name": "보수적",
           "growth_rate": 0.05,
           "prediction": yearly_total * 1.05,
           "assumptions": [
               "시장 포화",
               "FP 수 동일",
               "시스템 개선 효과 미미"
           ],
           "monthly_targets": distribute_monthly_target(yearly_total * 1.05, conservative=True)
       }

       # 4. 시나리오 2: 기본 (현재 성장률 유지)
       scenario_2 = {
           "name": "기본",
           "growth_rate": avg_growth_rate,
           "prediction": yearly_total * (1 + avg_growth_rate),
           "assumptions": [
               "현재 성장세 유지",
               "FP 수 동일",
               "시스템 개선 효과 일부"
           ],
           "monthly_targets": distribute_monthly_target(
               yearly_total * (1 + avg_growth_rate),
               moderate=True
           )
       }

       # 5. 시나리오 3: 공격적 (+25%)
       scenario_3 = {
           "name": "공격적",
           "growth_rate": 0.25,
           "prediction": yearly_total * 1.25,
           "assumptions": [
               "FP 루틴 시스템 도입 → 생산성 +150%",
               "Google 주소록 연동 → 신규 고객 +30%",
               "보장 분석 자동화 → 전환율 +20%",
               "AI 챗봇 도입 → 이탈률 -50%",
               "FP 신규 채용 2명"
           ],
           "monthly_targets": distribute_monthly_target(yearly_total * 1.25, aggressive=True),
           "required_investment": 50000,  # $50,000
           "expected_revenue_increase": yearly_total * 0.25 * 30  # 평균 보험료 30만원
       }

       # 6. ROI 계산
       scenario_3["roi"] = (
           scenario_3["expected_revenue_increase"] - scenario_3["required_investment"]
       ) / scenario_3["required_investment"]

       return {
           "scenarios": [scenario_1, scenario_2, scenario_3],
           "recommended": scenario_3,  # 공격적 성장 권장
           "past_year_total": yearly_total,
           "avg_growth_rate": avg_growth_rate
       }

   def distribute_monthly_target(yearly_target: int, **kwargs):
       # 월별 시즌성 반영
       seasonality = {
           1: 1.1,   # 신년 효과
           2: 0.9,   # 설 연휴
           3: 1.2,   # 분기 마감
           4: 1.0,
           5: 1.05,
           6: 1.15,  # 반기 마감
           7: 0.95,  # 여름 휴가
           8: 0.95,
           9: 1.15,  # 3분기 마감
           10: 1.05,
           11: 1.05,
           12: 1.2   # 연말 마감
       }

       total_weight = sum(seasonality.values())
       monthly_targets = {}

       for month, weight in seasonality.items():
           monthly_targets[month] = round(yearly_target * (weight / total_weight))

       return monthly_targets
```

#### Dependencies
- Story 3.1 (월간 예측 필요)

---

## Epic 4: 지점장 대시보드 및 모바일 앱

**Epic ID**: EPIC-3.4
**예상 기간**: 4주
**Story Points**: 34
**비즈니스 가치**: 지점 관리 효율 93% 향상

### Story 4.1: 지점장 통합 대시보드

**Story Points**: 21
**예상 기간**: 3주
**우선순위**: P1 (High)

#### Acceptance Criteria
- [ ] 지점 전체 목표 vs 실적 (일/주/월)
- [ ] 팀별 성과 비교 (순위, 달성률)
- [ ] Top Performer / Bottom Performer (상위/하위 20%)
- [ ] 지점 트렌드 분석 (vs 지난달/지난해)
- [ ] 즉시 조치 필요 알림 (부진 팀/FP)
- [ ] 실적 예측 (월간/연간)

#### Technical Tasks
```
1. Frontend:
   - BranchDashboard.tsx (지점장 대시보드)
   - TeamComparison.tsx (팀별 비교)
   - TopBottomPerformers.tsx (상하위 성과자)
   - BranchTrend.tsx (트렌드 분석)

2. Backend:
   - 지점 집계 서비스 (app/services/branch_aggregator.py)
   - 팀별 비교 분석
   - 지점장 대시보드 API

3. UI Layout:
   <BranchDashboard>
     <Header>
       <Title>강남지점 (2025년 12월)</Title>
       <BranchInfo>
         총 15명 FP (3팀)
       </BranchInfo>
     </Header>

     <ProgressSection>
       <BranchProgress
         target={75}
         current={54}
         achievementRate={72}
       />
     </ProgressSection>

     <TeamSection>
       <TeamComparison
         teams={[
           {name: '1팀', target: 25, current: 18, rate: 72},
           {name: '2팀', target: 25, current: 20, rate: 80},
           {name: '3팀', target: 25, current: 16, rate: 64}
         ]}
       />
     </TeamSection>

     <PerformersSection>
       <TopPerformers top3={topFPs} />
       <BottomPerformers bottom3={bottomFPs} />
     </PerformersSection>

     <TrendSection>
       <BranchTrend
         current={54}
         lastMonth={60}
         lastYear={48}
       />
     </TrendSection>

     <PredictionSection>
       <MonthlyPrediction prediction={74} target={75} />
       <YearlyPrediction scenarios={3} />
     </PredictionSection>
   </BranchDashboard>
```

#### Dependencies
- Epic 1, Epic 3 (팀 데이터 및 예측 필요)

---

### Story 4.2: 팀장용 모바일 앱 (Flutter)

**Story Points**: 13
**예상 기간**: 2주
**우선순위**: P3 (Nice-to-have)

#### Acceptance Criteria
- [ ] iOS/Android 네이티브 앱
- [ ] 일일 팀 현황 실시간 조회
- [ ] 즉시 조치 알림 푸시
- [ ] FP별 성과 상세 조회
- [ ] 원포인트 레슨 조회 및 할당
- [ ] 오프라인 모드 지원

#### Technical Tasks
```
1. Mobile App (Flutter):
   - lib/screens/team_dashboard.dart
   - lib/screens/fp_detail.dart
   - lib/screens/coaching_lesson.dart
   - lib/services/api_service.dart
   - lib/services/notification_service.dart

2. Push Notification:
   - FCM (Firebase Cloud Messaging) 통합
   - 알림 우선순위별 분류
   - 앱 백그라운드 시 알림

3. Offline Mode:
   - SQLite 로컬 DB
   - 최근 1주일 데이터 캐싱
   - 네트워크 복구 시 자동 동기화
```

#### Dependencies
- Story 1.3, 2.2 (대시보드 및 레슨 API)

---

## 📊 개발 로드맵

### Phase 3.1: 팀장 루틴 자동화 (6주)

```
Week 1-2: 활동 모니터링 기반 구축
✅ Story 1.1: 실시간 활동 모니터링
  - FP 활동 로그 수집
  - 실시간 집계
  - WebSocket 연결

Week 3-4: 알림 및 대시보드
✅ Story 1.2: 즉시 조치 알림 시스템
  - 알림 감지 엔진
  - 푸시 알림
✅ Story 1.3: 일일 팀 현황 대시보드
  - 대시보드 UI
  - AI 인사이트

Week 5-6: 리포트 자동화
✅ Story 1.4: 주간 팀 성과 리포트
  - Best Practice 추출
  - PDF 생성
  - 이메일 자동 발송
```

### Phase 3.2: 코칭 시스템 (6주)

```
Week 7-8: 성과 분석
✅ Story 2.1: FP 개인 성과 분석
  - 점수 계산
  - 약점 진단
  - 성과 리포트

Week 9-11: 맞춤형 코칭
✅ Story 2.2: 원포인트 레슨 자동 생성
  - 레슨 템플릿
  - AI 커스터마이징
  - 진행 추적
✅ Story 2.3: 4주 코칭 플랜
  - 주차별 목표
  - 일일 체크리스트
  - 진행률 시각화

Week 12: 회의 자료
✅ Story 2.4: 팀 코칭 회의 자료
  - 공통 패턴 분석
  - PPT 생성
```

### Phase 3.3: 예측 시스템 (4주)

```
Week 13-15: 실적 예측
✅ Story 3.1: 월간 실적 예측
  - 단순 예측
  - AI 보정
  - 신뢰 구간
  - 정확도 추적

Week 16: 연간 예측
✅ Story 3.2: 연간 실적 예측
  - 시나리오 분석
  - 월별 목표 배분
  - ROI 계산
```

### Phase 3.4: 지점장 대시보드 (4주)

```
Week 17-19: 지점장 대시보드
✅ Story 4.1: 통합 대시보드
  - 팀별 비교
  - Top/Bottom Performer
  - 트렌드 분석

Week 20: 모바일 앱 (선택)
✅ Story 4.2: Flutter 앱
  - iOS/Android
  - 푸시 알림
  - 오프라인 모드
```

---

## 🏗️ 기술 아키텍처

### 시스템 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│                 Frontend (Next.js)                      │
├─────────────────────────────────────────────────────────┤
│  FP용                                                   │
│  - /fp/dashboard (일일 루틴)                            │
│  - /fp/customers (고객 관리)                            │
│                                                         │
│  팀장용                                                 │
│  - /team/dashboard (팀 현황)                            │
│  - /team/coaching (코칭)                                │
│  - /team/reports (리포트)                               │
│                                                         │
│  지점장용                                               │
│  - /branch/dashboard (지점 현황)                        │
│  - /branch/teams (팀별 비교)                            │
│  - /branch/predictions (실적 예측)                      │
└─────────────────────────────────────────────────────────┘
                          ↓ REST API / WebSocket
┌─────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                     │
├─────────────────────────────────────────────────────────┤
│  Core Services                                          │
│  - ActivityTracker (활동 추적)                          │
│  - AlertEngine (알림 감지)                              │
│  - PerformanceAnalyzer (성과 분석)                      │
│  - CoachingPlanGenerator (코칭 플랜)                    │
│  - PredictionEngine (실적 예측)                         │
│                                                         │
│  ML Models                                              │
│  - Correction Model (보정 계수)                         │
│  - Pattern Recognition (패턴 인식)                      │
│  - Anomaly Detection (이상 감지)                        │
└─────────────────────────────────────────────────────────┘
         ↓                  ↓                  ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │   Celery     │
│  (관계형 DB)  │  │   (캐시)      │  │  (작업 큐)    │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ - fp_activ...│  │ - 실시간 집계 │  │ - 주간 리포트│
│ - team_ale...│  │ - WebSocket  │  │ - 일일 알림  │
│ - coaching...│  │ - 세션       │  │ - 예측 업데이트│
│ - performa...│  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 📊 성공 지표 (KPI)

### 팀장 효율성

| 지표 | Before | After | 개선 |
|-----|--------|-------|------|
| **일일 팀 관리 시간** | 4시간 | 1시간 | **-75%** |
| **FP별 상태 파악 시간** | 30분 | 3분 | **-90%** |
| **코칭 자료 준비 시간** | 2시간 | 10분 | **-92%** |
| **팀 성과 향상** | +5%/년 | +25%/년 | **+20%p** |

### 코칭 효과

| 지표 | Before | After | 개선 |
|-----|--------|-------|------|
| **코칭 정확도** | 60% | 90% | **+30%p** |
| **FP 개선 속도** | 8주 | 4주 | **-50%** |
| **FP 이탈률** | 30%/년 | 10%/년 | **-67%** |

### 예측 정확도

| 지표 | Before | After | 개선 |
|-----|--------|-------|------|
| **월간 예측 정확도** | 60% | 85% | **+25%p** |
| **연간 예측 정확도** | 50% | 75% | **+25%p** |
| **의사결정 시간** | 2주 | 1일 | **-93%** |

---

## 💰 예상 비용

### 개발 비용 (16주)

| 항목 | 예상 비용 |
|-----|----------|
| **Backend 개발** | $40,000 |
| **Frontend 개발** | $30,000 |
| **ML 모델 개발** | $15,000 |
| **모바일 앱 (Flutter)** | $10,000 |
| **QA 및 테스트** | $5,000 |
| **총계** | **$100,000** |

### 월간 운영 비용 (FP 15명 기준)

| 항목 | 예상 비용 |
|-----|----------|
| **서버 호스팅** | $150 |
| **데이터베이스** | $50 |
| **Redis** | $20 |
| **푸시 알림 (FCM)** | $10 |
| **총계** | **$230/월** |

---

## 🎯 우선순위 결정 기준

### P0 (Critical) - 즉시 구현
- Story 1.1-1.3 (팀장 일일 루틴)
- Story 2.1 (FP 성과 분석)

### P1 (High) - 4주 내
- Story 1.4 (주간 리포트)
- Story 2.2-2.3 (코칭 시스템)
- Story 4.1 (지점장 대시보드)

### P2 (Medium) - 8주 내
- Story 2.4 (회의 자료)
- Story 3.1-3.2 (예측 시스템)

### P3 (Nice-to-have) - 여유 있을 때
- Story 4.2 (모바일 앱)

---

## ✅ Definition of Done (DoD)

각 Story는 다음 조건을 **모두 만족**해야 완료:

1. **기능 완성**
   - [ ] 모든 Acceptance Criteria 충족
   - [ ] 단위 테스트 작성 (커버리지 > 80%)
   - [ ] 통합 테스트 통과
   - [ ] 코드 리뷰 완료

2. **성능**
   - [ ] API 응답 시간 < 500ms
   - [ ] 실시간 업데이트 지연 < 1초
   - [ ] 대시보드 로딩 시간 < 2초

3. **문서화**
   - [ ] API 문서 작성 (Swagger)
   - [ ] 사용자 가이드 작성
   - [ ] 팀장/지점장 교육 자료

4. **배포**
   - [ ] Staging 테스트 완료
   - [ ] Production 배포 승인
   - [ ] 모니터링 설정

---

## 🚀 Quick Start - 다음 단계

### Week 1: 개발 환경 구축

```bash
# 1. 데이터베이스 마이그레이션
cd backend
alembic revision --autogenerate -m "Add team management tables"
alembic upgrade head

# 2. Redis 설정
# docker-compose.yml에 Redis 추가

# 3. Celery 워커 시작
celery -A app.celery_app worker -l info

# 4. 개발 시작
- Story 1.1: 실시간 활동 모니터링
```

---

## 📞 팀 구성 권장사항

### Minimum Team (4명)

1. **Backend Developer** (2명)
   - 활동 추적, 집계, 알림
   - 예측 엔진, ML 모델

2. **Frontend Developer** (1명)
   - 대시보드 UI
   - 차트, 리포트

3. **Data Scientist** (1명)
   - ML 모델 개발
   - 예측 알고리즘

### Ideal Team (6명)

위 4명 + 추가:
4. **Mobile Developer** (1명) - Flutter 앱
5. **QA Engineer** (1명) - 테스트 자동화

---

## 🎉 결론

### 핵심 가치

```
"FP 루틴 데이터가 쌓이면,
 팀장은 정확히 코칭하고,
 지점장은 미래를 예측한다"

FP → 팀장 → 지점장
 ↓      ↓       ↓
루틴   코칭   전략
 ↓      ↓       ↓
성과   향상   성장
```

### 예상 효과

**팀장**:
- 관리 시간 -75%
- 코칭 정확도 +30%p
- 팀 성과 +20%p

**지점장**:
- 예측 정확도 +25%p
- 의사결정 시간 -93%
- 지점 성과 +22%p

### 시작하기

```bash
# Epic Plan 승인 후 바로 시작
cd backend
git checkout -b feature/epic-3.1-team-management
# Story 1.1 개발 착수!
```

---

**작성자**: Claude (AI Assistant)
**검토 필요**: Product Owner, 지점장, 팀장 대표
**다음 단계**: Epic 3.1 Phase 1 개발 착수 승인

