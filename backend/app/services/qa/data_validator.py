"""
Data Validator

파싱된 문서와 추출된 데이터의 품질을 검증합니다.
"""
import logging
from typing import Dict, Any, List, Optional

from app.models.validation import (
    DataValidationResult,
    ValidationSeverity,
)

logger = logging.getLogger(__name__)


class DataValidator:
    """데이터 품질 검증기"""

    def __init__(self):
        """검증기 초기화"""
        pass

    def validate(
        self,
        parsed_document: Optional[Dict[str, Any]] = None,
        critical_data: Optional[Dict[str, Any]] = None,
        relations: Optional[List[Dict[str, Any]]] = None,
        entity_links: Optional[Dict[str, Any]] = None,
    ) -> DataValidationResult:
        """
        전체 데이터 검증

        Args:
            parsed_document: 파싱된 문서 (Story 1.3)
            critical_data: 핵심 데이터 (Story 1.4)
            relations: 관계 목록 (Story 1.5)
            entity_links: 엔티티 링크 (Story 1.6)

        Returns:
            DataValidationResult
        """
        logger.info("데이터 검증 시작")

        result = DataValidationResult(is_valid=True)

        # 1. 문서 구조 검증
        if parsed_document:
            self._validate_structure(parsed_document, result)

        # 2. 핵심 데이터 검증
        if critical_data:
            self._validate_critical_data(critical_data, result)

        # 3. 관계 데이터 검증
        if relations:
            self._validate_relations(relations, result)

        # 4. 엔티티 링크 검증
        if entity_links:
            self._validate_entity_links(entity_links, result)

        # 통계 계산
        self._calculate_statistics(
            parsed_document, critical_data, relations, entity_links, result
        )

        logger.info(
            f"데이터 검증 완료: {'통과' if result.is_valid else '실패'} "
            f"({len(result.issues)}개 이슈)"
        )

        return result

    def _validate_structure(
        self, parsed_document: Dict[str, Any], result: DataValidationResult
    ):
        """문서 구조 검증"""
        articles = parsed_document.get("articles", [])

        # 기본 검증: 조항이 있는지
        if not articles:
            result.add_issue(
                severity=ValidationSeverity.CRITICAL,
                category="structure",
                message="문서에 조항이 없습니다",
                suggestion="문서 파싱이 올바르게 수행되었는지 확인하세요",
            )
            result.structure_valid = False
            return

        # 조항 번호 중복 검사
        article_nums = [a.get("article_num") for a in articles]
        duplicates = [num for num in article_nums if article_nums.count(num) > 1]
        if duplicates:
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="structure",
                message=f"중복된 조항 번호: {set(duplicates)}",
                suggestion="파싱 로직을 확인하세요",
            )

        # 각 조항에 최소 1개 이상의 문단이 있는지
        empty_articles = [
            a.get("article_num")
            for a in articles
            if not a.get("paragraphs")
        ]
        if empty_articles:
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="structure",
                message=f"문단이 없는 조항: {empty_articles[:5]}",
                location=", ".join(empty_articles[:3]),
                suggestion="해당 조항의 파싱 결과를 확인하세요",
            )

        # 텍스트가 비어있는 문단 검사
        empty_paragraphs = 0
        for article in articles:
            for para in article.get("paragraphs", []):
                if not para.get("text") or len(para.get("text", "").strip()) == 0:
                    empty_paragraphs += 1

        if empty_paragraphs > 0:
            result.add_issue(
                severity=ValidationSeverity.INFO,
                category="structure",
                message=f"{empty_paragraphs}개의 빈 문단 발견",
                suggestion="빈 문단은 처리에서 제외됩니다",
            )

    def _validate_critical_data(
        self, critical_data: Dict[str, Any], result: DataValidationResult
    ):
        """핵심 데이터 검증"""
        amounts = critical_data.get("amounts", [])
        periods = critical_data.get("periods", [])
        kcd_codes = critical_data.get("kcd_codes", [])

        # 기본 검증: 최소한의 데이터가 추출되었는지
        if not amounts and not periods and not kcd_codes:
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="critical_data",
                message="추출된 핵심 데이터가 없습니다",
                suggestion="문서에 금액, 기간, KCD 코드가 포함되어 있는지 확인하세요",
            )
            result.critical_data_valid = False

        # 금액 검증
        for i, amount in enumerate(amounts):
            value = amount.get("value", 0)
            if value <= 0:
                result.add_issue(
                    severity=ValidationSeverity.ERROR,
                    category="critical_data",
                    message=f"유효하지 않은 금액: {value}",
                    location=f"금액 #{i+1}",
                    suggestion="금액 추출 로직을 확인하세요",
                )
                result.critical_data_valid = False

            # 비정상적으로 큰 금액 (100억 이상)
            if value > 10_000_000_000:
                result.add_issue(
                    severity=ValidationSeverity.WARNING,
                    category="critical_data",
                    message=f"비정상적으로 큰 금액: {value:,}원",
                    location=f"금액 #{i+1}",
                    suggestion="금액이 올바른지 확인하세요",
                )

        # 기간 검증
        for i, period in enumerate(periods):
            days = period.get("days", 0)
            if days <= 0:
                result.add_issue(
                    severity=ValidationSeverity.ERROR,
                    category="critical_data",
                    message=f"유효하지 않은 기간: {days}일",
                    location=f"기간 #{i+1}",
                    suggestion="기간 추출 로직을 확인하세요",
                )
                result.critical_data_valid = False

            # 비정상적으로 긴 기간 (10년 이상)
            if days > 3650:
                result.add_issue(
                    severity=ValidationSeverity.WARNING,
                    category="critical_data",
                    message=f"비정상적으로 긴 기간: {days}일",
                    location=f"기간 #{i+1}",
                    suggestion="기간이 올바른지 확인하세요",
                )

        # KCD 코드 검증
        for i, kcd in enumerate(kcd_codes):
            code = kcd.get("code", "")
            is_valid = kcd.get("is_valid", False)

            if not is_valid:
                result.add_issue(
                    severity=ValidationSeverity.WARNING,
                    category="critical_data",
                    message=f"유효하지 않은 KCD 코드: {code}",
                    location=f"KCD #{i+1}",
                    suggestion="KCD 코드 형식을 확인하세요",
                )

    def _validate_relations(
        self, relations: List[Dict[str, Any]], result: DataValidationResult
    ):
        """관계 데이터 검증"""
        if not relations:
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="relations",
                message="추출된 관계가 없습니다",
                suggestion="LLM 관계 추출이 올바르게 수행되었는지 확인하세요",
            )
            result.relations_valid = False
            return

        total_relations = sum(len(r.get("relations", [])) for r in relations)

        if total_relations == 0:
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="relations",
                message="추출된 관계가 0개입니다",
                suggestion="문서에 보장-질병 관계가 있는지 확인하세요",
            )
            result.relations_valid = False

        # 개별 관계 검증
        low_confidence_count = 0
        for relation_result in relations:
            for relation in relation_result.get("relations", []):
                # 신뢰도 검증
                confidence = relation.get("confidence", 0.0)
                if confidence < 0.5:
                    low_confidence_count += 1

                # 필수 필드 검증
                if not relation.get("subject"):
                    result.add_issue(
                        severity=ValidationSeverity.ERROR,
                        category="relations",
                        message="관계의 주체(subject)가 없습니다",
                        suggestion="관계 추출 결과를 확인하세요",
                    )
                    result.relations_valid = False

                if not relation.get("object"):
                    result.add_issue(
                        severity=ValidationSeverity.ERROR,
                        category="relations",
                        message="관계의 객체(object)가 없습니다",
                        suggestion="관계 추출 결과를 확인하세요",
                    )
                    result.relations_valid = False

        # 낮은 신뢰도 경고
        if low_confidence_count > 0:
            result.add_issue(
                severity=ValidationSeverity.INFO,
                category="relations",
                message=f"{low_confidence_count}개의 낮은 신뢰도 관계 (<0.5)",
                suggestion="해당 관계들을 수동으로 확인하세요",
            )

    def _validate_entity_links(
        self, entity_links: Dict[str, Any], result: DataValidationResult
    ):
        """엔티티 링크 검증"""
        if not entity_links:
            result.add_issue(
                severity=ValidationSeverity.WARNING,
                category="entities",
                message="연결된 엔티티가 없습니다",
                suggestion="엔티티 링크가 수행되었는지 확인하세요",
            )
            result.entities_valid = False
            return

        # 연결 실패한 엔티티 카운트
        failed_links = []
        for mention, link_result in entity_links.items():
            if not link_result.get("matched_entity"):
                failed_links.append(mention)

        if failed_links:
            result.add_issue(
                severity=ValidationSeverity.INFO,
                category="entities",
                message=f"{len(failed_links)}개의 엔티티 연결 실패",
                suggestion=f"온톨로지에 다음 질병을 추가하세요: {failed_links[:5]}",
            )

    def _calculate_statistics(
        self,
        parsed_document: Optional[Dict[str, Any]],
        critical_data: Optional[Dict[str, Any]],
        relations: Optional[List[Dict[str, Any]]],
        entity_links: Optional[Dict[str, Any]],
        result: DataValidationResult,
    ):
        """통계 계산"""
        # 문서 통계
        if parsed_document:
            articles = parsed_document.get("articles", [])
            result.total_articles = len(articles)
            result.total_paragraphs = sum(
                len(a.get("paragraphs", [])) for a in articles
            )

        # 핵심 데이터 통계
        if critical_data:
            result.total_amounts = len(critical_data.get("amounts", []))
            result.total_periods = len(critical_data.get("periods", []))
            result.total_kcd_codes = len(critical_data.get("kcd_codes", []))

        # 관계 통계
        if relations:
            result.total_relations = sum(
                len(r.get("relations", [])) for r in relations
            )

        # 엔티티 링크 통계
        if entity_links:
            total_mentions = len(entity_links)
            successful_links = sum(
                1 for link in entity_links.values()
                if link.get("matched_entity") is not None
            )
            result.total_entities_linked = successful_links
            result.entity_link_rate = (
                successful_links / total_mentions if total_mentions > 0 else 0.0
            )
