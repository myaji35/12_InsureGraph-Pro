"""
보험사별 템플릿 사전 추출 스크립트

주기적으로 실행하여 각 보험사의 상품별 템플릿을 추출하고 캐시
- 템플릿 매칭 전략의 효율을 높이기 위한 사전 작업
- 주간 또는 월간 실행 권장
"""
import asyncio
from typing import List, Dict
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.crawler_document import CrawlerDocument
from app.services.learning.smart_learner import SmartInsuranceLearner


async def get_insurers_from_db() -> List[str]:
    """DB에서 보험사 목록 조회"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CrawlerDocument.insurer)
            .distinct()
            .where(CrawlerDocument.processing_step == 'graph_stored')
        )
        insurers = [row[0] for row in result.fetchall() if row[0]]

    logger.info(f"Found {len(insurers)} insurers in DB: {insurers}")
    return insurers


async def get_product_types_for_insurer(insurer: str) -> List[str]:
    """특정 보험사의 상품 유형 목록 조회"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CrawlerDocument.product_type)
            .distinct()
            .where(
                CrawlerDocument.insurer == insurer,
                CrawlerDocument.processing_step == 'graph_stored',
                CrawlerDocument.product_type.isnot(None)
            )
        )
        product_types = [row[0] for row in result.fetchall() if row[0]]

    logger.info(f"Found {len(product_types)} product types for {insurer}: {product_types}")
    return product_types


async def get_documents_for_template(
    insurer: str,
    product_type: str,
    min_documents: int = 3
) -> List[Dict]:
    """템플릿 추출용 문서 조회"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CrawlerDocument)
            .where(
                CrawlerDocument.insurer == insurer,
                CrawlerDocument.product_type == product_type,
                CrawlerDocument.processing_step == 'graph_stored',
                CrawlerDocument.extracted_text.isnot(None)
            )
            .limit(min_documents * 2)  # 여유있게 조회
        )
        documents = result.scalars().all()

    doc_list = [
        {
            "id": doc.id,
            "text": doc.extracted_text,
            "url": doc.url
        }
        for doc in documents
        if doc.extracted_text and len(doc.extracted_text) > 100
    ]

    logger.info(f"Found {len(doc_list)} documents for {insurer} - {product_type}")
    return doc_list


async def extract_template_for_product(
    smart_learner: SmartInsuranceLearner,
    insurer: str,
    product_type: str,
    min_documents: int = 3
) -> Dict:
    """특정 상품에 대한 템플릿 추출"""

    logger.info(f"Extracting template for {insurer} - {product_type}")

    # 문서 조회
    documents = await get_documents_for_template(insurer, product_type, min_documents)

    if len(documents) < min_documents:
        logger.warning(
            f"Not enough documents ({len(documents)}) for {insurer} - {product_type}, "
            f"need at least {min_documents}"
        )
        return {
            "insurer": insurer,
            "product_type": product_type,
            "status": "insufficient_documents",
            "document_count": len(documents),
            "template_extracted": False
        }

    # 템플릿 추출
    try:
        template_info = await smart_learner.template_extractor.extract_template(
            documents[:min_documents]
        )

        if template_info["template"]:
            # 템플릿 캐시에 저장
            smart_learner.template_matcher.cache_template(
                insurer,
                product_type,
                template_info
            )

            logger.info(
                f"✅ Template extracted for {insurer} - {product_type}: "
                f"{template_info['variable_count']} variables, "
                f"{template_info['coverage_ratio']:.1%} coverage"
            )

            return {
                "insurer": insurer,
                "product_type": product_type,
                "status": "success",
                "template_extracted": True,
                "coverage_ratio": template_info["coverage_ratio"],
                "variable_count": template_info["variable_count"],
                "document_count": len(documents)
            }
        else:
            logger.warning(f"Failed to extract template for {insurer} - {product_type}")
            return {
                "insurer": insurer,
                "product_type": product_type,
                "status": "extraction_failed",
                "template_extracted": False,
                "document_count": len(documents)
            }

    except Exception as e:
        logger.error(f"Error extracting template for {insurer} - {product_type}: {e}")
        return {
            "insurer": insurer,
            "product_type": product_type,
            "status": "error",
            "error": str(e),
            "template_extracted": False
        }


async def extract_templates_for_insurer(
    smart_learner: SmartInsuranceLearner,
    insurer: str,
    min_documents: int = 3
) -> Dict:
    """특정 보험사의 모든 상품에 대한 템플릿 추출"""

    logger.info(f"\n{'=' * 80}")
    logger.info(f"Extracting templates for {insurer}")
    logger.info(f"{'=' * 80}")

    # 상품 유형 조회
    product_types = await get_product_types_for_insurer(insurer)

    if not product_types:
        logger.warning(f"No product types found for {insurer}")
        return {
            "insurer": insurer,
            "status": "no_products",
            "products_optimized": 0,
            "products_total": 0,
            "results": []
        }

    # 각 상품별 템플릿 추출
    results = []
    for product_type in product_types:
        result = await extract_template_for_product(
            smart_learner,
            insurer,
            product_type,
            min_documents
        )
        results.append(result)

    # 통계
    products_optimized = sum(1 for r in results if r["template_extracted"])
    products_total = len(results)

    logger.info(f"\n✅ {insurer} optimization complete:")
    logger.info(f"   - Products optimized: {products_optimized}/{products_total}")
    logger.info(f"   - Success rate: {products_optimized/products_total:.1%}" if products_total > 0 else "   - No products")

    return {
        "insurer": insurer,
        "status": "completed",
        "products_optimized": products_optimized,
        "products_total": products_total,
        "results": results
    }


async def extract_all_templates(min_documents: int = 3) -> Dict:
    """모든 보험사의 템플릿 추출"""

    logger.info("=" * 80)
    logger.info("Insurance Template Extraction Script")
    logger.info("=" * 80)
    logger.info(f"Min documents required per product: {min_documents}\n")

    # SmartInsuranceLearner 초기화
    smart_learner = SmartInsuranceLearner()

    # DB에서 보험사 목록 조회
    insurers = await get_insurers_from_db()

    if not insurers:
        logger.warning("No insurers found in database")
        return {
            "status": "no_insurers",
            "insurers_processed": 0,
            "total_templates_extracted": 0
        }

    # 각 보험사별 템플릿 추출
    insurer_results = []
    for insurer in insurers:
        result = await extract_templates_for_insurer(
            smart_learner,
            insurer,
            min_documents
        )
        insurer_results.append(result)

    # 전체 통계
    total_insurers = len(insurers)
    total_products_optimized = sum(r["products_optimized"] for r in insurer_results)
    total_products = sum(r["products_total"] for r in insurer_results)

    logger.info("\n" + "=" * 80)
    logger.info("Overall Statistics")
    logger.info("=" * 80)
    logger.info(f"Insurers processed: {total_insurers}")
    logger.info(f"Total products optimized: {total_products_optimized}/{total_products}")
    logger.info(f"Success rate: {total_products_optimized/total_products:.1%}" if total_products > 0 else "No products")

    # 보험사별 상세 결과
    logger.info("\nDetails by Insurer:")
    for result in insurer_results:
        logger.info(f"  - {result['insurer']}: {result['products_optimized']}/{result['products_total']} products")

    # 정리
    await smart_learner.cleanup()

    return {
        "status": "completed",
        "insurers_processed": total_insurers,
        "total_templates_extracted": total_products_optimized,
        "total_products": total_products,
        "success_rate": total_products_optimized / total_products if total_products > 0 else 0,
        "results": insurer_results
    }


async def main():
    """메인 실행"""
    try:
        result = await extract_all_templates(min_documents=3)
        logger.info(f"\n✅ Template extraction completed: {result}")
    except Exception as e:
        logger.error(f"❌ Template extraction failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main())
