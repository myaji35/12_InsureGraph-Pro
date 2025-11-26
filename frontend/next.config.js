const createNextIntlPlugin = require('next-intl/plugin')

const withNextIntl = createNextIntlPlugin('./src/i18n.ts')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // GitHub Pages 배포 설정
  // NOTE: next-intl은 서버 컴포넌트를 사용하므로 정적 export와 호환되지 않습니다
  // 프로덕션 배포 시 Vercel, Netlify 등의 플랫폼을 사용하세요
  // output: 'export',

  // GitHub Pages의 repository 이름을 basePath로 설정
  // 예: https://username.github.io/repo-name
  // basePath를 리포지토리 이름으로 변경하세요
  // basePath: process.env.NODE_ENV === 'production' ? '/insuregraph-pro' : '',
  // assetPrefix: process.env.NODE_ENV === 'production' ? '/insuregraph-pro' : '',

  // 이미지 최적화
  images: {
    unoptimized: process.env.NODE_ENV === 'production',
  },

  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

module.exports = withNextIntl(nextConfig)
