import './globals.css'

export const metadata = {
  title: 'InsureGraph Pro - AI 보험 상담 데모',
  description: '지식그래프 기반 AI 보험 상담 시뮬레이션',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
