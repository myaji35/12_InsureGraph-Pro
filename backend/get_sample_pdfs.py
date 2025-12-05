"""
데이터베이스에서 샘플 PDF URL 추출

현재 시스템에 학습된 문서 5개의 URL을 가져옵니다.
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', 5432)
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')


def get_sample_documents(limit=5):
    """데이터베이스에서 샘플 문서 가져오기"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD
        )

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 처리된 문서 조회
        query = """
            SELECT
                id,
                insurer,
                title,
                pdf_url,
                category,
                product_type,
                status,
                created_at
            FROM crawler_documents
            WHERE status IN ('processed', 'completed', 'downloaded')
                AND pdf_url IS NOT NULL
                AND pdf_url != ''
            ORDER BY created_at DESC
            LIMIT %s
        """

        cursor.execute(query, (limit,))
        documents = cursor.fetchall()

        cursor.close()
        conn.close()

        return documents

    except Exception as e:
        print(f"❌ Database error: {e}")
        return []


if __name__ == "__main__":
    print("\n" + "="*80)
    print("📚 학습된 보험약관 문서 샘플 조회")
    print("="*80)

    documents = get_sample_documents(limit=5)

    if not documents:
        print("\n⚠️  데이터베이스에서 문서를 찾을 수 없습니다.")
        print("Fallback 샘플 URL을 사용합니다.\n")

        # Fallback samples
        print("\n샘플 PDF URL 목록:")
        print("-" * 80)
        print("1. 삼성화재 - 자동차보험")
        print("   (실제 크롤링된 URL을 여기에 출력)")
        print("\n2. KB손해보험 - 건강보험")
        print("   (실제 크롤링된 URL을 여기에 출력)")

    else:
        print(f"\n✅ {len(documents)}개 문서 찾음\n")
        print("샘플 PDF URL 목록:")
        print("-" * 80)

        for i, doc in enumerate(documents, 1):
            print(f"\n{i}. {doc['insurer']} - {doc['category']}")
            print(f"   제목: {doc['title']}")
            print(f"   URL: {doc['pdf_url']}")
            print(f"   상태: {doc['status']}")

        print("\n" + "="*80)
        print("\n이 URL들을 test_extraction_comparison.py의 폴백 함수에 추가하세요.")

    print("\n")
