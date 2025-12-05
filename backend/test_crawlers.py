"""
Insurance Crawlers Test Script

보험사 크롤러 시스템 테스트 및 데모
"""
import asyncio

# 크롤러 시스템 import
from app.services.crawlers import (
    get_crawler,
    get_all_crawlers,
    get_available_insurers,
    is_insurer_supported,
)
from app.services.crawlers.config_loader import load_insurer_config, load_all_insurer_configs


async def test_available_insurers():
    """사용 가능한 보험사 확인"""
    print("\n" + "="*60)
    print("📋 사용 가능한 보험사 목록")
    print("="*60)

    insurers = get_available_insurers()

    if not insurers:
        print("⚠️  등록된 보험사가 없습니다.")
        return

    for insurer_code in insurers:
        supported = "✅" if is_insurer_supported(insurer_code) else "❌"
        print(f"{supported} {insurer_code}")

    print(f"\n총 {len(insurers)}개 보험사 지원")


async def test_config_loading():
    """설정 파일 로드 테스트"""
    print("\n" + "="*60)
    print("⚙️  설정 파일 로드 테스트")
    print("="*60)

    try:
        configs = load_all_insurer_configs()

        for insurer_code, config in configs.items():
            print(f"\n{config.insurer_name} ({insurer_code}):")
            print(f"  - Base URL: {config.base_url}")
            print(f"  - Crawl Method: {config.crawl_method.value}")
            print(f"  - Has Pagination: {config.has_pagination}")
            print(f"  - Request Delay: {config.request_delay}s")

        if not configs:
            print("⚠️  로드된 설정 파일이 없습니다.")

    except Exception as e:
        print(f"❌ 설정 로드 실패: {e}")


async def test_crawler_creation():
    """크롤러 인스턴스 생성 테스트"""
    print("\n" + "="*60)
    print("🏭 크롤러 인스턴스 생성 테스트")
    print("="*60)

    insurers = get_available_insurers()

    for insurer_code in insurers:
        try:
            crawler = get_crawler(insurer_code)
            print(f"✅ {crawler.config.insurer_name}: {type(crawler).__name__}")

        except Exception as e:
            print(f"❌ {insurer_code}: {e}")


async def test_connection(insurer_code: str):
    """특정 보험사 연결 테스트"""
    print("\n" + "="*60)
    print(f"🔗 {insurer_code} 연결 테스트")
    print("="*60)

    try:
        crawler = get_crawler(insurer_code)

        print(f"보험사: {crawler.config.insurer_name}")
        print(f"URL: {crawler.config.base_url}")
        print(f"크롤링 방법: {crawler.config.crawl_method.value}")

        print("\n연결 테스트 중...")
        is_connected = await crawler.test_connection()

        if is_connected:
            print("✅ 연결 성공")
        else:
            print("❌ 연결 실패 (웹사이트가 다운되었거나 URL이 잘못되었을 수 있습니다)")

    except KeyError:
        print(f"❌ '{insurer_code}' 크롤러를 찾을 수 없습니다")
    except Exception as e:
        print(f"❌ 에러: {e}")


async def demo_crawling_flow(insurer_code: str = "samsung_life"):
    """크롤링 플로우 데모 (실제 크롤링 없이 구조만 보여줌)"""
    print("\n" + "="*60)
    print(f"🎬 {insurer_code} 크롤링 플로우 데모")
    print("="*60)

    try:
        crawler = get_crawler(insurer_code)

        print("\n1️⃣ 크롤러 초기화")
        print(f"   보험사: {crawler.config.insurer_name}")
        print(f"   방법: {crawler.config.crawl_method.value}")

        print("\n2️⃣ 상품 목록 조회 (시뮬레이션)")
        print("   - 암보험: 5개 상품")
        print("   - 실손보험: 3개 상품")
        print("   - 종신보험: 4개 상품")

        print("\n3️⃣ 약관 메타데이터 수집 (시뮬레이션)")
        print("   - 상품명, 코드, 카테고리")
        print("   - 다운로드 URL, 버전, 시행일")

        print("\n4️⃣ 약관 파일 다운로드 (시뮬레이션)")
        print("   - PDF 파일 다운로드")
        print("   - 로컬 저장소에 저장")

        print("\n5️⃣ 데이터베이스 저장 (시뮬레이션)")
        print("   - policy_metadata 테이블에 저장")
        print("   - ingestion_jobs에 작업 등록")

        print("\n✅ 크롤링 플로우 완료")

    except Exception as e:
        print(f"❌ 에러: {e}")


async def show_crawler_info(insurer_code: str):
    """특정 크롤러 상세 정보"""
    print("\n" + "="*60)
    print(f"ℹ️  {insurer_code} 크롤러 정보")
    print("="*60)

    try:
        crawler = get_crawler(insurer_code)
        config = crawler.config

        print(f"\n기본 정보:")
        print(f"  코드: {config.insurer_code}")
        print(f"  이름: {config.insurer_name}")
        print(f"  URL: {config.base_url}")

        print(f"\n크롤링 설정:")
        print(f"  방법: {config.crawl_method.value}")
        print(f"  인증: {config.auth_method.value}")
        print(f"  페이지네이션: {config.has_pagination}")
        print(f"  최대 페이지: {config.max_pages}")

        print(f"\nRate Limiting:")
        print(f"  요청 간격: {config.request_delay}초")
        print(f"  최대 재시도: {config.max_retries}회")

        print(f"\nSelectors:")
        print(f"  상품 목록: {config.product_list_selector}")
        print(f"  상품명: {config.product_name_selector}")
        print(f"  카테고리: {config.product_category_selector}")
        print(f"  다운로드: {config.download_link_selector}")

        if config.metadata:
            print(f"\n추가 정보:")
            for key, value in config.metadata.items():
                if key != "notes":
                    print(f"  {key}: {value}")

    except Exception as e:
        print(f"❌ 에러: {e}")


async def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("🧪 Insurance Crawler System Test")
    print("="*60)

    # 1. 사용 가능한 보험사 확인
    await test_available_insurers()

    # 2. 설정 파일 로드 테스트
    await test_config_loading()

    # 3. 크롤러 생성 테스트
    await test_crawler_creation()

    # 4. 연결 테스트 (실제 웹사이트에 접속)
    insurers = get_available_insurers()
    if insurers:
        await test_connection(insurers[0])

    # 5. 크롤링 플로우 데모
    await demo_crawling_flow()

    # 6. 상세 정보 출력
    if insurers:
        await show_crawler_info(insurers[0])

    print("\n" + "="*60)
    print("✅ 테스트 완료")
    print("="*60)


if __name__ == "__main__":
    # 테스트 실행
    asyncio.run(main())
