"""
AI-based PDF Link Extractor Service

LLM을 사용하여 HTML에서 보험약관 및 특약 PDF 링크를 추출하는 서비스
"""
import re
import json
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from loguru import logger
from openai import AsyncOpenAI

from app.core.config import settings


class AIPdfExtractor:
    """AI 기반 PDF 링크 추출기"""

    def __init__(self):
        """Initialize AI PDF Extractor"""
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=getattr(settings, "OPENAI_BASE_URL", None)
        )

    async def extract_pdf_links_from_html(
        self,
        html_content: str,
        insurer: str,
        url: str
    ) -> List[Dict[str, str]]:
        """
        HTML에서 PDF 링크를 추출

        Args:
            html_content: HTML 콘텐츠
            insurer: 보험사명
            url: 원본 URL

        Returns:
            List[Dict]: 추출된 PDF 정보 리스트
                - title: 문서 제목
                - url: PDF URL
                - category: 카테고리 (약관/특약)
                - product_type: 상품 유형
        """
        logger.info(f"Extracting PDF links from {url} for {insurer}")

        # HTML 파싱
        soup = BeautifulSoup(html_content, 'html.parser')

        # 모든 링크 찾기
        all_links = soup.find_all('a', href=True)

        # PDF 링크 필터링
        pdf_links = []
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # PDF 링크인지 확인
            if '.pdf' in href.lower() or 'download' in href.lower():
                # 절대 URL로 변환
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    # 상대 경로 → 절대 경로 변환
                    from urllib.parse import urljoin
                    href = urljoin(url, href)
                elif not href.startswith('http'):
                    continue

                pdf_links.append({
                    'href': href,
                    'text': text,
                    'title': link.get('title', '')
                })

        logger.info(f"Found {len(pdf_links)} potential PDF links")

        if not pdf_links:
            return []

        # AI를 사용하여 링크 분류
        classified_links = await self._classify_pdf_links_with_ai(
            pdf_links,
            insurer
        )

        return classified_links

    async def _classify_pdf_links_with_ai(
        self,
        pdf_links: List[Dict],
        insurer: str
    ) -> List[Dict[str, str]]:
        """
        AI를 사용하여 PDF 링크를 분류

        Args:
            pdf_links: PDF 링크 리스트
            insurer: 보험사명

        Returns:
            List[Dict]: 분류된 PDF 정보
        """
        # 링크 정보를 텍스트로 변환
        links_text = "\n".join([
            f"{i+1}. URL: {link['href']}\n   텍스트: {link['text']}\n   제목: {link.get('title', '')}"
            for i, link in enumerate(pdf_links)
        ])

        # AI 프롬프트
        prompt = f"""
당신은 {insurer} 보험사의 약관 문서를 분류하는 전문가입니다.

다음은 웹사이트에서 발견한 PDF 링크 목록입니다:

{links_text}

각 링크를 분석하여 다음 정보를 JSON 배열 형식으로 출력해주세요:

{{
  "documents": [
    {{
      "index": 링크 번호 (1부터 시작),
      "title": "문서 제목 (한국어, 간결하게)",
      "category": "약관" 또는 "특약",
      "product_type": "상품 유형 (예: 종신보험, 정기보험, 연금보험, CI보험, 건강보험, 저축보험 등)",
      "is_relevant": true 또는 false (보험약관/특약 문서인 경우 true, 아닌 경우 false)
    }}
  ]
}}

분류 기준:
1. "약관"은 주계약 약관을 의미합니다.
2. "특약"은 추가 특약 약관을 의미합니다.
3. 제목은 링크 텍스트나 URL에서 추출하되, 간결하고 명확하게 작성하세요.
4. is_relevant는 보험약관이나 특약 문서가 아닌 경우 (예: 공시, 안내문, 설명서 등) false로 설정하세요.

JSON만 출력하고 다른 텍스트는 출력하지 마세요.
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 보험약관 문서 분류 전문가입니다. JSON 형식으로만 응답하세요."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )

            # AI 응답 파싱
            ai_response = response.choices[0].message.content
            logger.debug(f"AI response: {ai_response}")

            # JSON 파싱
            result = json.loads(ai_response)
            documents = result.get('documents', [])

            # 결과 변환
            classified = []
            for doc in documents:
                if not doc.get('is_relevant', True):
                    continue

                index = doc.get('index', 0) - 1
                if 0 <= index < len(pdf_links):
                    classified.append({
                        'title': doc.get('title', pdf_links[index]['text']),
                        'url': pdf_links[index]['href'],
                        'category': doc.get('category', '약관'),
                        'product_type': doc.get('product_type', '기타'),
                    })

            logger.info(f"AI classified {len(classified)} relevant documents")
            return classified

        except Exception as e:
            logger.error(f"AI classification failed: {e}")

            # Fallback: 간단한 키워드 기반 분류
            return self._fallback_classification(pdf_links, insurer)

    def _fallback_classification(
        self,
        pdf_links: List[Dict],
        insurer: str
    ) -> List[Dict[str, str]]:
        """
        AI 실패 시 폴백: 키워드 기반 분류

        Args:
            pdf_links: PDF 링크 리스트
            insurer: 보험사명

        Returns:
            List[Dict]: 분류된 PDF 정보
        """
        logger.warning("Using fallback keyword-based classification")

        classified = []
        for link in pdf_links:
            text = (link['text'] + ' ' + link.get('title', '')).lower()

            # 약관/특약 키워드 확인
            if any(keyword in text for keyword in ['약관', '보험약관', '주계약']):
                category = '약관'
            elif any(keyword in text for keyword in ['특약', '추가특약']):
                category = '특약'
            else:
                continue  # 관련 없는 문서 제외

            # 상품 유형 추론
            product_type = '기타'
            if '종신' in text:
                product_type = '종신보험'
            elif '정기' in text:
                product_type = '정기보험'
            elif '연금' in text:
                product_type = '연금보험'
            elif 'ci' in text or '암' in text or '질병' in text:
                product_type = 'CI보험'
            elif '건강' in text or '의료' in text:
                product_type = '건강보험'
            elif '저축' in text:
                product_type = '저축보험'

            classified.append({
                'title': link['text'] or 'PDF 문서',
                'url': link['href'],
                'category': category,
                'product_type': product_type,
            })

        logger.info(f"Fallback classified {len(classified)} documents")
        return classified
