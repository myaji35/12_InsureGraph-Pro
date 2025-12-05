"""
Seed script for FP customer sample data
"""
import asyncio
from datetime import date, datetime, timedelta
from sqlalchemy import text
from app.core.database import async_engine

async def seed_fp_customers():
    """Add sample FP customer data"""
    engine = async_engine

    async with engine.begin() as conn:
        # Sample customers
        customers_data = [
            {
                "user_id": "user_test_001",
                "name": "김철수",
                "phone": "010-1234-5678",
                "email": "kim@example.com",
                "birth_date": date(1985, 3, 15),
                "gender": "male",
                "address": "서울시 강남구 테헤란로 123",
                "city": "서울",
                "district": "강남구",
                "tags": ["고객", "VIP"],
                "status": "active",
                "notes": "신규 가입 고객, 생명보험 관심 많음"
            },
            {
                "user_id": "user_test_001",
                "name": "이영희",
                "phone": "010-2345-6789",
                "email": "lee@example.com",
                "birth_date": date(1990, 7, 22),
                "gender": "female",
                "address": "서울시 서초구 반포대로 456",
                "city": "서울",
                "district": "서초구",
                "tags": ["고객"],
                "status": "active",
                "notes": "건강보험 가입 완료"
            },
            {
                "user_id": "user_test_001",
                "name": "박민수",
                "phone": "010-3456-7890",
                "email": "park@example.com",
                "birth_date": date(1982, 11, 8),
                "gender": "male",
                "address": "경기도 성남시 분당구 정자동 789",
                "city": "경기",
                "district": "성남시",
                "tags": ["고객", "재상담필요"],
                "status": "prospect",
                "notes": "암보험 상담 예정"
            },
            {
                "user_id": "user_test_001",
                "name": "최지은",
                "phone": "010-4567-8901",
                "email": "choi@example.com",
                "birth_date": date(1995, 5, 30),
                "gender": "female",
                "address": "서울시 송파구 잠실동 321",
                "city": "서울",
                "district": "송파구",
                "tags": ["고객"],
                "status": "active",
                "notes": "연금보험 가입 고려중"
            },
            {
                "user_id": "user_test_001",
                "name": "정대현",
                "phone": "010-5678-9012",
                "email": "jung@example.com",
                "birth_date": date(1978, 1, 12),
                "gender": "male",
                "address": "인천시 남동구 구월동 555",
                "city": "인천",
                "district": "남동구",
                "tags": ["고객", "VIP"],
                "status": "active",
                "notes": "종합보험 가입 완료"
            }
        ]

        print("🌱 Seeding FP customers...")
        customer_ids = []

        for customer in customers_data:
            result = await conn.execute(text("""
                INSERT INTO fp_customers
                (user_id, name, phone, email, birth_date, gender, address, city, district, tags, status, notes)
                VALUES
                (:user_id, :name, :phone, :email, :birth_date, :gender, :address, :city, :district, :tags, :status, :notes)
                RETURNING id
            """), customer)
            customer_id = result.fetchone()[0]
            customer_ids.append(customer_id)
            print(f"  ✅ Created customer: {customer['name']}")

        # Add consultations
        print("\n💬 Seeding consultations...")
        consultations_data = [
            {
                "customer_id": customer_ids[0],
                "consultation_date": datetime.now() - timedelta(days=7),
                "consultation_type": "meeting",
                "subject": "생명보험 상담",
                "content": "종신보험 vs 정기보험 비교 설명",
                "next_action": "견적서 발송",
                "next_action_date": datetime.now() + timedelta(days=3)
            },
            {
                "customer_id": customer_ids[1],
                "consultation_date": datetime.now() - timedelta(days=14),
                "consultation_type": "phone",
                "subject": "건강보험 가입",
                "content": "실손보험 가입 완료",
                "next_action": "정기 점검",
                "next_action_date": datetime.now() + timedelta(days=90)
            },
            {
                "customer_id": customer_ids[2],
                "consultation_date": datetime.now() - timedelta(days=3),
                "consultation_type": "email",
                "subject": "암보험 문의",
                "content": "3대 진단비 암보험 자료 요청",
                "next_action": "방문 상담 예약",
                "next_action_date": datetime.now() + timedelta(days=5)
            },
            {
                "customer_id": customer_ids[3],
                "consultation_date": datetime.now() - timedelta(days=21),
                "consultation_type": "meeting",
                "subject": "연금보험 상담",
                "content": "노후 준비 상품 비교",
                "next_action": "추가 상담",
                "next_action_date": datetime.now() + timedelta(days=7)
            }
        ]

        for consultation in consultations_data:
            await conn.execute(text("""
                INSERT INTO fp_consultations
                (customer_id, consultation_date, consultation_type, subject, content, next_action, next_action_date)
                VALUES
                (:customer_id, :consultation_date, :consultation_type, :subject, :content, :next_action, :next_action_date)
            """), consultation)
            print(f"  ✅ Created consultation: {consultation['subject']}")

        # Add products
        print("\n📋 Seeding customer products...")
        products_data = [
            {
                "customer_id": customer_ids[0],
                "product_name": "무배당 메트라이프 생명보험",
                "product_type": "life",
                "insurer": "메트라이프생명",
                "policy_number": "ML2024001",
                "start_date": date(2024, 1, 15),
                "end_date": date(2044, 1, 15),
                "premium": 150000,
                "coverage_amount": 50000000,
                "status": "active",
                "notes": "월납 자동이체"
            },
            {
                "customer_id": customer_ids[1],
                "product_name": "실손의료비보험",
                "product_type": "health",
                "insurer": "삼성화재",
                "policy_number": "SS2024002",
                "start_date": date(2024, 2, 1),
                "end_date": date(2034, 2, 1),
                "premium": 85000,
                "coverage_amount": 10000000,
                "status": "active",
                "notes": "갱신형"
            },
            {
                "customer_id": customer_ids[4],
                "product_name": "종합보험 패키지",
                "product_type": "life",
                "insurer": "현대해상",
                "policy_number": "HD2024003",
                "start_date": date(2023, 11, 1),
                "end_date": date(2043, 11, 1),
                "premium": 250000,
                "coverage_amount": 100000000,
                "status": "active",
                "notes": "생명+건강 통합 상품"
            }
        ]

        for product in products_data:
            await conn.execute(text("""
                INSERT INTO fp_customer_products
                (customer_id, product_name, product_type, insurer, policy_number,
                 start_date, end_date, premium, coverage_amount, status, notes)
                VALUES
                (:customer_id, :product_name, :product_type, :insurer, :policy_number,
                 :start_date, :end_date, :premium, :coverage_amount, :status, :notes)
            """), product)
            print(f"  ✅ Created product: {product['product_name']}")

        print("\n✨ Seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_fp_customers())
