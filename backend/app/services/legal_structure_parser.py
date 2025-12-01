"""
Legal Structure Parser Service

한국 법률 문서(보험 약관)의 구조를 파싱하는 서비스
제N조, ①항, 1., 가. 등의 계층 구조를 추출합니다.
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class Subclause:
    """하위 조항 (1., 2., 가., 나. 등)"""
    subclause_num: str
    text: str
    level: int = 3  # 계층 레벨


@dataclass
class Paragraph:
    """항 (①, ②, ③ 등)"""
    paragraph_num: str
    text: str
    subclauses: List[Subclause] = field(default_factory=list)
    level: int = 2


@dataclass
class Article:
    """조 (제1조, 제2조 등)"""
    article_num: str
    title: str
    text: str
    page: Optional[int] = None
    paragraphs: List[Paragraph] = field(default_factory=list)
    level: int = 1


@dataclass
class ParsedDocument:
    """파싱된 문서 전체"""
    articles: List[Article]
    total_articles: int
    total_paragraphs: int
    total_subclauses: int

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "articles": [
                {
                    "article_num": a.article_num,
                    "title": a.title,
                    "text": a.text,
                    "page": a.page,
                    "paragraphs": [
                        {
                            "paragraph_num": p.paragraph_num,
                            "text": p.text,
                            "subclauses": [
                                {
                                    "subclause_num": s.subclause_num,
                                    "text": s.text,
                                }
                                for s in p.subclauses
                            ]
                        }
                        for p in a.paragraphs
                    ]
                }
                for a in self.articles
            ],
            "total_articles": self.total_articles,
            "total_paragraphs": self.total_paragraphs,
            "total_subclauses": self.total_subclauses,
        }


class LegalStructureParser:
    """한국 법률 문서 구조 파싱"""

    # 정규표현식 패턴
    ARTICLE_PATTERN = re.compile(r'제(\d+)조\s*(?:\[([^\]]+)\])?')
    PARAGRAPH_PATTERN = re.compile(r'^([①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])\s+(.+)', re.MULTILINE)
    NUMBERED_SUBCLAUSE = re.compile(r'^(\d+)\.\s+(.+)', re.MULTILINE)
    LETTER_SUBCLAUSE = re.compile(r'^([가나다라마바사아자차카타파하])\.\s+(.+)', re.MULTILINE)
    EXCEPTION_PATTERN = re.compile(r'(다만|단서|제외하고|단)')

    def __init__(self):
        """Initialize parser"""
        pass

    def parse_text(self, text: str) -> ParsedDocument:
        """
        법률 문서 텍스트 파싱

        Args:
            text: 추출된 전체 텍스트

        Returns:
            ParsedDocument: 파싱된 문서 구조
        """
        logger.info("Parsing legal document structure...")

        articles = self._extract_articles(text)
        
        total_paragraphs = sum(len(a.paragraphs) for a in articles)
        total_subclauses = sum(
            len(p.subclauses) 
            for a in articles 
            for p in a.paragraphs
        )

        result = ParsedDocument(
            articles=articles,
            total_articles=len(articles),
            total_paragraphs=total_paragraphs,
            total_subclauses=total_subclauses,
        )

        logger.info(
            f"Parsed {result.total_articles} articles, "
            f"{result.total_paragraphs} paragraphs, "
            f"{result.total_subclauses} subclauses"
        )

        return result

    def _extract_articles(self, text: str) -> List[Article]:
        """조 추출"""
        articles = []

        # 조 단위로 분할
        article_matches = list(self.ARTICLE_PATTERN.finditer(text))

        for i, match in enumerate(article_matches):
            article_num_int = match.group(1)
            article_title = match.group(2) or ""
            
            # 조의 시작 위치
            start_pos = match.start()
            
            # 다음 조의 시작 위치 (없으면 텍스트 끝)
            end_pos = article_matches[i + 1].start() if i + 1 < len(article_matches) else len(text)
            
            # 조 전체 텍스트
            article_text = text[start_pos:end_pos].strip()
            
            # 조 객체 생성
            article = Article(
                article_num=f"제{article_num_int}조",
                title=article_title,
                text=article_text,
            )
            
            # 항 추출
            article.paragraphs = self._extract_paragraphs(article_text)
            
            articles.append(article)
            
            logger.debug(
                f"Article {article.article_num} '{article.title}': "
                f"{len(article.paragraphs)} paragraphs"
            )

        return articles

    def _extract_paragraphs(self, article_text: str) -> List[Paragraph]:
        """항 추출 (①, ②, ③)"""
        paragraphs = []

        # 항 패턴 찾기
        paragraph_matches = list(self.PARAGRAPH_PATTERN.finditer(article_text))

        if not paragraph_matches:
            # 항이 없는 경우 - 전체를 하나의 항으로 처리
            # (제목 다음부터 내용)
            lines = article_text.split('\n')
            if len(lines) > 1:
                content = '\n'.join(lines[1:]).strip()
                if content:
                    para = Paragraph(
                        paragraph_num="본문",
                        text=content,
                    )
                    para.subclauses = self._extract_subclauses(content)
                    paragraphs.append(para)
            return paragraphs

        for i, match in enumerate(paragraph_matches):
            para_num = match.group(1)
            
            # 항의 시작 위치
            start_pos = match.start()
            
            # 다음 항의 시작 위치
            end_pos = paragraph_matches[i + 1].start() if i + 1 < len(paragraph_matches) else len(article_text)
            
            # 항 텍스트
            para_text = article_text[start_pos:end_pos].strip()
            
            # 항 객체 생성
            paragraph = Paragraph(
                paragraph_num=para_num,
                text=para_text,
            )
            
            # 하위 조항 추출
            paragraph.subclauses = self._extract_subclauses(para_text)
            
            paragraphs.append(paragraph)

        return paragraphs

    def _extract_subclauses(self, paragraph_text: str) -> List[Subclause]:
        """하위 조항 추출 (1., 2., 가., 나.)"""
        subclauses = []

        # 숫자 하위 조항 (1., 2., 3.)
        numbered_matches = list(self.NUMBERED_SUBCLAUSE.finditer(paragraph_text))
        
        for match in numbered_matches:
            num = match.group(1)
            text = match.group(2).strip()
            
            subclauses.append(Subclause(
                subclause_num=f"{num}.",
                text=text,
            ))

        # 문자 하위 조항 (가., 나., 다.)
        letter_matches = list(self.LETTER_SUBCLAUSE.finditer(paragraph_text))
        
        for match in letter_matches:
            letter = match.group(1)
            text = match.group(2).strip()
            
            subclauses.append(Subclause(
                subclause_num=f"{letter}.",
                text=text,
            ))

        return subclauses

    def find_exceptions(self, text: str) -> List[Tuple[int, str]]:
        """
        예외 조항 찾기 (다만, 단서, 제외하고 등)

        Args:
            text: 검색할 텍스트

        Returns:
            List[Tuple[int, str]]: (위치, 매칭 텍스트) 리스트
        """
        exceptions = []
        
        for match in self.EXCEPTION_PATTERN.finditer(text):
            exceptions.append((match.start(), match.group(0)))
        
        return exceptions


# Singleton instance
_legal_parser: Optional[LegalStructureParser] = None


def get_legal_parser() -> LegalStructureParser:
    """법률 구조 파서 싱글톤 인스턴스"""
    global _legal_parser
    if _legal_parser is None:
        _legal_parser = LegalStructureParser()
    return _legal_parser
