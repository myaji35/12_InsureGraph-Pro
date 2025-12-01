"""
Customer Management API Endpoints

Story 3.4: Customer Portfolio Management
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Depends, Query as QueryParam
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.customer import (
    Customer, CustomerCreate, CustomerUpdate, CustomerWithPolicies,
    CustomerPolicy, CustomerPolicyCreate, CustomerPolicyUpdate,
    CustomerListResponse, CoverageSummary, CustomerFilter,
    PolicyStatus, PolicyType, Gender
)
from app.models.user import User
from loguru import logger


router = APIRouter()


# Helper functions

def calculate_age(birth_year: int) -> int:
    """Calculate age from birth year"""
    current_year = datetime.now().year
    return current_year - birth_year


async def get_customer_by_id(
    customer_id: UUID,
    user: User,
    db: AsyncSession
) -> dict:
    """Get customer by ID with permission check"""
    query = f"""
        SELECT * FROM customers 
        WHERE id = '{customer_id}' AND fp_user_id = '{user.id}'
    """
    result = await db.execute(query)
    customer = result.first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return dict(customer._mapping)


# Customer CRUD Endpoints

@router.get("/", response_model=CustomerListResponse, summary="Get customers list")
async def list_customers(
    search: Optional[str] = QueryParam(None, description="Search by name or email"),
    gender: Optional[Gender] = QueryParam(None),
    min_age: Optional[int] = QueryParam(None, ge=0, le=150),
    max_age: Optional[int] = QueryParam(None, ge=0, le=150),
    page: int = QueryParam(1, ge=1),
    page_size: int = QueryParam(20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of customers for the current FP user.
    
    Supports:
    - Search by name or email
    - Filter by gender, age range
    - Pagination
    """
    try:
        # Build WHERE conditions
        conditions = [f"fp_user_id = '{user.id}'"]
        
        if search:
            search_term = search.replace("'", "''")
            conditions.append(
                f"(name ILIKE '%{search_term}%' OR email ILIKE '%{search_term}%')"
            )
        
        if gender:
            conditions.append(f"gender = '{gender.value}'")
        
        current_year = datetime.now().year
        if min_age is not None:
            max_birth_year = current_year - min_age
            conditions.append(f"birth_year <= {max_birth_year}")
        
        if max_age is not None:
            min_birth_year = current_year - max_age
            conditions.append(f"birth_year >= {min_birth_year}")
        
        where_clause = " AND ".join(conditions)
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM customers WHERE {where_clause}"
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get customers with pagination
        offset = (page - 1) * page_size
        query = f"""
            SELECT c.*, 
                   COUNT(cp.id) as policy_count
            FROM customers c
            LEFT JOIN customer_policies cp ON c.id = cp.customer_id
            WHERE {where_clause}
            GROUP BY c.id
            ORDER BY c.last_contact_date DESC NULLS LAST, c.created_at DESC
            LIMIT {page_size} OFFSET {offset}
        """
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        customers = []
        for row in rows:
            customer_dict = dict(row._mapping)
            customer_dict['age'] = calculate_age(customer_dict['birth_year'])
            customers.append(Customer(**customer_dict))
        
        return CustomerListResponse(
            customers=customers,
            total=total or 0,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.error(f"Error listing customers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list customers: {str(e)}")


@router.post("/", response_model=Customer, summary="Create new customer")
async def create_customer(
    customer_data: CustomerCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new customer.
    
    Requires:
    - FP user authentication
    - Customer consent checkbox
    """
    if not customer_data.consent_given:
        raise HTTPException(
            status_code=400,
            detail="Customer consent is required to store personal information"
        )
    
    try:
        # Insert customer
        query = f"""
            INSERT INTO customers (
                fp_user_id, name, birth_year, gender, phone, email, 
                occupation, notes, consent_given
            ) VALUES (
                '{user.id}',
                '{customer_data.name.replace("'", "''")}',
                {customer_data.birth_year},
                '{customer_data.gender.value}',
                {f"'{customer_data.phone.replace("'", "''")}'" if customer_data.phone else 'NULL'},
                {f"'{customer_data.email.replace("'", "''")}'" if customer_data.email else 'NULL'},
                {f"'{customer_data.occupation.replace("'", "''")}'" if customer_data.occupation else 'NULL'},
                {f"'{customer_data.notes.replace("'", "''")}'" if customer_data.notes else 'NULL'},
                {customer_data.consent_given}
            )
            RETURNING *
        """
        
        result = await db.execute(query)
        await db.commit()
        row = result.first()
        
        customer_dict = dict(row._mapping)
        customer_dict['age'] = calculate_age(customer_dict['birth_year'])
        customer_dict['policy_count'] = 0
        
        logger.info(f"Created customer {customer_dict['id']} by user {user.id}")
        
        return Customer(**customer_dict)
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating customer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(e)}")


@router.get("/{customer_id}", response_model=CustomerWithPolicies, summary="Get customer details")
async def get_customer(
    customer_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get customer details including all policies.
    """
    try:
        # Get customer
        customer_dict = await get_customer_by_id(customer_id, user, db)
        customer_dict['age'] = calculate_age(customer_dict['birth_year'])
        
        # Get policies
        policies_query = f"""
            SELECT * FROM customer_policies
            WHERE customer_id = '{customer_id}'
            ORDER BY status, created_at DESC
        """
        policies_result = await db.execute(policies_query)
        policies_rows = policies_result.fetchall()
        
        policies = [CustomerPolicy(**dict(row._mapping)) for row in policies_rows]
        customer_dict['policy_count'] = len(policies)
        customer_dict['policies'] = policies
        
        return CustomerWithPolicies(**customer_dict)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(e)}")


@router.put("/{customer_id}", response_model=Customer, summary="Update customer")
async def update_customer(
    customer_id: UUID,
    customer_data: CustomerUpdate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update customer information.
    """
    try:
        # Check customer exists and belongs to user
        await get_customer_by_id(customer_id, user, db)
        
        # Build UPDATE query
        updates = []
        if customer_data.name is not None:
            updates.append(f"name = '{customer_data.name.replace("'", "''")}'")
        if customer_data.birth_year is not None:
            updates.append(f"birth_year = {customer_data.birth_year}")
        if customer_data.gender is not None:
            updates.append(f"gender = '{customer_data.gender.value}'")
        if customer_data.phone is not None:
            updates.append(f"phone = '{customer_data.phone.replace("'", "''")}'")
        if customer_data.email is not None:
            updates.append(f"email = '{customer_data.email.replace("'", "''")}'")
        if customer_data.occupation is not None:
            updates.append(f"occupation = '{customer_data.occupation.replace("'", "''")}'")
        if customer_data.last_contact_date is not None:
            updates.append(f"last_contact_date = '{customer_data.last_contact_date.isoformat()}'")
        if customer_data.notes is not None:
            updates.append(f"notes = '{customer_data.notes.replace("'", "''")}'")
        if customer_data.consent_given is not None:
            updates.append(f"consent_given = {customer_data.consent_given}")
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        query = f"""
            UPDATE customers
            SET {', '.join(updates)}
            WHERE id = '{customer_id}' AND fp_user_id = '{user.id}'
            RETURNING *
        """
        
        result = await db.execute(query)
        await db.commit()
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_dict = dict(row._mapping)
        customer_dict['age'] = calculate_age(customer_dict['birth_year'])
        
        # Get policy count
        count_query = f"""
            SELECT COUNT(*) as policy_count
            FROM customer_policies
            WHERE customer_id = '{customer_id}'
        """
        count_result = await db.execute(count_query)
        customer_dict['policy_count'] = count_result.scalar() or 0
        
        logger.info(f"Updated customer {customer_id} by user {user.id}")
        
        return Customer(**customer_dict)
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating customer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update customer: {str(e)}")


@router.delete("/{customer_id}", summary="Delete customer")
async def delete_customer(
    customer_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a customer and all their policies.
    
    Note: This is a hard delete. Consider soft delete in production.
    """
    try:
        # Check customer exists
        await get_customer_by_id(customer_id, user, db)
        
        # Delete customer (CASCADE will delete policies)
        query = f"""
            DELETE FROM customers
            WHERE id = '{customer_id}' AND fp_user_id = '{user.id}'
        """
        
        await db.execute(query)
        await db.commit()
        
        logger.info(f"Deleted customer {customer_id} by user {user.id}")
        
        return {"message": "Customer deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting customer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete customer: {str(e)}")


# Customer Policy Endpoints

@router.post("/{customer_id}/policies", response_model=CustomerPolicy, summary="Add policy to customer")
async def add_customer_policy(
    customer_id: UUID,
    policy_data: CustomerPolicyCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a new policy to a customer.
    """
    try:
        # Check customer exists
        await get_customer_by_id(customer_id, user, db)
        
        # Validate customer_id matches
        if policy_data.customer_id != customer_id:
            raise HTTPException(status_code=400, detail="Customer ID mismatch")
        
        # Insert policy
        query = f"""
            INSERT INTO customer_policies (
                customer_id, policy_name, insurer, policy_type,
                coverage_amount, premium_amount, start_date, end_date, notes
            ) VALUES (
                '{customer_id}',
                '{policy_data.policy_name.replace("'", "''")}',
                '{policy_data.insurer.replace("'", "''")}',
                {f"'{policy_data.policy_type.value}'" if policy_data.policy_type else 'NULL'},
                {policy_data.coverage_amount if policy_data.coverage_amount is not None else 'NULL'},
                {policy_data.premium_amount if policy_data.premium_amount is not None else 'NULL'},
                {f"'{policy_data.start_date.isoformat()}'" if policy_data.start_date else 'NULL'},
                {f"'{policy_data.end_date.isoformat()}'" if policy_data.end_date else 'NULL'},
                {f"'{policy_data.notes.replace("'", "''")}'" if policy_data.notes else 'NULL'}
            )
            RETURNING *
        """
        
        result = await db.execute(query)
        await db.commit()
        row = result.first()
        
        logger.info(f"Added policy to customer {customer_id}")
        
        return CustomerPolicy(**dict(row._mapping))
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add policy: {str(e)}")


@router.get("/{customer_id}/coverage", response_model=CoverageSummary, summary="Get coverage summary")
async def get_coverage_summary(
    customer_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get coverage summary and gap analysis for a customer.
    """
    try:
        # Check customer exists
        customer_dict = await get_customer_by_id(customer_id, user, db)
        
        # Get all policies
        query = f"""
            SELECT * FROM customer_policies
            WHERE customer_id = '{customer_id}'
        """
        result = await db.execute(query)
        policies = [dict(row._mapping) for row in result.fetchall()]
        
        # Calculate summary
        total_coverage = 0
        total_premium = 0
        active_policies = 0
        expired_policies = 0
        coverage_by_type = {}
        
        for policy in policies:
            if policy['coverage_amount']:
                total_coverage += policy['coverage_amount']
            if policy['premium_amount']:
                total_premium += policy['premium_amount']
            
            if policy['status'] == 'active':
                active_policies += 1
            elif policy['status'] == 'expired':
                expired_policies += 1
            
            policy_type = policy.get('policy_type', 'other')
            if policy_type:
                coverage_by_type[policy_type] = coverage_by_type.get(policy_type, 0) + (policy['coverage_amount'] or 0)
        
        # Simple gap analysis
        gaps = []
        recommendations = []
        
        policy_types_present = set(p.get('policy_type') for p in policies if p.get('policy_type'))
        
        if 'life' not in policy_types_present:
            gaps.append("생명보험 미가입")
            recommendations.append("가족 보장을 위해 생명보험 가입을 검토하세요")
        
        if 'health' not in policy_types_present:
            gaps.append("건강보험 미가입")
            recommendations.append("의료비 부담 완화를 위해 건강보험 가입을 권장합니다")
        
        if total_coverage < 100000000:  # 1억원
            gaps.append("총 보장액 부족")
            recommendations.append("최소 1억원 이상의 보장을 추천합니다")
        
        return CoverageSummary(
            total_coverage=total_coverage,
            total_premium=total_premium,
            active_policies=active_policies,
            expired_policies=expired_policies,
            coverage_by_type=coverage_by_type,
            gaps=gaps,
            recommendations=recommendations
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coverage summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get coverage summary: {str(e)}")
