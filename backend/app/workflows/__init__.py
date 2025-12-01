"""
Workflows Package

데이터 수집 파이프라인 워크플로우.
"""
# Import simple workflow (no LangGraph dependency)
from app.workflows.simple_ingestion_workflow import (
    SimpleIngestionWorkflow,
    get_ingestion_workflow,
    PipelineStatus as SimplePipelineStatus,
    PipelineResult as SimplePipelineResult,
)

# Try to import LangGraph-based workflow if available
try:
    from app.workflows.state import (
        PipelineState,
        PipelineStatus,
        PipelineResult,
        WorkflowConfig,
        StepStatus,
        StepResult,
        BatchPipelineState,
    )
    from app.workflows.ingestion_workflow import IngestionWorkflow
    from app.workflows.orchestrator import (
        IngestionOrchestrator,
        process_single_document,
        process_directory,
    )

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

__all__ = [
    # Simple workflow (always available)
    "SimpleIngestionWorkflow",
    "get_ingestion_workflow",
    "SimplePipelineStatus",
    "SimplePipelineResult",
]

# Add LangGraph components if available
if LANGGRAPH_AVAILABLE:
    __all__.extend([
        # State models
        "PipelineState",
        "PipelineStatus",
        "PipelineResult",
        "WorkflowConfig",
        "StepStatus",
        "StepResult",
        "BatchPipelineState",
        # Workflow
        "IngestionWorkflow",
        # Orchestrator
        "IngestionOrchestrator",
        "process_single_document",
        "process_directory",
    ])
