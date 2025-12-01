# Story 1.3 - Legal Structure Parsing (완료)
**완료일**: 2025-12-01
**상태**: ✅ 100% 완료
**소요 시간**: ~30분

---

## 개요

한국 법률 문서(보험 약관)의 구조를 파싱하여 계층 구조 트리를 생성하는 서비스를 구현했습니다.

---

## 완료된 작업

### 1. Legal Structure Parser 구현
- **파일**: `backend/app/services/legal_structure_parser.py` (250줄)

**주요 클래스**:

#### A. Subclause (하위 조항)
- 숫자 조항: 1., 2., 3.
- 문자 조항: 가., 나., 다.
- 텍스트 내용

#### B. Paragraph (항)
- 항 번호: ①, ②, ③
- 항 텍스트
- 하위 조항 목록

#### C. Article (조)
- 조 번호: 제1조, 제2조
- 조 제목: [보험금 지급]
- 항 목록
- 페이지 번호

#### D. ParsedDocument (전체 문서)
- 조 목록
- 통계 정보

---

## 주요 기능

### 1. 정규표현식 패턴

```python
# 조 패턴
ARTICLE_PATTERN = r'제(\d+)조\s*(?:\[([^\]]+)\])?'

# 항 패턴
PARAGRAPH_PATTERN = r'^([①②③④⑤⑥⑦⑧⑨⑩])\s+(.+)'

# 숫자 하위 조항
NUMBERED_SUBCLAUSE = r'^(\d+)\.\s+(.+)'

# 문자 하위 조항
LETTER_SUBCLAUSE = r'^([가나다라마바사아자차])\.\s+(.+)'

# 예외 조항
EXCEPTION_PATTERN = r'(다만|단서|제외하고|단)'
```

### 2. 계층 구조 파싱

```python
from app.services.legal_structure_parser import get_legal_parser

parser = get_legal_parser()
result = parser.parse_text(text)

# 계층 구조 순회
for article in result.articles:
    print(f"{article.article_num} [{article.title}]")
    for paragraph in article.paragraphs:
        print(f"  {paragraph.paragraph_num}")
        for subclause in paragraph.subclauses:
            print(f"    {subclause.subclause_num} {subclause.text}")
```

### 3. 파싱 결과 예시

**입력 텍스트**:
```
제10조 [보험금 지급]
① 회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때 다음과 같이 보험금을 지급합니다.
1. 일반암(C77 제외): 1억원
2. 소액암(C77): 1천만원
② 다만, 계약일로부터 90일 이내 진단 확정된 경우 면책합니다.
```

**파싱 결과**:
```python
{
  "articles": [
    {
      "article_num": "제10조",
      "title": "보험금 지급",
      "paragraphs": [
        {
          "paragraph_num": "①",
          "text": "회사는 피보험자가...",
          "subclauses": [
            {"subclause_num": "1.", "text": "일반암(C77 제외): 1억원"},
            {"subclause_num": "2.", "text": "소액암(C77): 1천만원"}
          ]
        },
        {
          "paragraph_num": "②",
          "text": "다만, 계약일로부터..."
        }
      ]
    }
  ],
  "total_articles": 1,
  "total_paragraphs": 2,
  "total_subclauses": 2
}
```

---

## 테스트 결과

**테스트 케이스**:
```
제10조 [보험금 지급] - 2개 항, 2개 하위 조항
제11조 [보험료 납입] - 2개 항
```

**결과**:
```
✅ Parsed 2 articles
✅ Parsed 4 paragraphs
✅ Parsed 2 subclauses
```

---

## 기술 세부사항

### 파싱 알고리즘

1. **조 분할**: 정규표현식으로 제N조 패턴 찾기
2. **항 추출**: 각 조 내에서 ①②③ 패턴 찾기
3. **하위 조항 추출**: 각 항 내에서 1., 2., 가., 나. 패턴 찾기
4. **계층 구조 구축**: Article → Paragraph → Subclause 트리 생성

### 특수 패턴 처리

- **예외 조항**: "다만", "단서", "제외하고" 패턴 감지
- **제목 없는 조**: 제목이 없어도 파싱 가능
- **항 없는 조**: 항이 없는 경우 "본문"으로 처리

---

## Sprint 2 완료!

**Sprint 2 목표**: 8 스토리 포인트

- ✅ Story 1.2 (3 pts) - Text Extraction
- ✅ Story 1.3 (5 pts) - Legal Structure Parsing

**현재 진행률**: ✅ **100% (8/8 pts) 완료!**

---

## 전체 프로젝트 진행 상황

- **완료된 스토리**: 4개 (1.0, 1.1, 1.2, 1.3)
- **완료된 스토리 포인트**: 16 / 150 (10.7%)
- **Sprint 1**: ✅ 100% 완료 (8/8 pts)
- **Sprint 2**: ✅ 100% 완료 (8/8 pts)

---

## 다음 단계 (Sprint 3)

**Sprint 3: Knowledge Graph Construction (Dec 30 - Jan 12)**

### Story 1.4: Neo4j Graph Construction (5 pts)
- 파싱된 구조를 Neo4j 그래프로 변환
- 노드: Article, Paragraph, Subclause
- 관계: CONTAINS, REFERENCES
- 예상 소요 시간: 3-4시간

### Story 1.5: Embedding Generation (3 pts)
- OpenAI/Azure API 통합
- 텍스트 임베딩 생성
- 벡터 저장
- 예상 소요 시간: 2-3시간

---

**작성자**: Claude
**작성일**: 2025-12-01
**Story Status**: DONE
**Sprint Status**: SPRINT 2 COMPLETE! 🎉
