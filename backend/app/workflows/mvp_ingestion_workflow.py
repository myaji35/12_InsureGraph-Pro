"""
MVP Ingestion Workflow

Simplified ingestion pipeline for MVP that saves to PostgreSQL instead of Neo4j.

Pipeline Flow:
1. PDF Text Extraction
2. Legal Structure Parsing
3. Critical Data Extraction
4. Save to PostgreSQL

This workflow is faster and simpler than the full workflow, suitable for MVP.
"""
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pathlib import Path

from loguru import logger

from app.services.pdf_text_extractor import get_pdf_extractor, PDFExtractionResult
from app.services.legal_structure_parser import get_legal_parser, ParsedDocument
from app.services.critical_data_extractor import get_critical_extractor, ExtractionResult
from app.repositories.document_repository import get_document_repository, DocumentRepository


class MVPPipelineStatus(str, Enum):
    """MVP Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MVPPipelineResult:
    """Result of MVP pipeline execution"""
    pipeline_id: UUID
    status: MVPPipelineStatus
    policy_id: Optional[UUID]
    policy_name: str
    insurer: str

    # Execution info
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Document ID in PostgreSQL
    document_id: Optional[UUID] = None

    # Metrics
    total_pages: int = 0
    total_chars: int = 0
    total_articles: int = 0
    total_paragraphs: int = 0
    total_subclauses: int = 0
    total_amounts: int = 0
    total_periods: int = 0
    total_kcd_codes: int = 0

    # Error info
    error: Optional[str] = None
    error_step: Optional[str] = None


class MVPIngestionWorkflow:
    """
    MVP ingestion workflow that saves to PostgreSQL.

    Features:
    - Sequential execution with clear error handling
    - Progress tracking
    - PostgreSQL storage (no Neo4j dependency)
    - Fast and simple
    """

    def __init__(self, document_repo: Optional[DocumentRepository] = None):
        """
        Initialize workflow.

        Args:
            document_repo: Optional DocumentRepository instance
        """
        # Initialize services
        self.pdf_extractor = get_pdf_extractor()
        self.legal_parser = get_legal_parser()
        self.critical_extractor = get_critical_extractor()
        self.document_repo = document_repo or get_document_repository()

        logger.info("MVPIngestionWorkflow initialized")

    async def run(
        self,
        pdf_path: str,
        policy_name: str,
        insurer: str,
        policy_id: Optional[UUID] = None,
        progress_callback: Optional[callable] = None,
    ) -> MVPPipelineResult:
        """
        Run the MVP ingestion pipeline.

        Args:
            pdf_path: Path to PDF file
            policy_name: Name of the insurance policy
            insurer: Insurance company name
            policy_id: Optional policy ID (will be generated if not provided)
            progress_callback: Optional callback for progress updates (step_name, progress_pct)

        Returns:
            MVPPipelineResult with execution details
        """
        # Initialize result
        policy_id = policy_id or uuid4()
        pipeline_id = uuid4()
        result = MVPPipelineResult(
            pipeline_id=pipeline_id,
            status=MVPPipelineStatus.PENDING,
            policy_id=policy_id,
            policy_name=policy_name,
            insurer=insurer,
            start_time=datetime.utcnow(),
        )

        logger.info(f"Starting MVP pipeline {pipeline_id} for policy {policy_id}")

        try:
            result.status = MVPPipelineStatus.RUNNING

            # Step 1: PDF Text Extraction
            logger.info(f"[Step 1/4] PDF Text Extraction: {pdf_path}")
            if progress_callback:
                await progress_callback("pdf_extraction", 0)

            pdf_result = await self._extract_text(pdf_path)
            result.total_pages = pdf_result.total_pages
            result.total_chars = pdf_result.total_chars

            if progress_callback:
                await progress_callback("pdf_extraction", 100)
            logger.info(f"  ✓ Extracted {pdf_result.total_pages} pages, {pdf_result.total_chars:,} chars")

            # Step 2: Legal Structure Parsing
            logger.info(f"[Step 2/4] Legal Structure Parsing")
            if progress_callback:
                await progress_callback("legal_parsing", 0)

            parsed_doc = await self._parse_structure(pdf_result.full_text)
            result.total_articles = parsed_doc.total_articles
            result.total_paragraphs = parsed_doc.total_paragraphs
            result.total_subclauses = parsed_doc.total_subclauses

            if progress_callback:
                await progress_callback("legal_parsing", 100)
            logger.info(
                f"  ✓ Parsed {parsed_doc.total_articles} articles, "
                f"{parsed_doc.total_paragraphs} paragraphs, "
                f"{parsed_doc.total_subclauses} subclauses"
            )

            # Step 3: Critical Data Extraction
            logger.info(f"[Step 3/4] Critical Data Extraction")
            if progress_callback:
                await progress_callback("data_extraction", 0)

            extracted_data = await self._extract_critical_data(pdf_result.full_text)
            result.total_amounts = len(extracted_data.amounts)
            result.total_periods = len(extracted_data.periods)
            result.total_kcd_codes = len(extracted_data.kcd_codes)

            if progress_callback:
                await progress_callback("data_extraction", 100)
            logger.info(
                f"  ✓ Extracted {len(extracted_data.amounts)} amounts, "
                f"{len(extracted_data.periods)} periods, "
                f"{len(extracted_data.kcd_codes)} KCD codes"
            )

            # Step 4: Save to PostgreSQL
            logger.info(f"[Step 4/4] Saving to PostgreSQL")
            if progress_callback:
                await progress_callback("database_save", 0)

            document = await self._save_to_database(
                policy_id=policy_id,
                policy_name=policy_name,
                insurer=insurer,
                full_text=pdf_result.full_text,
                parsed_doc=parsed_doc,
                extracted_data=extracted_data,
                total_pages=result.total_pages,
                total_chars=result.total_chars,
            )
            result.document_id = UUID(document["id"])

            if progress_callback:
                await progress_callback("database_save", 100)
            logger.info(f"  ✓ Saved document {result.document_id}")

            # Finalize
            result.status = MVPPipelineStatus.COMPLETED
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()

            logger.info(
                f"MVP Pipeline {pipeline_id} completed in {result.duration_seconds:.2f}s"
            )

        except Exception as e:
            logger.error(f"MVP Pipeline {pipeline_id} failed: {e}", exc_info=True)
            result.status = MVPPipelineStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()

        return result

    async def _extract_text(self, pdf_path: str) -> PDFExtractionResult:
        """Step 1: Extract text from PDF"""
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

    async def _save_to_database(
        self,
        policy_id: UUID,
        policy_name: str,
        insurer: str,
        full_text: str,
        parsed_doc: ParsedDocument,
        extracted_data: ExtractionResult,
        total_pages: int,
        total_chars: int,
    ) -> Dict[str, Any]:
        """Step 4: Save to PostgreSQL"""
        loop = asyncio.get_event_loop()

        # Convert Pydantic models to dicts (Pydantic v2)
        from loguru import logger
        logger.debug(f"Converting parsed_doc (type: {type(parsed_doc)})")
        parsed_structure = parsed_doc.model_dump() if hasattr(parsed_doc, 'model_dump') else parsed_doc.dict()

        logger.debug(f"Converting extracted_data (type: {type(extracted_data)})")
        critical_data = extracted_data.model_dump() if hasattr(extracted_data, 'model_dump') else extracted_data.dict()

        # Save to database
        return await loop.run_in_executor(
            None,
            self.document_repo.create,
            policy_name,
            insurer,
            full_text,
            parsed_structure,
            critical_data,
            policy_id,
            # Metadata
            total_pages,
            total_chars,
            parsed_doc.total_articles,
            parsed_doc.get_total_paragraphs(),
            parsed_doc.get_total_subclauses(),
            len(extracted_data.amounts),
            len(extracted_data.periods),
            len(extracted_data.kcd_codes),
        )


# Singleton instance
_workflow: Optional[MVPIngestionWorkflow] = None


def get_mvp_workflow() -> MVPIngestionWorkflow:
    """Get or create singleton workflow instance"""
    global _workflow
    if _workflow is None:
        _workflow = MVPIngestionWorkflow()
    return _workflow


if __name__ == "__main__":
    # Test workflow
    import sys

    async def progress_callback(step: str, progress: int):
        """Progress callback for testing"""
        print(f"  [{step}] {progress}%")

    async def test_workflow():
        print("=" * 70)
        print("🧪 MVP Ingestion Workflow Test")
        print("=" * 70)

        # Check if PDF path provided
        if len(sys.argv) > 1:
            pdf_path = sys.argv[1]
        else:
            print("\n⚠️  Usage: python mvp_ingestion_workflow.py <pdf_path>")
            print("   Example: python mvp_ingestion_workflow.py test_policy.pdf")
            return

        workflow = get_mvp_workflow()

        result = await workflow.run(
            pdf_path=pdf_path,
            policy_name="테스트 암보험",
            insurer="테스트 보험사",
            progress_callback=progress_callback,
        )

        print(f"\n{'='*70}")
        print(f"📊 MVP Pipeline Result")
        print(f"{'='*70}")
        print(f"Status: {result.status.value}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print(f"Document ID: {result.document_id}")
        print(f"\nMetrics:")
        print(f"  Pages: {result.total_pages}")
        print(f"  Chars: {result.total_chars:,}")
        print(f"  Articles: {result.total_articles}")
        print(f"  Paragraphs: {result.total_paragraphs}")
        print(f"  Subclauses: {result.total_subclauses}")
        print(f"  Amounts: {result.total_amounts}")
        print(f"  Periods: {result.total_periods}")
        print(f"  KCD Codes: {result.total_kcd_codes}")

        if result.status == MVPPipelineStatus.FAILED:
            print(f"\n❌ Error: {result.error}")
            print(f"   Failed at: {result.error_step}")
        else:
            print(f"\n✅ Pipeline completed successfully!")
            print(f"   Search for this document at /api/v1/search")

        print("=" * 70)

    asyncio.run(test_workflow())
