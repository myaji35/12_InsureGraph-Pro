"""
MetLife Crawler 테스트 스크립트

메트라이프 보험 약관 크롤러 테스트
"""
import asyncio
import sys
from loguru import logger

# 로깅 설정
logger.remove()
logger.add(sys.stdout, level="INFO")

from app.services.crawlers.metlife_crawler import MetLifeCrawler


async def test_metlife_crawler():
    """메트라이프 크롤러 테스트"""

    print("=" * 80)
    print("MetLife 보험 약관 크롤러 테스트")
    print("=" * 80)

    # 크롤러 생성
    crawler = MetLifeCrawler()

    # 1. 판매상품 크롤링 (최대 5개만)
    print("\n[1] 판매상품 크롤링 테스트...")
    active_products = await crawler.get_product_list(category='active')

    print(f"\n✅ 판매상품 발견: {len(active_products)}개")

    if active_products:
        print("\n📋 판매상품 샘플 (최대 5개):")
        for i, product in enumerate(active_products[:5], 1):
            print(f"\n  {i}. {product['product_name']}")
            print(f"     상품 유형: {product['product_type']}")
            print(f"     판매기간: {product['sales_period']}")
            print(f"     카테고리: {product['category']}")
            print(f"     다운로드 URL: {product['download_url'][:80]}...")

    # 2. 판매중지상품 크롤링 (최대 5개만)
    print("\n\n[2] 판매중지상품 크롤링 테스트...")
    discontinued_products = await crawler.get_product_list(category='discontinued')

    print(f"\n✅ 판매중지상품 발견: {len(discontinued_products)}개")

    if discontinued_products:
        print("\n📋 판매중지상품 샘플 (최대 5개):")
        for i, product in enumerate(discontinued_products[:5], 1):
            print(f"\n  {i}. {product['product_name']}")
            print(f"     상품 유형: {product['product_type']}")
            print(f"     판매기간: {product['sales_period']}")
            print(f"     카테고리: {product['category']}")
            print(f"     다운로드 URL: {product['download_url'][:80]}...")

    # 3. 전체 크롤링 (통계만)
    print("\n\n[3] 전체 크롤링 통계...")
    all_products = await crawler.get_product_list()

    print(f"\n✅ 총 상품 수: {len(all_products)}개")

    # 상품 유형별 통계
    product_types = {}
    for product in all_products:
        ptype = product['product_type']
        product_types[ptype] = product_types.get(ptype, 0) + 1

    print("\n📊 상품 유형별 통계:")
    for ptype, count in sorted(product_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {ptype}: {count}개")

    # 4. URL 검증 테스트 (첫 번째 상품)
    if all_products:
        print("\n\n[4] URL 검증 테스트...")
        first_product = all_products[0]
        is_valid = await crawler.validate_url(first_product['download_url'])

        print(f"\n  상품: {first_product['product_name']}")
        print(f"  URL: {first_product['download_url'][:80]}...")
        print(f"  검증 결과: {'✅ 유효' if is_valid else '❌ 무효'}")

    # 5. JSON 저장 테스트
    print("\n\n[5] JSON 저장 테스트...")
    json_path = await crawler.save_results_to_json(all_products)

    print(f"\n✅ 크롤링 결과 저장 완료!")
    print(f"  저장 경로: {json_path}")

    # 6. JSON 로드 테스트
    print("\n\n[6] JSON 로드 테스트...")
    loaded_data = await crawler.load_results_from_json(json_path)

    print(f"\n✅ JSON 로드 완료!")
    print(f"  코멘트: {loaded_data['metadata']['comment']}")
    print(f"  크롤링 시각: {loaded_data['metadata']['crawl_timestamp']}")
    print(f"  총 상품: {loaded_data['metadata']['total_products']}개")
    print(f"  판매상품: {loaded_data['metadata']['active_products']}개")
    print(f"  판매중지상품: {loaded_data['metadata']['discontinued_products']}개")

    print("\n" + "=" * 80)
    print("✅ 모든 테스트 완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_metlife_crawler())
