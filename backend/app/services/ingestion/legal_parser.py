"""
Korean Legal Document Structure Parser

Parses Korean insurance policy documents following legal document conventions:
- Articles: 제1조, 제2조, ...
- Paragraphs: ①, ②, ③, ...
- Subclauses: 1., 2., 가., 나., 다., ...
- Exception clauses: 다만, 단서, 제외하고, ...
"""
import re
from typing import List, Tuple, Optional
from app.models.document import (
    Article,
    Paragraph,
    Subclause,
    ParsedDocument,
    BoundingBox,
)


class LegalStructureParser:
    """Parser for Korean legal document structure"""

    # Regex patterns for Korean legal structure
    ARTICLE_PATTERN = r'제\s*(\d+)\s*조\s*(?:\[([^\]]+)\])?'  # 제1조 [제목]
    PARAGRAPH_PATTERN = r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]'  # Circled numbers
    SUBCLAUSE_NUMBER_PATTERN = r'(?:^|\n)\s*(\d+)\s*\.\s+'  # 1. 2. 3. ...
    SUBCLAUSE_LETTER_PATTERN = r'(?:^|\n)\s*([가-힣])\s*\.\s+'  # 가. 나. 다. ...
    EXCEPTION_KEYWORDS = ['다만', '단서', '제외하고', '제외한', '단,']

    def __init__(self):
        self.article_regex = re.compile(self.ARTICLE_PATTERN)
        self.paragraph_regex = re.compile(self.PARAGRAPH_PATTERN)
        self.subclause_number_regex = re.compile(self.SUBCLAUSE_NUMBER_PATTERN)
        self.subclause_letter_regex = re.compile(self.SUBCLAUSE_LETTER_PATTERN)

    def parse(self, ocr_text: str, total_pages: int) -> ParsedDocument:
        """
        Parse Korean legal document structure from OCR text

        Args:
            ocr_text: Full text extracted from OCR
            total_pages: Total number of pages in document

        Returns:
            ParsedDocument with hierarchical structure
        """
        errors = []
        warnings = []

        try:
            # Step 1: Extract all articles
            articles = self._extract_articles(ocr_text, errors, warnings)

            # Step 2: Calculate parsing confidence
            confidence = self._calculate_confidence(articles, ocr_text, errors, warnings)

            return ParsedDocument(
                articles=articles,
                total_pages=total_pages,
                parsing_confidence=confidence,
                parsing_errors=errors,
                parsing_warnings=warnings,
            )

        except Exception as e:
            errors.append(f"Critical parsing error: {str(e)}")
            return ParsedDocument(
                articles=[],
                total_pages=total_pages,
                parsing_confidence=0.0,
                parsing_errors=errors,
                parsing_warnings=warnings,
            )

    def _extract_articles(
        self, text: str, errors: List[str], warnings: List[str]
    ) -> List[Article]:
        """Extract all articles from text"""
        articles = []

        # Find all article matches
        article_matches = list(self.article_regex.finditer(text))

        if not article_matches:
            errors.append("No articles found in document")
            return articles

        for i, match in enumerate(article_matches):
            try:
                article_num_raw = match.group(1)
                article_title = match.group(2) if match.group(2) else ""
                article_num = f"제{article_num_raw}조"
                start_pos = match.start()

                # Determine end position (start of next article or end of text)
                if i < len(article_matches) - 1:
                    end_pos = article_matches[i + 1].start()
                else:
                    end_pos = len(text)

                # Extract article text
                article_text = text[start_pos:end_pos]

                # Estimate page number (rough approximation)
                # Assume ~2000 characters per page
                page = (start_pos // 2000) + 1

                # Parse paragraphs within article
                paragraphs = self._extract_paragraphs(
                    article_text, start_pos, errors, warnings
                )

                article = Article(
                    article_num=article_num,
                    title=article_title,
                    page=page,
                    position=start_pos,
                    paragraphs=paragraphs,
                    raw_text=article_text.strip(),
                )

                articles.append(article)

            except Exception as e:
                errors.append(f"Error parsing article at position {match.start()}: {str(e)}")

        return articles

    def _extract_paragraphs(
        self, article_text: str, article_start_pos: int, errors: List[str], warnings: List[str]
    ) -> List[Paragraph]:
        """Extract paragraphs from article text"""
        paragraphs = []

        # Find all paragraph markers
        paragraph_matches = list(self.paragraph_regex.finditer(article_text))

        if not paragraph_matches:
            # No explicit paragraphs - treat entire article as single paragraph
            warnings.append(f"No paragraphs found in article at position {article_start_pos}")
            return paragraphs

        for i, match in enumerate(paragraph_matches):
            try:
                para_num = match.group(0)
                start_pos = match.start()
                abs_position = article_start_pos + start_pos

                # Determine end position
                if i < len(paragraph_matches) - 1:
                    end_pos = paragraph_matches[i + 1].start()
                else:
                    end_pos = len(article_text)

                # Extract paragraph text
                para_text = article_text[start_pos:end_pos].strip()

                # Check for exception keywords
                has_exception, exception_keywords = self._check_exceptions(para_text)

                # Extract subclauses
                subclauses = self._extract_subclauses(
                    para_text, abs_position, errors, warnings
                )

                paragraph = Paragraph(
                    paragraph_num=para_num,
                    text=para_text,
                    position=abs_position,
                    subclauses=subclauses,
                    has_exception=has_exception,
                    exception_keywords=exception_keywords,
                )

                paragraphs.append(paragraph)

            except Exception as e:
                errors.append(f"Error parsing paragraph at position {match.start()}: {str(e)}")

        return paragraphs

    def _extract_subclauses(
        self, para_text: str, para_start_pos: int, errors: List[str], warnings: List[str]
    ) -> List[Subclause]:
        """Extract subclauses from paragraph text"""
        subclauses = []

        # Try number subclauses first (1. 2. 3. ...)
        number_matches = list(self.subclause_number_regex.finditer(para_text))
        if number_matches:
            for i, match in enumerate(number_matches):
                try:
                    subclause_num = match.group(1)
                    start_pos = match.end()
                    abs_position = para_start_pos + start_pos

                    # Determine end position
                    if i < len(number_matches) - 1:
                        end_pos = number_matches[i + 1].start()
                    else:
                        end_pos = len(para_text)

                    subclause_text = para_text[start_pos:end_pos].strip()

                    subclause = Subclause(
                        subclause_num=subclause_num,
                        text=subclause_text,
                        position=abs_position,
                    )
                    subclauses.append(subclause)

                except Exception as e:
                    errors.append(f"Error parsing number subclause: {str(e)}")

        # Try letter subclauses (가. 나. 다. ...)
        letter_matches = list(self.subclause_letter_regex.finditer(para_text))
        if letter_matches:
            for i, match in enumerate(letter_matches):
                try:
                    subclause_num = match.group(1)
                    start_pos = match.end()
                    abs_position = para_start_pos + start_pos

                    # Determine end position
                    if i < len(letter_matches) - 1:
                        end_pos = letter_matches[i + 1].start()
                    else:
                        end_pos = len(para_text)

                    subclause_text = para_text[start_pos:end_pos].strip()

                    subclause = Subclause(
                        subclause_num=subclause_num,
                        text=subclause_text,
                        position=abs_position,
                    )
                    subclauses.append(subclause)

                except Exception as e:
                    errors.append(f"Error parsing letter subclause: {str(e)}")

        return subclauses

    def _check_exceptions(self, text: str) -> Tuple[bool, List[str]]:
        """Check if text contains exception keywords"""
        found_keywords = []
        for keyword in self.EXCEPTION_KEYWORDS:
            if keyword in text:
                found_keywords.append(keyword)
        return len(found_keywords) > 0, found_keywords

    def _calculate_confidence(
        self,
        articles: List[Article],
        text: str,
        errors: List[str],
        warnings: List[str],
    ) -> float:
        """
        Calculate overall parsing confidence score

        Factors:
        - Number of articles found
        - Ratio of articles with paragraphs
        - Number of errors/warnings
        - Text coverage (how much of original text was parsed)
        """
        if not articles:
            return 0.0

        confidence = 1.0

        # Penalize for errors
        if errors:
            confidence -= min(0.5, len(errors) * 0.1)

        # Penalize for warnings
        if warnings:
            confidence -= min(0.2, len(warnings) * 0.05)

        # Check article structure quality
        articles_with_paragraphs = sum(1 for a in articles if a.paragraphs)
        if articles:
            paragraph_ratio = articles_with_paragraphs / len(articles)
            if paragraph_ratio < 0.5:
                confidence -= 0.2
            elif paragraph_ratio < 0.8:
                confidence -= 0.1

        # Ensure confidence is in [0, 1]
        return max(0.0, min(1.0, confidence))
