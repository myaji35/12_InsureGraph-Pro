'use client'

import { useState, useEffect } from 'react'
import { MessageSquare, Shield } from 'lucide-react'
import Link from 'next/link'

export default function DemoPage() {
  const [currentStory, setCurrentStory] = useState(0)

  const consultingStories = [
    {
      question: "아버지가 폐암 3기 진단받았는데, 5년 전 가입한 암보험에서 '소액암'이라며 10%만 보상한다는데 이게 맞나요?",
      answer: "약관을 분석한 결과, 해당 상품은 '일반암(2천만원)'과 '소액암(200만원)'을 구분합니다. 폐암은 일반암에 해당하나, 가입 시점의 약관 버전에 '조기암 진단 시 소액암 적용' 조항이 있었습니다. 3기는 조기암이 아니므로 보험사에 재심사를 요청하시면 전액 보상받으실 수 있습니다. 유사 판례 23건 중 21건이 고객 승소했습니다.",
      tag: "크레임"
    },
    {
      question: "실손보험 2개 가입했는데 병원비 300만원 중 150만원만 받았어요. 나머지는 어떻게 하나요?",
      answer: "실손보험 중복가입 시 '비례보상' 원칙이 적용됩니다. 총 보장한도 600만원(각 300만원)이지만 실제 의료비는 300만원이므로, 각 보험사가 50%씩 분담합니다. 단, KB손해보험 약관 제3조에 '타사 가입 통보 의무'가 있어 이를 이행하지 않으면 보상이 거절될 수 있습니다. 두 번째 보험사에 즉시 청구하시되, 첫 번째 보험사 지급내역서를 첨부하세요.",
      tag: "실손보험"
    },
    {
      question: "태아보험 가입하려는데 아내가 임신 24주입니다. 선천성 질환 보장이 안 된다는데 방법이 없을까요?",
      answer: "22주 이후 가입 시 대부분 보험사가 선천성 질환을 제외합니다. 하지만 현대해상과 삼성화재는 '24주까지 선천성 심장질환 특약' 가입이 가능합니다. 다만 보험료가 20% 인상되고 뇌질환은 제외됩니다. 삼성생명은 28주까지 가입 가능하나 선천성 질환은 전액 불보입니다. 출생 후 즉시 어린이보험 가입 시 3개월부터 선천성 질환 보장이 시작되므로 병행 가입을 권장합니다.",
      tag: "어린이보험"
    },
    {
      question: "연금저축보험 10년 납입했는데 해지하면 원금도 못 받는다는데, 세액공제 받은 400만원은 어떻게 되나요?",
      answer: "10년 납입 후 중도해지 시 해지환급금은 납입보험료의 65-75% 수준입니다. 여기에 세액공제 받은 총 400만원에 대해 기타소득세(16.5%)가 부과되어 66만원을 추가 납부해야 합니다. 대안으로 ①보험계약대출(연 4.7%, 납입금의 70%까지) ②납입중단 후 5년 뒤 연금개시(해지보다 15% 유리) ③저축기간 연장(원금 회복 시 해지) 중 선택할 수 있습니다. 한화생명은 납입중단 시에도 최저보증이율(연 2.5%)이 적용됩니다.",
      tag: "연금보험"
    },
    {
      question: "음주운전 사고로 상대방 전치 8주 진단 나왔는데, 운전자보험에서 형사합의금 5천만원을 거절했어요. 약관에는 보장한다고 되어 있는데요?",
      answer: "운전자보험 약관 제5조 '면책사항'을 확인한 결과, 모든 보험사가 '음주·무면허 운전'을 명시적으로 면책하고 있습니다. 메리츠화재 약관에는 '혈중알콜농도 0.03% 이상' 기준이 명시되어 있어, 이 이하일 경우 보상 가능성이 있습니다. 경찰 음주측정 결과지를 확인하시고 0.03% 미만이면 보험사에 재청구하세요. 또한 '형사합의금'과 별도로 '민사배상금'은 자동차보험 대인배상Ⅱ에서 처리 가능합니다.",
      tag: "크레임"
    },
    {
      question: "CI보험 가입 후 1년 뒤 뇌경색 진단받았는데, 보험사에서 '경미한 뇌졸중'이라 보장 안 된다는데 이게 맞나요?",
      answer: "CI보험 약관의 '중대한 질병' 정의를 분석한 결과, 뇌졸중은 ①신경학적 후유증이 24시간 이상 지속 ②CT/MRI로 병변 확인 두 가지 조건을 모두 충족해야 합니다. 삼성화재와 메트라이프는 '니혼코마스케일(JCS) 2점 이상' 추가 조건이 있으나, KB손해보험은 24시간 지속만 충족하면 인정합니다. 진단서에 '신경학적 증상 48시간 지속' 기록이 있다면 보험사에 이의신청하세요. 금융감독원 분쟁조정 시 평균 처리기간 45일, 고객 승소율 68%입니다.",
      tag: "CI보험"
    },
    {
      question: "15년 납입한 종신보험을 해지하려는데, 보험설계사가 '손해'라며 말립니다. 해지환급금이 납입액의 80%인데 손해가 맞나요?",
      answer: "15년 납입 시 해지환급금율 80%는 업계 평균(85%)보다 낮습니다. 손해 여부는 ①연평균 수익률(납입대비 환급금 증가율) ②기회비용(같은 돈을 은행 적금에 넣었을 때)을 비교해야 합니다. 15년간 연 2.1% 수익률이라면 은행 정기예금(연 3.5%)보다 불리합니다. 다만 종신보험은 '사망보장'이 목적이므로, ①현재 건강상태가 나빠 재가입 어려움 ②상속세 절세 필요 ③유족에게 목돈 전달 목적이 있다면 유지가 유리합니다. 삼성생명은 '보험료 납입완료 후 10년 경과 시 해지환급금 120%' 옵션이 있습니다.",
      tag: "종신보험"
    },
    {
      question: "어머니가 치매 진단 후 요양병원 입원했는데, 간병보험에서 '요양등급 3등급 이상만 보장'이라며 거절했어요. 요양등급 4등급인데 방법이 없나요?",
      answer: "간병보험 약관의 '요양등급 기준'은 보험사마다 다릅니다. 현대해상과 DB손해보험은 3등급 이상만 인정하지만, 메리츠화재와 한화손해보험은 4등급부터 보장합니다(단, 보험금 50% 감액). 또한 '치매 특약'은 요양등급과 무관하게 CDR(Clinical Dementia Rating) 2점 이상이면 인정됩니다. 어머니의 CDR 점수를 확인하시고 2점 이상이면 치매 특약으로 청구하세요. 만약 주계약으로 청구 거절 시 '감액 보장' 조항을 확인해 50%라도 받으실 것을 권장합니다.",
      tag: "크레임"
    },
    {
      question: "변액보험 10년 납입했는데 원금 3천만원이 2천2백만원이 됐어요. 보험사 책임 아닌가요? 펀드 운용 수수료도 너무 높은 것 같은데요.",
      answer: "변액보험 약관 제12조에 '원금보장 불가' 조항이 명시되어 있어 보험사 책임을 묻기는 어렵습니다. 다만 ①판매 시 '원금보장' 오인 설명 ②고위험 펀드 강제 배정 ③수수료 미고지 등이 있었다면 금융감독원 민원 제기가 가능합니다. 변액보험 수수료는 ①사업비(연 3-5%) ②자산운용보수(연 0.5-1.5%) ③펀드 보수(연 1-2%)로 총 연 5-8.5%입니다. 현재 손실 800만원 중 수수료가 약 500만원(총 납입액의 16%)을 차지합니다. 해지보다는 ①펀드 변경(안정형→공격형) ②추가납입 중단 후 10년 유지(사업비 소멸) ③최저보증 옵션 확인(일부 상품은 원금 80% 보장)을 검토하세요.",
      tag: "변액보험"
    },
    {
      question: "정기보험이 80세까지만 보장되는데, 80세 이후에 암 걸리면 어떻게 하나요? 그때 재가입하면 보험료가 너무 비싸지 않나요?",
      answer: "80세 이후 재가입은 ①건강상태 악화로 가입 거절 ②보험료가 현재의 10-15배 수준이라는 두 가지 문제가 있습니다. 대안은 ①100세 만기 정기보험(보험료 현재의 1.4배) ②종신보험 전환(80세 이전까지 추가보험료 납입) ③정기보험 만기 시 '갱신형'으로 전환(건강검진 없이 자동 연장, 보험료 2배 인상) 중 선택입니다. 메트라이프는 '80세 만기 후 85세까지 자동 연장' 특약이 있어 보험료 30% 추가로 5년 연장 가능합니다. 통계상 암 발병률은 70-75세가 정점이고 80세 이후는 15% 감소하므로, 정기보험 80세 만기도 충분한 선택입니다.",
      tag: "정기보험"
    }
  ]

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStory((prev) => (prev + 1) % consultingStories.length)
    }, 10000)

    return () => clearInterval(timer)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Simple Header */}
      <header className="container mx-auto px-6 py-6">
        <nav className="flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Shield className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              InsureGraph Pro
            </span>
          </Link>
          <Link
            href="/"
            className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:shadow-lg transition-all"
          >
            홈으로
          </Link>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-12 text-center">
        <div className="max-w-4xl mx-auto">
          <div className="inline-block px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium mb-6">
            🚀 지식그래프 기반 AI 상담 시뮬레이션
          </div>
          <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
            AI 보험 상담 데모
          </h1>
          <p className="text-xl text-gray-600 mb-8 leading-relaxed">
            실제 보험 상담 케이스를 통해 InsureGraph Pro의 지식그래프 기술을 경험해보세요
          </p>
        </div>
      </section>

      {/* Consulting Stories Section */}
      <section className="container mx-auto px-6 py-12 overflow-hidden">
        <div className="max-w-4xl mx-auto">
          <div className="relative bg-white rounded-2xl shadow-2xl p-8 min-h-[400px]">
            {/* Progress Bar */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gray-200 rounded-t-2xl overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-600 to-purple-600 transition-all duration-300 ease-linear"
                style={{
                  width: `${((currentStory + 1) / consultingStories.length) * 100}%`
                }}
              />
            </div>

            {/* Story Counter */}
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-blue-600" />
                <span className="text-sm font-medium text-gray-500">
                  상담 예시 {currentStory + 1} / {consultingStories.length}
                </span>
              </div>
              <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full">
                {consultingStories[currentStory].tag}
              </span>
            </div>

            {/* Question */}
            <div className="mb-6 transition-all duration-500 ease-in-out" key={`q-${currentStory}`}>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-bold text-sm">Q</span>
                </div>
                <div className="flex-1">
                  <p className="text-lg font-semibold text-gray-800 leading-relaxed">
                    {consultingStories[currentStory].question}
                  </p>
                </div>
              </div>
            </div>

            {/* Answer */}
            <div className="transition-all duration-500 ease-in-out" key={`a-${currentStory}`}>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                  <span className="text-white font-bold text-sm">A</span>
                </div>
                <div className="flex-1">
                  <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-4">
                    <p className="text-gray-700 leading-relaxed">
                      {consultingStories[currentStory].answer}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation Dots */}
            <div className="flex justify-center gap-2 mt-8">
              {consultingStories.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentStory(index)}
                  className={`h-2 rounded-full transition-all duration-300 ${
                    index === currentStory
                      ? 'w-8 bg-gradient-to-r from-blue-600 to-purple-600'
                      : 'w-2 bg-gray-300 hover:bg-gray-400'
                  }`}
                  aria-label={`상담 ${index + 1}로 이동`}
                />
              ))}
            </div>
          </div>

          {/* Auto-play indicator */}
          <div className="text-center mt-6">
            <p className="text-sm text-gray-500">
              10초마다 자동으로 다음 상담 예시가 표시됩니다
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-12 text-white">
            <h2 className="text-3xl font-bold mb-4">
              InsureGraph Pro로 더 많은 기능을 경험해보세요
            </h2>
            <p className="text-lg mb-8 text-blue-100">
              30개 보험사, 1,200개 이상의 약관을 실시간으로 분석하고 비교할 수 있습니다
            </p>
            <div className="inline-block px-8 py-4 bg-white text-blue-600 rounded-xl font-semibold">
              2026년 1월 찾아뵙겠습니다.
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-8">
        <div className="container mx-auto px-6">
          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center gap-2">
              <Shield className="h-6 w-6 text-blue-600" />
              <span className="font-semibold text-gray-700">InsureGraph Pro</span>
            </div>
            <div className="text-gray-600 text-sm">
              © 2025 InsureGraph Pro. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
