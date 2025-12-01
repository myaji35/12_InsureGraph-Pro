"""
File Extractor Service

Claude API를 사용하여 HTML에서 보험 약관 파일명을 추출하는 서비스
"""
import re
from typing import List, Dict, Tuple
from bs4 import BeautifulSoup

import anthropic
from loguru import logger

from app.core.config import settings


class FileExtractor:
    """Claude를 사용한 파일명 추출기"""

    def __init__(self):
        """Initialize with Anthropic API key"""
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.model = "claude-sonnet-4-5-20250929"  # Claude Sonnet 4.5

    def _preprocess_html(self, html_content: str, max_length: int = 100000) -> str:
        """
        HTML 전처리 및 축약

        Args:
            html_content: 원본 HTML
            max_length: 최대 길이

        Returns:
            str: 전처리된 HTML
        """
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style tags
        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Clean whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length] + "\n...(truncated)"
            logger.warning(f"HTML truncated from {len(html_content)} to {max_length} chars")

        return text

    def _extract_links_from_html(self, html_content: str) -> List[Dict[str, str]]:
        """
        HTML에서 모든 링크 추출

        Args:
            html_content: HTML 콘텐츠

        Returns:
            List[Dict]: 링크 정보 목록
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '')
            text = a_tag.get_text(strip=True)

            # PDF 링크만 추출
            if '.pdf' in href.lower() or 'pdf' in text.lower() or '약관' in text:
                links.append({
                    'href': href,
                    'text': text,
                    'title': a_tag.get('title', '')
                })

        logger.info(f"Extracted {len(links)} potential document links")
        return links

    async def extract_filenames(
        self,
        html_content: str,
        company_name: str,
        max_files: int = 5
    ) -> List[Dict[str, any]]:
        """
        HTML에서 약관 파일명 추출

        Args:
            html_content: HTML 콘텐츠
            company_name: 보험사명
            max_files: 최대 추출 파일 수

        Returns:
            List[Dict]: 발견된 파일 정보
            [
                {
                    "filename": "삼성화재_종합보험약관_v2.0.pdf",
                    "url": "https://...",
                    "confidence": 0.95,
                    "context": "링크 주변 텍스트"
                }
            ]
        """
        logger.info(f"Extracting filenames for {company_name} using Claude API...")

        # First, extract links from HTML
        links = self._extract_links_from_html(html_content)

        # Preprocess HTML for Claude
        processed_text = self._preprocess_html(html_content)

        # Build prompt for Claude
        prompt = f"""당신은 보험사 웹사이트 분석 전문가입니다.

다음 HTML 콘텐츠는 **{company_name}** 웹사이트에서 가져온 것입니다.

이 HTML에서 보험 약관 PDF 파일들의 정보를 추출해주세요.

**추출 규칙:**
1. 약관, 보험약관, 상품설명서, 특약 등의 문서만 추출
2. 각 파일에 대해 적절한 파일명을 생성 (형식: {company_name}_문서종류_버전.pdf)
3. 파일 URL이 있으면 함께 추출
4. 신뢰도를 0.0 ~ 1.0 사이로 평가
5. 최대 {max_files}개까지만 추출
6. 가장 중요한 문서부터 우선순위를 두어 추출

**출력 형식 (JSON):**
```json
[
  {{
    "filename": "삼성화재_종합보험약관_v2.0.pdf",
    "url": "https://example.com/doc.pdf",
    "confidence": 0.95,
    "context": "종합보험 상품 안내"
  }}
]
```

**발견된 링크들:**
{links[:20]}

**HTML 콘텐츠:**
{processed_text[:50000]}

JSON 형식으로만 응답해주세요. 설명이나 다른 텍스트는 포함하지 마세요."""

        try:
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract response
            response_text = message.content[0].text.strip()
            logger.debug(f"Claude response: {response_text[:500]}...")

            # Parse JSON response
            import json

            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON array directly
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    logger.error("No JSON found in Claude response")
                    return []

            # Parse JSON
            files = json.loads(json_str)

            logger.info(f"Claude extracted {len(files)} files for {company_name}")
            return files[:max_files]

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.error(f"Response was: {response_text}")
            return []
        except Exception as e:
            logger.error(f"Error extracting filenames: {e}")
            raise

    def extract_filenames_simple(
        self,
        html_content: str,
        company_name: str,
        max_files: int = 10
    ) -> List[Dict[str, any]]:
        """
        간단한 규칙 기반 파일명 추출 (Claude 없이)

        Args:
            html_content: HTML 콘텐츠
            company_name: 보험사명
            max_files: 최대 추출 파일 수

        Returns:
            List[Dict]: 발견된 파일 정보
        """
        logger.info(f"Extracting filenames using simple rules for {company_name}")

        soup = BeautifulSoup(html_content, 'html.parser')
        files = []

        # Find PDF links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href', '')
            text = a_tag.get_text(strip=True)

            # Check if it's a PDF link
            if '.pdf' not in href.lower():
                continue

            # Check if it contains insurance policy keywords
            keywords = ['약관', '보험약관', '특약', '상품설명서', '계약']
            if not any(keyword in text or keyword in href for keyword in keywords):
                continue

            # Generate filename
            filename = f"{company_name}_{text}.pdf" if text else f"{company_name}_약관.pdf"

            files.append({
                'filename': filename,
                'url': href,
                'confidence': 0.7,
                'context': text
            })

            if len(files) >= max_files:
                break

        logger.info(f"Extracted {len(files)} files using simple rules")
        return files


# Async wrapper for compatibility
async def extract_filenames_from_html(
    html_content: str,
    company_name: str,
    max_files: int = 10,
    use_claude: bool = True
) -> List[Dict[str, any]]:
    """
    HTML에서 파일명 추출 (비동기 래퍼)

    Args:
        html_content: HTML 콘텐츠
        company_name: 보험사명
        max_files: 최대 파일 수
        use_claude: Claude API 사용 여부

    Returns:
        List[Dict]: 파일 정보 목록
    """
    extractor = FileExtractor()

    if use_claude:
        return await extractor.extract_filenames(html_content, company_name, max_files)
    else:
        return extractor.extract_filenames_simple(html_content, company_name, max_files)
