# Insurance Company Crawlers

보험사별 약관 수집을 위한 유연하고 확장 가능한 크롤러 시스템

## 📋 개요

각 보험사마다 웹사이트 구조, 약관 제공 방식, 인증 방법이 다릅니다. 이 시스템은 **Strategy Pattern**과 **Factory Pattern**을 사용하여 보험사별로 다른 크롤링 전략을 쉽게 추가하고 관리할 수 있도록 설계되었습니다.

## 🏗️ 아키텍처

```
crawlers/
├── base_crawler.py           # 추상 베이스 클래스
├── samsung_life_crawler.py   # 삼성생명 크롤러
├── kb_insurance_crawler.py   # KB손해보험 크롤러
├── crawler_factory.py        # 크롤러 생성 팩토리
├── crawler_registry.py       # 크롤러 등록/관리
├── config_loader.py          # YAML 설정 로더
└── configs/                  # 보험사별 설정 파일
    ├── samsung_life.yaml
    └── kb_insurance.yaml
```

## 🎯 주요 기능

### 1. 보험사별 크롤링 전략

각 보험사마다 다른 크롤링 방법을 지원합니다:

- **Static HTML**: requests + BeautifulSoup
- **Dynamic JS**: Playwright/Selenium (JavaScript 렌더링 필요)
- **API**: REST API 직접 호출
- **Hybrid**: 복합 방식 (API + 스크래핑)

### 2. 유연한 설정 관리

YAML 파일로 각 보험사의 설정을 관리:

```yaml
insurer_code: samsung_life
insurer_name: 삼성생명
base_url: https://www.samsunglife.com
crawl_method: dynamic_js
product_list_selector: .product-list .product-item
request_delay: 1.5
```

### 3. 쉬운 확장

새로운 보험사 추가가 간단합니다:

1. `BaseInsurerCrawler`를 상속한 새 크롤러 클래스 작성
2. 레지스트리에 등록
3. 설정 YAML 파일 작성 (선택사항)

## 📖 사용 방법

### 기본 사용

```python
from app.services.crawlers import get_crawler

# 1. 크롤러 인스턴스 가져오기
crawler = get_crawler("samsung_life")

# 2. 연결 테스트
is_connected = await crawler.test_connection()

# 3. 상품 목록 조회
products = await crawler.get_product_list(category="암보험")

# 4. 특정 상품의 약관 메타데이터 조회
metadata = await crawler.get_policy_metadata(product_id="12345")

# 5. 약관 파일 다운로드
filepath = await crawler.download_policy(metadata, save_path="/tmp/policies")

# 6. 전체 약관 크롤링
all_metadata = await crawler.crawl_all_policies(
    categories=["암보험", "실손보험"],
    save_dir="/tmp/policies"
)
```

### 모든 보험사 크롤링

```python
from app.services.crawlers import get_all_crawlers

# 모든 등록된 크롤러 가져오기
crawlers = get_all_crawlers()

for insurer_code, crawler in crawlers.items():
    print(f"Crawling {crawler.config.insurer_name}...")

    try:
        metadata_list = await crawler.crawl_all_policies()
        print(f"  ✅ Found {len(metadata_list)} policies")
    except Exception as e:
        print(f"  ❌ Error: {e}")
```

### 사용 가능한 보험사 확인

```python
from app.services.crawlers import get_available_insurers, is_insurer_supported

# 지원되는 보험사 목록
insurers = get_available_insurers()
print(f"Available insurers: {', '.join(insurers)}")

# 특정 보험사 지원 여부
if is_insurer_supported("samsung_life"):
    print("삼성생명 크롤러를 사용할 수 있습니다")
```

### 설정 파일 로드

```python
from app.services.crawlers.config_loader import load_insurer_config

# YAML 파일에서 설정 로드
config = load_insurer_config("samsung_life")

print(f"Insurer: {config.insurer_name}")
print(f"Base URL: {config.base_url}")
print(f"Crawl Method: {config.crawl_method}")
```

## 🆕 새로운 보험사 크롤러 추가하기

### Step 1: 크롤러 클래스 작성

```python
# app/services/crawlers/hyundai_marine_crawler.py

from app.services.crawlers.base_crawler import (
    BaseInsurerCrawler,
    InsurerConfig,
    PolicyMetadata,
    CrawlMethod,
)

class HyundaiMarineCrawler(BaseInsurerCrawler):
    """현대해상 크롤러"""

    def __init__(self):
        config = InsurerConfig(
            insurer_code="hyundai_marine",
            insurer_name="현대해상",
            base_url="https://www.hi.co.kr",
            crawl_method=CrawlMethod.STATIC_HTML,
            # ... 기타 설정
        )
        super().__init__(config)

    async def get_product_list(self, category=None):
        # 구현
        pass

    async def get_policy_metadata(self, product_id):
        # 구현
        pass

    async def download_policy(self, metadata, save_path):
        # 구현
        pass
```

### Step 2: 레지스트리에 등록

```python
# app/services/crawlers/crawler_registry.py (수정)

def _auto_register_crawlers():
    try:
        from app.services.crawlers.samsung_life_crawler import SamsungLifeCrawler
        from app.services.crawlers.kb_insurance_crawler import KBInsuranceCrawler
        from app.services.crawlers.hyundai_marine_crawler import HyundaiMarineCrawler  # 추가

        register_crawler("samsung_life", SamsungLifeCrawler)
        register_crawler("kb_insurance", KBInsuranceCrawler)
        register_crawler("hyundai_marine", HyundaiMarineCrawler)  # 추가

    except Exception as e:
        logger.error(f"Failed to auto-register crawlers: {e}")
```

### Step 3: 설정 파일 작성 (선택)

```yaml
# app/services/crawlers/configs/hyundai_marine.yaml

insurer_code: hyundai_marine
insurer_name: 현대해상
base_url: https://www.hi.co.kr
crawl_method: static_html
product_list_selector: .product-item
request_delay: 1.0
```

## 🔧 설정 옵션

### CrawlMethod

- `static_html`: 정적 HTML 페이지 (requests + BeautifulSoup)
- `dynamic_js`: JavaScript 렌더링 필요 (Playwright)
- `api`: REST API 직접 호출
- `hybrid`: 복합 방식

### AuthMethod

- `none`: 인증 불필요
- `basic`: Basic Authentication
- `oauth`: OAuth 2.0
- `session`: 세션 기반 인증
- `api_key`: API 키 인증

### 주요 설정 항목

| 항목 | 설명 | 예시 |
|------|------|------|
| `insurer_code` | 보험사 코드 | `samsung_life` |
| `insurer_name` | 보험사 이름 | `삼성생명` |
| `base_url` | 기본 URL | `https://...` |
| `crawl_method` | 크롤링 방법 | `dynamic_js` |
| `product_list_selector` | 상품 목록 CSS 셀렉터 | `.product-list` |
| `request_delay` | 요청 간 지연 (초) | `1.5` |
| `has_pagination` | 페이지네이션 여부 | `true` |
| `max_pages` | 최대 페이지 수 | `50` |

## 📊 PolicyMetadata 구조

크롤링된 약관 메타데이터:

```python
@dataclass
class PolicyMetadata:
    insurer_code: str             # 보험사 코드
    insurer_name: str             # 보험사 이름
    product_name: str             # 상품명
    product_code: Optional[str]   # 상품 코드
    category: Optional[str]       # 카테고리 (예: "암보험")
    sub_category: Optional[str]   # 하위 카테고리
    download_url: Optional[str]   # 다운로드 URL
    effective_date: Optional[str] # 시행일
    version: Optional[str]        # 버전
    file_type: str = "pdf"        # 파일 유형
    file_size: Optional[int]      # 파일 크기
    additional_info: Optional[Dict]  # 추가 정보
```

## 🧪 테스트

```python
# 특정 보험사 연결 테스트
crawler = get_crawler("samsung_life")
success = await crawler.test_connection()

if success:
    print("✅ Connection successful")
else:
    print("❌ Connection failed")

# 메타데이터 유효성 검증
metadata = await crawler.get_policy_metadata("12345")
is_valid = crawler.validate_metadata(metadata)
```

## 🎨 실제 사용 예시

### API 엔드포인트에서 사용

```python
from fastapi import APIRouter, HTTPException
from app.services.crawlers import get_crawler, get_available_insurers

router = APIRouter()

@router.get("/insurers")
async def list_insurers():
    """지원되는 보험사 목록"""
    return {"insurers": get_available_insurers()}

@router.post("/crawl/{insurer_code}")
async def crawl_insurer(insurer_code: str, category: Optional[str] = None):
    """특정 보험사 크롤링"""
    try:
        crawler = get_crawler(insurer_code)
        metadata_list = await crawler.crawl_all_policies(
            categories=[category] if category else None
        )

        return {
            "status": "success",
            "insurer": insurer_code,
            "policies_found": len(metadata_list),
            "metadata": [vars(m) for m in metadata_list]
        }

    except KeyError:
        raise HTTPException(status_code=404, detail=f"Insurer not found: {insurer_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Celery Task에서 사용

```python
from celery import shared_task
from app.services.crawlers import get_crawler

@shared_task
def crawl_insurer_task(insurer_code: str, categories: List[str] = None):
    """비동기 크롤링 작업"""
    import asyncio

    async def _crawl():
        crawler = get_crawler(insurer_code)
        return await crawler.crawl_all_policies(categories=categories)

    metadata_list = asyncio.run(_crawl())

    return {
        "insurer": insurer_code,
        "policies": len(metadata_list),
    }
```

## 💡 Best Practices

1. **Rate Limiting 준수**: 각 보험사의 `request_delay` 설정을 지켜주세요
2. **에러 핸들링**: try-except로 개별 상품 크롤링 실패를 처리하세요
3. **로깅**: 각 단계마다 로그를 남겨 디버깅을 용이하게 하세요
4. **설정 분리**: 하드코딩 대신 YAML 설정 파일을 사용하세요
5. **테스트**: 새 크롤러 추가 시 `test_connection()`으로 먼저 테스트하세요

## 🔒 주의사항

- **웹사이트 변경**: 보험사 웹사이트 구조가 변경되면 셀렉터를 업데이트해야 합니다
- **이용 약관**: 각 보험사의 크롤링 정책을 확인하세요
- **개인정보**: 약관 문서 외에 개인정보는 수집하지 마세요
- **서버 부하**: rate limiting을 준수하여 서버에 부담을 주지 마세요

## 📝 TODO

- [ ] 추가 보험사 크롤러 구현 (한화생명, AIA, 메리츠화재 등)
- [ ] Playwright 통합 (JavaScript 렌더링)
- [ ] 크롤링 결과 캐싱
- [ ] 크롤링 스케줄링 (주기적 업데이트)
- [ ] 약관 변경 감지
- [ ] 다운로드 진행률 추적

## 📚 참고

- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Playwright Python](https://playwright.dev/python/)
- [Strategy Pattern](https://refactoring.guru/design-patterns/strategy)
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method)
