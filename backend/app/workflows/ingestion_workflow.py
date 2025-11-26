"""
Ingestion Workflow

LangGraph를 사용한 데이터 수집 파이프라인 워크플로우.
각 단계를 노드로 정의하고 순차적으로 실행합니다.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END

from app.workflows.state import PipelineState, PipelineStatus, WorkflowConfig
from app.services.ingestion.legal_parser import LegalStructureParser
from app.services.ingestion.critical_data_extractor import CriticalDataExtractor
from app.services.ingestion.relation_extractor import RelationExtractor
from app.services.ingestion.entity_linker import EntityLinker
from app.services.graph.neo4j_service import Neo4jService
from app.services.graph.embedding_service import create_embedding_service
from app.services.graph.graph_builder import GraphBuilder

logger = logging.getLogger(__name__)


class IngestionWorkflow:
    """데이터 수집 파이프라인 워크플로우"""

    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        워크플로우 초기화

        Args:
            config: 워크플로우 설정
        """
        self.config = config or WorkflowConfig()

        # 컴포넌트 초기화
        self.legal_parser = LegalStructureParser()
        self.critical_extractor = CriticalDataExtractor()
        self.relation_extractor = RelationExtractor()
        self.entity_linker = EntityLinker()

        # Neo4j와 임베딩 서비스는 나중에 초기화 (connection 필요)
        self.neo4j_service: Optional[Neo4jService] = None
        self.graph_builder: Optional[GraphBuilder] = None

        # 워크플로우 그래프 구축
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """LangGraph 워크플로우 그래프 구축"""
        # StateGraph 생성
        workflow = StateGraph(PipelineState)

        # 각 단계를 노드로 추가
        workflow.add_node("initialize", self._initialize_step)
        workflow.add_node("extract_ocr", self._extract_ocr_step)
        workflow.add_node("parse_structure", self._parse_structure_step)
        workflow.add_node("extract_critical_data", self._extract_critical_data_step)
        workflow.add_node("extract_relations", self._extract_relations_step)
        workflow.add_node("link_entities", self._link_entities_step)
        workflow.add_node("build_graph", self._build_graph_step)
        workflow.add_node("validate", self._validate_step)
        workflow.add_node("finalize", self._finalize_step)

        # 엣지 추가 (단계 간 연결)
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "extract_ocr")
        workflow.add_edge("extract_ocr", "parse_structure")
        workflow.add_edge("parse_structure", "extract_critical_data")
        workflow.add_edge("extract_critical_data", "extract_relations")
        workflow.add_edge("extract_relations", "link_entities")
        workflow.add_edge("link_entities", "build_graph")
        workflow.add_edge("build_graph", "validate")
        workflow.add_edge("validate", "finalize")
        workflow.add_edge("finalize", END)

        return workflow.compile()

    async def _initialize_step(self, state: PipelineState) -> PipelineState:
        """
        Step 0: 초기화
        파이프라인 시작 및 설정 확인
        """
        logger.info(f"[Step 0] 파이프라인 초기화: {state.pipeline_id}")

        state.mark_step_started("initialize")
        state.status = PipelineStatus.RUNNING
        state.start_time = datetime.utcnow()

        try:
            # 필수 입력 검증
            if not state.pdf_path:
                raise ValueError("PDF 경로가 제공되지 않았습니다")
            if not state.product_info:
                raise ValueError("제품 정보가 제공되지 않았습니다")

            # Neo4j 서비스 초기화
            if not self.neo4j_service:
                self.neo4j_service = Neo4jService(
                    uri=self.config.neo4j_uri,
                    user=self.config.neo4j_user,
                    password=self.config.neo4j_password,
                )
                self.neo4j_service.connect()

            # 임베딩 서비스 초기화
            if self.config.generate_embeddings and not self.graph_builder:
                embedding_service = create_embedding_service(
                    provider=self.config.embedding_provider
                )
                self.graph_builder = GraphBuilder(
                    neo4j_service=self.neo4j_service,
                    embedding_service=embedding_service,
                )
            elif not self.graph_builder:
                self.graph_builder = GraphBuilder(
                    neo4j_service=self.neo4j_service,
                    embedding_service=None,
                )

            state.mark_step_completed("initialize", {"status": "initialized"})
            logger.info(f"[Step 0] 초기화 완료")

        except Exception as e:
            logger.error(f"[Step 0] 초기화 실패: {e}")
            state.mark_step_failed("initialize", str(e))

        return state

    async def _extract_ocr_step(self, state: PipelineState) -> PipelineState:
        """
        Step 1: OCR 텍스트 추출
        PDF에서 텍스트를 추출합니다 (실제로는 이미 추출된 텍스트 사용)
        """
        logger.info(f"[Step 1] OCR 텍스트 추출 시작")

        state.mark_step_started("extract_ocr")

        try:
            # 실제 구현에서는 Upstage Document Parse API 호출
            # 여기서는 파일에서 읽기로 간소화
            with open(state.pdf_path, 'r', encoding='utf-8') as f:
                ocr_text = f.read()

            state.ocr_text = ocr_text

            state.mark_step_completed(
                "extract_ocr",
                {"text_length": len(ocr_text), "status": "extracted"}
            )
            logger.info(f"[Step 1] OCR 추출 완료: {len(ocr_text)} 글자")

        except Exception as e:
            logger.error(f"[Step 1] OCR 추출 실패: {e}")
            state.mark_step_failed("extract_ocr", str(e))

        return state

    async def _parse_structure_step(self, state: PipelineState) -> PipelineState:
        """
        Step 2: 법률 문서 구조 파싱 (Story 1.3)
        제N조, ①항, 가.나.다. 등의 계층 구조 파싱
        """
        logger.info(f"[Step 2] 문서 구조 파싱 시작")

        state.mark_step_started("parse_structure")

        try:
            # LegalStructureParser 사용
            parsed_doc = self.legal_parser.parse(state.ocr_text)

            # Pydantic 모델을 dict로 변환하여 저장
            state.parsed_document = parsed_doc.model_dump()

            state.mark_step_completed(
                "parse_structure",
                {
                    "total_articles": len(parsed_doc.articles),
                    "total_paragraphs": sum(len(a.paragraphs) for a in parsed_doc.articles),
                    "status": "parsed"
                }
            )
            logger.info(f"[Step 2] 구조 파싱 완료: {len(parsed_doc.articles)}개 조항")

        except Exception as e:
            logger.error(f"[Step 2] 구조 파싱 실패: {e}")
            state.mark_step_failed("parse_structure", str(e))

        return state

    async def _extract_critical_data_step(self, state: PipelineState) -> PipelineState:
        """
        Step 3: 핵심 데이터 추출 (Story 1.4)
        금액, 기간, KCD 코드 등의 정형 데이터 추출
        """
        logger.info(f"[Step 3] 핵심 데이터 추출 시작")

        state.mark_step_started("extract_critical_data")

        try:
            # CriticalDataExtractor 사용
            critical_data = self.critical_extractor.extract(state.ocr_text)

            # dict로 변환하여 저장
            state.critical_data = critical_data.model_dump()

            state.mark_step_completed(
                "extract_critical_data",
                {
                    "amounts_count": len(critical_data.amounts),
                    "periods_count": len(critical_data.periods),
                    "kcd_codes_count": len(critical_data.kcd_codes),
                    "status": "extracted"
                }
            )
            logger.info(
                f"[Step 3] 핵심 데이터 추출 완료: "
                f"금액 {len(critical_data.amounts)}개, "
                f"기간 {len(critical_data.periods)}개, "
                f"KCD 코드 {len(critical_data.kcd_codes)}개"
            )

        except Exception as e:
            logger.error(f"[Step 3] 핵심 데이터 추출 실패: {e}")
            state.mark_step_failed("extract_critical_data", str(e))

        return state

    async def _extract_relations_step(self, state: PipelineState) -> PipelineState:
        """
        Step 4: 관계 추출 (Story 1.5)
        LLM을 사용하여 보장-질병 관계 추출
        """
        logger.info(f"[Step 4] 관계 추출 시작")

        state.mark_step_started("extract_relations")

        try:
            from app.models.document import ParsedDocument
            from app.models.critical_data import CriticalData

            # dict를 다시 Pydantic 모델로 변환
            parsed_doc = ParsedDocument(**state.parsed_document)
            critical_data = CriticalData(**state.critical_data)

            # 각 paragraph에 대해 관계 추출
            all_relations = []
            for article in parsed_doc.articles:
                for paragraph in article.paragraphs:
                    result = await self.relation_extractor.extract(
                        clause_text=paragraph.text,
                        critical_data=critical_data,
                        use_cascade=self.config.use_cascade,
                    )
                    all_relations.append(result.model_dump())

            state.relations = all_relations

            # 총 관계 수 계산
            total_relations = sum(len(r.get("relations", [])) for r in all_relations)

            state.mark_step_completed(
                "extract_relations",
                {
                    "total_clauses": len(all_relations),
                    "total_relations": total_relations,
                    "status": "extracted"
                }
            )
            logger.info(f"[Step 4] 관계 추출 완료: {total_relations}개 관계")

        except Exception as e:
            logger.error(f"[Step 4] 관계 추출 실패: {e}")
            state.mark_step_failed("extract_relations", str(e))

        return state

    async def _link_entities_step(self, state: PipelineState) -> PipelineState:
        """
        Step 5: 엔티티 연결 (Story 1.6)
        질병 명칭을 표준 온톨로지에 연결
        """
        logger.info(f"[Step 5] 엔티티 연결 시작")

        state.mark_step_started("link_entities")

        try:
            entity_links = {}
            total_linked = 0
            total_unlinked = 0

            # 모든 관계에서 질병 엔티티 추출 및 연결
            for relation_result in state.relations:
                for relation in relation_result.get("relations", []):
                    disease_mention = relation.get("object")
                    if not disease_mention:
                        continue

                    # 이미 연결한 엔티티는 스킵
                    if disease_mention in entity_links:
                        continue

                    # EntityLinker로 연결
                    link_result = self.entity_linker.link(
                        disease_mention,
                        use_fuzzy=self.config.use_fuzzy_matching,
                        fuzzy_threshold=self.config.fuzzy_threshold,
                    )

                    entity_links[disease_mention] = link_result.model_dump()

                    if link_result.is_successful():
                        total_linked += 1
                    else:
                        total_unlinked += 1

            state.entity_links = entity_links

            state.mark_step_completed(
                "link_entities",
                {
                    "total_entities": len(entity_links),
                    "linked": total_linked,
                    "unlinked": total_unlinked,
                    "link_rate": f"{(total_linked / len(entity_links) * 100):.1f}%" if entity_links else "N/A",
                    "status": "linked"
                }
            )
            logger.info(
                f"[Step 5] 엔티티 연결 완료: "
                f"{total_linked}/{len(entity_links)}개 연결됨 "
                f"({total_linked / len(entity_links) * 100:.1f}%)"
            )

        except Exception as e:
            logger.error(f"[Step 5] 엔티티 연결 실패: {e}")
            state.mark_step_failed("link_entities", str(e))

        return state

    async def _build_graph_step(self, state: PipelineState) -> PipelineState:
        """
        Step 6: Neo4j 그래프 구축 (Story 1.7)
        모든 데이터를 Neo4j 지식 그래프로 구축
        """
        logger.info(f"[Step 6] 그래프 구축 시작")

        state.mark_step_started("build_graph")

        try:
            # GraphBuilder로 그래프 구축
            stats = await self.graph_builder.build_graph_from_document(
                ocr_text=state.ocr_text,
                product_info=state.product_info,
                generate_embeddings=self.config.generate_embeddings,
            )

            state.graph_stats = stats.model_dump()

            state.mark_step_completed(
                "build_graph",
                {
                    "total_nodes": stats.total_nodes,
                    "total_relationships": stats.total_relationships,
                    "construction_time": stats.construction_time_seconds,
                    "status": "constructed"
                }
            )
            logger.info(
                f"[Step 6] 그래프 구축 완료: "
                f"{stats.total_nodes}개 노드, "
                f"{stats.total_relationships}개 관계"
            )

        except Exception as e:
            logger.error(f"[Step 6] 그래프 구축 실패: {e}")
            state.mark_step_failed("build_graph", str(e))

        return state

    async def _validate_step(self, state: PipelineState) -> PipelineState:
        """
        Step 7: 검증 (Story 1.9)
        데이터와 그래프의 품질 검증
        """
        logger.info(f"[Step 7] 종합 검증 시작")

        state.mark_step_started("validate")

        try:
            # Story 1.9: ComprehensiveValidator 사용
            from app.services.qa.validator import ComprehensiveValidator

            validator = ComprehensiveValidator(neo4j_service=self.neo4j_service)

            # 전체 검증 수행
            report = await validator.validate_all(
                pipeline_id=state.pipeline_id,
                parsed_document=state.parsed_document,
                critical_data=state.critical_data,
                relations=state.relations,
                entity_links=state.entity_links,
                graph_stats=state.graph_stats,
                neo4j_service=self.neo4j_service,
            )

            # 검증 리포트 출력
            if self.config.verbose:
                logger.info("\n" + report.print_report())
            else:
                logger.info(report.get_summary())

            # 품질 임계값 확인 (기본: 0.7)
            quality_threshold = 0.7
            if not validator.validate_quality_threshold(report, quality_threshold):
                logger.warning(
                    f"품질 점수가 임계값보다 낮습니다: "
                    f"{report.quality_metrics.overall_score:.2f} < {quality_threshold}"
                )

            # 검증 결과를 상태에 저장
            state.mark_step_completed(
                "validate",
                {
                    "validation_passed": report.is_valid,
                    "quality_score": report.quality_metrics.overall_score,
                    "quality_grade": report.quality_metrics.get_grade(),
                    "total_issues": report.total_issues,
                    "critical_issues": report.critical_issues,
                    "errors": report.errors,
                    "warnings": report.warnings,
                    "status": "validated"
                }
            )

            # 치명적 이슈가 있으면 에러로 처리
            if report.critical_issues > 0:
                critical = report.get_all_issues()[:3]  # 처음 3개만
                error_msg = f"치명적 이슈 {report.critical_issues}개: {[str(i) for i in critical]}"
                logger.error(error_msg)
                # 하지만 파이프라인은 계속 진행 (경고만)

            logger.info(f"[Step 7] 검증 완료: {report.get_summary()}")

        except Exception as e:
            logger.error(f"[Step 7] 검증 실패: {e}")
            state.mark_step_failed("validate", str(e))

        return state

    async def _finalize_step(self, state: PipelineState) -> PipelineState:
        """
        Step 8: 마무리
        파이프라인 완료 처리
        """
        logger.info(f"[Step 8] 파이프라인 마무리")

        state.mark_step_started("finalize")

        try:
            # 전체 상태 업데이트
            state.end_time = datetime.utcnow()

            # 실패한 단계가 있는지 확인
            failed_steps = state.get_failed_steps()
            if failed_steps:
                state.status = PipelineStatus.FAILED
                logger.error(f"파이프라인 실패: {len(failed_steps)}개 단계 실패")
            else:
                state.status = PipelineStatus.COMPLETED
                logger.info("파이프라인 성공적으로 완료")

            state.mark_step_completed(
                "finalize",
                {
                    "final_status": state.status.value,
                    "total_duration": state.get_total_duration(),
                    "progress": state.get_progress_percentage(),
                    "status": "finalized"
                }
            )

        except Exception as e:
            logger.error(f"[Step 8] 마무리 실패: {e}")
            state.mark_step_failed("finalize", str(e))

        return state

    async def run(self, state: PipelineState) -> PipelineState:
        """
        워크플로우 실행

        Args:
            state: 초기 파이프라인 상태

        Returns:
            최종 파이프라인 상태
        """
        logger.info(f"워크플로우 실행 시작: {state.pipeline_id}")

        try:
            # LangGraph 실행
            final_state = await self.graph.ainvoke(state)
            return final_state

        except Exception as e:
            logger.error(f"워크플로우 실행 중 에러: {e}")
            state.status = PipelineStatus.FAILED
            state.errors.append(str(e))
            return state

        finally:
            # Neo4j 연결 종료
            if self.neo4j_service:
                self.neo4j_service.close()

    def cleanup(self):
        """리소스 정리"""
        if self.neo4j_service:
            self.neo4j_service.close()
