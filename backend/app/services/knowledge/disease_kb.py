"""
Disease Knowledge Base (Stub)

질병 지식 베이스 - Story 3에서 완전 구현 예정.
현재는 Story 2의 의존성 해결을 위한 최소 구현.
"""
from typing import Optional, List, Dict


class DiseaseKnowledgeBase:
    """
    질병 지식 베이스 (Stub)

    TODO: Story 3에서 완전한 구현 예정
    - KCD 코드 매핑
    - 질병 분류
    - 동의어/이형태 관리
    - 질병 계층 구조
    """

    def __init__(self):
        """초기화"""
        # 기본 질병 매핑 (샘플)
        self._disease_map = {
            "암": {"kcd_code": "C00-C97", "category": "암"},
            "뇌졸중": {"kcd_code": "I60-I69", "category": "뇌혈관질환"},
            "당뇨병": {"kcd_code": "E10-E14", "category": "내분비질환"},
            "심근경색": {"kcd_code": "I21", "category": "심혈관질환"},
            "급성심근경색증": {"kcd_code": "I21", "category": "심혈관질환"},
        }

    def normalize_disease(self, disease_name: str) -> Optional[str]:
        """
        질병명 정규화

        Args:
            disease_name: 입력 질병명

        Returns:
            정규화된 질병명
        """
        # 간단한 정규화
        disease_name = disease_name.strip()

        # 매핑에 있으면 반환
        if disease_name in self._disease_map:
            return disease_name

        # 없으면 원본 반환
        return disease_name

    def get_kcd_code(self, disease_name: str) -> Optional[str]:
        """
        KCD 코드 조회

        Args:
            disease_name: 질병명

        Returns:
            KCD 코드
        """
        disease_info = self._disease_map.get(disease_name)
        return disease_info["kcd_code"] if disease_info else None

    def get_disease_category(self, disease_name: str) -> Optional[str]:
        """
        질병 분류 조회

        Args:
            disease_name: 질병명

        Returns:
            질병 분류
        """
        disease_info = self._disease_map.get(disease_name)
        return disease_info["category"] if disease_info else None

    def find_similar_diseases(self, disease_name: str, top_k: int = 5) -> List[str]:
        """
        유사 질병 찾기

        Args:
            disease_name: 질병명
            top_k: 최대 결과 수

        Returns:
            유사 질병 리스트
        """
        # TODO: Story 3에서 실제 유사도 계산 구현
        # 지금은 빈 리스트 반환
        return []

    def is_valid_disease(self, disease_name: str) -> bool:
        """
        유효한 질병명인지 확인

        Args:
            disease_name: 질병명

        Returns:
            유효 여부
        """
        return disease_name in self._disease_map
