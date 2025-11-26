# InsureGraph Pro Frontend - Vercel 배포 가이드

## 개요

이 프로젝트는 Vercel에 배포하도록 설정되어 있습니다. Vercel은 Next.js를 만든 회사의 플랫폼으로, 모든 Next.js 기능을 완벽하게 지원합니다.

---

## 1. Vercel 배포 시작하기

### 1.1 Vercel 가입
1. [https://vercel.com](https://vercel.com) 접속
2. GitHub 계정으로 로그인

### 1.2 프로젝트 Import
1. "Add New..." → "Project" 클릭
2. GitHub repository 선택
3. **Root Directory**: `frontend` 설정
4. "Deploy" 클릭

---

## 2. 환경 변수 설정

Vercel 대시보드 → Settings → Environment Variables

```bash
# API 설정
NEXT_PUBLIC_API_BASE_URL=https://your-backend.com/api
NEXT_PUBLIC_API_VERSION=v1

# Clerk 인증
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxxxx
CLERK_SECRET_KEY=sk_live_xxxxx
```

---

## 3. 자동 배포

- **main 브랜치 push**: 프로덕션 자동 배포
- **Pull Request**: Preview 환경 자동 생성

```bash
git push origin main  # 프로덕션 배포
```

---

## 4. 로컬 개발 환경과 동일성 유지

### 환경 변수 동기화
```bash
# Vercel 환경 변수 다운로드
vercel env pull .env.local
```

### 프로덕션 빌드 테스트
```bash
npm run build
npm start
```

---

**배포 URL**: https://your-project.vercel.app
**문서 업데이트**: 2025-11-26
