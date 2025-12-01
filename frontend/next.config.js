/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Vercel 배포 설정
  // 모든 Next.js 기능 지원 (Middleware, SSR, ISR 등)

  // 이미지 최적화 활성화 (Vercel은 자동 이미지 최적화 지원)
  images: {
    domains: ['localhost'], // 필요시 외부 이미지 도메인 추가
  },

  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },

  // API rewrites for development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`
          : 'http://localhost:8000/api/:path*',
      },
    ];
  },
}

module.exports = nextConfig
