"""
Document parsing data models for Korean legal structure
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box coordinates [x1, y1, x2, y2]"""
    x1: float
    y1: float
    x2: float
    y2: float

    @classmethod
    def from_list(cls, coords: List[float]) -> "BoundingBox":
        """Create BoundingBox from list [x1, y1, x2, y2]"""
        if len(coords) != 4:
            raise ValueError("Bounding box must have exactly 4 coordinates")
        return cls(x1=coords[0], y1=coords[1], x2=coords[2], y2=coords[3])

    def to_list(self) -> List[float]:
        """Convert to list format"""
        return [self.x1, self.y1, self.x2, self.y2]


class Subclause(BaseModel):
    """Subclause within a paragraph (1., 2., 가., 나., etc.)"""
    subclause_num: str = Field(..., description="Subclause number (1, 2, 가, 나, etc.)")
    text: str = Field(..., description="Subclause text content")
    position: int = Field(..., description="Character position in original text")


class Paragraph(BaseModel):
    """Paragraph within an article (①, ②, ③, etc.)"""
    paragraph_num: str = Field(..., description="Paragraph number (①, ②, ③, etc.)")
    text: str = Field(..., description="Paragraph text content")
    position: int = Field(..., description="Character position in original text")
    subclauses: List[Subclause] = Field(default_factory=list, description="Subclauses within paragraph")
    has_exception: bool = Field(default=False, description="Whether paragraph contains exception clause")
    exception_keywords: List[str] = Field(default_factory=list, description="Exception keywords found (다만, 단서, etc.)")


class Article(BaseModel):
    """Article in Korean legal document (제N조)"""
    article_num: str = Field(..., description="Article number (제1조, 제2조, etc.)")
    title: str = Field(..., description="Article title")
    page: int = Field(..., description="Page number where article appears")
    position: int = Field(..., description="Character position in original text")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box coordinates")
    paragraphs: List[Paragraph] = Field(default_factory=list, description="Paragraphs within article")
    raw_text: str = Field(..., description="Original raw text of article")


class ParsedDocument(BaseModel):
    """Parsed Korean legal document with hierarchical structure"""
    articles: List[Article] = Field(default_factory=list, description="All articles in document")
    total_pages: int = Field(..., description="Total number of pages")
    parsing_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall parsing confidence score")
    parsing_errors: List[str] = Field(default_factory=list, description="List of parsing errors encountered")
    parsing_warnings: List[str] = Field(default_factory=list, description="List of parsing warnings")

    def get_article_by_num(self, article_num: str) -> Optional[Article]:
        """Get article by article number"""
        for article in self.articles:
            if article.article_num == article_num:
                return article
        return None

    def get_total_paragraphs(self) -> int:
        """Get total number of paragraphs across all articles"""
        return sum(len(article.paragraphs) for article in self.articles)

    def get_total_subclauses(self) -> int:
        """Get total number of subclauses across all articles"""
        total = 0
        for article in self.articles:
            for paragraph in article.paragraphs:
                total += len(paragraph.subclauses)
        return total
