# InsureGraph Pro - Development Guide

## 🚀 빠른 시작 가이드

### 1. 환경 설정

```bash
# 1. 환경 변수 파일 생성
cp .env.local.example .env.local

# 2. Clerk API 키 설정 (.env.local 파일 수정)
# Clerk 대시보드에서 키를 가져와 입력하세요
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
CLERK_SECRET_KEY=sk_test_your_key_here

# 3. 의존성 설치
npm install

# 4. 개발 서버 시작
npm run dev
```

### 2. 백엔드 없이 개발하기

**중요**: 이 프로젝트는 백엔드 없이도 프론트엔드 개발이 가능합니다!

#### 인증 시스템: Clerk

- ✅ 백엔드 API 불필요
- ✅ Google OAuth, Email/Password 기본 제공
- ✅ 사용자 관리, 세션 관리 자동 처리

```typescript
// 사용 예시
import { useUser } from '@clerk/nextjs'

function MyComponent() {
  const { user, isLoaded } = useUser()

  if (!isLoaded) return <div>Loading...</div>
  if (!user) return <div>Not logged in</div>

  return <div>Hello {user.firstName}!</div>
}
```

#### API 호출 처리

개발 모드에서 백엔드가 없을 경우:

```typescript
import { apiClient } from '@/lib/api-client'

try {
  const data = await apiClient.getDocuments()
} catch (error) {
  // Network Error가 발생해도 앱이 멈추지 않음
  // 콘솔에 경고 메시지만 표시
  console.log('백엔드 연결 실패 - 나중에 연결 가능')
}
```

### 3. 개발 서버 접속

```
http://localhost:3000  (기본 포트)
http://localhost:3040  (현재 설정)
```

---

## 🛡️ 에러 방지 시스템

### 문제 1: "Network Error" 회원가입 에러

**원인**: 백엔드 API 서버가 실행되지 않음

**해결책**:
1. **Clerk 사용 (권장)**: 백엔드 없이 인증 가능
2. 백엔드 서버 시작:
   ```bash
   cd backend
   python main.py
   ```

### 문제 2: 환경 변수 누락

**증상**: Clerk 기능이 작동하지 않음

**해결책**:
```bash
# .env.local 파일이 있는지 확인
ls -la .env.local

# 없으면 생성
cp .env.local.example .env.local

# Clerk 키 입력 (https://dashboard.clerk.com에서 가져오기)
```

### 문제 3: 브라우저 캐시

**증상**: 코드를 수정했는데 변경사항이 반영되지 않음

**해결책**:
- Chrome: `Cmd + Shift + R` (Mac) 또는 `Ctrl + Shift + R` (Windows)
- 또는 시크릿 모드로 접속: `Cmd + Shift + N`

---

## 📂 프로젝트 구조

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── sign-in/           # Clerk 로그인 페이지
│   │   ├── sign-up/           # Clerk 회원가입 페이지
│   │   ├── dashboard/         # 대시보드
│   │   └── ...
│   ├── components/            # React 컴포넌트
│   ├── lib/                   # 유틸리티
│   │   ├── api-client.ts      # API 호출 (백엔드 연결)
│   │   ├── env-validation.ts  # 환경 변수 검증
│   │   └── toast.ts           # 알림 시스템
│   └── middleware.ts          # Clerk 인증 미들웨어
├── .env.local.example         # 환경 변수 템플릿
└── package.json
```

---

## 🔧 개발 워크플로우

### Phase 1: 프론트엔드만 개발

1. Clerk로 인증 구현 ✅
2. UI/UX 완성
3. Mock 데이터로 화면 구현
4. 컴포넌트 테스트

### Phase 2: 백엔드 통합

1. 백엔드 API 엔드포인트 개발
2. apiClient에서 실제 API 호출
3. 에러 핸들링 개선
4. 통합 테스트

### Phase 3: 배포 준비

1. 환경 변수 프로덕션 설정
2. 빌드 테스트: `npm run build`
3. E2E 테스트
4. 성능 최적화

---

## 🚨 트러블슈팅

### "Network Error" 발생 시

```typescript
// src/lib/api-client.ts에서 자동으로 처리됩니다
// 개발 모드에서는 경고만 표시하고 계속 진행
if (!error.response) {
  console.warn('⚠️  백엔드 연결 실패 - 개발 계속 가능')
}
```

### Clerk 관련 에러

```
Error: Missing publishableKey
```

**해결**:
```bash
# .env.local 파일 확인
cat .env.local | grep CLERK

# 키가 없으면 Clerk 대시보드에서 가져오기
# https://dashboard.clerk.com/last-active?path=api-keys
```

### 포트 충돌

```bash
# 3000번 포트가 사용 중일 때
PORT=3040 npm run dev

# 또는 package.json 수정
"scripts": {
  "dev": "next dev -p 3040"
}
```

---

## 📚 추가 리소스

- [Next.js 문서](https://nextjs.org/docs)
- [Clerk 문서](https://clerk.com/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [React Flow](https://reactflow.dev/docs)

---

## 💡 Best Practices

### 1. 항상 .env.local 사용

❌ 하드코딩:
```typescript
const API_URL = 'http://localhost:8000'
```

✅ 환경 변수:
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL
```

### 2. 에러 핸들링

❌ 에러 무시:
```typescript
try {
  await apiClient.login(data)
} catch (error) {
  // 아무것도 하지 않음
}
```

✅ 사용자 피드백:
```typescript
try {
  await apiClient.login(data)
} catch (error) {
  showError('로그인에 실패했습니다')
  console.error(error)
}
```

### 3. 타입 안전성

✅ TypeScript 활용:
```typescript
interface User {
  id: string
  email: string
  full_name: string
}

const user: User = await apiClient.getMe()
```

---

## 🎯 다음 단계

- [ ] 백엔드 API 개발 시작
- [ ] 실제 GraphRAG 통합
- [ ] 프로덕션 환경 설정
- [ ] CI/CD 파이프라인 구축
