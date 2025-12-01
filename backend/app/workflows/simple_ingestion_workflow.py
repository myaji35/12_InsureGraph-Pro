"""
Simple Ingestion Workflow

전체 데이터 처리 파이프라인을 통합하는 간단한 워크플로우.

Pipeline Flow:
1. PDF Text Extraction
2. Legal Structure Parsing
3. Critical Data Extraction
4. Embedding Generation
5. Neo4j Graph Construction
6. Validation

각 단계는 독립적으로 실행 가능하며, 에러 발생 시 중단됩니다.
"""
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pathlib import Path

from loguru import logger

from app.services.pdf_text_extractor import get_pdf_extractor, PDFExtractionResult
from app.services.legal_structure_parser import get_legal_parser, ParsedDocument
from app.services.critical_data_extractor import get_critical_extractor, ExtractionResult
from app.services.embedding_generator import get_embedding_generator, EmbeddingResult
from app.services.neo4j_graph_builder import get_graph_builder, GraphStats


class PipelineStatus(str, Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineMetrics:
    """Pipeline execution metrics"""
    total_pages: int = 0
    total_chars: int = 0
    total_articles: int = 0
    total_paragraphs: int = 0
    total_subclauses: int = 0
    total_amounts: int = 0
    total_periods: int = 0
    total_kcd_codes: int = 0
    total_embeddings: int = 0
    graph_nodes: int = 0
    graph_relationships: int = 0


@dataclass
class PipelineResult:
    """Result of pipeline execution"""
    pipeline_id: UUID
    status: PipelineStatus
    policy_id: UUID
    policy_name: str
    insurer: str

    # Execution info
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Metrics
    metrics: PipelineMetrics = field(default_factory=PipelineMetrics)

    # Error info
    error: Optional[str] = None
    error_step: Optional[str] = None

    # Intermediate results (for debugging)
    pdf_result: Optional[PDFExtractionResult] = None
    parsed_doc: Optional[ParsedDocument] = None
    extracted_data: Optional[ExtractionResult] = None
    embeddings: Optional[EmbeddingResult] = None
    graph_stats: Optional[GraphStats] = None


class SimpleIngestionWorkflow:
    """
    Simple ingestion workflow that integrates all data processing steps.

    Features:
    - Sequential execution with clear error handling
    - Progress tracking
    - Metrics collection
    - Rollback on failure
    """

    def __init__(self, use_mock_embeddings: bool = False):
        """
        Initialize workflow.

        Args:
            use_mock_embeddings: Use mock embeddings instead of OpenAI API
        """
        self.use_mock_embeddings = use_mock_embeddings

        # Initialize services
        self.pdf_extractor = get_pdf_extractor()
        self.legal_parser = get_legal_parser()
        self.critical_extractor = get_critical_extractor()
        self.embedding_generator = get_embedding_generator()
        self.graph_builder = get_graph_builder()

        logger.info("SimpleIngestionWorkflow initialized")

    async def run(
        self,
        pdf_path: str,
        policy_name: str,
        insurer: str,
        policy_id: Optional[UUID] = None,
        progress_callback: Optional[callable] = None,
    ) -> PipelineResult:
        """
        Run the complete ingestion pipeline.

        Args:
            pdf_path: Path to PDF file
            policy_name: Name of the insurance policy
            insurer: Insurance company name
            policy_id: Optional policy ID (will be generated if not provided)
            progress_callback: Optional callback for progress updates (step_name, progress_pct)

        Returns:
            PipelineResult with execution details
        """
        # Initialize result
        policy_id = policy_id or uuid4()
        pipeline_id = uuid4()
        result = PipelineResult(
            pipeline_id=pipeline_id,
            status=PipelineStatus.PENDING,
            policy_id=policy_id,
            policy_name=policy_name,
            insurer=insurer,
            start_time=datetime.utcnow(),
        )

        logger.info(f"Starting pipeline {pipeline_id} for policy {policy_id}")

        try:
            result.status = PipelineStatus.RUNNING

            # Step 1: PDF Text Extraction
            logger.info(f"[Step 1/6] PDF Text Extraction: {pdf_path}")
            if progress_callback:
                await progress_callback("pdf_extraction", 0)

            pdf_result = await self._extract_text(pdf_path)
            result.pdf_result = pdf_result
            result.metrics.total_pages = pdf_result.total_pages
            result.metrics.total_chars = pdf_result.total_chars

            if progress_callback:
                await progress_callback("pdf_extraction", 100)
            logger.info(f"  ✓ Extracted {pdf_result.total_pages} pages, {pdf_result.total_chars:,} chars")

            # Step 2: Legal Structure Parsing
            logger.info(f"[Step 2/6] Legal Structure Parsing")
            if progress_callback:
                await progress_callback("legal_parsing", 0)

            parsed_doc = await self._parse_structure(pdf_result.full_text)
            result.parsed_doc = parsed_doc
            result.metrics.total_articles = parsed_doc.total_articles
            result.metrics.total_paragraphs = parsed_doc.total_paragraphs
            result.metrics.total_subclauses = parsed_doc.total_subclauses

            if progress_callback:
                await progress_callback("legal_parsing", 100)
            logger.info(
                f"  ✓ Parsed {parsed_doc.total_articles} articles, "
                f"{parsed_doc.total_paragraphs} paragraphs, "
                f"{parsed_doc.total_subclauses} subclauses"
            )

            # Step 3: Critical Data Extraction
            logger.info(f"[Step 3/6] Critical Data Extraction")
            if progress_callback:
                await progress_callback("data_extraction", 0)

            extracted_data = await self._extract_critical_data(pdf_result.full_text)
            result.extracted_data = extracted_data
            result.metrics.total_amounts = len(extracted_data.amounts)
            result.metrics.total_periods = len(extracted_data.periods)
            result.metrics.total_kcd_codes = len(extracted_data.kcd_codes)

            if progress_callback:
                await progress_callback("data_extraction", 100)
            logger.info(
                f"  ✓ Extracted {len(extracted_data.amounts)} amounts, "
                f"{len(extracted_data.periods)} periods, "
                f"{len(extracted_data.kcd_codes)} KCD codes"
            )

            # Step 4: Embedding Generation
            logger.info(f"[Step 4/6] Embedding Generation")
            if progress_callback:
                await progress_callback("embedding_generation", 0)

            embeddings = await self._generate_embeddings(parsed_doc.articles)
            result.embeddings = embeddings
            result.metrics.total_embeddings = embeddings.total_embeddings

            if progress_callback:
                await progress_callback("embedding_generation", 100)
            logger.info(
                f"  ✓ Generated {embeddings.total_embeddings} embeddings "
                f"(~{embeddings.total_tokens:,} tokens)"
            )

            # Step 5: Neo4j Graph Construction
            logger.info(f"[Step 5/6] Neo4j Graph Construction")
            if progress_callback:
                await progress_callback("graph_construction", 0)

            graph_stats = await self._build_graph(
                policy_id=policy_id,
                policy_name=policy_name,
                insurer=insurer,
                articles=parsed_doc.articles,
                extracted_data=extracted_data,
                embeddings=embeddings,
            )
            result.graph_stats = graph_stats
            result.metrics.graph_nodes = graph_stats.total_nodes
            result.metrics.graph_relationships = graph_stats.relationships

            if progress_callback:
                await progress_callback("graph_construction", 100)
            logger.info(
                f"  ✓ Built graph with {graph_stats.total_nodes} nodes, "
                f"{graph_stats.relationships} relationships"
            )

            # Step 6: Validation
            logger.info(f"[Step 6/6] Validation")
            if progress_callback:
                await progress_callback("validation", 0)

            await self._validate(result)

            if progress_callback:
                await progress_callback("validation", 100)
            logger.info(f"  ✓ Validation passed")

            # Finalize
            result.status = PipelineStatus.COMPLETED
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()

            logger.info(
                f"Pipeline {pipeline_id} completed in {result.duration_seconds:.2f}s"
            )

        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} failed: {e}", exc_info=True)
            result.status = PipelineStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()

        return result

    async def _extract_text(self, pdf_path: str) -> PDFExtractionResult:
        """Step 1: Extract text from PDF"""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.pdf_extractor.extract_text_from_file,
            pdf_path
        )

    async def _parse_structure(self, text: str) -> ParsedDocument:
        """Step 2: Parse legal structure"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.legal_parser.parse_text,
            text
        )

    async def _extract_critical_data(self, text: str) -> ExtractionResult:
        """Step 3: Extract critical data"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.critical_extractor.extract_all,
            text
        )

    async def _generate_embeddings(self, articles) -> EmbeddingResult:
        """Step 4: Generate embeddings"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.embedding_generator.generate_for_articles,
            articles
        )

    async def _build_graph(
        self,
        policy_id: UUID,
        policy_name: str,
        insurer: str,
        articles,
        extracted_data,
        embeddings,
    ) -> GraphStats:
        """Step 5: Build Neo4j graph"""
        # Create constraints first
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.graph_builder.create_constraints)

        # Build graph
        return await loop.run_in_executor(
            None,
            self.graph_builder.build_graph,
            policy_id,
            policy_name,
            insurer,
            articles,
            extracted_data,
            embeddings,
        )

    async def _validate(self, result: PipelineResult):
        """Step 6: Validate results"""
        # Basic validation
        if result.metrics.total_pages == 0:
            raise ValueError("No pages extracted from PDF")

        if result.metrics.total_articles == 0:
            raise ValueError("No articles parsed from text")

        if result.metrics.graph_nodes == 0:
            raise ValueError("No nodes created in graph")

        # Check consistency
        expected_nodes = (
            1  # Policy
            + result.metrics.total_articles
            + result.metrics.total_paragraphs
            + result.metrics.total_subclauses
            + result.metrics.total_amounts
            + result.metrics.total_periods
            + result.metrics.total_kcd_codes
        )

        if result.metrics.graph_nodes != expected_nodes:
            logger.warning(
                f"Graph node count mismatch: expected {expected_nodes}, got {result.metrics.graph_nodes}"
            )


# Singleton instance
_workflow: Optional[SimpleIngestionWorkflow] = None


def get_ingestion_workflow() -> SimpleIngestionWorkflow:
    """Get or create singleton workflow instance"""
    global _workflow
    if _workflow is None:
        _workflow = SimpleIngestionWorkflow()
    return _workflow


if __name__ == "__main__":
    # Test workflow
    import sys

    async def progress_callback(step: str, progress: int):
        """Progress callback for testing"""
        print(f"  [{step}] {progress}%")

    async def test_workflow():
        print("=" * 70)
        print("🧪 Simple Ingestion Workflow Test")
        print("=" * 70)

        # Check if PDF path provided
        if len(sys.argv) > 1:
            pdf_path = sys.argv[1]
        else:
            # Use test data
            print("\n⚠️  No PDF provided, creating test PDF path")
            pdf_path = "test_policy.pdf"

        workflow = get_ingestion_workflow()

        result = await workflow.run(
            pdf_path=pdf_path,
            policy_name="테스트 암보험",
            insurer="테스트 보험사",
            progress_callback=progress_callback,
        )

        print(f"\n{'='*70}")
        print(f"📊 Pipeline Result")
        print(f"{'='*70}")
        print(f"Status: {result.status.value}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print(f"\nMetrics:")
        print(f"  Pages: {result.metrics.total_pages}")
        print(f"  Articles: {result.metrics.total_articles}")
        print(f"  Paragraphs: {result.metrics.total_paragraphs}")
        print(f"  Subclauses: {result.metrics.total_subclauses}")
        print(f"  Amounts: {result.metrics.total_amounts}")
        print(f"  Periods: {result.metrics.total_periods}")
        print(f"  KCD Codes: {result.metrics.total_kcd_codes}")
        print(f"  Embeddings: {result.metrics.total_embeddings}")
        print(f"  Graph Nodes: {result.metrics.graph_nodes}")
        print(f"  Graph Relationships: {result.metrics.graph_relationships}")

        if result.status == PipelineStatus.FAILED:
            print(f"\n❌ Error: {result.error}")
            print(f"   Failed at: {result.error_step}")
        else:
            print(f"\n✅ Pipeline completed successfully!")

        print("=" * 70)

    asyncio.run(test_workflow())
