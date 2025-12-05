"""
LLM Entity Extractor 테스트 스크립트
"""
import os
import sys
from loguru import logger

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_entity_extractor import LLMEntityExtractor

# 테스트 텍스트 (실제 보험 문서 발췌)
TEST_TEXT = """
암진단보험금

피보험자가 보험기간 중 암으로 진단확정된 경우에는 가입금액(1억원)을 암진단보험금으로 지급합니다.

단, 다음의 경우에는 보험금을 지급하지 않습니다:
1. 고의적인 사고로 인한 경우
2. 보험계약일로부터 90일 이내에 진단확정된 경우 (면책기간)
3. 음주운전 중 사고로 인한 경우

보장개시일: 계약일로부터 90일 경과 후
특약: 암수술급여특약 (수술 1회당 500만원 지급)

수술급여금 지급조건:
- 암으로 인한 수술을 받은 경우
- 병원 입원 후 수술받은 경우만 해당
- 본인부담금 20만원 공제 후 지급

가입조건: 만 20세 이상 65세 미만의 건강한 자
"""

def main():
    logger.info("=" * 80)
    logger.info("LLM Entity Extractor 테스트 시작")
    logger.info("=" * 80)

    # 추출기 초기화
    extractor = LLMEntityExtractor()

    # 엔티티 및 관계 추출
    logger.info("텍스트에서 엔티티와 관계 추출 중...")
    entities, relationships = extractor.extract_entities_and_relationships(
        text=TEST_TEXT,
        insurer="삼성화재",
        product_type="암보험",
        document_id="test_doc_001"
    )

    # 결과 출력
    logger.info("\n" + "=" * 80)
    logger.info(f"추출된 엔티티: {len(entities)}개")
    logger.info("=" * 80)
    for i, entity in enumerate(entities, 1):
        logger.info(f"\n[엔티티 {i}]")
        logger.info(f"  ID: {entity['entity_id']}")
        logger.info(f"  라벨: {entity['label']}")
        logger.info(f"  타입: {entity['type']}")
        logger.info(f"  설명: {entity['description']}")
        logger.info(f"  원문: {entity['source_text'][:100]}...")

    logger.info("\n" + "=" * 80)
    logger.info(f"추출된 관계: {len(relationships)}개")
    logger.info("=" * 80)
    for i, rel in enumerate(relationships, 1):
        # 엔티티 라벨 찾기
        source_entity = next((e for e in entities if e['entity_id'] == rel['source_entity_id']), None)
        target_entity = next((e for e in entities if e['entity_id'] == rel['target_entity_id']), None)

        if source_entity and target_entity:
            logger.info(f"\n[관계 {i}]")
            logger.info(f"  {source_entity['label']} -- [{rel['relationship_type']}] --> {target_entity['label']}")
            logger.info(f"  설명: {rel['description']}")

    # 통계
    logger.info("\n" + "=" * 80)
    logger.info("통계")
    logger.info("=" * 80)
    logger.info(f"총 엔티티 수: {len(entities)}")
    logger.info(f"총 관계 수: {len(relationships)}")
    logger.info(f"관계/엔티티 비율: {len(relationships) / len(entities) if entities else 0:.2f}")

    # 타입별 통계
    entity_types = {}
    for entity in entities:
        entity_type = entity['type']
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

    logger.info("\n엔티티 타입별 분포:")
    for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {entity_type}: {count}개")

    relationship_types = {}
    for rel in relationships:
        rel_type = rel['relationship_type']
        relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1

    logger.info("\n관계 타입별 분포:")
    for rel_type, count in sorted(relationship_types.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {rel_type}: {count}개")

    logger.info("\n" + "=" * 80)
    logger.info("테스트 완료!")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
