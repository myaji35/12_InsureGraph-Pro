# GitHub Pages 배포 가이드

## 사전 준비

### 1. Repository 이름 확인 및 설정

`next.config.js` 파일의 `basePath`와 `assetPrefix`를 실제 repository 이름으로 변경하세요:

```javascript
// 예: https://username.github.io/insuregraph-pro
basePath: process.env.NODE_ENV === 'production' ? '/insuregraph-pro' : '',
assetPrefix: process.env.NODE_ENV === 'production' ? '/insuregraph-pro' : '',
```

만약 **username.github.io** 리포지토리를 사용한다면 basePath를 빈 문자열로 설정하세요:

```javascript
basePath: '',
assetPrefix: '',
```

### 2. Clerk API Key 설정

GitHub Repository Settings에서 Secret 추가:
1. Repository > Settings > Secrets and variables > Actions
2. **New repository secret** 클릭
3. Name: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
4. Value: Clerk Dashboard의 Publishable Key

## 배포 방법

### 자동 배포 (GitHub Actions)

1. **main** 브랜치에 push하면 자동으로 배포됩니다:

```bash
git add .
git commit -m "Deploy to GitHub Pages"
git push origin main
```

2. GitHub Actions 탭에서 배포 진행 상황 확인

### 수동 배포

GitHub Actions 탭에서 **Deploy to GitHub Pages** workflow를 수동으로 실행할 수 있습니다.

## GitHub Pages 설정

1. Repository > Settings > Pages
2. **Source**: GitHub Actions 선택
3. 첫 배포 후 자동으로 URL이 생성됩니다:
   - `https://username.github.io/repository-name/`

## 로컬 빌드 테스트

배포 전 로컬에서 static export 테스트:

```bash
npm run build
```

생성된 `out/` 디렉토리를 확인하세요.

## 주의사항

### 1. Static Export 제한사항

GitHub Pages는 static hosting이므로 다음 기능은 사용할 수 없습니다:
- ❌ Server-side Rendering (SSR)
- ❌ API Routes (`/api/*`)
- ❌ Image Optimization (설정에서 비활성화됨)
- ❌ Middleware (일부 기능)

### 2. Clerk 인증

✅ Clerk은 클라이언트 사이드에서 작동하므로 정상 작동합니다.

Clerk Dashboard에서 Allowed domains에 GitHub Pages URL 추가:
```
https://username.github.io
```

### 3. Backend API

백엔드 서버가 필요한 기능:
- 문서 업로드
- AI 분석
- GraphRAG 검색

해결 방법:
- Backend를 별도로 배포 (Vercel, Railway, Render 등)
- `.env.local`에 API URL 설정:
  ```
  NEXT_PUBLIC_API_URL=https://your-backend-url.com
  ```

## 문제 해결

### 404 오류

- basePath가 올바르게 설정되었는지 확인
- `.nojekyll` 파일이 `public/` 디렉토리에 있는지 확인

### 스타일/이미지 안보임

- assetPrefix 설정 확인
- 이미지 경로가 절대 경로인지 확인 (`/image.png` → `image.png`)

### Clerk 인증 오류

- Clerk Dashboard의 Allowed domains 확인
- NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY Secret 확인

## 배포 완료 확인

1. `https://username.github.io/repository-name/` 접속
2. 페이지 로드 확인
3. Clerk 로그인 테스트
4. 브라우저 Console 오류 확인
