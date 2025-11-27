"""
PDF Processing Service

pdfplumber를 사용하여 PDF 문서에서 텍스트를 추출하고,
Claude API를 사용하여 엔티티를 추출합니다.
"""
import re
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

import pdfplumber
from anthropic import Anthropic
from loguru import logger

from app.core.config import settings


@dataclass
class Article:
    """보험 약관 조항"""
    article_num: str  # 제1조, 제2조, etc.
    title: str  # 용어의 정의
    content: str  # 전체 내용
    page: int  # 페이지 번호
    paragraphs: List[str]  # 단락 목록


@dataclass
class ExtractedEntity:
    """추출된 엔티티"""
    entity_type: str  # COVERAGE, EXCLUSION, CONDITION, TERM, etc.
    entity_name: str
    description: str
    source_article: str  # 제1조, 제2조, etc.
    confidence: float  # 0.0 ~ 1.0


@dataclass
class PDFProcessingResult:
    """PDF 처리 결과"""
    total_pages: int
    total_articles: int
    articles: List[Article]
    entities: List[ExtractedEntity]
    parsing_confidence: float
    raw_text: str


class PDFProcessor:
    """PDF 처리 서비스"""

    def __init__(self):
        """Initialize PDF processor with Claude client"""
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-5-sonnet-20241022"

    async def process_pdf(self, pdf_path: str) -> PDFProcessingResult:
        """
        PDF 파일 전체 처리 파이프라인

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            PDFProcessingResult: 처리 결과
        """
        logger.info(f"Starting PDF processing: {pdf_path}")

        # 1. PDF에서 텍스트 추출
        raw_text, total_pages = await self.extract_text_from_pdf(pdf_path)
        logger.info(f"Extracted {len(raw_text)} characters from {total_pages} pages")

        # 2. 조항 구조 파싱
        articles = await self.parse_articles(raw_text)
        logger.info(f"Parsed {len(articles)} articles")

        # 3. Claude API로 엔티티 추출 (각 조항마다)
        all_entities = []
        for article in articles:
            entities = await self.extract_entities_from_article(article)
            all_entities.extend(entities)

        logger.info(f"Extracted {len(all_entities)} entities")

        # 4. 파싱 신뢰도 계산 (조항 수와 엔티티 수 기반)
        parsing_confidence = self._calculate_confidence(articles, all_entities)

        return PDFProcessingResult(
            total_pages=total_pages,
            total_articles=len(articles),
            articles=articles,
            entities=all_entities,
            parsing_confidence=parsing_confidence,
            raw_text=raw_text[:10000]  # 첫 10,000자만 저장
        )

    async def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, int]:
        """
        PDF에서 전체 텍스트 추출

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            Tuple[str, int]: (전체 텍스트, 총 페이지 수)
        """
        full_text = []
        total_pages = 0

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)

                for page_num, page in enumerate(pdf.pages, start=1):
                    # 텍스트 추출
                    text = page.extract_text()

                    if text:
                        # 페이지 번호 태그 추가
                        full_text.append(f"\n[PAGE {page_num}]\n")
                        full_text.append(text)

                    # 테이블도 추출 가능
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            # 테이블을 텍스트로 변환
                            table_text = self._table_to_text(table)
                            full_text.append(table_text)

            return "\n".join(full_text), total_pages

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise

    async def parse_articles(self, text: str) -> List[Article]:
        """
        텍스트에서 조항 구조 파싱

        한국 보험 약관은 다음과 같은 구조를 가집니다:
        - 제1조 (용어의 정의)
        - 제2조 (보장의 종류)
        - ...

        Args:
            text: 전체 텍스트

        Returns:
            List[Article]: 파싱된 조항 목록
        """
        articles = []

        # 정규식: "제N조 (제목)" 또는 "제N조(제목)" 또는 "제 N 조 (제목)"
        # 다양한 포맷 지원
        article_pattern = r'제\s*(\d+)\s*조\s*[\(【]([^)】]+)[\)】]'

        # 모든 조항 시작 위치 찾기
        matches = list(re.finditer(article_pattern, text))

        if not matches:
            logger.warning("No articles found in document")
            return articles

        for i, match in enumerate(matches):
            article_num_raw = match.group(1)
            article_title = match.group(2).strip()
            article_num = f"제{article_num_raw}조"

            # 조항 시작 위치
            start_pos = match.start()

            # 조항 끝 위치 (다음 조항 시작 전까지)
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)

            # 조항 내용 추출
            content = text[start_pos:end_pos].strip()

            # 페이지 번호 추출 (가장 가까운 [PAGE N] 태그)
            page_match = re.search(r'\[PAGE (\d+)\]', text[:start_pos][::-1])
            page_num = int(page_match.group(1)) if page_match else 1

            # 단락 분리 (줄바꿈 2개 이상으로 구분)
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]

            article = Article(
                article_num=article_num,
                title=article_title,
                content=content,
                page=page_num,
                paragraphs=paragraphs
            )

            articles.append(article)
            logger.debug(f"Parsed article: {article_num} - {article_title}")

        return articles

    async def extract_entities_from_article(self, article: Article) -> List[ExtractedEntity]:
        """
        Claude API를 사용하여 조항에서 엔티티 추출

        Args:
            article: 조항 객체

        Returns:
            List[ExtractedEntity]: 추출된 엔티티 목록
        """
        try:
            # Claude API 프롬프트
            prompt = self._build_entity_extraction_prompt(article)

            # Claude API 호출
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,  # 일관성을 위해 0으로 설정
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # 응답 파싱
            response_text = message.content[0].text
            entities = self._parse_entity_response(response_text, article.article_num)

            logger.debug(f"Extracted {len(entities)} entities from {article.article_num}")
            return entities

        except Exception as e:
            logger.error(f"Failed to extract entities from {article.article_num}: {e}")
            return []

    def _build_entity_extraction_prompt(self, article: Article) -> str:
        """엔티티 추출을 위한 Claude 프롬프트 생성"""

        prompt = f"""당신은 보험 약관 분석 전문가입니다. 다음 조항에서 핵심 정보를 추출해주세요.

**조항 정보:**
- 조항 번호: {article.article_num}
- 제목: {article.title}
- 페이지: {article.page}

**조항 내용:**
{article.content[:4000]}

**추출할 엔티티 유형:**

1. **COVERAGE** (보장 내용)
   - 보험금을 지급하는 사고, 질병, 상해 등
   - 예: "암 진단", "입원급여금", "수술급여금"

2. **EXCLUSION** (면책 사항)
   - 보험금을 지급하지 않는 경우
   - 예: "고의적 사고", "전쟁으로 인한 손해"

3. **CONDITION** (보장 조건)
   - 보험금 지급을 위한 조건
   - 예: "계약일로부터 90일 경과 후", "의사의 진단서 제출"

4. **TERM** (용어 정의)
   - 약관에서 사용되는 특수 용어
   - 예: "보험수익자", "책임개시일", "피보험자"

5. **BENEFIT** (급여 혜택)
   - 구체적인 보험금 지급 내역
   - 예: "일일 입원급여금 10만원", "암 진단급여금 3천만원"

6. **REQUIREMENT** (요구 사항)
   - 계약자나 피보험자가 이행해야 할 의무
   - 예: "사고 발생 시 즉시 통보", "진단서 제출"

**출력 형식 (JSON):**
```json
[
  {{
    "entity_type": "COVERAGE | EXCLUSION | CONDITION | TERM | BENEFIT | REQUIREMENT",
    "entity_name": "엔티티 이름 (간결하게)",
    "description": "상세 설명",
    "confidence": 0.0 ~ 1.0 (신뢰도)
  }},
  ...
]
```

**주의사항:**
- 조항 내용에 명시적으로 언급된 정보만 추출하세요
- 추론하거나 가정하지 마세요
- JSON 배열 형식으로만 응답하세요 (다른 텍스트 포함 X)
- 엔티티가 없으면 빈 배열 [] 반환
"""
        return prompt

    def _parse_entity_response(self, response: str, source_article: str) -> List[ExtractedEntity]:
        """Claude API 응답에서 엔티티 파싱"""

        try:
            # JSON 추출 (코드 블록이 있을 경우 제거)
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 코드 블록 없이 JSON만 있는 경우
                json_str = response.strip()

            # JSON 파싱
            entity_list = json.loads(json_str)

            # ExtractedEntity 객체로 변환
            entities = []
            for item in entity_list:
                entity = ExtractedEntity(
                    entity_type=item.get('entity_type', 'UNKNOWN'),
                    entity_name=item.get('entity_name', ''),
                    description=item.get('description', ''),
                    source_article=source_article,
                    confidence=float(item.get('confidence', 0.8))
                )
                entities.append(entity)

            return entities

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing entities: {e}")
            return []

    def _table_to_text(self, table: List[List[str]]) -> str:
        """테이블을 텍스트로 변환"""
        if not table:
            return ""

        lines = []
        for row in table:
            # None 값 제거 및 공백 정리
            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
            lines.append(" | ".join(cleaned_row))

        return "\n[TABLE]\n" + "\n".join(lines) + "\n[/TABLE]\n"

    def _calculate_confidence(self, articles: List[Article], entities: List[ExtractedEntity]) -> float:
        """
        파싱 신뢰도 계산

        조항 수, 엔티티 수, 엔티티 평균 신뢰도를 종합하여 계산
        """
        if not articles:
            return 0.0

        # 조항 수 기반 신뢰도 (많을수록 높음, 최대 0.3)
        article_score = min(len(articles) / 100, 0.3)

        # 엔티티 수 기반 신뢰도 (많을수록 높음, 최대 0.3)
        entity_score = min(len(entities) / 200, 0.3)

        # 엔티티 평균 신뢰도 (최대 0.4)
        if entities:
            avg_entity_confidence = sum(e.confidence for e in entities) / len(entities)
            entity_conf_score = avg_entity_confidence * 0.4
        else:
            entity_conf_score = 0.0

        total_confidence = article_score + entity_score + entity_conf_score

        return min(total_confidence, 1.0)


# Singleton instance
pdf_processor = PDFProcessor()
