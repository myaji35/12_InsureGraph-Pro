"""
FP Customer Management API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.models.fp_customer import (
    FPCustomer, FPCustomerCreate, FPCustomerUpdate, FPCustomerWithDetails,
    Consultation, ConsultationCreate,
    CustomerProduct, CustomerProductCreate,
    ProductMatchingRequest, ProductMatchingResponse
)

router = APIRouter()


def get_current_user_id() -> str:
    """TODO: Clerk 인증 연동"""
    return "user_test_001"


@router.get("/customers", response_model=List[FPCustomerWithDetails])
async def get_customers(
    city: Optional[str] = None,
    district: Optional[str] = None,
    birth_month: Optional[int] = Query(None, ge=1, le=12),
    status: Optional[str] = None,
    tags: Optional[str] = None,  # comma-separated
    db: AsyncSession = Depends(get_db)
):
    """고객 목록 조회 (필터링 지원)"""
    user_id = get_current_user_id()

    # Build query with filters
    query = """
        SELECT
            c.*,
            COUNT(DISTINCT cons.id) as consultation_count,
            COUNT(DISTINCT p.id) as product_count,
            MAX(cons.consultation_date) as last_contact_date
        FROM fp_customers c
        LEFT JOIN fp_consultations cons ON c.id = cons.customer_id
        LEFT JOIN fp_customer_products p ON c.id = p.customer_id
        WHERE c.user_id = :user_id
    """

    params = {"user_id": user_id}

    if city:
        query += " AND c.city = :city"
        params["city"] = city

    if district:
        query += " AND c.district = :district"
        params["district"] = district

    if birth_month:
        query += " AND EXTRACT(MONTH FROM c.birth_date) = :birth_month"
        params["birth_month"] = birth_month

    if status:
        query += " AND c.status = :status"
        params["status"] = status

    if tags:
        tag_list = tags.split(",")
        query += " AND c.tags && :tags"
        params["tags"] = tag_list

    query += " GROUP BY c.id ORDER BY c.created_at DESC"

    result = await db.execute(text(query), params)
    rows = result.fetchall()

    customers = []
    for row in rows:
        customer_dict = dict(row._mapping)

        # Get consultations
        cons_result = await db.execute(
            text("SELECT * FROM fp_consultations WHERE customer_id = :customer_id ORDER BY consultation_date DESC"),
            {"customer_id": customer_dict["id"]}
        )
        consultations = [dict(r._mapping) for r in cons_result.fetchall()]

        # Get products
        prod_result = await db.execute(
            text("SELECT * FROM fp_customer_products WHERE customer_id = :customer_id ORDER BY created_at DESC"),
            {"customer_id": customer_dict["id"]}
        )
        products = [dict(r._mapping) for r in prod_result.fetchall()]

        customers.append({
            **customer_dict,
            "consultations": consultations,
            "products": products
        })

    return customers


@router.post("/customers", response_model=FPCustomer)
async def create_customer(
    customer: FPCustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    """새 고객 추가"""
    user_id = get_current_user_id()

    query = text("""
        INSERT INTO fp_customers
        (user_id, name, phone, email, birth_date, gender, address, city, district, tags, status, notes)
        VALUES
        (:user_id, :name, :phone, :email, :birth_date, :gender, :address, :city, :district, :tags, :status, :notes)
        RETURNING *
    """)

    result = await db.execute(query, {
        "user_id": user_id,
        "name": customer.name,
        "phone": customer.phone,
        "email": customer.email,
        "birth_date": customer.birth_date,
        "gender": customer.gender,
        "address": customer.address,
        "city": customer.city,
        "district": customer.district,
        "tags": customer.tags,
        "status": customer.status,
        "notes": customer.notes
    })

    await db.commit()
    row = result.fetchone()
    return dict(row._mapping)


@router.put("/customers/{customer_id}", response_model=FPCustomer)
async def update_customer(
    customer_id: UUID,
    customer: FPCustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """고객 정보 수정"""
    user_id = get_current_user_id()

    # Build update query dynamically
    updates = []
    params = {"id": customer_id, "user_id": user_id}

    for field, value in customer.dict(exclude_unset=True).items():
        if value is not None:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    updates.append("updated_at = CURRENT_TIMESTAMP")

    query = text(f"""
        UPDATE fp_customers
        SET {', '.join(updates)}
        WHERE id = :id AND user_id = :user_id
        RETURNING *
    """)

    result = await db.execute(query, params)
    await db.commit()

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Customer not found")

    return dict(row._mapping)


@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """고객 삭제"""
    user_id = get_current_user_id()

    result = await db.execute(
        text("DELETE FROM fp_customers WHERE id = :id AND user_id = :user_id"),
        {"id": customer_id, "user_id": user_id}
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {"message": "Customer deleted successfully"}


@router.post("/customers/{customer_id}/consultations", response_model=Consultation)
async def add_consultation(
    customer_id: UUID,
    consultation: ConsultationCreate,
    db: AsyncSession = Depends(get_db)
):
    """상담 이력 추가"""
    query = text("""
        INSERT INTO fp_consultations
        (customer_id, consultation_date, consultation_type, subject, content, next_action, next_action_date)
        VALUES
        (:customer_id, :consultation_date, :consultation_type, :subject, :content, :next_action, :next_action_date)
        RETURNING *
    """)

    result = await db.execute(query, {
        "customer_id": customer_id,
        "consultation_date": consultation.consultation_date,
        "consultation_type": consultation.consultation_type,
        "subject": consultation.subject,
        "content": consultation.content,
        "next_action": consultation.next_action,
        "next_action_date": consultation.next_action_date
    })

    await db.commit()
    row = result.fetchone()
    return dict(row._mapping)


@router.post("/customers/{customer_id}/products", response_model=CustomerProduct)
async def add_customer_product(
    customer_id: UUID,
    product: CustomerProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """고객 가입상품 추가"""
    query = text("""
        INSERT INTO fp_customer_products
        (customer_id, product_name, product_type, insurer, policy_number,
         start_date, end_date, premium, coverage_amount, status, notes)
        VALUES
        (:customer_id, :product_name, :product_type, :insurer, :policy_number,
         :start_date, :end_date, :premium, :coverage_amount, :status, :notes)
        RETURNING *
    """)

    result = await db.execute(query, {
        "customer_id": customer_id,
        "product_name": product.product_name,
        "product_type": product.product_type,
        "insurer": product.insurer,
        "policy_number": product.policy_number,
        "start_date": product.start_date,
        "end_date": product.end_date,
        "premium": product.premium,
        "coverage_amount": product.coverage_amount,
        "status": product.status,
        "notes": product.notes
    })

    await db.commit()
    row = result.fetchone()
    return dict(row._mapping)


@router.post("/customers/{customer_id}/analyze-matching", response_model=ProductMatchingResponse)
async def analyze_product_matching(
    customer_id: UUID,
    request: ProductMatchingRequest,
    db: AsyncSession = Depends(get_db)
):
    """AI 기반 상품 매칭 분석"""
    # Get customer info
    result = await db.execute(
        text("SELECT * FROM fp_customers WHERE id = :id"),
        {"id": customer_id}
    )
    customer = result.fetchone()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer_dict = dict(customer._mapping)

    # Get existing products
    prod_result = await db.execute(
        text("SELECT * FROM fp_customer_products WHERE customer_id = :customer_id"),
        {"customer_id": customer_id}
    )
    existing_products = [dict(r._mapping) for r in prod_result.fetchall()]

    # Simple AI matching logic (can be enhanced with actual LLM)
    reasons = []
    recommendations = []
    score = 50.0  # Base score

    # Age analysis
    if customer_dict.get("birth_date"):
        from datetime import date
        age = (date.today() - customer_dict["birth_date"]).days // 365

        if request.product_type == "life":
            if 30 <= age <= 50:
                score += 20
                reasons.append(f"고객 연령({age}세)이 생명보험 가입에 적합한 나이입니다")
            elif age > 50:
                score += 10
                recommendations.append("종신보험보다는 정기보험을 권장합니다")

        elif request.product_type == "health":
            if age < 40:
                score += 25
                reasons.append("젊은 나이에 건강보험 가입 시 보험료가 저렴합니다")
            else:
                score += 15
                recommendations.append("암보험이나 CI보험을 함께 검토하세요")

    # Existing products analysis
    has_similar_product = any(
        p.get("insurer") == request.insurer and p.get("product_type") == request.product_type
        for p in existing_products
    )

    if has_similar_product:
        score -= 30
        reasons.append(f"이미 {request.insurer}의 {request.product_type} 상품에 가입되어 있습니다")
        recommendations.append("중복 가입 여부를 확인하고, 보장 내용을 비교하세요")
    else:
        score += 15
        reasons.append(f"{request.product_type} 상품이 없어 보장 공백이 있을 수 있습니다")

    # Location-based analysis
    if customer_dict.get("city"):
        score += 5
        reasons.append(f"{customer_dict['city']} 지역 고객으로 지점 방문이 용이합니다")

    # Consultation history
    cons_result = await db.execute(
        text("SELECT COUNT(*) as count FROM fp_consultations WHERE customer_id = :customer_id"),
        {"customer_id": customer_id}
    )
    cons_count = cons_result.fetchone()[0]

    if cons_count > 3:
        score += 10
        reasons.append(f"상담 이력({cons_count}회)이 많아 신뢰 관계가 형성되어 있습니다")

    recommendations.append(f"{request.insurer}의 최신 {request.product_type} 상품 자료를 준비하세요")
    recommendations.append("고객의 현재 보장 내용과 비교 분석 자료를 제시하세요")

    return ProductMatchingResponse(
        customer_id=customer_id,
        customer_name=customer_dict["name"],
        insurer=request.insurer,
        product_type=request.product_type,
        matching_score=min(100.0, max(0.0, score)),
        reasons=reasons,
        recommendations=recommendations
    )


@router.get("/stats/summary")
async def get_summary_stats(db: AsyncSession = Depends(get_db)):
    """통계 요약"""
    user_id = get_current_user_id()

    result = await db.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
            COUNT(CASE WHEN status = 'prospect' THEN 1 END) as prospect,
            COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive
        FROM fp_customers
        WHERE user_id = :user_id
    """), {"user_id": user_id})

    stats = dict(result.fetchone()._mapping)
    return stats
