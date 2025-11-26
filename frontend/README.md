# InsureGraph Pro - Frontend

FP(Financial Planner) 전용 보험 약관 분석 시스템의 프론트엔드 애플리케이션입니다.

## 기술 스택

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.4
- **State Management**: Zustand 4.4
- **HTTP Client**: Axios 1.6
- **UI Components**: React 18.2

## 주요 기능

### 인증 시스템
- JWT 기반 로그인/회원가입
- 자동 토큰 갱신 (Refresh Token)
- 보호된 라우트 (Protected Routes)
- 역할 기반 접근 제어 (RBAC)

### 대시보드
- 사용자 정보 표시
- 약관 문서 관리
- 질의응답 인터페이스
- 고객 포트폴리오 분석

## 시작하기

### 필수 요구사항

- Node.js 18.x 이상
- npm 또는 yarn
- Backend API 서버 실행 중 (기본: http://localhost:8000)

### 설치

```bash
# 의존성 설치
npm install

# 또는
yarn install
```

### 환경 변수 설정

`.env.local` 파일을 생성하고 다음 변수를 설정하세요:

```env
# API 서버 URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# API 버전
NEXT_PUBLIC_API_VERSION=v1

# 환경 (development, production)
NEXT_PUBLIC_ENVIRONMENT=development
```

### 개발 서버 실행

```bash
npm run dev

# 또는
yarn dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인하세요.

### 빌드

```bash
# 프로덕션 빌드
npm run build

# 빌드된 앱 실행
npm run start
```

### 타입 체크

```bash
npm run type-check
```

### 린트

```bash
npm run lint
```

## 프로젝트 구조

```
frontend/
├── public/              # 정적 파일
├── src/
│   ├── app/            # Next.js App Router 페이지
│   │   ├── layout.tsx  # 루트 레이아웃
│   │   ├── page.tsx    # 홈 페이지
│   │   ├── login/      # 로그인 페이지
│   │   ├── register/   # 회원가입 페이지
│   │   └── dashboard/  # 대시보드
│   ├── components/     # 재사용 가능한 컴포넌트
│   ├── lib/           # 유틸리티 및 헬퍼
│   │   ├── api-client.ts  # API 클라이언트
│   │   └── utils.ts      # 유틸리티 함수
│   ├── store/         # Zustand 스토어
│   │   └── auth-store.ts # 인증 상태 관리
│   ├── types/         # TypeScript 타입 정의
│   │   └── index.ts   # 전역 타입
│   └── styles/        # 스타일 파일
│       └── globals.css # Tailwind CSS 전역 스타일
├── .env.local         # 환경 변수 (git에서 제외)
├── .eslintrc.json     # ESLint 설정
├── next.config.js     # Next.js 설정
├── tailwind.config.ts # Tailwind CSS 설정
├── tsconfig.json      # TypeScript 설정
└── package.json       # 프로젝트 메타데이터
```

## API 클라이언트

API 클라이언트는 axios 기반으로 구현되었으며 다음 기능을 제공합니다:

### 인증 API
- `login(data)` - 로그인
- `register(data)` - 회원가입
- `logout(refreshToken)` - 로그아웃
- `getMe()` - 현재 사용자 정보 조회
- `updateProfile(data)` - 프로필 업데이트
- `changePassword(current, new)` - 비밀번호 변경

### 질의응답 API
- `executeQuery(data)` - 질의 실행
- `getQueryStatus(queryId)` - 질의 상태 조회

### 문서 API
- `uploadDocument(file, metadata)` - 문서 업로드
- `getDocuments(params)` - 문서 목록 조회
- `getDocument(documentId)` - 문서 상세 조회
- `deleteDocument(documentId)` - 문서 삭제

### 자동 토큰 갱신

API 클라이언트는 401 응답 시 자동으로 refresh token을 사용하여 access token을 갱신하고 요청을 재시도합니다.

## 상태 관리

Zustand를 사용한 인증 상태 관리:

```typescript
import { useAuthStore } from '@/store/auth-store'

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuthStore()

  // ...
}
```

### 상태
- `user` - 현재 사용자 정보
- `accessToken` - JWT 액세스 토큰
- `refreshToken` - JWT 리프레시 토큰
- `isAuthenticated` - 인증 상태
- `isLoading` - 로딩 상태
- `error` - 에러 메시지

### 액션
- `login(data)` - 로그인
- `register(data)` - 회원가입
- `logout()` - 로그아웃
- `loadUser()` - 사용자 정보 로드
- `clearError()` - 에러 초기화

## 스타일링

Tailwind CSS를 사용하며 커스텀 유틸리티 클래스를 제공합니다:

### 버튼
- `.btn-primary` - 주요 액션 버튼
- `.btn-secondary` - 보조 액션 버튼

### 입력 필드
- `.input-field` - 표준 입력 필드

### 카드
- `.card` - 카드 컨테이너

### 색상 팔레트
- `primary-*` - 주요 브랜드 색상 (Blue)
- `secondary-*` - 보조 색상 (Gray)

## 보안

### 인증
- JWT 기반 인증
- Access Token + Refresh Token 패턴
- LocalStorage에 토큰 저장 (HttpOnly Cookie 미지원)
- 자동 토큰 갱신

### API 보안
- CORS 설정 필요 (Backend)
- Authorization Bearer Token
- 401 에러 시 자동 로그인 페이지 리디렉션

## 개발 가이드

### 새 페이지 추가

```bash
# src/app/ 디렉토리에 폴더 생성
mkdir -p src/app/my-page

# page.tsx 파일 생성
touch src/app/my-page/page.tsx
```

### 새 컴포넌트 추가

```bash
# src/components/ 디렉토리에 컴포넌트 생성
touch src/components/MyComponent.tsx
```

### API 엔드포인트 추가

`src/lib/api-client.ts` 파일의 `APIClient` 클래스에 메서드를 추가하세요:

```typescript
async myNewEndpoint(data: any): Promise<any> {
  const response = await this.client.post('/my-endpoint', data)
  return response.data
}
```

### 상태 관리 추가

새로운 Zustand 스토어를 생성하려면 `src/store/` 디렉토리에 파일을 추가하세요:

```typescript
import { create } from 'zustand'

interface MyState {
  // state
}

export const useMyStore = create<MyState>()((set) => ({
  // state and actions
}))
```

## 배포

### Vercel (권장)

```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
vercel
```

### Docker

```bash
# Docker 이미지 빌드
docker build -t insuregraph-frontend .

# 컨테이너 실행
docker run -p 3000:3000 insuregraph-frontend
```

### 환경 변수 설정

프로덕션 환경에서는 다음 환경 변수를 설정하세요:

- `NEXT_PUBLIC_API_URL` - 프로덕션 API URL
- `NEXT_PUBLIC_API_VERSION` - API 버전 (v1)
- `NEXT_PUBLIC_ENVIRONMENT` - production

## 트러블슈팅

### API 연결 오류

```
Error: Network Error
```

**해결 방법:**
1. Backend API 서버가 실행 중인지 확인
2. `.env.local`의 `NEXT_PUBLIC_API_URL` 확인
3. CORS 설정 확인 (Backend)

### 토큰 만료 오류

```
Error: 401 Unauthorized
```

**해결 방법:**
1. LocalStorage의 토큰 삭제 후 재로그인
2. Backend의 JWT 설정 확인 (만료 시간)

### 타입 오류

```
Type error: ...
```

**해결 방법:**
1. `npm run type-check` 실행하여 타입 오류 확인
2. `src/types/index.ts`의 타입 정의 확인

## 라이선스

Proprietary - All Rights Reserved

## 지원

문의사항이 있으시면 개발팀에 연락하세요.
