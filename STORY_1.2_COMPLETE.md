# Story 1.2 - PDF Text Extraction (완료)
**완료일**: 2025-12-01
**상태**: ✅ 100% 완료
**소요 시간**: ~30분

---

## 개요

PyMuPDF 라이브러리를 사용하여 PDF 파일에서 텍스트를 추출하는 서비스를 구현했습니다.

---

## 완료된 작업

### 1. PyMuPDF 라이브러리 설치
- **라이브러리**: PyMuPDF (fitz) v1.26.6
- **용도**: PDF 텍스트 추출, 메타데이터 읽기
- **설치 완료**: ✅

### 2. PDF 텍스트 추출 서비스 구현
- **파일**: `backend/app/services/pdf_text_extractor.py` (190줄)

**주요 클래스**:

#### A. PDFPage
단일 PDF 페이지 정보를 담는 데이터 클래스
- `page_num`: 페이지 번호 (1-indexed)
- `text`: 페이지 텍스트
- `width`, `height`: 페이지 크기 (포인트)
- `char_count`: 문자 수

#### B. PDFExtractionResult
전체 추출 결과를 담는 클래스
- `total_pages`: 전체 페이지 수
- `total_chars`: 전체 문자 수
- `pages`: 페이지 목록
- `full_text`: 전체 텍스트
- `metadata`: PDF 메타데이터

#### C. PDFTextExtractor
실제 추출 로직을 수행하는 메인 클래스
- `extract_text_from_file(pdf_path, max_pages)`: 파일에서 추출
- 페이지별 텍스트 분리
- PDF 메타데이터 추출 (제목, 저자, 생성일 등)
- 페이지 크기 정보 수집

---

## 주요 기능

### 1. 페이지별 텍스트 추출
```python
from app.services.pdf_text_extractor import get_pdf_extractor

extractor = get_pdf_extractor()
result = extractor.extract_text_from_file("policy.pdf")

# 페이지별 접근
for page in result.pages:
    print(f"Page {page.page_num}: {page.char_count} chars")
    print(page.text[:100])  # 처음 100자
```

### 2. 메타데이터 추출
```python
result = extractor.extract_text_from_file("policy.pdf")

# PDF 메타데이터
print(result.metadata)
# {
#   "title": "암보험 약관",
#   "author": "삼성생명",
#   "creation_date": "D:20230101120000",
#   ...
# }
```

### 3. 전체 텍스트 접근
```python
# 모든 페이지 텍스트 결합
full_text = result.full_text
print(f"Total: {result.total_pages} pages, {result.total_chars} characters")
```

---

## 기술 세부사항

### PDF 열기 및 처리
```python
import fitz  # PyMuPDF

doc = fitz.open(pdf_path)  # 파일 열기
page = doc[page_num]       # 페이지 접근
text = page.get_text()     # 텍스트 추출
rect = page.rect           # 페이지 크기
doc.close()                # 문서 닫기
```

### 메타데이터 추출
```python
metadata = {
    "title": doc.metadata.get("title", ""),
    "author": doc.metadata.get("author", ""),
    "subject": doc.metadata.get("subject", ""),
    "keywords": doc.metadata.get("keywords", ""),
    "creator": doc.metadata.get("creator", ""),
    "producer": doc.metadata.get("producer", ""),
    "creation_date": doc.metadata.get("creationDate", ""),
    "mod_date": doc.metadata.get("modDate", ""),
}
```

### 싱글톤 패턴
```python
_pdf_extractor = None

def get_pdf_extractor():
    """PDF 추출기 싱글톤 인스턴스"""
    global _pdf_extractor
    if _pdf_extractor is None:
        _pdf_extractor = PDFTextExtractor()
    return _pdf_extractor
```

---

## 성능 특징

### 장점
- ✅ 빠른 텍스트 추출 (PyMuPDF는 C 기반으로 매우 빠름)
- ✅ 페이지별 분리 저장
- ✅ 메타데이터 자동 추출
- ✅ 메모리 효율적 (페이지별 처리)
- ✅ 외부 API 불필요 (로컬 처리)

### 제한사항
- ⚠️ OCR 없음 (스캔된 이미지 PDF는 추출 불가)
- ⚠️ 표(table) 구조 파싱 없음
- ⚠️ 레이아웃 정보 제한적

---

## 다음 단계 (Story 1.3)

**Story 1.3: Legal Structure Parsing**
- 추출된 텍스트에서 법적 구조 파싱 (제N조, ①항 등)
- 계층 구조 트리 생성
- 조항 간 참조 관계 파악

**연계 작업**:
- Story 1.2에서 추출한 텍스트를 입력으로 사용
- 정규표현식 + LLM 기반 구조 파싱
- 예상 소요 시간: 3-4시간

---

## Sprint 2 진행 상황

**Sprint 2 목표**: 8 스토리 포인트

- ✅ Story 1.2 (3 pts) - Text Extraction - **완료**
- 📋 Story 1.3 (5 pts) - Header/Section Extraction - 다음 작업

**현재 진행률**: 37.5% (3/8 pts)

---

## 전체 프로젝트 진행 상황

- **완료된 스토리**: 3개 (Story 1.0, 1.1, 1.2)
- **완료된 스토리 포인트**: 11 / 150 (7.3%)
- **Sprint 1**: ✅ 100% 완료 (8/8 pts)
- **Sprint 2**: 🔄 진행 중 (3/8 pts)

---

**작성자**: Claude
**작성일**: 2025-12-01
**Story Status**: DONE
