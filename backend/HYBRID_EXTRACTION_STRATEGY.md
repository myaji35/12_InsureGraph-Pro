# 하이브리드 PDF 추출 전략 (Hybrid Extraction Strategy)

## 📋 개요

**하이브리드 방식**은 pdfplumber(무료)와 Upstage(유료)를 **문서 특성에 따라 자동으로 선택**하여 사용하는 전략입니다.

### 핵심 아이디어

```
간단한 문서 → pdfplumber (무료, 빠름)
복잡한 문서 → Upstage (유료, 고품질)
```

이를 통해:
- ✅ **비용 절감**: 50-70% 감소
- ✅ **품질 유지**: 필요한 곳에만 Upstage 사용
- ✅ **자동 판단**: 수동 개입 없이 최적 방법 선택

---

## 🎯 문서 복잡도 판단 기준

### 1. 파일 크기 기반 (1차 필터)

```python
if file_size < 1MB:
    → pdfplumber (간단한 문서일 가능성 높음)
elif file_size > 10MB:
    → Upstage (복잡한 문서일 가능성 높음)
else:
    → 2차 판단으로 이동
```

### 2. 첫 페이지 샘플링 (2차 필터)

첫 2페이지를 pdfplumber로 빠르게 추출하여 복잡도 평가:

```python
# 첫 2페이지 추출
sample_text = extract_first_pages(pdf, num_pages=2)

# 복잡도 점수 계산
complexity_score = calculate_complexity(sample_text)

if complexity_score >= 70:
    → Upstage (복잡)
else:
    → pdfplumber (간단)
```

### 3. 복잡도 점수 계산 알고리즘

```python
def calculate_complexity(sample_text: str) -> int:
    """
    문서 복잡도 점수 계산 (0-100)

    점수가 높을수록 Upstage 사용 권장
    """
    score = 0

    # 1. 한글 비율 (낮으면 OCR 필요)
    korean_ratio = count_korean(sample_text) / len(sample_text)
    if korean_ratio < 0.3:
        score += 30  # OCR 품질이 낮음

    # 2. 표 패턴 감지
    table_indicators = ['┌', '┐', '│', '─', '┼']
    if any(char in sample_text for char in table_indicators):
        score += 25  # 표가 많음

    # 3. 조항 구조 인식
    articles = len(re.findall(r'제\d+조', sample_text))
    if articles < 3:  # 2페이지에 조항이 3개 미만
        score += 20  # 구조 인식 실패 가능

    # 4. 특수문자 비율
    special_chars = count_special_chars(sample_text)
    special_ratio = special_chars / len(sample_text)
    if special_ratio > 0.3:
        score += 15  # 레이아웃 깨짐 가능

    # 5. 텍스트 밀도
    lines = sample_text.split('\n')
    avg_line_length = sum(len(line) for line in lines) / len(lines)
    if avg_line_length < 10:
        score += 10  # 줄이 너무 짧음 (레이아웃 문제)

    return min(score, 100)
```

### 4. 복잡도 점수별 처리 전략

| 점수 | 판단 | 처리 방법 | 예상 비율 |
|------|------|----------|-----------|
| **0-30** | 매우 간단 | pdfplumber | 30% |
| **31-50** | 간단 | pdfplumber | 30% |
| **51-70** | 보통 | pdfplumber + 품질 검증 | 20% |
| **71-85** | 복잡 | Upstage | 15% |
| **86-100** | 매우 복잡 | Upstage + 표 추출 | 5% |

---

## 💡 하이브리드 구현 전략

### 전략 1: 단순 임계값 기반 (Simple Threshold)

**장점:** 구현 간단, 빠른 판단
**단점:** 정확도 낮음

```python
async def extract_hybrid_simple(pdf_url: str, file_size: int):
    """단순 임계값 기반 하이브리드"""

    # 5MB 이상이면 Upstage
    if file_size > 5 * 1024 * 1024:
        return await extract_with_upstage(pdf_url)
    else:
        return await extract_with_pdfplumber(pdf_url)
```

**예상 효과:**
- 비용 절감: 40-50%
- 품질: 중간 (일부 복잡한 문서 놓침)

---

### 전략 2: 샘플링 기반 (Sampling-based) ⭐ 권장

**장점:** 정확도 높음, 비용 효율적
**단점:** 첫 페이지 추출 시간 추가 (1-2초)

```python
async def extract_hybrid_smart(pdf_url: str):
    """샘플링 기반 스마트 하이브리드"""

    # 1. 첫 2페이지만 빠르게 추출 (pdfplumber)
    sample_result = await extract_sample_pages(pdf_url, num_pages=2)
    sample_text = sample_result['text']

    # 2. 복잡도 평가
    complexity = calculate_complexity(sample_text)

    # 3. 복잡도에 따라 선택
    if complexity >= 70:
        logger.info(f"복잡도 {complexity}점 → Upstage 사용")
        return await extract_with_upstage(pdf_url)
    else:
        logger.info(f"복잡도 {complexity}점 → pdfplumber 사용")
        return await extract_with_pdfplumber(pdf_url)
```

**예상 효과:**
- 비용 절감: 60-70%
- 품질: 높음 (복잡한 문서 정확히 감지)

---

### 전략 3: 점진적 업그레이드 (Progressive Upgrade)

**장점:** 최소 비용, 필요 시에만 Upstage
**단점:** 2단계 처리로 시간 증가 가능

```python
async def extract_hybrid_progressive(pdf_url: str):
    """점진적 업그레이드 하이브리드"""

    # 1단계: pdfplumber로 시도
    logger.info("1단계: pdfplumber 시도")
    result = await extract_with_pdfplumber(pdf_url)

    # 2단계: 품질 검증
    quality = calculate_quality_score(result['text'])

    # 3단계: 품질이 낮으면 Upstage로 재처리
    if quality['overall_score'] < 0.7:
        logger.warning(f"품질 낮음 ({quality['overall_score']:.3f}) → Upstage로 재처리")
        result = await extract_with_upstage(pdf_url)
    else:
        logger.info(f"품질 양호 ({quality['overall_score']:.3f}) → pdfplumber 유지")

    return result
```

**예상 효과:**
- 비용 절감: 70-80%
- 품질: 매우 높음 (실패 시에만 Upstage)
- 시간: 일부 문서는 2배 소요

---

### 전략 4: ML 기반 예측 (ML-based Prediction) 🚀 고급

**장점:** 가장 정확한 판단
**단점:** 학습 데이터 필요, 복잡도 높음

```python
class DocumentComplexityPredictor:
    """문서 복잡도 예측 모델"""

    def __init__(self):
        self.model = self.load_model()

    async def predict_complexity(self, pdf_url: str) -> float:
        """
        문서 복잡도 예측 (0.0 ~ 1.0)

        Features:
        - 파일 크기
        - 페이지 수
        - 파일명 패턴
        - 첫 페이지 샘플링 결과
        """
        features = await self.extract_features(pdf_url)
        complexity_score = self.model.predict(features)

        return complexity_score

    async def extract_features(self, pdf_url: str):
        """특징 추출"""
        # 파일 메타데이터
        file_size = await get_file_size(pdf_url)

        # 첫 페이지 샘플링
        sample = await extract_sample_pages(pdf_url, num_pages=1)

        return {
            'file_size': file_size,
            'sample_korean_ratio': calculate_korean_ratio(sample['text']),
            'sample_article_count': count_articles(sample['text']),
            'sample_table_indicators': count_table_indicators(sample['text']),
            # ... 더 많은 특징
        }

async def extract_hybrid_ml(pdf_url: str):
    """ML 기반 하이브리드"""

    predictor = DocumentComplexityPredictor()

    # 복잡도 예측
    complexity = await predictor.predict_complexity(pdf_url)

    # 0.7 이상이면 Upstage
    if complexity >= 0.7:
        return await extract_with_upstage(pdf_url)
    else:
        return await extract_with_pdfplumber(pdf_url)
```

**예상 효과:**
- 비용 절감: 75-85%
- 품질: 최고
- 정확도: 95%+ (학습 후)

---

## 🔧 실제 구현 예시

### 하이브리드 Document Processor 구현

```python
# backend/app/services/hybrid_document_processor.py

from typing import Dict, Any, Optional
from loguru import logger
import re


class HybridDocumentProcessor:
    """
    하이브리드 PDF 추출 프로세서

    문서 특성에 따라 pdfplumber와 Upstage를 자동 선택
    """

    def __init__(
        self,
        strategy: str = "smart",  # simple, smart, progressive, ml
        complexity_threshold: int = 70,
        quality_threshold: float = 0.7
    ):
        self.strategy = strategy
        self.complexity_threshold = complexity_threshold
        self.quality_threshold = quality_threshold

        self.pdfplumber_processor = StreamingPDFProcessor()
        self.upstage_parser = UpstageDocumentParser()

        # 통계 수집
        self.stats = {
            'total_docs': 0,
            'pdfplumber_used': 0,
            'upstage_used': 0,
            'cost_saved': 0.0
        }

    async def process_document(
        self,
        pdf_url: str,
        file_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        문서 처리 (하이브리드 방식)

        Args:
            pdf_url: PDF URL
            file_size: 파일 크기 (선택)

        Returns:
            추출 결과 + 메타데이터
        """
        self.stats['total_docs'] += 1

        # 전략별 처리
        if self.strategy == "simple":
            result = await self._extract_simple(pdf_url, file_size)
        elif self.strategy == "smart":
            result = await self._extract_smart(pdf_url)
        elif self.strategy == "progressive":
            result = await self._extract_progressive(pdf_url)
        elif self.strategy == "ml":
            result = await self._extract_ml(pdf_url)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

        # 통계 업데이트
        self._update_stats(result)

        return result

    async def _extract_simple(
        self,
        pdf_url: str,
        file_size: Optional[int]
    ) -> Dict[str, Any]:
        """전략 1: 단순 임계값"""

        # 파일 크기 확인
        if file_size is None:
            file_size = await self.pdfplumber_processor._get_file_size(pdf_url)

        threshold = 5 * 1024 * 1024  # 5MB

        if file_size > threshold:
            logger.info(f"파일 크기 {file_size/1024/1024:.1f}MB > 5MB → Upstage")
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=True
            )
            result['hybrid_decision'] = 'upstage'
            result['decision_reason'] = f'file_size={file_size/1024/1024:.1f}MB'
        else:
            logger.info(f"파일 크기 {file_size/1024/1024:.1f}MB <= 5MB → pdfplumber")
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=False
            )
            result['hybrid_decision'] = 'pdfplumber'
            result['decision_reason'] = f'file_size={file_size/1024/1024:.1f}MB'

        return result

    async def _extract_smart(self, pdf_url: str) -> Dict[str, Any]:
        """전략 2: 샘플링 기반 (권장)"""

        logger.info("샘플링 기반 복잡도 평가 시작")

        # 1. 첫 2페이지 샘플링
        sample_result = await self._extract_sample_pages(pdf_url, num_pages=2)
        sample_text = sample_result['text']

        # 2. 복잡도 계산
        complexity = self._calculate_complexity(sample_text)

        logger.info(f"복잡도 점수: {complexity}/100")

        # 3. 복잡도에 따라 선택
        if complexity >= self.complexity_threshold:
            logger.info(f"복잡도 {complexity} >= {self.complexity_threshold} → Upstage")
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=True,
                extract_tables=True,
                smart_chunking=True
            )
            result['hybrid_decision'] = 'upstage'
            result['decision_reason'] = f'complexity={complexity}'
        else:
            logger.info(f"복잡도 {complexity} < {self.complexity_threshold} → pdfplumber")
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=False
            )
            result['hybrid_decision'] = 'pdfplumber'
            result['decision_reason'] = f'complexity={complexity}'

        result['complexity_score'] = complexity

        return result

    async def _extract_progressive(self, pdf_url: str) -> Dict[str, Any]:
        """전략 3: 점진적 업그레이드"""

        logger.info("1단계: pdfplumber로 시도")

        # 1단계: pdfplumber 시도
        result = await self.pdfplumber_processor.process_pdf_streaming(
            pdf_url,
            use_upstage=False
        )

        # 2단계: 품질 검증
        quality = self._calculate_quality_score(result['text'])
        overall_quality = quality['overall_score']

        logger.info(f"품질 점수: {overall_quality:.3f}")

        # 3단계: 품질이 낮으면 Upstage로 재처리
        if overall_quality < self.quality_threshold:
            logger.warning(
                f"품질 {overall_quality:.3f} < {self.quality_threshold} → Upstage로 재처리"
            )
            result = await self.pdfplumber_processor.process_pdf_streaming(
                pdf_url,
                use_upstage=True,
                extract_tables=True,
                smart_chunking=True
            )
            result['hybrid_decision'] = 'upstage'
            result['decision_reason'] = f'quality={overall_quality:.3f}'
            result['retry_from'] = 'pdfplumber'
        else:
            logger.info(f"품질 {overall_quality:.3f} >= {self.quality_threshold} → pdfplumber 유지")
            result['hybrid_decision'] = 'pdfplumber'
            result['decision_reason'] = f'quality={overall_quality:.3f}'

        result['quality_score_initial'] = overall_quality

        return result

    async def _extract_ml(self, pdf_url: str) -> Dict[str, Any]:
        """전략 4: ML 기반 (향후 구현)"""

        # TODO: ML 모델 구현
        logger.warning("ML 모델 미구현, smart 전략으로 폴백")
        return await self._extract_smart(pdf_url)

    async def _extract_sample_pages(
        self,
        pdf_url: str,
        num_pages: int = 2
    ) -> Dict[str, Any]:
        """첫 N페이지 샘플링"""

        import httpx
        import io
        import pdfplumber

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            pdf_bytes = response.content

        pdf_file = io.BytesIO(pdf_bytes)

        sample_text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for i, page in enumerate(pdf.pages[:num_pages]):
                text = page.extract_text()
                if text:
                    sample_text += text + "\n"

        return {
            'text': sample_text,
            'pages_sampled': num_pages
        }

    def _calculate_complexity(self, sample_text: str) -> int:
        """복잡도 점수 계산 (0-100)"""

        if not sample_text:
            return 100  # 추출 실패 = 매우 복잡

        score = 0

        # 1. 한글 비율 (낮으면 OCR 품질 문제)
        korean_chars = sum(1 for c in sample_text if ord('가') <= ord(c) <= ord('힣'))
        korean_ratio = korean_chars / len(sample_text) if sample_text else 0

        if korean_ratio < 0.2:
            score += 35  # 한글 거의 없음
        elif korean_ratio < 0.4:
            score += 20  # 한글 적음

        # 2. 표 패턴 감지
        table_indicators = ['┌', '┐', '└', '┘', '│', '─', '┼', '┬', '┴']
        table_count = sum(1 for char in table_indicators if char in sample_text)

        if table_count > 20:
            score += 25  # 표가 많음
        elif table_count > 10:
            score += 15

        # 3. 조항 구조 인식
        articles = len(re.findall(r'제\d+조', sample_text))
        chapters = len(re.findall(r'제\d+장', sample_text))

        if articles < 2 and chapters < 1:
            score += 20  # 구조 인식 실패

        # 4. 특수문자 비율
        special_chars = sum(1 for c in sample_text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / len(sample_text) if sample_text else 0

        if special_ratio > 0.4:
            score += 15  # 특수문자 많음 (레이아웃 깨짐)
        elif special_ratio > 0.3:
            score += 10

        # 5. 텍스트 밀도
        lines = [line for line in sample_text.split('\n') if line.strip()]
        avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0

        if avg_line_length < 10:
            score += 10  # 줄이 너무 짧음

        return min(score, 100)

    def _calculate_quality_score(self, text: str) -> Dict[str, float]:
        """품질 점수 계산"""

        if not text:
            return {'overall_score': 0.0}

        # 한글 비율
        korean_chars = sum(1 for c in text if ord('가') <= ord(c) <= ord('힣'))
        korean_ratio = korean_chars / len(text) if text else 0

        # 구조 점수
        articles = len(re.findall(r'제\d+조', text))
        structure_score = min(articles / 30, 1.0)

        # 종합 점수
        overall = korean_ratio * 0.6 + structure_score * 0.4

        return {
            'korean_ratio': korean_ratio,
            'structure_score': structure_score,
            'overall_score': overall
        }

    def _update_stats(self, result: Dict[str, Any]):
        """통계 업데이트"""

        decision = result.get('hybrid_decision', 'unknown')

        if decision == 'pdfplumber':
            self.stats['pdfplumber_used'] += 1
            # pdfplumber는 무료이므로 비용 절감
            # 평균 페이지당 $0.005 절감 가정
            pages = result.get('total_pages', 0)
            self.stats['cost_saved'] += pages * 0.005
        elif decision == 'upstage':
            self.stats['upstage_used'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """통계 조회"""

        total = self.stats['total_docs']
        pdfplumber_ratio = (self.stats['pdfplumber_used'] / total * 100) if total > 0 else 0
        upstage_ratio = (self.stats['upstage_used'] / total * 100) if total > 0 else 0

        return {
            'total_documents': total,
            'pdfplumber_used': self.stats['pdfplumber_used'],
            'pdfplumber_ratio': f"{pdfplumber_ratio:.1f}%",
            'upstage_used': self.stats['upstage_used'],
            'upstage_ratio': f"{upstage_ratio:.1f}%",
            'estimated_cost_saved': f"${self.stats['cost_saved']:.2f}",
            'strategy': self.strategy
        }


# 사용 예시
async def example_usage():
    """하이브리드 프로세서 사용 예시"""

    # 1. 프로세서 생성
    processor = HybridDocumentProcessor(
        strategy="smart",           # 샘플링 기반 (권장)
        complexity_threshold=70,    # 70점 이상이면 Upstage
        quality_threshold=0.7       # 품질 0.7 미만이면 Upstage
    )

    # 2. 문서 처리
    pdf_urls = [
        "https://example.com/simple.pdf",
        "https://example.com/complex.pdf",
        # ... 더 많은 문서
    ]

    for pdf_url in pdf_urls:
        result = await processor.process_document(pdf_url)

        print(f"문서: {pdf_url}")
        print(f"  선택: {result['hybrid_decision']}")
        print(f"  이유: {result['decision_reason']}")
        print(f"  페이지: {result['total_pages']}")
        print(f"  텍스트: {len(result['text']):,}자")

    # 3. 통계 확인
    stats = processor.get_stats()
    print("\n통계:")
    print(f"  총 문서: {stats['total_documents']}")
    print(f"  pdfplumber 사용: {stats['pdfplumber_used']} ({stats['pdfplumber_ratio']})")
    print(f"  Upstage 사용: {stats['upstage_used']} ({stats['upstage_ratio']})")
    print(f"  예상 절감 비용: {stats['estimated_cost_saved']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
```

---

## 📊 전략별 비교

| 전략 | 비용 절감 | 품질 | 속도 | 복잡도 | 권장 대상 |
|------|----------|------|------|--------|-----------|
| **Simple** | 40-50% | ★★☆ | ★★★ | ★☆☆ | 빠른 구현 필요 |
| **Smart** ⭐ | 60-70% | ★★★ | ★★☆ | ★★☆ | **일반적 사용** |
| **Progressive** | 70-80% | ★★★ | ★☆☆ | ★★☆ | 비용 최소화 |
| **ML-based** 🚀 | 75-85% | ★★★ | ★★★ | ★★★ | 대규모 시스템 |

---

## 💰 비용 시뮬레이션

### 시나리오: 월 10,000페이지 처리

**전체 Upstage 사용 시:**
- 비용: 10,000 × $0.005 = **$50/월**

**하이브리드 (Smart) 사용 시:**
- pdfplumber: 7,000 페이지 (70%) → $0
- Upstage: 3,000 페이지 (30%) → $15
- **총 비용: $15/월** (70% 절감!)

**하이브리드 (Progressive) 사용 시:**
- pdfplumber: 8,000 페이지 (80%) → $0
- Upstage: 2,000 페이지 (20%) → $10
- **총 비용: $10/월** (80% 절감!)

---

## 🎯 실전 팁

### 1. 복잡도 임계값 조정

환경에 맞게 임계값을 조정하세요:

```python
# 비용 절감 우선 (더 많이 pdfplumber 사용)
processor = HybridDocumentProcessor(
    complexity_threshold=85  # 85점 이상만 Upstage
)

# 품질 우선 (더 많이 Upstage 사용)
processor = HybridDocumentProcessor(
    complexity_threshold=60  # 60점 이상 Upstage
)
```

### 2. 문서 유형별 최적화

```python
# 보험약관 (복잡) → 낮은 임계값
insurance_processor = HybridDocumentProcessor(
    complexity_threshold=60
)

# 간단한 공지사항 → 높은 임계값
notice_processor = HybridDocumentProcessor(
    complexity_threshold=90
)
```

### 3. A/B 테스트

```python
# 일부 문서로 테스트하여 최적 임계값 찾기
test_results = await test_different_thresholds(
    sample_pdfs,
    thresholds=[60, 70, 80, 90]
)

optimal_threshold = find_optimal_threshold(test_results)
```

---

## 📈 모니터링 대시보드

### 수집할 메트릭

1. **사용 비율**
   - pdfplumber 사용률
   - Upstage 사용률

2. **비용**
   - 실제 비용
   - 절감 비용

3. **품질**
   - 평균 품질 점수
   - Upstage vs pdfplumber 품질 차이

4. **성능**
   - 평균 처리 시간
   - 에러율

### 모니터링 코드 예시

```python
# 통계 로깅
logger.info(f"[하이브리드 통계] {processor.get_stats()}")

# 주기적 리포트
async def daily_report():
    stats = processor.get_stats()

    report = f"""
    일일 하이브리드 추출 리포트
    ============================
    총 문서: {stats['total_documents']}
    pdfplumber: {stats['pdfplumber_used']} ({stats['pdfplumber_ratio']})
    Upstage: {stats['upstage_used']} ({stats['upstage_ratio']})
    절감 비용: {stats['estimated_cost_saved']}
    """

    send_to_slack(report)
```

---

## ✅ 결론

### 권장 전략

1. **시작 단계**: Simple 전략으로 빠르게 시작
2. **안정화 단계**: Smart 전략으로 업그레이드 (권장)
3. **최적화 단계**: Progressive 또는 ML 전략

### 기대 효과

- ✅ **비용**: 60-70% 절감 (Smart 전략 기준)
- ✅ **품질**: Upstage와 동일 (필요한 곳에만 사용)
- ✅ **속도**: pdfplumber 수준 유지
- ✅ **확장성**: 대규모 처리 가능

### 다음 단계

1. `HybridDocumentProcessor` 구현
2. 샘플 문서로 테스트
3. 임계값 조정 및 최적화
4. 모니터링 대시보드 구축
5. ML 모델 학습 (선택)

**지금 바로 하이브리드 방식을 적용하여 비용은 절감하고 품질은 유지하세요!** 🚀
