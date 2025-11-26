# API Specifications: InsureGraph Pro

**Project**: InsureGraph Pro
**API Version**: v1
**Base URL**: `https://api.insuregraph.com/api/v1`
**Protocol**: HTTPS only
**Authentication**: JWT Bearer Token
**Content-Type**: `application/json`
**Version**: 1.0
**Date**: 2025-11-25

---

## 📋 Overview

This document provides comprehensive API specifications for InsureGraph Pro backend services. All APIs follow RESTful conventions and return JSON responses.

### API Design Principles

1. **Resource-based URLs**: `/api/v1/resources/{id}`
2. **HTTP Methods**: GET (read), POST (create), PUT (update), DELETE (delete)
3. **Status Codes**: Standard HTTP codes (200, 201, 400, 401, 403, 404, 500)
4. **Error Format**: Consistent JSON error structure
5. **Versioning**: `/api/v1/` prefix for backward compatibility
6. **Pagination**: Cursor-based or offset-based
7. **Rate Limiting**: Per-user tier limits

---

## 🔐 Authentication

### Login

**Endpoint**: `POST /api/v1/auth/login`

**Request**:
```json
{
  "email": "fp@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "fp@example.com",
    "role": "fp",
    "ga_id": "660e8400-e29b-41d4-a716-446655440111",
    "tier": "pro"
  }
}
```

**Error Response** (401 Unauthorized):
```json
{
  "error": {
    "code": "AUTH_FAILED",
    "message": "Invalid email or password",
    "details": null
  }
}
```

---

### Refresh Token

**Endpoint**: `POST /api/v1/auth/refresh`

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

---

### Logout

**Endpoint**: `POST /api/v1/auth/logout`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response** (204 No Content)

---

## 📄 Policy Ingestion API

### Upload Policy PDF

**Endpoint**: `POST /api/v1/policies/ingest`

**Authentication**: Required (Admin only)

**Request** (multipart/form-data):
```
POST /api/v1/policies/ingest
Content-Type: multipart/form-data
Authorization: Bearer {access_token}

--boundary
Content-Disposition: form-data; name="file"; filename="samsung_cancer_insurance_2023.pdf"
Content-Type: application/pdf

[PDF binary data]
--boundary
Content-Disposition: form-data; name="metadata"
Content-Type: application/json

{
  "insurer": "Samsung Life",
  "product_name": "Cancer Insurance Premium",
  "product_code": "SL-CI-001",
  "launch_date": "2023-03-15",
  "version": "2.0",
  "description": "Comprehensive cancer coverage"
}
--boundary--
```

**Response** (202 Accepted):
```json
{
  "job_id": "job_7a8b9c0d-1234-5678-90ab-cdef12345678",
  "status": "processing",
  "estimated_time": 180,
  "webhook_url": "https://api.insuregraph.com/webhooks/job_7a8b9c0d-1234-5678-90ab-cdef12345678",
  "created_at": "2025-11-25T10:30:00Z"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": {
    "code": "INVALID_FILE",
    "message": "File must be a PDF",
    "details": {
      "received_type": "application/msword",
      "allowed_types": ["application/pdf"]
    }
  }
}
```

**Validation Rules**:
- File type: `application/pdf` only
- Max size: 100 MB
- Required metadata fields: `insurer`, `product_name`, `launch_date`

---

### Get Ingestion Job Status

**Endpoint**: `GET /api/v1/policies/ingest/{job_id}/status`

**Authentication**: Required

**Response** (200 OK - Processing):
```json
{
  "job_id": "job_7a8b9c0d-1234-5678-90ab-cdef12345678",
  "status": "processing",
  "progress": 45,
  "current_stage": "extract_relations",
  "stages": [
    {
      "name": "ocr",
      "status": "completed",
      "duration_ms": 12500,
      "confidence": 0.97
    },
    {
      "name": "parse_structure",
      "status": "completed",
      "duration_ms": 8300,
      "articles_parsed": 89
    },
    {
      "name": "extract_critical",
      "status": "completed",
      "duration_ms": 3200,
      "data_extracted": 145
    },
    {
      "name": "extract_relations",
      "status": "in_progress",
      "progress": 65
    },
    {
      "name": "construct_graph",
      "status": "pending"
    }
  ],
  "created_at": "2025-11-25T10:30:00Z",
  "updated_at": "2025-11-25T10:32:45Z"
}
```

**Response** (200 OK - Completed):
```json
{
  "job_id": "job_7a8b9c0d-1234-5678-90ab-cdef12345678",
  "status": "completed",
  "progress": 100,
  "results": {
    "product_id": "prod_12345678-90ab-cdef-1234-567890abcdef",
    "nodes_created": 1247,
    "edges_created": 3521,
    "clauses_parsed": 89,
    "coverages_identified": 12,
    "diseases_linked": 245,
    "validation_status": "passed",
    "warnings": [
      "Article 23 paragraph 5 has low OCR confidence (0.72)"
    ]
  },
  "created_at": "2025-11-25T10:30:00Z",
  "completed_at": "2025-11-25T10:33:15Z",
  "duration_ms": 195000
}
```

**Response** (200 OK - Failed):
```json
{
  "job_id": "job_7a8b9c0d-1234-5678-90ab-cdef12345678",
  "status": "failed",
  "progress": 30,
  "error": {
    "code": "OCR_FAILED",
    "message": "OCR confidence too low",
    "stage": "ocr",
    "details": {
      "confidence": 0.45,
      "threshold": 0.80,
      "pages_affected": [15, 16, 17]
    }
  },
  "created_at": "2025-11-25T10:30:00Z",
  "failed_at": "2025-11-25T10:31:20Z"
}
```

---

### List Ingested Policies

**Endpoint**: `GET /api/v1/policies`

**Authentication**: Required

**Query Parameters**:
- `insurer` (optional): Filter by insurer name
- `product_type` (optional): Filter by type (cancer, cardiovascular, etc.)
- `status` (optional): Filter by status (active, deprecated)
- `page` (optional, default: 1): Page number
- `per_page` (optional, default: 20, max: 100): Items per page

**Request**:
```
GET /api/v1/policies?insurer=Samsung%20Life&page=1&per_page=20
Authorization: Bearer {access_token}
```

**Response** (200 OK):
```json
{
  "policies": [
    {
      "id": "prod_12345678-90ab-cdef-1234-567890abcdef",
      "insurer": "Samsung Life",
      "product_name": "Cancer Insurance Premium",
      "product_code": "SL-CI-001",
      "launch_date": "2023-03-15",
      "version": "2.0",
      "status": "active",
      "coverages_count": 12,
      "clauses_count": 89,
      "created_at": "2025-11-25T10:33:15Z"
    },
    {
      "id": "prod_23456789-01bc-def2-3456-7890abcdef12",
      "insurer": "Samsung Life",
      "product_name": "Cardiovascular Disease Insurance",
      "product_code": "SL-CV-002",
      "launch_date": "2022-06-01",
      "version": "1.5",
      "status": "active",
      "coverages_count": 8,
      "clauses_count": 67,
      "created_at": "2025-11-20T14:22:30Z"
    }
  ],
  "pagination": {
    "total": 45,
    "page": 1,
    "per_page": 20,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 🔍 Query API

### Execute Policy Query

**Endpoint**: `POST /api/v1/analysis/query`

**Authentication**: Required

**Request**:
```json
{
  "query": "갑상선암 보장돼요?",
  "context": {
    "product_ids": ["prod_12345678-90ab-cdef-1234-567890abcdef"],
    "customer_profile": {
      "age": 35,
      "gender": "F",
      "existing_policies": []
    }
  },
  "options": {
    "include_reasoning_path": true,
    "max_hops": 3,
    "confidence_threshold": 0.7
  }
}
```

**Response** (200 OK):
```json
{
  "query_id": "qry_98765432-10fe-dcba-9876-543210fedcba",
  "query": "갑상선암 보장돼요?",
  "classification": {
    "type": "simple_coverage",
    "confidence": 0.95
  },
  "answer": {
    "summary": "갑상선암(C77)은 소액암으로 분류되어 1천만원이 보장되며, 계약일로부터 90일 면책기간이 적용됩니다.",
    "confidence": 0.92,
    "status": "high_confidence",
    "details": [
      {
        "product": {
          "id": "prod_12345678-90ab-cdef-1234-567890abcdef",
          "name": "Cancer Insurance Premium"
        },
        "coverage": {
          "name": "암진단특약",
          "code": "CI-001"
        },
        "is_covered": true,
        "conditions": [
          {
            "type": "waiting_period",
            "days": 90,
            "description": "계약일로부터 90일 이후 발생한 갑상선암은 보장"
          },
          {
            "type": "classification",
            "description": "갑상선암(C77)은 소액암으로 분류"
          }
        ],
        "payment_amount": 10000000,
        "exclusions": [],
        "reasoning": "약관 제10조 ②항에 따라 갑상선의 악성신생물(C77)은 소액암으로 분류되어 일반암 보장금액의 10%인 1천만원이 지급됩니다."
      }
    ]
  },
  "reasoning_path": {
    "nodes": [
      {
        "id": "prod_12345678",
        "type": "Product",
        "label": "Cancer Insurance Premium"
      },
      {
        "id": "cov_ci001",
        "type": "Coverage",
        "label": "암진단특약"
      },
      {
        "id": "dis_c77",
        "type": "Disease",
        "label": "갑상선암(C77)"
      },
      {
        "id": "cond_waiting",
        "type": "Condition",
        "label": "면책기간 90일"
      }
    ],
    "edges": [
      {
        "id": "edge_1",
        "source": "prod_12345678",
        "target": "cov_ci001",
        "type": "HAS_COVERAGE",
        "is_highlighted": true
      },
      {
        "id": "edge_2",
        "source": "cov_ci001",
        "target": "dis_c77",
        "type": "COVERS",
        "is_highlighted": true,
        "properties": {
          "classification": "minor_cancer",
          "amount": 10000000
        }
      },
      {
        "id": "edge_3",
        "source": "cov_ci001",
        "target": "cond_waiting",
        "type": "REQUIRES",
        "is_highlighted": true
      }
    ]
  },
  "sources": [
    {
      "clause_id": "clause_123",
      "article_num": "제10조",
      "title": "보험금 지급",
      "paragraph": "②항",
      "page": 15,
      "excerpt": "다만, 갑상선의 악성신생물(C77), 기타 피부암(C44), 제자리암(D00~D09), 경계성 종양(D37~D48) 중 하나로 진단 확정된 경우에는 제1항 암진단급여금의 10%를 지급합니다."
    }
  ],
  "warnings": [],
  "disclaimer": "본 분석은 참고용이며, 최종 판단은 보험사가 합니다.",
  "execution_time_ms": 342,
  "model_used": "solar-pro",
  "cost": 0.002,
  "created_at": "2025-11-25T11:15:30Z"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "Query too short",
    "details": {
      "query_length": 3,
      "min_length": 5
    }
  }
}
```

**Status Codes**:
- `high_confidence`: Confidence >= 0.85 (proceed)
- `medium_confidence`: Confidence 0.70-0.84 (proceed with warning)
- `needs_review`: Confidence < 0.70 (expert review required)
- `failed`: Validation failed or error occurred

---

### Gap Analysis

**Endpoint**: `POST /api/v1/analysis/gap-analysis`

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "cust_11111111-2222-3333-4444-555555555555",
  "current_policies": [
    {
      "product_id": "prod_12345678-90ab-cdef-1234-567890abcdef",
      "purchase_date": "2015-06-01",
      "coverages": [
        {
          "name": "암진단특약",
          "amount": 50000000
        }
      ]
    }
  ],
  "target_profile": {
    "age": 35,
    "occupation": "office_worker",
    "health_concerns": ["cancer", "cardiovascular"],
    "family_history": ["cancer"]
  }
}
```

**Response** (200 OK):
```json
{
  "analysis_id": "gap_22222222-3333-4444-5555-666666666666",
  "customer_id": "cust_11111111-2222-3333-4444-555555555555",
  "gaps": [
    {
      "type": "outdated_policy",
      "severity": "high",
      "category": "cancer",
      "description": "2015년 가입 암보험은 갑상선 림프절 전이를 소액암으로 분류하여 보장금액이 낮습니다",
      "current_coverage": {
        "product_id": "prod_12345678-90ab-cdef-1234-567890abcdef",
        "amount": 5000000,
        "classification": "minor_cancer"
      },
      "recommended_coverage": {
        "amount": 50000000,
        "classification": "general_cancer",
        "reason": "2020년 이후 약관은 림프절 전이를 일반암으로 인정"
      },
      "impact": {
        "potential_loss": 45000000,
        "probability": "medium"
      }
    },
    {
      "type": "missing_coverage",
      "severity": "medium",
      "category": "cardiovascular",
      "description": "뇌심혈관 질환 담보가 없습니다",
      "current_coverage": null,
      "recommended_coverage": {
        "amount": 50000000,
        "reason": "가족력 및 연령대 고려 시 필수 담보"
      },
      "impact": {
        "potential_loss": 50000000,
        "probability": "low"
      }
    }
  ],
  "opportunities": [
    {
      "type": "claim_opportunity",
      "description": "현재 보험에서 갑상선암 소액암으로 청구 가능",
      "product_id": "prod_12345678-90ab-cdef-1234-567890abcdef",
      "estimated_amount": 5000000,
      "required_actions": [
        "진단서 제출",
        "병리조직검사 결과 첨부"
      ]
    }
  ],
  "score": {
    "overall": 65,
    "cancer": 70,
    "cardiovascular": 45,
    "disability": 60,
    "death": 75
  },
  "recommendations": [
    {
      "action": "upgrade_policy",
      "priority": "high",
      "suggested_product_id": "prod_99999999-aaaa-bbbb-cccc-dddddddddddd",
      "reasoning": "최신 약관으로 갈아타면 림프절 전이 보장 강화"
    },
    {
      "action": "add_coverage",
      "priority": "medium",
      "suggested_product_id": "prod_88888888-9999-aaaa-bbbb-cccccccccccc",
      "reasoning": "뇌심혈관 질환 담보 추가 권장"
    }
  ],
  "created_at": "2025-11-25T11:20:00Z"
}
```

---

### Product Comparison

**Endpoint**: `POST /api/v1/analysis/compare`

**Authentication**: Required

**Request**:
```json
{
  "product_ids": [
    "prod_12345678-90ab-cdef-1234-567890abcdef",
    "prod_23456789-01bc-def2-3456-7890abcdef12"
  ],
  "comparison_criteria": [
    "coverage_overlap",
    "cost_benefit",
    "claim_conditions"
  ]
}
```

**Response** (200 OK):
```json
{
  "comparison_id": "cmp_33333333-4444-5555-6666-777777777777",
  "products": [
    {
      "product_id": "prod_12345678-90ab-cdef-1234-567890abcdef",
      "name": "Samsung Cancer Insurance Premium",
      "insurer": "Samsung Life",
      "strengths": [
        "광범위한 소액암 보장",
        "면책기간 짧음 (90일)"
      ],
      "weaknesses": [
        "비례보상 50%",
        "갑상선암 보장금액 낮음"
      ],
      "total_coverage_amount": 100000000,
      "premium_estimate": 50000
    },
    {
      "product_id": "prod_23456789-01bc-def2-3456-7890abcdef12",
      "name": "Hanwha CI Insurance",
      "insurer": "Hanwha Life",
      "strengths": [
        "비례보상 100%",
        "중대질병 보장 우수"
      ],
      "weaknesses": [
        "갑상선암 제외",
        "면책기간 길음 (120일)"
      ],
      "total_coverage_amount": 150000000,
      "premium_estimate": 70000
    }
  ],
  "overlaps": [
    {
      "disease": "갑상선암(C77)",
      "overlap_type": "partial",
      "details": {
        "prod_12345678": {
          "is_covered": true,
          "amount": 10000000,
          "classification": "minor_cancer"
        },
        "prod_23456789": {
          "is_covered": false,
          "reason": "갑상선암 제외"
        }
      }
    },
    {
      "disease": "급성심근경색(I21)",
      "overlap_type": "duplicate",
      "combined_payout": 75000000,
      "individual_payouts": {
        "prod_12345678": 50000000,
        "prod_23456789": 50000000
      },
      "conflict": {
        "type": "proportional_payment",
        "rule": "각 상품별 50% 비례보상",
        "actual_payout": 75000000
      }
    }
  ],
  "recommendations": {
    "best_for_customer": "prod_23456789",
    "reasoning": "중대질병 보장이 우수하고 갑상선암 리스크가 낮은 고객에게 적합",
    "cost_benefit_ratio": {
      "prod_12345678": 2.0,
      "prod_23456789": 2.14
    }
  },
  "summary": "Product B (Hanwha CI Insurance)가 보장 범위와 금액 면에서 우수하나, 갑상선암 보장이 필요한 경우 Product A 추가 고려",
  "created_at": "2025-11-25T11:25:00Z"
}
```

---

## 👥 Customer Management API

### List Customers

**Endpoint**: `GET /api/v1/customers`

**Authentication**: Required

**Query Parameters**:
- `search` (optional): Search by name
- `page`, `per_page`: Pagination

**Response** (200 OK):
```json
{
  "customers": [
    {
      "id": "cust_11111111-2222-3333-4444-555555555555",
      "name": "김○○",
      "birth_year": 1990,
      "gender": "F",
      "policy_count": 3,
      "last_contact": "2025-11-20T15:30:00Z",
      "created_at": "2025-10-01T09:00:00Z"
    }
  ],
  "pagination": {
    "total": 25,
    "page": 1,
    "per_page": 20
  }
}
```

---

### Get Customer Detail

**Endpoint**: `GET /api/v1/customers/{customer_id}`

**Authentication**: Required (must own customer or be admin)

**Response** (200 OK):
```json
{
  "id": "cust_11111111-2222-3333-4444-555555555555",
  "name": "김철수",
  "birth_year": 1990,
  "gender": "F",
  "phone_masked": "010-****-5678",
  "consent_id": "consent_12345",
  "consent_date": "2025-10-01T09:00:00Z",
  "policies": [
    {
      "product_id": "prod_12345678-90ab-cdef-1234-567890abcdef",
      "product_name": "Cancer Insurance Premium",
      "purchase_date": "2015-06-01",
      "status": "active"
    }
  ],
  "coverage_summary": {
    "cancer": 50000000,
    "cardiovascular": 0,
    "disability": 30000000,
    "death": 100000000
  },
  "created_at": "2025-10-01T09:00:00Z",
  "updated_at": "2025-11-20T15:30:00Z"
}
```

---

### Create Customer

**Endpoint**: `POST /api/v1/customers`

**Authentication**: Required

**Request**:
```json
{
  "name": "김철수",
  "birth_date": "1990-05-15",
  "gender": "M",
  "phone": "010-1234-5678",
  "email": "customer@example.com",
  "consent_id": "consent_67890",
  "policies": [
    {
      "product_id": "prod_12345678-90ab-cdef-1234-567890abcdef",
      "purchase_date": "2020-03-01"
    }
  ]
}
```

**Response** (201 Created):
```json
{
  "id": "cust_11111111-2222-3333-4444-555555555555",
  "name": "김철수",
  "birth_year": 1990,
  "gender": "M",
  "created_at": "2025-11-25T11:30:00Z"
}
```

---

## 🛡️ Compliance API

### Validate Sales Script

**Endpoint**: `POST /api/v1/compliance/validate-script`

**Authentication**: Required

**Request**:
```json
{
  "script": "이 상품은 갑상선암을 100% 보장합니다!",
  "context": {
    "product_id": "prod_12345678-90ab-cdef-1234-567890abcdef",
    "fp_id": "fp_44444444-5555-6666-7777-888888888888"
  }
}
```

**Response** (200 OK):
```json
{
  "validation_id": "val_55555555-6666-7777-8888-999999999999",
  "is_compliant": false,
  "violations": [
    {
      "type": "forbidden_phrase",
      "severity": "critical",
      "phrase": "100% 보장",
      "position": {
        "start": 15,
        "end": 24
      },
      "reason": "절대적 단언 표현 금지",
      "suggestion": "약관에 따라 보장될 수 있습니다"
    },
    {
      "type": "missing_disclaimer",
      "severity": "high",
      "missing_phrases": ["면책기간", "보험사 최종 판단"],
      "reason": "필수 설명 의무 누락"
    }
  ],
  "corrected_script": "이 상품은 약관 제10조에 따라 갑상선암을 소액암으로 분류하여 보장하며, 계약일로부터 90일 면책기간이 적용됩니다. 자세한 사항은 약관을 확인하시고, 최종 판단은 보험사가 합니다.",
  "risk_score": 85,
  "created_at": "2025-11-25T11:35:00Z"
}
```

---

## 📊 Analytics API

### Get Overview Analytics

**Endpoint**: `GET /api/v1/analytics/overview`

**Authentication**: Required

**Query Parameters**:
- `start_date`, `end_date`: Date range

**Response** (200 OK):
```json
{
  "period": {
    "start": "2025-11-01",
    "end": "2025-11-30"
  },
  "metrics": {
    "total_customers": 125,
    "active_customers": 98,
    "total_queries": 1547,
    "avg_queries_per_customer": 15.7,
    "avg_confidence_score": 0.87,
    "query_success_rate": 0.94
  },
  "top_questions": [
    {
      "query": "갑상선암 보장돼요?",
      "count": 87,
      "avg_confidence": 0.92
    },
    {
      "query": "뇌출혈 보장 금액은?",
      "count": 65,
      "avg_confidence": 0.89
    }
  ],
  "activity_timeline": [
    {
      "date": "2025-11-01",
      "queries": 45,
      "customers": 32
    }
  ]
}
```

---

## ⚠️ Error Responses

### Standard Error Format

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "additional context"
    },
    "trace_id": "uuid-for-debugging"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_FAILED` | 401 | Invalid credentials |
| `TOKEN_EXPIRED` | 401 | JWT token expired |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INVALID_INPUT` | 400 | Validation error |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily down |

---

## 🔄 Rate Limiting

Rate limits apply per user based on tier:

| Tier | Queries/Day | Ingestion/Month | API Calls/Min |
|------|-------------|-----------------|---------------|
| **Free** | 50 | 0 | 10 |
| **Pro** | 1000 | 50 | 60 |
| **Enterprise** | Unlimited | Unlimited | 300 |

**Response Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1700985600
```

**When Exceeded** (429):
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 1000,
      "reset_at": "2025-11-26T00:00:00Z"
    }
  }
}
```

---

## 📖 Pagination

All list endpoints support pagination:

**Query Parameters**:
- `page` (default: 1)
- `per_page` (default: 20, max: 100)

**Response Format**:
```json
{
  "data": [...],
  "pagination": {
    "total": 245,
    "page": 2,
    "per_page": 20,
    "total_pages": 13,
    "has_next": true,
    "has_prev": true
  }
}
```

---

## 🔗 Webhooks (Optional)

For long-running operations (e.g., ingestion), you can provide a webhook URL:

**Webhook Payload** (POST to your URL):
```json
{
  "event": "ingestion.completed",
  "job_id": "job_7a8b9c0d-1234-5678-90ab-cdef12345678",
  "status": "completed",
  "results": {
    "product_id": "prod_12345678-90ab-cdef-1234-567890abcdef",
    "nodes_created": 1247,
    "edges_created": 3521
  },
  "timestamp": "2025-11-25T10:33:15Z"
}
```

---

## 📚 OpenAPI 3.0 Specification

Full OpenAPI spec available at:
- **Dev**: `https://api-dev.insuregraph.com/openapi.json`
- **Prod**: `https://api.insuregraph.com/openapi.json`

Import into Postman or Swagger UI for interactive testing.

---

**Document Owner**: Backend Tech Lead
**Last Updated**: 2025-11-25
**Next Review**: After Sprint 2
