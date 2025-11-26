"""
Unit tests for LegalStructureParser
"""
import pytest
from app.services.ingestion.legal_parser import LegalStructureParser
from app.models.document import Article, Paragraph, Subclause


class TestLegalStructureParser:
    """Test suite for Korean legal document parsing"""

    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return LegalStructureParser()

    def test_simple_article_parsing(self, parser):
        """Test parsing a simple article with title"""
        text = """
        제1조 [보험금의 지급]
        회사는 피보험자가 보험기간 중 암으로 진단확정되었을 때 보험금을 지급합니다.
        """
        result = parser.parse(text, total_pages=1)

        assert len(result.articles) == 1
        assert result.articles[0].article_num == "제1조"
        assert result.articles[0].title == "보험금의 지급"
        assert result.parsing_confidence > 0.5

    def test_article_with_paragraphs(self, parser):
        """Test parsing article with multiple paragraphs"""
        text = """
        제10조 [암진단급여금 지급]
        ① 회사는 피보험자가 보험기간 중 암으로 진단확정되었을 때 보험금을 지급합니다.
        ② 제1항의 암진단 급여금은 최초 1회에 한하여 지급합니다.
        ③ 피보험자가 사망한 경우 이 계약은 소멸되며 보험금을 지급하지 않습니다.
        """
        result = parser.parse(text, total_pages=1)

        assert len(result.articles) == 1
        article = result.articles[0]
        assert article.article_num == "제10조"
        assert len(article.paragraphs) == 3
        assert article.paragraphs[0].paragraph_num == "①"
        assert article.paragraphs[1].paragraph_num == "②"
        assert article.paragraphs[2].paragraph_num == "③"

    def test_paragraph_with_exception_clause(self, parser):
        """Test detection of exception clauses (다만, 단서)"""
        text = """
        제5조 [면책기간]
        ① 회사는 보험금을 지급합니다. 다만, 계약일로부터 90일 이내에 진단확정된 경우는 제외합니다.
        """
        result = parser.parse(text, total_pages=1)

        assert len(result.articles) == 1
        article = result.articles[0]
        assert len(article.paragraphs) == 1
        paragraph = article.paragraphs[0]
        assert paragraph.has_exception is True
        assert "다만" in paragraph.exception_keywords

    def test_subclauses_number_format(self, parser):
        """Test parsing numbered subclauses (1. 2. 3.)"""
        text = """
        제8조 [보장내용]
        ① 회사는 다음의 경우 보험금을 지급합니다.
        1. 일반암(C77 제외): 1억원
        2. 소액암(C77): 1천만원
        3. 고액암(C18-C20): 2억원
        """
        result = parser.parse(text, total_pages=1)

        article = result.articles[0]
        paragraph = article.paragraphs[0]
        assert len(paragraph.subclauses) == 3
        assert paragraph.subclauses[0].subclause_num == "1"
        assert paragraph.subclauses[1].subclause_num == "2"
        assert paragraph.subclauses[2].subclause_num == "3"

    def test_subclauses_letter_format(self, parser):
        """Test parsing letter subclauses (가. 나. 다.)"""
        text = """
        제9조 [면책사유]
        ① 다음의 경우 보험금을 지급하지 않습니다.
        가. 피보험자의 고의로 인한 사고
        나. 전쟁, 내란, 폭동으로 인한 사고
        다. 핵연료물질에 의한 사고
        """
        result = parser.parse(text, total_pages=1)

        article = result.articles[0]
        paragraph = article.paragraphs[0]
        assert len(paragraph.subclauses) == 3
        assert paragraph.subclauses[0].subclause_num == "가"
        assert paragraph.subclauses[1].subclause_num == "나"
        assert paragraph.subclauses[2].subclause_num == "다"

    def test_multiple_articles(self, parser):
        """Test parsing multiple articles"""
        text = """
        제1조 [목적]
        이 계약은 보험금 지급을 목적으로 합니다.

        제2조 [용어의 정의]
        ① 이 계약에서 사용하는 용어의 뜻은 다음과 같습니다.
        1. 암: 악성신생물을 말합니다.
        2. 진단확정: 의사의 진단을 말합니다.

        제3조 [보험금의 지급]
        ① 회사는 보험금을 지급합니다.
        """
        result = parser.parse(text, total_pages=1)

        assert len(result.articles) == 3
        assert result.articles[0].article_num == "제1조"
        assert result.articles[1].article_num == "제2조"
        assert result.articles[2].article_num == "제3조"

        # Check article 2 has subclauses
        article2 = result.articles[1]
        assert len(article2.paragraphs) == 1
        assert len(article2.paragraphs[0].subclauses) == 2

    def test_article_without_title(self, parser):
        """Test parsing article without title in brackets"""
        text = """
        제15조
        회사는 보험금을 지급합니다.
        """
        result = parser.parse(text, total_pages=1)

        assert len(result.articles) == 1
        assert result.articles[0].article_num == "제15조"
        assert result.articles[0].title == ""

    def test_article_without_paragraphs(self, parser):
        """Test parsing article without paragraph markers"""
        text = """
        제20조 [기타사항]
        이 계약에 정하지 않은 사항은 일반 관례에 따릅니다.
        """
        result = parser.parse(text, total_pages=1)

        assert len(result.articles) == 1
        article = result.articles[0]
        # No explicit paragraphs - should trigger warning
        assert len(result.parsing_warnings) > 0

    def test_complex_document(self, parser):
        """Test parsing complex document with all elements"""
        text = """
        제10조 [암진단급여금 지급]
        ① 회사는 피보험자가 다음 각 호의 암으로 진단확정되었을 때 보험금을 지급합니다.
        1. 일반암(C77 제외): 1억원
        2. 소액암(C77): 1천만원
        3. 고액암: 2억원
        ② 제1항의 암진단급여금은 최초 1회에 한하여 지급합니다. 다만, 갱신 시에는 재지급할 수 있습니다.
        ③ 피보험자가 사망한 경우 이 계약은 소멸됩니다.

        제11조 [면책기간]
        ① 회사는 계약일로부터 90일 이내에 진단확정된 암에 대해서는 보험금을 지급하지 않습니다.
        ② 제1항에도 불구하고 갱신계약의 경우는 면책기간을 적용하지 않습니다.
        """
        result = parser.parse(text, total_pages=1)

        assert len(result.articles) == 2

        # Check first article
        article1 = result.articles[0]
        assert article1.article_num == "제10조"
        assert article1.title == "암진단급여금 지급"
        assert len(article1.paragraphs) == 3

        # Check paragraph with subclauses
        para1 = article1.paragraphs[0]
        assert len(para1.subclauses) == 3

        # Check paragraph with exception
        para2 = article1.paragraphs[1]
        assert para2.has_exception is True
        assert "다만" in para2.exception_keywords

        # Check second article
        article2 = result.articles[1]
        assert article2.article_num == "제11조"
        assert len(article2.paragraphs) == 2

    def test_empty_text(self, parser):
        """Test parsing empty text"""
        result = parser.parse("", total_pages=0)

        assert len(result.articles) == 0
        assert result.parsing_confidence == 0.0
        assert len(result.parsing_errors) > 0

    def test_text_with_no_articles(self, parser):
        """Test parsing text with no articles"""
        text = """
        이것은 일반 텍스트입니다.
        약관이 아닙니다.
        제N조 형식의 조항이 없습니다.
        """
        result = parser.parse(text, total_pages=1)

        assert len(result.articles) == 0
        assert result.parsing_confidence == 0.0
        assert len(result.parsing_errors) > 0

    def test_malformed_article_number(self, parser):
        """Test handling malformed article numbers"""
        text = """
        제 1 조 [띄어쓰기 있음]
        정상적인 내용입니다.

        제2조[띄어쓰기 없음]
        정상적인 내용입니다.

        제3조 [정상]
        정상적인 내용입니다.
        """
        result = parser.parse(text, total_pages=1)

        # Should handle flexible spacing
        assert len(result.articles) >= 2  # At least some should parse

    def test_exception_keyword_variations(self, parser):
        """Test detection of various exception keywords"""
        text = """
        제1조 [테스트]
        ① 다만, 예외가 있습니다.
        ② 단서가 있습니다.
        ③ 제외하고 다른 경우
        ④ 제외한 경우
        ⑤ 단, 특별한 경우
        """
        result = parser.parse(text, total_pages=1)

        article = result.articles[0]
        exceptions_count = sum(1 for p in article.paragraphs if p.has_exception)
        assert exceptions_count >= 4  # Should detect most exception keywords

    def test_get_article_by_num(self, parser):
        """Test getting article by number"""
        text = """
        제1조 [첫번째]
        내용
        제2조 [두번째]
        내용
        """
        result = parser.parse(text, total_pages=1)

        article = result.get_article_by_num("제2조")
        assert article is not None
        assert article.title == "두번째"

        # Non-existent article
        assert result.get_article_by_num("제99조") is None

    def test_get_total_counts(self, parser):
        """Test counting total paragraphs and subclauses"""
        text = """
        제1조 [테스트]
        ① 첫 번째 항
        1. 소항 1
        2. 소항 2
        ② 두 번째 항

        제2조 [테스트2]
        ① 첫 번째 항
        가. 소항 가
        나. 소항 나
        다. 소항 다
        """
        result = parser.parse(text, total_pages=1)

        assert result.get_total_paragraphs() == 3
        assert result.get_total_subclauses() == 5  # 2 + 3

    def test_parsing_confidence_calculation(self, parser):
        """Test confidence score calculation"""
        # Good document
        good_text = """
        제1조 [테스트]
        ① 내용
        제2조 [테스트2]
        ① 내용
        """
        good_result = parser.parse(good_text, total_pages=1)
        assert good_result.parsing_confidence > 0.8

        # Poor document (no paragraphs)
        poor_text = """
        제1조 [테스트]
        내용
        제2조 [테스트2]
        내용
        """
        poor_result = parser.parse(poor_text, total_pages=1)
        # Should have lower confidence due to warnings
        assert poor_result.parsing_confidence < good_result.parsing_confidence
