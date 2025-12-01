"""
Pipeline Validator Service

전체 파이프라인 결과의 품질을 검증합니다.

Validation Checks:
1. Data Completeness - 모든 단계에서 데이터가 생성되었는지
2. Data Consistency - 데이터 간 일관성 (예: 금액 수 일치)
3. Data Quality - 데이터 품질 (예: 텍스트 길이, 중복 등)
4. Graph Integrity - Neo4j 그래프 무결성
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID

from app.services.pdf_text_extractor import PDFExtractionResult
from app.services.legal_structure_parser import ParsedDocument
from app.services.critical_data_extractor import ExtractionResult
from app.services.embedding_generator import EmbeddingResult
from app.services.neo4j_graph_builder import GraphStats
from loguru import logger


class ValidationSeverity(str, Enum):
    """Validation issue severity"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """A validation issue found during checks"""
    severity: ValidationSeverity
    category: str  # "completeness", "consistency", "quality", "graph"
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Result of pipeline validation"""
    passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
                   for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)

    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == severity]


class PipelineValidator:
    """
    Validates pipeline results for quality and consistency.

    Features:
    - Completeness checks (모든 데이터 생성 확인)
    - Consistency checks (데이터 간 일관성)
    - Quality checks (데이터 품질)
    - Graph integrity checks (Neo4j 그래프 무결성)
    """

    def __init__(
        self,
        min_text_chars: int = 100,
        min_articles: int = 1,
        max_article_length: int = 10000,
        embedding_dimension: int = 1536,
    ):
        """
        Initialize validator with thresholds.

        Args:
            min_text_chars: Minimum characters in extracted text
            min_articles: Minimum number of articles
            max_article_length: Maximum article length (detect issues)
            embedding_dimension: Expected embedding dimension
        """
        self.min_text_chars = min_text_chars
        self.min_articles = min_articles
        self.max_article_length = max_article_length
        self.embedding_dimension = embedding_dimension

    def validate_pipeline(
        self,
        pdf_result: Optional[PDFExtractionResult],
        parsed_doc: Optional[ParsedDocument],
        extracted_data: Optional[ExtractionResult],
        embeddings: Optional[EmbeddingResult],
        graph_stats: Optional[GraphStats],
    ) -> ValidationResult:
        """
        Validate complete pipeline results.

        Args:
            pdf_result: PDF extraction result
            parsed_doc: Parsed document
            extracted_data: Extracted critical data
            embeddings: Generated embeddings
            graph_stats: Graph construction stats

        Returns:
            ValidationResult with all issues
        """
        issues = []
        total_checks = 0
        passed_checks = 0

        # 1. Completeness Checks
        completeness_issues, comp_total, comp_passed = self._check_completeness(
            pdf_result, parsed_doc, extracted_data, embeddings, graph_stats
        )
        issues.extend(completeness_issues)
        total_checks += comp_total
        passed_checks += comp_passed

        # 2. Consistency Checks
        if all([pdf_result, parsed_doc, extracted_data, embeddings, graph_stats]):
            consistency_issues, cons_total, cons_passed = self._check_consistency(
                pdf_result, parsed_doc, extracted_data, embeddings, graph_stats
            )
            issues.extend(consistency_issues)
            total_checks += cons_total
            passed_checks += cons_passed

        # 3. Quality Checks
        if parsed_doc:
            quality_issues, qual_total, qual_passed = self._check_quality(parsed_doc)
            issues.extend(quality_issues)
            total_checks += qual_total
            passed_checks += qual_passed

        # 4. Graph Integrity
        if graph_stats:
            graph_issues, graph_total, graph_passed = self._check_graph_integrity(graph_stats)
            issues.extend(graph_issues)
            total_checks += graph_total
            passed_checks += graph_passed

        # Determine if passed
        passed = not any(issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
                        for issue in issues)

        result = ValidationResult(
            passed=passed,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            issues=issues,
        )

        # Log summary
        if passed:
            logger.info(f"Validation passed: {passed_checks}/{total_checks} checks")
        else:
            logger.warning(f"Validation failed: {len(issues)} issues found")
            for issue in issues:
                if issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    logger.error(f"[{issue.severity.value.upper()}] {issue.message}")

        return result

    def _check_completeness(
        self, pdf_result, parsed_doc, extracted_data, embeddings, graph_stats
    ) -> tuple[List[ValidationIssue], int, int]:
        """Check if all pipeline steps produced data"""
        issues = []
        total = 5
        passed = 0

        # Check PDF extraction
        if pdf_result is None:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="completeness",
                message="PDF extraction result is missing",
            ))
        elif pdf_result.total_chars < self.min_text_chars:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="completeness",
                message=f"Extracted text too short: {pdf_result.total_chars} chars (min: {self.min_text_chars})",
                details={"extracted_chars": pdf_result.total_chars},
            ))
        else:
            passed += 1

        # Check legal parsing
        if parsed_doc is None:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="completeness",
                message="Legal structure parsing result is missing",
            ))
        elif parsed_doc.total_articles < self.min_articles:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="completeness",
                message=f"Too few articles parsed: {parsed_doc.total_articles} (min: {self.min_articles})",
                details={"articles": parsed_doc.total_articles},
            ))
        else:
            passed += 1

        # Check data extraction
        if extracted_data is None:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="completeness",
                message="Critical data extraction result is missing",
            ))
        else:
            passed += 1

        # Check embeddings
        if embeddings is None:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="completeness",
                message="Embeddings generation result is missing",
            ))
        elif embeddings.total_embeddings == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="completeness",
                message="No embeddings generated",
            ))
        else:
            passed += 1

        # Check graph construction
        if graph_stats is None:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="completeness",
                message="Graph construction stats are missing",
            ))
        elif graph_stats.total_nodes == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="completeness",
                message="No nodes created in graph",
            ))
        else:
            passed += 1

        return issues, total, passed

    def _check_consistency(
        self, pdf_result, parsed_doc, extracted_data, embeddings, graph_stats
    ) -> tuple[List[ValidationIssue], int, int]:
        """Check consistency between pipeline stages"""
        issues = []
        total = 4
        passed = 0

        # Check article count consistency
        expected_nodes = (
            1  # Policy
            + parsed_doc.total_articles
            + parsed_doc.total_paragraphs
            + parsed_doc.total_subclauses
            + len(extracted_data.amounts)
            + len(extracted_data.periods)
            + len(extracted_data.kcd_codes)
        )

        if graph_stats.total_nodes != expected_nodes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="consistency",
                message=f"Graph node count mismatch: expected {expected_nodes}, got {graph_stats.total_nodes}",
                details={
                    "expected": expected_nodes,
                    "actual": graph_stats.total_nodes,
                    "difference": abs(expected_nodes - graph_stats.total_nodes),
                },
            ))
        else:
            passed += 1

        # Check embedding count
        expected_embeddings = (
            parsed_doc.total_articles
            + parsed_doc.total_paragraphs
            + parsed_doc.total_subclauses
        )

        if embeddings.total_embeddings != expected_embeddings:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="consistency",
                message=f"Embedding count mismatch: expected {expected_embeddings}, got {embeddings.total_embeddings}",
                details={
                    "expected": expected_embeddings,
                    "actual": embeddings.total_embeddings,
                },
            ))
        else:
            passed += 1

        # Check embedding dimensions
        if embeddings.embeddings:
            first_emb = embeddings.embeddings[0]
            if first_emb.dimension != self.embedding_dimension:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="consistency",
                    message=f"Incorrect embedding dimension: {first_emb.dimension} (expected: {self.embedding_dimension})",
                    details={"dimension": first_emb.dimension},
                ))
            else:
                passed += 1
        else:
            passed += 1

        # Check graph node breakdown
        expected_article_nodes = parsed_doc.total_articles
        if graph_stats.article_nodes != expected_article_nodes:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="consistency",
                message=f"Article node count mismatch in graph: expected {expected_article_nodes}, got {graph_stats.article_nodes}",
            ))
        else:
            passed += 1

        return issues, total, passed

    def _check_quality(self, parsed_doc) -> tuple[List[ValidationIssue], int, int]:
        """Check data quality"""
        issues = []
        total = 3
        passed = 0

        # Check for empty articles
        empty_articles = [a for a in parsed_doc.articles if not a.text and not a.paragraphs]
        if empty_articles:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                category="quality",
                message=f"Found {len(empty_articles)} empty articles",
                details={"empty_article_nums": [a.article_num for a in empty_articles]},
            ))
        else:
            passed += 1

        # Check for very long articles (potential parsing error)
        long_articles = [a for a in parsed_doc.articles if a.text and len(a.text) > self.max_article_length]
        if long_articles:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                category="quality",
                message=f"Found {len(long_articles)} unusually long articles",
                details={"long_article_nums": [a.article_num for a in long_articles]},
            ))
        else:
            passed += 1

        # Check for duplicate article numbers
        article_nums = [a.article_num for a in parsed_doc.articles]
        if len(article_nums) != len(set(article_nums)):
            duplicates = [num for num in article_nums if article_nums.count(num) > 1]
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category="quality",
                message=f"Found duplicate article numbers: {set(duplicates)}",
                details={"duplicate_nums": list(set(duplicates))},
            ))
        else:
            passed += 1

        return issues, total, passed

    def _check_graph_integrity(self, graph_stats) -> tuple[List[ValidationIssue], int, int]:
        """Check graph database integrity"""
        issues = []
        total = 2
        passed = 0

        # Check if policy node exists
        if graph_stats.policy_nodes != 1:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="graph",
                message=f"Expected exactly 1 policy node, got {graph_stats.policy_nodes}",
                details={"policy_nodes": graph_stats.policy_nodes},
            ))
        else:
            passed += 1

        # Check node distribution
        structural_nodes = (
            graph_stats.article_nodes
            + graph_stats.paragraph_nodes
            + graph_stats.subclause_nodes
        )
        entity_nodes = (
            graph_stats.amount_nodes
            + graph_stats.period_nodes
            + graph_stats.kcd_nodes
        )

        if structural_nodes == 0:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="graph",
                message="No structural nodes (articles/paragraphs) in graph",
            ))
        else:
            passed += 1

        return issues, total, passed


# Singleton instance
_validator: Optional[PipelineValidator] = None


def get_pipeline_validator() -> PipelineValidator:
    """Get or create singleton validator instance"""
    global _validator
    if _validator is None:
        _validator = PipelineValidator()
    return _validator


if __name__ == "__main__":
    # Test validator with sample data
    from app.services.legal_structure_parser import get_legal_parser
    from app.services.critical_data_extractor import get_critical_extractor
    from app.services.embedding_generator import get_embedding_generator
    from app.services.neo4j_graph_builder import get_graph_builder, GraphStats
    from uuid import uuid4

    sample_text = """제10조 [보험금 지급]
① 회사는 피보험자가 보험기간 중 암으로 진단 확정되었을 때 다음과 같이 보험금을 지급합니다.
1. 일반암(C77 제외): 1억원

② 다만, 계약일로부터 90일 이내 진단 확정된 경우 면책합니다.
"""

    print("=" * 70)
    print("🧪 Pipeline Validator Test")
    print("=" * 70)

    # Generate test data
    print("\n📊 Generating test data...")
    parser = get_legal_parser()
    parsed = parser.parse_text(sample_text)

    extractor = get_critical_extractor()
    extracted = extractor.extract_all(sample_text)

    emb_gen = get_embedding_generator()
    embeddings = emb_gen.generate_for_articles(parsed.articles)

    # Mock PDF result
    from app.services.pdf_text_extractor import PDFExtractionResult, PDFPage
    pdf_result = PDFExtractionResult(
        total_pages=1,
        total_chars=len(sample_text),
        pages=[PDFPage(1, sample_text, 595, 842, len(sample_text))],
        full_text=sample_text,
        metadata={},
    )

    # Create graph (will clean up after)
    builder = get_graph_builder()
    policy_id = uuid4()
    graph_stats = builder.build_graph(
        policy_id=policy_id,
        policy_name="테스트 보험",
        insurer="테스트사",
        articles=parsed.articles,
        extracted_data=extracted,
        embeddings=embeddings,
    )

    print(f"  ✓ Generated: {parsed.total_articles} articles, {len(extracted.amounts)} amounts, {graph_stats.total_nodes} nodes")

    # Validate
    print("\n🔍 Running validation...")
    validator = get_pipeline_validator()
    result = validator.validate_pipeline(
        pdf_result=pdf_result,
        parsed_doc=parsed,
        extracted_data=extracted,
        embeddings=embeddings,
        graph_stats=graph_stats,
    )

    print(f"\n{'='*70}")
    print(f"📊 Validation Result")
    print(f"{'='*70}")
    print(f"Passed: {result.passed}")
    print(f"Total Checks: {result.total_checks}")
    print(f"Passed: {result.passed_checks}")
    print(f"Failed: {result.failed_checks}")

    if result.issues:
        print(f"\n⚠️  Issues Found ({len(result.issues)}):")
        for issue in result.issues:
            icon = {
                ValidationSeverity.INFO: "ℹ️",
                ValidationSeverity.WARNING: "⚠️",
                ValidationSeverity.ERROR: "❌",
                ValidationSeverity.CRITICAL: "🔴",
            }[issue.severity]
            print(f"  {icon} [{issue.severity.value.upper()}] {issue.message}")
            if issue.details:
                print(f"     Details: {issue.details}")
    else:
        print(f"\n✅ No issues found!")

    # Cleanup
    builder.clear_policy(policy_id)
    builder.close()

    print("\n" + "=" * 70)
    print("✅ Validator test complete!")
    print("=" * 70)
